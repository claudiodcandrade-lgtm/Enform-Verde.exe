"""SAR pipeline regression: actual local GeoTIFF windows, never full-scene reads.

These are synthetic test rasters, NOT measured crop accuracy or property masks.
"""
from datetime import date
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

import sar_landcover_lemplus as sl
from native_carbon import native_class


class FullSeasonRTCReaderTest(unittest.TestCase):
    def test_all_months_bounded_and_failed_pair_falls_back(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.20,-11.88,-55.19,-11.87)],crs=4326)
        months,season=sl.agricultural_year(date(2026,11,10))
        self.assertEqual(season,"2025/2026")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); feats=[]
            for i,(year,month) in enumerate(months):
                paths={}
                for pol,val in (("vv",.15+.005*i),("vh",.045+.002*i)):
                    name=root/f"{year}_{month}_{pol}.tif"
                    with rasterio.open(name,"w",driver="GTiff",width=120,height=120,
                            count=1,dtype="float32",crs="EPSG:4326",
                            transform=from_origin(-55.204,-11.866,0.00015,0.00015),
                            nodata=-9999) as dst:
                        values=np.full((120,120),val,dtype="float32")
                        values[:,60:]*=1.5
                        dst.write(values,1)
                    paths[pol]={"href":str(name)}
                if i==0:
                    feats.append({"id":"bad-first-scene",
                        "properties":{"datetime":f"{year}-{month:02d}-27T00:00:00Z",
                            "sat:relative_orbit":40,"sat:orbit_state":"ascending"},
                        "assets":{"vv":paths["vv"],"vh":{"href":str(root/"missing_vh.tif")}}})
                feats.append({"id":f"valid-{i}","properties":{
                    "datetime":f"{year}-{month:02d}-15T00:00:00Z",
                    "sat:relative_orbit":40,"sat:orbit_state":"ascending"},
                    "assets":paths})
            def search(*args):return feats
            with patch("sentinel1_mpc._signed_href",side_effect=lambda href,token:href):
                values, audit=sl._monthly_features(
                    aoi,months,search_fn=search,token_fn=lambda:"fixture")
            self.assertIsNotNone(values,str(audit))
            features,transform,shape=values
            self.assertEqual(features.shape[2],36)
            self.assertGreater(np.isfinite(features).all(-1).sum(),0)
            self.assertEqual(len(audit["observed_months"]),12)
            self.assertEqual(audit["scenes_used"],12)
            self.assertTrue(audit["pixel_read_errors"])
            self.assertLess(shape[0]*shape[1],50000)

    def test_missing_month_returns_diagnostic_not_fabricated_mask(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.20,-11.88,-55.19,-11.87)],crs=4326)
        months,_=sl.agricultural_year(date(2026,11,10))
        with patch("sentinel1_mpc._signed_href",side_effect=lambda h,t:h):
            result,audit=sl._monthly_features(aoi,months,search_fn=lambda *args:[],token_fn=lambda:"x")
        self.assertIsNone(result)
        self.assertEqual(audit["reason"],"NENHUMA_CENA_RTC_VV_VH")

    def test_geographic_provisional_domain_distinct_from_local_validation(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.20,-11.88,-55.19,-11.87)],crs=4326)
        eligible,reason=sl.in_validated_domain(None,aoi=aoi)
        self.assertTrue(eligible)
        self.assertIn("PROVISORIO",reason)
        metadata={"Formação florestal":{"parent":"vegetação natural"},
                  "Lavoura de Soja":{"parent":"uso não nativo"}}
        self.assertTrue(native_class("Formação florestal","SAR_EXPERIMENTAL_MODELO",metadata))
        self.assertFalse(native_class("Lavoura de Soja","SAR_EXPERIMENTAL_MODELO",metadata))
        self.assertIsNone(native_class("Formação florestal","IBGE",metadata))


if __name__=="__main__":
    unittest.main()
