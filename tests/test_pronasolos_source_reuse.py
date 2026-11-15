import unittest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

import desktop_app


class PronaSolosSourceReuseTests(unittest.TestCase):
    def test_aoi_soil_sources_are_prepared_once_and_reused_for_exact_stratum_overlay(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.0,-3.1,-54.9,-3.0)],crs="EPSG:4326")
        raw_paths={i:Path(f"horizon_{i}.tif") for i in range(2,7)}
        official={"paths":{"lower":{i:Path(f"lo_{i}.tif") for i in range(2,7)},
                            "upper":{i:Path(f"hi_{i}.tif") for i in range(2,7)}},
                  "provenance":{"source":"fixture"}}
        with patch("soil_pronasolos_zonal.verified_local_horizons",return_value=raw_paths) as local, \
             patch("soil_soc_official_uncertainty.fetch_official_bounds",return_value=official) as bounds:
            prepared=desktop_app._prepare_pronasolos_sources(aoi)
        local.assert_called_once()
        bounds.assert_called_once()
        self.assertEqual(prepared["paths"],raw_paths)
        self.assertEqual(prepared["official_paths"],official["paths"])

        expected={"0–100 cm":{"tc_ha":83.0},"_diagnostic":{"target_status":"OK"}}
        with patch("soil_pronasolos_zonal.mapped_soil_0_100_on_polygon",return_value=expected) as overlay:
            got=desktop_app.pronasolos_soc_profiles(aoi,prepared=prepared)
        self.assertIs(got,expected)
        overlay.assert_called_once()
        self.assertEqual(overlay.call_args.kwargs["official_bound_paths"],official["paths"])


if __name__=="__main__":
    unittest.main()
