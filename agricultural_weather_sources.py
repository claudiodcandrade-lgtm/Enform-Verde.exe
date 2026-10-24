"""Weather source registry and microrregional station selection for Enform Verde.

Public endpoints and licensed endpoints are intentionally distinguished.
Do not label model-grid values as station measurements.
"""
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt, isfinite

SOURCES = {
 "INMET": {"type":"observed_station","url":"https://tempo.inmet.gov.br/",
           "catalog":"https://portal.inmet.gov.br/paginas/catalogoaut",
           "freshness_hours":2,"access":"public portal; automatic API endpoint not guaranteed"},
 "BDMEP": {"type":"historical_station","url":"https://bdmep.inmet.gov.br/",
           "freshness_hours":2160,"access":"CSV export; email confirmation may be required"},
 "CPTEC": {"type":"weather_forecast","url":"https://servicos.cptec.inpe.br/XML/",
           "freshness_hours":24,"access":"public XML, verify license for commercial use"},
 "CLIMATEMPO": {"type":"licensed_weather","url":"https://advisor.climatempo.com.br/",
           "freshness_hours":24,"access":"contract and API credentials required"},
 "EMBRAPA_CLIMAPI": {"type":"weather_forecast","url":"https://api.cnptia.embrapa.br/climapi/v1",
           "freshness_hours":6,"access":"AgroAPI subscription and bearer token required"}
}

def haversine_km(lat1,lon1,lat2,lon2):
    a=sin(radians((lat2-lat1)/2))**2+cos(radians(lat1))*cos(radians(lat2))*sin(radians((lon2-lon1)/2))**2
    return 6371.0088*2*asin(min(1,sqrt(a)))

def rank_stations(latitude, longitude, stations, *, max_distance_km=150,
                  max_elevation_difference_m=400):
    """Rank by distance and altitude; stations are not automatically representative."""
    ranked=[]
    for s in stations:
        try:
            lat,lon=float(s["latitude"]),float(s["longitude"])
            if not all(map(isfinite,(lat,lon))) or not -90<=lat<=90 or not -180<=lon<=180:continue
            d=haversine_km(latitude,longitude,lat,lon)
            elevation_delta=abs(float(s["elevation_m"])-float(s["aoi_elevation_m"])) if "elevation_m" in s and "aoi_elevation_m" in s else None
            if d>max_distance_km or elevation_delta is not None and elevation_delta>max_elevation_difference_m:continue
            ranked.append({**s,"distance_km":round(d,2),"elevation_difference_m":elevation_delta,
                           "representativeness":"requires terrain, exposure, coverage and QC review"})
        except (ValueError,TypeError,KeyError):continue
    return sorted(ranked,key=lambda s:(s["distance_km"],s["elevation_difference_m"] or 0))

def check_freshness(observed_utc,source,*,now=None):
    now=now or datetime.now(timezone.utc)
    if isinstance(observed_utc,str):observed_utc=datetime.fromisoformat(observed_utc.replace("Z","+00:00"))
    if observed_utc.tzinfo is None:raise ValueError("UTC timestamp must be timezone-aware")
    age=(now-observed_utc).total_seconds()/3600
    return {"source":source,"age_hours":round(age,2),
            "fresh":0<=age<=SOURCES[source]["freshness_hours"],
            "limit_hours":SOURCES[source]["freshness_hours"]}

def quality_check_hourly(rows):
    """Conservative missing-value and physical-range filter; not sensor calibration."""
    limits={"temperature_c":(-60,65),"relative_humidity_pct":(0,100),
            "precipitation_mm":(0,600),"wind_speed_m_s":(0,90)}
    result=[]
    for row in rows:
        cleaned=dict(row); flags=[]
        for key,(low,high) in limits.items():
            if key not in row:continue
            try:
                v=float(str(row[key]).replace(",","."))
                if not isfinite(v) or v in (9999,-9999) or not low<=v<=high:raise ValueError
                cleaned[key]=v
            except (ValueError,TypeError):
                cleaned[key]=None;flags.append(key+": ausente/invalido")
        cleaned["quality_flags"]=flags
        result.append(cleaned)
    return result
