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
 {"id":"TAPAJOS_PRIMARY_2018","institution":"Afiliações conforme artigo original; não usadas para transferência do dado","region":"FLONA do Tapajós, km 72 e km 117 da BR-163; Pará","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa de terra firme","role":"microlocal_published_plot_summary; secondary_AGB_reference; not_SAR_calibration","year":2018,"citation":"Santos, F.G.; Camargo, P.B.; Oliveira Junior, R.C. Estoque e dinâmica de biomassa arbórea em floresta ombrófila densa na FLONA Tapajós: Amazônia Oriental. Ciência Florestal 28(3):1049–1059.","doi":"10.5902/1980509833388","url":"https://www.scielo.br/j/cflo/a/Y7zf8xHmVZWndCh6xYhJCwn/?lang=pt","year_of_data":2010,"plot_count":12,"site_count":2,"agb_mean_by_site_mg_ha":{"km72":298.11,"km117":248.92},"agb_sd_by_site_mg_ha":{"km72":29.40,"km117":61.78},"transfer_rule":"within_35km_of_km83_only; published_summary_not_pixel_plot_training; two_spatial_clusters; 2010_data"},
 {"id":"ORNL_TG07_KM83","institution":"ORNL DAAC / LBA","region":"Floresta Nacional do Tapajós, km 83; Pará","biome":"Amazônia","physiognomy":"floresta tropical de terra firme","role":"primary_georeferenced_inventory; DBH_ge_35cm; biomass_not_in_source_file","year":2001,"citation":"Tree demography and biomass dynamics in an old-growth tropical forest in eastern Amazonia. ORNL DAAC TG-07.","doi":"10.3334/ORNLDAAC/923","url":"https://daac.ornl.gov/LBA/guides/TG07_FFT_Survey_Km83.html","transfer_rule":"large_tree_subsample_only; apply_documented_allometry; do_not_treat_as_full_stand_agb"},
 {"id":"SFB_IFN_BIOMASS_EQUATIONS_2025","institution":"Serviço Florestal Brasileiro / SNIF / IFN","region":"Brasil; filtros por bioma, vegetação e UF","biome":"*","physiognomy":"equações alométricas por floresta/tipologia","role":"official_national_inventory_derived_data_and_222_allometries; not_SAR_plot_pixel_pairs","year":2025,"citation":"Painel de Biomassa e Carbono — dados abertos e equações do IFN/SFB.","url":"https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono","transfer_rule":"use_as_national_response_reference_and_tree_allometry_catalog; verify plot coordinates and support before SAR calibration"},
 {"id":"JESUS_CAATINGA_SENTINEL1_2023","institution":"Autores e instituições indicados no artigo Journal of Arid Land","region":"Alto Sertão de Sergipe; Caatinga arbórea","biome":"Caatinga","physiognomy":"Caatinga arbórea; estratos/estação fenológica devem corresponder","role":"national_SAR_field_study; 19_plots_30x30m; MLR_R2_RMSE_reported; coefficients_not_yet_verified","year":2023,"citation":"de Jesus, J.B. et al. Estimation of aboveground biomass of arboreal species in the semi-arid region of Brazil using SAR images. Journal of Arid Land 15:695–709.","doi":"10.1007/s40333-023-0017-4","url":"https://link.springer.com/article/10.1007/s40333-023-0017-4","reported_metrics":{"intermediate_period_R2":0.73,"intermediate_period_RMSE_Mg_ha":8.33,"green_period_R2":0.72,"green_period_RMSE_Mg_ha":8.40},"transfer_rule":"published_coefficients/predictor transformations still require full-text review; local Sergipe model; recalibrate/validate separately using IFN/SFB and regional plots before any wider use"},
 {"id":"UFC_LIMA_CAATINGA_SENTINEL_2021","institution":"Universidade Federal do Ceará","region":"Caatinga; local study area in Ceará","biome":"Caatinga","physiognomy":"floresta tropical sazonalmente seca; woody and herbaceous strata separate","role":"masters_dissertation; field_plus_Sentinel1_C_and_Sentinel2; local_regression; coefficients_pending_review","year":2021,"citation":"Lima, M.M.P. Uso de imagens Sentinel para estimativa do estoque de carbono e biomassa acima do solo no bioma Caatinga. Dissertação (Mestrado em Engenharia Agrícola), UFC, 2021.","url":"https://repositorio.ufc.br/handle/riufc/58011","transfer_rule":"retrieve full thesis and exact predictor equations; distinguish woody/herbaceous biomass and seasonal inputs; no national transfer without revalidation"},
 {"id":"SAMPAIO_SILVA_CAATINGA_ALLOMETRY_2005","institution":"UFPE / Universidade do Estado da Bahia","region":"Semiárido brasileiro; dez espécies da Caatinga","biome":"Caatinga","physiognomy":"Caatinga; equação mista exclui Cereus jamacaru; DAP validado até 30 cm","role":"destructive_primary_allometry; 30_individuals_per_species; response_labels_for_field_inventories","year":2005,"citation":"Sampaio, E.V.S.B.; Silva, G.C. Biomass equations for Brazilian semiarid caatinga plants. Acta Botanica Brasilica 19(4).","doi":"10.1590/S0102-33062005000400028","url":"https://www.scielo.br/j/abb/a/H7MJLqBYjHc4Bp63L6pyHsG/?lang=en","verified_equation":{"form":"B_kg = 0.173 × DBH_cm^2.295","species_scope":"nine non-Cactaceae species pooled","dbh_cm_max":30},"transfer_rule":"tree-to-plot allometric response only; not an SAR equation; do not apply outside species/range without testing"},
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
            "RandomForest":RandomForestRegressor(n_estimators=300,min_samples_leaf=2,random_state=random_state,n_jobs=2),
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

