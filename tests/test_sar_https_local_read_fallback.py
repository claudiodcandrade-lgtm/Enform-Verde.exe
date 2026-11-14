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
    def __init__(self,path,observed):self.path=path;self.observed=observed;self.count=1;self.width=100;self.height=100
    def __enter__(self):
        from pathlib import Path
        self.observed.append(Path(self.path).is_file())
        return self
    def __exit__(self,*args):return False


class _Rasterio:
    def __init__(self,observed):self.observed=observed
    def open(self,path):return _Dataset(path,self.observed)

class _MemoryFile:
    def __init__(self,data):self.data=data
    def __enter__(self):return _Dataset("memory",[])
    def __exit__(self,*args):return False
    def open(self):return _Dataset("memory",[])
    def close(self):pass


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

    def test_oversized_cog_uses_bounded_official_aoi_crop(self):
        class Large(_Response):
            headers={"Content-Type":"image/tiff","Content-Length":str(2*1024**3)}
            def iter_content(self,chunk_size):
                raise AssertionError("oversized source must not be streamed in full")
        class CropResponse:
            status_code=200
            headers={"Content-Type":"image/tiff; application=geotiff"}
            content=b"II*\x00crop"
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def iter_content(self,chunk_size):yield self.content
        observed=[]
        rasterio=_Rasterio(observed)
        rasterio.io=type("IO",(),{"MemoryFile":_MemoryFile})
        requests_stub=_RequestsStub(Large())
        crop_calls=[]
        def post(url,**kwargs):
            crop_calls.append((url,kwargs))
            return CropResponse()
        geom={"type":"Polygon","coordinates":[[[-55.21,-11.89],[-55.17,-11.89],
             [-55.17,-11.855],[-55.21,-11.855],[-55.21,-11.89]]]}
        with patch("tls_setup.configure"), \
             patch("sentinel1_mpc.asset_href_for_read_attempt",return_value="https://signed.example/large.tif"), \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with _open_signed_cog_via_https(
                    "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                    rasterio=rasterio,request_get=requests_stub.get,request_post=post,
                    item_id="S1_TEST_RTC",asset_key="vv",geometry=geom,
                    max_bytes=1024) as ds:
                self.assertEqual(ds.path,"memory")
        self.assertEqual(len(crop_calls),1)
        self.assertIn("/api/data/v1/item/crop?",crop_calls[0][0])
        self.assertIn("assets=vv",crop_calls[0][0])
        self.assertEqual(crop_calls[0][1]["verify"],True)

    def test_signing_failure_recovers_through_aoi_crop(self):
        class CropResponse:
            status_code=200
            headers={"Content-Type":"image/tiff; application=geotiff"}
            content=b"II*\x00crop"
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def iter_content(self,chunk_size):yield self.content
        requests_stub=_RequestsStub(None)
        rasterio=_Rasterio([])
        rasterio.io=type("IO",(),{"MemoryFile":_MemoryFile})
        geom={"type":"Polygon","coordinates":[[[-55.21,-11.89],[-55.17,-11.89],
             [-55.17,-11.855],[-55.21,-11.855],[-55.21,-11.89]]]}
        crop_calls=[]
        def post(url,**kwargs):crop_calls.append(url);return CropResponse()
        with patch("tls_setup.configure"), \
             patch("sentinel1_mpc.asset_href_for_read_attempt",side_effect=ValueError("token unavailable")), \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with _open_signed_cog_via_https(
                    "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                    rasterio=rasterio,request_post=post,item_id="S1_TEST_RTC",
                    asset_key="vv",geometry=geom) as ds:
                self.assertEqual(ds.path,"memory")
        self.assertEqual(len(crop_calls),1)

    def test_transport_failure_recovers_through_aoi_crop(self):
        class CropResponse:
            status_code=200
            headers={"Content-Type":"image/tiff; application=geotiff"}
            content=b"II*\x00crop"
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def iter_content(self,chunk_size):yield self.content
        requests_stub=_RequestsStub(None)
        def failed_get(*args,**kwargs):raise requests_stub.RequestException("connection reset")
        rasterio=_Rasterio([])
        rasterio.io=type("IO",(),{"MemoryFile":_MemoryFile})
        geom={"type":"Polygon","coordinates":[[[-55.21,-11.89],[-55.17,-11.89],
             [-55.17,-11.855],[-55.21,-11.855],[-55.21,-11.89]]]}
        crop_calls=[]
        def post(url,**kwargs):crop_calls.append(url);return CropResponse()
        with patch("tls_setup.configure"), \
             patch("sentinel1_mpc.asset_href_for_read_attempt",return_value="https://signed.example/x.tif"), \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with _open_signed_cog_via_https(
                    "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                    rasterio=rasterio,request_get=failed_get,request_post=post,
                    item_id="S1_TEST_RTC",asset_key="vv",geometry=geom) as ds:
                self.assertEqual(ds.path,"memory")
        self.assertEqual(len(crop_calls),1)

    def test_crop_response_is_stopped_at_size_limit(self):
        class LargeCrop:
            status_code=200
            headers={"Content-Type":"image/tiff; application=geotiff"}
            def __init__(self):self.closed=False
            def __enter__(self):return self
            def __exit__(self,*args):self.closed=True;return False
            def iter_content(self,chunk_size):
                yield b"1234"
                yield b"5"
                raise AssertionError("reader must stop after exceeding the cap")
        response=LargeCrop()
        requests_stub=_RequestsStub(None)
        rasterio=_Rasterio([])
        rasterio.io=type("IO",(),{"MemoryFile":_MemoryFile})
        geom={"type":"Polygon","coordinates":[[[-55.21,-11.89],[-55.17,-11.89],
             [-55.17,-11.855],[-55.21,-11.855],[-55.21,-11.89]]]}
        with patch("tls_setup.configure"), \
             patch("sentinel1_mpc.asset_href_for_read_attempt",side_effect=ValueError("token unavailable")), \
             patch.dict(sys.modules,{"requests":requests_stub}):
            with self.assertRaisesRegex(RuntimeError,"bounded response size"):
                with _open_signed_cog_via_https(
                        "https://sentinel1euwestrtc.blob.core.windows.net/x.tif",
                        rasterio=rasterio,request_post=lambda *a,**k:response,
                        item_id="S1_TEST_RTC",asset_key="vv",geometry=geom,max_crop_bytes=4):
                    pass
        self.assertTrue(response.closed)


if __name__=="__main__":unittest.main()
