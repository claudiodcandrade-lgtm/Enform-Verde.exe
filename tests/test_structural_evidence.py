import unittest
from structural_evidence import StructuralEvidence, evidence_se, random_effects_summary, harmonize_primary_plot_rows, harmonize_ifn_dap10_rows

class StructuralEvidenceTests(unittest.TestCase):
    def test_aggregate_results_never_become_synthetic_plots(self):
        rows=[
          StructuralEvidence("A","Inst","Cerrado","Savana","GO","AGB","Mg/ha",mean=20,sd=5,n_plots=25),
          StructuralEvidence("B","Inst","Cerrado","Savana","DF","AGB","Mg/ha",mean=30,ci95_low=25,ci95_high=35,n_plots=20),
        ]
        out=random_effects_summary(rows)
        self.assertTrue(out["available"]); self.assertEqual(out["k"],2)
        self.assertIn("no synthetic plots",out["interpretation"])

    def test_iqr_conversion_is_explicit(self):
        e=StructuralEvidence("C","Inst","Caatinga","Caatinga","NE","AGB","Mg/ha",mean=43,iqr_low=25,iqr_high=61,n_plots=70)
        se,method=evidence_se(e)
        self.assertGreater(se,0); self.assertIn("IQR",method)

    def test_median_iqr_is_not_mixed_into_mean_meta_analysis(self):
        med=StructuralEvidence("M","Inst","Caatinga","Caatinga","NE","AGB","Mg/ha",center_type="median",mean=43,iqr_low=25,iqr_high=61,n_plots=70)
        avg=StructuralEvidence("A","Inst","Caatinga","Caatinga","NE","AGB","Mg/ha",mean=50,sd=10,n_plots=25)
        out=random_effects_summary([med,avg])
        self.assertEqual(out["k"],1)
        self.assertIn(("M","center_not_mean"),out["excluded_studies"])

    def test_range_only_is_envelope_not_weight(self):
        a=StructuralEvidence("A","Inst","Mata Atlântica","Semidecidual","MG","AGB","Mg/ha",mean=180,range_low=100,range_high=260)
        b=StructuralEvidence("B","Inst","Mata Atlântica","Semidecidual","RJ","AGB","Mg/ha",mean=75,sd=12,n_plots=63)
        out=random_effects_summary([a,b])
        self.assertEqual(out["k"],1)
        self.assertIn(("A","no_defensible_se"),out["excluded_studies"])
        self.assertEqual(out["observed_transfer_envelope"],[100.0,260.0])

    def test_primary_rows_remain_real_plot_rows(self):
        trees=[{"plot_id":"1","dbh_cm":10,"height_m":5},{"plot_id":"1","dbh_cm":20,"height_m":8},
               {"plot_id":"2","dbh_cm":30,"height_m":10}]
        out=harmonize_primary_plot_rows(trees,"TEST",0.1)
        self.assertEqual(len(out),2)
        self.assertTrue(all(not r["synthetic"] for r in out))
        self.assertGreater(out[0]["basal_area_m2_ha"],0)

    def test_ifn_harmonizer_uses_official_fields_and_requires_area(self):
        rows=[
          {"bioma":"Cerrado","uf":"DF","mun":"Teste","lon_pc":"-47.9","lat_pc":"-15.9","UA":"10","Subunidade":"A","Subparcela":"1","DAP":"20","HT":"8","SA":"1","PS":"2","HAB":"1"},
          {"bioma":"Cerrado","uf":"DF","mun":"Teste","lon_pc":"-47.9","lat_pc":"-15.9","UA":"10","Subunidade":"A","Subparcela":"1","DAP":"30","HT":"10","SA":"4","PS":"3","HAB":"1"},
        ]
        with self.assertRaises(ValueError): harmonize_ifn_dap10_rows(rows,None)
        out=harmonize_ifn_dap10_rows(rows,0.1)
        self.assertEqual(len(out),1); self.assertEqual(out[0]["n_live_stems"],1)
        self.assertEqual(out[0]["biome"],"Cerrado"); self.assertFalse(out[0]["synthetic"])
        self.assertGreater(out[0]["basal_area_m2_ha"],0)

if __name__=="__main__": unittest.main()
