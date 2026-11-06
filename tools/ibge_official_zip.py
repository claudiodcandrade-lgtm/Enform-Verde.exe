"""Fail-closed download/cache of official IBGE vector ZIPs.

A ZIP central-directory check is not a geospatial validation; callers still
must verify the official layer, CRS, legenda_1, code and AOI intersection.
"""
import hashlib
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
    partial = folder / (tag + ".part")
    if _archive_ok(path):
        digest = _digest(path)
        if not sidecar.exists() or sidecar.read_text(encoding="ascii").strip() == digest:
            if not sidecar.exists():
                sidecar.write_text(digest + "\n", encoding="ascii")
            return path
    path.unlink(missing_ok=True)
    sidecar.unlink(missing_ok=True)
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
