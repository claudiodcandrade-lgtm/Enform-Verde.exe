"""Regression: joint stock IC needs explicit, valid covariance for all pools."""
import math
import unittest
import geopandas as gpd
from shapely.geometry import box
from native_carbon import COMPARTMENTS, summarize_native_carbon

class DeclaredNativeTotalUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs="EPSG:6933")
        self.classes=gpd.GeoDataFrame(
            [{"class_name":"Floresta Ombrófila Densa",
              "source":"IBGE+MAPBIOMAS","geometry":box(0,0,100,100)}],
            crs="EPSG:6933")
        self.covariance=[[1.0 if i==j else 0.0 for j in range(6)] for i in range(6)]
    def estimate(self,frame,phys):
        return {"components":[{"parametro":name,"tc":float(i+1)}
                              for i,name in enumerate(COMPARTMENTS)]}
    def test_no_false_total_ci_from_marginal_stocks(self):
        result=summarize_native_carbon(self.aoi,self.classes,self.estimate)
        self.assertIsNone(result["total_uncertainty"])
        self.assertTrue(result["complete"])
    def test_explicit_covariance_enables_normal_approximation_only(self):
        r=summarize_native_carbon(self.aoi,self.classes,self.estimate,
                                  covariance_tc2_ha2=self.covariance)
        u=r["total_uncertainty"]
        self.assertAlmostEqual(u["stock_tC"],21.,places=5)
        self.assertAlmostEqual(u["se_tC"],math.sqrt(6.),places=5)
        self.assertFalse(u["coverage_validated"])
        self.assertEqual(len(u["order"]),6)
        self.assertEqual(u["order"][0]["compartimento"],COMPARTMENTS[0])
    def test_missing_pool_blocks_joint_interval(self):
        def incomplete(frame,phys):
            return {"components":[{"parametro":COMPARTMENTS[0],"tc":1.}]}
        with self.assertRaisesRegex(ValueError,"completos"):
            summarize_native_carbon(self.aoi,self.classes,incomplete,
                                    covariance_tc2_ha2=self.covariance)
    def test_incompatible_covariance_dimension_blocks_joint_interval(self):
        with self.assertRaisesRegex(ValueError,"dimension"):
            summarize_native_carbon(self.aoi,self.classes,self.estimate,
                                    covariance_tc2_ha2=[[1.]])
if __name__ == "__main__":
    unittest.main()
