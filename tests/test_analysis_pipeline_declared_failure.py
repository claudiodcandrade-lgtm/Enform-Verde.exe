"""A declared technical failure remains visible without publishing stale output."""
import unittest
from unittest.mock import patch

from analysis_pipeline_contract import validate_result_for_publication


class DeclaredFailureReportingTests(unittest.TestCase):
    def test_error_stage_may_be_reported_only_when_opted_in(self):
        result={"status":"ERRO_TECNICO_LEITURA_SAR","vector_path":"unknown.geojson",
                "recent_sar_cover":{"reason":"SELECTED_SCENES_PIXEL_READ_FAILED"}}
        with patch("analysis_pipeline_contract.geometry_hash",return_value="a"*64):
            self.assertTrue(validate_result_for_publication(
                "a"*64,object(),result,required_keys=("vector_path",),
                allow_declared_error_status=True))
            with self.assertRaisesRegex(ValueError,"ETAPA_COM_ERRO"):
                validate_result_for_publication(
                    "a"*64,object(),result,required_keys=("vector_path",))
            with self.assertRaisesRegex(ValueError,"ERRO_INTERNO_NA_ETAPA"):
                validate_result_for_publication(
                    "a"*64,object(),{**result,"error":"unhandled exception"},
                    required_keys=("vector_path",),allow_declared_error_status=True)


if __name__=="__main__":unittest.main()
