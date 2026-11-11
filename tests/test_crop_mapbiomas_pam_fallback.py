import unittest

from crop_mapbiomas_pam_fallback import build_mapbiomas_pam_contingency


def exhausted_land():
    return {
        "status": "ERRO_TECNICO_LEITURA_SAR",
        "classes": [{"source": "SEM_COBERTURA", "class_name": "Não classificado"}],
        "recent_sar_cover": {"status": "ERRO_TECNICO", "readable_scene_count": 0,
                             "pixel_read_attempt_count": 36, "reason": "SELECTED_SCENES_PIXEL_READ_FAILED"},
        "sar_classifier_lemplus": {"status": "N/D_SEM_PIXELS_SAR", "pixels": 0},
        "alternative_radar_screen": {"status": "ACESSO_RESTRITO",
                                     "routes_not_configured": ["NISAR"]},
        "native_sar_experimental": {"status": "N/D", "reason": "nenhum GeoTIFF SAR fornecido"},
    }


class CropMapBiomasPAMFallbackTests(unittest.TestCase):
    def test_fallback_is_blocked_until_all_configured_sar_routes_have_audits(self):
        calls=[]
        out=build_mapbiomas_pam_contingency(None, {"status":"ERRO_TECNICO_LEITURA_SAR"},
            map_reader=lambda _: calls.append("map") or {})
        self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")
        self.assertEqual(calls,[])

    def test_any_processed_sar_pixels_block_the_historical_fallback(self):
        land=exhausted_land()
        land["sar_classifier_lemplus"]={"status":"SAR_CLASSIFICADOR_EXPERIMENTAL","pixels":100}
        out=build_mapbiomas_pam_contingency(None,land,map_reader=lambda _: self.fail("must not read MapBiomas"))
        self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")

    def test_unexecuted_sar_classifier_blocks_the_historical_fallback(self):
        land=exhausted_land()
        land["sar_classifier_lemplus"]={"status":"NOT_EXECUTED",
                                        "reason":"primary model already produced output"}
        out=build_mapbiomas_pam_contingency(None,land,
            map_reader=lambda _: self.fail("MapBiomas must remain blocked"))
        self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")
        self.assertEqual(out["sar_gate"]["reason"],
                         "ROTA_SAR_NAO_EXECUTADA_OU_STATUS_NAO_TERMINAL")

    def test_exhausted_sar_uses_mapbiomas_area_and_regional_pam_as_historical_reference(self):
        land=exhausted_land()
        mapped={"collection":11,"year":2025,"mapped_area_ha":100,
                "source_url":"mapbiomas","classes":[{"class_code":39,"class_name":"Soja","area_ha":40}]}
        out=build_mapbiomas_pam_contingency(None,land,map_reader=lambda _:mapped,
            micro_fn=lambda _: {"dominant":{"code":"51006","name":"Sinop","uf":"MT"}},
            yields_fn=lambda crop,code:{y:3000+100*(y-2015) for y in range(2015,2025)})
        self.assertEqual(out["status"],"FALLBACK_HISTORICO_MAPBIOMAS_PAM")
        self.assertFalse(out["current_crop_cover_confirmed"])
        self.assertEqual(out["classes"][0]["pam_year_count"],10)
        self.assertAlmostEqual(out["classes"][0]["conditional_reference_production_t"],
                               out["classes"][0]["area_ha"]*3450/1000)
        self.assertIn("não mensurada",out["classes"][0]["uncertainty"])


if __name__ == "__main__":
    unittest.main()