def fit_local_powerlaw_calibration(canopy_backscatter_linear, agb_mg_ha, groups, min_plots=20, min_groups=5):
    """Locally calibrate the CASINO-style P-band power law with robust grouped CV.

    This is a transparent local approximation, not the ESA CASINO processor. Input
    must be positive *ground-cancelled canopy backscatter in linear units* paired
    to independent national field plots. Ordinary HH/HV backscatter, dB values,
    unpaired published means, and synthetic plots are rejected by design.
    """
    from scipy.optimize import least_squares
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    x=np.asarray(canopy_backscatter_linear,dtype=float).reshape(-1)
    y=np.asarray(agb_mg_ha,dtype=float).reshape(-1)
    g=np.asarray(groups).astype(str).reshape(-1)
    if len(x)!=len(y) or len(y)!=len(g): raise ValueError("Backscatter, AGB e grupo espacial devem ter o mesmo número de observações.")
    good=np.isfinite(x)&np.isfinite(y)&(x>0)&(y>0)&(g!="")&(g!="None")
    x,y,g=x[good],y[good],g[good]
    if len(y)<min_plots: raise ValueError(f"Calibração P-band recusada: requer pelo menos {min_plots} pares parcela–pixel válidos; encontrou {len(y)}.")
    labels=np.unique(g)
    if len(labels)<min_groups: raise ValueError(f"Calibração P-band recusada: requer ao menos {min_groups} grupos independentes para validação espacial; encontrou {len(labels)}.")
    if len(np.unique(np.round(y,8)))<5 or len(np.unique(np.round(x,12)))<5: raise ValueError("Amostra sem variação suficiente para calibrar a relação P-band–AGB.")

    # Forward model: canopy backscatter = k * AGB**alpha. Robust soft-L1 loss
    # limits leverage from individual plots; bounds enforce positive k/alpha.
    def fit(ix):
        xx,yy=x[ix],y[ix]
        alpha0=.6; k0=float(np.median(xx/np.power(yy,alpha0)))
        scale=max(float(np.median(xx)),1e-9)
        res=least_squares(lambda q:(q[0]*np.power(yy,q[1])-xx)/scale,
                          x0=[max(k0,1e-12),alpha0],bounds=([1e-12,.05],[1e6,3.0]),loss="soft_l1",f_scale=.1,max_nfev=5000)
        if not res.success: raise ValueError("A otimização robusta do modelo P-band não convergiu.")
        return float(res.x[0]),float(res.x[1])
    cv=GroupKFold(n_splits=min(5,len(labels))); pred=np.full(len(y),np.nan,dtype=float)
    for tr,te in cv.split(x,y,g):
        k,alpha=fit(tr); pred[te]=np.power(np.maximum(x[te]/k,0),1/alpha)
    e=pred-y; metrics={"n":int(len(y)),"independent_groups":int(len(labels)),
        "RMSE_Mg_ha":float(np.sqrt(mean_squared_error(y,pred))),
        "MAE_Mg_ha":float(mean_absolute_error(y,pred)),"bias_Mg_ha":float(np.mean(e)),
        "R2":float(r2_score(y,pred)),"validation":"out-of-fold GroupKFold by spatial/site group",
        "out_of_fold_residual_quantiles_Mg_ha":[float(v) for v in np.quantile(e,[.025,.975])]}
    k,alpha=fit(np.arange(len(y)))
    return {"model":"local_robust_P_band_power_law","equation":"AGB = (CB_ground_cancelled_linear / k) ** (1 / alpha)",
        "k":k,"alpha":alpha,"metrics":metrics,"fit_loss":"soft_l1 robust nonlinear least squares",
        "calibration_scope":"the submitted regional/fitofisionomic field sample only; no extrapolation claim",
        "source_model":"CASINO-style P-band power-law family (Soja et al., 2021; DOI 10.1016/j.rse.2020.112153)",
        "operational_limits":["not the official ESA CASINO processor","requires compatible P-band interferometric/ground-cancelled canopy backscatter","requires independent plot–pixel pairs from Brazilian field data","keep Caatinga and humid tropical forest calibrations separate","cross-validation intervals describe sampled groups only; do not imply national transferability"]}
