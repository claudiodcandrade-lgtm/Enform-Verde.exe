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
        helper=next(f for f in ast.walk(tree) if isinstance(f,ast.FunctionDef)
                    and f.name=="_read_optical_cog_quadrants")
        helper_source=ast.get_source_segment(SOURCE.read_text(encoding="utf-8"),helper)
        self.assertIn("reproject(",helper_source)
        self.assertIn("src.read(",helper_source)
        self.assertIn("resize",calls)
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="transform" for n in ast.walk(fn)))
        self.assertIn("isfinite",calls)
        literals=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant)
                  and isinstance(n.value,str)]
        self.assertTrue(any("pixels RGB válidos" in value for value in literals))
        self.assertTrue(any("Nenhuma das" in value for value in literals))
        self.assertIn("_read_optical_cog_quadrants(",ast.get_source_segment(SOURCE.read_text(encoding="utf-8"),fn))
        self.assertIn("OPTICAL_MAX_SCENE_CANDIDATES",ast.get_source_segment(SOURCE.read_text(encoding="utf-8"),fn))

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
        self.assertLess(body.index("nasa_gibs_preview(", body.index("def worker():")), body.index("im=esri_export(rs,service="))
        self.assertLess(body.index("if cached_optical:"),body.index("nasa_gibs_preview("))
        self.assertNotIn("offline_brazil_preview",body)

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
        self.assertIn("_read_optical_cog_quadrants",cbers)
        self.assertIn("_fetch_stac_features_paged",src)
        self.assertNotIn("_draw_offline_brazil_basemap",body)

    def test_black_or_blank_optical_pixels_are_rejected_before_canvas_delivery(self):
        src=SOURCE.read_text(encoding="utf-8")
        self.assertIn("def _require_visible_optical_image(image,provider):",src)
        self.assertIn("p99<20.0 or spread<5.0 or visible_fraction<0.15",src)
        self.assertIn("optical_pixels=pixels[~overlay]",src)
        self.assertIn("IBGE_POTENTIAL_FALLBACK",src)
        self.assertIn("load_ibge_land_use_reference(g)",src)
        tree=ast.parse(src)
        fn=next(n for n in ast.walk(tree)
                if isinstance(n,ast.FunctionDef) and n.name=="show_google_map")
        body=ast.get_source_segment(src,fn)
        self.assertIn("_require_visible_optical_image(p.get(\"image\")",body)
        for call in ("cbers4a_wfi_preview(","sentinel2_earthsearch_preview(",
                     "sentinel2_preview(","nasa_gibs_preview("):
            pos=body.index(call)
            self.assertIn("_require_visible_optical_image",body[pos:pos+350],call)

    def test_black_optical_image_is_rejected_and_visible_image_is_accepted(self):
        from PIL import Image
        from desktop_app import _require_visible_optical_image
        with self.assertRaisesRegex(RuntimeError,"preta/em branco"):
            _require_visible_optical_image(Image.new("RGB",(32,32),(0,0,0)),"CBERS test")
        visible=Image.new("RGB",(32,32),(45,82,57))
        for x in range(16,32):
            for y in range(32):visible.putpixel((x,y),(150,175,95))
        self.assertIs(_require_visible_optical_image(visible,"CBERS test"),visible)

    def test_windows_gui_fixture_has_spatial_texture_required_by_pixel_gate(self):
        workflow=(SOURCE.parent/".github"/"workflows"/"build-windows.yml").read_text(encoding="utf-8")
        start=workflow.index("def synthetic_optical_preview(gdf,out_w=1000")
        end=workflow.index("app.cbers4a_wfi_preview=synthetic_optical_preview",start)
        fixture=workflow[start:end]
        self.assertIn("Image.fromarray",fixture)
        self.assertIn("np.indices",fixture)
        self.assertNotIn('Image.new("RGB",(int(out_w),int(out_h)),(34,104,71))',fixture)

    def test_preview_reads_are_split_into_bounded_quadrants(self):
        from desktop_app import OPTICAL_COG_TILE_SIZE,_iter_optical_quadrants
        self.assertEqual(OPTICAL_COG_TILE_SIZE,512)
        tiles=list(_iter_optical_quadrants(1024,768))
        self.assertEqual(len(tiles),4)
        self.assertTrue(all(w<=512 and h<=512 for _,_,w,h in tiles))
        covered={(x+dx,y+dy) for x,y,w,h in tiles for dx in range(w) for dy in range(h)}
        self.assertEqual(len(covered),1024*768)

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
