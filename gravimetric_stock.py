"""Gravimetric litter and dead-wood stock estimators with explicit uncertainty.

All estimates are per plot first. Inferential uncertainty is calculated across
independent sampling units (preferably IFN conglomerates or inventory plots),
not across subsamples within a plot. Missing replication returns no CI rather
than a fabricated margin of error.
"""
from __future__ import annotations

import math
import numpy as np

def _mean_ci(values, confidence=0.95):
    x=np.asarray(list(values),dtype=float)
    x=x[np.isfinite(x)]
    if len(x)<2:
        return {"n_independent_units":int(len(x)),"mean":float(x.mean()) if len(x) else None,
                "se":None,"margin_error":None,"ci":None,
                "status":"SEM_IC: menos de duas unidades amostrais independentes"}
    n=len(x); mean=float(x.mean()); se=float(x.std(ddof=1)/math.sqrt(n))
    try:
        from scipy.stats import t
        critical=float(t.ppf((1+confidence)/2,n-1)); method="t_student"
    except Exception:
        critical=1.959963984540054; method="normal_approximation_fallback"
    margin=critical*se
    return {"n_independent_units":n,"mean":mean,"se":se,"margin_error":margin,
            "ci":[mean-margin,mean+margin],"confidence":float(confidence),
            "critical_method":method,"status":"IC calculado entre unidades independentes"}

def summarize_plot_stocks(plot_stocks_mg_ha, cluster_ids=None, confidence=0.95):
    """Summarize plot stocks; when IDs are supplied, first collapse subsamples to clusters."""
    vals=np.asarray(list(plot_stocks_mg_ha),dtype=float)
    if cluster_ids is None:
        return _mean_ci(vals,confidence)
    ids=np.asarray(list(cluster_ids),dtype=object)
    if len(ids)!=len(vals):
        raise ValueError("cluster_ids deve ter o mesmo comprimento de plot_stocks_mg_ha.")
    cluster_means=[]
    for key in dict.fromkeys(ids.tolist()):
        z=vals[ids==key]; z=z[np.isfinite(z)]
        if len(z):cluster_means.append(float(z.mean()))
    result=_mean_ci(cluster_means,confidence)
    result["subsamples_collapsed"]=True
    result["cluster_means_mg_ha"]=cluster_means
    return result

def litter_stock_from_quadrats(dry_mass_g, sampled_area_m2, cluster_ids=None, confidence=0.95):
    """Convert dry litter mass in g from known-area quadrats to Mg dry matter/ha."""
    masses=np.asarray(list(dry_mass_g),dtype=float)
    areas=np.asarray(list(sampled_area_m2),dtype=float)
    if len(masses)!=len(areas) or len(masses)==0:
        raise ValueError("Informe massa seca e área para cada quadrado.")
    if np.any(~np.isfinite(masses)) or np.any(masses<0) or np.any(~np.isfinite(areas)) or np.any(areas<=0):
        raise ValueError("Massa deve ser >=0 e área amostrada deve ser >0.")
    # g/m² × 0.01 = Mg/ha
    plots=masses/areas*0.01
    summary=summarize_plot_stocks(plots,cluster_ids,confidence)
    summary.update({"plot_stocks_mg_ha":plots.tolist(),"unit":"Mg matéria seca/ha",
                    "conversion":"(massa seca g / área m²) × 0,01"})
    return summary

def litter_depth_mass_calibration(depth_cm, dry_mass_g, sampled_area_m2, target_depth_cm,
                                  confidence=0.95):
    """OLS calibration of litter depth against gravimetric dry stock; report mean and prediction intervals."""
    x=np.asarray(list(depth_cm),dtype=float); mass=np.asarray(list(dry_mass_g),dtype=float)
    area=np.asarray(list(sampled_area_m2),dtype=float)
    if not(len(x)==len(mass)==len(area)) or len(x)<3:
        raise ValueError("Calibração exige pelo menos três amostras pareadas de profundidade, massa e área.")
    if np.any(~np.isfinite(x)) or np.any(x<0) or np.any(~np.isfinite(mass)) or np.any(mass<0) or np.any(~np.isfinite(area)) or np.any(area<=0):
        raise ValueError("Calibração contém valores inválidos.")
    y=mass/area*0.01
    X=np.column_stack((np.ones(len(x)),x)); beta=np.linalg.lstsq(X,y,rcond=None)[0]
    residual=y-X@beta; df=len(y)-2
    if df<=0:raise ValueError("Graus de liberdade insuficientes para a calibração.")
    mse=float(residual@residual/df); xtx_inv=np.linalg.inv(X.T@X)
    x0=np.array([1.0,float(target_depth_cm)])
    pred=float(x0@beta); se_mean=math.sqrt(max(0.0,mse*float(x0@xtx_inv@x0)))
    se_pred=math.sqrt(max(0.0,mse+se_mean**2))
    try:
        from scipy.stats import t
        critical=float(t.ppf((1+confidence)/2,df)); method="t_student"
    except Exception:
        critical=1.959963984540054; method="normal_approximation_fallback"
    ss=float(((y-y.mean())**2).sum()); r2=1.0-float(residual@residual)/ss if ss>0 else None
    return {"intercept_mg_ha":float(beta[0]),"slope_mg_ha_per_cm":float(beta[1]),
            "target_depth_cm":float(target_depth_cm),"predicted_mean_mg_ha":max(0.0,pred),
            "mean_ci95":[max(0.0,pred-critical*se_mean),max(0.0,pred+critical*se_mean)],
            "individual_prediction_interval95":[max(0.0,pred-critical*se_pred),max(0.0,pred+critical*se_pred)],
            "rmse_mg_ha":math.sqrt(mse),"r2":r2,"n_pairs":int(len(y)),
            "degrees_freedom":int(df),"critical_method":method,
            "uncertainty_note":"IC da média e intervalo de predição individual são distintos; aplicar somente à classe, estação e protocolo amostrados."}

def necromass_line_intersect_stock(diameters_cm, density_kg_m3, transect_length_m,
                                  cluster_ids=None, confidence=0.95):
    """Estimate fallen wood dry stock from line-intersect diameters and decay-class density.

    Per transect: Mg/ha = (pi² / (8 L)) * sum(d_m² * rho_kg_m3) * 10.
    """
    ds=list(diameters_cm); rhos=list(density_kg_m3)
    if len(ds)!=len(rhos):raise ValueError("Cada peça precisa de diâmetro e densidade.")
    if not ds:raise ValueError("Informe os registros de peças interceptadas por transecto.")
    if len(transect_length_m)!=len(ds):raise ValueError("transect_length_m deve indicar o comprimento percorrido para cada peça.")
    stock=[]
    for d,rho,length in zip(ds,rhos,transect_length_m):
        d=float(d); rho=float(rho); length=float(length)
        if not all(math.isfinite(v) for v in (d,rho,length)) or d<0 or rho<=0 or length<=0:
            raise ValueError("Diâmetro >=0, densidade >0 e comprimento de transecto >0 são obrigatórios.")
        # Convert each observation to a per-ha transect contribution; aggregate by independent cluster below.
        stock.append((math.pi**2/(8*length))*((d/100.0)**2)*rho*10.0)
    summary=summarize_plot_stocks(stock,cluster_ids,confidence)
    summary.update({"transect_contributions_mg_ha":stock,"unit":"Mg matéria seca/ha",
                    "formula":"(π²/(8L)) × Σ(d_m² × ρ_kg/m³) × 10",
                    "density_requirement":"ρ seca medida/validada por espécie ou estado de decomposição; não substituir por densidade de madeira viva sem justificativa"})
    return summary
