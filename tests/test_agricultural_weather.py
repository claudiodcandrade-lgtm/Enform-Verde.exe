import io
import unittest
from datetime import datetime,timezone,timedelta
from agricultural_weather_sources import rank_stations,quality_check_hourly,check_freshness
from cptec_forecast_client import forecast_by_city,forecast_by_coordinates
from agricultural_weather import fetch_daily_weather,summarize_weather

class FakeResponse:
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n=-1):return self.data if n<0 else self.data[:n]
def opener(request,timeout):return FakeResponse(b"<cidade><previsao><dia>2026-10-25</dia><tempo>pn</tempo></previsao></cidade>")

class WeatherTests(unittest.TestCase):
    def test_stations_nearest(self):
        stations=[{"latitude":-16,"longitude":-48,"name":"near"},
                  {"latitude":-23,"longitude":-46,"name":"far"}]
        ranked=rank_stations(-16,-48,stations,max_distance_km=50)
        self.assertEqual([x["name"] for x in ranked],["near"])
    def test_missing_and_outlier(self):
        result=quality_check_hourly([{"temperature_c":"9999","relative_humidity_pct":"82,5","precipitation_mm":-2}])[0]
        self.assertIsNone(result["temperature_c"])
        self.assertIsNone(result["precipitation_mm"])
        self.assertEqual(result["relative_humidity_pct"],82.5)
    def test_freshness(self):
        now=datetime(2026,10,24,12,tzinfo=timezone.utc)
        self.assertTrue(check_freshness((now-timedelta(minutes=30)).isoformat(),"INMET",now=now)["fresh"])
        self.assertFalse(check_freshness((now-timedelta(days=2)).isoformat(),"INMET",now=now)["fresh"])
    def test_cptec_city(self):
        r=forecast_by_city(244,opener=opener)
        self.assertEqual(r["periods"][0]["dia"],"2026-10-25")
        self.assertEqual(r["status"],"forecast")
    def test_cptec_coordinates(self):
        r=forecast_by_coordinates(-15.5,-47.8,opener=opener)
        self.assertEqual(r["status"],"forecast")
    def test_power_daily_parse_and_summary(self):
        payload=b'{"properties":{"parameter":{"T2M":{"20261020":24},"T2M_MAX":{"20261020":30},"T2M_MIN":{"20261020":20},"PRECTOTCORR":{"20261020":12}}}}'
        def mock(req,timeout):return FakeResponse(payload)
        r=fetch_daily_weather(-15,-47,days=7,end_date="2026-10-20",opener=mock)
        self.assertEqual(r["observations"][0]["T2M"],24)
        summary=summarize_weather(r)
        self.assertEqual(summary["rain_mm"],12)
        self.assertEqual(summary["gdd_c_day"],15)
    def test_power_rejects_bad_coordinates(self):
        with self.assertRaises(ValueError):fetch_daily_weather(100,0)
    def test_invalid_city(self):
        with self.assertRaises(ValueError):forecast_by_city(-1,opener=opener)

if __name__=="__main__":unittest.main()
