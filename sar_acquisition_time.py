"""SAR acquisition chronology in Brasília time (America/Sao_Paulo).

Use acquisition timestamps, never publication/processing/download timestamps.
Unknown dates are explicit and never ordered above known acquisitions.
"""
from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BRASILIA = ZoneInfo("America/Sao_Paulo")
FIELDS = ("startTime","start_time","start_datetime","datetime","acquisitionDate",
          "acquisition_datetime","sceneDate","scene_date","acquired","timeStart")

def acquisition_utc(scene):
    if not isinstance(scene,dict):
        return None
    p=scene.get("properties") or {}
    for container in (scene,p):
        for field in FIELDS:
            value=container.get(field)
            if value is None:continue
            if isinstance(value,(int,float)):
                try:return datetime.fromtimestamp(value/1000 if value>1e11 else value, tz=timezone.utc)
                except (ValueError,OverflowError):continue
            if isinstance(value,str):
                try:
                    d=datetime.fromisoformat(value.replace("Z","+00:00"))
                    # A naive timestamp cannot reliably be mapped to Brasília.
                    if d.tzinfo is not None:return d.astimezone(timezone.utc)
                except ValueError:continue
    return None

def annotate_acquisition(scene):
    item=dict(scene)
    dt=acquisition_utc(item)
    item["acquisition_utc"]=dt.isoformat(timespec="seconds").replace("+00:00","Z") if dt else None
    item["acquisition_brasilia"]=dt.astimezone(BRASILIA).strftime("%d/%m/%Y %H:%M:%S") if dt else None
    item["acquisition_timezone"]="America/Sao_Paulo (Brasília; UTC−03:00)"
    item["acquisition_status"]="CONFIRMADA" if dt else "SEM_HORARIO_AQUISICAO_VERIFICAVEL"
    return item

def newest_acquisitions(items):
    records=[annotate_acquisition(it) for it in items]
    return sorted(records,key=lambda x:(x["acquisition_utc"] is not None,x["acquisition_utc"] or ""),reverse=True)

def summarize_catalog_acquisition(items):
    ordered=newest_acquisitions(items)
    return {"latest":ordered[0] if ordered and ordered[0]["acquisition_utc"] else None,
            "items":ordered, "date_policy":"aquisição real, mais recente primeiro; data desconhecida após datadas",
            "warning":"A cena mais nova só pode ser utilizada se polarização, produto, cobertura e modelo forem compatíveis. O mosaico composto exige datas por cena."}


def acquisition_display(scene):
    """Clearly distinguish annual ESA CCI L4 reference periods from SAR scene timestamps."""
    import re
    path=str(scene.get("path") or scene.get("scene") or "")
    m=re.search(r"ESACCI-BIOMASS-L4-(?:AGB|AGB_SD)-MERGED-100m-(20\d{2})-fv[0-9.]+\.tif",path,re.I)
    if m:
        year=m.group(1)
        return {"brasilia":"NÃO SE APLICA — produto anual composto",
                "utc":"NÃO SE APLICA — produto anual composto",
                "reference_period":year,
                "explanation":"ESA CCI Biomass L4: mapa anual multissensor; não é cena de aquisição instantânea. Não atribuir hora da data de referência ou de processamento como aquisição."}
    dt=scene.get("acquisition_utc")
    br=scene.get("acquisition_brasilia")
    if dt and br:
        return {"brasilia":str(br),"utc":str(dt),"reference_period":None,"explanation":None}
    return {"brasilia":"NÃO IDENTIFICADO NOS METADADOS",
            "utc":"NÃO IDENTIFICADO NOS METADADOS",
            "reference_period":None,
            "explanation":"Verificar metadados do produto/catálogo de origem; não assumir horário a partir de nome, criação ou download do arquivo."}
