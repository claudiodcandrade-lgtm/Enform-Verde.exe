"""Validated direct-stock references for carbon compartments.

Only standing dry-mass stocks enter litter. Annual litterfall, depth alone,
and allometric deadwood proxies are explicitly excluded.
"""
from __future__ import annotations

def aoi_to_wgs84(aoi):
    """Normalize common AOI objects and infer EPSG:4326 only from lon/lat bounds.

    KML/KMZ readers can return valid geographic coordinates without attaching a
    CRS. Treating those as unknown caused regional stock references to silently
    disappear. Projected coordinates are never guessed.
    """
    import geopandas as gpd
    if isinstance(aoi, gpd.GeoDataFrame):
        frame=aoi.copy()
    elif isinstance(aoi, gpd.GeoSeries):
        frame=gpd.GeoDataFrame(geometry=aoi.copy())
    else:
        frame=gpd.GeoDataFrame(geometry=[aoi],crs="EPSG:4326")
    if frame.crs is None:
        bounds=frame.total_bounds
        west,south,east,north=map(float,bounds)
        if not (-180<=west<=east<=180 and -90<=south<=north<=90):
            raise ValueError("AOI sem CRS e coordenadas não reconhecíveis como longitude/latitude")
        frame=frame.set_crs("EPSG:4326")
    return frame.to_crs("EPSG:4326")

def tapajos_litter_stock_component(biome, physiognomy, aoi):
    """Closest direct standing-stock inventory for the matching Tapajos physiognomy.

    Uses only the first, pre-treatment control sampling (April 1999): three
    independent plots in each of two interdigitated soil types. The published
    cell errors are SEs. The six plot observations are pooled, and a two-sided
    95% Student-t interval (df=5) is reconstructed from the reported SEs.
    Repeated seasons and fertilized plots are deliberately excluded.
    """
    if str(biome or "").strip().casefold() not in ("amazônia", "amazonia"):
        return None
    p=str(physiognomy or "").casefold()
    if "floresta ombrófila densa" not in p and "floresta ombrofila densa" not in p:
        return None
    if aoi is None:
        return None
    try:
        g=aoi_to_wgs84(aoi)
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
    # McGroddy et al. Table 5, Apr. 1999 untreated controls:
    # sandy clay 4.4 (SE 0.6), sandy loam 5.5 (SE 1.4), n=3 each.
    import math
    n=6
    mean=(4.4+5.5)/2
    pooled_sd=math.sqrt((2*(3*0.6**2)+2*(3*1.4**2)
                         +3*(4.4-mean)**2+3*(5.5-mean)**2)/(n-1))
    se=pooled_sd/math.sqrt(n)
    # t(0.975, df=5)=2.5706; clamp the lower stock bound at zero.
    margin=2.5706*se
    return {
        "mean_dry_mg_ha":mean,
        "range_dry_mg_ha":[max(0.0,mean-margin),mean+margin],
        "method":"média gravimétrica do estoque de forest floor em parcelas-controle na FLONA Tapajós, abril/1999, antes de intervenção; duas classes de solo interdigitadas, n=3 parcelas independentes por classe (n total=6). IC95% t bilateral, gl=5, reconstruído das médias e erros-padrão publicados. Não é medição direta da AOI; não é produtividade/queda anual; transferência espacial limitada a 15 km e à classe IBGE Floresta Ombrófila Densa.",
        "source":"McGroddy et al. (2008), Journal of Geophysical Research: Biogeosciences 113, G04012, Tabela 5",
        "url":"https://doi.org/10.1029/2008JG000756",
        "status":"ESTOQUE GRAVIMÉTRICO DE REFERÊNCIA — MESMA CLASSE E MICRORREGIÃO",
        "origin":"INVENTARIO_DIRETO_MICRORREGIONAL",
        "uncertainty_kind":"IC95% t da média entre seis parcelas independentes; não incorpora erro de transferência para a AOI",
        "n_independent_units":n,
        "standard_error_dry_mg_ha":se,
        "degrees_of_freedom":5,
        "evidence_type":"standing_litter_dry_mass"
    }

