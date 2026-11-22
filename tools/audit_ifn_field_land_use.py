#!/usr/bin/env python3
"""Cross-check IFN 2025 FIELD subplot forest-cover flags with 2026 PANEL UAs.

This is a temporal/source-consistency audit, NOT native-cover confirmation,
IBGE fitophysiognomy validation, plot-pixel SAR calibration or a carbon estimate.
Each physical UF+UA counts once; subplots/equations are never independent UAs.
"""
import argparse
import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from tools.ifn_state_identity import canonical_state, canonical_ua
from tools.audit_ifn_panel_biome_coverage import (NATIVE_SOURCE_LAND_CLASSES,
                                                 TARGET_BIOMES, SOURCE_CRS_DECLARED)

SOURCES = {
    "ifn_uso_terra_mato_grosso_2025": "MT",
    "ifn_uso_terra_mato_grosso_do_sul_2025": "MS",
    "ifn_uso_terra_para_2025": "PA",
}
FIELD_COLUMNS = {"bioma", "uf", "ua", "sub", "subp", "cobertura_florestal", "uso_da_terra"}
CANDIDATE_COLUMNS = {"uf", "ua", "bioma_declarado", "classe_nativa_declarada",
                     "legenda_1_ibge_verificada", "par_sar_validado",
                     "estoque_carbono_validado", "precisao_geografica_de_campo_verificada",
                     "crs_fonte_documentado"}
ALLOWED_CANDIDATE_BIOMES = frozenset(normalized_name.casefold() for normalized_name in TARGET_BIOMES)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalized(value):
    return unicodedata.normalize("NFKC", str(value or "")).strip().casefold()


def _headers(values, required):
    labels = [normalized(v) for v in values]
    if not all(labels) or len(labels) != len(set(labels)) or not required.issubset(labels):
        raise ValueError("missing, blank or ambiguous IFN source columns")
    return {name: labels.index(name) for name in required}


