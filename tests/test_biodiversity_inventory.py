import math
import tempfile
import unittest
from pathlib import Path

from biodiversity_inventory import (load_biodiversity_inventory_csv,
    plot_agb_reference_chave2014, summarize_top10_species)


def records(design="simple random"):
    out=[]
    for plot, species in (
        ("P1", {"Species A": [20, 10], "Species B": [10]}),
        ("P2", {"Species A": [20], "Species C": [15]}),
        ("P3", {"Species A": [10], "Species B": [10]}),
    ):
        for sp, values in species.items():
            for d in values:
                out.append({"inventory_id":"I1","plot_id":plot,"plot_area_ha":"0.1",
                    "biome":"Amazônia","physiognomy":"FESV","microregion":"Sinop",
                    "species":sp,"dbh_cm":str(d),"status":"alive",
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

    def test_top10_is_ranked_by_plot_incidence_and_basal_area_is_expanded_by_plot_area(self):
        result=summarize_top10_species(records(),biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        self.assertEqual(result["status"],"REFERENCIA_FITOSSOCIOLOGICA_REGIONAL")
        rows={r["species"]:r for r in result["top10_by_plot_incidence"]}
        self.assertEqual(rows["Species A"]["plot_incidence_n"],3)
        expected=2*(math.pi*(0.2/2)**2)+2*math.pi*(0.1/2)**2
        self.assertAlmostEqual(rows["Species A"]["mean_basal_area_m2_ha"],expected/3/0.1)
        self.assertEqual(len(result["community_ci95_source_region_m2_ha"]),2)
        self.assertFalse(result["property_observation"])

    def test_no_compatible_physiognomy_or_microregion_returns_nd(self):
        result=summarize_top10_species(records(),biome="Amazônia",physiognomy="Cerrado",microregion="Sinop")
        self.assertEqual(result["status"],"N/D")
        self.assertEqual(result["reason"],"SEM_INVENTARIO_COMPATIVEL_NA_FITOFISIONOMIA_E_MICRORREGIAO")

    def test_non_simple_sampling_design_does_not_claim_ci95(self):
        result=summarize_top10_species(records("systematic clustered"),biome="Amazônia",physiognomy="FESV",microregion="Sinop")
        self.assertIsNone(result["community_ci95_source_region_m2_ha"])
        self.assertTrue(all(row["ci95_source_region_m2_ha"] is None for row in result["top10_by_plot_incidence"]))

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
            self.assertEqual(len(load_biodiversity_inventory_csv(path)),1)
            row["licensed_for_use"]="false"
            with path.open("w",newline="",encoding="utf-8") as stream:
                w=csv.DictWriter(stream,fieldnames=list(row));w.writeheader();w.writerow(row)
            with self.assertRaisesRegex(ValueError,"licença"):
                load_biodiversity_inventory_csv(path)


if __name__ == "__main__":
    unittest.main()
