import unittest
import tempfile
from pathlib import Path

from inventory_microdata_library import (summarize_inventory_microdata,
    official_inventory_database_status, select_official_inventory_units)
from national_inventory_database import initialize_database


class InventoryMicrodataLibraryTests(unittest.TestCase):
    def test_large_database_integrity_scan_is_cached_until_file_changes(self):
        import sqlite3
        from unittest.mock import patch
        import inventory_microdata_library as module
        module._official_inventory_database_status_cached.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"inventory.sqlite"
            path.write_bytes(b"same immutable database version")
            with patch("inventory_microdata_library.sqlite3.connect",
                       side_effect=sqlite3.OperationalError("test sentinel")) as connect:
                first=official_inventory_database_status(path)
                second=official_inventory_database_status(path)
            self.assertEqual(first["status"],"ERRO_LEITURA")
            self.assertEqual(second,first)
            connect.assert_called_once()
            path.write_bytes(b"replacement database version with a different size")
            with patch("inventory_microdata_library.sqlite3.connect",
                       side_effect=sqlite3.OperationalError("test sentinel")) as connect:
                official_inventory_database_status(path)
            connect.assert_called_once()

    def test_official_ifn_database_and_ibge_crosswalk_meet_full_selection_contract(self):
        status=official_inventory_database_status()
        self.assertEqual(status["status"],"PRONTO_PARA_SELECAO_DE_REFERENCIAS")
        self.assertTrue(status["operational_for_tree_selection"])
        self.assertEqual(status["observation_rows"],841387)
        self.assertEqual(status["sampling_units"],8951)
        self.assertEqual(status["source_workbooks"],27)
        self.assertEqual(status["ibge_unique_unit_matches"],8951)
        self.assertFalse(status["agb_or_canopy_height_estimator_available"])

    def test_ifn_selection_filters_location_biome_and_exact_ibge_legenda_1(self):
        import sqlite3
        from inventory_microdata_library import OFFICIAL_DB
        with sqlite3.connect(f"file:{OFFICIAL_DB.resolve()}?mode=ro",uri=True) as conn:
            unit=conn.execute("""SELECT s.biome,s.ua_center_lon,s.ua_center_lat,x.ibge_legenda_1,s.uf,s.ua_id
                FROM ifn_sampling_unit_summary s JOIN ifn_sampling_unit_ibge_crosswalk x
                ON x.ua_id=s.ua_id AND x.uf=s.uf
                WHERE x.match_status='MATCH_UNICO_PONTO_INTERIOR' AND s.biome IS NOT NULL
                AND x.ibge_legenda_1 IS NOT NULL ORDER BY s.uf,s.ua_id LIMIT 1""").fetchone()
        biome,lon,lat,physiognomy,uf,ua_id=unit
        result=select_official_inventory_units(biome=biome,physiognomy=physiognomy,
            longitude=lon,latitude=lat,max_distance_km=1,max_units=5)
        self.assertEqual(result["status"],"SELECAO_IFN_POR_LOCALIZACAO_BIOMA_FITOFISIONOMIA")
        self.assertEqual(result["units"][0]["uf"],uf)
        self.assertEqual(result["units"][0]["ua_id"],ua_id)
        self.assertEqual(result["units"][0]["distance_km"],0)
        self.assertTrue(all(row["biome"]==biome and row["ibge_legenda_1"]==physiognomy
                            for row in result["units"]))
        self.assertTrue(result["trees"])
        self.assertTrue(all(row["tree_coordinate_interpretation"]==
            "UA_CENTER_ONLY_NOT_INDIVIDUAL_TREE_COORDINATE" for row in result["trees"]))
        self.assertIn("não são métricas por hectare",result["interpretation"])
        bio=result["biodiversity_reference"]
        self.assertEqual(bio["status"],"INDICADOR_FITOSSOCIOLOGICO_IFN")
        self.assertLessEqual(len(bio["top_10_species_by_sampling_unit_frequency"]),10)
        self.assertTrue(all(0 < row["frequency_pct"] <= 100
                            for row in bio["top_10_species_by_sampling_unit_frequency"]))
        compact=select_official_inventory_units(biome=biome,physiognomy=physiognomy,
            longitude=lon,latitude=lat,max_distance_km=1,max_units=5,include_trees=False)
        self.assertEqual(compact["trees"],[])
        self.assertEqual(compact["biodiversity_reference"],bio)

    def test_wrong_physiognomy_cannot_select_ifn_tree_records(self):
        import sqlite3
        from inventory_microdata_library import OFFICIAL_DB, select_official_inventory_units
        with sqlite3.connect(f"file:{OFFICIAL_DB.resolve()}?mode=ro",uri=True) as conn:
            biome,lon,lat=conn.execute("""SELECT s.biome,s.ua_center_lon,s.ua_center_lat
                FROM ifn_sampling_unit_summary s WHERE s.biome IS NOT NULL
                AND s.ua_center_lon IS NOT NULL AND s.ua_center_lat IS NOT NULL LIMIT 1""").fetchone()
        result=select_official_inventory_units(biome=biome,physiognomy="FITOFISIONOMIA_INEXISTENTE",
            longitude=lon,latitude=lat,max_distance_km=250)
        self.assertEqual(result["status"],"N/D")
        self.assertEqual(result["reason"],"NO_IFN_UNIT_MATCHES_LOCATION_BIOME_PHYSIOGNOMY_AND_RADIUS")
        self.assertEqual(result["trees"],[])

    def test_mexiana_uses_confirmed_plot_area_and_keeps_nonspatial_status(self):
        data=summarize_inventory_microdata()
        mex=data["inventories"]["MX_SANTO_AMBROSIO_2025"]
        self.assertEqual(data["tree_record_count"],2390)
        self.assertEqual(mex["tree_record_count"],2144)
        self.assertEqual(mex["plot_count"],167)
        self.assertAlmostEqual(mex["mean_plot_agb_allometric_mg_ha"],418.66155,places=4)
        self.assertAlmostEqual(mex["mean_plot_basal_area_m2_ha"],36.42564,places=4)
        self.assertFalse(mex["plot_georeferenced"])
        self.assertFalse(mex["sar_pair_available"])
        self.assertIn("não separar FOD aluvial",mex["limitation"])
        self.assertIn("allométrica",mex["agb_kind"])

    def test_jalapao_keeps_area_normalized_metrics_unavailable(self):
        data=summarize_inventory_microdata()
        jal=data["inventories"]["CE_JALAPAO_FOREST_2026"]
        self.assertEqual(jal["tree_record_count"],246)
        self.assertEqual(jal["plot_count"],10)
        self.assertFalse(jal["area_normalized_metrics_available"])
        self.assertIsNone(jal["mean_plot_stems_ha"])
        self.assertIsNone(jal["mean_plot_basal_area_m2_ha"])
        self.assertFalse(jal["plot_georeferenced"])

    def test_catalog_registers_both_project_inventories_without_promoting_to_sar(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary=initialize_database(Path(tmp)/"inventories.sqlite")
            self.assertEqual(summary["locally_harmonized_project_inventory_datasets"],2)
            # The two owner-provided inventories plus IFN and ORNL/Tapajós
            # are local primary datasets. Only IFN and ORNL are plot-level
            # harmonized datasets; project files retain their limitations.
            self.assertEqual(summary["locally_usable_primary_inventory_datasets"],4)
            self.assertEqual(summary["locally_harmonized_plot_level_datasets"],2)


if __name__=="__main__":
    unittest.main()
