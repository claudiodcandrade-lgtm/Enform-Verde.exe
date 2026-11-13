"""Independent HTTPS-to-local COG reader fallback for Windows GDAL failures."""
import unittest
from unittest.mock import patch
import sys

from recent_sar_landcover import _open_signed_cog_via_https


class _Response:
    status_code=200
    headers={"Content-Type":"image/tiff","Content-Length":"8"}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def iter_content(self,chunk_size):
        yield b"II*\x00data"


class _Dataset:
    def __init__(self,path,observed):self.path=path;self.observed=observed
    def __enter__(self):
        from pathlib import Path
        self.observed.append(Path(self.path).is_file())
        return self
    def __exit__(self,*args):return False


class _Rasterio:
    def __init__(self,observed):self.observed=observed
    def open(self,path):return _Dataset(path,self.observed)


class _RequestsStub:
    class RequestException(Exception):pass
    def __init__(self,response):self.response=response
    def get(self,*args,**kwargs):return self.response


class SarHttpsLocalReadFallbackTests(unittest.TestCase):
    def test_streams_signed_tiff_to_temporary_file_and_removes_it(self):
        observed=[]
        rasterio=_Rasterio(observed)
        requests_stub=_RequestsStub(_Response())
        with patch("tls_setup.configure") as configure, \
             patch("sentinel1_mpc.asset_href_for_read_attempt",return_value="https://signed.example/asset.tif") as sign, \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with _open_signed_cog_via_https(
                    "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                    rasterio=rasterio,token="sig=not-logged",token_fn=lambda:"sig=fresh",
                    request_get=requests_stub.get) as ds:
                path=ds.path
                self.assertTrue(__import__("pathlib").Path(path).is_file())
        from pathlib import Path
        self.assertTrue(observed[0])
        self.assertFalse(Path(path).exists())
        configure.assert_called_once_with()
        sign.assert_called_once()
        self.assertEqual(requests_stub.response.status_code,200)

    def test_rejects_non_tiff_payload(self):
        class Html(_Response):
            headers={"Content-Type":"text/html","Content-Length":"8"}
            def iter_content(self,chunk_size):yield b"<html>no"
        requests_stub=_RequestsStub(Html())
        with patch("tls_setup.configure"), \
             patch("sentinel1_mpc.asset_href_for_read_attempt",return_value="https://signed.example/asset.tif"), \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with self.assertRaisesRegex(RuntimeError,"non-raster response"):
                with _open_signed_cog_via_https(
                        "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                            rasterio=_Rasterio([]),request_get=requests_stub.get):
                    pass


if __name__=="__main__":unittest.main()
