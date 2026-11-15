import ast
import unittest
from pathlib import Path


class StacPaginationTests(unittest.TestCase):
    def test_follows_next_page_for_full_aoi_scene_discovery(self):
        source = (Path(__file__).resolve().parents[1] / "desktop_app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                  and n.name == "_fetch_stac_features_paged")
        body = ast.get_source_segment(source, fn)
        self.assertIn('x.get("rel")=="next"', body)
        self.assertIn('features.extend(page)', body)
        self.assertIn('requests.post(link["href"]', body)
        self.assertIn('requests.get(link["href"]', body)

    def test_respects_page_limit(self):
        source = (Path(__file__).resolve().parents[1] / "desktop_app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                  and n.name == "_fetch_stac_features_paged")
        body = ast.get_source_segment(source, fn)
        self.assertIn("while pages<max_pages", body)
        self.assertIn('pages+=1', body)


if __name__ == "__main__":
    unittest.main()
