#!/usr/bin/env python3
"""Descriptive IFN necromass candidate x IBGE published-centroid crosswalk.

NEVER interprets a published centroid, matching name or hypothetical displacement
radius as field positional accuracy, independent transfer error, SAR calibration,
carbon stock, or an IC95%. Each physical UF+UA contributes at most once.
"""
import argparse
import csv
import hashlib
import io
import json
import unicodedata
from collections import Counter
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def normalize(value):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', str(value).strip().casefold())
                   if not unicodedata.combining(ch))


def boolean(value):
    if value not in ('true', 'false'):
        raise ValueError('unknown spatial scenario boolean')
    return value == 'true'


def crosswalk(candidate_bytes, spatial_bytes, necro_audit, panel_audit, spatial_report):
    if digest(spatial_bytes) != spatial_report.get('output_csv_sha256'):
        raise ValueError('spatial CSV SHA256 does not match independent spatial audit')
    if (necro_audit.get('biomass_source_sha256') !=
            panel_audit.get('source_sha256', {}).get('ifn_painel_biomassa_2026')):
        raise ValueError('necromass and IBGE panels use different biomass source SHA256')
    candidates = json.loads(candidate_bytes)
    if not isinstance(candidates, list) or len(candidates) != necro_audit.get('candidate_ua'):
        raise ValueError('necromass candidate count differs from source audit')
    if spatial_report.get('independent_field_ibge_validation') is not False or spatial_report.get('carbon_homologation') is not False:
        raise ValueError('unexpected validated status in descriptive spatial source')
    reader = csv.DictReader(io.StringIO(spatial_bytes.decode('utf-8-sig'), newline=''))
    required = {'uf', 'ua', 'bioma_declarado', 'tipologia_origem_declarada',
                'ibge_legenda_1_centroide_publicado_nao_validado',
                'estavel_cenario_0_m_nao_erro', 'estavel_cenario_250_m_nao_erro',
                'estavel_cenario_1000_m_nao_erro', 'posicao_campo_verificada',
                'ibge_fitofisionomia_campo_validada', 'par_sar_validado',
                'estoque_carbono_validado', 'apto_calibracao_sar'}
    headers = reader.fieldnames or []
    if not required.issubset(headers) or len(set(headers)) != len(headers):
        raise ValueError('missing or duplicate spatial audit headers')
    spatial = {}
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('ragged spatial audit row')
        key = (row['uf'].strip(), row['ua'].strip())
        if not all(key) or key in spatial:
            raise ValueError('duplicate or missing spatial physical UA')
        if any(row[field] != 'false' for field in ('posicao_campo_verificada',
                'ibge_fitofisionomia_campo_validada', 'par_sar_validado',
                'estoque_carbono_validado', 'apto_calibracao_sar')):
            raise ValueError('unverified spatial source must not claim calibration')
        spatial[key] = row
    results = []
    seen = set()
    by_biome = Counter()
    counts = Counter()
    for candidate in candidates:
        key = (str(candidate['uf']).strip(), str(candidate['ua']).strip())
        if not all(key) or key in seen:
            raise ValueError('duplicate or missing necromass physical UA')
        seen.add(key)
        if candidate.get('scientifically_validated') is not False or candidate.get('sar_pair_eligible') is not False:
            raise ValueError('necromass candidates cannot be prevalidated')
        biome = candidate['biome']
        by_biome[biome] += 1
        counts['candidate_ua'] += 1
        row = spatial.get(key)
        label = None
        stable = [False, False, False]
        same_name = False
        if row is not None:
            counts['physical_ua_joined'] += 1
            if row['bioma_declarado'] != biome:
                raise ValueError('biome mismatch across IFN sources')
            if normalize(row['tipologia_origem_declarada']) != normalize(candidate['source_typology_unverified_ibge']):
                raise ValueError('source typology mismatch across IFN panels')
            stable = [boolean(row[f'estavel_cenario_{radius}_m_nao_erro']) for radius in (0, 250, 1000)]
            if (stable[2] and not stable[1]) or (stable[1] and not stable[0]):
                raise ValueError('non-nested hypothetical displacement scenarios')
            label = row['ibge_legenda_1_centroide_publicado_nao_validado'].strip()
            if label in ('', 'N/D'):
                label = None
            else:
                counts['published_centroid_ibge_label_present'] += 1
                same_name = normalize(label) == normalize(candidate['source_typology_unverified_ibge'])
                if same_name:
                    counts['strict_text_label_agreement_not_accuracy'] += 1
            for radius, is_stable in zip((0, 250, 1000), stable):
                if is_stable:
                    counts[f'geometric_stability_{radius}m_not_positional_error'] += 1
            if stable[2] and same_name:
                counts['strict_name_agreement_and_1000m_stability_not_validation'] += 1
        else:
            counts['not_in_spatial_panel_candidates'] += 1
        results.append({'uf': key[0], 'ua': key[1], 'biome': biome,
                        'source_typology': candidate['source_typology_unverified_ibge'],
                        'ibge_label_at_published_centroid_NOT_FIELD_VALIDATED': label,
                        'strict_name_agreement_NOT_ACCURACY': same_name,
                        'stable_0m_NOT_ERROR': stable[0],
                        'stable_250m_NOT_ERROR': stable[1],
                        'stable_1000m_NOT_ERROR': stable[2],
                        'field_position_verified': False, 'sar_pair_eligible': False,
                        'carbon_stock_tC_ha': None, 'transfer_error': None,
                        'confidence_interval_95': None})
    report = {'report_type': 'licensed_IFN_necromass_x_IBGE_published_centroid_screen_NOT_validation',
              'candidate_json_sha256': digest(candidate_bytes),
              'spatial_csv_sha256': digest(spatial_bytes),
              'biomass_source_sha256_cross_audited': necro_audit['biomass_source_sha256'],
              'candidate_ua_by_biome': dict(sorted(by_biome.items())),
              'counts': dict(sorted(counts.items())),
              'field_positional_accuracy_m': None, 'transfer_error': None,
              'carbon_stock_tC_ha': None, 'confidence_interval_95': None,
              'scientific_validation': False, 'sar_plot_pixel_validation': False,
              'warning': 'Name agreement is not accuracy: IFN typology derives from secondary information; IBGE is sampled at published centroids of unknown field accuracy. 0/250/1000m are hypothetical geometry scenarios, not positional errors. Source necromass is biomass t/ha, NOT carbon. No field plot-pixel pairs, design-based variance, temporal equivalence, or transfer-error estimate. No release evidence.'}
    return results, report


def main():
    parser = argparse.ArgumentParser()
    for name in ('candidates', 'spatial_csv', 'necro_audit', 'panel_audit', 'spatial_report', 'report', 'output_csv'):
        parser.add_argument('--' + name.replace('_', '-'), required=True)
    args = parser.parse_args()
    data, report = crosswalk(Path(args.candidates).read_bytes(), Path(args.spatial_csv).read_bytes(),
                             json.loads(Path(args.necro_audit).read_text()),
                             json.loads(Path(args.panel_audit).read_text()),
                             json.loads(Path(args.spatial_report).read_text()))
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with Path(args.output_csv).open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(data[0]) if data else ['uf', 'ua'])
        writer.writeheader()
        writer.writerows(data)
    print(json.dumps({'candidate_ua': len(data), 'scientific_validation': False}))


if __name__ == '__main__':
    main()
