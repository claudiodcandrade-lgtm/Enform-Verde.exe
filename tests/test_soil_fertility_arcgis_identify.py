"""Offline, deterministic contract for official Embrapa numeric MapServer fallback."""
import unittest
from soil_fertility_arcgis_identify import point_values, sample_official_fertility, numeric_result

class SoilIdentifyFallbackTests(unittest.TestCase):
    def test_numeric_pixels_only(self):
        payload={"results":[
            {"layerId":37,"value":"12.75","attributes":{}},
            {"layerId":44,"value":"5.4","attributes":{}},
            {"layerId":45,"value":"#00ff00","attributes":{}},
            {"layerId":23,"value":"NoData","attributes":{}},
            {"layerId":39,"value":"-9999","attributes":{}},
        ]}
        self.assertEqual(point_values(payload),{37:12.75,44:5.4})
        self.assertIsNone(numeric_result({"R":4,"G":1,"B":3}))

    def test_sampled_fertility_is_not_area_weighted_stock(self):
        import geopandas as gpd
        from shapely.geometry import box
        area=gpd.GeoDataFrame(geometry=[box(-58.8,-2.7,-58.79,-2.69)],crs=4326)
        results=sample_official_fertility(area,fetch=lambda lon,lat:{37:10.,44:5.5},max_points=9)
        self.assertEqual(results["status"],"MAPA_PREDITIVO_AMOSTRAL")
        ctc=next(x for x in results["units"]["PROPRIEDADE — AMOSTRA DE PIXELS"] if x["attribute"]=="ctc")
        self.assertEqual(ctc["mean"],10)
        self.assertIsNone(ctc["coverage_pct"])
        self.assertIsNone(ctc["mapped_area_ha"])
        self.assertIsNone(ctc["raster_sha256"])
        self.assertIsNone(results["ic95"])

if __name__=="__main__":
    unittest.main()
