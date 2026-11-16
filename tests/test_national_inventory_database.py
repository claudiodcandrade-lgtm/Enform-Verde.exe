import tempfile
import unittest
from pathlib import Path

from national_inventory_database import (
    discover_ckan_datasets,
    initialize_database,
    rank_inventory_candidates,
    register_discovered_records,
)


class NationalInventoryDatabaseTests(unittest.TestCase):
    def test_local_catalog_separates_portals_and_loaded_plot_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"inventories.sqlite"
            summary=initialize_database(db)
            self.assertGreaterEqual(summary["portal_count"],15)
            self.assertEqual(summary["locally_harmonized_plot_level_datasets"],1)
            self.assertEqual(summary["published_aggregate_records"],27)
            self.assertGreaterEqual(summary["catalog_record_count"],77)
            self.assertEqual(summary["curated_public_dataset_records"],20)
            counts=summary["observed_official_counts"]
            self.assertEqual(counts["SINAFLOR_PMFS_AMAZONIA"]["distinct_registry_ids"],1508)
            self.assertEqual(counts["SINAFLOR_VOLUMES_IF100"]["source_record_rows"],2438833)
            self.assertEqual(counts["IBAMA_LICENSES_FEDERAL"]["distinct_federal_process_ids"],2532)

    def test_selection_requires_exact_physiognomy_and_prioritizes_open_georeferenced_plots(self):
        rows=[
            {"record_id":"near_aggregate","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
             "longitude":-55.0,"latitude":-3.0,"open_data":0,"georeferenced":0,"data_level":"published_aggregate"},
            {"record_id":"far_open","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
             "longitude":-50.0,"latitude":-4.0,"open_data":1,"georeferenced":1,"data_level":"primary_tree","model_eligible":1},
            {"record_id":"wrong_phys","biome":"Amazônia","physiognomy":"Campinarana",
             "longitude":-55.0,"latitude":-3.0,"open_data":1,"georeferenced":1,"data_level":"primary_tree"},
        ]
        ranked=rank_inventory_candidates(rows,biome="Amazônia",
            physiognomy="Floresta Ombrófila Densa",longitude=-55.1,latitude=-3.0)
        self.assertEqual([r["record_id"] for r in ranked],["far_open","near_aggregate"])
        self.assertTrue(ranked[0]["open_georeferenced_plot_data"])
        self.assertLess(ranked[1]["distance_km"],ranked[0]["distance_km"])

    def test_verified_agency_attachment_is_last_resort_and_process_approval_is_not_enough(self):
        rows=[
            {"record_id":"accepted_attachment","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
             "longitude":-55.0,"latitude":-3.0,"data_level":"published_aggregate","published_mean":22,
             "agency_inventory_acceptance_verified":True,"inventory_document_url":"https://example.test/inv.pdf",
             "inventory_document_sha256":"a"*64,"acceptance_evidence_url":"https://example.test/decision.pdf",
             "method_and_units_verified":True},
            {"record_id":"license_only","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
             "longitude":-55.0,"latitude":-3.0,"data_level":"published_aggregate","published_mean":99,
             "agency_inventory_acceptance_verified":False,"accepted_by_agency":True},
        ]
        ranked=rank_inventory_candidates(rows,biome="Amazônia",physiognomy="Floresta Ombrófila Densa",
            longitude=-55.0,latitude=-3.0)
        self.assertEqual(ranked[0]["record_id"],"accepted_attachment")
        self.assertEqual(ranked[0]["selection_priority"],3)
        self.assertTrue(ranked[0]["verified_accepted_agency_inventory"])
        self.assertEqual(ranked[1]["selection_priority"],4)
        self.assertFalse(ranked[1]["verified_accepted_agency_inventory"])

    def test_ckan_discovery_paginates_and_deduplicates_without_downloading(self):
        class Response:
            def __init__(self,start):self.start=start
            def raise_for_status(self):pass
            def json(self):
                if self.start==0:
                    return {"success":True,"result":{"count":2,"results":[{"id":"a","title":"IFN A"}]}}
                return {"success":True,"result":{"count":2,"results":[{"id":"b","title":"IFN B"}]}}
        class Session:
            def __init__(self):self.calls=[]
            def get(self,url,params,timeout):
                self.calls.append((url,params["start"]))
                return Response(params["start"])
        session=Session()
        rows=discover_ckan_datasets("https://data.example/api/3/action",["IFN"],
            session=session,rows=1,max_pages=3)
        self.assertEqual([r["id"] for r in rows],["a","b"])
        self.assertEqual([x[1] for x in session.calls],[0,1])

    def test_discovered_records_are_leads_not_calibration_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"inventories.sqlite"
            initialize_database(db)
            added=register_discovered_records(db,"SFB_IFN",[
                {"id":"ifn-test","title":"Inventário florestal","url":"https://example.test/data"}])
            self.assertEqual(added,1)
            import sqlite3
            with sqlite3.connect(db) as conn:
                row=conn.execute("SELECT harvest_status,evidence_status,model_eligible FROM inventory_records WHERE record_id='SFB_IFN:ifn-test'").fetchone()
            self.assertEqual(row,("METADADO_DESCOBERTO_NAO_BAIXADO","NAO_TRIADO_NAO_ELEGIVEL",0))


if __name__=="__main__":unittest.main()
