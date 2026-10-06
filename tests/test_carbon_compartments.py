import unittest
from pathlib import Path
from carbon_compartments import ifn_necromass_component, infer_uf_from_aoi, rows_for_compartment, tapajos_litter_stock_component

try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:
    gpd=box=None

DATA=Path(__file__).resolve().parents[1]/"data"/"ifn_necromass_biome_uf_v1.csv"

class CarbonCompartmentTests(unittest.TestCase):
    def test_excel_sheets_select_prefixed_necromass_and_litter_rows(self):
        rows=[
          {"parametro":"Necromassa aérea — referência direta IFN","tc":1.0},
          {"parametro":"Necromassa subterrânea — raízes mortas","tc":None},
          {"parametro":"Serapilheira — estoque de massa seca","tc":2.0},
          {"parametro":"Biomassa aérea","tc":3.0},
        ]
        self.assertEqual(len(rows_for_compartment(rows,"Necromassa")),2)
        self.assertEqual(len(rows_for_compartment(rows,"Serapilheira")),1)
        self.assertEqual(rows_for_compartment(rows,"Biomassa aérea")[0]["tc"],3.0)

    def test_direct_ifn_necromass_uses_biome_and_state_and_preserves_transfer_limit(self):
        r=ifn_necromass_component("Amazônia","Pará",DATA)
        self.assertIsNotNone(r)
        self.assertEqual(r["evidence_type"],"direct_ifn_aboveground_necromass")
        self.assertGreater(r["mean_dry_mg_ha"],0)
        self.assertGreater(r["n_independent_units"],1)
        self.assertFalse(r["include_in_total"])
        self.assertIn("não traz coordenadas nem classe IBGE",r["method"])
        self.assertIsNone(ifn_necromass_component("Pantanal","Mato Grosso do Sul",DATA))
        self.assertIsNone(ifn_necromass_component("Amazônia","São Paulo",DATA))

    @unittest.skipUnless(gpd and box, "geospatial dependencies required")
    def test_uf_intersection_reads_cached_official_shape_and_selects_maximum_overlap(self):
        import json, tempfile
        from shapely.geometry import mapping
        features=[
          {"type":"Feature","properties":{"id":"15"},"geometry":mapping(box(-56,-5,-53,-2))},
          {"type":"Feature","properties":{"id":"13"},"geometry":mapping(box(-70,-10,-60,-2))}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"unidades_federacao_ibge_minima.geojson"
            target.write_text(json.dumps({"type":"FeatureCollection","features":features}),encoding="utf-8")
            target.write_text(target.read_text(encoding="utf-8")+" "*1200,encoding="utf-8")
            aoi=gpd.GeoDataFrame(geometry=[box(-55,-4,-54,-3)],crs="EPSG:4326")
            self.assertEqual(infer_uf_from_aoi(aoi,tmp),"Pará")

    @unittest.skipUnless(gpd and box, "geospatial dependencies required")
    def test_tapajos_standing_litter_stock_is_available_and_geofenced(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-54.984,-3.068,-54.982,-3.065)],crs="EPSG:4326")
        r=tapajos_litter_stock_component("Amazônia","Floresta Ombrófila Densa",aoi)
        self.assertIsNotNone(r)
        self.assertEqual(r["mean_dry_mg_ha"],6.0)
        self.assertEqual(r["range_dry_mg_ha"],[0.0,11.8])
        self.assertEqual(r["evidence_type"],"standing_litter_dry_mass")
        self.assertNotIn("queda anual",r["method"])

    @unittest.skipUnless(gpd and box, "geospatial dependencies required")
    def test_tapajos_litter_does_not_transfer_outside_study_class_or_biome(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-54.96,-3.31,-54.94,-3.29)],crs="EPSG:4326")
        self.assertIsNone(tapajos_litter_stock_component("Amazônia","Floresta Ombrófila Densa",aoi))
        local=gpd.GeoDataFrame(geometry=[box(-54.984,-3.068,-54.982,-3.065)],crs="EPSG:4326")
        self.assertIsNone(tapajos_litter_stock_component("Cerrado","Floresta Ombrófila Densa",local))
        self.assertIsNone(tapajos_litter_stock_component("Amazônia","Savana Arborizada",local))

if __name__=="__main__":
    unittest.main()
