"""Zonal fertility estimates from REAL Embrapa 90 m numerical WCS rasters.

No laboratory observation is inferred; no RGB/renderer imagery is accepted.
Per-depth estimates are map predictions, with descriptive spatial variability
only (not a calibrated predictive confidence interval). Failures return N/D.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from math import ceil, isfinite
from pathlib import Path

WCS = "https://geoinfo.dados.embrapa.br/geoserver/ows"
CATALOG = "https://geoportal.sgb.gov.br/server/rest/services/pronasolos/atributos_solo_90m/MapServer"
LICENSE = "Embrapa Solos; CC BY-NC 3.0 BR — uso comercial depende de autorização"
DEPTHS = ("0-5", "5-15", "15-30", "30-60", "60-100", "100-200")
ATTRS = {
    "ph": ("pH", "", 44, ("acidez", "ph")),
    "ctc": ("CTC", "cmolc/kg", 37, ("capacidade de troca", "ctc", "cation exchange")),
    "ce": ("Condutividade elétrica", "dS/m", 51, ("condutividade", "salinidade", "electrical conductivity")),
    "sand": ("Areia", "g/kg", 16, ("areia", "sand")),
    "silt": ("Silte", "g/kg", 30, ("silte", "silt")),
    "clay": ("Argila", "g/kg", 23, ("argila", "clay")),
    "organic_carbon": ("Carbono orgânico (teor)", "g/kg", 9, ("teor de carbono", "carbon content", "organic carbon")),
}
UNAVAILABLE = ("Fósforo disponível (P)", "Potássio trocável (K)",
               "Cálcio trocável (Ca)", "Magnésio trocável (Mg)",
               "Alumínio trocável (Al)", "Saturação por bases (V%)",
               "Matéria orgânica laboratorial")
MAX_CELLS = 1_000_000
MAX_TILES = 6


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _xml10_clean(payload):
    """Remove XML 1.0 forbidden code points/entities emitted by broken WCS metadata."""
    raw = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(payload)
    def valid(code):
        return code in (0x9, 0xA, 0xD) or 0x20 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD or 0x10000 <= code <= 0x10FFFF
    def entity(match):
        token = match.group(1) or match.group(2)
        try:
            code = int(token, 16 if match.group(1) else 10)
        except ValueError:
            return ""
        return match.group(0) if valid(code) else ""
    raw = re.sub(r"&#(?:x([0-9a-fA-F]+)|([0-9]+));", entity, raw)
    return "".join(ch for ch in raw if valid(ord(ch)))


def discover_coverages(xml_bytes):
    """Match only advertised, depth-specific national WCS coverages.

    A guessed coverage identifier is never sent as if its existence were verified.
    Broken XML 1.0 control references from the WCS are stripped without guessing
    coverage IDs; malformed structural XML remains a technical error.
    """
    root = ET.fromstring(_xml10_clean(xml_bytes))
    selected = {}
    for node in root.iter():
        if node.tag.split("}")[-1] != "CoverageSummary":
            continue
        fields = {}
        for child in node:
            local = child.tag.split("}")[-1]
            if local in ("CoverageId", "Title", "Abstract", "Identifier"):
                fields.setdefault(local, []).append(child.text or "")
        cov = (fields.get("CoverageId") or fields.get("Identifier") or [""])[0].strip()
        title = " ".join(fields.get("Title", []) + fields.get("Abstract", []))
        words = _norm(cov + " " + title)
        if not cov or not ("90m" in words.replace(" ", "") or "90 m" in words):
            continue
        for name, (_label, _unit, _first, aliases) in ATTRS.items():
            if not any(re.search(r"(?<![a-z0-9])" + re.escape(_norm(a)) +
                                 r"(?![a-z0-9])", words) for a in aliases):
                continue
            for index, depth in enumerate(DEPTHS):
                low, high = depth.split("-")
                patterns = (rf"(?<!\d)0*{low}\s+(?:a\s+|to\s+)?0*{high}(?!\d)",
                            rf"(?<!\d)0*{low}\s+0*{high}\s*cm\b")
                if any(re.search(p, words) for p in patterns):
                    key = (name, depth)
                    # Ambiguous matching is N/D, not arbitrary selection.
                    if key in selected and selected[key] != cov:
                        selected[key] = None
                    else:
                        selected.setdefault(key, cov)
    return {k: v for k, v in selected.items() if v is not None}


def _weights(gdf, ds, max_cells=MAX_CELLS):
    """Exact AOI × cell weights in EPSG:6933; zero weight for uncovered pixels."""
    import numpy as np
    import shapely
    from pyproj import Transformer
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds, Window, transform as window_transform
    from shapely.geometry import mapping

    geom = gdf.to_crs(ds.crs).geometry.union_all()
    if geom.is_empty:
        raise ValueError("polígono vazio")
    if not geom.is_valid:
        from shapely.validation import make_valid
        geom = make_valid(geom)
    left, bottom, right, top = ds.bounds
    x0, y0, x1, y1 = geom.bounds
    if x1 <= left or x0 >= right or y1 <= bottom or y0 >= top:
        raise ValueError("sem cobertura no raster oficial")
    # Enclosing integer pixel window: preserve cells partially touched by AOI.
    from math import floor
    fw = from_bounds(max(x0, left), max(y0, bottom), min(x1, right),
                     min(y1, top), transform=ds.transform)
    col0, row0 = floor(fw.col_off), floor(fw.row_off)
    col1, row1 = ceil(fw.col_off + fw.width), ceil(fw.row_off + fw.height)
    win = Window(col0, row0, col1-col0, row1-row0).intersection(Window(0, 0, ds.width, ds.height))
    if win.width * win.height > max_cells:
        raise ValueError("AOI excede limite de pixels; usar processamento por blocos")
    h, w = int(win.height), int(win.width)
    transform = window_transform(win, ds.transform)
    touched = geometry_mask([mapping(geom)], out_shape=(h,w),
                            transform=transform, invert=True, all_touched=True)
    rows, cols = np.nonzero(touched)
    vals = ds.read(1, window=win, masked=True)
    if not len(rows):
        raise ValueError("nenhuma célula intersectada")
    xmin = transform.c + cols * transform.a
    xmax = xmin + transform.a
    ymax = transform.f + rows * transform.e
    ymin = ymax + transform.e
    boxes = shapely.box(np.minimum(xmin,xmax), np.minimum(ymin,ymax),
                        np.maximum(xmin,xmax), np.maximum(ymin,ymax))
    tr = Transformer.from_crs(ds.crs, "EPSG:6933", always_xy=True)
    def equal_area(parts):
        return shapely.area(shapely.transform(parts,
            lambda xy: np.column_stack(tr.transform(xy[:,0], xy[:,1]))))
    inner = shapely.contains(geom, boxes)
    weights = np.zeros(len(boxes), dtype=float)
    if inner.any():
        weights[inner] = equal_area(boxes[inner])
    if (~inner).any():
        weights[~inner] = equal_area(shapely.intersection(boxes[~inner],geom))
    data = vals[rows, cols]
    mask = ~np.ma.getmaskarray(data) & np.isfinite(np.asarray(data))
    raw = np.asarray(np.ma.filled(data, np.nan), dtype=float)
    return weights, raw, mask


def zonal_raster(gdf, raster_path, *, attribute, depth, max_cells=MAX_CELLS):
    """Return weighted raster mean and actual covered area, never an invented IC95%."""
    import numpy as np
    import rasterio
    if attribute not in ATTRS or depth not in DEPTHS:
        raise ValueError("atributo/profundidade não reconhecido")
    if gdf.crs is None:
        raise ValueError("AOI sem CRS")
    with rasterio.open(raster_path) as ds:
        if ds.count != 1 or ds.dtypes[0] not in ("float32", "float64") or ds.crs is None:
            raise ValueError("somente raster NUMÉRICO bruto float de uma banda e CRS")
        if abs(ds.transform.b)>1e-10 or abs(ds.transform.d)>1e-10:
            raise ValueError("grade raster rotacionada")
        weights, values, valid = _weights(gdf, ds, max_cells)
    valid &= weights > 0
    if attribute == "ph":
        valid &= (values > 0) & (values <= 14)
    elif attribute in ("sand","silt","clay"):
        valid &= (values >= 0) & (values <= 1000)
    else:
        valid &= values >= 0
    if not valid.any():
        raise ValueError("nenhum pixel bruto válido na interseção")
    vv, ww = values[valid], weights[valid]
    mean = float(np.average(vv, weights=ww))
    sd = float(np.sqrt(np.average((vv - mean)**2, weights=ww))) if len(vv)>1 else None
    # Full AOI area is distinct from the valid mapped area.
    total = float(gdf.to_crs(6933).geometry.union_all().area) / 10000
    mapped = float(ww.sum()) / 10000
    return {"mean": mean, "spatial_sd": sd, "valid_pixels": int(valid.sum()),
            "mapped_area_ha": mapped,
            "aoi_area_ha": total,
            "coverage_pct": min(100., 100*mapped/total) if total else 0.,
            "uncertainty": "N/D — DP espacial descritivo não é erro preditivo ou IC95%",
            "method": "interseção geométrica exata AOI × pixel, peso EPSG:6933"}


def _download_coverage(session, coverage_id, geom, path, max_tiles=MAX_TILES):
    """Fetch raw TIFF through the official Embrapa WCS, not MapServer export."""
    import rasterio
    from rasterio.merge import merge
    from pronasolos_wcs import (_window_bounds, _tiles, coverage_url,
                                 validate_tile, _download, NODATA)
    bounds = _window_bounds(geom)
    tiles = list(_tiles(bounds))
    if len(tiles)>max_tiles:
        raise ValueError("AOI grande: cobertura dividida em mais blocos que o limite operacional")
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = path.with_suffix(".provenance.json")
    if path.is_file() and manifest_path.is_file():
        try:
            recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_tile(path)
            cached_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if (recorded.get("coverage_id") == coverage_id and
                    recorded.get("source") == WCS and
                    recorded.get("sha256") == cached_sha):
                return cached_sha
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    # Do not trust stale TIFFs without matching product identity and hash.
    path.unlink(missing_ok=True)
    manifest_path.unlink(missing_ok=True)
    tmpfiles = []
    for i,tile in enumerate(tiles):
        tmp = path.with_name(path.stem + f"_tile{i}.tif")
        _download(coverage_url(coverage_id, tile), tmp, session, (10,50), attempts=2)
        validate_tile(tmp)
        tmpfiles.append(tmp)
    if len(tmpfiles) == 1:
        tmpfiles[0].replace(path)
    else:
        datasets = [rasterio.open(p) for p in tmpfiles]
        try:
            arr,transform = merge(datasets, nodata=NODATA)
            profile = datasets[0].profile.copy()
        finally:
            for ds in datasets: ds.close()
        profile.update(transform=transform, height=arr.shape[1],
                       width=arr.shape[2], nodata=NODATA, compress="deflate")
        with rasterio.open(path, "w", **profile) as out: out.write(arr)
        for p in tmpfiles: p.unlink(missing_ok=True)
    validate_tile(path)
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda:src.read(1024*1024), b""): h.update(chunk)
    digest = h.hexdigest()
    manifest_path.write_text(json.dumps({
        "coverage_id":coverage_id, "source":WCS, "sha256":digest,
        "retrieval_kind":"numerical WCS GetCoverage, not MapServer render",
        "downloaded_utc":datetime.now(timezone.utc).isoformat()
    }, ensure_ascii=False, indent=2),encoding="utf-8")
    return digest


def analyze_fertility(aoi, *, units=None, session=None, coverages=None,
                      cache_root=None, max_cells=MAX_CELLS):
    """National attempt with controlled N/D and per-soil-unit zonal means.

    units = iterable of (mapping unit label, GeoDataFrame geometry).
    Nothing in the output is a laboratory observation or changes SOC stock.
    """
    import requests
    import geopandas as gpd
    result = {"status":"N/D", "method":"raster bruto WCS 90 m + interseção AOI×pixels",
              "source":WCS, "catalog":CATALOG, "license":LICENSE,
              "retrieved_utc":datetime.now(timezone.utc).isoformat(),
              "laboratory_samples":None, "validation_accuracy":None, "ic95":None,
              "unavailable_attributes":list(UNAVAILABLE), "layers":[], "units":{},
              "carbon_stock_independent":True}
    if aoi is None or aoi.crs is None:
        result["reason"]="AOI sem CRS"
        return result
    session = session or requests.Session()
    try:
        if coverages is None:
            response = session.get(WCS, params={"service":"WCS","version":"2.0.1",
                                      "request":"GetCapabilities"}, timeout=(8,25))
            response.raise_for_status()
            coverages = discover_coverages(response.content)
        if not coverages:
            result["reason"]="WCS oficial não retornou identificadores de coberturas químicas compatíveis"
            from soil_fertility_arcgis_identify import sample_official_fertility
            alternate=sample_official_fertility(aoi,session=session)
            if alternate.get("status")=="MAPA_PREDITIVO_AMOSTRAL":
                alternate["wcs_diagnostic"]=result["reason"]
                return alternate
            result["fallback_status"]=alternate.get("status")
            result["reason"]+="; MapServer Identify: "+str(alternate.get("reason") or "N/D")
            return result
        from shapely.geometry import mapping
        geom = aoi.to_crs(4326).geometry.union_all()
        bounds_key = hashlib.sha256(geom.wkb).hexdigest()[:18]
        root = Path(cache_root or (Path.home()/".enform_verde"/"fertilidade_90m")) / bounds_key
        geometry_units = [("PROPRIEDADE — sem atribuição pedológica",aoi)]
        if units:
            geometry_units += [(str(name),zone) for name,zone in units if zone is not None]
        success = 0
        for attr,(label,unit,layer_first,aliases) in ATTRS.items():
            for i,depth in enumerate(DEPTHS):
                layer={"attribute":attr,"label":label,"unit":unit,"depth_cm":depth,
                       "mapserver_layer_id":layer_first+i,
                       "mapserver_url":CATALOG+"/"+str(layer_first+i),
                       "wcs_coverage_id":coverages.get((attr,depth)),
                       "status":"N/D"}
                cov=coverages.get((attr,depth))
                if not cov:
                    layer["reason"]="camada WCS não encontrada no catálogo; não interpolar"
                    result["layers"].append(layer)
                    continue
                out = root / (attr+"_"+depth.replace("-","_")+".tif")
                try:
                    digest=_download_coverage(session,cov,geom,out)
                    layer.update({"sha256":digest,"file":str(out),"source":WCS})
                    mapped_property = False
                    for key,zone in geometry_units:
                        try:
                            stats=zonal_raster(zone,out,attribute=attr,depth=depth,max_cells=max_cells)
                        except (ValueError,RuntimeError) as exc:
                            stats={"status":"N/D","reason":str(exc)[:160]}
                        if key == geometry_units[0][0] and stats.get("mean") is not None:
                            mapped_property = True
                        result["units"].setdefault(key,[]).append({
                            "attribute":attr,"label":label,"unit":unit,
                            "depth_cm":depth,"wcs_coverage_id":cov,
                            "mapserver_layer_id":layer_first+i,"raster_sha256":digest, **stats})
                    if mapped_property:
                        layer["status"]="MAPA_PREDITIVO_NUMERICO_COM_INTERSECAO"
                        success+=1
                    else:
                        layer["reason"]="Raster recebido, mas sem pixels numericamente válidos na propriedade"

                except Exception as exc:
                    layer["reason"]=type(exc).__name__+": "+str(exc).split("https://")[0][:180]
                result["layers"].append(layer)
        attempted=[x for x in result["layers"] if x.get("wcs_coverage_id")]
        technical_failures=[x for x in attempted if x.get("reason") and x.get("mean") is None]
        result["status"]=("MAPEAMENTO_PREDITIVO_PARCIAL" if success else
                          "ERRO_TECNICO" if technical_failures else "N/D")
        result["reason"]=(f"{success} de {len(ATTRS)*len(DEPTHS)} camadas processadas; "
                          "sem validação local de acurácia" if success else
                          f"Falha técnica em {len(technical_failures)} camadas WCS com cobertura anunciada"
                          if technical_failures else
                          "Catálogo oficial sem pixels/coberturas compatíveis na AOI")
        if not success:
            from soil_fertility_arcgis_identify import sample_official_fertility
            alternate=sample_official_fertility(aoi,session=session)
            if alternate.get("status")=="MAPA_PREDITIVO_AMOSTRAL":
                alternate["wcs_diagnostic"]=result["reason"]
                return alternate
            result["reason"]+="; MapServer Identify: "+str(alternate.get("reason") or "N/D")
        result["uncertainty_note"]="Médias de mapas digitais, não ensaios da propriedade. DP entre pixels não fornece IC95%; variância do modelo indisponível."
    except Exception as exc:
        result["status"]="ERRO_TECNICO"
        result["reason"]=type(exc).__name__+": "+str(exc).split("https://")[0][:180]
        try:
            from soil_fertility_arcgis_identify import sample_official_fertility
            alternate=sample_official_fertility(aoi,session=session)
            if alternate.get("status")=="MAPA_PREDITIVO_AMOSTRAL":
                alternate["wcs_diagnostic"]=result["reason"]
                return alternate
            result["reason"]+="; MapServer Identify: "+str(alternate.get("reason") or "N/D")
        except Exception as fallback_exc:
            result["reason"]+="; MapServer Identify: "+type(fallback_exc).__name__
    return result


def fertility_report_lines(result, fmt):
    """Human-readable raster-derived means, with explicit numerical N/D."""
    lines = ["", "FERTILIDADE DO SOLO — ESTIMATIVAS CARTOGRÁFICAS EMBRAPA 90 m"]
    lines.append("Previsões regionais de mapas digitais, NÃO são análises laboratoriais da propriedade.")
    lines.append("Serviço numérico consultado: " + str(result.get("source") or WCS))
    if result.get("status")=="ERRO_TECNICO":
        lines.append("FALHA TÉCNICA — valores não calculados. Isso não comprova ausência de dados; a consulta deve ser repetida/corrigida.")
        lines.append("Diagnóstico: "+str(result.get("reason") or "erro sem detalhe")[:240])
        lines.append("Não apresentar esta falha como N/D por indisponibilidade científica.")
        return lines
    if result.get("status")=="MAPA_PREDITIVO_AMOSTRAL":
        lines.append("AMOSTRAGEM NUMÉRICA OFICIAL — MapServer Identify; não é média zonal de toda a AOI.")
        lines.append("Pontos amostrados: "+str(result.get("sampled_points"))+
                     "; cobertura areal e erro preditivo: N/D.")
    else:
        lines.append("Estatística: interseção exata pixel × AOI e unidade cartográfica; áreas EPSG:6933.")
        if result.get("status") != "MAPEAMENTO_PREDITIVO_PARCIAL":
            lines.append("Valores numéricos: N/D — " + str(result.get("reason") or "raster oficial indisponível")[:230])
    for area_label, records in (result.get("units") or {}).items():
        lines.append("  ZONA: " + str(area_label))
        for item in records:
            if item.get("mean") is None:
                continue
            value=fmt(item["mean"], 3)
            sd=("N/D" if item.get("spatial_sd") is None else fmt(item["spatial_sd"], 3))
            lines.append("    " + str(item.get("label")) + " [" + str(item.get("depth_cm")) + " cm]: "
                         + value + " " + str(item.get("unit") or "") +
                         "; cobertura " + (fmt(item.get("coverage_pct"),2)+"%" if item.get("coverage_pct") is not None else "N/D") +
                         "; pixels " + str(item.get("valid_pixels") if item.get("valid_pixels") is not None else "N/D") +
                         "; DP espacial descritivo " + sd + ".")
            lines.append("      Layer WCS " + str(item.get("wcs_coverage_id")) +
                         "; SHA256 " + str(item.get("raster_sha256")) +
                         "; incerteza preditiva N/D.")
    lines.append("P, K, Ca, Mg, Al, V%, soma de bases e atributos não disponíveis: N/D sem interpolação.")
    lines.append("DP espacial não equivale a erro do modelo ou IC95%. Licença: " +
                 str(result.get("license") or LICENSE))
    return lines
