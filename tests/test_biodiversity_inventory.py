import math
import tempfile
import unittest
from pathlib import Path

from biodiversity_inventory import (load_biodiversity_inventory_csv,
    plot_agb_reference_chave2014, summarize_top10_species)


def records(design="simple random"):
    out=[]
    common_names={"Araucaria angustifolia":"araucária", "Ocotea puberula":"canela-guaicá",
                  "Cedrela fissilis":"cedro-rosa"}
    for plot, species in (
        ("P1", {"Araucaria angustifolia": [20, 10], "Ocotea puberula": [10]}),
        ("P2", {"Araucaria angustifolia": [20], "Cedrela fissilis": [15]}),
        ("P3", {"Araucaria angustifolia": [10], "Ocotea puberula": [10]}),
    ):
        for sp, values in species.items():
            for d in values:
                out.append({"inventory_id":"I1","plot_id":plot,"plot_area_ha":"0.1",
                    "biome":"Amazônia","physiognomy":"FESV","microregion":"Sinop",
                    "species":sp,"scientific_name":sp,"common_name":common_names[sp],
                    "dbh_cm":str(d),"status":"alive",
                    "inclusion_threshold_dap_cm":"5","sampling_design":design,
                    "institution":"Instituição","source_url":"https://example.org/inventory",
                    "licensed_for_use":"true"})
    return out


class BiodiversityInventoryTests(unittest.TestCase):
    def test_published_chave_reference_uses_measured_tree_height_and_wood_density(self):
        row={"status":"alive","dbh_cm":20,"height_m":15,"wood_density_g_cm3":0.6}
        result=plot_agb_reference_chave2014([row],plot_area_ha=0.1)
        expected=0.0673*(0.6*20**2*15)**0.976/1000/0.1
        self.assertAlmostEqual(result["agb_ref_mg_ha"],expected)
        self.assertFalse(result["property_observation"])
        self.assertIn("NAO_VALIDACAO_LOCAL",result["status"])

    def test_published_reference_does_not_impute_missing_tree_measurements(self):
        with self.assertRaisesRegex(ValueError,"DAP, altura medida e densidade"):
            plot_agb_reference_chave2014([{"status":"alive","dbh_cm":20}],plot_area_ha=0.1)

    def test_top10_is_ranked_by_mean_basal_area_and_shows_both_names(self):
        result=summarize_top10_species(records(),biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        self.assertEqual(result["status"],"REFERENCIA_FITOSSOCIOLOGICA_REGIONAL")
        rows={r["species"]:r for r in result["top10_by_dominance"]}
        self.assertEqual(rows["Araucaria angustifolia"]["plot_incidence_n"],3)
        self.assertEqual(rows["Araucaria angustifolia"]["common_name"],"araucária")
        self.assertEqual(rows["Araucaria angustifolia"]["scientific_name"],"Araucaria angustifolia")
        expected=2*(math.pi*(0.2/2)**2)+2*math.pi*(0.1/2)**2
        self.assertAlmostEqual(rows["Araucaria angustifolia"]["mean_basal_area_m2_ha"],expected/3/0.1)
        self.assertEqual(result["geographic_scope"],"MICRORREGIONAL")
        self.assertEqual(len(result["community_ci95_source_region_m2_ha"]),2)
        self.assertFalse(result["property_observation"])

    def test_no_compatible_physiognomy_or_microregion_returns_nd(self):
        result=summarize_top10_species(records(),biome="Amazônia",physiognomy="Cerrado",microregion="Sinop")
        self.assertEqual(result["status"],"N/D")
        self.assertEqual(result["reason"],"SEM_INVENTARIO_COMPATIVEL_NA_FITOFISIONOMIA_E_MICRORREGIAO")

    def test_non_simple_sampling_design_does_not_claim_ci95(self):
        result=summarize_top10_species(records("systematic clustered"),biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        self.assertIsNone(result["community_ci95_source_region_m2_ha"])
        self.assertTrue(all(row["ci95_source_region_m2_ha"] is None for row in result["top10_by_dominance"]))

    def test_uses_same_biome_and_physiognomy_regional_fallback_and_marks_scope(self):
        rows=records()
        for row in rows:row["microregion"]="Outra microrregião"
        result=summarize_top10_species(rows,biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        self.assertEqual(result["status"],"REFERENCIA_FITOSSOCIOLOGICA_REGIONAL")
        self.assertEqual(result["geographic_scope"],"REGIONAL")
        self.assertEqual(result["source_microregions"],["Outra microrregião"])

    def test_inventory_height_distribution_is_reported_as_regional_tree_height_reference(self):
        rows=records()
        for row in rows:row["height_m"]="12"
        result=summarize_top10_species(rows,biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        height=result["inventory_tree_height_distribution"]
        self.assertEqual(height["status"],"REFERENCIA_ALTURA_INVENTARIO_REGIONAL")
        self.assertFalse("SAR" in height["status"])
        self.assertEqual(height["bins"][2]["mean_frequency_pct"],100)

    def test_csv_requires_provenance_licensing_and_inclusion_threshold(self):
        row=records()[0]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"inventory.csv"
            import csv
            with path.open("w",newline="",encoding="utf-8") as stream:
                w=csv.DictWriter(stream,fieldnames=list(row));w.writeheader();w.writerow(row)
            loaded=load_biodiversity_inventory_csv(path)
            self.assertEqual(len(loaded),1)
            self.assertEqual(loaded[0]["scientific_name"],"Araucaria angustifolia")
            row["licensed_for_use"]="false"
            with path.open("w",newline="",encoding="utf-8") as stream:
                w=csv.DictWriter(stream,fieldnames=list(row));w.writeheader();w.writerow(row)
            with self.assertRaisesRegex(ValueError,"licença"):
                load_biodiversity_inventory_csv(path)

    def test_legacy_published_taxon_is_not_falsely_labeled_scientific(self):
        row=records()[0]
        row.pop("scientific_name")
        row["species"]="araucária"
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"legacy.csv"
            import csv
            with path.open("w",newline="",encoding="utf-8") as stream:
                w=csv.DictWriter(stream,fieldnames=list(row));w.writeheader();w.writerow(row)
            loaded=load_biodiversity_inventory_csv(path)
        self.assertEqual(loaded[0]["name_as_published"],"araucária")
        self.assertTrue(loaded[0]["scientific_name"].startswith("N/D"))


if __name__ == "__main__":
    unittest.main()
