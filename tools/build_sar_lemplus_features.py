# Reproducible feature extraction for LEM+ (CC BY 4.0, doi:10.17632/vz6d7tw87f.1); run once per orbit (24 and 126).
import sys, json, time, collections
sys.path.insert(0,'/home/claude/repo')
import tls_setup; tls_setup.configure()
import numpy as np, geopandas as gpd, requests, rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from sentinel1_mpc import get_runtime_sas_token, _signed_href
F=8  # 10 m -> 80 m
g=gpd.read_file('/tmp/lemp/LEM_dataset.shp')
b=list(g.total_bounds)
r=requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search",json={"collections":["sentinel-1-rtc"],"bbox":b,"datetime":"2019-10-01/2020-09-30","limit":250},timeout=90).json()
scenes=[f for f in r["features"] if f["properties"]["sat:relative_orbit"]==24]
n=len(g); S=collections.defaultdict(lambda: np.zeros(n)); C=collections.defaultdict(lambda: np.zeros(n))
tok=get_runtime_sas_token(); t0=time.time(); log=open('/tmp/lemfeat/log.txt','a')
for i,f in enumerate(sorted(scenes,key=lambda x:x["properties"]["datetime"])):
    month=f["properties"]["datetime"][:7]
    try:
        for pol in ("vv","vh"):
            if time.time()-t0>2400: tok=get_runtime_sas_token(); t0=time.time()
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",GDAL_HTTP_MAX_RETRY="4",GDAL_HTTP_RETRY_DELAY="2",**tls_setup.gdal_env()):
                with rasterio.open(_signed_href(f["assets"][pol]["href"],tok)) as src:
                    gg=g.to_crs(src.crs)
                    l,bt,rr,tp=src.bounds
                    sub=gg.cx[l:rr,bt:tp]
                    if sub.empty: break
                    w=from_bounds(*sub.total_bounds,transform=src.transform).round_offsets().round_lengths()
                    w=w.intersection(rasterio.windows.Window(0,0,src.width,src.height))
                    oh,ow=max(1,int(w.height//F)),max(1,int(w.width//F))
                    a=src.read(1,window=w,out_shape=(oh,ow),resampling=Resampling.average).astype('float64')
                    tr=src.window_transform(w)*rasterio.Affine.scale(w.width/ow,w.height/oh)
                    ids=rasterize(((geom,int(idx)+1) for idx,geom in zip(sub.index,sub.geometry)),out_shape=a.shape,transform=tr,fill=0,dtype='int32')
                    ok=(ids>0)&np.isfinite(a)&(a>0)
                    s=np.bincount(ids[ok]-1,weights=a[ok],minlength=n); c=np.bincount(ids[ok]-1,minlength=n)
                    S[(month,pol)]+=s; C[(month,pol)]+=c
        log.write(f"{i} {f['id']} ok\n"); log.flush()
    except Exception as e:
        log.write(f"{i} {f['id']} ERR {type(e).__name__} {str(e)[:150]}\n"); log.flush()
    if i%5==0:
        np.savez('/tmp/lemfeat/feat.npz',**{f"{k[0]}_{k[1]}_S":v for k,v in S.items()},**{f"{k[0]}_{k[1]}_C":v for k,v in C.items()})
np.savez('/tmp/lemfeat/feat.npz',**{f"{k[0]}_{k[1]}_S":v for k,v in S.items()},**{f"{k[0]}_{k[1]}_C":v for k,v in C.items()})
open('/tmp/lemfeat/DONE','w').write(json.dumps({"scenes":len(scenes),"ids":[f["id"] for f in scenes]}))
