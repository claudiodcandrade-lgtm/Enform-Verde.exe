"""Contract regressions with synthetic numerical rasters; NOT field accuracy validation."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from soil_fertility_zonal import (ATTRS, analyze_fertility,
                                  discover_coverages, zonal_raster)
from soil_soc_official_uncertainty import discover_official_bounds
from soil_pronasolos_zonal import mapped_soil_0_100_on_polygon
from soil_intersection_report import soil_intersection_lines


class SoilMappedAttributesContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.aoi = gpd.GeoDataFrame(geometry=[box(0, 0, 20, 20)], crs="EPSG:6933")

    def write(self, name, values, transform=None, dtype="float32"):
        p = self.root / name
        a = np.asarray(values, dtype=dtype)
        with rasterio.open(p, "w", driver="GTiff", height=2, width=2, count=1,
                           dtype=dtype, crs="EPSG:6933",
                           transform=transform or from_origin(0, 20, 10, 10),
                           nodata=-9999) as out:
            out.write(a, 1)
        return p

    def test_discovery_requires_numeric_attribute_and_depth(self):
        xml = b"""<Capabilities><Contents>
        <CoverageSummary><CoverageId>geonode__br_90m_ph_0_5cm_v2</CoverageId></CoverageSummary>
        <CoverageSummary><CoverageId>geonode__br_90m_ctc_0_5cm_v2</CoverageId></CoverageSummary>
        <CoverageSummary><CoverageId>geonode__br_90m_phosphorus_0_5cm_v2</CoverageId></CoverageSummary>
        </Contents></Capabilities>"""
        found = discover_coverages(xml)
        self.assertEqual(found[("ph", "0-5")], "geonode__br_90m_ph_0_5cm_v2")
        self.assertEqual(found[("ctc", "0-5")], "geonode__br_90m_ctc_0_5cm_v2")
        self.assertNotIn(("ph", "5-15"), found)

    def test_area_weighted_fertility_not_pixel_centroid_average(self):
        p = self.write("ph.tif", [[5, 8], [5, 8]])
        subset = gpd.GeoDataFrame(geometry=[box(5, 0, 20, 20)], crs=6933)
        stats = zonal_raster(subset, p, attribute="ph", depth="0-5")
        self.assertAlmostEqual(stats["mean"], 7.0, places=5)
        self.assertAlmostEqual(stats["coverage_pct"], 100, places=3)
        self.assertEqual(stats["valid_pixels"], 4)
        self.assertIn("não é", stats["uncertainty"])

    def test_source_confirmed_one_layer_does_not_manufacture_others(self):
        p = self.write("ph.tif", [[5, 8], [5, 8]])
        def fake_download(session, coverage_id, geom, path):
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, path)
            return "f" * 64
        with patch("soil_fertility_zonal._download_coverage", side_effect=fake_download):
            data = analyze_fertility(self.aoi, coverages={("ph", "0-5"): "test_scientific_fixture"},
                                    cache_root=self.root / "cache")
        self.assertEqual(data["status"], "MAPEAMENTO_PREDITIVO_PARCIAL")
        values = data["units"]["PROPRIEDADE — sem atribuição pedológica"]
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["mean"], 6.5)
        self.assertEqual(len(data["layers"]), len(ATTRS)*6)
        self.assertIn("Saturação por bases (V%)", data["unavailable_attributes"])

    def test_wcs_cache_requires_matching_coverage_and_checksum(self):
        from unittest.mock import Mock
        from soil_fertility_zonal import _download_coverage
        source=self.write("fixture.tif",[[5,8],[5,8]])
        destination=self.root/"cache_ph.tif"
        downloaded=[]
        def fake_download(url, dest, session, timeout, attempts=2):
            downloaded.append(url)
            shutil.copyfile(source,dest)
        bounds=(-0.01,-0.01,0.01,0.01)
        with patch("pronasolos_wcs._window_bounds",return_value=bounds), \
             patch("pronasolos_wcs._tiles",return_value=[bounds]), \
             patch("pronasolos_wcs._download",side_effect=fake_download), \
             patch("pronasolos_wcs.validate_tile"):
            _download_coverage(Mock(),"geonode__br_90m_ph_0_5cm_v2",
                               box(-0.01,-0.01,0.01,0.01),destination)
            _download_coverage(Mock(),"geonode__br_90m_ph_0_5cm_v2",
                               box(-0.01,-0.01,0.01,0.01),destination)
            self.assertEqual(len(downloaded),1)
            _download_coverage(Mock(),"geonode__br_90m_ph_0_5cm_v3",
                               box(-0.01,-0.01,0.01,0.01),destination)
            self.assertEqual(len(downloaded),2)
            destination.write_bytes(b"cache altered without metadata update")
            _download_coverage(Mock(),"geonode__br_90m_ph_0_5cm_v3",
                               box(-0.01,-0.01,0.01,0.01),destination)
            self.assertEqual(len(downloaded),3)

    def test_bound_cache_rejects_stale_coverage_identifier(self):
        from unittest.mock import Mock
        from soil_soc_official_uncertainty import fetch_official_bounds
        geom=box(-55,-10,-54.999,-9.999)
        def xml(version):
            elements=[]
            for depth in ("0_5","5_15","15_30","30_60","60_100"):
                for side in ("lower","upper"):
                    suffix=version if depth=="0_5" and side=="lower" else "v2"
                    ident="geonode__br_90m_carbon_stock_"+depth+"cm_uncertainty_"+side+"_"+suffix
                    elements.append("<CoverageSummary><CoverageId>"+ident+"</CoverageId></CoverageSummary>")
            return ("<Capabilities><Contents>"+"".join(elements)+
                    "</Contents></Capabilities>").encode()
        response=Mock()
        response.raise_for_status.return_value=None
        response.content=xml("v2")
        sess=Mock()
        sess.get.return_value=response
        calls=[]
        def save(url,dest,session,timeout,attempts=2):
            calls.append(url)
            Path(dest).write_bytes(("mock WCS "+url).encode())
        bounds=(-55.01,-10.01,-54.99,-9.99)
        with patch("pronasolos_wcs._window_bounds",return_value=bounds), \
             patch("pronasolos_wcs._tiles",return_value=[bounds]), \
             patch("pronasolos_wcs._download",side_effect=save), \
             patch("pronasolos_wcs.validate_tile"):
            out=fetch_official_bounds(geom,session=sess,cache_root=self.root/"bounds")
            self.assertEqual(len(out["provenance"]["layers"]),10)
            self.assertEqual(len(calls),10)
            fetch_official_bounds(geom,session=sess,cache_root=self.root/"bounds")
            self.assertEqual(len(calls),10)
            response.content=xml("v3")
            fetch_official_bounds(geom,session=sess,cache_root=self.root/"bounds")
            self.assertEqual(len(calls),11)

    def test_official_bound_discovery_requires_depth_and_side(self):
        ids = []
        for depth in ("0_5", "5_15", "15_30", "30_60", "60_100"):
            for side in ("lower", "upper"):
                ids.append("<CoverageSummary><CoverageId>geonode__br_90m_carbon_stock_"
                           + depth + "cm_uncertainty_" + side + "</CoverageId></CoverageSummary>")
        found = discover_official_bounds(("<Capabilities><Contents>" + "".join(ids) +
                                          "</Contents></Capabilities>").encode())
        self.assertEqual(len(found), 10)
        self.assertIn(("lower","60-100"), found)

    def test_marginal_bounds_envelope_not_joint_ci(self):
        paths={}
        bounds={"lower":{},"upper":{}}
        for i in range(2,7):
            paths[i]=self.write("stock_"+str(i)+".tif", np.full((2,2),i))
            bounds["lower"][i]=self.write("lower_"+str(i)+".tif", np.full((2,2),i-1))
            bounds["upper"][i]=self.write("upper_"+str(i)+".tif", np.full((2,2),i+1))
        result=mapped_soil_0_100_on_polygon(self.aoi,paths,official_bound_paths=bounds,
                                             official_provenance={"source":"fixture"})
        stock=result["0–100 cm"]
        self.assertAlmostEqual(stock["tc_ha"],20.0)
        official=stock["official_uncertainty"]
        self.assertEqual(official["status"],"ENVELOPE_MARGINAL_OFICIAL")
        self.assertEqual(official["sum_bounds_envelope_tc_ha"],[15.0,25.0])
        self.assertAlmostEqual(official["sum_bounds_envelope_stock_tC"][0],0.6)
        rendered=" ".join(soil_intersection_lines(result))
        self.assertIn("NÃO é IC95%",rendered)

    def test_missing_or_misaligned_uncertainty_preserves_stock(self):
        paths={}
        bounds={"lower":{},"upper":{}}
        for i in range(2,7):
            paths[i]=self.write("stock_"+str(i)+".tif", np.full((2,2),i))
            bounds["lower"][i]=self.write("lower_"+str(i)+".tif", np.full((2,2),i-1))
            bounds["upper"][i]=self.write("upper_"+str(i)+".tif", np.full((2,2),i+1))
        bounds["upper"][6]=self.write("misaligned.tif",np.full((2,2),7),
                                       transform=from_origin(1,20,10,10))
        result=mapped_soil_0_100_on_polygon(self.aoi,paths,official_bound_paths=bounds)
        self.assertAlmostEqual(result["0–100 cm"]["tc_ha"],20.0)
        self.assertEqual(result["0–100 cm"]["official_uncertainty"]["status"],"N/D")
        self.assertFalse(result["0–100 cm"]["predictive_uncertainty_quantified"])


if __name__=="__main__":
    unittest.main()
