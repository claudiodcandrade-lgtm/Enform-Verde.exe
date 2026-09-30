"""Scientific calibration, saturation diagnostics and multiscale SAR texture tools.
Enform Verde SAR v3.10.

External inventories/literature are NEVER silently pooled with local plots. They are
used as priors, plausibility envelopes and transferability evidence unless compatible
plot-level observations with coordinates and matching predictors are explicitly supplied.
"""
from __future__ import annotations
import math
import numpy as np

SCIENTIFIC_INVENTORY_REGISTRY = [
 {"id":"EMBRAPA_AP_FLOTA_2012","institution":"Embrapa Amapá / IEF-AP / INPA","region":"Amapá","biome":"Amazônia","physiognomy":"floresta amazônica","role":"external_reference","year":2012,"citation":"Oliveira, L.P.S.; Sotta, E.D.; Higuchi, N. Quantificação da biomassa na Floresta Estadual do Amapá","url":"https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1004540","transfer_rule":"prior_only_unless_plot_level_compatible"},
 {"id":"EMBRAPA_CPAA_WANDELLI_2014","institution":"Embrapa Amazônia Ocidental / INPA","region":"Amazônia Central","biome":"Amazônia","physiognomy":"vegetação secundária","role":"external_reference","year":2014,"citation":"Wandelli, E.V.; Fearnside, P.M. Equações alométricas para vegetações secundárias de diferentes históricos de uso da terra na Amazônia Central","url":"https://www.alice.cnptia.embrapa.br/alice/handle/doc/1008287","transfer_rule":"secondary_forest_only"},
 {"id":"EMBRAPA_CPATU_DUCEY_2009","institution":"Embrapa Amazônia Oriental / colaboradores","region":"Amazônia Oriental","biome":"Amazônia","physiognomy":"floresta secundária 15 anos","role":"external_reference","year":2009,"citation":"Ducey et al. Biomass equations for forest regrowth in the eastern Amazon using randomized branch sampling. Acta Amazonica 39(2):349-360","url":"https://www.alice.cnptia.embrapa.br/alice/handle/doc/658345","transfer_rule":"secondary_forest_only"},
 {"id":"UFLA_UFV_ROMERO_2022","institution":"UFLA / UFV / colaboradores","region":"Acre","biome":"Amazônia","physiognomy":"floresta amazônica; árvores grandes","role":"external_reference","year":2022,"citation":"Romero et al. Aboveground biomass allometric models for large trees in southwestern Amazonia. Trees, Forests and People 9:100317","doi":"10.1016/j.tfp.2022.100317","url":"https://repositorio.ufla.br/handle/1/55978","transfer_rule":"large_tree_allometry_reference"},
 {"id":"UFRA_ALVARES_2025","institution":"UFRA","region":"Pará / Amazônia Oriental","biome":"Amazônia","physiognomy":"floresta secundária em recuperação","role":"external_reference","year":2025,"citation":"Alvares, J.L.S. Predições de carbono em uma floresta secundária em recuperação na Amazônia oriental. UFRA","url":"https://repositorio.ufra.edu.br/jspui/handle/riufra/2761","transfer_rule":"secondary_forest_only"},
 {"id":"EMBRAPA_AC_DIRECT_2024","institution":"Embrapa Acre / colaboradores","region":"Sudoeste da Amazônia","biome":"Amazônia","physiognomy":"floresta tropical","role":"transferability_guard","year":2024,"citation":"To improve estimates of neotropical forest carbon stocks more direct measurements are needed. Forest Ecology and Management 570:122195","doi":"10.1016/j.foreco.2024.122195","url":"https://www.alice.cnptia.embrapa.br/alice/handle/doc/1168974","transfer_rule":"do_not_pool_regions_blindly"},
 {"id":"TROPISAR_PARACOU_2023","institution":"NASA JPL / Politecnico di Milano / ESA collaborators","region":"Guiana Francesa","biome":"Amazônia/Guianas","physiognomy":"floresta tropical densa ~200-500 Mg/ha","role":"sar_method_reference","year":2023,"citation":"Ramachandran et al. Mapping tropical forest aboveground biomass using airborne SAR tomography. Scientific Reports 13:6233","doi":"10.1038/s41598-023-33311-y","url":"https://www.nature.com/articles/s41598-023-33311-y","transfer_rule":"method_prior_not_local_calibration"},
]

