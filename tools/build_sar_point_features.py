# Reproducible point-feature extraction (INPE sits/sitsdata labels: MT 2014-16, Rondonia 2022).
"""Monthly Sentinel-1 RTC features (VV, VH dB; 80 m; 3x3 mean) at labelled points.
Groups points by 1-degree cell and agricultural year; one decimated read per scene/cell."""
import sys, json, math, time, collections
sys.path.insert(0,'/home/claude/repo')
import tls_setup; tls_setup.configure()
import numpy as np, pandas as pd, requests, rasterio
from concurrent.futures import ThreadPoolExecutor
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.warp import transform as wtransform
from sentinel1_mpc import get_runtime_sas_token, _signed_href
pts=pd.read_csv(sys.argv[1]); out=sys.argv[2]
F=8
TOK={'t':get_runtime_sas_token(),'at':time.time()}
def tok():
    if time.time()-TOK['at']>1800: TOK['t']=get_runtime_sas_token(); TOK['at']=time.time()
    return TOK['t']
def months_for(y0): return [(y0,m) for m in (10,11,12)]+[(y0+1,m) for m in range(1,10)]
pts['cell']=[f"{math.floor(x)}_{math.floor(y)}" for x,y in zip(pts.lon,pts.lat)]
groups=list(pts.groupby(['cell','season_start']))
res={}
def job(key_df):
    (cell,y0),df=key_df
    bb=[df.lon.min()-0.01,df.lat.min()-0.01,df.lon.max()+0.01,df.lat.max()+0.01]
    try:
        r=requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search",json={"collections":["sentinel-1-rtc"],"bbox":bb,"datetime":f"{y0}-10-01/{y0+1}-09-30","limit":500},timeout=120).json()
    except Exception as e: return cell,y0,{}, f"stac {e}"
    fs=[f for f in r.get('features',[]) if {'vv','vh'}<=set(f['assets'])]
    if not fs: return cell,y0,{}, "no scenes"
    orb=collections.Counter(f['properties']['sat:relative_orbit'] for f in fs).most_common(1)[0][0]
    fs=[f for f in fs if f['properties']['sat:relative_orbit']==orb]
    S=collections.defaultdict(lambda: np.zeros(len(df))); C=collections.defaultdict(lambda: np.zeros(len(df)))
    for f in fs:
        ym=tuple(int(x) for x in f['properties']['datetime'][:7].split('-'))
        for pol in ('vv','vh'):
            try:
                with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",GDAL_HTTP_MAX_RETRY="4",GDAL_HTTP_RETRY_DELAY="2",**tls_setup.gdal_env()):
                    with rasterio.open(_signed_href(f['assets'][pol]['href'],tok())) as src:
                        xs,ys=wtransform('EPSG:4326',src.crs,df.lon.tolist(),df.lat.tolist())
                        l,b,rr,t=src.bounds; inside=[(l<x<rr and b<y<t) for x,y in zip(xs,ys)]
                        if not any(inside): continue
                        X=[x for x,i in zip(xs,inside) if i]; Y=[y for y,i in zip(ys,inside) if i]
                        w=from_bounds(min(X)-300,min(Y)-300,max(X)+300,max(Y)+300,transform=src.transform).round_offsets().round_lengths()
                        w=w.intersection(rasterio.windows.Window(0,0,src.width,src.height))
                        oh,ow=max(3,int(w.height//F)),max(3,int(w.width//F))
                        a=src.read(1,window=w,out_shape=(oh,ow),resampling=Resampling.average).astype(float)
                        tr=src.window_transform(w)*rasterio.Affine.scale(w.width/ow,w.height/oh)
                        for k,(x,y,i) in enumerate(zip(xs,ys,inside)):
                            if not i: continue
                            c,rw=~tr*(x,y); c,rw=int(c),int(rw)
                            win=a[max(0,rw-1):rw+2,max(0,c-1):c+2]; v=win[np.isfinite(win)&(win>0)]
                            if v.size: S[(ym,pol)][k]+=v.mean(); C[(ym,pol)][k]+=1
            except Exception: continue
    feats={}
    for k_,idx in enumerate(df.index):
        row=[]
        for ym in months_for(y0):
            vv=S[(ym,'vv')][k_]/C[(ym,'vv')][k_] if C[(ym,'vv')][k_] else np.nan
            vh=S[(ym,'vh')][k_]/C[(ym,'vh')][k_] if C[(ym,'vh')][k_] else np.nan
            row+=[10*np.log10(vv) if vv>0 else np.nan,10*np.log10(vh) if vh>0 else np.nan]
            row.append(row[-1]-row[-2])
        feats[int(idx)]=row
    return cell,y0,feats,f"ok orbit {orb} scenes {len(fs)}"
log=open(out+'.log','w')
with ThreadPoolExecutor(8) as ex:
    for cell,y0,feats,msg in ex.map(job,groups):
        res.update(feats); log.write(f"{cell} {y0} {len(feats)} {msg}\n"); log.flush()
        json.dump(res,open(out,'w'))
open(out+'.DONE','w').write('ok')
