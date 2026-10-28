"""Native-carbon AOI coverage and farm-stratum scientific regression gates."""
import unittest
import geopandas as gpd
from shapely.geometry import box

from native_carbon import COMPARTMENTS, estimate_native_components, summarize_native_carbon


class NativeAoiCoverageGapTests(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs="EPSG:6933")
        self.native=dict(class_name="Floresta Ombrófila Densa",
                         source="IBGE+MAPBIOMAS",geometry=box(0,0,40,100))
    def estimate(self,frame,phys):
        return {"components":[{"parametro":name,"tc":10., "fonte":"SYNTHETIC"}
                              for name in COMPARTMENTS]}

    def test_unclassified_area_cannot_be_misreported_as_full_coverage(self):
        classes=gpd.GeoDataFrame([self.native],crs="EPSG:6933")
        result=summarize_native_carbon(self.aoi,classes,self.estimate)
        self.assertAlmostEqual(result["native_area_ha"],.4)
        self.assertAlmostEqual(result["unmapped_aoi_area_ha"],.6)
        self.assertAlmostEqual(result["unknown_cover_area_ha"],.6)
        self.assertAlmostEqual(result["known_total_tc"],24.0) # 6 pools x 10 tC/ha x 0.4 ha
        self.assertEqual(result["cover_completeness"],"PARTIAL_OR_UNKNOWN")
        self.assertFalse(result["complete"])
        self.assertIsNone(result["total_uncertainty"])

    def test_explicit_pasture_class_removes_false_unknown_gap(self):
        classes=gpd.GeoDataFrame([self.native,{
            "class_name":"Pastagem","source":"MAPBIOMAS",
            "geometry":box(40,0,100,100)}],crs="EPSG:6933")
        result=summarize_native_carbon(self.aoi,classes,self.estimate)
        self.assertAlmostEqual(result["native_area_ha"],.4)
        self.assertAlmostEqual(result["excluded_other_uses_ha"],.6)
        self.assertEqual(result["unmapped_aoi_area_ha"],0.)
        self.assertEqual(result["unknown_cover_area_ha"],0.)
        self.assertEqual(result["cover_completeness"],"COMPLETE")
        self.assertTrue(result["complete"])

    def test_unknown_gap_rejects_total_interval_even_with_supplied_covariance(self):
        classes=gpd.GeoDataFrame([self.native],crs="EPSG:6933")
        cov=[[1.0 if i==j else 0. for j in range(6)] for i in range(6)]
        with self.assertRaisesRegex(ValueError,"cobertura nativa"):
            summarize_native_carbon(self.aoi,classes,self.estimate,
                                    covariance_tc2_ha2=cov)


class SantoAmbrosioNativeStratumIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.parent=gpd.GeoDataFrame(
            geometry=[box(-49.60,-.12,-49.41,.045)],crs="EPSG:4326")
        self.forest=gpd.GeoDataFrame(
            geometry=[box(-49.56,-.09,-49.50,-.04)],crs="EPSG:4326")

    def analyze(self,stratum,phys,**kwargs):
        return estimate_native_components(
            stratum,phys,"Amazônia",lambda *args:{},lambda *args:{},**kwargs)

    def test_full_farm_provenance_can_support_small_matching_forest_stratum(self):
        no_parent=self.analyze(self.forest,"Floresta Ombrófila Densa")
        self.assertFalse(any(x["parametro"]=="Serapilheira"
                             for x in no_parent["components"]))
        with_parent=self.analyze(self.forest,"Floresta Ombrófila Densa",
                                 property_aoi=self.parent)
        litter=[row for row in with_parent["components"]
                if row["parametro"]=="Serapilheira"]
        self.assertEqual(len(litter),1)
        self.assertAlmostEqual(litter[0]["tc"],14.3876*.47,places=5)
        self.assertIn("transferência",litter[0]["obs"])
        self.assertTrue(litter[0]["fonte"].startswith("Inventário da Fazenda"))

    def test_no_transfer_to_savanna_or_neighboring_property(self):
        savanna=self.analyze(self.forest,"Savana Arborizada",property_aoi=self.parent)
        self.assertFalse(any(r["parametro"]=="Serapilheira"
                             for r in savanna["components"]))
        neighboring=gpd.GeoDataFrame(
            geometry=[box(-49.62,-.08,-49.58,-.05)],crs="EPSG:4326")
        outside=self.analyze(neighboring,"Floresta Ombrófila Densa",
                             property_aoi=self.parent)
        self.assertFalse(any(r["parametro"]=="Serapilheira"
                             for r in outside["components"]))


if __name__=="__main__":
    unittest.main()