def santo_ambrosio_litter_stock_component(biome, physiognomy, aoi):
    """Local gravimetric litter-stock summary for the Santo Ambrósio forest AOI.

    The reported 17 quadrats support the sampling interval for the farm-level
    mean only. They do not quantify class-specific or transfer uncertainty.
    Apply only to an AOI matching the known farm footprint and a compatible
    dense ombrophilous forest class.
    """
    import math
    if str(biome or "").strip().casefold() not in ("amazônia", "amazonia") or aoi is None:
        return None
    p=str(physiognomy or "").casefold()
    if "floresta ombrófila densa" not in p and "floresta ombrofila densa" not in p:
        return None
    try:
        frame=aoi_to_wgs84(aoi)
        west,south,east,north=map(float,frame.total_bounds)
        centroid=frame.geometry.union_all().centroid
        # CAR footprint envelope recorded for Fazenda Santo Ambrósio, Chaves/PA.
        if not (-49.678 <= west < east <= -49.333 and -0.153 <= south < north <= 0.078):
            return None
        if not (-49.658 <= centroid.x <= -49.353 and -0.133 <= centroid.y <= 0.058):
            return None
        area_ha=float(frame.to_crs("EPSG:6933").geometry.union_all().area/10000.0)
        if not 20000 <= area_ha <= 60000:
            return None
    except Exception:
        return None
    n=17
    mean=14.3876
    sd=9.2863
    se=sd/math.sqrt(n)
    margin=2.1199*se  # t(0.975, df=16)
    return {
        "mean_dry_mg_ha":mean,
        "range_dry_mg_ha":[max(0.0,mean-margin),mean+margin],
        "method":"estoque gravimétrico local de serapilheira: 17 quadrados de 0,5×0,5 m, massa seca após secagem a 70 °C até peso constante. Média 14,3876 Mg/ha, DP 9,2863 Mg/ha; IC95% t bilateral da média, gl=16. O IC representa somente erro amostral sob independência; não quantifica transferência entre classes ou representatividade espacial total da fazenda.",
        "source":"Inventário da Fazenda Santo Ambrósio — resumo local de 17 amostras gravimétricas de serapilheira",
        "status":"ESTOQUE GRAVIMÉTRICO LOCAL — IC95% AMOSTRAL; TRANSFERÊNCIA NÃO INCLUÍDA",
        "origin":"INVENTARIO_DIRETO_LOCAL",
        "uncertainty_kind":"IC95% t da média (n=17, gl=16); erro de transferência/classificação não estimado",
        "n_independent_units":n,
        "standard_error_dry_mg_ha":se,
        "degrees_of_freedom":n-1,
        "evidence_type":"standing_litter_dry_mass",
        "include_in_total":True,
    }

def tapajos_necromass_components(biome, physiognomy, aoi):
    """Published direct coarse-wood carbon stocks, geofenced to Tapajós forest.

    Pyle et al. report downed and standing CWD stocks separately for Tapajós
    subsites. Published 95% intervals are retained as carbon, avoiding an
    unsupported conversion to dry mass. Transfer uncertainty to the AOI is not
    included and the result is not used outside the local terra-firme domain.
    """
    if str(biome or "").strip().casefold() not in ("amazônia", "amazonia") or aoi is None:
        return {}
    p=str(physiognomy or "").casefold()
    if "floresta ombrófila densa" not in p and "floresta ombrofila densa" not in p:
        return {}
    try:
        frame=aoi_to_wgs84(aoi)
        from pyproj import Geod
        geod=Geod(ellps="WGS84")
        geom=frame.geometry.union_all()
        polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
        max_km=0.0
        for poly in polys:
            for x,y,*_ in poly.exterior.coords:
                _,_,d=geod.inv(float(x),float(y),-54.9833,-3.0667)
                max_km=max(max_km,abs(d)/1000)
        if max_km>15.0:return {}
    except Exception:
        return {}
    common={
        "method":"estoque diretamente medido de coarse woody debris (CWD) na FLONA Tapajós; média publicada de quatro subáreas (km 67, km 72 e km 117), IC95% publicado com bootstrap. O intervalo é amostral entre subáreas e não inclui erro de transferência até a AOI; estudo de floresta de terra firme, não extrapolar para várzea/mangue.",
        "source":"Pyle et al. (2008), Dynamics of carbon, biomass, and structure in two Amazonian forests, JGR Biogeosciences; Tabela 2, DOI 10.1029/2007JG000592",
        "url":"https://doi.org/10.1029/2007JG000592",
        "status":"NECROMASSA DIRETA — REFERÊNCIA MICRORREGIONAL TAPAJÓS; IC95% PUBLICADO",
        "origin":"INVENTARIO_DIRETO_MICRORREGIONAL",
        "uncertainty_kind":"IC95% publicado/bootstrapping; incerteza de transferência espacial não incluída",
        "sampling_units_reported":4,
        "evidence_type":"direct_coarse_woody_debris_carbon_stock",
    }
    return {
        "Necromassa aérea — madeira morta caída (CWD)":{**common,"mean_tc_ha":32.0,"range_tc_ha":[28.3,35.7],
            "method":common["method"]+" CWD caída: 32,0 Mg C/ha (IC95% 28,3–35,7)."},
        "Necromassa aérea — madeira morta em pé (CWD)":{**common,"mean_tc_ha":8.7,"range_tc_ha":[7.4,10.0],
            "method":common["method"]+" CWD em pé: 8,7 Mg C/ha (IC95% 7,4–10,0)."},
    }

