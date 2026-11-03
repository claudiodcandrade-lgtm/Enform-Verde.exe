"""Synthetic regression: experimental soil never becomes known certified carbon."""
import unittest

import geopandas as gpd
from shapely.geometry import box

from native_carbon import summarize_native_carbon
from executive_carbon_report import executive_carbon_lines, uncertainty_for_pool


class ExperimentalCarbonSeparationTests(unittest.TestCase):
    def test_aoi_total_excludes_experimental_soil_but_displays_separately(self):
        area=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs="EPSG:6933")
        classes=gpd.GeoDataFrame([{
            "class_name":"Floresta Ombrófila Densa",
            "source":"IBGE+MAPBIOMAS",
            "geometry":box(0,0,100,100),
        }],crs="EPSG:6933")

        def synthetic_estimator(frame, physiognomy):
            return {"components":[{
                "parametro":"Solo 0–100 cm",
                "tc":64.8,
                "origem":"EXPERIMENTAL_FISICO",
                "range_tc_ha":[24.0,126.0],
                "scientifically_homologated":False,
                "include_in_total":False,
            }]}

        result=summarize_native_carbon(area,classes,synthetic_estimator)
        self.assertIsNone(result["known_total_tc"])
        self.assertAlmostEqual(result["experimental_only_total_tc"],64.8,delta=5e-7)
        self.assertAlmostEqual(result["experimental_only_total_tco2"],64.8*44/12,delta=1e-6)
        self.assertFalse(result["complete"])
        soil=next(c for c in result["strata"][0]["components"]
                  if c["parametro"]=="Solo 0–100 cm")
        self.assertAlmostEqual(soil["experimental_total_tc"],64.8,delta=1e-6)
        self.assertIsNone(soil["total_tc"])
        self.assertFalse(soil["include_in_total"])
        self.assertFalse(soil["scientifically_homologated"])
        lines=executive_carbon_lines(result,lambda x:f"{x:.2f}")
        self.assertTrue(any("Subtotal APENAS EXPERIMENTAL" in line for line in lines))
        self.assertTrue(any("CENÁRIOS FÍSICOS" in line for line in lines))
        self.assertTrue(any("NÃO é IC95%" in line for line in lines))

    def test_numerical_scenario_range_is_not_observed_uncertainty(self):
        row={"tc":64.8,"origem":"EXPERIMENTAL_FISICO",
             "range_tc_ha":[24.0,126.0]}
        val=uncertainty_for_pool(row)
        self.assertIsNone(val["absolute_tc_ha"])
        self.assertIsNone(val["percent"])
        self.assertEqual(val["scenario_range_tc_ha"],[24.0,126.0])
        self.assertIn("NÃO é IC95%",val["kind"])


if __name__=="__main__":
    unittest.main()
