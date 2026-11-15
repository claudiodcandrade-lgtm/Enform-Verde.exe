"""Synthetic unit contracts, not satellite availability or field validation."""
import unittest
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from native_biomass_sentinel1_height import (sentinel1_structure_features,
                                             combine_biomass_sentinel1_height)
from land_use_sar import name_native_from_ibge
from native_carbon import native_class


class NativeSARProximityFusionTests(unittest.TestCase):
    def test_sar_validated_forest_near_ibge_compatible_is_named_with_distance(self):
        sar=gpd.GeoDataFrame([dict(class_name="Floresta",source="SAR_VALIDADO",
                                   taxonomy="SAR",geometry=box(0,0,10,10))],crs="EPSG:6933")
        ibge=gpd.GeoDataFrame([dict(class_name="Savana Arborizada",
                                    geometry=box(11,0,20,10)),
                                dict(class_name="Floresta Ombrófila Densa",
                                     geometry=box(70,0,80,10))],crs="EPSG:6933")
        rows=name_native_from_ibge(sar,ibge,max_proximity_m=100)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows.iloc[0].class_name,"Floresta Ombrófila Densa")
        self.assertEqual(rows.iloc[0].source,"SAR_VALIDADO+IBGE_PROXIMIDADE")
        self.assertIn("distância",rows.iloc[0].taxonomy)
        self.assertAlmostEqual(rows.geometry.area.sum(),100)
        self.assertTrue(native_class(rows.iloc[0].class_name,rows.iloc[0].source))

    def test_nearest_out_of_range_cannot_relabel(self):
        sar=gpd.GeoDataFrame([dict(class_name="Floresta",source="SAR_VALIDADO",
                                   taxonomy="SAR",geometry=box(0,0,10,10))],crs="EPSG:6933")
        ibge=gpd.GeoDataFrame([dict(class_name="Floresta Ombrófila Densa",
                                    geometry=box(300,0,320,10))],crs="EPSG:6933")
        rows=name_native_from_ibge(sar,ibge,max_proximity_m=100)
        self.assertEqual(rows.iloc[0].class_name,"Floresta")
        self.assertEqual(rows.iloc[0].source,"SAR_VALIDADO")

    def test_sentinel1_backscatter_texture_is_not_height_or_native_confirmation(self):
        vv=np.full((6,6),0.3)
        vh=np.linspace(.04,.12,36).reshape(6,6)
        f=sentinel1_structure_features(vv,vh)
        self.assertEqual(f["status"],"PIXELS_SAR_ESTRUTURAIS_PROCESSADOS")
        self.assertGreater(f["neighbor_rms_contrast_db"],0)
        self.assertFalse(f["native_presence_confirmed"])
        self.assertFalse(f["height_measured"])

    def test_direct_biomass_height_survives_without_s1_and_unvalidated_model(self):
        fh=dict(product="FP_FH__L2B",height_mean_m=28.4,height_n_valid_pixels=32,
                height_metric="H100",height_standard_error_pixel_zonal_mean_m=2.4)
        direct=combine_biomass_sentinel1_height(fh)
        self.assertEqual(direct["status"],"ALTURA_BIOMASS_DIRETA")
        self.assertEqual(direct["height_mean_m"],28.4)
        obs=sentinel1_structure_features(np.full((4,4),.2),
                                          np.linspace(.04,.10,16).reshape(4,4))
        conditioned=combine_biomass_sentinel1_height(fh,obs,
                                 residual_model={"coefficients":{"intercept_m":5},
                                                 "holdout_rmse_m":2.5})
        self.assertEqual(conditioned["height_mean_m"],28.4)
        self.assertEqual(conditioned["correction_status"],"BLOQUEADA_SEM_VALIDACAO_COMPATIVEL")

    def test_block_when_height_only_from_backscatter(self):
        f=sentinel1_structure_features(np.full((4,4),.2),np.full((4,4),.06))
        out=combine_biomass_sentinel1_height(None,f)
        self.assertIsNone(out["height_mean_m"])


if __name__=="__main__":
    unittest.main()
