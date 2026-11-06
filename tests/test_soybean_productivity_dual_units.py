"""Unit conversion and uncertainty tests for soybean forecast."""
import unittest
from crop_forecast_pipeline import productivity_display

class TestSoybeanUnits(unittest.TestCase):
    def test_tonnes_bags_percent(self):
        p={"median":3600.,"p05":3000.,"p95":4200.}
        got=productivity_display("Soja",p,fmt=lambda x,nd=0:f"{x:.{nd}f}")
        for token in ("3.60 t/ha","3.00–4.20 t/ha","60.00 sacas/ha","50.00–70.00 sacas/ha","60 kg/saca","-16.7% / +16.7%"):
            self.assertIn(token,got)
        self.assertEqual(p["median"],3600.)
    def test_other_crops_no_soy_bags(self):
        got=productivity_display("Milho",{"median":6000.,"p05":4000.,"p95":8000.},fmt=lambda x,nd=0:f"{x:.{nd}f}")
        self.assertIn("6.00 t/ha",got)
        self.assertNotIn("sacas/ha",got)
    def test_asymmetric_and_zero_median(self):
        fmt=lambda x,nd=0:f"{x:.{nd}f}"
        got=productivity_display("Soja",{"median":3000.,"p05":2400.,"p95":3900.},fmt=fmt)
        self.assertIn("-20.0% / +30.0%",got)
        got=productivity_display("Soja",{"median":0.,"p05":0.,"p95":200.},fmt=fmt)
        self.assertIn("incerteza relativa: N/D",got)

if __name__=="__main__":
    unittest.main()
