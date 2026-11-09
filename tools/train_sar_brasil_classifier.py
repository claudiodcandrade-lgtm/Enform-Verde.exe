# Reproducible training/validation of the SAR Brazil classifier v2 (LEM+ BA + INPE MT + INPE RO).
import json, math, numpy as np, pandas as pd, collections, joblib, sys
sys.path.insert(0,'/tmp/lemfeat')
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import confusion_matrix
exec(open('/tmp/lemfeat/train.py').read().split('def wilson')[0])   # reuses LEM feature/label construction (X, y_lc, y_cr, valid, blocks)
def wilson(k,n,z=1.959963984540054):
    if n==0: return (None,None)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return (max(0,c-h),min(1,c+h))
m=valid&np.array([v is not None for v in y_lc])
XL,yL,gL=X[m],y_lc[m].astype(str),blocks[m]; regL=np.array(['Cerrado-BA (LEM+)']*len(yL))
pts=pd.read_csv('/tmp/amz/points.csv'); F=json.load(open('/tmp/amz/feats.json'))
rows=[(i,F[str(i)]) for i in pts.index if str(i) in F]
XP=np.array([r for _,r in rows],float); idx=[i for i,_ in rows]
okP=np.isfinite(XP).all(1); XP=XP[okP]; idx=np.array(idx)[okP]
yP=pts.label.values[idx].astype(str); gP=np.array([f"{math.floor(x/0.1)}_{math.floor(y/0.1)}" for x,y in zip(pts.lon.values[idx],pts.lat.values[idx])])
regP=np.where(pts.source.values[idx].astype(str).str.contains('Rondonia') if hasattr(pts.source.values,'str') else np.array(['Rondonia' in s for s in pts.source.values[idx]]),'Amazônia-RO (2022)','Mato Grosso (2014-16)')
Xa=np.vstack([XL,XP]); ya=np.concatenate([yL,yP]); ga=np.concatenate([gL,gP]); ra=np.concatenate([regL,regP])
cnt=collections.Counter(ya); keep={k for k,v in cnt.items() if v>=15}; mk=np.array([v in keep for v in ya])
Xa,ya,ga,ra=Xa[mk],ya[mk],ga[mk],ra[mk]
oof=np.empty(len(ya),dtype=object)
for tr,te in GroupKFold(5).split(Xa,ya,ga):
    rf=RandomForestClassifier(n_estimators=400,class_weight='balanced',random_state=20261109,n_jobs=-1).fit(Xa[tr],ya[tr]); oof[te]=rf.predict(Xa[te])
labels=sorted(keep); cm=confusion_matrix(ya,oof.astype(str),labels=labels)
per={}
for i,l in enumerate(labels):
    tp=cm[i,i]; npred=cm[:,i].sum(); ntrue=cm[i,:].sum()
    per[l]={"n_reference":int(ntrue),"n_predicted":int(npred),"precision":tp/npred if npred else None,"precision_wilson95":wilson(tp,npred),"recall":tp/ntrue if ntrue else None,"recall_wilson95":wilson(tp,ntrue)}
byreg={}
for rg in sorted(set(ra)):
    s=ra==rg; c=int((oof[s].astype(str)==ya[s]).sum()); byreg[rg]={"n":int(s.sum()),"accuracy":c/s.sum(),"accuracy_wilson95":wilson(c,int(s.sum()))}
final=RandomForestClassifier(n_estimators=400,class_weight='balanced',random_state=20261109,n_jobs=-1).fit(Xa,ya)
old=joblib.load('/tmp/lemfeat/sar_lemplus_rf_v1.joblib')
joblib.dump({"landcover":final,"crop":old["crop"]},'/tmp/amz/sar_brasil_rf_v2.joblib',compress=3)
oa=np.trace(cm)/cm.sum()
rep={"task":"cobertura","labels":labels,"confusion_matrix":cm.tolist(),"overall_accuracy":oa,"overall_accuracy_wilson95":wilson(int(np.trace(cm)),int(cm.sum())),
     "per_class":per,"by_region":byreg,"n_samples":int(len(ya)),"n_spatial_blocks":int(len(set(ga))),"validation":"GroupKFold(5) por blocos espaciais de 0,1° (fora da amostra espacial)"}
json.dump({"landcover":rep},open('/tmp/amz/report2.json','w'),ensure_ascii=False,indent=1,default=lambda o:int(o) if isinstance(o,np.integer) else float(o))
print("OA=%.3f"%oa,rep["overall_accuracy_wilson95"],"n",len(ya),"blocks",rep["n_spatial_blocks"])
for l,v in per.items(): print("  ",l,v["n_reference"],"P=%.2f"%(v["precision"] or 0),[round(x,2) for x in v["precision_wilson95"] if x is not None],"R=%.2f"%(v["recall"] or 0))
for rg,v in byreg.items(): print("  região",rg,v)
