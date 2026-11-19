"""Synthetic routing regression: FH L2A pixels must reach the automatic pipeline.

The mocked FH raster values are test fixtures, not measured field data.
Live MAAP FH evidence remains a separate GitHub Actions job.
"""
import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

import sar_pipeline as sp
from desktop_app import App, _sar_dashboard_payload
from native_carbon import estimate_native_components, summarize_native_carbon


class _Tree:
    def __init__(self): self.rows=[]
    def get_children(self, *_): return list(range(len(self.rows)))
    def delete(self, item): pass
    def insert(self, *args, values): self.rows.append(values)


class _Var:
    def __init__(self): self.value=""
    def set(self, value): self.value=value


class _Text:
    def __init__(self): self.value=""


class AutomaticFHL2ATests(unittest.TestCase):
    def test_real_fh_l2a_route_preserves_product_and_zonal_height(self):
        aoi=gpd.GeoDataFrame(
            geometry=[box(-55.21,-11.89,-55.17,-11.85)],crs="EPSG:4326")
        item={"id":"BIOMASS_FP_FH__L2A_SYNTHETIC",
              "_product_type":"FP_FH__L2A",
              "_collection":"BiomassLevel2a",
              "_stage":"OPERATIONAL_L2A",
              "assets":{}}
        predicted={"status":"SAR_MODELED_EXPERIMENTAL",
                   "agb_mg_ha":120.0,
                   "uncertainty_mg_ha":None,
                   "data_origin":"SYNTHETIC_TEST_ONLY"}
        with patch.object(sp,"national_predictive_route_matrix",return_value={}), \
             patch.object(sp,"biomass_l2b_search",return_value=[item]) as catalog_search, \
             patch.object(sp,"download_maap_height",
                          return_value={"available":True,"paths":["/test/FP_FH__L2A_height.tif"],
                                        "fh_items":1}) as downloader, \
             patch.object(sp,"role",return_value="HEIGHT"), \
             patch.object(sp,"_zonal",return_value={"mean":21.5,"sd":4.3,
                                                     "n":1200,"min":4.0,"max":36.0}), \
             patch.object(sp,"tapajos_h100_structure_agb",return_value=predicted):
            result=sp.automatic_pipeline(
                aoi,"Amazônia","Floresta Estacional Sempre-Verde",cache="/tmp/enform-fh-test",
                biomass_catalog_items=[item],
                biomass_search_audit={"queries":[
                    {"product_type":"FP_FH__L2A","catalog_search_complete":True,
                     "pagination_complete":True}],
                    "errors":[],"height_queries_complete":True,
                    "height_catalog_item_count":1})
        catalog_search.assert_not_called()
        self.assertTrue(downloader.called)
        self.assertEqual(result["sar_height"]["product"],"FP_FH__L2A")
        self.assertEqual(result["height_mean_m"],21.5)
        self.assertEqual(result["height_n_valid_pixels"],1200)
        self.assertEqual(result["height_route_status"],"ALTURA_SAR_PROCESSADA")
        self.assertFalse(result["sar_height"]["height_interpretation"]
                         ["agb_inference_permitted"])
        self.assertEqual(result["audit"]["biomass_height_catalog"]["fh_count"],1)
        self.assertIn("FP_FH__L2A",result["audit"]["biomass_l2b"]
                      ["products_discovered"])
        self.assertEqual(result["data_origin"],"SYNTHETIC_TEST_ONLY")

    def test_fh_inventory_agb_reaches_executive_panel_and_report(self):
        """One complete synthetic regression from FH pixels through the rendered carbon panel.

        The FH zonal values are fixtures. This proves software handoff only;
        live Sinop FH pixel access is checked by its separate Actions job.
        """
        import desktop_app as ui
        aoi=gpd.GeoDataFrame(geometry=[box(-54.98049,-2.93999,-54.97841,-2.93351)],
                             crs="EPSG:4326")
        item={"id":"BIOMASS_FP_FH__L2A_DASHBOARD_FIXTURE",
              "_product_type":"FP_FH__L2A","_collection":"BiomassLevel2a",
              "_stage":"OPERATIONAL_L2A","assets":{}}
        with patch.object(sp,"national_predictive_route_matrix",return_value={}), \
             patch.object(sp,"download_maap_height",return_value={
                 "available":True,"paths":["/test/FP_FH__L2A_height.tif"],"fh_items":1}), \
             patch.object(sp,"role",return_value="HEIGHT"), \
             patch.object(sp,"_zonal",return_value={"mean":31.162,"sd":2.1,
                                                     "n":8,"min":27.0,"max":34.0}):
            sar=sp.automatic_pipeline(
                aoi,"Amazônia","Floresta Ombrófila Densa",cache="/tmp/enform-fh-dashboard",
                biomass_catalog_items=[item],biomass_search_audit={
                    "queries":[{"product_type":"FP_FH__L2A",
                                 "catalog_search_complete":True,"pagination_complete":True}],
                    "errors":[],"height_queries_complete":True,"height_catalog_item_count":1})
        self.assertEqual(sar["data_origin"],"SAR_P_HEIGHT_X_INVENTORY_STRUCTURE")
        self.assertEqual(sar["height_n_valid_pixels"],8)
        self.assertEqual(sar["sar_height"]["product"],"FP_FH__L2A")

        native=summarize_native_carbon(
            aoi,gpd.GeoDataFrame({"class_name":["Floresta Ombrófila Densa"],
                                  "source":["SAR_VALIDADO+IBGE"]},geometry=aoi.geometry,crs=aoi.crs),
            lambda frame,phys: estimate_native_components(
                frame,phys,"Amazônia",lambda *_:sar,lambda *_:{}))
        stratum=native["strata"][0]
        agb=next(row for row in stratum["components"] if row["parametro"]=="Biomassa aérea")
        self.assertAlmostEqual(agb["tc"],sar["agb_mg_ha"]*.47)

        land={"status":"SAR_PROCESSADO","recent_sar_cover":{"status":"PROCESSADO"}}
        payload=_sar_dashboard_payload(native,land)
        json.dumps(sar,ensure_ascii=False,default=str)
        json.dumps(payload,ensure_ascii=False,default=str)
        self.assertEqual(payload["height_products"][0]["product"],"FP_FH__L2A")
        self.assertEqual(payload["height_products"][0]["agb_data_origin"],
                         "SAR_P_HEIGHT_X_INVENTORY_STRUCTURE")
        with tempfile.TemporaryDirectory() as tmp:
            vector=Path(tmp)/"land.geojson"
            vector.write_text("{}",encoding="utf-8")
            land["vector_path"]=str(vector)
            table=_Tree(); report=_Text(); summary=_Var()
            app=SimpleNamespace(
                project={"version":"test","sar_result":payload,"land_use":land},
                carbon_dashboard_table=table,res=report,overall_exec_var=summary,
                status=_Var(),nb=SimpleNamespace(select=lambda *_:None),tabs=[None,None,None,"carbon"],
                _set=lambda widget,value:setattr(widget,"value",value),_map_provider="test",
                _populate_carbon_dashboard=lambda result:App._populate_carbon_dashboard(app,result),
                _refresh_overall_executive_summary=lambda:App._refresh_overall_executive_summary(app),
                biome=SimpleNamespace(get=lambda:"Amazônia"),
                _executive_excerpt=lambda text,labels:text[:2500])
            with patch.object(ui,"land_use_report_lines",return_value=[]):
                App._present_native_carbon(app,native,land)
            aerial=next(row for row in table.rows if row[0]=="Biomassa aérea")
            self.assertIn("FP_FH__L2A",report.value)
            self.assertIn("Altura FH",summary.value)
            self.assertIn("31,16",report.value)
            self.assertIn("Biomassa aérea",aerial[0])
            self.assertIn("SAR_P_HEIGHT_X_INVENTORY_STRUCTURE",report.value)


if __name__=="__main__":
    unittest.main()
