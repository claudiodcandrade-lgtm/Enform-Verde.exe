"""Weather provenance stays attached to summary and visible in executive report."""
import unittest
from agricultural_weather import summarize_weather
from inmet_weather_client import weather_executive_lines


class WeatherIntervalProvenanceTest(unittest.TestCase):
    def test_nasa_power_interval_is_retained_and_displayed(self):
        series = {"source": "NASA POWER", "source_url": "https://power.larc.nasa.gov",
                  "start": "2026-08-01", "end": "2026-10-29",
                  "retrieved_utc": "2026-11-04T10:00:00+00:00",
                  "observations": [{"date": "20260801", "T2M": 26,
                                    "T2M_MAX": 31, "T2M_MIN": 21,
                                    "PRECTOTCORR": 4}]}
        summary = summarize_weather(series)
        self.assertEqual(summary["start"], "2026-08-01")
        self.assertEqual(summary["end"], "2026-10-29")
        self.assertEqual(summary["retrieved_utc"], "2026-11-04T10:00:00+00:00")
        text = "\n".join(weather_executive_lines(power=summary))
        self.assertIn("Período NASA POWER: 2026-08-01 a 2026-10-29", text)
        self.assertIn("2026-11-04T10:00:00+00:00", text)


if __name__ == "__main__":
    unittest.main()
