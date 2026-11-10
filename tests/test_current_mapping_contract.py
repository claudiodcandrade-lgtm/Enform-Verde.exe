"""Regression contracts for SAR-only current mapping and fail-closed unknowns."""
from pathlib import Path
import unittest


class CurrentMappingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.land = Path("land_use_sar.py").read_text(encoding="utf-8")
        cls.desktop = Path("desktop_app.py").read_text(encoding="utf-8")
        cls.crops = Path("crop_identifier_consolidated.py").read_text(encoding="utf-8")
        cls.monitor = Path("crop_monitoring_forecast.py").read_text(encoding="utf-8")
        cls.vigor = Path("crop_vigor_auto.py").read_text(encoding="utf-8")
        cls.vigor_math = Path("crop_vigor.py").read_text(encoding="utf-8")

    def test_mapbiomas_cannot_enter_current_land_use_layers(self):
        run = self.land[self.land.index("def run_land_use"):self.land.index("def report_lines")]
        self.assertIn("DESATIVADO: MapBiomas não participa", run)
        self.assertNotIn("raw_layers.append(mb.copy())", run)
        self.assertNotIn("layers.append(mb", run)
        self.assertNotIn("raster_class_polygons(aoi,source_path)", run)
        self.assertIn("MapBiomas é somente referência", self.land)

    def test_current_crop_identity_requires_validated_sar(self):
        self.assertNotIn("MAPBIOMAS_C11", self.crops)
        body = self.monitor[self.monitor.index("def crops_in_land_result"):self.monitor.index("def monitoring_forecast")]
        self.assertIn('return _crops_from_sar_source(land, "SAR_VALIDADO")', body)
        self.assertIn('return _crops_from_sar_source(land, "SAR_EXPERIMENTAL_MODELO")', body)
        self.assertIn('annual_experimental = bool(conditional_crops and not current_crops)', self.monitor)
        self.assertNotIn('source") == "MAPBIOMAS"', body)
        self.assertIn("PAM is a yield baseline", self.crops)

    def test_ibge_legend2_is_labeled_as_cartographic_reference(self):
        self.assertIn("Cobertura vegetal cartográfica IBGE (legenda_2; referência, não comprova cobertura atual)", self.desktop)

    def test_unknown_is_neither_native_zero_nor_non_native(self):
        self.assertIn('item.get("native_status") is False', self.desktop)
        self.assertNotIn('item.get("native_status") is not True', self.desktop)
        self.assertIn('else None)', self.desktop)
        self.assertIn("não significa 0 ha", self.desktop)
        self.assertIn("N/D_NOT_VERIFIABLE_WITHOUT_VALIDATED_SAR", self.land)

    def test_orbital_fallback_units_are_explicitly_unclassified(self):
        self.assertIn("run_recent_sar_screen(aoi,outdir)", self.land)
        self.assertIn("SAR_CURRENT_EXPERIMENTAL", self.land)
        self.assertIn("classe semântica N/D", self.land)
        self.assertIn("N/D_SEM_COBERTURA_SAR", self.land)

    def test_cbers_is_primary_optical_source(self):
        worker = self.desktop[self.desktop.index("        def worker():", self.desktop.index("def cbers4a_wfi_preview")):]
        self.assertLess(worker.index("cbers4a_wfi_preview(g,out_w=w"),
                        worker.index("sentinel2_earthsearch_preview(g,out_w=w"))
        self.assertLess(worker.index("sentinel2_earthsearch_preview(g,out_w=w"),
                        worker.index("sentinel2_preview(g,extent_factor=extent_factor)"))
        self.assertLess(worker.index("sentinel2_preview(g,extent_factor=extent_factor)"),
                        worker.index("nasa_gibs_preview(g,out_w=w"))
        self.assertLess(worker.index("nasa_gibs_preview(g,out_w=w"),
                        worker.index("_read_satellite_preview_cache"))
        self.assertLess(worker.index("_read_satellite_preview_cache"),
                        worker.index("offline_brazil_preview(g,extent_factor,(w,h))"))
        self.assertIn("CACHE ÓPTICO", worker)
        self.assertIn("NASA GIBS", worker)
        self.assertIn("strictly visual context", worker)
        self.assertIn("contingência excepcional", worker)
        self.assertIn("a origem não foi identificada como imagem óptica", worker)
        cbers = self.desktop[self.desktop.index("def cbers4a_wfi_preview"):self.desktop.index("\ndef ", self.desktop.index("def cbers4a_wfi_preview") + 8)]
        self.assertIn('keys=("BAND15","BAND14","BAND13")', cbers)
        self.assertIn('"CMASK"', cbers)
        self.assertIn('"aoi_coverage_fraction":aoi_coverage', cbers)

    def test_vigor_never_reads_mapbiomas_and_labels_rvi_proxy(self):
        # Owner policy 09/11/2026: experimental RVI size proxy allowed when no
        # height product exists, always labelled as such.
        self.assertNotIn("mapbiomas_zonal", self.vigor)
        self.assertNotIn("RASTER_URL", self.vigor)
        self.assertIn("height_provider", self.vigor)
        self.assertIn("EXPERIMENTAL_PROXY_RVI", self.vigor_math)

    def test_sar_classifier_has_class_level_evidence_gate(self):
        # Owner decision 08/11/2026: any measured accuracy accepted as
        # experimental; uncertainty (n + Wilson CI95) is mandatory.
        self.assertIn("MIN_VALIDATION = 1", self.land)
        self.assertIn("'precision_wilson95_lower'", self.land)
        self.assertIn("'n_independent'", self.land)


if __name__ == "__main__":
    unittest.main()

class CarbonExecutiveTable(unittest.TestCase):
    def test_stock_table_has_bounded_compartment_rows_and_statistical_total(self):
        from executive_carbon_report import executive_carbon_lines
        lines = executive_carbon_lines({
            "area_aoi_ha": 100.0, "native_area_ha": 100.0,
            "excluded_other_uses_ha": 0.0, "unknown_cover_area_ha": 0.0,
            "cover_completeness": "COMPLETE", "complete": True,
            "known_total_tc": 10.0,
            "total_uncertainty": {"se_tC": 1.0},
            "strata": [{"class_name": "Floresta", "area_ha": 100.0,
                "components": [{"parametro": "Biomassa aérea", "tc": 0.1,
                    "total_tc": 10.0, "quantified_area_ha": 100.0,
                    "range_tc_ha": [0.08, 0.12]}]}]},
            lambda x: f"{x:.2f}")
        text = "\n".join(lines)
        self.assertIn("COMPARTIMENTO / TOTAL", text)
        for name in ("Biomassa aérea", "Biomassa subterrânea", "Necromassa aérea",
                     "Necromassa subterrânea", "Serapilheira", "Solo 0–100 cm"):
            self.assertIn(name, text)
        self.assertIn("TOTAL — soma dos compartimentos", text)
        self.assertIn("0.10", text)
        self.assertIn("N/D", text)


if __name__ == "__main__":
    unittest.main()
