"""CPTEC/INPE XML forecast client (municipality ID or coordinates).

CPTEC forecast is model guidance, not observed station data. Commercial
distribution may require authorization from CPTEC/INPE.
"""
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import quote
from xml.etree import ElementTree

BASE="https://servicos.cptec.inpe.br/XML"

def _read(url,opener):
    with opener(Request(url,headers={"User-Agent":"EnformVerde/3.24 climate-source-client"}),timeout=25) as response:
        data=response.read(2_000_001)
    if len(data)>2_000_000:raise ValueError("CPTEC XML response exceeds 2MB")
    return ElementTree.fromstring(data)

def forecast_by_city(city_id,*,seven_days=True,opener=urlopen):
    city=int(city_id)
    if city<=0:raise ValueError("CPTEC city ID must be positive")
    path=f"cidade/7dias/{city}/previsao.xml" if seven_days else f"cidade/{city}/previsao.xml"
    url=f"{BASE}/{path}"
    root=_read(url,opener)
    periods=[]
    for node in root.findall(".//previsao"):
        periods.append({child.tag:(child.text or "").strip() for child in node})
    return {"status":"forecast" if periods else "no_forecast",
            "source":"CPTEC/INPE XML","source_url":url,
            "kind":"previsao por municipio; nao observacao microrregional",
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
            "city_id":city,"periods":periods,
            "limitations":["A escala municipal não resolve microclimas do talhão",
                           "Verificar termos de uso antes de utilização comercial"]}

def forecast_by_coordinates(latitude,longitude,*,opener=urlopen):
    lat,lon=float(latitude),float(longitude)
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError("Invalid coordinates")
    url=f"{BASE}/cidade/{lat:.5f}/{lon:.5f}/estendidaLatLon.xml"
    root=_read(url,opener)
    periods=[{child.tag:(child.text or "").strip() for child in node} for node in root.findall(".//previsao")]
    return {"status":"forecast" if periods else "no_forecast",
            "source":"CPTEC/INPE XML","source_url":url,
            "kind":"previsao por coordenadas, nao estacao",
            "latitude":lat,"longitude":lon,
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
            "periods":periods,
            "limitations":["Precisao espacial depende do produto CPTEC",
                           "Verificar termos de uso antes de utilização comercial"]}
