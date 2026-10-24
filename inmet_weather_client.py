"""Public INMET automatic station observations; BDMEP historical access is not assumed public/API-enabled."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from math import asin,cos,radians,sin,sqrt
import json
from urllib.request import Request,urlopen

STATIONS_URL="https://apitempo.inmet.gov.br/estacoes/T"
OBS_URL="https://apitempo.inmet.gov.br/estacao"

def _get_json(url,timeout=18):
    with urlopen(Request(url,headers={"User-Agent":"EnformVerde/3.24 meteorology","Accept":"application/json"}),timeout=timeout) as response:
        return json.load(response)

def _number(v):
    if isinstance(v,(int,float)):return float(v)
    if isinstance(v,str):
        try:return float(v.strip().replace(",","."))
        except ValueError:return None
    return None

def _distance_km(lat1,lon1,lat2,lon2):
    p1,p2=radians(lat1),radians(lat2)
    dlat=p2-p1;dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(p1)*cos(p2)*sin(dlon/2)**2
    return 12742*asin(min(1,sqrt(a)))

def nearest_automatic_stations(lat,lon,stations,max_distance_km=150,limit=5):
    candidates=[]
    for st in stations:
        la=_number(st.get("VL_LATITUDE"));lo=_number(st.get("VL_LONGITUDE"))
        code=st.get("CD_ESTACAO")
        if la is None or lo is None or not code:continue
        distance=_distance_km(lat,lon,la,lo)
        if distance<=max_distance_km:candidates.append((distance,st))
    return sorted(candidates,key=lambda item:item[0])[:limit]

def fetch_inmet_nearby(lat,lon,days=7,max_distance_km=150):
    """Return observations or a transparent unavailable status, never silently replace with POWER."""
    result={"status":"indisponivel","source":"INMET estações automáticas (API pública)",
            "bdmep":"BDMEP histórico: acesso/API não confirmado; não consultado",
            "station":None,"distance_km":None,"temperature_mean_c":None,
            "rain_mm":None,"records":0,"source_url":STATIONS_URL}
    try:
        stations=_get_json(STATIONS_URL)
        if not isinstance(stations,list):raise ValueError("catálogo INMET inválido")
        candidates=nearest_automatic_stations(lat,lon,stations,max_distance_km)
        if not candidates:
            result["reason"]="nenhuma estação automática no raio de "+str(max_distance_km)+" km"
            return result
        end=datetime.now(timezone.utc).date()-timedelta(days=1)
        start=end-timedelta(days=max(1,days)-1)
        for distance,st in candidates:
            code=st["CD_ESTACAO"]
            url=f"{OBS_URL}/{start:%Y-%m-%d}/{end:%Y-%m-%d}/{code}"
            try:
                rows=_get_json(url)
                if not isinstance(rows,list) or not rows:continue
                temperatures=[x for row in rows if (x:=_number(row.get("TEM_INS"))) is not None]
                # Hourly precipitation; missing hours invalidate a complete-period total.
                rain=[x for row in rows if (x:=_number(row.get("CHUVA"))) is not None]
                result.update(status="observado",station=st.get("DC_NOME") or code,
                              station_code=code,distance_km=round(distance,1),
                              temperature_mean_c=round(sum(temperatures)/len(temperatures),2) if temperatures else None,
                              rain_mm=round(sum(rain),2) if rain else None,
                              rain_records=len(rain),records=len(rows),
                              period=f"{start:%Y-%m-%d} a {end:%Y-%m-%d}",source_url=url,
                              note="Chuva somada apenas nas horas disponíveis; verificar lacunas antes de interpretar como acumulado integral.")
                return result
            except Exception:continue
        result["reason"]="estações encontradas, mas sem observações acessíveis no período"
    except Exception as exc:
        result["reason"]=type(exc).__name__+": "+str(exc)
    return result

def weather_executive_lines(inmet=None,power=None,forecast=None,fmt=str):
    lines=["PAINEL EXECUTIVO — METEOROLOGIA","PRIORIDADE: INMET (estações automáticas) → NASA POWER (grade) → CPTEC/INPE (previsão)",
           "INMET/BDMEP — OBSERVAÇÕES"]
    if inmet and inmet.get("status")=="observado":
        lines.extend(["Estação: "+str(inmet["station"])+" | distância: "+fmt(inmet["distance_km"])+" km",
                      "Período: "+str(inmet.get("period","N/D")),
                      "Temperatura média: "+(fmt(inmet["temperature_mean_c"])+" °C" if inmet.get("temperature_mean_c") is not None else "N/D"),
                      "Chuva registrada nas horas disponíveis: "+(fmt(inmet["rain_mm"])+" mm" if inmet.get("rain_mm") is not None else "N/D"),
                      "Registros horários: "+str(inmet["records"])+" | "+inmet.get("note","")])
    else:lines.append("Sem observações INMET verificadas: "+str((inmet or {}).get("reason","consulta não realizada")))
    lines.append("NASA POWER — GRADE SATELITAL/MODELADA")
    if power:
        for key,label,unit in [("mean_temperature_c","Temperatura média","°C"),("rain_mm","Precipitação","mm"),("gdd_c_day","Graus-dia base 10 °C","°C dia")]:
            value=power.get(key)
            lines.append(label+": "+(fmt(value)+" "+unit if isinstance(value,(int,float)) else "N/D"))
        lines.append("Dias com temperatura: "+str(power.get("temperature_days","N/D")))
    else:lines.append("Sem dados disponíveis")
    lines.append("CPTEC/INPE — PREVISÃO")
    if forecast:
        lines.append("Períodos recebidos: "+str(len(forecast.get("periods",[])))+"; não interpretar repetições como dias independentes.")
    else:lines.append("Previsão indisponível")
    lines.extend(["BDMEP: consulta automática histórica não habilitada sem acesso oficial confirmado.",
                  "Observação pontual de estação, estimativa em grade e previsão são produtos distintos.",
                  "Fenologia, vigor e produtividade não são deduzidos somente desses dados.",""])
    return lines
