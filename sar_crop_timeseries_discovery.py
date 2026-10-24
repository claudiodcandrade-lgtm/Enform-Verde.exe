"""Discovery of recent Sentinel-1 acquisitions for crop phenology.

Uses official Copernicus STAC API. Discovery only: scenes must be calibrated,
terrain-corrected and harmonized before time-series inference.
"""
from datetime import datetime, timedelta, timezone
import json
from urllib.request import Request, urlopen

STAC_SEARCH = "https://stac.dataspace.copernicus.eu/v1/search"

def discover_recent_sar(aoi_geojson, days=90, now=None, limit=100, opener=urlopen):
    """Find Sentinel-1 GRD scenes intersecting a GeoJSON Polygon/MultiPolygon.

    Returns a normalized acquisition manifest, never inferred crop classes.
    The caller must paginate via the STAC next link if needed.
    """
    if not isinstance(aoi_geojson, dict) or aoi_geojson.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("AOI must be a GeoJSON Polygon or MultiPolygon in EPSG:4326")
    if not isinstance(days, int) or not 1 <= days <= 730:
        raise ValueError("days must be between 1 and 730")
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    end = now or datetime.now(timezone.utc)
    if end.tzinfo is None:
        raise ValueError("now must have timezone")
    start = end - timedelta(days=days)
    payload = {
        "collections": ["sentinel-1-grd"],
        "intersects": aoi_geojson,
        "datetime": start.isoformat().replace("+00:00", "Z") + "/" +
                    end.isoformat().replace("+00:00", "Z"),
        "limit": limit,
    }
    request = Request(STAC_SEARCH, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json",
                               "Accept": "application/geo+json"},
                      method="POST")
    with opener(request, timeout=45) as response:
        data = json.load(response)
    scenes = []
    for item in data.get("features", []):
        props = item.get("properties") or {}
        scenes.append({
            "id": item.get("id"),
            "acquisition_utc": props.get("datetime") or props.get("start_datetime"),
            "platform": props.get("platform"),
            "polarizations": props.get("sar:polarizations"),
            "orbit_state": props.get("sat:orbit_state"),
            "relative_orbit": props.get("sat:relative_orbit"),
            "incidence_angle": props.get("view:incidence_angle"),
            "published_utc": props.get("published") or props.get("created"),
            "collection": item.get("collection"),
            "assets": item.get("assets", {}),
            "source": STAC_SEARCH,
        })
    return {
        "queried_at_utc": end.isoformat(),
        "date_from_utc": start.isoformat(),
        "source": STAC_SEARCH,
        "scenes": scenes,
        "next": next((link for link in data.get("links", [])
                      if link.get("rel") == "next"), None),
        "status": "discovery_only",
        "note": "No crop inference or biomass estimation performed",
    }
