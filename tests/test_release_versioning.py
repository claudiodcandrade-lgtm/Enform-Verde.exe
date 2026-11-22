"""Every new version must produce a Windows EXE package named from APP_VERSION."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "build-windows.yml"


def app_version():
    m = re.search(r'^APP_VERSION="([^"]+)"', (ROOT / "desktop_app.py").read_text(encoding="utf-8"), re.M)
    return m.group(1)


class ReleaseVersioningTests(unittest.TestCase):
    def test_version_format_and_release_notes_exist(self):
        ver = app_version()
        self.assertRegex(ver, r"^\d+\.\d+\.\d+(-[A-Z0-9-]+)?$")
        self.assertTrue((ROOT / f"APP_RELEASE_NOTES_v{ver.split('-')[0]}.md").is_file())

    def test_release_notes_title_matches_executable_version(self):
        ver = app_version()
        notes = (ROOT / f"APP_RELEASE_NOTES_v{ver.split('-')[0]}.md").read_text(encoding="utf-8")
        self.assertRegex(notes.splitlines()[0], rf"^# Enform Verde v{re.escape(ver)}$")

    def test_build_does_not_package_heavy_cartographic_raster(self):
        text = WF.read_text(encoding="utf-8")
        self.assertNotIn("Build offline IBGE administrative and infrastructure map", text)
        self.assertNotIn("offline_ibge_map.json.gz;.", text)
        self.assertNotIn("offline_ibge_tiles", text)
        self.assertNotIn("ibge-map-cache", text)
        self.assertIn("APP_RELEASE_NOTES_v$num.md", text)
        self.assertIn("does not match desktop_app.APP_VERSION", text)

    def test_artifact_and_release_derive_from_app_version(self):
        text = WF.read_text(encoding="utf-8")
        # parse without PyYAML (not a runtime dependency)
        self.assertEqual(text.count("path: dist/Enform Verde/"), 1)
        block = text[text.index("path: dist/Enform Verde/") - 200:text.index("path: dist/Enform Verde/")]
        self.assertIn("name: Enform-Verde-Windows-v${{ env.APP_VERSION }}", block)
        self.assertIn("\n  publish-release:\n", text)
        self.assertIn("contents: write", text[text.index("publish-release:"):])
        self.assertIn("--module-check", text)
        self.assertIn("--visual-check", text)
        self.assertIn('validation/ui_visual_baseline.json;validation', text)
        self.assertIn('--add-data "data/structural_aggregate_evidence_v1.csv;data"', text)
        self.assertNotIn('data/national_inventory_microdata_v1.sqlite;data', text)
        self.assertIn("External IFN database and manifest are missing beside the application", text)
        self.assertIn("External IFN database SHA-256 does not match the verified manifest", text)
        self.assertIn("Large IFN database must remain outside the PyInstaller internal runtime", text)
        self.assertIn("python tools/build_inventory_runtime_manifest.py", text)
        self.assertIn("EXE_SMOKE_BEGIN label=$Label", text)
        self.assertIn("EXE_SMOKE_EXIT label=$Label", text)
        self.assertIn("COMPILED_EXE_TIMEOUT label=$Label", text)
        self.assertIn("$diagnosticFiles = switch ($Label)", text)
        self.assertIn("enform_verde_acceptance_progress.txt", text)
        self.assertIn("enform_verde_acceptance_entry.txt", text)
        self.assertIn("[System.IO.Path]::GetTempPath()", text)
        self.assertIn("[System.IO.File]::ReadAllBytes($log)", text)
        self.assertIn("ACCEPTANCE_DIAGNOSTIC_CONTENT_BEGIN", text)
        self.assertIn("enform_acceptance_diagnostics", text)
        self.assertIn("Upload failed EXE acceptance diagnostics", text)
        self.assertIn("name: acceptance-diagnostics-${{ github.run_id }}", text)
        self.assertIn('faulthandler.dump_traceback_later(60,repeat=True,file=progress)',
                      (ROOT / "desktop_app.py").read_text(encoding="utf-8"))
        self.assertIn('enform_verde_acceptance_entry.txt',
                      (ROOT / "desktop_app.py").read_text(encoding="utf-8"))
        self.assertIn("Invoke-CheckedExe 'tapajos-acceptance'", text)
        self.assertIn("Aggregated inventory evidence is missing beside the frozen Python module runtime", text)
        self.assertIn("Compiled inventory evidence is missing the two eligible Tapajos aggregate references", text)
        self.assertNotRegex(text, r"VERSÃO \d+\.\d+\.\d+")          # no hard-coded version in LEIA-ME
        for mod in ("pronasolos_wcs", "crop_forecast_pipeline", "crop_vigor"):
            self.assertIn("--hidden-import " + mod, text)

    def test_build_workflow_has_one_complete_release_pipeline(self):
        text = WF.read_text(encoding="utf-8")
        self.assertEqual(text.count("  build-windows:"), 1)
        self.assertEqual(text.count("  publish-release:"), 1)
        self.assertEqual(text.count("  maap-real-fh-proof:"), 1)
        self.assertEqual(text.count("path: dist/Enform Verde/"), 1)
        self.assertIn("-Pattern '^# Enform Verde v(.+)$' | Select-Object -First 1", text)
        self.assertNotIn("-Pattern '^# Enform Verde v(.+)          git fetch", text)

    def test_v88_167_word_sync_updates_the_cover_not_only_the_history(self):
        text = (ROOT / ".github" / "workflows" / "sync-v88-167-word.yml").read_text(encoding="utf-8")
        self.assertIn('--cover-version "V88.167 | 3.26.77-PRECAMPO-EXPERIMENTAL"', text)
        self.assertIn("--cover-state", text)

    def test_v88_168_word_sync_tracks_the_new_candidate_and_checkpoint(self):
        text = (ROOT / ".github" / "workflows" / "sync-v88-168-word.yml").read_text(encoding="utf-8")
        self.assertIn("V88.168_FH_AGB_BALIZAS_HORIZONTAIS_MULTIFONTE.md", text)
        self.assertIn('--cover-version "V88.168 | 3.26.78-PRECAMPO-EXPERIMENTAL"', text)
        self.assertIn("ESPECIFICACAO_TECNICA_COMPLETA_V88_168.docx", text)

    def test_v88_170_word_sync_tracks_ifn_query_batching_candidate(self):
        text = (ROOT / ".github" / "workflows" / "sync-v88-170-word.yml").read_text(encoding="utf-8")
        self.assertIn("V88.170_IFN_BATCHED_BIODIVERSITY_QUERY.md", text)
        self.assertIn('--cover-version "V88.170 | 3.26.80-PRECAMPO-EXPERIMENTAL"', text)
        self.assertIn("ESPECIFICACAO_TECNICA_COMPLETA_V88_170.docx", text)

    def test_v88_172_word_sync_tracks_current_candidate(self):
        text = (ROOT / ".github" / "workflows" / "sync-v88-172-word.yml").read_text(encoding="utf-8")
        self.assertIn("V88.172_AGB_CCI_INVENTORIES_VIGOR_RESPONSIVENESS.md", text)
        self.assertIn('--cover-version "V88.172 | 3.26.82-PRECAMPO-EXPERIMENTAL"', text)
        self.assertIn("ESPECIFICACAO_TECNICA_COMPLETA_V88_172.docx", text)

    def test_only_current_word_checkpoint_watches_the_shared_updater(self):
        workflows = ROOT / ".github" / "workflows"
        for version in ("165", "167", "168", "169", "170"):
            text = (workflows / f"sync-v88-{version}-word.yml").read_text(encoding="utf-8")
            paths = text.split("    paths:\n", 1)[1].split("permissions:\n", 1)[0]
            self.assertNotIn("tools/update_spec_docx.py", paths)
        previous = (workflows / "sync-v88-171-word.yml").read_text(encoding="utf-8")
        previous_triggers = previous.split("permissions:\n", 1)[0]
        self.assertIn("workflow_dispatch:", previous_triggers)
        self.assertNotIn("push:", previous_triggers)
        current = (workflows / "sync-v88-172-word.yml").read_text(encoding="utf-8")
        paths = current.split("    paths:\n", 1)[1].split("permissions:\n", 1)[0]
        self.assertIn("tools/update_spec_docx.py", paths)

    def test_windows_acceptance_checks_current_ibge_and_inventory_fallback_contracts(self):
        text = WF.read_text(encoding="utf-8")
        self.assertIn("COBERTURA NATIVA MAPEADA (máscara anual × região fitoecológica IBGE).", text)
        self.assertIn("IBGE potential must remain separate from mapped current native-cover intersection", text)
        self.assertIn("rotas sar configuradas ainda não foram todas tentadas", text)
        self.assertIn("ausência não confirmada", text)
        self.assertNotIn('"Fitofisionomia presente na propriedade:" in src', text)
        self.assertNotIn('"pixels sar" in out["inventory_fallback_gate"]', text)


if __name__ == "__main__":
    unittest.main()
