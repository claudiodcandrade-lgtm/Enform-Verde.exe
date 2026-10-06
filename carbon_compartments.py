"""Validated direct-stock references for carbon compartments.

Only standing dry-mass stocks enter litter. Annual litterfall, depth alone,
and allometric deadwood proxies are explicitly excluded.
"""
from __future__ import annotations

def tapajos_litter_stock_component(biome, physiognomy, aoi):
    """Direct standing forest-floor dry-mass reference, geofenced to the study site."""
    if str(biome or "").strip().casefold() not in ("amazônia", "amazonia"):
        return None
    p=str(physiognomy or "").casefold()
    if "floresta ombrófila densa" not in p and "floresta ombrofila densa" not in p:
        return None
    if aoi is None:
        return None
    try:
        g=aoi.to_crs("EPSG:4326")
        from pyproj import Geod
        geod=Geod(ellps="WGS84")
        geom=g.geometry.union_all()
        polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
        # Complete AOI boundary must remain inside the local study domain.
        max_km=0.0
        for poly in polys:
            for x,y,*_ in poly.exterior.coords:
                _,_,d=geod.inv(float(x),float(y),-54.9833,-3.0667)
                max_km=max(max_km,abs(d)/1000)
        if max_km>15.0:
            return None
    except Exception:
        return None
    return {
        "mean_dry_mg_ha":6.0,
        "range_dry_mg_ha":[0.0,11.8],
        "method":"massa seca do estoque de forest floor medida em parcelas controle na FLONA Tapajós; média publicada 6,0 ± 5,8 Mg/ha. Referência local, não medição da AOI; amplitude truncada em zero, não IC95%.",
        "source":"McGroddy et al. (2008), Journal of Geophysical Research: Biogeosciences 113, G04012",
        "url":"https://doi.org/10.1029/2008JG000756",
        "status":"ESTOQUE GRAVIMÉTRICO LOCAL — REFERÊNCIA",
        "origin":"LITERATURA_MICRORREGIONAL",
        "uncertainty_kind":"média ± dispersão publicada; amplitude descritiva, sem cobertura probabilística declarada",
        "evidence_type":"standing_litter_dry_mass"
    }

def empty_compartment(name, reason):
    return {
        "mean_dry_mg_ha":None, "range_dry_mg_ha":None,
        "method":reason, "source":"Sem observação direta compatível incluída na biblioteca",
        "status":"NÃO ESTIMADO — DADO DIRETO COMPATÍVEL INDISPONÍVEL",
        "origin":"NAO_ESTIMADO"
    }

UF_BY_IBGE_ID={
 "11":"Rondônia","12":"Acre","13":"Amazonas","14":"Roraima","15":"Pará","16":"Amapá","17":"Tocantins",
 "21":"Maranhão","22":"Piauí","23":"Ceará","24":"Rio Grande do Norte","25":"Paraíba","26":"Pernambuco",
 "27":"Alagoas","28":"Sergipe","29":"Bahia","31":"Minas Gerais","32":"Espírito Santo","33":"Rio de Janeiro",
 "35":"São Paulo","41":"Paraná","42":"Santa Catarina","43":"Rio Grande do Sul","50":"Mato Grosso do Sul",
 "51":"Mato Grosso","52":"Goiás","53":"Distrito Federal"
}
IBGE_UF_GEOJSON_URL="https://servicodados.ibge.gov.br/api/v3/malhas/estados?formato=application/vnd.geo+json&qualidade=minima"

def infer_uf_from_aoi(aoi, cache_dir=None):
    """Find the UF with greatest AOI area overlap using official IBGE state boundaries."""
    from pathlib import Path
    import json, requests
    try:
        import geopandas as gpd
    except ImportError:
        return None
    cache=Path(cache_dir or Path.home()/".enform_verde"/"data"/"IBGE")
    cache.mkdir(parents=True,exist_ok=True)
    target=cache/"unidades_federacao_ibge_minima.geojson"
    try:
        if not target.exists() or target.stat().st_size<1000:
            response=requests.get(IBGE_UF_GEOJSON_URL,timeout=(10,90))
            response.raise_for_status()
            tmp=target.with_suffix(".part"); tmp.write_bytes(response.content); tmp.replace(target)
        states=gpd.read_file(target)
        if states.empty or "geometry" not in states: return None
        id_field=next((k for k in ("id","codarea","CD_UF","CD_GEOCUF") if k in states.columns),None)
        if id_field is None:return None
        states=states.to_crs("EPSG:6933")
        geom=aoi.to_crs("EPSG:6933").geometry.union_all()
        areas=states.geometry.intersection(geom).area
        if len(areas)==0 or float(areas.max())<=0:return None
        raw=str(states.iloc[int(areas.argmax())][id_field]).zfill(2)
        return UF_BY_IBGE_ID.get(raw)
    except Exception:
        return None

def ifn_necromass_component(biome, uf, csv_path):
    """Direct SFB/IFN Panel mean by biome×UF; keeps UAs as independent units.

    The released table has no plot coordinates or IBGE physiognomy field, so
    this is explicitly a state-level inventory reference, not a class-specific
    AOI estimate. It is never interpreted as belowground necromass.
    """
    import csv, math
    if not uf or not csv_path:return None
    try:
        with open(csv_path,encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        row=next((r for r in rows if r.get("bioma","").strip().casefold()==str(biome or "").strip().casefold()
                  and r.get("uf","").strip().casefold()==str(uf).strip().casefold()),None)
        if not row:return None
        n=int(row["n_ua"]); mean=float(row["mean_dry_mg_ha"]); sd=float(row["sd_between_ua_mg_ha"])
        if n<2 or not all(math.isfinite(x) for x in (mean,sd)) or mean<0 or sd<0:return None
        # Student-t critical for df>=30 is close to 1.96; a conservative 1.96 SE
        # is labeled an approximate sampling interval, not AOI prediction error.
        margin=1.96*sd/math.sqrt(n)
        return {
          "mean_dry_mg_ha":mean,"range_dry_mg_ha":[max(0.0,mean-margin),mean+margin],
          "method":f"média direta de necromassa aérea IFN/SFB, agrupada por bioma {biome} × UF {uf}; {n} unidades amostrais independentes (UA). IC aproximado de 95% da média entre UAs. A tabela publicada não traz coordenadas nem classe IBGE; este valor é referência estadual agregada, não estimativa validada para a fitofisionomia da AOI.",
          "source":"SFB/IFN, Painel de Biomassa e Carbono — dados abertos de necromassa por UA (t matéria seca/ha)",
          "status":"INVENTÁRIO DIRETO IFN — REFERÊNCIA BIOMA×UF; FITOFISIONOMIA NÃO ESTRATIFICADA",
          "origin":"INVENTARIO_DIRETO_IFN",
          "uncertainty_kind":"IC aproximado de 95% da média entre UAs; não inclui erro de transferência espacial/classe",
          "n_independent_units":n,"n_ua":n,"sd_between_ua_mg_ha":sd,
          "evidence_type":"direct_ifn_aboveground_necromass",
          "include_in_total":False
        }
    except Exception:
        return None
