"""Numerical raster window composition stays indexed and keeps source tiles."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from raster_tile_mosaic import build_vrt_mosaic


class RasterTileMosaicTests(unittest.TestCase):
    def test_vrt_reads_quadrants_without_materializing_or_removing_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources = []
            for name, x, value in (("left.tif", 0, 1), ("right.tif", 2, 2)):
                path = root / name
                with rasterio.open(path, "w", driver="GTiff", width=2, height=2,
                                   count=1, dtype="float32", crs="EPSG:4326",
                                   transform=from_origin(x, 2, 1, 1), nodata=-9999) as dst:
                    dst.write(np.full((2, 2), value, dtype="float32"), 1)
                sources.append(path)
            vrt = build_vrt_mosaic(sources, root / "mosaic.vrt")
            self.assertTrue(all(path.is_file() for path in sources))
            with rasterio.open(vrt) as src:
                self.assertEqual((src.width, src.height), (4, 2))
                np.testing.assert_array_equal(src.read(1),
                    np.array([[1, 1, 2, 2], [1, 1, 2, 2]], dtype="float32"))

    def test_vrt_rejects_incompatible_source_grids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = []
            for name, crs in (("a.tif", "EPSG:4326"), ("b.tif", "EPSG:3857")):
                path = root / name
                with rasterio.open(path, "w", driver="GTiff", width=2, height=2,
                                   count=1, dtype="float32", crs=crs,
                                   transform=from_origin(0, 2, 1, 1), nodata=-9999) as dst:
                    dst.write(np.ones((2, 2), dtype="float32"), 1)
                paths.append(path)
            with self.assertRaisesRegex(ValueError, "incompatíveis"):
                build_vrt_mosaic(paths, root / "invalid.vrt")


if __name__ == "__main__":
    unittest.main()
