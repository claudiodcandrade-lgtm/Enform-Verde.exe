"""Patch 0003: thin and fragmented soil strata are sampled on the interior."""
import unittest
from shapely.affinity import rotate
from shapely.geometry import MultiPolygon, box
from pronasolos_identify import sample_points_in_stratum

class StratumSamplingTests(unittest.TestCase):
    def test_thin_diagonal_stratum_gets_full_budget_inside(self):
        geom=rotate(box(0,0,100000,600),35,origin=(0,0))
        points=sample_points_in_stratum(geom,36)
        self.assertEqual(len(points),36)
        self.assertTrue(all(geom.covers(p) for p in points))

    def test_every_fragment_is_represented(self):
        polygons=[box(i*20000,(i%3)*15000,i*20000+900,(i%3)*15000+900) for i in range(8)]
        geom=MultiPolygon(polygons)
        points=sample_points_in_stratum(geom,36)
        self.assertGreaterEqual(len(points),8)
        for polygon in polygons:
            self.assertTrue(any(polygon.covers(p) for p in points))

    def test_points_unique_deterministic_and_capped(self):
        geom=box(0,0,30000,30000)
        a=sample_points_in_stratum(geom,20)
        b=sample_points_in_stratum(geom,20)
        self.assertEqual([(p.x,p.y) for p in a],[(p.x,p.y) for p in b])
        self.assertEqual(len(a),20)
        self.assertEqual(len({(round(p.x,2),round(p.y,2)) for p in a}),20)

    def test_empty_geometry(self):
        geom=box(0,0,1,1).difference(box(0,0,1,1))
        self.assertEqual(sample_points_in_stratum(geom,36),[])
