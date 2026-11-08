"""Synthetic fail-closed regressions; these are NOT observational validation."""
import csv
import hashlib
import io
import json
import unittest

from tools.audit_ifn_necromass_ibge_crosswalk import crosswalk


def fixture():
    candidates = [{'uf': 'MT', 'ua': 'mt_1', 'biome': 'Cerrado',
                   'source_typology_unverified_ibge': 'Savana',
                   'scientifically_validated': False, 'sar_pair_eligible': False},
                  {'uf': 'MT', 'ua': 'mt_2', 'biome': 'Cerrado',
                   'source_typology_unverified_ibge': 'Savana',
                   'scientifically_validated': False, 'sar_pair_eligible': False}]
    row = {'uf': 'MT', 'ua': 'mt_1', 'bioma_declarado': 'Cerrado',
           'tipologia_origem_declarada': 'savana',
           'ibge_legenda_1_centroide_publicado_nao_validado': 'Savana',
           'estavel_cenario_0_m_nao_erro': 'true',
           'estavel_cenario_250_m_nao_erro': 'true',
           'estavel_cenario_1000_m_nao_erro': 'false',
           'posicao_campo_verificada': 'false',
           'ibge_fitofisionomia_campo_validada': 'false',
           'par_sar_validado': 'false', 'estoque_carbono_validado': 'false',
           'apto_calibracao_sar': 'false'}
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    raw = buf.getvalue().encode()
    candidate_raw = json.dumps(candidates).encode()
    necro = {'candidate_ua': 2, 'biomass_source_sha256': 'abc'}
    panel = {'source_sha256': {'ifn_painel_biomassa_2026': 'abc'}}
    spatial = {'output_csv_sha256': hashlib.sha256(raw).hexdigest(),
               'independent_field_ibge_validation': False, 'carbon_homologation': False}
    return candidate_raw, raw, necro, panel, spatial


class CrosswalkTests(unittest.TestCase):
    def test_joins_physical_ua_without_promotion(self):
        data, report = crosswalk(*fixture())
        self.assertEqual(report['counts']['physical_ua_joined'], 1)
        self.assertEqual(report['counts']['not_in_spatial_panel_candidates'], 1)
        self.assertEqual(report['counts']['strict_text_label_agreement_not_accuracy'], 1)
        self.assertIsNone(data[0]['carbon_stock_tC_ha'])
        self.assertFalse(report['scientific_validation'])

    def test_rejects_cross_source_biomass_hash_mismatch(self):
        args = list(fixture())
        args[3]['source_sha256']['ifn_painel_biomassa_2026'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'different biomass source'):
            crosswalk(*args)

    def test_rejects_duplicate_physical_ua(self):
        args = list(fixture())
        candidates = json.loads(args[0])
        candidates.append(candidates[0])
        args[0] = json.dumps(candidates).encode()
        args[2]['candidate_ua'] = 3
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            crosswalk(*args)

    def test_rejects_false_validation_promotion(self):
        args = list(fixture())
        lines = args[1].decode().splitlines()
        headers = lines[0].split(',')
        values = lines[1].split(',')
        values[headers.index('posicao_campo_verificada')] = 'true'
        args[1] = ('\n'.join([lines[0], ','.join(values)]) + '\n').encode()
        args[4]['output_csv_sha256'] = hashlib.sha256(args[1]).hexdigest()
        with self.assertRaisesRegex(ValueError, 'must not claim calibration'):
            crosswalk(*args)

    def test_rejects_non_nested_sensitivity(self):
        args = list(fixture())
        args[1] = args[1].replace(b'true,true,false', b'true,false,true')
        args[4]['output_csv_sha256'] = hashlib.sha256(args[1]).hexdigest()
        with self.assertRaisesRegex(ValueError, 'non-nested'):
            crosswalk(*args)

    def test_rejects_spatial_sha_mismatch(self):
        args = list(fixture())
        args[4]['output_csv_sha256'] = 'incorrect'
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            crosswalk(*args)


if __name__ == '__main__':
    unittest.main()
