import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from height_calibration import validate_sar_height_pairs


class SarHeightAgreementTests(unittest.TestCase):
    def test_inventory_field_heights_do_not_replace_primary_sar_height(self):
        out=validate_sar_height_pairs(pd.DataFrame({"field_height_m":[10]}))
        self.assertEqual(out["status"],"SAR_HEIGHT_CALIBRATION_BLOCKED")
        self.assertEqual(out["height_estimate_source"],"produto SAR direto, quando disponível")
        self.assertIsNone(out["calibrated_height_m"])
        self.assertIsNone(out["local_validation_error_m"])

    def test_gtdx_height_keeps_pixel_standard_error_and_not_h100(self):
        from sar_pipeline import _gtdx_height_summary
        out=_gtdx_height_summary(
            {"mean":31.2,"sd":2.5,"n":12},
            {"mean":1.6,"sd":0.4,"n":12},
            "height_amazon_25m.tif","height_uncertainty_amazon_25m.tif")
        self.assertEqual(out["height_standard_error_pixel_zonal_mean_m"],1.6)
        self.assertFalse(out["height_definition_compatible_with_H100"])
        self.assertEqual(out["height_n_valid_pixels"],12)
        self.assertIn("TanDEM-X",out["sensor"])

    def test_gtdx_attempts_public_download_without_earthdata_credentials(self):
        import sar_pipeline as sp
        class Geometry:
            @property
            def bounds(self): return (-55.0,-4.0,-54.0,-3.0)
            def union_all(self): return self
        class GDF:
            geometry=Geometry()
            def to_crs(self,*args,**kwargs): return self
        class Response:
            status_code=200
            def __init__(self,payload=None): self.payload=payload
            def raise_for_status(self): return None
            def json(self): return self.payload
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def iter_content(self,chunk_size): yield b"public-test"
        class Session:
            def __init__(self): self.calls=[]
            def get(self,url,**kwargs):
                self.calls.append(url)
                if "cmr.earthdata.nasa.gov" in url:
                    return Response({"feed":{"entry":[{"links":[
                        {"href":"https://data.example/height_amazon_25m.tif"},
                        {"rel":"http://esipfed.org/ns/fedsearch/1.1/s3#","href":"s3://ornl-cumulus-prod-protected/global_vegetation/ForestHt_Biomass_GEDI_TDX/data/height_amazon_25m.tif"},
                        {"href":"https://data.example/height_uncertainty_amazon_25m.tif"}]}]}})
                return Response()
        session=Session()
        with tempfile.TemporaryDirectory() as td, \
             patch.object(sp,"_earthaccess_requests_session",return_value=(None,{"reason":"no credentials"})), \
             patch.object(sp.requests,"Session",return_value=session), \
             patch.object(sp,"_zonal",side_effect=[
                 {"mean":30.0,"sd":2.0,"n":3},{"mean":1.4,"sd":0.3,"n":3}]):
            out=sp.download_gtdx_height(GDF(),cache=td)
        self.assertTrue(out["available"])
        self.assertEqual(out["access_route"],"tentativa pública sem autenticação")
        self.assertIn("cmr.earthdata.nasa.gov",session.calls[0])
        self.assertFalse(any(url.startswith("s3://") for url in session.calls))

    def test_valid_fh_pixels_are_not_misreported_as_technical_route_failure(self):
        from sar_pipeline import _priority_height_route_state
        out=_priority_height_route_state(cci_eligible=False, valid_height_pixels=1512)
        self.assertEqual(out["status"],"FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL")
        self.assertFalse(out["technical_error"])
        self.assertFalse(out["cci_promoted"])

    def test_unresolved_height_route_remains_a_failure(self):
        from sar_pipeline import _priority_height_route_state
        out=_priority_height_route_state(cci_eligible=False, valid_height_pixels=0)
        self.assertEqual(out["status"],"ERRO_TECNICO_ROTA_PRIORITARIA")
        self.assertTrue(out["technical_error"])

    def test_gtdx_height_rejects_negative_error(self):
        from sar_pipeline import _gtdx_height_summary
        with self.assertRaises(ValueError):
            _gtdx_height_summary(
                {"mean":31.2,"sd":2.5,"n":12},
                {"mean":-1,"sd":0,"n":12},
                "height_amazon_25m.tif","height_uncertainty_amazon_25m.tif")

    def test_gtdx_downloader_retrieves_height_and_matching_uncertainty(self):
        import sar_pipeline as sp
        class Geometry:
            @property
            def bounds(self): return (-55.0,-4.0,-54.0,-3.0)
            def union_all(self): return self
        class GDF:
            geometry=Geometry()
            def to_crs(self,*args,**kwargs): return self
        class Response:
            def __init__(self,payload=None): self.payload=payload; self.status_code=200
            def raise_for_status(self): return None
            def json(self): return self.payload
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def iter_content(self,chunk_size):
                yield b"test-geotiff"
        class Session:
            def __init__(self): self.calls=[]
            def get(self,url,**kwargs):
                self.calls.append(url)
                if "cmr.earthdata.nasa.gov" in url:
                    return Response({"feed":{"entry":[{"links":[
                        {"href":"https://data.ornldaac.earthdata.nasa.gov/protected/global_vegetation/ForestHt_Biomass_GEDI_TDX/data/height_amazon_25m.tif"},
                        {"href":"s3://ornl-cumulus-prod-protected/global_vegetation/ForestHt_Biomass_GEDI_TDX/data/height_amazon_25m.tif"},
                        {"href":"https://data.ornldaac.earthdata.nasa.gov/protected/global_vegetation/ForestHt_Biomass_GEDI_TDX/data/height_uncertainty_amazon_25m.tif"},
                        {"href":"s3://ornl-cumulus-prod-protected/global_vegetation/ForestHt_Biomass_GEDI_TDX/data/height_uncertainty_amazon_25m.tif"}]}]}})
                return Response()
        session=Session()
        with tempfile.TemporaryDirectory() as td, \
             patch.object(sp,"_earthaccess_requests_session",return_value=(session,{"available":True})), \
             patch.object(sp,"_zonal",side_effect=[
                 {"mean":31.2,"sd":2.5,"n":4},{"mean":1.6,"sd":0.4,"n":4}]):
            out=sp.download_gtdx_height(GDF(),cache=td)
            self.assertTrue(out["available"])
            self.assertEqual(out["height_mean_m"],31.2)
            self.assertEqual(out["height_standard_error_pixel_zonal_mean_m"],1.6)
            self.assertFalse(out["height_definition_compatible_with_H100"])
            self.assertTrue((Path(td)/"height_amazon_25m.tif").exists())
            self.assertTrue((Path(td)/"height_uncertainty_amazon_25m.tif").exists())
            self.assertTrue(any("data.ornldaac.earthdata.nasa.gov/protected/" in url for url in session.calls))
            self.assertFalse(any(url.startswith("s3://") for url in session.calls))


if __name__ == "__main__":
    unittest.main()
