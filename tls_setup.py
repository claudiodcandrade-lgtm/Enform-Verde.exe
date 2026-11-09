"""One place to make HTTPS work identically for requests AND GDAL/rasterio.

Root cause addressed (V87.37, case Sinop 08/11/2026): the Windows EXE could
search catalogues but failed to read COG pixels (CBERS-4A, Sentinel-1 RTC)
and sometimes even to open Earth Search. GDAL inside rasterio uses its own
libcurl, which does not read the Windows certificate store; antivirus HTTPS
inspection and corporate/ISP proxies install roots ONLY in that store.
Some modules passed a CA bundle per call, others (e.g. the SAR series reader)
did not.

Fix: build once a merged bundle = certifi + Windows ROOT/CA stores, write it
to the user cache, and export it through the environment variables honoured
by requests (REQUESTS_CA_BUNDLE), Python ssl (SSL_CERT_FILE) and GDAL/curl
(CURL_CA_BUNDLE, GDAL_CURL_CA_BUNDLE). Certificate verification is never
disabled. Values already set by the user are kept.
"""
from __future__ import annotations

import hashlib
import os
import ssl
from pathlib import Path

ENV_KEYS = ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE", "GDAL_CURL_CA_BUNDLE")
_STATE = {}


def _windows_store_pems():
    pems = []
    enum = getattr(ssl, "enum_certificates", None)       # Windows only
    if enum is None:
        return pems
    for store in ("ROOT", "CA"):
        try:
            for cert, encoding, trust in enum(store):
                if encoding == "x509_asn":
                    pems.append(ssl.DER_cert_to_PEM_cert(cert))
        except (OSError, PermissionError):
            continue
    return pems


def merged_ca_bundle(cache_dir=None):
    try:
        import certifi
        base = Path(certifi.where()).read_text(encoding="ascii", errors="ignore")
    except Exception:
        base = ""
    extra = _windows_store_pems()
    # Operating-system bundle (Linux/macOS, or a bundle the user configured)
    # also carries roots of TLS-inspecting proxies/antivirus.
    paths = ssl.get_default_verify_paths()
    for candidate in (os.environ.get("SSL_CERT_FILE"), paths.cafile, paths.openssl_cafile):
        try:
            if candidate and Path(candidate).is_file() and "certifi" not in str(candidate):
                extra.append(Path(candidate).read_text(encoding="ascii", errors="ignore"))
                break
        except OSError:
            continue
    if not extra:
        return None if not base else str(Path(__import__("certifi").where()))
    text = base.rstrip() + "\n" + "\n".join(extra)
    digest = hashlib.sha256(text.encode("ascii", "ignore")).hexdigest()[:16]
    root = Path(cache_dir or (Path.home() / ".enform_verde" / "tls"))
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"ca_bundle_{digest}.pem"
    if not out.is_file():
        tmp = out.with_suffix(".tmp")
        tmp.write_text(text, encoding="ascii", errors="ignore")
        tmp.replace(out)
    return str(out)


def configure(cache_dir=None, force=False):
    """Idempotent. Returns the audit dict (bundle path, store certs, env set)."""
    if _STATE and not force:
        return dict(_STATE)
    bundle = merged_ca_bundle(cache_dir)
    applied = {}
    if bundle:
        for key in ENV_KEYS:
            if not os.environ.get(key) or force:
                os.environ[key] = bundle
                applied[key] = bundle
    os.environ.setdefault("GDAL_HTTP_UNSAFESSL", "NO")
    _STATE.update({"bundle": bundle, "windows_store_certificates": len(_windows_store_pems()),
                   "env_applied": sorted(applied), "verification": "ENABLED"})
    return dict(_STATE)


def gdal_env():
    """Options to pass explicitly to rasterio.Env (belt and braces)."""
    state = configure()
    env = {"GDAL_HTTP_UNSAFESSL": "NO"}
    if state.get("bundle"):
        env.update({"CURL_CA_BUNDLE": state["bundle"], "GDAL_CURL_CA_BUNDLE": state["bundle"]})
    return env
