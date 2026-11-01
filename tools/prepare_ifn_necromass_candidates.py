#!/usr/bin/env python3
"""Join licensed SFB necromass observations to IFN vegetation metadata, fail-closed.

A matching physical UA does NOT establish that deadwood transects were in the
same subplot, an IBGE fitofisionomia, a SAR pixel, or an independent validation.
Published necromassa_t_por_ha is biomass, NOT automatically carbon tC/ha.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from tools.ifn_state_identity import (InvalidUAIdentity, canonical_state, canonical_ua,
                                      quarantine_ua_alias)

NECRO_FIELDS = {"bioma", "uf", "ua", "n_transectos", "cod_classe_uso_da_terra", "necromassa_t_por_ha"}
BIOMASS_FIELDS = {"bioma", "uf", "ua", "sanidade", "classe_uso_da_terra", "tipologia_da_vegetacao", "equacoes"}
BIOMES = {"Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal"}
NATIVE_CLASSES = {"Floresta Natural", "Savana", "Savana-estépica", "Estepe", "Palmeiral", "Formação Pioneira", "Campinarana"}
# SFB/IFN land-use dictionary, 2024, Table 3. The 2026 panel uses
# cod_classe_uso_da_terra but the dictionary version match is not independently
# audited: a category match is only a provisional screening, NOT an IBGE overlay.
IFN_LAND_DICTIONARY = "https://dados.florestal.gov.br/dataset/344012f6-8bdc-43ec-b76f-7b7c51b053e6/resource/6bf07d59-fce4-46e4-83e8-34d82ae27640/download/metadados_uso_da_terra_uf_ifn_mai_2024.pdf"
NATIVE_FOREST_CODE_LAND = {
    **{c: {"Floresta Natural"} for c in ("111", "112", "113", "18")},
    **{c: {"Floresta Natural", "Formação Pioneira"} for c in ("12", "13")},
    "14": {"Savana", "Floresta Natural"},
    "15": {"Savana-estépica", "Floresta Natural"},
    "16": {"Campinarana", "Floresta Natural"},
    "17": {"Palmeiral", "Floresta Natural"},
}
OTHER_NATURAL_CODES = {"31", "32"}  # natural shrublands/grasslands, not forest
ANTHROPIC_CODES = {"19", "41", "42", "43", "44", "45"}  # planted forests, crops, pasture


def _identity(value):
    return unicodedata.normalize("NFKC", str(value or "").strip()).casefold()


def _rows(raw, required, source):
    try:
        raw.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        raw.decode("cp1252")  # strict: reject bytes not representable in cp1252
        encoding = "cp1252"
    matches = []
    for delimiter in (";", ",", "\t"):
        with io.TextIOWrapper(io.BytesIO(raw), encoding=encoding, newline="") as stream:
            probe = csv.DictReader(stream, delimiter=delimiter)
            if required.issubset(set(probe.fieldnames or [])):
                matches.append(delimiter)
    if len(matches) != 1:
        raise ValueError(f"{source}: mandatory schema or delimiter ambiguous")
    with io.TextIOWrapper(io.BytesIO(raw), encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream, delimiter=matches[0])
        headers = reader.fieldnames or []
        canonical = [_identity(x) for x in headers]
        if not all(canonical) or len(canonical) != len(set(canonical)):
            raise ValueError(f"{source}: duplicate or blank headers")
        for number, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f"{source}: unexpected extra columns at row {number}")
            if any(value is not None and str(value).strip() for value in row.values()):
                yield row


@lru_cache(maxsize=128)
def _canonical_uf(value):
    return canonical_state(value)


def _key(row):
    uf = _canonical_uf(row.get("uf"))
    ua = canonical_ua(row.get("ua"))
    return (uf, ua) if uf and ua else None


def _number(value):
    x = float(str(value).strip().replace(",", "."))
    if not math.isfinite(x) or x < 0:
        raise ValueError("invalid nonnegative numeric measurement")
    return x


def prepare(necromass_raw, biomass_raw, necromass_sha256, biomass_sha256):
    hashes = {
        "necromass_source_sha256": hashlib.sha256(necromass_raw).hexdigest(),
        "biomass_source_sha256": hashlib.sha256(biomass_raw).hexdigest(),
    }
    if (hashes["necromass_source_sha256"] != str(necromass_sha256).lower() or
            hashes["biomass_source_sha256"] != str(biomass_sha256).lower()):
        raise ValueError("IFN source SHA256 mismatch")
    biomass = defaultdict(lambda: {"biomes": set(), "typologies": set(), "land": set(),
                                   "sanidade": set(), "coords": set(), "key_equation": False})
    biomass_rows = 0
    excluded = Counter()
    quarantined_ua_aliases = set()
    for row in _rows(biomass_raw, BIOMASS_FIELDS, "biomass"):
        biomass_rows += 1
        try:
            key = _key(row)
        except InvalidUAIdentity:
            try:
                uf = _canonical_uf(row.get("uf"))
            except ValueError:
                uf = ""
            alias = quarantine_ua_alias(row.get("ua"))
            if uf and alias:
                quarantined_ua_aliases.add((uf, alias))
            excluded["biomass_invalid_ua_rows"] += 1
            continue
        except ValueError:
            excluded["biomass_invalid_state_rows"] += 1
            continue
        if key is None:
            excluded["biomass_missing_physical_ua_rows"] += 1
            continue
        entry = biomass[key]
        entry["biomes"].add(str(row["bioma"] or "").strip())
        entry["typologies"].add(str(row["tipologia_da_vegetacao"] or "").strip())
        entry["land"].add(str(row["classe_uso_da_terra"] or "").strip())
        entry["sanidade"].add(str(row["sanidade"] or "").strip())
        if "lon_pc" in row and "lat_pc" in row:
            entry["coords"].add((str(row["lon_pc"]).strip(), str(row["lat_pc"]).strip()))
        entry["key_equation"] |= _identity(row["equacoes"]) == "agb_chave"
    necromass = defaultdict(list)
    necromass_rows = 0
    for row in _rows(necromass_raw, NECRO_FIELDS, "necromass"):
        necromass_rows += 1
        try:
            key = _key(row)
        except InvalidUAIdentity:
            try:
                uf = _canonical_uf(row.get("uf"))
            except ValueError:
                uf = ""
            alias = quarantine_ua_alias(row.get("ua"))
            if uf and alias:
                quarantined_ua_aliases.add((uf, alias))
            excluded["necromass_invalid_ua_rows"] += 1
            continue
        except ValueError:
            excluded["necromass_invalid_state_rows"] += 1
            continue
        if key is None:
            excluded["necromass_missing_physical_ua_rows"] += 1
            continue
        necromass[key].append(row)
    candidates, strata, biome_counts = [], Counter(), Counter()
    for key, records in sorted(necromass.items()):
        if key in quarantined_ua_aliases:
            excluded["ambiguous_physical_ua_control_alias"] += 1
            continue
        if len(records) != 1:
            excluded["duplicate_necromass_physical_ua"] += 1
            continue
        row = records[0]
        try:
            biomass_t_ha = _number(row["necromassa_t_por_ha"])
            # SFB panel metadata describes n_transectos as "Número do
            # transecto", NOT a statistically independent sample count.
            transect_field = str(row["n_transectos"] or "").strip()
            if not transect_field:
                raise ValueError("missing source transect field")
        except (TypeError, ValueError):
            excluded["invalid_necromass_measurement_or_transects"] += 1
            continue
        metadata = biomass.get(key)
        if metadata is None:
            excluded["missing_biomass_metadata"] += 1
            continue
        if (any(len(metadata[field]) != 1 or "" in metadata[field]
                for field in ("biomes", "typologies", "land", "sanidade")) or
                len(metadata["coords"]) > 1 or not metadata["key_equation"]):
            excluded["ambiguous_biomass_ua_metadata"] += 1
            continue
        biome = next(iter(metadata["biomes"]))
        typology = next(iter(metadata["typologies"]))
        land = next(iter(metadata["land"]))
        sanidade = next(iter(metadata["sanidade"]))
        # CSV rows may omit trailing columns. A missing biome is not a
        # mismatch that can be repaired from the tree table: the deadwood
        # observation must independently declare its source biome.
        necromass_biome = str(row.get("bioma") or "").strip()
        if not necromass_biome:
            excluded["missing_necromass_biome"] += 1
            continue
        if biome != necromass_biome:
            excluded["biome_mismatch"] += 1
            continue
        if biome not in BIOMES:
            excluded["outside_five_target_biomes"] += 1
            continue
        if land not in NATIVE_CLASSES or sanidade != "Vivas":
            excluded["not_unambiguously_native_living_tree_metadata"] += 1
            continue
        code = str(row["cod_classe_uso_da_terra"] or "").strip()
        if code not in NATIVE_FOREST_CODE_LAND:
            if not code:
                excluded["missing_necromass_land_code"] += 1
            elif code in OTHER_NATURAL_CODES:
                excluded["natural_nonforest_code_needs_separate_domain"] += 1
            elif code in ANTHROPIC_CODES:
                excluded["planted_or_agricultural_necromass_land_code"] += 1
            else:
                excluded["unverified_necromass_land_code"] += 1
            continue
        if land not in NATIVE_FOREST_CODE_LAND[code]:
            excluded["tree_land_class_incompatible_with_necromass_code"] += 1
            continue
        # Code category is screened against SFB 2024 metadata, but no
        # independently verified transect-to-subplot/IBGE join is implied.
        candidate = {
            "biome": biome, "uf": key[0], "ua": key[1],
            "source_typology_unverified_ibge": typology,
            "source_tree_land_class": land,
            "source_necromass_land_code": code,
            "source_necromass_code_category": "natural_forest_2024_dictionary_provisional",
            "source_n_transectos_uninterpreted": transect_field,
            "necromass_biomass_t_ha": biomass_t_ha,
            "necromass_carbon_tC_ha": None,
            "ibge_spatial_overlay_verified": False,
            "deadwood_transect_land_crosswalk_verified": False,
            "microregional_verified": False,
            "sar_pair_eligible": False,
            "scientifically_validated": False,
        }
        candidates.append(candidate)
        biome_counts[biome] += 1
        strata[(biome, typology, land)] += 1
    report = {
        **hashes, "source_license": "SFB/IFN portal Creative Commons Attribution (verify per resource)",
        "necromass_rows": necromass_rows, "necromass_unique_physical_ua": len(necromass),
        "biomass_equation_rows": biomass_rows, "biomass_unique_physical_ua": len(biomass),
        "candidate_ua": len(candidates), "candidate_ua_by_biome": dict(sorted(biome_counts.items())),
        "ua_control_format_aliases_quarantined": len(quarantined_ua_aliases),
        "candidate_strata": [
            {"biome": b, "source_typology": t, "tree_land_class": land, "candidate_ua": n}
            for (b, t, land), n in sorted(strata.items())
        ], "exclusions": dict(sorted(excluded.items())),
        "ifn_land_code_dictionary_url": IFN_LAND_DICTIONARY,
        "land_code_dictionary_version_compatibility_verified": False,
        "scientific_validation": False, "sar_pair_eligible": False,
        "uncertainty_tC_ha": None, "carbon_stock_tC_ha": None,
        "ibge_fitophysiognomy_verified": False, "transfer_error_quantified": False,
        "warning": "Matched UA and provisional native-forest code only; n_transectos is not treated as sample count. No verified code-version equivalence, deadwood-to-subplot crosswalk, IBGE overlay, carbon fraction, design-based variance, or SAR positional accuracy. Never promote to homologation.",
    }
    return candidates, report


def sources_from_download_audit(audit_path, raw_dir):
    """Resolve only two verified official files; never trust arbitrary audit paths."""
    audit = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    resources = {row["id"]: row for row in audit["resources"]}
    result = []
    for source_id in ("ifn_painel_necromassa_t_ha_2026", "ifn_painel_biomassa_2026"):
        row = resources[source_id]
        expected_filename = source_id + ".csv"
        digest = row.get("sha256", "")
        if (row.get("status") != "downloaded_unvalidated" or
                row.get("local_file") != expected_filename or
                len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest)):
            raise ValueError(f"{source_id}: source audit incomplete or unsafe")
        result.append((Path(raw_dir) / expected_filename, digest))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-audit")
    parser.add_argument("--raw-dir")
    parser.add_argument("--necromass")
    parser.add_argument("--biomass")
    parser.add_argument("--necromass-sha256")
    parser.add_argument("--biomass-sha256")
    parser.add_argument("--audit", required=True)
    parser.add_argument("--candidates", required=True)
    args = parser.parse_args()
    if args.download_audit and args.raw_dir:
        (necromass_path, necromass_sha), (biomass_path, biomass_sha) = sources_from_download_audit(
            args.download_audit, args.raw_dir)
    elif all((args.necromass, args.biomass, args.necromass_sha256, args.biomass_sha256)):
        necromass_path, biomass_path = Path(args.necromass), Path(args.biomass)
        necromass_sha, biomass_sha = args.necromass_sha256, args.biomass_sha256
    else:
        parser.error("provide --download-audit and --raw-dir, or both files and both SHA256 hashes")
    candidates, report = prepare(necromass_path.read_bytes(), biomass_path.read_bytes(),
                                 necromass_sha, biomass_sha)
    Path(args.audit).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.candidates).write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_ua": len(candidates), "scientific_validation": False,
                      "carbon_stock_ready": False}))


if __name__ == "__main__":
    main()
