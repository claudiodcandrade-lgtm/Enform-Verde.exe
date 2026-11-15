import unittest

from crop_mapbiomas_pam_fallback import build_mapbiomas_pam_contingency


def exhausted_land():
    def absence():
        return {"status": "SAR_AUSENCIA_COBERTURA_CONFIRMADA",
                "coverage_absence_confirmed": True,
                "catalog_search_complete": True,
                "pagination_complete": True,
                "pixel_read_complete": True,
                "valid_pixel_count": 0,
                "technical_error_count": 0,
                "pixels": 0}
    return {
        "status": "SAR_AUSENCIA_COBERTURA_CONFIRMADA",
        "classes": [{"source": "SEM_COBERTURA", "class_name": "Não classificado"}],
        "all_sar_missions_checked": True,
        "unconfigured_sar_routes": [],
        "recent_sar_cover": absence(),
        "sar_classifier_lemplus": absence(),
        "alternative_radar_screen": absence(),
        "native_sar_experimental": absence(),
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

    def test_technical_errors_in_any_sar_route_never_unlock_fallback(self):
        for field, status in (
            ("recent_sar_cover", "ERRO_TECNICO"),
            ("sar_classifier_lemplus", "ERRO_TECNICO_LEITURA_SAR"),
            ("alternative_radar_screen", "ACESSO_RESTRITO"),
            ("native_sar_experimental", "ERROR"),
        ):
            with self.subTest(route=field):
                land=exhausted_land()
                land[field]={"status":status,"reason":"transport/pixel/auth failure"}
                out=build_mapbiomas_pam_contingency(None,land,
                    map_reader=lambda _: self.fail("technical SAR failure must block fallback"))
                self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")

    def test_incomplete_pagination_or_unconfigured_mission_blocks_fallback(self):
        for mutate in (
            lambda x: x["recent_sar_cover"].update(pagination_complete=False),
            lambda x: x.update(unconfigured_sar_routes=["NISAR"]),
            lambda x: x.update(all_sar_missions_checked=False),
        ):
            land=exhausted_land();mutate(land)
            out=build_mapbiomas_pam_contingency(None,land,
                map_reader=lambda _: self.fail("incomplete coverage search must block fallback"))
            self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")

    def test_absence_certificate_with_read_errors_is_rejected(self):
        land=exhausted_land()
        land["sar_classifier_lemplus"]["technical_error_count"]=1
        out=build_mapbiomas_pam_contingency(None,land,
            map_reader=lambda _: self.fail("read failure must block fallback"))
        self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")

    def test_unexecuted_sar_classifier_blocks_the_historical_fallback(self):
        land=exhausted_land()
        land["sar_classifier_lemplus"]={"status":"NOT_EXECUTED",
                                        "reason":"primary model already produced output"}
        out=build_mapbiomas_pam_contingency(None,land,
            map_reader=lambda _: self.fail("MapBiomas must remain blocked"))
        self.assertEqual(out["status"],"BLOQUEADO_ATE_ESGOTAR_SAR")
        self.assertEqual(out["sar_gate"]["reason"],
                         "AUSENCIA_SAR_NAO_COMPROVADA_OU_ROTA_COM_ERRO")

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

    def test_mapbiomas_unicode_failure_keeps_stage_and_detail(self):
        def fail(_):
            raise UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "invalid native GDAL message")
        out=build_mapbiomas_pam_contingency(exhausted_land(), exhausted_land(), map_reader=fail)
        self.assertEqual(out["status"],"ERRO_TECNICO_MAPBIOMAS")
        self.assertEqual(out["stage"],"mapbiomas_pixel_read")
        self.assertIn("UnicodeDecodeError",out["reason"])
        self.assertTrue(out["detail"])


if __name__ == "__main__":
    unittest.main()
