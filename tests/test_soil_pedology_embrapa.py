"""Synthetic geometry only; no claim of validation of Embrapa map accuracy."""
import unittest
import geopandas as gpd
from shapely.geometry import mapping,box
from soil_pedology_embrapa import (intersect_soil_units,analyze_embrapa_pedology,
                                 pedology_report_lines,FERTILITY_LAYERS)
def aoi_rect():return gpd.GeoDataFrame(geometry=[box(-55.1,-11.1,-55,-11)],crs=4326)
class PedologyUnitTests(unittest.TestCase):
    def test_exclusive_intersection_and_association_not_split_into_soils(self):
        a=aoi_rect()
        half=box(-55.1,-11.1,-55.05,-11)
        data={"type":"FeatureCollection","features":[
            {"type":"Feature","geometry":mapping(half),"properties":{
              "leg_desc":"LVd - Latossolos Vermelhos + Argissolos",
              "simbolos":"LVd","comp1":"Latossolos","comp2":"Argissolos"}},
            {"type":"Feature","geometry":mapping(box(-55.075,-11.1,-55,-11)),
             "properties":{"leg_desc":"CX - Cambissolos","simbolos":"CX","comp1":"Cambissolos"}}]}
        result=intersect_soil_units(a,data)
        self.assertEqual(result["status"],"MAPEAMENTO_REGIONAL")
        self.assertAlmostEqual(result["covered_area_ha"],result["area_aoi_ha"],places=5)
        self.assertEqual(len(result["soil_mapping_units"]),2)
        self.assertIsNone(result["area_by_soil_component_ha"])
        self.assertIsNone(result["classification_uncertainty_ha"])
        self.assertIn("SEM divisão individual de área"," ".join(pedology_report_lines(result,lambda v,n:f"{v:.{n}f}")))
    def test_absent_data_or_fetch_failure_remains_nd(self):
        a=aoi_rect()
        self.assertEqual(analyze_embrapa_pedology(a,fetcher=lambda *_:{"features":[]})["status"],"N/D")
        self.assertEqual(analyze_embrapa_pedology(a,fetcher=lambda *_:(_ for _ in ()).throw(OSError("offline")))["status"],"N/D")
    def test_fertility_catalog_does_not_manufacture_vpercent(self):
        self.assertEqual(FERTILITY_LAYERS["ctc_cmolc_kg"]["0–5 cm"],37)
        self.assertEqual(FERTILITY_LAYERS["ph"]["60–100 cm"],48)
        self.assertNotIn("base_saturation_percent",FERTILITY_LAYERS)
    def test_missing_crs_blocks(self):
        a=aoi_rect().set_crs(None,allow_override=True)
        self.assertEqual(analyze_embrapa_pedology(a,fetcher=lambda *_:{"features":[]})["status"],"N/D")
if __name__=="__main__":unittest.main()
