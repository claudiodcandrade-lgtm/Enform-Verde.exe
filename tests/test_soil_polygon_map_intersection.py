"""Solo 0–100 cm por interseção polígono × mapa Embrapa/PronaSolos.

Synthetic rasters and mocked HTTP only: numerical/contract regressions, NOT
field validation. The live WCS route was checked manually on 2026-11-03.
"""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Polygon, box

import pronasolos_wcs as wcs
from native_carbon import estimate_native_components, summarize_native_carbon
from soil_intersection_report import soil_intersection_lines, soil_intersection_summary
from soil_pronasolos_zonal import mapped_soil_0_100_on_polygon

PX = wcs.PIXEL_DEG


def geotiff_bytes(values, west, north, crs="EPSG:4326", px=PX, dtype="float32"):
    buf = io.BytesIO()
    arr = np.asarray(values, dtype=dtype)
    with rasterio.MemoryFile() as mem:
        with mem.open(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                      dtype=dtype, crs=crs, transform=from_origin(west, north, px, px),
                      nodata=(-9999 if dtype.startswith("float") else 0)) as dst:
            dst.write(arr, 1)
        buf.write(mem.read())
    return buf.getvalue()


def write_layers(root, grids, west=-55.0, north=-3.0, crs="EPSG:4326"):
    paths = {}
    for lid, grid in zip(range(2, 7), grids):
        p = Path(root) / f"h{lid}.tif"
        p.write_bytes(geotiff_bytes(grid, west, north, crs=crs))
        paths[lid] = p
    return paths


class GeographicExactIntersectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)

    def test_epsg4326_raster_is_accepted_and_matches_supersampled_reference(self):
        # Embrapa publishes EPSG:4326; the former code required a projected CRS
        # and therefore could never use the official rasters.
        rng = np.random.default_rng(7)
        grids = [rng.uniform(5, 40, (30, 30)) for _ in range(5)]
        paths = write_layers(self.tmp.name, grids)
        poly = Polygon([(-54.9990, -3.0010), (-54.9790, -3.0030),
                        (-54.9770, -3.0230), (-54.9960, -3.0200)])
        out = mapped_soil_0_100_on_polygon(gpd.GeoDataFrame(geometry=[poly], crs=4326), paths)
        self.assertEqual(out["_diagnostic"]["target_status"], "COMPLETO_POR_INTERSECAO_RASTER")
        # independent reference: 20×20 supersampling, cos(lat) area weights
        from rasterio.features import geometry_mask
        from shapely.geometry import mapping
        f = 20; T = from_origin(-55.0, -3.0, PX / f, PX / f)
        sub = geometry_mask([mapping(poly)], out_shape=(30 * f, 30 * f), transform=T, invert=True)
        frac = sub.reshape(30, f, 30, f).mean(axis=(1, 3))
        lat = -3.0 - (np.arange(30) + .5) * PX
        w = frac * np.cos(np.radians(lat))[:, None]
        ref = float((np.sum(grids, axis=0) * w).sum() / w.sum())
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"], ref, delta=0.05)
        self.assertIn("0–30 cm", out); self.assertTrue(out["0–30 cm"]["diagnostic_only"])

    def test_nodata_pixels_give_partial_coverage_not_nd_and_not_extrapolated(self):
        grids = [np.full((10, 10), 10.0) for _ in range(5)]
        grids[4][:, :5] = -9999.0                      # west half unmapped in 60–100
        paths = write_layers(self.tmp.name, grids)
        poly = box(-55.0, -3.0 - 10 * PX, -55.0 + 10 * PX, -3.0)
        out = mapped_soil_0_100_on_polygon(gpd.GeoDataFrame(geometry=[poly], crs=4326), paths)
        top = out["0–100 cm"]
        self.assertAlmostEqual(top["tc_ha"], 50.0)
        self.assertTrue(top["partial_coverage"])
        self.assertAlmostEqual(top["coverage_fraction"], 0.5, delta=1e-3)
        self.assertEqual(out["_diagnostic"]["target_status"], "PARCIAL_SEM_EXTRAPOLACAO")
        self.assertTrue(any("COBERTURA PARCIAL" in l for l in soil_intersection_lines(out)))

    def test_all_nodata_is_nd(self):
        grids = [np.full((4, 4), 10.0) for _ in range(4)] + [np.full((4, 4), -9999.0)]
        paths = write_layers(self.tmp.name, grids)
        out = mapped_soil_0_100_on_polygon(
            gpd.GeoDataFrame(geometry=[box(-55.0, -3.0 - 4 * PX, -55.0 + 4 * PX, -3.0)], crs=4326), paths)
        self.assertNotIn("0–100 cm", out)
        self.assertIn("N/D", soil_intersection_lines(out)[0])


