#!/usr/bin/env python3
"""End-to-end EXPERIMENTAL model test for one AOI (owner policy 09/11/2026:
defensible experimental models now, field accuracy later).

Chain: Sentinel-1 SAR classifier on AOI + 8 km ring → land use/crops in the AOI
→ per-crop field vs. peer fields of the same crop in the ring (relative vigor,
RVI proxy if no height) → calibrated PAM-panel yield forecast with vigor
→ JSON + text report. Private geometry is never written to the repository.

Usage:
  python tools/test_models_aoi.py --bbox W S E N --phytoregion "Floresta Estacional Sempre-Verde" [--as-of 2026-11-09]
  python tools/test_models_aoi.py --vector fazenda.kml --phytoregion "..." --out relatorio.json
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def summarize_class_areas(rows, min_area_ha=0.05):
    """Sum hectares across every polygon of each class; never overwrite duplicates."""
    totals = {}
    for class_name, area_ha in rows:
        if area_ha > min_area_ha:
            totals[str(class_name)] = totals.get(str(class_name), 0.0) + float(area_ha)
    return {name: round(value, 1) for name, value in totals.items()}


def crop_field_key(crop, field_number):
    """One report entry per field, even for repeated crop labels."""
    return f"{crop}__field_{field_number}"


def run(aoi, phytoregion, as_of, ring_km=8.0):
    import geopandas as gpd
    from crop_forecast_pipeline import forecast_fields, forecast_lines
    from crop_vigor_auto import automatic_vigor
    from sar_landcover_lemplus import classify_aoi, in_validated_domain
    report = {"as_of": as_of.isoformat(), "phytoregion": phytoregion, "crops": {}}
    ib = aoi.copy(); ib["legenda_1"] = phytoregion
    ok, msg = in_validated_domain(ib, "legenda_1", aoi)
    report["domain"] = msg
    aoi_eq = aoi.to_crs(6933)
    ring = gpd.GeoDataFrame(geometry=[aoi_eq.geometry.union_all().buffer(ring_km * 1000)], crs=6933)
    res = classify_aoi(ring.to_crs(4326), as_of=as_of)
    report["classifier"] = {k: v for k, v in res.items() if k not in ("polygons_6933", "classes")}
    polys = res.get("polygons_6933")
    if polys is None or polys.empty:
        report["status"] = "N/D — classificador SAR sem resultado"
        return report
    inside = polys.clip(aoi_eq)
    inside["area_ha"] = inside.area / 1e4
    report["aoi_classes_ha"] = summarize_class_areas(
        (r.class_name, r.area_ha) for r in inside.itertuples()
    )
    lines = ["TESTE EXPERIMENTAL DE MODELOS — " + msg,
             "Classificação SAR (safra " + str(res.get("season")) + ", " + str(res.get("scenes_used")) + " cenas):"]
    lines += [f"  {k}: {v:.1f} ha" for k, v in sorted(report["aoi_classes_ha"].items(), key=lambda kv: -kv[1])]
    for field_number, r in enumerate(inside.itertuples(), start=1):
        if not str(r.class_name).startswith("Lavoura de ") or r.area_ha < 5:
            continue
        crop = r.class_name.replace("Lavoura de ", "")
        field = gpd.GeoDataFrame(geometry=[r.geometry], crs=6933).to_crs(4326)
        peers = polys[polys.class_name == r.class_name].overlay(aoi_eq, how="difference").explode(index_parts=False)
        peers = peers[peers.area / 1e4 >= 5].reset_index(drop=True)
        peers["class_name"] = r.class_name
        vig = automatic_vigor(field, as_of, crop, reference_gdf=peers.to_crs(4326), ring_km=ring_km)
        entry = {"area_ha": round(r.area_ha, 1), "peer_fields": int(len(peers)),
                 "vigor": {k: vig.get(k) for k in ("status", "class", "probabilities", "size_basis", "reason",
                                                    "scene_id", "acquisition_utc", "reference_fields")}}
        lines.append(f"• {crop} ({r.area_ha:.1f} ha; {len(peers)} talhões vizinhos da mesma cultura no raio de {ring_km:g} km)")
        if vig.get("status") == "experimental":
            p = ", ".join(f"{k} {100 * v:.0f}%" for k, v in vig["probabilities"].items())
            lines.append(f"  Vigor: {vig['class']} ({p}); base de tamanho: {vig.get('size_basis')}; cena {str(vig.get('acquisition_utc'))[:10]}")
        else:
            lines.append("  Vigor: N/D — " + str(vig.get("reason")))
        try:
            rep = forecast_fields([{"id": crop, "gdf": field, "crop": crop, "identification": {"label_allowed": True},
                                    "vigor": vig, "area_ha": r.area_ha}], as_of=as_of)
            entry["forecast"] = {"status": rep.get("status"), "model": rep.get("model"),
                                 "production": rep.get("production")}
            lines += ["  " + x for x in forecast_lines(rep)]
        except Exception as exc:
            entry["forecast"] = {"status": "N/D", "reason": type(exc).__name__ + ": " + str(exc)[:200]}
            lines.append("  Previsão: N/D — " + entry["forecast"]["reason"])
        # Preserve individual fields: the crop label alone is not a unique key.
        report["crops"][crop_field_key(crop, field_number)] = {"crop": crop, **entry}
    report["text"] = lines
    return report


def main():
    import geopandas as gpd
    from shapely.geometry import box
    ap = argparse.ArgumentParser()
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--bbox", nargs=4, type=float)
    source.add_argument("--vector")
    ap.add_argument("--phytoregion", required=True); ap.add_argument("--as-of")
    ap.add_argument("--out")
    a = ap.parse_args()
    aoi = (gpd.read_file(a.vector).to_crs(4326) if a.vector else
           gpd.GeoDataFrame(geometry=[box(*a.bbox)], crs=4326))
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    rep = run(aoi, a.phytoregion, as_of)
    print("\n".join(rep.get("text", [rep.get("status", "")])))
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
