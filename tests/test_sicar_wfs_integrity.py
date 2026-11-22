"""SICAR WFS response integrity: never return a polygon for a different CAR.

Offline contract tests; live WFS availability is a separate integration check.
"""
import sys
import types
import unittest
from unittest.mock import patch

import desktop_app

CAR = "MT-5108501-CBE0F5EDD27A4D7888E7392EA7D44793"
OTHER = "MT-5103700-92A39DC62FDF4D88874F218D41BE1C7F"


def feature(code):
    return {"type": "Feature", "properties": {"cod_imovel": code},
            "geometry": {"type": "Point", "coordinates": [-56.0, -12.0]}}


class Reply:
    ok = True
    status_code = 200

    def __init__(self, features):
        self.features = features

    def json(self):
        return {"type": "FeatureCollection", "features": self.features}


class Session:
    def __init__(self, features):
        self.features = features
        self.calls = []

    def get(self, url, params=None, timeout=None, **kwargs):
        self.calls.append((url, params))
        return Reply(self.features)


class Frame:
    def __init__(self):
        self.attrs = {}
        self.crs = "EPSG:4326"


class SICARIntegrityTests(unittest.TestCase):
    def _run(self, features):
        session = Session(features)
        captured = []
        def from_features(features, crs=None):
            captured.append((list(features), crs))
            return Frame()
        fake_gpd = types.SimpleNamespace(
            GeoDataFrame=types.SimpleNamespace(from_features=from_features))
        return session, captured, fake_gpd

    def test_wfs_ignoring_cql_filter_must_not_return_other_property(self):
        session, captured, fake_gpd = self._run([feature(OTHER)])
        with patch.object(desktop_app, "_sicar_session", return_value=session), \
                patch.dict(sys.modules, {"geopandas": fake_gpd}):
            with self.assertRaisesRegex(LookupError, "no_exact_cod_imovel"):
                desktop_app.resolve_car(CAR)
        self.assertEqual(len(session.calls), 6)
        self.assertEqual(captured, [])

    def test_exact_code_selected_when_wfs_returns_unfiltered_mixture(self):
        session, captured, fake_gpd = self._run([feature(OTHER), feature(CAR)])
        with patch.object(desktop_app, "_sicar_session", return_value=session), \
                patch.dict(sys.modules, {"geopandas": fake_gpd}):
            frame = desktop_app.resolve_car(CAR)
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(captured[0][0][0]["properties"]["cod_imovel"], CAR)
        self.assertEqual(captured[0][1], "EPSG:4326")
        self.assertEqual(frame.attrs["sicar_cod_imovel"], CAR)

    def test_duplicate_exact_matches_rejected(self):
        session, captured, fake_gpd = self._run([feature(CAR), feature(CAR)])
        with patch.object(desktop_app, "_sicar_session", return_value=session), \
                patch.dict(sys.modules, {"geopandas": fake_gpd}):
            with self.assertRaisesRegex(RuntimeError, "múltiplos"):
                desktop_app.resolve_car(CAR)
        self.assertEqual(captured, [])

    def test_missing_geometry_rejected(self):
        item = feature(CAR)
        item["geometry"] = None
        session, captured, fake_gpd = self._run([item])
        with patch.object(desktop_app, "_sicar_session", return_value=session), \
                patch.dict(sys.modules, {"geopandas": fake_gpd}):
            with self.assertRaisesRegex(RuntimeError, "sem geometria"):
                desktop_app.resolve_car(CAR)
        self.assertEqual(captured, [])


if __name__ == "__main__":
    unittest.main()