# Soft diagnostic ranges: never hard clipping. Saturation is data/structure dependent.
SATURATION_PRIORS = {
 "C":{"soft_mg_ha":70.0,"range_mg_ha":(50.0,100.0),"use":"auxiliary_texture_moisture_disturbance"},
 "L":{"soft_mg_ha":150.0,"range_mg_ha":(100.0,250.0),"use":"structure_texture_polarimetry_with_saturation_test"},
 "P":{"soft_mg_ha":350.0,"range_mg_ha":(250.0,500.0),"use":"priority_dense_forest; tomography_if_valid_stack"},
 "X":{"soft_mg_ha":80.0,"range_mg_ha":(40.0,150.0),"use":"canopy_surface_texture_or_insar_height; not_direct_dense_AGB"},
}

def saturation_audit(agb_mg_ha, bands, empirical_slopes=None):
    """Return warnings/weights; never pretends that literature thresholds are universal."""
    empirical_slopes=empirical_slopes or {}
    out={"agb_mg_ha":float(agb_mg_ha),"bands":{},"warning":[]}
    for b in sorted(set(str(x).upper() for x in bands)):
        p=SATURATION_PRIORS.get(b)
        if not p: continue
        ratio=float(agb_mg_ha)/p["soft_mg_ha"]
        slope=empirical_slopes.get(b)
        state="low_risk" if ratio<0.7 else ("diagnostic_zone" if ratio<1.2 else "high_risk")
        if slope is not None and abs(float(slope))<0.02: state="empirically_saturated"
        weight={"low_risk":1.0,"diagnostic_zone":0.65,"high_risk":0.35,"empirically_saturated":0.1}[state]
        out["bands"][b]={"state":state,"weight":weight,"prior":p,"empirical_slope":slope}
        if state in ("high_risk","empirically_saturated"):
            out["warning"].append(f"Banda {b}: baixa sensibilidade esperada à AGB nesta faixa; não usar isoladamente.")
    return out

def _quantize(a, levels=32):
    a=np.asarray(a,dtype=float); good=np.isfinite(a)
    if not good.any(): return np.zeros(a.shape,dtype=np.uint8),good
    lo,hi=np.nanpercentile(a[good],[2,98])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi<=lo: hi=lo+1.0
    q=np.clip((a-lo)/(hi-lo),0,1)
    return np.floor(q*(levels-1)).astype(np.uint8),good

def glcm_features(array, levels=32, offsets=((0,1),(1,0),(1,1),(1,-1))):
    """Dependency-light GLCM summary for a 2-D SAR window."""
    q,good=_quantize(array,levels); P=np.zeros((levels,levels),dtype=float)
    h,w=q.shape
    for dy,dx in offsets:
        y0=max(0,-dy); y1=min(h,h-dy); x0=max(0,-dx); x1=min(w,w-dx)
        a=q[y0:y1,x0:x1]; b=q[y0+dy:y1+dy,x0+dx:x1+dx]
        m=good[y0:y1,x0:x1]&good[y0+dy:y1+dy,x0+dx:x1+dx]
        if not m.any(): continue
        np.add.at(P,(a[m],b[m]),1); np.add.at(P,(b[m],a[m]),1)
    s=P.sum()
    if s<=0: return {k:float("nan") for k in ("contrast","dissimilarity","homogeneity","asm","energy","entropy","correlation")}
    P/=s; i,j=np.indices(P.shape); d=i-j
    asm=float((P*P).sum()); mi=float((i*P).sum()); mj=float((j*P).sum())
    si=math.sqrt(float((((i-mi)**2)*P).sum())); sj=math.sqrt(float((((j-mj)**2)*P).sum()))
    return {"contrast":float((d*d*P).sum()),"dissimilarity":float((np.abs(d)*P).sum()),
            "homogeneity":float((P/(1+d*d)).sum()),"asm":asm,"energy":math.sqrt(asm),
            "entropy":float(-(P[P>0]*np.log2(P[P>0])).sum()),
            "correlation":float((((i-mi)*(j-mj)*P).sum())/(si*sj)) if si*sj else 0.0}

