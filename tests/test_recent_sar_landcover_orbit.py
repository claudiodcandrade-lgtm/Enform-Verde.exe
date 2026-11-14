"""Contract tests for orbit selection, redaction and missing evidence."""
import unittest
from datetime import datetime,timedelta,timezone
from recent_sar_landcover import (_select_orbit_series,_safe_reason,
                                  _retryable_pixel_read_failure)
class OrbitSelectionTests(unittest.TestCase):
    def test_complete_alternate_orbit_beats_single_latest_scene(self):
        t=datetime(2026,11,4,tzinfo=timezone.utc)
        records=[(t-timedelta(days=1),{"orbit_state":"ascending","relative_orbit":1})]
        records.extend((t-timedelta(days=d),{"orbit_state":"descending","relative_orbit":80})
                       for d in (5,20,45,70))
        selected,orbit=_select_orbit_series(records,t)
        self.assertEqual(orbit,("MPC","descending",80))
        self.assertGreaterEqual(len(selected),3)
        self.assertLessEqual((t-selected[0][0]).total_seconds(),30*86400)

    def test_stale_latest_scene_cannot_make_a_current_monitoring_series(self):
        t=datetime(2026,11,13,tzinfo=timezone.utc)
        records=[(t-timedelta(days=d),{"provider":"INPE","orbit_state":"ascending","relative_orbit":1})
                 for d in (40,55,70,85)]
        selected,orbit=_select_orbit_series(records,t)
        self.assertEqual(selected,[])
        self.assertIsNone(orbit)
    def test_unknown_orbit_must_not_be_mixed(self):
        t=datetime(2026,11,4,tzinfo=timezone.utc)
        rows=[(t-timedelta(days=d),{"orbit_state":None,"relative_orbit":None}) for d in (1,20,45)]
        self.assertEqual(_select_orbit_series(rows,t),([],None))
    def test_sensitive_raster_access_url_redacted(self):
        reason=_safe_reason(ValueError("GDAL: https://asset.example/rtc.tif?sig=SECRET&sv=3"))
        self.assertNotIn("SECRET",reason)
        self.assertNotIn("https://",reason)
    def test_deterministic_empty_or_outside_aoi_errors_do_not_retry_transports(self):
        self.assertFalse(_retryable_pixel_read_failure(ValueError("SAR_SCENE_NO_VALID_PIXELS_IN_AOI")))
        self.assertFalse(_retryable_pixel_read_failure(ValueError("SAR asset does not intersect AOI")))
    def test_transport_and_decoder_errors_keep_alternate_routes(self):
        self.assertTrue(_retryable_pixel_read_failure(OSError("TLS connection reset")))
        self.assertTrue(_retryable_pixel_read_failure(UnicodeError("invalid response text")))
if __name__=="__main__":unittest.main()
