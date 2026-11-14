#!/usr/bin/env python3
"""Train a TerraClass map-agreement SAR experiment; never certifies field accuracy."""
from __future__ import annotations
import argparse
import json
from terraclass_sar_experiment import train_spatial_map_agreement


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True, help="co-registered SAR feature GeoTIFF")
    parser.add_argument("--reference", required=True, help="official TerraClass vector file")
    parser.add_argument("--label-field", required=True, help="TerraClass legend text field")
    parser.add_argument("--domain", choices=("amazonia", "cerrado"), required=True)
    parser.add_argument("--reference-year", type=int, required=True)
    parser.add_argument("--feature-year", type=int, required=True)
    parser.add_argument("--model", required=True, help="output experimental .joblib")
    parser.add_argument("--report", required=True, help="output map-agreement .json")
    parser.add_argument("--block-size-m", type=float, default=5000)
    args = parser.parse_args(argv)
    result = train_spatial_map_agreement(
        args.features, args.reference, args.model, args.report,
        label_field=args.label_field, domain=args.domain,
        reference_year=args.reference_year, feature_year=args.feature_year,
        block_size_m=args.block_size_m,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