def multiscale_texture(array, window_sizes=(5,7,11), levels=32):
    """Global diagnostic features at several nominal pixel scales.
    Pixel-to-metre interpretation must be supplied by raster metadata in reports."""
    a=np.asarray(array,dtype=float)
    out={}
    for n in window_sizes:
        # Sample overlapping n*n windows to avoid one scene-wide GLCM dominating.
        vals=[]; step=max(1,n//2)
        for y in range(0,max(1,a.shape[0]-n+1),step):
            for x in range(0,max(1,a.shape[1]-n+1),step):
                z=a[y:y+n,x:x+n]
                if z.shape==(n,n) and np.isfinite(z).mean()>=0.7: vals.append(glcm_features(z,levels))
        if vals:
            for k in vals[0]: out[f"GLCM_{n}_{k}"]=float(np.nanmedian([v[k] for v in vals]))
    return out

def rank_external_evidence(biome, physiognomy, region=""):
    """Rank evidence for applicability. Ranking is not a pooled calibration."""
    b=(biome or "").lower(); p=(physiognomy or "").lower(); r=(region or "").lower()
    rows=[]
    for x in SCIENTIFIC_INVENTORY_REGISTRY:
        score=0
        if x["biome"].lower() in (b,"*") or b in x["biome"].lower(): score+=3
        if p and any(t in x["physiognomy"].lower() for t in p.replace("/"," ").split() if len(t)>4): score+=2
        if r and r in x["region"].lower(): score+=2
        y=dict(x); y["compatibility_score"]=score; rows.append(y)
    return sorted(rows,key=lambda z:(-z["compatibility_score"],-z["year"]))

def fit_local_ensemble(X,y,groups=None,random_state=42):
    """Compare transparent local models. Requires LOCAL matched plot predictors.
    Uses GroupKFold when spatial/group labels are supplied; otherwise shuffled KFold is
    labelled non-spatial and must not be represented as spatial validation.
    """
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
    from sklearn.model_selection import KFold, GroupKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
    X=np.asarray(X,float); y=np.asarray(y,float)
    if X.ndim!=2 or len(y)!=len(X) or len(y)<10: raise ValueError("São necessárias >=10 parcelas locais com preditores SAR coincidentes.")
    models={"Ridge":make_pipeline(StandardScaler(),Ridge(alpha=1.0)),
            "RandomForest":RandomForestRegressor(n_estimators=400,min_samples_leaf=2,random_state=random_state,n_jobs=-1),
            "HistGradientBoosting":HistGradientBoostingRegressor(max_iter=300,l2_regularization=1.0,random_state=random_state)}
    if groups is not None and len(np.unique(groups))>=5:
        cv=GroupKFold(n_splits=min(5,len(np.unique(groups)))); split=list(cv.split(X,y,groups)); validation="spatial/grouped"
    else:
        cv=KFold(n_splits=min(5,max(2,len(y)//5)),shuffle=True,random_state=random_state); split=list(cv.split(X,y)); validation="random_nonspatial"
    metrics={}
    for name,m in models.items():
        pred=cross_val_predict(m,X,y,cv=split,n_jobs=None)
        metrics[name]={"rmse_mg_ha":float(math.sqrt(mean_squared_error(y,pred))),"mae_mg_ha":float(mean_absolute_error(y,pred)),
                       "r2":float(r2_score(y,pred)),"validation":validation}
    best=min(metrics,key=lambda n:metrics[n]["rmse_mg_ha"]); models[best].fit(X,y)
    return {"model":models[best],"model_name":best,"metrics":metrics,"validation":validation,
            "external_inventory_policy":"priors_and_validation_only_not_pooled_without_compatible_plot_data"}
