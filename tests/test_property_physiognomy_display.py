import unittest
from property_physiognomy_display import format_property_physiognomies
def fmt(x,n=2):return f"{x:.{n}f}".replace(".",",")
class NativeFitoAreaTests(unittest.TestCase):
    def test_mixed_aoi_native_intersection_not_100_percent_ibge(self):
        r={"area_aoi_ha":1459.91,"strata":[{"physiognomy":"Floresta Estacional Sempre-Verde","area_ha":917.81,"source":"IBGE+MAPBIOMAS"}]}
        text=format_property_physiognomies(r,fmt)
        self.assertIn("Floresta Estacional Sempre-Verde: 917,81 ha (62,87%",text)
        self.assertNotIn("1.459,91 ha",text)
        self.assertIn("MAPEADA",text)
    def test_multiple_formations_and_nodata_area(self):
        r={"area_aoi_ha":1000,"unknown_cover_area_ha":100,"strata":[
          {"physiognomy":"Floresta","area_ha":300,"source":"IBGE+MAPBIOMAS"},
          {"physiognomy":"Savana","area_ha":200,"source":"SAR_VALIDADO+IBGE"}]}
        text=format_property_physiognomies(r,fmt)
        self.assertIn("Floresta: 300,00 ha (30,00%",text)
        self.assertIn("Savana: 200,00 ha (20,00%",text)
        self.assertIn("100,00 ha (10,00%",text)
    def test_without_cover_no_guess(self):
        self.assertIn("Não determinada",format_property_physiognomies(
           {"area_aoi_ha":1459.91,"strata":[]},fmt))
    def test_equal_area_matches_native_denominator(self):
        import geopandas as gpd
        from shapely.geometry import box
        from property_physiognomy_display import equal_area_aoi_ha
        aoi=gpd.GeoDataFrame(geometry=[box(-55.88,-12.57,-55.87,-12.56)],crs=4326)
        expected=float(aoi.to_crs(6933).geometry.union_all().area)/10000
        self.assertAlmostEqual(equal_area_aoi_ha(aoi),expected,places=8)
        with self.assertRaises(ValueError):
            equal_area_aoi_ha(None)
if __name__=="__main__":unittest.main()
