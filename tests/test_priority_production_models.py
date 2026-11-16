"""Coverage contracts for the owner's priority production systems."""
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from priority_production_models import (TARGETS, PAM_CLIMATE_SCENARIO_CROPS,
    estimate_forage_dry_matter, estimate_wood_increment, integrated_system_components,
    model_contract, priority_target)
from crop_identifier_consolidated import CROPS
from crop_yield_scenario import load_microregion_yields


class PriorityProductionModelContracts(unittest.TestCase):
    def test_all_priority_targets_have_distinct_units_and_equations(self):
        required={"Milho","Soja","Arroz","Algodão","Pastagens","Cana-de-açúcar",
                  "Silvicultura","ILPF","ILP","IPF","Sorgo","Café","Feijão","Citros"}
        self.assertTrue(required.issubset(TARGETS))
        for target in required:
            route=model_contract(target)
            self.assertTrue(route["equation"])
            self.assertTrue(route["unit"])
            self.assertTrue(route["inputs"])
        self.assertIn("Algodão",CROPS)

    def test_category_aliases_and_distinct_output_units(self):
        self.assertEqual(priority_target("pasto"),"Pastagens")
        self.assertEqual(priority_target("Floresta plantada"),"Silvicultura")
        self.assertEqual(priority_target("ilpf"),"ILPF")
        self.assertNotEqual(TARGETS["Pastagens"]["unit"],TARGETS["ILP"]["unit"])
        self.assertIn("Arroz",PAM_CLIMATE_SCENARIO_CROPS)

    def test_forage_calculator_requires_observed_inputs_and_reports_unit(self):
        missing=estimate_forage_dry_matter([{"par_mj_m2":10}],rue_g_mj=1.5)
        self.assertEqual(missing["status"],"N/D")
        result=estimate_forage_dry_matter(
            [{"par_mj_m2":10,"fipar":.5,"water_stress":.8}],
            rue_g_mj=1.5,rue_sd_g_mj=.15)
        self.assertEqual(result["status"],"experimental")
        self.assertEqual(result["dry_matter_kg_ha"],60.0)
        self.assertEqual(result["uncertainty"],"parcial: apenas erro de RUE; demais fontes não propagadas")

    def test_forestry_increment_needs_two_inventories(self):
        missing=estimate_wood_increment(80,None,2)
        self.assertEqual(missing["status"],"N/D")
        result=estimate_wood_increment(80,110,3,start_sd=4,end_sd=5)
        self.assertEqual(result["annual_volume_increment_m3_ha_yr"],10)
        self.assertAlmostEqual(result["sd_m3_ha_yr"],(41**.5)/3)

    def test_integrated_outputs_remain_component_vector(self):
        result=integrated_system_components({"grao":{"value":4,"unit":"t/ha"},
            "forragem":{"value":3200,"unit":"kg MS/ha"}})
        self.assertEqual(result["status"],"experimental_components_only")
        self.assertEqual(result["system_interaction"],"N/D — requer experimento/coeficientes do sistema integrado")
        self.assertEqual(len(result["components"]),2)

    def test_cotton_history_uses_ibge_sidra_when_not_bundled(self):
        payload=[{"D3N":"Variável","D3C":"112"},
                 {"D3N":"2023","D3C":"2023","V":"4200"},
                 {"D3N":"2024","D3C":"2024","V":"4400"}]
        response=io.BytesIO(json.dumps(payload).encode("utf-8"))
        # Give the loader an explicitly empty bundle so this contract tests
        # the SIDRA fallback even when the production package ships newer PAM data.
        with tempfile.TemporaryDirectory() as tmp:
            pam_path=Path(tmp)/"empty_pam.csv.gz"
            with gzip.open(pam_path,"wt",encoding="utf-8",newline="") as stream:
                stream.write("")
            with patch("urllib.request.urlopen",return_value=response) as opened:
                values=load_microregion_yields("Algodão","51006",path=pam_path)
        self.assertEqual(values,{2023:4200.0,2024:4400.0})
        self.assertIn("n9/51006/v/112/p/2015-2024/c782/40099",opened.call_args.args[0].full_url)


if __name__=="__main__":
    unittest.main()