class NativeCarbonAreaBasisTests(unittest.TestCase):
    def test_partial_soil_stock_uses_mapped_area_only(self):
        aoi = gpd.GeoDataFrame(geometry=[box(0, 0, 1000, 1000)], crs="EPSG:6933")   # 100 ha
        classes = gpd.GeoDataFrame([{"class_name": "Floresta Ombrófila Densa",
                                     "source": "SAR_VALIDADO+IBGE", "geometry": box(0, 0, 1000, 1000)}],
                                   crs="EPSG:6933")

        def soil(_frame):
            return {"0–100 cm": {"tc_ha": 80.0, "spatial_sd_tc_ha": 5.0, "coverage_fraction": 0.6,
                                 "area_covered_ha": 60.0, "partial_coverage": True,
                                 "profile_pairing": "interseção geométrica exata"}}

        def estimator(frame, physiognomy):
            return estimate_native_components(frame, physiognomy, "Amazônia",
                                              lambda *a, **k: {}, soil)
        res = summarize_native_carbon(aoi, classes, estimator)
        row = next(c for c in res["strata"][0]["components"] if c["parametro"] == "Solo 0–100 cm")
        self.assertAlmostEqual(row["total_tc"], 80.0 * 60.0, places=6)     # not × 100 ha
        self.assertAlmostEqual(row["quantified_area_ha"], 60.0)
        self.assertIn("COBERTURA PARCIAL", row["obs"])
        self.assertFalse(res["strata"][0]["complete"])
        total = next(t for t in res["components"] if t["parametro"] == "Solo 0–100 cm")
        self.assertAlmostEqual(total["quantified_area_ha"], 60.0)
        self.assertAlmostEqual(total["tc_on_quantified_area"], 80.0)


class WcsAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.geom = box(-55.0 + 3 * PX, -3.0 - 8 * PX, -55.0 + 8 * PX, -3.0 - 3 * PX)

    def session(self, body_for, status=200, ctype="image/tiff"):
        s = MagicMock()
        def get(url, timeout=None):
            r = MagicMock(); r.status_code = status; r.headers = {"Content-Type": ctype}
            r.content = body_for(url); r.text = "<ows:ExceptionReport/>"
            return r
        s.get.side_effect = get
        return s

    def ok_body(self, url):
        b = wcs._window_bounds(self.geom)
        n = round((b[2] - b[0]) / PX); m = round((b[3] - b[1]) / PX)
        return geotiff_bytes(np.full((m, n), 12.5), b[0], b[3])

    def test_window_is_snapped_outward_to_published_grid(self):
        b = wcs._window_bounds(self.geom)
        for v in b:
            self.assertAlmostEqual(v / PX, round(v / PX), places=6)
        self.assertLessEqual(b[0], self.geom.bounds[0]); self.assertGreaterEqual(b[2], self.geom.bounds[2])

    def test_large_window_is_tiled(self):
        tiles = list(wcs._tiles((-56.0, -4.0, -54.0, -3.0), max_px=1000))
        self.assertEqual(len(tiles), 3 * 2)

    def test_fetch_writes_hashed_manifest_and_reuses_cache(self):
        s = self.session(self.ok_body)
        got = wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=s)
        self.assertEqual(set(got["paths"]), {2, 3, 4, 5, 6})
        prov = got["provenance"]
        self.assertEqual(prov["unit"], "Mg C/ha"); self.assertIn("CC BY-NC", prov["license"])
        self.assertTrue(all(len(v["sha256"]) == 64 for v in prov["layers"].values()))
        calls = s.get.call_count
        again = wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=s)
        self.assertTrue(again["provenance"]["cache_reused"]); self.assertEqual(s.get.call_count, calls)

    def test_tampered_cache_is_reacquired(self):
        s = self.session(self.ok_body)
        got = wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=s)
        p = got["paths"][6]; p.write_bytes(p.read_bytes()[:-10] + b"0123456789")
        again = wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=s)
        self.assertFalse(again["provenance"]["cache_reused"])

    def test_http_error_and_html_page_fail_closed(self):
        wcs.time.sleep = lambda *_: None
        with self.assertRaises(wcs.WcsAcquisitionError):
            wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=self.session(self.ok_body, status=503))
        with self.assertRaises(wcs.WcsAcquisitionError):
            wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name + "/b",
                               session=self.session(lambda u: b"<html>erro</html>", ctype="text/html"))

    def test_wrong_pixel_size_or_rendered_image_is_rejected(self):
        p = Path(self.tmp.name) / "x.tif"
        p.write_bytes(geotiff_bytes(np.ones((4, 4)), -55, -3, px=0.001))
        with self.assertRaisesRegex(wcs.WcsAcquisitionError, "grade"):
            wcs.validate_tile(p)
        p.write_bytes(geotiff_bytes(np.ones((4, 4)), -55, -3, dtype="uint8"))
        with self.assertRaisesRegex(wcs.WcsAcquisitionError, "renderizada"):
            wcs.validate_tile(p)

    def test_end_to_end_mocked_wcs_then_exact_intersection(self):
        got = wcs.fetch_horizons(self.geom, cache_dir=self.tmp.name, session=self.session(self.ok_body))
        out = mapped_soil_0_100_on_polygon(gpd.GeoDataFrame(geometry=[self.geom], crs=4326), got["paths"])
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"], 5 * 12.5, places=4)
        out["_diagnostic"]["wcs_provenance"] = got["provenance"]
        s = soil_intersection_summary(out)
        self.assertEqual(s["method_code"], "area_weighted_raw_raster_polygon_intersection")
        self.assertAlmostEqual(s["coverage_pct"], 100.0, places=3)


if __name__ == "__main__":
    unittest.main()
