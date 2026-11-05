"""Fetch Embrapa 90 m SOC *published* 95% marginal prediction-bound rasters.

Do not invent uncertainty from spatial variation. Published marginal bounds
for five depths do NOT establish a calibrated joint 0–100 cm 95% interval.
"""
from __future__ import annotations
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

DEPTHS = ("0-5", "5-15", "15-30", "30-60", "60-100")
SOURCE = "https://geoinfo.dados.embrapa.br/geoserver/ows"


def _tokens(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def discover_official_bounds(data):
    """Only WCS-advertised, unambiguous depth-specific prediction bounds.

    The provider can use alternative identifier names; unknown products are N/D.
    """
    root = ET.fromstring(data)
    candidates={}
    for el in root.iter():
        if el.tag.split("}")[-1] != "CoverageSummary": continue
        fields={}
        for sub in el:
            field=sub.tag.split("}")[-1]
            if field in ("CoverageId","Identifier","Title","Abstract"):
                fields.setdefault(field,[]).append(sub.text or "")
        ident=(fields.get("CoverageId") or fields.get("Identifier") or [""])[0].strip()
        title=" ".join(fields.get("Title",[])+fields.get("Abstract",[]))
        text=_tokens(ident+" "+title)
        if not ident or not (("90m" in text.replace(" ","")) or ("90 m" in text)):continue
        if not (("stock" in text) or ("estoque" in text)):continue
        if not (("carbon" in text) or ("carbono" in text)):continue
        if not (("predict" in text) or ("predic" in text) or ("uncert" in text)
                or ("interval" in text) or ("lower" in text) or ("upper" in text)
                or ("limit" in text)): continue
        side=None
        lower=("lower","inferior","p025","q025","lwr","li95","low")
        upper=("upper","superior","p975","q975","upr","ls95","high")
        w=set(text.split())
        if any(v in w for v in lower):side="lower"
        if any(v in w for v in upper):
            if side:continue
            side="upper"
        if not side:continue
        for d in DEPTHS:
            a,b=d.split("-")
            if re.search(r"(?<!\d)0*"+a+r"\s+(?:to\s+|a\s+)?0*"+b+r"(?:\s*cm)?\b",text):
                key=(side,d)
                if key in candidates and candidates[key] != ident:candidates[key]=None
                else:candidates.setdefault(key,ident)
    return {k:v for k,v in candidates.items() if v is not None}


def _sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()


def fetch_official_bounds(geom_4326, *, session=None, cache_root=None, max_tiles=8):
    """Return 5 lower and 5 upper official raw rasters, or explicit failure.

    There is no guess-based fallback or interpolation from published model RMSE.
    """
    import requests
    import rasterio
    from rasterio.merge import merge
    from pronasolos_wcs import (_window_bounds,_tiles,coverage_url,validate_tile,
                                 _download,NODATA)
    session=session or requests.Session()
    response=session.get(SOURCE, params={"service":"WCS","version":"2.0.1",
                     "request":"GetCapabilities"},timeout=(10,30))
    response.raise_for_status()
    coverage_ids=discover_official_bounds(response.content)
    expected={(s,d) for s in ("lower","upper") for d in DEPTHS}
    missing=expected-set(coverage_ids)
    if missing:
        raise ValueError("camadas oficiais de limites de predição incompletas no WCS: "+
                         ", ".join(sorted(f"{s}:{d}" for s,d in missing)))
    bounds=_window_bounds(geom_4326)
    tiles=list(_tiles(bounds))
    if len(tiles)>max_tiles:
        raise ValueError("AOI muito extensa para download automático das bandas de incerteza")
    key=hashlib.sha256(json.dumps([round(v,10) for v in bounds]).encode()).hexdigest()[:20]
    root=Path(cache_root or Path.home()/".enform_verde"/"soc_uncertainty_90m")/key
    root.mkdir(parents=True,exist_ok=True)
    paths={"lower":{},"upper":{}}
    provenance={"source":SOURCE,"meaning":"limites marginais de predição declarados pela Embrapa",
                "layers":{}}
    for side in ("lower","upper"):
        for lid,d in enumerate(DEPTHS,start=2):
            cov=coverage_ids[(side,d)]
            dest=root/f"{side}_{d.replace('-','_')}.tif"
            reuse=False
            manifest=dest.with_suffix(".provenance.json")
            if dest.is_file() and manifest.is_file():
                try:
                    meta=json.loads(manifest.read_text(encoding="utf-8"))
                    validate_tile(dest)
                    reuse=(meta.get("coverage_id")==cov and
                           meta.get("source")==SOURCE and
                           meta.get("sha256")==_sha256(dest))
                except (OSError,TypeError,ValueError,json.JSONDecodeError):
                    reuse=False
            if not reuse:
                dest.unlink(missing_ok=True)
                manifest.unlink(missing_ok=True)
                tpaths=[]
                for i,tile in enumerate(tiles):
                    p=root/f"{side}_{lid}_tile{i}.tif"
                    _download(coverage_url(cov,tile),p,session,(10,120),attempts=2)
                    validate_tile(p)
                    tpaths.append(p)
                if len(tpaths)==1:tpaths[0].replace(dest)
                else:
                    datasets=[rasterio.open(p) for p in tpaths]
                    try:
                        arr,transform=merge(datasets,nodata=NODATA)
                        profile=datasets[0].profile.copy()
                    finally:
                        for ds in datasets:ds.close()
                    profile.update(transform=transform,height=arr.shape[1],
                        width=arr.shape[2],nodata=NODATA,compress="deflate")
                    with rasterio.open(dest,"w",**profile) as ds:ds.write(arr)
                    for p in tpaths:p.unlink(missing_ok=True)
                manifest.write_text(json.dumps({
                    "coverage_id":cov,"source":SOURCE,
                    "sha256":_sha256(dest),
                    "interval_meaning":"published marginal predictive bound"
                },ensure_ascii=False,indent=2),encoding="utf-8")
            paths[side][lid]=dest
            provenance["layers"][f"{side}_{d}"]={
                "coverage_id":cov,"sha256":_sha256(dest),"path":str(dest)}
    return {"paths":paths,"provenance":provenance}
