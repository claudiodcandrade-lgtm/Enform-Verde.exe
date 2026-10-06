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
