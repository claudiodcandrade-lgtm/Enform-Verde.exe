"""Small deterministic COG-read contracts for the optical viewport."""
import importlib.util
import unittest

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("rasterio"), "rasterio unavailable in this environment")
class OpticalQuadrantReadTests(unittest.TestCase):
    def test_local_cog_is_reprojected_in_bounded_quadrants(self):
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        from desktop_app import _read_optical_cog_quadrants

        width=height=600
        transform=from_origin(0,600,1,1)
        source=np.arange(1,width*height+1,dtype=np.float32).reshape(height,width)
        with MemoryFile() as mem:
            with mem.open(driver="GTiff",height=height,width=width,count=1,dtype="float32",
                          crs="EPSG:3857",transform=transform) as dst:
                dst.write(source,1)
            with mem.open() as src:
                result=_read_optical_cog_quadrants(src,transform,"EPSG:3857",width,height)
        np.testing.assert_allclose(result,source,rtol=0,atol=0.01)


if __name__=="__main__":
    unittest.main()
