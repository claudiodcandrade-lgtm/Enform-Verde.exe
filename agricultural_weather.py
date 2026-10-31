"""NASA POWER daily point meteorology: observational/reanalysis grid, not station readings."""
from datetime import date,datetime,timedelta,timezone
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import json
from math import isfinite

API="https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS=("T2M","T2M_MAX","T2M_MIN","PRECTOTCORR","ALLSKY_SFC_SW_DWN","RH2M","WS2M")

def _valid(value):
    try:
        v=float(value)
        return v if isfinite(v) and v not in (-999,-9999) else None
    except (ValueError,TypeError):return None

def fetch_daily_weather(latitude,longitude,*,days=90,end_date=None,opener=urlopen):
    lat,lon=float(latitude),float(longitude)
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError("Invalid coordinates")
    if not isinstance(days,int) or not 7<=days<=730:raise ValueError("days must be 7..730")
    end=end_date or (datetime.now(timezone.utc).date()-timedelta(days=2))
    if isinstance(end,str):end=date.fromisoformat(end)
    start=end-timedelta(days=days-1)
    url=API+"?"+urlencode({"parameters":",".join(PARAMETERS),"community":"AG",
                         "longitude":lon,"latitude":lat,"start":start.strftime("%Y%m%d"),
                         "end":end.strftime("%Y%m%d"),"format":"JSON"})
    with opener(Request(url,headers={"User-Agent":"EnformVerde/3.24"}),timeout=45) as response:
        data=json.load(response)
    values=(data.get("properties") or {}).get("parameter") or {}
    dates=sorted(set().union(*(set(v) for v in values.values() if isinstance(v,dict))))
    observations=[{"date":d,**{k:_valid((values.get(k) or {}).get(d)) for k in PARAMETERS}} for d in dates]
    return {"source":"NASA POWER","source_url":url,"source_kind":"meteorologia em grade no centroide; nao estacao local",
            "latitude":lat,"longitude":lon,"start":start.isoformat(),"end":end.isoformat(),
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
            "observations":observations,"status":"ok" if observations else "sem_dados"}

def summarize_weather(series,*,base_temperature_c=10):
    rows=series.get("observations") or []
    t=[r["T2M"] for r in rows if r.get("T2M") is not None]
    p=[r["PRECTOTCORR"] for r in rows if r.get("PRECTOTCORR") is not None]
    gdd=[max(0,(r["T2M_MAX"]+r["T2M_MIN"])/2-base_temperature_c)
         for r in rows if r.get("T2M_MAX") is not None and r.get("T2M_MIN") is not None]
    return {"temperature_days":len(t),"rain_days":len(p),"gdd_days":len(gdd),
            "mean_temperature_c":round(sum(t)/len(t),2) if t else None,
            "rain_mm":round(sum(p),2) if p else None,
            "gdd_c_day":round(sum(gdd),2) if gdd else None,
            "gdd_base_c":base_temperature_c}
