"""Build a lightweight indexed VRT over aligned raster tiles without merging arrays."""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path


def build_vrt_mosaic(tile_paths, destination):
    """Create a VRT index for aligned tiles; retain source tiles on disk.

    This avoids loading a large mosaic into RAM and writing a second full-size
    raster. The returned VRT is window-readable by Rasterio/GDAL; provenance
    and hashes for source tiles remain the caller's responsibility.
    """
    import rasterio

    tiles=[Path(p).resolve() for p in tile_paths]
    if not tiles:
        raise ValueError("VRT sem tiles de origem")
    sources=[]
    for path in tiles:
        with rasterio.open(path) as src:
            if src.count!=1 or src.crs is None or src.transform.b or src.transform.d:
                raise ValueError("tiles devem ter uma banda, CRS e grade sem rotação")
            sources.append({"path":path,"crs":src.crs,"transform":src.transform,
                "width":src.width,"height":src.height,"dtype":src.dtypes[0],
                "nodata":src.nodata,"bounds":src.bounds})
    first=sources[0]; tr=first["transform"]
    for item in sources[1:]:
        other=item["transform"]
        if (item["crs"]!=first["crs"] or item["dtype"]!=first["dtype"]
                or item["nodata"]!=first["nodata"]
                or not math.isclose(other.a,tr.a,abs_tol=1e-12)
                or not math.isclose(other.e,tr.e,abs_tol=1e-12)
                or other.b or other.d):
            raise ValueError("tiles com CRS, tipo, nodata ou resolução incompatíveis")
    pixel_x=tr.a; pixel_y=-tr.e
    left=min(x["bounds"].left for x in sources)
    right=max(x["bounds"].right for x in sources)
    bottom=min(x["bounds"].bottom for x in sources)
    top=max(x["bounds"].top for x in sources)
    width=round((right-left)/pixel_x); height=round((top-bottom)/pixel_y)
    if width<1 or height<1 or not math.isclose((right-left)/pixel_x,width,abs_tol=1e-6) \
            or not math.isclose((top-bottom)/pixel_y,height,abs_tol=1e-6):
        raise ValueError("extensão dos tiles não se alinha à grade de pixels")

    vrt=ET.Element("VRTDataset",rasterXSize=str(width),rasterYSize=str(height))
    srs=ET.SubElement(vrt,"SRS");srs.text=first["crs"].to_wkt()
    gt=ET.SubElement(vrt,"GeoTransform")
    gt.text=", ".join(map(str,(left,pixel_x,0.0,top,0.0,-pixel_y)))
    gdal_type={"uint8":"Byte","uint16":"UInt16","int16":"Int16",
               "uint32":"UInt32","int32":"Int32","float32":"Float32",
               "float64":"Float64"}.get(first["dtype"])
    if gdal_type is None:
        raise ValueError("tipo raster sem mapeamento VRT suportado: "+first["dtype"])
    band=ET.SubElement(vrt,"VRTRasterBand",dataType=gdal_type,band="1")
    if first["nodata"] is not None:
        ET.SubElement(band,"NoDataValue").text=str(first["nodata"])
    for item in sources:
        bounds=item["bounds"]
        xoff=round((bounds.left-left)/pixel_x)
        yoff=round((top-bounds.top)/pixel_y)
        if not (math.isclose((bounds.left-left)/pixel_x,xoff,abs_tol=1e-6)
                and math.isclose((top-bounds.top)/pixel_y,yoff,abs_tol=1e-6)):
            raise ValueError("origem do tile desalinhada à grade do mosaico")
        source=ET.SubElement(band,"SimpleSource")
        filename=ET.SubElement(source,"SourceFilename",relativeToVRT="0")
        filename.text=str(item["path"])
        ET.SubElement(source,"SourceBand").text="1"
        ET.SubElement(source,"SrcRect",xOff="0",yOff="0",
                      xSize=str(item["width"]),ySize=str(item["height"]))
        ET.SubElement(source,"DstRect",xOff=str(xoff),yOff=str(yoff),
                      xSize=str(item["width"]),ySize=str(item["height"]))
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(vrt).write(destination,encoding="UTF-8",xml_declaration=True)
    with rasterio.open(destination) as check:
        if check.count!=1 or check.width!=width or check.height!=height or check.crs!=first["crs"]:
            destination.unlink(missing_ok=True)
            raise ValueError("VRT gerado não passou pela reabertura de verificação")
    return destination
