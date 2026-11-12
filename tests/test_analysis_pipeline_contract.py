"""AOI identity and result publication contracts."""
import unittest
import geopandas as gpd
from shapely.geometry import Polygon
from analysis_pipeline_contract import geometry_hash, validate_result_for_publication


class AnalysisPipelineContractTests(unittest.TestCase):
    def setUp(self):
        self.aoi = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Polygon([(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01), (0, 0)])],
            crs="EPSG:4326",
        )
        self.fingerprint = geometry_hash(self.aoi)

    def test_same_aoi_can_publish_complete_result(self):
        result = {"status": "COMPLETE", "vector_path": "/tmp/classes.gpkg"}
        self.assertTrue(validate_result_for_publication(
            self.fingerprint, self.aoi, result, required_keys=("vector_path",)))

    def test_changed_aoi_is_blocked(self):
        changed = self.aoi.copy()
        changed.loc[0, "geometry"] = Polygon(
            [(0, 0), (0.02, 0), (0.02, 0.01), (0, 0.01), (0, 0)])
        with self.assertRaisesRegex(ValueError, "HASH_AOI_DIVERGENTE"):
            validate_result_for_publication(self.fingerprint, changed, {"status": "COMPLETE"})

    def test_internal_errors_and_missing_fields_cannot_be_marked_complete(self):
        with self.assertRaisesRegex(ValueError, "ERRO_INTERNO_NA_ETAPA"):
            validate_result_for_publication(
                self.fingerprint, self.aoi, {"status": "COMPLETE", "error": "pixel read failed"})
        with self.assertRaisesRegex(ValueError, "SAIDA_INCOMPLETA"):
            validate_result_for_publication(
                self.fingerprint, self.aoi, {"status": "COMPLETE"}, required_keys=("vector_path",))

    def test_technical_failure_status_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "ETAPA_COM_ERRO"):
            validate_result_for_publication(
                self.fingerprint, self.aoi, {"status": "ERRO_TECNICO_LEITURA_SAR"})


if __name__ == "__main__":
    unittest.main()
