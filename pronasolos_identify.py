"""Auditable multi-layer ArcGIS identify request for Embrapa/PronaSolos soil C.

The official service returns raster values for five 90-m soil horizons
covering 0–100 cm, independently identified as layer IDs 2..6. A batched response is parsed without
substituting zero for missing layers or mixing values from another location.
https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer
"""
from math import isfinite

LAYER_IDS=(2,3,4,5,6)
SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer/identify"
# Secondary officially published SGB/PronaSolos service: parent raster group
# "Estoque de Carbono (Mg/ha)" and horizons 2-6 match the primary service.
# Validate each response independently; NEVER sum horizons across services.
ALTERNATE_SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/solos_90m/MapServer/identify"
# Independently published SGB service: raw SOC layers 2..6, identical horizon
# semantics. No cross-service mixing within a single paired 0-100cm profile.
THIRD_SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/atributos_solo_90m/MapServer/identify"
SERVICE_CANDIDATES=(SERVICE,ALTERNATE_SERVICE,THIRD_SERVICE)


def build_identify_params(x,y,extent,layer_ids=LAYER_IDS,*,crs=3857):
    """One ArcGIS query for all requested horizons at one EPSG:3857 coordinate.

    Coordinates are NOT reprojected here. Reject other CRS rather than
    silently labeling geographic degrees as Web Mercator metres.
    """
    if isinstance(crs,bool) or str(crs).upper().removeprefix("EPSG:") != "3857":
        raise ValueError("PronaSolos identify requires projected EPSG:3857 coordinates")
    if not layer_ids or any(lid not in LAYER_IDS for lid in layer_ids):
        raise ValueError("Unknown PronaSolos soil carbon layer")
    coords=(x,y,*extent)
    if any(isinstance(v,bool) or not isfinite(float(v)) for v in coords):
        raise ValueError("Invalid coordinates")
    return {"f":"json","geometry":f"{float(x)},{float(y)}",
            "geometryType":"esriGeometryPoint","sr":"3857",
            "layers":"all:"+",".join(str(v) for v in layer_ids),
            "tolerance":"5","mapExtent":",".join(str(float(v)) for v in extent),
            "imageDisplay":"1600,1600,96","returnGeometry":"false"}

def numeric_soil_stock(result):
    """Read a pixel stock, not class renderer values or non-numeric NoData."""
    if not isinstance(result,dict):
        return None
    at=result.get("attributes") or {}
    candidates=[result.get("value")]
    if isinstance(at,dict):
        for key,value in at.items():
            k=str(key).casefold()
            # ArcGIS "stretched pixel value" may be a renderer colour/intensity
            # (e.g. 0–255), NOT the stock in Mg C/ha. Never use it as stock.
            # Only accept attributes referring to an unscaled raw pixel value.
            if "stretched" in k or "render" in k or "display" in k:
                continue
            if ("pixel" in k and "value" in k) or k in (
                  "value","valor","pixel_value","raw_value","raw pixel value"):
                candidates.append(value)
    for raw in candidates:
        if raw is None or isinstance(raw,bool):
            continue
        try:
            value=float(str(raw).strip().replace(" ","").replace(",","."))
        except (TypeError,ValueError,OverflowError):
            continue
        # Reported in Mg C / ha for each 90-m depth horizon.
        if isfinite(value) and 0 <= value < 2000:
            return value
    return None

def extract_paired_horizons(payload,layer_ids=LAYER_IDS):
    """Validate a batched identify response; return point's measured layers only.

    Duplicates with conflicting values are rejected; missing horizons remain
    missing (never zero). A map service's generic group layer is disregarded.
    """
    if not isinstance(payload,dict):
        raise ValueError("Invalid ArcGIS identify payload")
    if payload.get("error"):
        raise ValueError("PronaSolos service reported an error: "+str(payload["error"])[:300])
    results=payload.get("results")
    if not isinstance(results,list):
        raise ValueError("ArcGIS identify missing results array")
    expected=set(layer_ids)
    found={}
    for item in results:
        if not isinstance(item,dict):
            continue
        try:
            lid=int(item.get("layerId",-1))
        except (TypeError,ValueError,OverflowError):
            continue
        if lid not in expected:
            continue
        value=numeric_soil_stock(item)
        if value is None:
            continue
        if lid in found and abs(found[lid]-value)>1e-8:
            raise ValueError("Conflicting raster values for soil horizon "+str(lid))
        found[lid]=value
    return found


def sample_points_in_stratum(geom, max_points=36, grid_steps=(6, 12, 24, 48, 96, 192)):
    """Deterministic query points strictly inside thin/fragmented polygons.

    Always samples each sizeable polygon part, then refines cell-center grids.
    No image or carbon values are synthesized by this procedure.
    """
    from shapely.geometry import Point
    if geom is None or geom.is_empty:
        return []
    max_points=max(1,int(max_points))
    parts=sorted(getattr(geom,"geoms",[geom]),key=lambda g:g.area,reverse=True)
    chosen,seen=[],set()
    def add(p):
        key=(round(p.x,2),round(p.y,2))
        if key not in seen and geom.covers(p):
            seen.add(key)
            chosen.append(p)
    add(geom.representative_point())
    for part in parts[:max(1,max_points//2)]:
        if part.area>0:
            add(part.representative_point())
    minx,miny,maxx,maxy=geom.bounds
    inside=[]
    for n in grid_steps:
        dx=(maxx-minx)/n
        dy=(maxy-miny)/n
        cand=[Point(minx+(i+0.5)*dx,miny+(j+0.5)*dy)
              for j in range(n) for i in range(n)]
        inside=[p for p in cand if geom.covers(p)]
        if len(inside)+len(chosen)>=max_points:
            break
    room=max_points-len(chosen)
    if room>0 and inside:
        stride=max(1,len(inside)/room)
        idx=sorted({int(k*stride) for k in range(room) if int(k*stride)<len(inside)})
        for k in idx:
            add(inside[k])
    return chosen[:max_points]
