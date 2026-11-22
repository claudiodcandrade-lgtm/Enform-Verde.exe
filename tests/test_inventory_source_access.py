import json
import tempfile
import unittest
from pathlib import Path

from inventory_source_access import collect_hierarchical_sources
from national_inventory_database import rank_inventory_candidates


class _Response:
    def __init__(self, payload=None, content=b""):
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _Session:
    """Offline fake for CKAN, Dataverse, OAI-PMH, DSpace and Zenodo."""
    def get(self, url, params=None, timeout=None):
        params = params or {}
        if "api/3/action/package_search" in url:
            return _Response({"success": True, "result": {"count": 0, "results": []}})
        if "/api/search" in url:
            return _Response({"data": {"items": []}})
        if "zenodo.org/api/records" in url:
            return _Response({"hits": {"hits": []}})
        if "/server/api/core/items" in url:
            return _Response({"_embedded": {"items": []}})
        if params.get("verb") == "Identify":
            return _Response(content=b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><Identify/></OAI-PMH>')
        if params.get("verb") == "ListRecords":
            return _Response(content=b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListRecords/></OAI-PMH>')
        raise AssertionError(f"unhandled mocked source request: {url} {params}")


class _ICMBIOSession(_Session):
    def get(self, url, params=None, timeout=None):
        if "gov.br/icmbio/pt-br/assuntos/unidade-de-conservacao/planos-de-manejo" in url:
            return _Response(content=(
                b'<a href="/icmbio/pt-br/assuntos/unidade-de-conservacao/flona-tapajos">'
                b'Floresta Nacional do Tapajos</a>'
                b'<a href="/icmbio/pt-br/assuntos/unidade-de-conservacao/flona-tapajos/plano-de-manejo">'
                b'Plano de Manejo - Flona do Tapajos</a>'
                b'<a href="https://example.org/inventario.pdf">Inventario florestal</a>'
            ))
        return super().get(url, params=params, timeout=timeout)


class InventorySourceAccessTests(unittest.TestCase):
    def test_collector_writes_links_manifest_and_searchable_catalog_without_promoting_leads(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = collect_hierarchical_sources(root, session=_Session())
            self.assertGreaterEqual(manifest["candidate_or_route_count"], 50)
            self.assertEqual(manifest["machine_discovered_count"], 0)
            self.assertTrue((root / "acesso_fontes_hierarquizadas.html").exists())
            self.assertTrue((root / "fontes_hierarquizadas.csv").exists())
            self.assertTrue((root / "catalogo_inventarios_fontes_hierarquizadas.sqlite").exists())
            stored = json.loads((root / "manifest_fontes_hierarquizadas.json").read_text(encoding="utf-8"))
            self.assertIn("microrregião", " ".join(stored["selection_policy"]).casefold())

    def test_microregion_is_used_first_and_regional_fallback_is_marked(self):
        rows = [
            {"record_id": "local", "biome": "Amazônia", "physiognomy": "Floresta Ombrófila Densa",
             "microregion": "Santarém", "data_level": "published_aggregate", "record_type": "published_aggregate",
             "institution_recognized": True, "structural_metrics": {"center": 20}},
            {"record_id": "regional", "biome": "Amazônia", "physiognomy": "Floresta Ombrófila Densa",
             "microregion": "Altamira", "data_level": "published_aggregate", "record_type": "published_aggregate",
             "institution_recognized": True, "structural_metrics": {"center": 30}},
            {"record_id": "wrong_formation", "biome": "Amazônia", "physiognomy": "Campinarana",
             "microregion": "Santarém", "data_level": "primary_tree", "open_data": 1, "georeferenced": 1},
        ]
        local = rank_inventory_candidates(rows, biome="Amazônia", physiognomy="Floresta Ombrófila Densa",
                                          microregion="Santarém")
        self.assertEqual([r["record_id"] for r in local], ["local"])
        self.assertEqual(local[0]["geographic_scope"], "MICRORREGIAO")
        regional = rank_inventory_candidates(rows[1:], biome="Amazônia", physiognomy="Floresta Ombrófila Densa",
                                              microregion="Santarém")
        self.assertEqual([r["record_id"] for r in regional], ["regional"])
        self.assertEqual(regional[0]["geographic_scope"], "REGIONAL_FALLBACK")

    def test_icmbio_official_plan_pages_are_discovered_as_nonquantitative_leads(self):
        with tempfile.TemporaryDirectory() as td:
            manifest=collect_hierarchical_sources(Path(td),session=_ICMBIOSession())
        rows=[r for r in manifest["records"]
              if r.get("source_id")=="ICMBIO_PLANOS_UC" and r.get("record_type")=="catalog_lead"]
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r["usable_for_estimation"] is False for r in rows))
        self.assertTrue(all("gov.br/icmbio/" in r["url"] for r in rows))
        self.assertTrue(all("example.org" not in r["url"] for r in rows))


if __name__ == "__main__":
    unittest.main()
