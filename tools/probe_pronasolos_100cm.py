"""Live reproducible probe of official PronaSolos 0–100 cm MapServer.

Only remote observations are recorded. This does NOT validate spatial
representativeness, stock calibration or 95% predictive intervals.
No environmental observations are simulated.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

# Script execution from tools/ must resolve the repository's own modules.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from pronasolos_identify import LAYER_IDS, SERVICE, build_identify_params, extract_paired_horizons
from soil_profile_stats import summarize_paired_soil_profiles

SITES = (
    ("Amazônia — Tapajós", -54.95, -3.03),
    ("Cerrado — Brasília", -47.93, -15.85),
    ("Caatinga — Petrolina", -40.53, -9.32),
    ("Mata Atlântica — Itapetininga", -48.05, -23.6),
    ("Pantanal — Nhecolândia", -56.70, -18.70),
)

def web_mercator(lon,lat):
    if not -180 <= lon <= 180 or not -85 <= lat <= 85:
        raise ValueError("invalid test site coordinates")
    radius=6378137.0
    return radius*math.radians(lon),radius*math.log(math.tan(math.pi/4+math.radians(lat)/2))

def query_site(session,name,lon,lat):
    x,y=web_mercator(lon,lat)
    params=build_identify_params(x,y,(x-5000,y-5000,x+5000,y+5000))
    result={"name":name,"lon":lon,"lat":lat,"status":"INCOMPLETE","layer_ids_requested":list(LAYER_IDS),
            "method":"ArcGIS identify; one point, five native 90-m horizons",
            "uncertainty_kind":"not estimated: pixel values are not field validation"}
    try:
        response=session.get(SERVICE,params=params,timeout=(5,12))
        response.raise_for_status()
        raw=response.content
        result["http_status"]=response.status_code
        result["response_sha256"]=hashlib.sha256(raw).hexdigest()
        payload=response.json()
        horizon=extract_paired_horizons(payload)
        result["received_layer_ids"]=sorted(horizon)
        result["observed_stock_tc_ha_by_layer"]={str(k):float(v) for k,v in horizon.items()}
        products=summarize_paired_soil_profiles([horizon])
        result["profiles_tc_ha"]={k:v["tc_ha"] for k,v in products.items()}
        result["status"]="PASS_0_100_COMPLETE" if "0–100 cm" in products else "INCOMPLETE_NO_EXTRAPOLATION"
    except Exception as exc:
        result["status"]="ERROR_RETRIEVAL_OR_VALIDATION"
        result["error"]=type(exc).__name__+": "+str(exc)[:300]
    return result

def main():
    output=Path(sys.argv[1]) if len(sys.argv)>1 else Path("pronasolos_probe_100cm.json")
    with requests.Session() as session:
        sites=[query_site(session,*site) for site in SITES]
    report={
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "service":SERVICE,
        "service_metadata":"https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer",
        "target_depth_cm":100,
        "layers_requested":list(LAYER_IDS),
        "status":"PASS_SOME_COMPLETE" if any(x["status"]=="PASS_0_100_COMPLETE" for x in sites) else "NO_COMPLETE_SITE",
        "limitations":"Point retrieval proof only; not a sampled AOI estimate, independent validation, field truth, 95% CI or proof of five-biome accuracy",
        "sites":sites
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("PRONASOLOS_0_100_REAL_SERVICE_PROBE",report["status"],output)
    for site in sites:
        print(site["name"],site["status"],site.get("received_layer_ids"),site.get("error",""))
    return 0 if report["status"]=="PASS_SOME_COMPLETE" else 2

if __name__=="__main__":
    sys.exit(main())
