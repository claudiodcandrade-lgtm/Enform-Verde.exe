"""Fail-closed download/cache of official IBGE vector ZIPs.

A ZIP central-directory check is not a geospatial validation; callers still
must verify the official layer, CRS, legenda_1, code and AOI intersection.
"""
import hashlib
import json
import time
import zipfile
from pathlib import Path

import requests


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _archive_ok(path, check_crc=False):
    try:
        if not path.is_file() or path.stat().st_size <= 1024 * 1024:
            return False
        with zipfile.ZipFile(path) as archive:
            return bool(archive.infolist()) and (not check_crc or archive.testzip() is None)
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return False


def download_ibge_zip(url, folder, tag, version, attempts=3, pause=time.sleep):
    """Download official bytes atomically; retry only transient network errors.

    Never promote HTML, truncated ZIP, corrupt cache or stale .part to a
    phytoregion. SHA256 sidecar protects cache against subsequent alteration,
    but is NOT a publisher-signed checksum or scientific validation.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (tag + ".zip")
    sidecar = folder / (tag + ".sha256")
    verified = folder / (tag + ".verified.json")
    partial = folder / (tag + ".part")
    if _archive_ok(path):
        stat = path.stat()
        try:
            receipt=json.loads(verified.read_text(encoding="utf-8"))
            unchanged=(receipt.get("size_bytes")==stat.st_size
                and receipt.get("mtime_ns")==stat.st_mtime_ns
                and receipt.get("inode")==getattr(stat,"st_ino",None))
            if unchanged and sidecar.exists() and receipt.get("sha256")==sidecar.read_text(encoding="ascii").strip():
                return path
        except (OSError,ValueError,TypeError):
            pass
        # Legacy caches carry only SHA-256. Verify them once, then persist a
        # stat-bound receipt so each subsequent AOI does not reread the whole
        # national archive (hundreds of MB) before bbox/quadrant extraction.
        digest = _digest(path)
        if not sidecar.exists() or sidecar.read_text(encoding="ascii").strip() == digest:
            sidecar.write_text(digest + "\n", encoding="ascii")
            verified.write_text(json.dumps({"sha256":digest,"size_bytes":stat.st_size,
                "mtime_ns":stat.st_mtime_ns,"inode":getattr(stat,"st_ino",None)},sort_keys=True),encoding="utf-8")
            return path
    path.unlink(missing_ok=True)
    sidecar.unlink(missing_ok=True)
    verified.unlink(missing_ok=True)
    partial.unlink(missing_ok=True)
    for attempt in range(attempts):
        try:
            with requests.get(url, stream=True, timeout=(30, 300),
                              headers={"User-Agent": f"Enform-Verde/{version}"}) as response:
                response.raise_for_status()
                with partial.open("wb") as out:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        if chunk:
                            out.write(chunk)
            if not _archive_ok(partial, check_crc=True):
                raise ValueError("Official IBGE response is not a complete valid ZIP")
            digest = _digest(partial)
            partial.replace(path)
            sidecar.write_text(digest + "\n", encoding="ascii")
            stat=path.stat()
            verified.write_text(json.dumps({"sha256":digest,"size_bytes":stat.st_size,
                "mtime_ns":stat.st_mtime_ns,"inode":getattr(stat,"st_ino",None)},sort_keys=True),encoding="utf-8")
            return path
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            partial.unlink(missing_ok=True)
            if attempt + 1 >= attempts:
                raise
            pause(min(2 ** attempt, 8))
        except requests.exceptions.HTTPError as exc:
            partial.unlink(missing_ok=True)
            status = exc.response.status_code if exc.response is not None else None
            if status not in (429, 500, 502, 503, 504) or attempt + 1 >= attempts:
                raise
            pause(min(2 ** attempt, 8))
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    raise RuntimeError("IBGE download attempts exhausted")
