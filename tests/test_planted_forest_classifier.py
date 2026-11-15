import unittest
from crop_model_registry import CROPS, PLANTED_FOREST_CLASSES, CLASSIFIER_TARGETS
from planted_forest_classifier import planted_forest_map_label, planted_forest_decision

class PlantedForestTests(unittest.TestCase):
    def test_ten_targets_plus_forest_parent(self):
        self.assertEqual(len(CROPS),8)
        self.assertEqual(len(CLASSIFIER_TARGETS),11)
        self.assertIn("Eucalipto",PLANTED_FOREST_CLASSES)
        self.assertIn("Pinus",PLANTED_FOREST_CLASSES)
    def test_map_class_9_is_generic_only(self):
        self.assertEqual(planted_forest_map_label("mapbiomas_c11_coverage",9),"Floresta plantada")
        self.assertIsNone(planted_forest_map_label("mapbiomas_c11_first_season",9))
    def test_map_cannot_promote_genus(self):
        r=planted_forest_decision(None,{"Eucalipto":.99,"Pinus":.01},
            {"Eucalipto":{"eligible":True,"n_independent":100,"precision_wilson95_lower":.99}},
            mapped_silviculture=True)
        self.assertEqual(r["class_name"],"Floresta plantada")
        self.assertEqual(r["source"],"MAPBIOMAS")
    def test_sar_genus_requires_gate(self):
        bad=planted_forest_decision("Floresta plantada",{"Eucalipto":.99,"Pinus":.01},{})
        self.assertEqual(bad["class_name"],"Floresta plantada")
        good=planted_forest_decision("Floresta plantada",{"Eucalipto":.99,"Pinus":.01},
           {"Eucalipto":{"eligible":True,"n_independent":100,"precision_wilson95_lower":.95}})
        self.assertEqual(good["class_name"],"Eucalipto")
    def test_native_not_silviculture(self):
        r=planted_forest_decision("Formação florestal")
        self.assertIsNone(r["class_name"])

if __name__=="__main__":
    unittest.main()
