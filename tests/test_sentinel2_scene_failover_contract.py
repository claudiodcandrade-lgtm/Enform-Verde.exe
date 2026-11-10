"""Sentinel-2 visual fallback safety: never treat a catalog hit as loaded pixels."""
import ast
import pathlib
import unittest

SOURCE=pathlib.Path(__file__).resolve().parents[1]/"desktop_app.py"

class Sentinel2SceneFailoverContract(unittest.TestCase):
    def test_real_pixels_and_multiple_scenes_required(self):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
        funcs=[f for f in ast.walk(tree) if isinstance(f,ast.FunctionDef)
               and f.name=="sentinel2_earthsearch_preview"]
        self.assertEqual(len(funcs),1)
        fn=funcs[0]
        calls=[n.func.attr for n in ast.walk(fn) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute)]
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="reproject" for n in ast.walk(fn)))
        self.assertIn("read",calls)
        self.assertIn("resize",calls)
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="transform" for n in ast.walk(fn)))
        self.assertIn("isfinite",calls)
        literals=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant)
                  and isinstance(n.value,str)]
        self.assertTrue(any("pixels RGB válidos" in value for value in literals))
        self.assertTrue(any("Nenhuma das" in value for value in literals))
        # Distinct source band windows, not reusing red's exact pixel window.
        self.assertIn("win=from_bounds(",ast.get_source_segment(SOURCE.read_text(encoding="utf-8"),fn))

    def test_satellite_background_uses_verified_sources_then_nasa_visual_fallback(self):
        src=SOURCE.read_text(encoding="utf-8")
        tree=ast.parse(src)
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)
                and n.name=="show_google_map")
        body=ast.get_source_segment(src,fn)
        # CBERS-first, then Sentinel-2 Earth Search and Planetary Computer,
        # then NASA VIIRS for visual context only.
        positions=[body.index(name) for name in ("cbers4a_wfi_preview(","sentinel2_earthsearch_preview(",
                                                  "sentinel2_preview(","nasa_gibs_preview(")]
        self.assertEqual(positions,sorted(positions))
        calls=[n.func.id for n in ast.walk(fn) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Name)]
        self.assertIn("nasa_gibs_preview",calls)
        self.assertIn("esri_export", calls)
        self.assertLess(nasa if "nasa" in locals() else body.index("nasa_gibs_preview("), source.index("esri_export(") if "source" in locals() else body.index("esri_export("))
        self.assertLess(body.index("nasa_gibs_preview("),body.index("offline_brazil_preview("))
        self.assertIn("contingência sem imagem óptica",body)

    def test_each_optical_route_requires_real_pixels_over_the_aoi(self):
        src=SOURCE.read_text(encoding="utf-8")
        tree=ast.parse(src)
        names={"sentinel2_earthsearch_preview","sentinel2_preview","cbers4a_wfi_preview"}
        bodies={n.name:ast.get_source_segment(src,n) for n in ast.walk(tree)
                if isinstance(n,ast.FunctionDef) and n.name in names}
        self.assertEqual(set(bodies),names)
        for name,body in bodies.items():
            self.assertIn("aoi_coverage<0.95",body,name+" must reject partial-AOI imagery")
        cbers=bodies["cbers4a_wfi_preview"]
        self.assertIn("aoi_coverage_fraction",cbers)
        self.assertIn("_fetch_stac_features_paged",src)
        self.assertNotIn("_draw_offline_brazil_basemap",body)

    def test_cbers_4a_uses_official_rgb_cogs_and_clear_mask(self):
        src=SOURCE.read_text(encoding="utf-8")
        tree=ast.parse(src)
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)
                and n.name=="cbers4a_wfi_preview")
        body=ast.get_source_segment(src,fn)
        for value in ("https://data.inpe.br/bdc/stac/v1/search","CB4A-WFI-L4-SR-1",
                      "BAND15","BAND14","BAND13","CMASK","mask==127",
                      "resolution_m\":55"):
            self.assertIn(value,body)
        self.assertIn("reproject",body)
        self.assertIn("valid.sum()",body)

if __name__=="__main__":
    unittest.main()