def load_candidates(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        _headers(reader.fieldnames or [], CANDIDATE_COLUMNS)
        seen = {}
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("malformed IFN candidate CSV")
            key = (canonical_state(row["uf"]), canonical_ua(row["ua"]))
            if not all(key) or key in seen:
                raise ValueError("missing or duplicated physical UF+UA candidate")
            biome = normalized(row["bioma_declarado"])
            if biome not in ALLOWED_CANDIDATE_BIOMES:
                raise ValueError("candidate source has missing or unexpected biome")
            if normalized(row["classe_nativa_declarada"]) not in NATIVE_SOURCE_LAND_CLASSES:
                raise ValueError("candidate source lacks a consistent provisional native land-use class")
            if normalized(row["crs_fonte_documentado"]) != normalized(SOURCE_CRS_DECLARED):
                raise ValueError("candidate source CRS differs from documented panel metadata")
            if any(normalized(row[name]) != "false" for name in (
                    "legenda_1_ibge_verificada", "par_sar_validado",
                    "estoque_carbono_validado", "precisao_geografica_de_campo_verificada")):
                raise ValueError("unvalidated candidate source cannot assert IBGE/SAR/field/carbon validation")
            seen[key] = biome
    if not seen:
        raise ValueError("empty IFN candidate CSV")
    return seen


def load_subplots(paths):
    from openpyxl import load_workbook  # only the observational workflow installs it
    by_ua = defaultdict(lambda: {"biomes": set(), "flags": set(), "codes": set(),
                                  "subplots": set(), "duplicate": False, "unresolved": False})
    source_rows = Counter()
    for source_id, path in sorted(paths.items()):
        expected_uf = SOURCES[source_id]
        wb = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            if len(wb.worksheets) != 1:
                raise ValueError("unexpected IFN field workbook sheet count")
            rows = wb.worksheets[0].iter_rows(values_only=False)
            header = next(rows, None)
            if header is None:
                raise ValueError("empty IFN field workbook")
            columns = _headers([c.value for c in header], FIELD_COLUMNS)
            for cells in rows:
                if not any(c.value is not None for c in cells):
                    continue
                if any(c.data_type == "f" for c in cells):
                    raise ValueError("formula cell cannot be field observation")
                def field(name):
                    i = columns[name]
                    return normalized(cells[i].value) if i < len(cells) else ""
                uf = canonical_state(field("uf"))
                if uf != expected_uf:
                    raise ValueError("field record UF conflicts with licensed state file")
                ua = canonical_ua(field("ua"))
                if not ua:
                    raise ValueError("field record missing physical UA")
                key = (uf, ua)
                info = by_ua[key]
                info["biomes"].add(field("bioma"))
                sub, subp = field("sub"), field("subp")
                if not sub or not subp or sub == "na" or subp == "na":
                    info["unresolved"] = True
                else:
                    subplot = (sub, subp)
                    if subplot in info["subplots"]:
                        info["duplicate"] = True
                    info["subplots"].add(subplot)
                flag = field("cobertura_florestal")
                info["flags"].add(flag if flag in {"s", "n"} else "N/D")
                code = field("uso_da_terra")
                info["codes"].add(code if code and code != "na" else "N/D")
                source_rows[source_id] += 1
        finally:
            wb.close()
    return by_ua, dict(source_rows)


def audit(candidate_path, source_paths, download_report):
    candidates = load_candidates(candidate_path)
    resources = {r["id"]: r for r in download_report["resources"]}
    if set(source_paths) != set(SOURCES) or not set(SOURCES).issubset(resources):
        raise ValueError("incomplete licensed field source set")
    hashes = {}
    for sid, path in source_paths.items():
        rec = resources[sid]
        if (rec.get("status") != "downloaded_unvalidated"
                or rec.get("validated_file_extension") != ".xlsx"):
            raise ValueError("field source missing, failed or not XLSX: " + sid)
        actual = digest(path)
        if actual != rec.get("sha256"):
            raise ValueError("field source SHA256 mismatch: " + sid)
        hashes[sid] = actual
    field, source_rows = load_subplots(source_paths)
    by_biome = defaultdict(Counter)
    matched = 0
    for key, biome in candidates.items():
        c = by_biome[biome]
        c["candidate_physical_ua"] += 1
        if key not in field:
            c["no_matching_field_ua"] += 1
            continue
        matched += 1
        info = field[key]
        c["matched_physical_ua"] += 1
        if (len(info["biomes"]) != 1 or biome not in info["biomes"]
                or info["duplicate"] or info["unresolved"]):
            c["field_identity_or_biome_unresolved"] += 1
            continue
        if info["flags"] == {"s"}:
            c["all_recorded_subplots_forest_S"] += 1
        elif info["flags"] == {"n"}:
            c["all_recorded_subplots_forest_N"] += 1
        elif "N/D" in info["flags"]:
            c["missing_or_uninterpretable_forest_flag"] += 1
        else:
            c["mixed_forest_S_N_subplots"] += 1
    # Field-only UAs (notably Pantanal) must remain visible even if the
    # modeled 2026 panel has no candidate there. Count UF+UA once; never
    # treat subplot S/N as a native-cover or carbon observation.
    field_by_biome = defaultdict(Counter)
    field_ua_unresolved_biome = 0
    for key, info in field.items():
        labels = info["biomes"]
        if len(labels) != 1 or next(iter(labels)) not in ALLOWED_CANDIDATE_BIOMES:
            field_ua_unresolved_biome += 1
            continue
        biome = next(iter(labels))
        counts = field_by_biome[biome]
        counts["field_physical_ua"] += 1
        if key not in candidates:
            counts["field_ua_without_panel_candidate"] += 1
        elif candidates[key] != biome:
            counts["field_ua_with_panel_biome_disagreement"] += 1
        else:
            counts["field_ua_with_same_biome_panel_candidate"] += 1
        if info["duplicate"] or info["unresolved"]:
            counts["field_subplot_identity_unresolved"] += 1
        elif info["flags"] == {"s"}:
            counts["all_recorded_subplots_forest_S"] += 1
        elif info["flags"] == {"n"}:
            counts["all_recorded_subplots_forest_N"] += 1
        elif "N/D" in info["flags"]:
            counts["missing_or_uninterpretable_forest_flag"] += 1
        else:
            counts["mixed_forest_S_N_subplots"] += 1
    if (sum(c["field_physical_ua"] for c in field_by_biome.values())
            + field_ua_unresolved_biome != len(field)):
        raise AssertionError("field physical UA biome counts do not reconcile")
    return {
        "type": "IFN_2025_field_subplots_vs_2026_panel_UA_descriptive_NOT_homologation",
        "source_license": "Creative Commons Attribution (official SFB 2025 field land-use dataset)",
        "source_dataset": "https://dados.florestal.gov.br/dataset/ifn-uso-da-terra-por-uf_disp-set2025",
        "source_metadata": "https://dados.florestal.gov.br/pt_BR/dataset/8b8e2ad3-eb97-485b-aa68-842c82602f47/resource/0f4ff89c-30cf-4dfd-9b19-3bc77327c917/download/metadados_ifn_uso-da-terra_disp-set2025.pdf",
        "source_years_from_metadata": "2011-2024; field date per row N/D",
        "field_xlsx_sha256": dict(sorted(hashes.items())),
        "panel_candidate_csv_sha256": digest(candidate_path),
        "field_rows_by_state_source": source_rows,
        "field_unique_physical_ua": len(field),
        "field_ua_with_unresolved_or_unrecognized_biome": field_ua_unresolved_biome,
        "field_physical_ua_by_declared_biome_including_without_panel": {
            b: dict(sorted(c.items())) for b, c in sorted(field_by_biome.items())
        },
        "panel_candidate_unique_physical_ua": len(candidates),
        "matched_unique_physical_ua": matched,
        "candidate_native_label_and_all_validation_flags_strictly_checked": True,
        "candidate_crs_documented_not_field_accuracy": SOURCE_CRS_DECLARED,
        "by_declared_biome": {b: dict(sorted(c.items())) for b, c in sorted(by_biome.items())},
        "subparcel_codes_are_not_native_cover_classes": True,
        "field_forest_flag_is_not_proof_of_native_vegetation": True,
        "field_ua_identity_is_not_independent_geolocation": True,
        "field_vs_panel_temporal_comparability_validated": False,
        "independent_fitophysiognomy_ibge_validation": False,
        "field_to_sar_plot_pixel_pairs_validated": False,
        "transfer_error": None,
        "carbon_stock_tC_ha": None,
        "confidence_interval_95": None,
        "scientific_validation": False,
        "warning": "A physical UF+UA is counted once, regardless of number of subplots. "
                   "Field forest S/N is NOT a native/non-native classification: savannas "
                   "and natural grasslands may be nonforest. Field 2011-2024 and panel "
                   "2026 have no independently matched per-row dates or positions. "
                   "Do not infer current land cover, IBGE class, SAR pairs, transfer "
                   "error, biomass or carbon from these descriptive counts."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-csv", required=True)
    p.add_argument("--raw-dir", required=True)
    p.add_argument("--download-audit", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    report = json.loads(Path(a.download_audit).read_text(encoding="utf-8"))
    paths = {sid: Path(a.raw_dir) / (sid + ".xlsx") for sid in SOURCES}
    result = audit(a.candidate_csv, paths, report)
    Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"field_ua": result["field_unique_physical_ua"],
                      "matched_physical_ua": result["matched_unique_physical_ua"],
                      "validated": False}))


if __name__ == "__main__":
    main()
