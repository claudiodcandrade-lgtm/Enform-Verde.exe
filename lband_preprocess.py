import os, re, shutil, subprocess, zipfile, tarfile
from pathlib import Path
import numpy as np

def detect_lband_product(path):
    p=Path(path)
    names=[x.name.lower() for x in (p.rglob("*") if p.is_dir() else [p])]
    joined=" ".join(names)
    if any(x in joined for x in ["nrb","l2.2","l22","gamma0","sigma0"]) and any(x.endswith((".tif",".tiff")) for x in names):
        return "CEOS_ARD_NRB"
    if any(x in joined for x in ["img-hh","img-hv","img-vv","img-vh"]) and ("led-" in joined or "vol-" in joined):
        return "CEOS_L11_SLC"
    if p.suffix.lower() in (".tif",".tiff"):return "GEOTIFF"
    return "UNKNOWN"

def extract_archive(path,out):
    p=Path(path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()==".zip":
        with zipfile.ZipFile(p) as z:z.extractall(out)
    elif p.suffix.lower() in (".tar",".gz",".tgz") or p.name.lower().endswith(".tar.gz"):
        with tarfile.open(p) as t:t.extractall(out)
    else:return p
    return out

def find_geotiffs(root):
    p=Path(root)
    return [str(x) for x in p.rglob("*") if x.suffix.lower() in (".tif",".tiff")]

def calibrate_jaxa_l15_l21(dn,cf=-83.0):
    a=np.asarray(dn,dtype=np.float64)
    with np.errstate(divide="ignore",invalid="ignore"):
        db=10.0*np.log10(np.square(a))+cf
    return db

def calibrate_jaxa_l11(i,q,cf=-83.0):
    i=np.asarray(i,dtype=np.float64);q=np.asarray(q,dtype=np.float64)
    with np.errstate(divide="ignore",invalid="ignore"):
        db=10.0*np.log10(i*i+q*q)+cf
    return db

def preprocess_lband(path,workdir,dem=None):
    """Professional gate: prefer JAXA L2.2 NRB/CEOS-ARD. Raw SLC requires a verified processor."""
    src=extract_archive(path,Path(workdir)/"unpacked")
    kind=detect_lband_product(src)
    if kind in ("CEOS_ARD_NRB","GEOTIFF"):
        ras=find_geotiffs(src) if Path(src).is_dir() else [str(src)]
        return {"status":"ARD_READY","kind":kind,"rasters":ras,"steps":["produto georreferenciado/ARD detectado","sem recalibração destrutiva"],"qa":[]}
    if kind=="CEOS_L11_SLC":
        # JAXA states ScanSAR L1.1 is not supported by SNAP. Do not fake a conversion.
        return {"status":"SLC_PROCESSOR_REQUIRED","kind":kind,"rasters":[],"steps":["CEOS L1.1/SLC detectado"],"qa":["JAXA ScanSAR L1.1 não deve ser enviado ao SNAP; use L2.2 NRB equivalente quando disponível.","Calibração JAXA CF=-83 dB está registrada, mas focusing/geocoding/RTC requer processador validado para este modo."]}
    return {"status":"UNSUPPORTED","kind":kind,"rasters":[],"steps":[],"qa":["Formato L-band não reconhecido."]}
