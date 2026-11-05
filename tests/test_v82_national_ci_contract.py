"""UI must never show IBGE potential as current native forest."""
import unittest
from pathlib import Path
from national_analysis_audit import audit_national_coverage

ROOT=Path(__file__).resolve().parents[1]
class NationalCIContractTests(unittest.TestCase):
    def test_real_brazil_islands_are_in_aoi_plausibility_envelope(self):
        import geopandas as gpd
        from shapely.geometry import box
        islands={"Fernando de Noronha":(-32.43,-3.84),
                 "Trindade":(-29.32,-20.52),"São Pedro e São Paulo":(-29.35,0.93)}
        for label,(lon,lat) in islands.items():
            with self.subTest(place=label):
                a=gpd.GeoDataFrame(geometry=[box(lon,lat,lon+.002,lat+.002)],crs=4326)
                ha=float(a.to_crs(6933).geometry.union_all().area)/10000
                r=audit_national_coverage(a,{"classes":[{"class_name":"Não classificada",
                    "area_ha":ha,"native_status":None,"source":"SEM_COBERTURA"}]})
                self.assertTrue(r["brazil_bbox_plausible"])
                self.assertEqual(r["current_sar_observation"],"N/D")
    def test_ibge_potential_only_in_separate_diagnostic(self):
        src=(ROOT/"desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("Fitofisionomia presente na propriedade:",src)
        self.assertIn("Código(s) das regiões fitoecológicas",src)
        self.assertIn("format_property_physiognomies",src)
        self.assertIn("POTENCIAL IBGE",src)
    def test_workflows_group_by_sha_and_never_cancel_doc_build(self):
        for file in ("build-windows.yml","dashboard-dual-tests.yml"):
            s=(ROOT/".github"/"workflows"/file).read_text(encoding="utf-8")
            self.assertIn("github.event.pull_request.head.sha || github.sha",s)
            self.assertIn("cancel-in-progress: false",s)
if __name__=="__main__":unittest.main()
