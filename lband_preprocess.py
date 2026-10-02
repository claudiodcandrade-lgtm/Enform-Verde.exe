import os, re, shutil, subprocess, zipfile, tarfile
from pathlib import Path, PurePosixPath
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

def _safe_target(root,name):
    # Archive member paths use POSIX separators even on Windows. Reject absolute,
    # drive-qualified and parent traversal paths before creating any file.
    raw=str(name).replace("\\","/"); parts=PurePosixPath(raw).parts
    if not raw or raw.startswith("/") or any(p in ("..","") for p in parts):
        raise ValueError(f"Unsafe archive member path: {name!r}")
    target=(Path(root)/Path(*parts)).resolve(); base=Path(root).resolve()
    if target!=base and base not in target.parents:raise ValueError(f"Archive member escapes target: {name!r}")
    return target

def _copy_stream(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("wb") as out:shutil.copyfileobj(src,out,length=1024*1024)

def extract_archive(path,out):
    p=Path(path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()==".zip":
        total=0
        with zipfile.ZipFile(p) as z:
            members=z.infolist()
            if len(members)>100000:raise ValueError("Archive contém número excessivo de arquivos.")
            for info in members:
                target=_safe_target(out,info.filename)
                if info.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                total+=info.file_size
                if total>8*1024**3:raise ValueError("Conteúdo expandido do archive excede 8 GiB.")
                with z.open(info) as src:_copy_stream(src,target)
    elif p.suffix.lower() in (".tar",".gz",".tgz") or p.name.lower().endswith(".tar.gz"):
        total=0
        with tarfile.open(p) as t:
            members=t.getmembers()
            if len(members)>100000:raise ValueError("Archive contém número excessivo de arquivos.")
            for info in members:
                if info.issym() or info.islnk() or not (info.isfile() or info.isdir()):
                    raise ValueError("Archive contém links ou tipos de arquivo não permitidos.")
                target=_safe_target(out,info.name)
                if info.isdir():target.mkdir(parents=True,exist_ok=True);continue
                total+=info.size
                if total>8*1024**3:raise ValueError("Conteúdo expandido do archive excede 8 GiB.")
                src=t.extractfile(info)
                if src is None:raise ValueError(f"Não foi possível ler membro {info.name!r}.")
                with src:_copy_stream(src,target)
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
    """Prefer JAXA L2.2 NRB/CEOS-ARD. Raw SLC requires a verified processor."""
    src=extract_archive(path,Path(workdir)/"unpacked")
    kind=detect_lband_product(src)
    if kind in ("CEOS_ARD_NRB","GEOTIFF"):
        ras=find_geotiffs(src) if Path(src).is_dir() else [str(src)]
        return {"status":"ARD_READY","kind":kind,"rasters":ras,"steps":["produto georreferenciado/ARD detectado","sem recalibração destrutiva"],"qa":[]}
    if kind=="CEOS_L11_SLC":
        names=" ".join(x.name.lower() for x in Path(src).rglob("*"))
        scansar=any(x in names for x in ["w1","w2","w3","scansar"])
        gpt=shutil.which("gpt")
        if scansar:
            return {"status":"SLC_SCAN_ARD_REQUIRED","kind":kind,"rasters":[],"steps":["ScanSAR L1.1 detectado","buscar L2.2 CEOS-ARD/NRB equivalente"],"qa":["JAXA declara ScanSAR L1.1 incompatível com SNAP; a rota profissional exige L2.2/NRB ou processador JAXA validado."]}
        if not gpt:
            return {"status":"SLC_SNAP_REQUIRED","kind":kind,"rasters":[],"steps":["Stripmap/Spotlight L1.1 detectado"],"qa":["Instale ESA SNAP/S1TBX para calibração e Range-Doppler Terrain Correction automatizados."]}
        graph=Path(workdir)/"alos2_l11_to_tc.xml"
        out=Path(workdir)/"alos2_tc.dim"
        graph.write_text("""<graph id="ALOS2_L11_PRO"><version>1.0</version><node id="Read"><operator>Read</operator><sources/><parameters><file>${input}</file></parameters></node><node id="Calibration"><operator>Calibration</operator><sources><sourceProduct refid="Read"/></sources><parameters><outputSigmaBand>true</outputSigmaBand></parameters></node><node id="TC"><operator>Terrain-Correction</operator><sources><sourceProduct refid="Calibration"/></sources><parameters><demName>SRTM 1Sec HGT</demName><pixelSpacingInMeter>25.0</pixelSpacingInMeter><mapProjection>AUTO:42001</mapProjection></parameters></node><node id="Write"><operator>Write</operator><sources><sourceProduct refid="TC"/></sources><parameters><file>${output}</file><formatName>BEAM-DIMAP</formatName></parameters></node></graph>""",encoding="utf-8")
        volume=next((x for x in Path(src).rglob("*") if x.name.lower().startswith("vol-")),None)
        if volume is None:return {"status":"SLC_METADATA_MISSING","kind":kind,"rasters":[],"steps":[],"qa":["Arquivo VOL CEOS não encontrado."]}
        cp=subprocess.run([gpt,str(graph),"-Pinput="+str(volume),"-Poutput="+str(out)],capture_output=True,text=True)
        if cp.returncode!=0:return {"status":"SLC_PREPROCESS_FAILED","kind":kind,"rasters":[],"steps":["SNAP Calibration","Range-Doppler Terrain Correction"],"qa":[cp.stderr[-1500:]]}
        ras=find_geotiffs(workdir)
        return {"status":"SLC_PREPROCESSED","kind":kind,"rasters":ras,"steps":["SNAP Calibration","Range-Doppler Terrain Correction"],"qa":[]}
    return {"status":"UNSUPPORTED","kind":kind,"rasters":[],"steps":[],"qa":["Formato L-band não reconhecido."]}
