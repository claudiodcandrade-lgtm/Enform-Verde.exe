import unittest
try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:
    gpd=box=None

from national_fallback import national_agb_fallback, inventory_fallback_gate
import sar_pipeline as sar

class NationalFallbackTests(unittest.TestCase):
    def test_inventory_fallback_gate_requires_confirmed_sar_unavailability(self):
        self.assertTrue(inventory_fallback_gate(False,[])["eligible"])
        self.assertTrue(inventory_fallback_gate(False,["Sentinel-1: sem pixels processados"])["eligible"])
        self.assertFalse(inventory_fallback_gate(True,[])["eligible"])
        self.assertFalse(inventory_fallback_gate(False,["Earthdata authentication rejected"])["eligible"])

    def test_all_scoped_biomes_always_return_agb_and_uncertainty(self):
        cases=[
          ("Amazônia","Floresta Ombrófila Aberta"),
          ("Cerrado","Savana Arborizada"),
          ("Caatinga","Savana-Estépica Arborizada"),
          ("Mata Atlântica","Floresta Estacional Semidecidual"),
        ]
        for biome,phys in cases:
            r=national_agb_fallback(biome,phys)
            self.assertTrue(r and r["available"],(biome,phys,r))
            self.assertGreater(r["agb_mg_ha"],0)
            lo,hi=r["agb_range_mg_ha"]
            self.assertLessEqual(lo,r["agb_mg_ha"])
            self.assertGreaterEqual(hi,r["agb_mg_ha"])
            self.assertGreater(hi-lo,0)
            self.assertEqual(r["data_origin"],"MODELAGEM_LITERATURA_HIERARQUICA")
            self.assertIn("não é validação SAR",r["uncertainty_kind"])

    def test_more_specific_physiognomy_changes_fallback(self):
        dense=national_agb_fallback("Amazônia","Floresta Ombrófila Densa")
        openf=national_agb_fallback("Amazônia","Floresta Ombrófila Aberta")
        self.assertNotEqual(dense["agb_mg_ha"],openf["agb_mg_ha"])
        semidec=national_agb_fallback("Mata Atlântica","Floresta Estacional Semidecidual")
        secondary=national_agb_fallback("Mata Atlântica","Floresta secundária em regeneração")
        self.assertNotEqual(semidec["agb_mg_ha"],secondary["agb_mg_ha"])

    @unittest.skipUnless(gpd and box,"geospatial dependencies required")
    def test_tapajos_necromass_not_inferred_from_literature_or_mixed_roots(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-54.95,-3.07,-54.94,-3.06)],crs="EPSG:4326")
        r=sar.literature_fallback("Amazônia","Floresta Ombrófila Densa",aoi=aoi)
        self.assertTrue(r and r["available"])
        components=r.get("regional_components") or {}
        self.assertNotIn("Biomassa subterrânea",components)
        self.assertFalse(any(name.startswith("Necromassa") for name in components))
        self.assertIn("Serapilheira — estoque no piso florestal",components)
        self.assertIn("forest floor",components["Serapilheira — estoque no piso florestal"]["method"].lower())
        self.assertNotIn("produtividade/queda anual",components["Serapilheira — estoque no piso florestal"]["method"])

    @unittest.skipUnless(gpd and box,"geospatial dependencies required")
    def test_pipeline_withholds_inventory_agb_after_processed_sar_without_model(self):
        g=gpd.GeoDataFrame(geometry=[box(-47.96,-15.98,-47.94,-15.96)],crs="EPSG:4326")
        real=(sar.maap_search,sar.discover_asf,sar.planetary_alos_palsar,sar.planetary_sentinel1_cog,sar.public_sentinel1_cog,sar.cci_history)
        try:
            sar.maap_search=lambda *a,**k:[]
            sar.discover_asf=lambda *a,**k:[]
            sar.planetary_alos_palsar=lambda *a,**k:{"items":1,"scene_ids":["L"],"paths":[],"stats":[{"scene":"L","polarization":"HH","n":12,"pixel_state":"PROCESSADO"}],"errors":[],"provider":"test","pixel_state":"PROCESSADO"}
            sar.planetary_sentinel1_cog=lambda *a,**k:{"items":1,"scene_ids":["C"],"paths":[],"stats":[{"scene":"C","polarization":"VV","n":12,"pixel_state":"PROCESSADO"}],"errors":[],"provider":"test","pixel_state":"PROCESSADO"}
            sar.public_sentinel1_cog=lambda *a,**k:{"items":0,"paths":[],"stats":[],"errors":[],"provider":"test"}
            sar.cci_history=lambda *a,**k:{"items":0,"paths":[]}
            out=sar.automatic_pipeline(g,"Cerrado","Savana Arborizada",cache="test_cache_national")
            self.assertEqual(out["status"],"SAR_PROCESSADO_SEM_MODELO_AGB")
            self.assertIsNone(out["literature_reference"])
            self.assertIsNone(out["agb_mg_ha"])
            self.assertFalse(out["inventory_fallback_gate"]["eligible"])
            self.assertIn("não será substituída",out["message"])
        finally:
            sar.maap_search,sar.discover_asf,sar.planetary_alos_palsar,sar.planetary_sentinel1_cog,sar.public_sentinel1_cog,sar.cci_history=real

if __name__=="__main__":
    unittest.main()
