import tempfile
import unittest
import csv
from pathlib import Path

from national_inventory_database import (
    discover_ckan_datasets,
    initialize_database,
    query_inventory_candidates,
    rank_inventory_candidates,
    register_discovered_records,
)


class NationalInventoryDatabaseTests(unittest.TestCase):
    def test_seed_is_skipped_when_manifest_is_unchanged(self):
        from unittest.mock import patch
        import national_inventory_database as catalog
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"catalog.sqlite"
            initialize_database(db)
            with patch.object(catalog,"_read_csv",wraps=catalog._read_csv) as reader:
                initialize_database(db)
            loaded=[Path(call.args[0]).name for call in reader.call_args_list]
            self.assertEqual(loaded,["national_inventory_portals_v1.csv"])

    def test_on_demand_catalog_query_is_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"catalog.sqlite"
            initialize_database(db)
            result=query_inventory_candidates(db,biome="Amazônia",
                physiognomy="Floresta Ombrófila Densa",limit=3)
            self.assertLessEqual(len(result),3)
            import sqlite3
            with self.assertRaises(sqlite3.OperationalError):
                uri=db.resolve().as_uri()+"?mode=ro"
                conn=sqlite3.connect(uri,uri=True)
                try:conn.execute("DELETE FROM inventory_records")
                finally:conn.close()

    def test_priority_research_sources_are_registered(self):
        with Path("data/national_inventory_portals_v1.csv").open(encoding="utf-8-sig",newline="") as f:
            portals={r["source_id"] for r in csv.DictReader(f)}
        expected={"EMBRAPA_FLORESTAS","EMBRAPA_AMAZONIA_ORIENTAL","EMBRAPA_PANTANAL",
            "EMBRAPA_CERRADOS","EMBRAPA_SEMIARIDO","INPA_REPOSITORY","UFV_LOCUS",
            "SIF_UFV","UFPR_ACERVO","UFLA_RIUFLA","IEF_MG_INVENTARIO","USP_ESALQ",
            "MUSEU_GOELDI","JBRJ_RESEARCH","VALE_RESERVA_NATURAL",
            "ICMBIO_DADOS_ABERTOS","ICMBIO_PLANOS_UC"}
        self.assertTrue(expected.issubset(portals))
        with Path("data/structural_inventory_sources_v1.csv").open(encoding="utf-8-sig",newline="") as f:
            sources={r["source_id"] for r in csv.DictReader(f)}
        self.assertTrue({"EMBRAPA_AO_MFT_MONITORING","RIPARIA_EMBRAPA_UNB_CAPAOZINHO_1993",
            "EMBRAPA_SEMIARIDO_CAATINGA_10PLOTS_2014","IEF_UFLA_MG_IF_2008_CERRADO",
            "INPA_PDBFF_CENSUS_1987_1989","VALE_RNV_TABULEIRO_PUBLICATIONS",
            "ICMBIO_FLONA_TAPAJOS_2012_204"}.issubset(sources))

    def test_uc_inventory_is_aggregate_not_plot_microdata(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"catalog.sqlite"
            initialize_database(db)
            conn=sqlite3.connect(db)
            try:
                row=conn.execute("SELECT plot_count, model_eligible, harvest_status, structural_metrics_json "
                    "FROM inventory_records WHERE record_id=?",
                    ("aggregate:ICMBIO_FLONA_TAPAJOS_2012_área_1_densidade",)).fetchone()
            finally:
                conn.close()
        self.assertEqual(row[0],94)
        self.assertEqual(row[1],0)
        self.assertEqual(row[2],"REFERENCIA_PUBLICADA_NAO_HARMONIZADA")
        self.assertIn("272.47",row[3])

    def test_local_catalog_separates_portals_and_loaded_plot_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"inventories.sqlite"
            summary=initialize_database(db)
            self.assertGreaterEqual(summary["portal_count"],15)
            # IFN DAP10 and ORNL/Tapajós are both locally harmonized at
            # plot level; neither count includes SINAFLOR aggregates or leads.
            self.assertEqual(summary["locally_harmonized_plot_level_datasets"],2)
            self.assertEqual(summary["published_aggregate_records"],32)
            self.assertGreaterEqual(summary["catalog_record_count"],77)
            self.assertEqual(summary["curated_public_dataset_records"],30)
            with Path("data/national_inventory_datasets_v1.csv").open(encoding="utf-8-sig",newline="") as f:
                sinaflor=next(r for r in csv.DictReader(f) if r["dataset_id"]=="SINAFLOR_PMFS_AMAZONIA")
            self.assertEqual(sinaflor["current_harvest_status"],"downloaded_sanitized_summary")
            tapajos=query_inventory_candidates(db,biome="Amazônia",
                physiognomy="Floresta Ombrófila Densa de terra firme",limit=200)
            records={r["record_id"]:r for r in tapajos}
            self.assertIn("aggregate:ICMBIO_FLONA_TAPAJOS_2012_área_1_densidade",records)
            self.assertFalse(records["aggregate:ICMBIO_FLONA_TAPAJOS_2012_área_1_densidade"]["model_eligible"])
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

    def test_verified_agency_attachment_is_last_resort_and_unverified_process_is_not_enough(self):
        rows=[
            {"record_id":"accepted_attachment","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
             "longitude":-55.0,"latitude":-3.0,"data_level":"published_aggregate","published_mean":22,
             "agency_inventory_acceptance_verified":True,"inventory_document_url":"https://example.test/inv.pdf",
             "inventory_document_sha256":"a"*64,"inventory_document_official_repository_verified":True,
             "acceptance_evidence_url":"https://example.test/decision.pdf",
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

    def test_approved_sinaflor_pmfs_establishes_underlying_inventory_acceptance(self):
        rows=[{
            "record_id":"pmfs_inventory","source_id":"IBAMA_SINAFLOR",
            "biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
            "record_type":"sinaflor_pmfs_inventory","data_level":"published_aggregate",
            "published_mean":31.0,"pmfs_approval_verified":True,
            "plan_approval_evidence_url":"https://official.example/pmfs-decision.pdf",
            "inventory_document_url":"https://official.example/inventory.pdf",
            "inventory_document_sha256":"b"*64,"inventory_document_official_repository_verified":True,
            "method_and_units_verified":True,
        },{
            "record_id":"unapproved_pmfs","source_id":"IBAMA_SINAFLOR",
            "biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa",
            "record_type":"sinaflor_pmfs_inventory","data_level":"published_aggregate",
            "published_mean":99.0,"pmfs_approval_verified":False,
            "inventory_document_url":"https://official.example/unapproved.pdf",
            "inventory_document_sha256":"c"*64,"method_and_units_verified":True,
        }]
        ranked=rank_inventory_candidates(rows,biome="Amazônia",
            physiognomy="Floresta Ombrófila Densa")
        by_id={r["record_id"]:r for r in ranked}
        self.assertTrue(by_id["pmfs_inventory"]["verified_accepted_agency_inventory"])
        self.assertEqual(by_id["pmfs_inventory"]["selection_priority"],3)
        self.assertFalse(by_id["unapproved_pmfs"]["verified_accepted_agency_inventory"])

    def test_approved_environmental_license_accepts_its_linked_inventory(self):
        rows=[{
            "record_id":"approved_license_inventory","source_id":"IBAMA_LICENCIAMENTO",
            "biome":"Cerrado","physiognomy":"Cerrado sensu stricto",
            "record_type":"approved_environmental_license_inventory",
            "data_level":"published_aggregate","published_mean":18.5,
            "environmental_approval_verified":True,
            "approval_source_official_verified":True,
            "approval_evidence_url":"https://official.example/license-decision.pdf",
            "inventory_document_url":"https://official.example/annex/inventory.pdf",
            "inventory_document_sha256":"d"*64,"inventory_document_official_repository_verified":True,
            "method_and_units_verified":True,
        },{
            "record_id":"approved_license_without_hash","source_id":"IBAMA_LICENCIAMENTO",
            "biome":"Cerrado","physiognomy":"Cerrado sensu stricto",
            "record_type":"approved_environmental_license_inventory",
            "data_level":"published_aggregate","published_mean":18.5,
            "environmental_approval_verified":True,
            "approval_source_official_verified":True,
            "approval_evidence_url":"https://official.example/license-decision.pdf",
            "inventory_document_url":"https://official.example/annex/inventory.pdf",
            "inventory_document_sha256":"missing","inventory_document_official_repository_verified":True,
            "method_and_units_verified":True,
        }]
        ranked=rank_inventory_candidates(rows,biome="Cerrado",
            physiognomy="Cerrado sensu stricto")
        by_id={r["record_id"]:r for r in ranked}
        self.assertTrue(by_id["approved_license_inventory"]["verified_accepted_agency_inventory"])
        self.assertEqual(by_id["approved_license_inventory"]["selection_priority"],3)
        self.assertFalse(by_id["approved_license_without_hash"]["verified_accepted_agency_inventory"])

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
            conn = sqlite3.connect(db)
            try:
                row=conn.execute("SELECT harvest_status,evidence_status,model_eligible FROM inventory_records WHERE record_id='SFB_IFN:ifn-test'").fetchone()
            finally:
                conn.close()
            self.assertEqual(row,("METADADO_DESCOBERTO_NAO_BAIXADO","NAO_TRIADO_NAO_ELEGIVEL",0))


if __name__=="__main__":unittest.main()
