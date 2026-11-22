import unittest
from inmet_weather_client import nearest_automatic_stations,weather_executive_lines

class WeatherExecutiveTests(unittest.TestCase):
    def test_nearest_station(self):
        stations=[{"CD_ESTACAO":"A001","VL_LATITUDE":"-3.0","VL_LONGITUDE":"-55.0","DC_NOME":"Próxima"},
                  {"CD_ESTACAO":"A002","VL_LATITUDE":"-20.0","VL_LONGITUDE":"-50.0"}]
        nearest=nearest_automatic_stations(-3.035,-54.9475,stations)
        self.assertEqual(nearest[0][1]["CD_ESTACAO"],"A001")
        self.assertEqual(len(nearest),1)
    def test_missing_station_values(self):
        from unittest.mock import patch
        from inmet_weather_client import fetch_inmet_nearby
        stations=[{"CD_ESTACAO":"A001","VL_LATITUDE":-3.0,"VL_LONGITUDE":-55.0}]
        with patch("inmet_weather_client._get_json",side_effect=[stations,[{"TEM_INS":None,"CHUVA":None}]]):
            result=fetch_inmet_nearby(-3.035,-54.9475)
        self.assertEqual(result["status"],"indisponivel")

    def test_no_fabricated_inmet_data(self):
        lines=weather_executive_lines({"status":"indisponivel","reason":"sem estação"},
                                      {"mean_temperature_c":30.83,"rain_mm":1473.84,"gdd_c_day":1887.94,"temperature_days":89},
                                      {"periods":[{"dia":"2026-10-31"}]},str)
        self.assertTrue(lines[0].startswith("PAINEL EXECUTIVO"))
        self.assertTrue(any("sem estação" in x for x in lines))
        self.assertTrue(any("1473.84" in x for x in lines))
        self.assertTrue(any("não são combinadas numa média única" in x for x in lines))
        self.assertTrue(any("PRIORIDADE: NASA POWER para histórico recente em grade; CPTEC/INPE para previsão futura" in x for x in lines))
        self.assertFalse(any("Climatempo" in x for x in lines))

if __name__=="__main__":unittest.main()
