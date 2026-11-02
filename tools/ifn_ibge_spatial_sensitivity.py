#!/usr/bin/env python3
"""IFN/SFB published-centroid x IBGE legenda_1 spatial sensitivity; NOT validation.

Source coordinates have unknown FIELD positional accuracy. Scenario radii
are NOT estimated errors, confidence regions, or SAR plot-pixel tolerances.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from pyproj import Geod
from shapely.geometry import Point, Polygon
from shapely import make_valid
from shapely.ops import unary_union
from shapely.strtree import STRtree

GEOD = Geod(ellps="WGS84")
RADII_M = (0, 250, 1000)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def geodesic_disc(lon, lat, radius_m, vertices=128):
    """Polygonal geodesic-disc approximation, never a positional error bound."""
    if not math.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius must be positive and finite")
    bearings = [i * 360 / vertices for i in range(vertices)]
    lons, lats, _ = GEOD.fwd([lon] * vertices, [lat] * vertices,
                             bearings, [radius_m] * vertices)
    return Polygon(zip(lons, lats))



def sanitize_official_ibge(polygons, labels):
    """Quarantine unclassified/invalid features; never silently assign a class."""
    if len(polygons) != len(labels):
        raise ValueError("IBGE geometry/legend lengths differ")
    kept, names = [], []
    stats = Counter()
    for geom, label in zip(polygons, labels):
        if geom is None or geom.is_empty:
            stats["missing_or_empty_geometry"] += 1
            continue
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            stats["nonpolygon_geometry"] += 1
            continue
        name = label.strip() if isinstance(label, str) else ""
        if not name:
            name = "N/D"
            stats["missing_legenda_1_quarantined"] += 1
        if not geom.is_valid:
            stats["invalid_geometry_quarantined"] += 1
            geom = make_valid(geom)
            if geom.geom_type == "GeometryCollection":
                polys = [g for g in geom.geoms
                         if g.geom_type in ("Polygon", "MultiPolygon")]
                geom = unary_union(polys) if polys else None
            if (geom is None or geom.is_empty
                    or geom.geom_type not in ("Polygon", "MultiPolygon")):
                stats["invalid_geometry_without_polygon"] += 1
                continue
            name = "N/D"  # Repaired geometries cannot prove IBGE class.
        kept.append(geom)
        names.append(name)
    if not kept:
        raise ValueError("IBGE has no usable polygon footprint")
    return kept, names, dict(stats)


class IbgeSensitivity:
    def __init__(self, polygons, labels):
        if not polygons or len(polygons) != len(labels):
            raise ValueError("nonempty polygon and legenda_1 arrays required")
        for geometry, label in zip(polygons, labels):
            if (geometry is None or geometry.is_empty or not geometry.is_valid
                    or geometry.geom_type not in ("Polygon", "MultiPolygon")
                    or not isinstance(label, str) or not label.strip()):
                raise ValueError("invalid IBGE polygon or empty legenda_1")
        self.polygons = list(polygons)
        self.labels = [x.strip() for x in labels]
        self.tree = STRtree(self.polygons)

    def evaluate(self, lon, lat, radii_m=RADII_M):
        if (not math.isfinite(lon) or not math.isfinite(lat)
                or not -180 <= lon <= 180 or not -90 <= lat <= 90
                or (lon == 0 and lat == 0)):
            raise ValueError("invalid/unresolved published coordinates")
        if (not radii_m or radii_m[0] != 0
                or any(not math.isfinite(r) or r < 0 for r in radii_m)):
            raise ValueError("radii must start at zero and be finite/nonnegative")
        point = Point(lon, lat)
        point_ids = [int(i) for i in self.tree.query(point)
                     if self.polygons[int(i)].covers(point)]
        point_labels = {self.labels[i] for i in point_ids}
        point_label = next(iter(point_labels)) if len(point_labels) == 1 and "N/D" not in point_labels else None
        stability = {}
        for radius in radii_m:
            if radius == 0:
                stability["0"] = bool(point_label and len(point_ids) == 1)
                continue
            disc = geodesic_disc(lon, lat, radius)
            indices = [int(i) for i in self.tree.query(disc)
                       if self.polygons[int(i)].intersects(disc)]
            labels = {self.labels[i] for i in indices}
            if not point_label or labels != {point_label}:
                stable = False
            else:
                stable = unary_union([self.polygons[i] for i in indices]).covers(disc)
            stability[str(radius)] = bool(stable)
        return {
            "legenda_1_no_centroide_publicado": point_label or "N/D",
            "multiplas_feicoes_ibge_no_centroide": len(point_ids) != 1,
            "estabilidade_geometrica_cenarios_m": stability,
            "posicao_campo_verificada": False,
            "tipologia_campo_ibge_validada": False,
            "erro_posicional_m": "N/D",
            "erro_transferencia": "N/D",
            "par_sar_validado": False,
            "homologado": False,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifn-csv", required=True)
    parser.add_argument("--ibge-vector", required=True,
                        help="Official IBGE ZIP or GeoPackage with legenda_1")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    import geopandas as gpd

    source = Path(args.ibge_vector)
    if source.suffix.lower() not in (".zip", ".gpkg"):
        parser.error("IBGE must be a single hashable ZIP or GeoPackage")
    if not source.is_file():
        parser.error("IBGE vector missing")
    ifn = Path(args.ifn_csv)
    if not ifn.is_file():
        parser.error("IFN candidate CSV missing")
    vector = gpd.read_file("zip://" + str(source.resolve())
                           if source.suffix.lower() == ".zip" else source)
    if vector.crs is None:
        parser.error("IBGE vector CRS missing; never assume WGS84")
    fields = [name for name in vector.columns
              if str(name).strip().casefold() == "legenda_1"]
    if len(fields) != 1:
        parser.error("IBGE legenda_1 missing or ambiguous")
    original_crs = str(vector.crs)
    vector = vector.to_crs("EPSG:4326")
    polygons, labels, ibge_qc = sanitize_official_ibge(
        vector.geometry.tolist(), vector[fields[0]].tolist())
    engine = IbgeSensitivity(polygons, labels)

    with ifn.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"uf", "ua", "lon_pc_publicado", "lat_pc_publicado"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            parser.error("IFN candidate columns missing")
        rows = list(reader)
    if not rows:
        parser.error("IFN candidate CSV empty")
    seen = set()
    counts = Counter()
    for row in rows:
        key = (row["uf"], row["ua"])
        if key in seen:
            parser.error("duplicate physical IFN UF+UA; reject pseudo-replication")
        seen.add(key)
        result = engine.evaluate(float(row["lon_pc_publicado"].replace(",", ".")),
                                 float(row["lat_pc_publicado"].replace(",", ".")))
        row["ibge_legenda_1_centroide_publicado_nao_validado"] = result["legenda_1_no_centroide_publicado"]
        for radius, stable in result["estabilidade_geometrica_cenarios_m"].items():
            row[f"estavel_cenario_{radius}_m_nao_erro"] = str(stable).lower()
            if stable:
                counts[f"stable_{radius}_m"] += 1
        row["posicao_campo_verificada"] = "false"
        row["ibge_fitofisionomia_campo_validada"] = "false"
        row["erro_posicional_m"] = "N/D"
        row["erro_transferencia"] = "N/D"
        row["apto_calibracao_sar"] = "false"
        if result["legenda_1_no_centroide_publicado"] != "N/D":
            counts["point_label_present"] += 1

    output = Path(args.output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "type": "IFN_IBGE_published_centroid_geometric_sensitivity_NOT_validation",
        "ifn_candidate_sha256": sha256(ifn),
        "ibge_vector_sha256": sha256(source),
        "output_csv_sha256": sha256(output),
        "ifn_physical_ua": len(rows),
        "counts": dict(counts),
        "radii_m_scenarios_not_errors": list(RADII_M),
        "ibge_crs_original": original_crs,
        "ibge_geometry_quarantine": ibge_qc,
        "ibge_source_polygon_completeness_verified": not any(ibge_qc.values()),
        "field_positional_accuracy": None,
        "transfer_error": None,
        "independent_field_ibge_validation": False,
        "sar_plot_pixel_validation": False,
        "carbon_homologation": False,
        "warning": "IFN published centroid field accuracy unknown. IBGE legenda_1 "
                   "at published coordinates and arbitrary 250/1000 m scenarios "
                   "do NOT validate field position, fitophysiognomy, native cover, "
                   "SAR, or transfer error. Geodesic discs are polygonal approximations."
    }
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"screened_physical_ua": len(rows), "validated": False}))


if __name__ == "__main__":
    main()
