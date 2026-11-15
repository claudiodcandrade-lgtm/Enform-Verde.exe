# Reproducible training/validation (spatial 0.1-degree blocks) of the SAR LEM+ classifier.
import json, math, numpy as np, geopandas as gpd, collections
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import confusion_matrix
g=gpd.read_file('/tmp/lemp/LEM_dataset.shp')
MONTHS=['2019-10','2019-11','2019-12','2020-01','2020-02','2020-03','2020-04','2020-05','2020-06','2020-07','2020-08','2020-09']
def feats(path):
    d=np.load(path); X=[]
    for m in MONTHS:
        vv=d[f'{m}_vv_S']/np.where(d[f'{m}_vv_C']>0,d[f'{m}_vv_C'],np.nan); vh=d[f'{m}_vh_S']/np.where(d[f'{m}_vh_C']>0,d[f'{m}_vh_C'],np.nan)
        X+= [10*np.log10(vv),10*np.log10(vh),10*np.log10(vh)-10*np.log10(vv)]
    return np.column_stack(X)
A=feats('/tmp/lemfeat/feat.npz'); B=feats('/tmp/lemfeat/feat126.npz')
okA=np.isfinite(A).all(1); okB=np.isfinite(B).all(1)
X=np.where(okA[:,None],A,B); orbit=np.where(okA,24,np.where(okB,126,0))
valid=okA|okB
cols=[c for c in g.columns if '_20' in c]
CROPS={'Soybean':'Soja','Corn':'Milho','Cotton':'Algodão','Coffee':'Café','Sorghum':'Sorgo','Beans':'Feijão','Millet':'Milheto'}
def lc(row):
    vals=[str(row[c]) for c in cols if str(row[c])!='nan']
    if not vals or 'Conversion area' in vals or 'Not identified' in vals: return None
    s=set(vals)
    if s=={'Cerrado'}: return 'Vegetação nativa (Cerrado)'
    if s & set(CROPS) or 'Hay' in s or 'Crotalaria' in s: return 'Cultivo agrícola'
    if s <= {'Pasture','Brachiaria','Uncultivated soil'} and ('Pasture' in s or 'Brachiaria' in s): return 'Pastagem'
    if any(v.startswith('Eucalyptus') for v in s): return 'Silvicultura'
    return None
def crop(row):
    for c in ('Jan_2020','Feb_2020','Dec_2019','Mar_2020'):
        v=str(row[c])
        if v in CROPS: return CROPS[v]
    v=[str(row[c]) for c in cols]
    if 'Coffee' in v: return 'Café'
    return None
y_lc=np.array([lc(r) for _,r in g.iterrows()],dtype=object); y_cr=np.array([crop(r) for _,r in g.iterrows()],dtype=object)
cent=g.to_crs(4326).geometry.centroid
blocks=np.array([f"{math.floor(p.x/0.1)}_{math.floor(p.y/0.1)}" for p in cent])
def wilson(k,n,z=1.959963984540054):
    if n==0: return (None,None)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return (max(0,c-h),min(1,c+h))
def run(y,name,min_n=15):
    m=valid&np.array([v is not None for v in y])
    cnt=collections.Counter(y[m]); keep={k for k,v in cnt.items() if v>=min_n}
    m&=np.array([v in keep for v in y])
    Xm,ym,gm=X[m],y[m].astype(str),blocks[m]
    oof=np.empty(len(ym),dtype=object)
    for tr,te in GroupKFold(5).split(Xm,ym,gm):
        rf=RandomForestClassifier(n_estimators=300,class_weight='balanced',random_state=20261108,n_jobs=-1).fit(Xm[tr],ym[tr])
        oof[te]=rf.predict(Xm[te])
    labels=sorted(keep); cm=confusion_matrix(ym,oof.astype(str),labels=labels)
    per={}
    for i,l in enumerate(labels):
        tp=cm[i,i]; npred=cm[:,i].sum(); ntrue=cm[i,:].sum()
        per[l]={"n_reference":int(ntrue),"n_predicted":int(npred),"precision":tp/npred if npred else None,
                "precision_wilson95":wilson(tp,npred),"recall":tp/ntrue if ntrue else None,"recall_wilson95":wilson(tp,ntrue)}
    oa=np.trace(cm)/cm.sum()
    final=RandomForestClassifier(n_estimators=300,class_weight='balanced',random_state=20261108,n_jobs=-1).fit(Xm,ym)
    return final,{"task":name,"labels":labels,"confusion_matrix":cm.tolist(),"overall_accuracy":oa,
                  "overall_accuracy_wilson95":wilson(int(np.trace(cm)),int(cm.sum())),"per_class":per,
                  "n_fields":int(len(ym)),"n_spatial_blocks":int(len(set(gm))),
                  "validation":"GroupKFold(5) por blocos espaciais de 0,1° (fora da amostra espacial)"}
import joblib
mlc,rlc=run(y_lc,'cobertura'); mcr,rcr=run(y_cr,'cultura')
joblib.dump({"landcover":mlc,"crop":mcr},'/tmp/lemfeat/sar_lemplus_rf_v1.joblib',compress=3)
json.dump({"landcover":rlc,"crop":rcr,"n_valid_fields":int(valid.sum()),"orbit_counts":collections.Counter(orbit.tolist())},open('/tmp/lemfeat/report.json','w'),ensure_ascii=False,indent=1,default=lambda o:int(o) if isinstance(o,np.integer) else float(o))
for r in (rlc,rcr):
    print(r["task"],"OA=%.3f"%r["overall_accuracy"],r["overall_accuracy_wilson95"],"n",r["n_fields"],"blocks",r["n_spatial_blocks"])
    for l,v in r["per_class"].items(): print("   ",l,v["n_reference"],"P=%.2f"%(v["precision"] or 0),[round(x,2) for x in v["precision_wilson95"] if x is not None],"R=%.2f"%(v["recall"] or 0))
