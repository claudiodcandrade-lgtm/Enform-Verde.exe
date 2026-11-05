"""Public INPE STAC fallback for Brazil-wide Sentinel-1 RTC COGs.

This is a pixel-ready RTC source and uses the same VV/VH gamma0 intent as the
MPC route. It may lag the newest GRD acquisitions; item acquisition times and
orbit compatibility must still be checked before using it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

STAC_ITEMS = "https://data.inpe.br/bdc/stac/v1/collections/sentinel-1-rtc-1/items"
ALLOWED_HOSTS = {"data.inpe.br"}
COLLECTION_ID = "sentinel-1-rtc-1"


def _json(url, *, opener=urlopen, timeout=45):
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.hostname not in ALLOWED_HOSTS:
        raise ValueError("Untrusted INPE STAC/COG endpoint")
    req=Request(url,headers={"Accept":"application/geo+json, application/json"})
    try:
        with opener(req,timeout=timeout) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError("INPE STAC request failed ("+type(exc).__name__+")") from None


def _bounds(geometry):
    coords=geometry.get("coordinates") or []
    pts=[]
    def walk(v):
        if isinstance(v,(list,tuple)) and len(v)>=2 and all(isinstance(x,(int,float)) for x in v[:2]):
            pts.append((float(v[0]),float(v[1])))
        elif isinstance(v,(list,tuple)):
            for child in v: walk(child)
    walk(coords)
    if not pts: raise ValueError("AOI GeoJSON has no coordinate pairs")
    return min(x for x,_ in pts),min(y for _,y in pts),max(x for x,_ in pts),max(y for _,y in pts)


def _asset_for(assets, polarization):
    terms=(polarization, "gamma0_"+polarization, "gamma0 "+polarization,
           "backscatter_"+polarization, "backscatter "+polarization)
    for key,asset in (assets or {}).items():
        label=" ".join(str(x or "") for x in
                       (key,asset.get("title"),asset.get("description"),asset.get("common_name"))).casefold()
        href=asset.get("href")
        parts=urlsplit(str(href or ""))
        if (any(term in label for term in terms) and parts.scheme=="https"
                and parts.hostname in ALLOWED_HOSTS):
            return {"href":href,"title":asset.get("title"),"type":asset.get("type")}
    return None


def search_sentinel1_inpe_rtc(aoi_geojson, *, start_utc, end_utc,
                              opener=urlopen, page_limit=1000, max_pages=100):
    """Search the INPE public Sentinel-1 RTC collection and return normalized scenes."""
    if not isinstance(aoi_geojson,dict) or aoi_geojson.get("type") not in {"Polygon","MultiPolygon"}:
        raise ValueError("AOI must be a GeoJSON Polygon or MultiPolygon")
    start=_aware(start_utc);end=_aware(end_utc)
    if start>=end:raise ValueError("Invalid UTC interval")
    west,south,east,north=_bounds(aoi_geojson)
    params={"bbox":f"{west},{south},{east},{north}",
            "datetime":start.isoformat().replace("+00:00","Z")+"/"+end.isoformat().replace("+00:00","Z"),
            "limit":max(1,min(int(page_limit),10000))}
    url=STAC_ITEMS+"?"+urlencode(params)
    scenes=[];pages=0;seen=set()
    while url and pages<max_pages:
        data=_json(url,opener=opener)
        pages+=1
        for item in data.get("features",[]):
            ident=item.get("id")
            props=item.get("properties") or {}
            acquired=props.get("datetime") or props.get("start_datetime")
            if not ident or ident in seen or not acquired:continue
            assets=item.get("assets") or {}
            vv=_asset_for(assets,"vv");vh=_asset_for(assets,"vh")
            if not vv or not vh:continue
            try:
                dt=_aware(acquired)
            except (ValueError,TypeError):
                continue
            if not (start<=dt<=end):continue
            scenes.append({
                "id":ident,"acquisition_utc":dt.isoformat(),
                "published_utc":props.get("created") or props.get("updated"),
                "platform":props.get("platform"),
                "orbit_state":props.get("sat:orbit_state") or props.get("orbit_state"),
                "relative_orbit":props.get("sat:relative_orbit") or props.get("relative_orbit"),
                "polarizations":["VV","VH"],"collection":COLLECTION_ID,
                "assets":{"vv":vv,"vh":vh},
                "source":"INPE_STAC_RTC","provider":"INPE",
                "radiometry":"gamma0_power","crs":"EPSG:4326"})
            seen.add(ident)
        nxt=next((x for x in data.get("links",[]) if x.get("rel")=="next"),None)
        if not nxt:url=None
        else:
            url=urljoin(url,nxt.get("href",""))
            if urlsplit(url).hostname not in ALLOWED_HOSTS:
                raise ValueError("Untrusted INPE STAC pagination link")
    return {"status":"discovery_only","provider":"INPE","collection":COLLECTION_ID,
            "scene_count":len(scenes),"pages_read":pages,
            "pagination_complete":not bool(url),"scenes":sorted(scenes,key=lambda x:x["acquisition_utc"],reverse=True),
            "warning":"INPE RTC may lag recent Sentinel-1 GRD acquisitions; date and COG reads must be checked."}


def _aware(value):
    if isinstance(value,datetime):dt=value
    else:dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("Timestamp must include UTC timezone")
    return dt.astimezone(timezone.utc)


if __name__=="__main__":
    raise SystemExit("Call search_sentinel1_inpe_rtc with an AOI and bounded UTC interval.")
