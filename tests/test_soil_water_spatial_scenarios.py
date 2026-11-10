"""Synthetic unit tests for FAO56 storage and the PAM yield sensitivity wiring.

These numbers are software checks only: neither moisture measurement nor
independent agronomic validation.
"""
import unittest
from datetime import date,timedelta
from unittest.mock import patch
from soil_water_balance_spatial import (available_capacity_mm,
    daily_storage,scenarios,pedotransfer_saxton_rawls)
from crop_forecast_pipeline import _modelled_soil_water_and_yield


def weather(days=35,rain=3.):
    start=date(2026,10,1)
    return [{"date":(start+timedelta(days=i)).strftime("%Y%m%d"),
             "PRECTOTCORR":rain,"T2M_MAX":33.,"T2M_MIN":22.}
            for i in range(days)]


class SoilWaterModelTests(unittest.TestCase):
    def test_capacity_and_pedotransfer(self):
        self.assertAlmostEqual(available_capacity_mm(.6,ad_mm_cm=1.),
                               60.,places=6)
        self.assertAlmostEqual(available_capacity_mm(.6,theta_fc=.3,
                         theta_wp=.15),90.,places=6)
        x=pedotransfer_saxton_rawls(.45,.30,2.)
        self.assertGreater(x["theta_fc"],x["theta_wp"])
        self.assertGreater(x["ad_mm_cm"],0)

    def test_scenario_sensitivity_and_mass_bounds(self):
        data=scenarios(weather(35),root_depth_m=.6,lat_deg=-11.87,
                       ad_class="AD4",kc=1.15)
        self.assertEqual(data["status"],"ARMAZENAMENTO_HIDRICO_MODELADO")
        self.assertTrue(data["scenario_intervals_are_not_CI95"])
        self.assertEqual(set(data["storage_mm_by_scenario"]),{"seco","central","umido"})
        for label,val in data["storage_mm_by_scenario"].items():
            self.assertGreaterEqual(val,0)
            self.assertLessEqual(val,
              data["root_zone_capacity_mm_by_scenario"][label])
        self.assertEqual(data["as_of"],"2026-11-04")

    def test_missing_hydraulic_data_is_explicit_not_default(self):
        x=scenarios(weather(),root_depth_m=.6,lat_deg=-11.87)
        self.assertEqual(x["status"],"N/D_SEM_PARAMETROS_HIDRAULICOS")

    def test_missing_day_rejected(self):
        s=weather(16);s.pop(4)
        with self.assertRaisesRegex(ValueError,"unfilled gap"):
            daily_storage(s,capacity_mm=80,lat_deg=-11.87)

    def test_forecast_mathematical_sensitivity_uses_beta(self):
        params={"a":1000.,"b":0.,"harvest_year":2026,"beta":500.}
        with patch("crop_panel_yield_model.season_ry_ensemble",
                   side_effect=[[.4],[.5],[.6]]) as sim:
            result=_modelled_soil_water_and_yield("Soja",-11.87,weather(),
                date(2026,11,4),2026,range(2001,2026),
                {"ad_class":"AD4","source":"ZARC typed AD4"},
                [.5],params)
        self.assertEqual(result["status"],"ARMAZENAMENTO_HIDRICO_MODELADO")
        a=result["yield_sensitivity_by_scenario"]
        self.assertAlmostEqual(a["seco"]["delta_vs_calibrated_RY_kg_ha"],-50.)
        self.assertAlmostEqual(a["umido"]["delta_vs_calibrated_RY_kg_ha"],50.)
        self.assertEqual(sim.call_count,3)


if __name__=="__main__":
    unittest.main()
