#!/usr/bin/env python3
"""Cross-state AGB transfer diagnostics from real IFN/SFB *candidate* sampling UAs.

This is NOT SAR validation, an IBGE-fitophysiognomy crosswalk, a plot-to-pixel
match, an AOI stock, a predictive CI, or proof of independently measured AGB.
The IFN panel's AGB_Chave values are published *model-derived* inventory
estimates. A state-blocked holdout can measure descriptive transfer error
against those values, not true field measurement or satellite error.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

from tools.ifn_state_identity import canonical_state, canonical_ua

REQUIRED = (
    "bioma", "uf", "ua", "tipologia_da_vegetacao", "classe_uso_da_terra",
    "agb_mg_ha", "source_equation", "equation_choice_audited",
    "ibge_fitophysiognomy_verified", "sar_pair_eligible",
    "scientifically_validated",
)
BIOMES = {"Amazônia", "Caatinga", "Cerrado", "Mata Atlântica", "Pantanal"}


def evaluate(raw, expected_sha256, *, raw_ifn_sha256):
    """Leave-one-UF-out transfer error by EXACT source IFN typology.

    Each training UF contributes one state mean to the transferred predictor,
    so a state with many IFN units does not dominate other training states.
    Every test UF is withheld completely; no IFN UA appears in both sides.
    At least three states, three training UAs, and two test UAs per fold are
    required. No distributional assumption or arbitrary interval is imposed.
    """
    digest = hashlib.sha256(raw).hexdigest()
    if digest.lower() != str(expected_sha256).lower():
        raise ValueError("candidate CSV SHA256 mismatch")
    if not isinstance(raw_ifn_sha256, str) or len(raw_ifn_sha256) != 64 or any(
        c not in "0123456789abcdefABCDEF" for c in raw_ifn_sha256
    ):
        raise ValueError("raw official IFN source SHA256 is required")
    try:
        decoded = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("candidate CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = reader.fieldnames or []
    if (not set(REQUIRED).issubset(headers) or len(headers) != len(set(headers))
            or any(not str(name or "").strip() for name in headers)):
        raise ValueError("missing, duplicate or blank candidate headers")
    by_group = defaultdict(lambda: defaultdict(list))
    seen = set()
    total = 0
    for i, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"row {i}: malformed candidate CSV")
        if not any(row.values()):
            continue
        total += 1
        biome = row["bioma"].strip()
        typology = row["tipologia_da_vegetacao"].strip()
        if biome not in BIOMES or not typology:
            raise ValueError(f"row {i}: unsupported or missing sampling domain")
        uf = canonical_state(row["uf"])
        ua = canonical_ua(row["ua"])
        if not ua:
            raise ValueError(f"row {i}: blank physical UA")
        physical = (uf, ua)
        if physical in seen:
            raise ValueError(f"row {i}: duplicated physical UF+UA across source rows")
        seen.add(physical)
        # The upstream deduplicator has NOT independently audited the chosen
        # equation, IBGE class or plot/SAR position. Do not silently promote it.
        if (row["source_equation"].strip() != "AGB_Chave"
                or any(row[key].strip().casefold() != "false" for key in (
                    "equation_choice_audited", "ibge_fitophysiognomy_verified",
                    "sar_pair_eligible", "scientifically_validated"
                ))):
            raise ValueError(f"row {i}: candidates cannot claim audited model or SAR validation")
        try:
            agb = float(row["agb_mg_ha"])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"row {i}: invalid AGB") from exc
        if not math.isfinite(agb) or agb < 0:
            raise ValueError(f"row {i}: AGB must be finite and nonnegative")
        by_group[(biome, typology)][uf].append((ua, agb))
    if total == 0:
        raise ValueError("no candidate UAs")
    strata = []
    all_test = []
    for (biome, typology), by_state in sorted(by_group.items()):
        states = sorted(by_state)
        folds = []
        # A two-state cross-validation merely swaps one state for another:
        # do not treat this as a robust transfer error across Brazilian UFs.
        if len(states) >= 3:
            for test_uf in states:
                test = by_state[test_uf]
                training = {uf: by_state[uf] for uf in states if uf != test_uf}
                n_train = sum(len(rows) for rows in training.values())
                if len(test) < 2 or n_train < 3:
                    continue
                # Equal-state-weight training mean; do not allow large UFs to
                # overwhelm smaller ones. Still not a design-based IFN mean.
                state_means = [sum(v for _, v in rows) / len(rows)
                               for rows in training.values()]
                predicted = sum(state_means) / len(state_means)
                errors = [predicted - obs for _, obs in test]
                folds.append({
                    "held_out_uf": test_uf,
                    "train_ufs": sorted(training),
                    "train_ua_count": n_train,
                    "test_ua_count": len(test),
                    "train_ua_ids": sorted(f"{uf}:{ua}" for uf, rows in training.items()
                                           for ua, _ in rows),
                    "test_ua_ids": sorted(f"{test_uf}:{ua}" for ua, _ in test),
                    "mean_predicted_agb_mg_ha": predicted,
                    "rmse_mg_ha": math.sqrt(sum(e * e for e in errors) / len(errors)),
                    "mae_mg_ha": sum(abs(e) for e in errors) / len(errors),
                    "bias_mg_ha": sum(errors) / len(errors),
                })
                all_test.append((biome, typology, test_uf, errors))
        n_units = sum(len(v) for v in by_state.values())
        if folds:
            # Equal held-out UF weight, not repeated equation/plot row weight.
            rmse = math.sqrt(sum(f["rmse_mg_ha"] ** 2 for f in folds) / len(folds))
            mae = sum(f["mae_mg_ha"] for f in folds) / len(folds)
            bias = sum(f["bias_mg_ha"] for f in folds) / len(folds)
        else:
            rmse = mae = bias = None
        strata.append({
            "biome": biome,
            "ifn_source_typology": typology,
            "ibge_fitophysiognomy_verified": False,
            "source_state_count": len(states),
            "source_ua_count": n_units,
            "heldout_state_count": len(folds),
            "heldout_ua_count": sum(f["test_ua_count"] for f in folds),
            "transfer_rmse_mg_ha": rmse,
            "transfer_mae_mg_ha": mae,
            "transfer_bias_mg_ha": bias,
            "transfer_error_status": "descriptive_cross_state_diagnostic" if folds else "not_available",
            "folds": folds,
            "can_use_for_aoi_carbon": False,
            "sar_validation": False,
            "ci95": None,
        })
    return {
        "status": "diagnostic_not_scientifically_homologated",
        "candidate_csv_sha256": digest,
        "raw_official_ifn_sha256_claim": raw_ifn_sha256.lower(),
        "raw_official_ifn_bytes_verified_by_this_tool": False,
        "candidate_ua_count": total,
        "strata_count": len(strata),
        "strata_with_transfer_diagnostic": sum(bool(s["folds"]) for s in strata),
        "heldout_state_folds": sum(len(s["folds"]) for s in strata),
        "strata": strata,
        "sampling_unit": "unique canonical (UF, UA)",
        "transfer_design": "leave-one-UF-out; equal training-UF means; equal held-out-UF metric weighting",
        "uncertainty_kind": "observed model-to-model discrepancy against IFN panel AGB_Chave; not SAR predictive error",
        "limitations": (
            "IFN AGB_Chave is allometrically modelled from inventory, not a "
            "direct independent SAR or carbon measurement. Published coordinates "
            "are rounded, positional accuracy unverified. Source IFN typology is "
            "NOT an IBGE fitophysiognomy. Training/test UFs are distinct but "
            "allometric equation validity, sampling design, ecological transfer, "
            "spatial/temporal dependence, AOI applicability and any prediction "
            "interval coverage are not independently validated. No CI95 or "
            "per-AOI estimate; no release-gate evidence promotion."
        ),
        "scientifically_homologated": False,
        "is_sar_validation": False,
        "is_aoi_ci95": False,
        "independent_prediction_interval_coverage": None,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate-csv", required=True)
    p.add_argument("--candidate-sha256", required=True)
    p.add_argument("--raw-ifn-sha256", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    result = evaluate(Path(args.candidate_csv).read_bytes(),
                      args.candidate_sha256,
                      raw_ifn_sha256=args.raw_ifn_sha256)
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "candidate_ua_count", "strata_count", "strata_with_transfer_diagnostic",
        "heldout_state_folds", "scientifically_homologated"
    )}, ensure_ascii=False))


if __name__ == "__main__":
    main()
