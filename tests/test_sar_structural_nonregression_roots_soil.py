"""Non-regression: SAR canopy/AGB additions must not replace allometric roots
or Embrapa Solos/PronaSolos exact 0-100 cm soil mapping.

Synthetic values only; not independent accuracy evidence.
"""
import unittest
import geopandas as gpd
from shapely.geometry import box
from native_carbon import estimate_native_components
from root_allometry_uncertainty import cairns_root_prediction
from soil_pronasolos_zonal import DEPTHS, mapped_soil_0_100_on_polygon
from native_sar_structural_agb import agb_sar_crown_inventory_contract


class MandatoryCarbonPoolNonRegression(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(-55,-4,-54.999,-3.999)],crs="EPSG:4326")

    def test_roots_stay_allometric_and_soil_stays_0_100_map(self):
        sar=lambda *args: {
            "agb_mg_ha":100.0,"data_origin":"SAR_HEIGHT_INVENTORY_STRUCTURAL",
            "source":"synthetic SAR fixture"}
        calls=[]
        def soil(frame):
            calls.append(frame)
            return {"0–30 cm":{"tc_ha":9.0},
                    "0–100 cm":{"tc_ha":57.0,"coverage_fraction":1.0,
                                 "profile_pairing":"cinco horizontes mesmo pixel; interseção geométrica"}}
        result=estimate_native_components(
            self.aoi,"Floresta Ombrófila Densa","Amazônia",sar,soil)
        rows={x["parametro"]:x for x in result["components"]}
        self.assertEqual(len(calls),1)
        self.assertIn("Biomassa subterrânea",rows)
        self.assertEqual(rows["Biomassa subterrânea"]["origem"],"MODELAGEM_ALOMETRIA")
        self.assertAlmostEqual(rows["Biomassa subterrânea"]["tc"],
                               cairns_root_prediction(100.0)["mean_model_tc_ha"])
        self.assertEqual(rows["Solo 0–100 cm"]["tc"],57.0)
        self.assertEqual(rows["Solo 0–100 cm"]["origem"],"MAPEAMENTO")
        self.assertIn("Embrapa Solos/PronaSolos",rows["Solo 0–100 cm"]["fonte"])
        self.assertNotIn("Solo 0–30 cm",rows)

    def test_missing_soil_100cm_is_never_replaced_by_shallow_0_30(self):
        r=estimate_native_components(self.aoi,"Floresta Ombrófila Densa",
                "Amazônia",lambda *_:{"agb_mg_ha":100.0,"data_origin":"SAR_TEST"},
                lambda *_:{"0–30 cm":{"tc_ha":19.0},
                           "_diagnostic":{"target_status":"INCOMPLETO_NAO_EXTRAPOLAR"}})
        row=next(x for x in r["components"] if x["parametro"]=="Solo 0–100 cm")
        self.assertIsNone(row["tc"])
        self.assertFalse(row["include_in_total"])

    def test_pronasolos_depths_exactly_five_ending_100(self):
        self.assertEqual([d for _,d in DEPTHS],
                         ["0-5","5-15","15-30","30-60","60-100"])
        r=mapped_soil_0_100_on_polygon(self.aoi,{})
        self.assertFalse(r["_diagnostic"]["target_0_100_available"])

    def test_structural_agb_cannot_overwrite_roots_or_soil(self):
        result=agb_sar_crown_inventory_contract(None,None,None,None,
                 biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        self.assertIsNone(result["agb_mg_ha"])
        self.assertNotIn("root_carbon_tc_ha",result)
        self.assertNotIn("soil_stock_tc_ha",result)


if __name__=="__main__":
    unittest.main()
