"""Auditable, conservative calculation traces for experimental scientific estimates."""
import hashlib
import json
import math
import re

def number(x):
    if isinstance(x, bool):
        return None
    try:
        y = float(x)
        return y if math.isfinite(y) else None
    except (TypeError, ValueError):
        return None

def seal(record):
    data=json.dumps(record,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(",",":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def source_record(row):
    url=row.get("source_url") or row.get("url")
    sha=row.get("source_sha256") or row.get("dataset_sha256")
    url=url if isinstance(url,str) and url.startswith("https://") else None
    sha=sha.lower() if isinstance(sha,str) and re.fullmatch(r"[0-9a-fA-F]{64}",sha) else None
    return {"url":url,"sha256_claim":sha,"source_bytes_verified":False,
            "warning":"Declarar SHA256 nao e o mesmo que verificar os bytes publicados."}

def bounded(bounds, point):
    if not isinstance(bounds,(list,tuple)) or len(bounds)!=2 or point is None:
        return None
    low,high=(number(v) for v in bounds)
    return [low,high] if low is not None and high is not None and 0<=low<=point<=high else None

def audit_carbon_component(row, *, area_ha, formation, analysis_id=None):
    """Actual area*density arithmetic, separated from unverified AOI uncertainty."""
    if not isinstance(row,dict):
        raise ValueError("component must be a dict")
    area,density=number(area_ha),number(row.get("tc"))
    ref=source_record(row)
    out={"schema":"enform.experimental.trace.v1","kind":"carbon","analysis_id":analysis_id,
         "formation":str(formation),"pool":str(row.get("parametro","")),
         "source_name":str(row.get("fonte","")),"source":ref,
         "model":str(row.get("metodo","")),"scientifically_homologated":False}
    if area is None or density is None or area<0 or density<0:
        out.update(status="N/D",reason="Area/densidade ausente ou invalida",result=None)
    else:
        interval=bounded(row.get("range_tc_ha"),density)
        stock=area*density
        out.update(status="ESTIMATIVA_EXPERIMENTAL_NAO_HOMOLOGADA",
                   formula="stock_tC = density_tC_ha * intersected_area_ha; tCO2e = tC * 44/12",
                   inputs={"density_tC_ha":density,"intersected_area_ha":area},
                   result={"stock_tC":stock,"stock_tCO2e":stock*44/12},
                   density_source_range_tC_ha=interval,
                   scaled_source_range_tC=[v*area for v in interval] if interval else None,
                   uncertainty_kind=str(row.get("uncertainty_kind") or row.get("obs") or "desconhecida"),
                   is_AOI_CI95=False,
                   unquantified_errors=["transferencia espacial","classificacao/area",
                                       "covariancia entre estratos"],
                   note="Faixa da fonte vezes area nao e IC95% do total da AOI.",
                   source_auditable=bool(ref["url"] and ref["sha256_claim"]))
    out["trace_sha256"]=seal(out)
    return out

def audit_yield_forecast(forecast, *, analysis_id=None):
    """Historical regional productivity never proves individual field-scale coverage."""
    forecast=forecast if isinstance(forecast,dict) else {}
    value=number(forecast.get("yield_t_ha"))
    area=number(forecast.get("crop_area_ha"))
    iv=forecast.get("prediction_interval_t_ha")
    bounds=bounded([iv.get("lower"),iv.get("upper")],value) if isinstance(iv,dict) else None
    ref=source_record(forecast)
    out={"schema":"enform.experimental.trace.v1","kind":"yield","analysis_id":analysis_id,
         "crop":forecast.get("crop"),"model_id":forecast.get("model_id"),
         "source":ref,"training_source":forecast.get("training_source"),
         "geographic_domain":forecast.get("geographic_domain"),
         "temporal_domain":forecast.get("temporal_domain"),
         "interval_method":forecast.get("interval_method"),
         "uncertainty_kind":forecast.get("uncertainty_kind"),
         "scientifically_homologated":False,"field_coverage_validated":False,
         "warning":"PAM microrregional nao comprova produtividade em talhoes."}
    if value is None or value<0 or bounds is None:
        out.update(status="N/D",reason="Estimativa/intervalo ausente ou invalido",result=None)
    else:
        out.update(status="EXPERIMENTAL_NAO_HOMOLOGADO",
                   formula="production_t = yield_t_ha * mapped_crop_area_ha",
                   result={"yield_t_ha":value,"range_t_ha":bounds,
                           "production_t":value*area if area is not None and area>=0 else None,
                           "production_range_t":[v*area for v in bounds]
                           if area is not None and area>=0 else None},
                   source_auditable=bool(ref["url"] and ref["sha256_claim"]))
    out["trace_sha256"]=seal(out)
    return out

def eligible_experimental_yield(forecast):
    if not isinstance(forecast,dict) or forecast.get("status")!="previsao_experimental":
        return False
    trace=audit_yield_forecast(forecast)
    return (trace["status"]!="N/D" and trace["source_auditable"]
            and isinstance(forecast.get("model_id"),str) and bool(forecast["model_id"].strip())
            and isinstance(forecast.get("training_source"),str)
            and forecast["training_source"].startswith("https://")
            and isinstance(forecast.get("geographic_domain"),str)
            and bool(forecast["geographic_domain"].strip())
            and isinstance(forecast.get("temporal_domain"),str)
            and bool(forecast["temporal_domain"].strip())
            and forecast.get("uncertainty_kind") in (
                "explicit_uncalibrated_scenario_range",
                "empirical_spatiotemporal_prediction_interval")
            and isinstance(forecast.get("interval_method"),str)
            and bool(forecast["interval_method"].strip()))
