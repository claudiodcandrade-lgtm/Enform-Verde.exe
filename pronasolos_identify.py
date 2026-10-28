"""Auditable multi-layer ArcGIS identify request for Embrapa/PronaSolos soil C.

The official service returns raster values for five 90-m soil horizons
covering 0–100 cm, independently identified as layer IDs 2..6. A batched response is parsed without
substituting zero for missing layers or mixing values from another location.
https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer
"""
from math import isfinite

LAYER_IDS=(2,3,4,5,6)
SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer/identify"

def build_identify_params(x,y,extent,layer_ids=LAYER_IDS):
    """One ArcGIS query for all requested horizons at exactly one coordinate."""
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
            if ("pixel" in k and "value" in k) or "stretched" in k or k in (
                  "value","valor","pixel_value"):
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