def component_has_confidence_interval(component):
    """Return True only when the source explicitly describes a 95% confidence interval."""
    kind=str((component or {}).get("uncertainty_kind") or "").casefold()
    return any(marker in kind for marker in (
        "ic95", "ic aproximado de 95%", "intervalo de confiança de 95%",
        "intervalo preditivo aproximado de 95%"
    ))

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
        geom=aoi_to_wgs84(aoi).to_crs("EPSG:6933").geometry.union_all()
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
        # Last-resort, design-level prediction interval for one AOI-like unit.
        # The state/biome UA SD is the predictive dispersion; using only the
        # standard error of the statewide mean would materially understate it.
        try:
            from scipy.stats import t as student_t
            critical=float(student_t.ppf(0.975,n-1))
        except Exception:
            critical={1:12.706,2:4.303,3:3.182,4:2.776,5:2.571,6:2.447,7:2.365,
                      8:2.306,9:2.262,10:2.228,11:2.201,12:2.179,13:2.160,
                      14:2.145,15:2.131,16:2.120,17:2.110,18:2.101,19:2.093,
                      20:2.086,21:2.080,22:2.074,23:2.069,24:2.064,25:2.060,
                      26:2.056,27:2.052,28:2.048,29:2.045,30:2.042}.get(n-1,1.96)
        margin=critical*sd*math.sqrt(1.0+1.0/n)
        return {
          "mean_dry_mg_ha":mean,"range_dry_mg_ha":[max(0.0,mean-margin),mean+margin],
          "method":f"média direta de necromassa aérea IFN/SFB, agrupada por bioma {biome} × UF {uf}; {n} unidades amostrais independentes (UA). Intervalo preditivo aproximado de 95% para uma nova unidade, calculado com t({n-1}) × DP entre UAs × √(1+1/n), truncado em zero. Último nível da hierarquia quando não existe inventário por classe/proximidade. A tabela publicada não traz coordenadas nem classe IBGE; a extrapolação assume permutabilidade dentro do estrato bioma×UF e não valida correspondência da fitofisionomia da AOI.",
          "source":"SFB/IFN, Painel de Biomassa e Carbono — dados abertos de necromassa por UA (t matéria seca/ha)",
          "status":"FALLBACK ÚLTIMA HIERARQUIA — IFN BIOMA×UF; FITOFISIONOMIA NÃO ESTRATIFICADA",
          "origin":"INVENTARIO_DIRETO_IFN",
          "uncertainty_kind":"intervalo preditivo aproximado de 95% t da variabilidade entre UAs; assume permutabilidade no estrato bioma×UF; classe e transferência ecológica não quantificadas",
          "n_independent_units":n,"n_ua":n,"sd_between_ua_mg_ha":sd,
          "evidence_type":"direct_ifn_aboveground_necromass",
          "include_in_total":True
        }
    except Exception:
        return None

def rows_for_compartment(analysis_rows, prefix):
    """Select analysis rows for a named workbook sheet by stable compartment prefix."""
    prefix=str(prefix or "")
    return [row for row in (analysis_rows or [])
            if str(row.get("parametro","")).startswith(prefix)]
