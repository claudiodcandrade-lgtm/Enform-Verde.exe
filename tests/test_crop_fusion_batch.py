import tempfile
import unittest
from pathlib import Path
from crop_fusion_batch import classify_crop_batch
from tests.test_crop_fusion_inference import CropFusionTests

class BatchTests(unittest.TestCase):
    def test_abstention_and_export(self):
        obs,height,regional,gates=CropFusionTests().fixture()
        records=[{"observation_id":"a","observation":obs,"probabilities":{"Soja":.95,"Milho":.05}},
                 {"observation_id":"b","observation":obs,"probabilities":{"Soja":.5,"Milho":.5}}]
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"out.json"
            res=classify_crop_batch(records,height_contract=height,regional_records={"Soja":regional},
                                    validation_gates=gates,model_source="synthetic",output_path=dest)
            self.assertEqual(res["accepted"],1)
            self.assertEqual(res["abstained"],1)
            self.assertTrue(dest.exists())
            self.assertEqual(res["results"][1]["source"],"SEM_CLASSIFICACAO_SAR")
    def test_invalid_records_fail(self):
        with self.assertRaises(ValueError):
            classify_crop_batch({},height_contract={},regional_records={},validation_gates={},model_source="synthetic")
if __name__=="__main__":
    unittest.main()
