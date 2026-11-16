import unittest
from types import SimpleNamespace

import sar_landcover_lemplus as sar


class _Geometry:
    def __init__(self, minx, miny, maxx, maxy):
        self.bounds = (minx, miny, maxx, maxy)

    def union_all(self):
        return self


class _Frame:
    def __init__(self, minx, miny, maxx, maxy):
        self.geometry = _Geometry(minx, miny, maxx, maxy)

    def to_crs(self, _crs):
        return self


class SarCropDomainPolicyTests(unittest.TestCase):
    def test_tapajos_outside_domain_keeps_agriculture_but_suppresses_crop_names(self):
        # Approximate Tapajos km 83 location, north of the model's training envelope.
        aoi = _Frame(-55.2, -3.2, -55.1, -3.1)
        self.assertFalse(sar._aoi_in_training_envelope(aoi))
        self.assertEqual(
            list(sar._crop_labels_with_domain_guard(["Soja", "Café"], False)),
            [sar.UNIDENTIFIED_CROP, sar.UNIDENTIFIED_CROP],
        )

    def test_sinop_inside_domain_retains_experimental_crop_predictions(self):
        aoi = _Frame(-55.21, -11.89, -55.17, -11.855)
        self.assertTrue(sar._aoi_in_training_envelope(aoi))
        self.assertEqual(
            list(sar._crop_labels_with_domain_guard(["Soja", "Café"], True)),
            ["Soja", "Café"],
        )

    def test_entire_aoi_must_fit_envelope_not_only_its_center(self):
        # Center is in the envelope, but part of this AOI extends north of it.
        aoi = _Frame(-55.2, -8.0, -55.0, -7.0)
        self.assertFalse(sar._aoi_in_training_envelope(aoi))

    def test_generic_experimental_crop_does_not_enter_crop_specific_forecast(self):
        from crop_monitoring_forecast import experimental_crops_in_land_result
        land={"classes":[{"class_name":sar.UNIDENTIFIED_CROP,"area_ha":1.92,
                           "source":"SAR_EXPERIMENTAL_MODELO"}]}
        self.assertEqual(experimental_crops_in_land_result(land),{})

    def test_80m_pixel_area_explains_064_ha_label_granularity(self):
        self.assertEqual(sar.PIXEL_M * sar.PIXEL_M / 10_000, 0.64)


if __name__ == "__main__":
    unittest.main()
