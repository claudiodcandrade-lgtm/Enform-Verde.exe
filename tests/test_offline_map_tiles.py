import json,tempfile,unittest
from pathlib import Path
from collections import OrderedDict
from offline_map_tiles import load_quadrants_for_bbox,write_quadrant_tiles

class OfflineMapTileTests(unittest.TestCase):
    def test_writes_clipped_quadrants_and_loads_only_view(self):
        layers={"municipios":[
            {"bbox":[1,1,2,2],"properties":{"name":"west"},"geometry":{"type":"Polygon","coordinates":[[[1,1],[2,1],[2,2],[1,2],[1,1]]]}},
            {"bbox":[8,8,9,9],"properties":{"name":"east"},"geometry":{"type":"Polygon","coordinates":[[[8,8],[9,8],[9,9],[8,9],[8,8]]]}},
        ],"localidades":[]}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);summary=write_quadrant_tiles(layers,root,bounds=(0,0,10,10),tile_degrees=5)
            manifest=json.loads((root/"index.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["tile_count"],2)
            self.assertEqual(manifest["feature_counts"]["municipios"],2)
            cache=OrderedDict()
            view=load_quadrants_for_bbox(root,[0,0,4,4],manifest,cache,max_cached_tiles=1)
            self.assertEqual([f["properties"]["name"] for f in view["municipios"]],["west"])
            other=load_quadrants_for_bbox(root,[6,6,10,10],manifest,cache,max_cached_tiles=1)
            self.assertEqual([f["properties"]["name"] for f in other["municipios"]],["east"])
            self.assertEqual(len(cache),1)
if __name__=="__main__":unittest.main()
