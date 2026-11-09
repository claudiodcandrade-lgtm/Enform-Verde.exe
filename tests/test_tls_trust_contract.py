"""V87.39 root cause (Sinop): GDAL/curl ignored the Windows/OS trust store."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TlsTrustContract(unittest.TestCase):
    """V87.37 root cause: GDAL/curl ignored the OS/Windows trust store."""

    def test_merged_bundle_contains_certifi_and_os_roots_and_env_is_exported(self):
        import os, tempfile
        import tls_setup
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "proxy_root.pem")
            with open(fake, "w") as f:
                f.write("-----BEGIN CERTIFICATE-----\nFAKEPROXYROOT\n-----END CERTIFICATE-----\n")
            old = {k: os.environ.pop(k, None) for k in tls_setup.ENV_KEYS}
            os.environ["SSL_CERT_FILE"] = fake
            try:
                tls_setup._STATE.clear()
                bundle = tls_setup.merged_ca_bundle(d)
                text = open(bundle, encoding="ascii", errors="ignore").read()
                self.assertIn("FAKEPROXYROOT", text)
                self.assertGreater(text.count("BEGIN CERTIFICATE"), 50)      # certifi roots kept
                os.environ.pop("SSL_CERT_FILE")
                tls_setup._STATE.clear()
                state = tls_setup.configure(cache_dir=d)
                self.assertEqual(state["verification"], "ENABLED")
                self.assertEqual(os.environ.get("GDAL_HTTP_UNSAFESSL"), "NO")
                self.assertEqual(tls_setup.gdal_env()["GDAL_HTTP_UNSAFESSL"], "NO")
            finally:
                tls_setup._STATE.clear()
                for k, v in old.items():
                    os.environ.pop(k, None)
                    if v is not None:
                        os.environ[k] = v

    def test_every_remote_gdal_reader_uses_the_shared_trust(self):
        src = (ROOT / "recent_sar_landcover.py").read_text(encoding="utf-8")
        self.assertIn("gdal_env()", src)
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertLess(app.index("tls_setup.configure()"), app.index("from sar_pipeline import"))
        self.assertIn("--network-check", app)
        self.assertNotIn('GDAL_HTTP_UNSAFESSL="YES"', app + src)

    def test_windows_schannel_never_receives_oversized_merged_ca_bundle(self):
        import os, tempfile
        from unittest.mock import patch
        import tls_setup
        with tempfile.TemporaryDirectory() as d:
            bundle = Path(d) / "merged.pem"
            bundle.write_bytes(b"X" * (tls_setup.WINDOWS_SCHANNEL_CA_LIMIT + 1))
            old = {k: os.environ.pop(k, None) for k in tls_setup.ENV_KEYS}
            try:
                os.environ["CURL_CA_BUNDLE"] = str(bundle)
                os.environ["GDAL_CURL_CA_BUNDLE"] = str(bundle)
                tls_setup._STATE.clear()
                with patch.object(tls_setup, "_uses_windows_schannel", return_value=True), \
                     patch.object(tls_setup, "merged_ca_bundle", return_value=str(bundle)):
                    state = tls_setup.configure(force=True)
                    self.assertNotIn("CURL_CA_BUNDLE", os.environ)
                    self.assertNotIn("GDAL_CURL_CA_BUNDLE", os.environ)
                    self.assertIn("REQUESTS_CA_BUNDLE", os.environ)
                    self.assertIn("GDAL_CURL_CA_BUNDLE", state["env_applied"])
                    self.assertEqual(tls_setup.gdal_env(), {"GDAL_HTTP_UNSAFESSL": "NO"})
            finally:
                tls_setup._STATE.clear()
                for k, v in old.items():
                    os.environ.pop(k, None)
                    if v is not None:
                        os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
