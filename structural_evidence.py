"""Structural evidence library for Brazilian forest inventories.

Rules:
- Primary plot/tree data stay at observation level and may support plot-SAR pairing.
- Published aggregate results remain study-level evidence; they are NEVER expanded
  into synthetic plots.
- Comparable study-level means may be combined by random-effects meta-analysis.
- CI/SE/SD are transformed transparently. IQR-to-SD is an approximation and is
  explicitly flagged. Min/max ranges are envelopes only and receive no inverse-
  variance weight.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Iterable

SUPPORTED_BIOMES=("Amazônia","Cerrado","Mata Atlântica","Caatinga")

@dataclass(frozen=True)
class StructuralEvidence:
    source_id: str
    institution: str
    biome: str
    physiognomy: str
    region: str
    metric: str
    unit: str
    center_type: str = "mean"
    mean: float | None = None
    sd: float | None = None
    se: float | None = None
    ci95_low: float | None = None
    ci95_high: float | None = None
    iqr_low: float | None = None
    iqr_high: float | None = None
    range_low: float | None = None
    range_high: float | None = None
    n_plots: int | None = None
    n_sites: int | None = None
    data_level: str = "published_aggregate"
    plot_data_open: bool = False
    citation: str = ""
    url: str = ""
    notes: str = ""

def evidence_se(e: StructuralEvidence):
    """Return (SE, method) only when a defensible study-level SE can be derived."""
    if e.se is not None and e.se > 0:
        return float(e.se),"published_se"
    if e.sd is not None and e.sd > 0 and e.n_plots and e.n_plots > 1:
        return float(e.sd)/math.sqrt(float(e.n_plots)),"published_sd/sqrt(n_plots)"
    if e.ci95_low is not None and e.ci95_high is not None and e.ci95_high > e.ci95_low:
        return (float(e.ci95_high)-float(e.ci95_low))/(2*1.96),"ci95_width/3.92"
    if e.iqr_low is not None and e.iqr_high is not None and e.iqr_high > e.iqr_low and e.n_plots and e.n_plots > 1:
        # Normal approximation only. Kept explicit in outputs.
        sd=(float(e.iqr_high)-float(e.iqr_low))/1.349
        return sd/math.sqrt(float(e.n_plots)),"IQR/1.349/sqrt(n_plots)_approx"
    return None,None

def random_effects_summary(records: Iterable[StructuralEvidence]):
    """DerSimonian-Laird study-level random-effects synthesis.

    Only same-metric/same-unit records with means and usable SE enter weighting.
    Range-only records remain in the transfer envelope and are listed as excluded.
    """
    rows=list(records)
    usable=[]; excluded=[]
    for e in rows:
        if str(e.center_type).casefold() != "mean":
            excluded.append((e.source_id,"center_not_mean")); continue
        if e.mean is None:
            excluded.append((e.source_id,"missing_mean")); continue
        se,method=evidence_se(e)
        if se is None or not math.isfinite(se) or se <= 0:
            excluded.append((e.source_id,"no_defensible_se")); continue
        usable.append((e,float(e.mean),float(se),method))
    if not usable:
        return {"available":False,"reason":"no study-level mean with defensible SE",
                "excluded_studies":excluded,"k":0}
    metrics={e.metric for e,_,_,_ in usable}; units={e.unit for e,_,_,_ in usable}
    if len(metrics)!=1 or len(units)!=1:
        raise ValueError("Random-effects synthesis requires one metric and one unit.")
    yi=[x[1] for x in usable]; vi=[x[2]**2 for x in usable]; wi=[1/v for v in vi]
    sw=sum(wi); fixed=sum(w*y for w,y in zip(wi,yi))/sw
    q=sum(w*(y-fixed)**2 for w,y in zip(wi,yi))
    k=len(usable); c=sw-sum(w*w for w in wi)/sw
    tau2=max(0.0,(q-(k-1))/c) if k>1 and c>0 else 0.0
    wr=[1/(v+tau2) for v in vi]; swr=sum(wr)
    mu=sum(w*y for w,y in zip(wr,yi))/swr
    se_mu=math.sqrt(1/swr)
    lo,hi=mu-1.96*se_mu,mu+1.96*se_mu
    envelope=[]
    for e in rows:
        if e.range_low is not None: envelope.append(float(e.range_low))
        if e.range_high is not None: envelope.append(float(e.range_high))
        if e.ci95_low is not None: envelope.append(float(e.ci95_low))
        if e.ci95_high is not None: envelope.append(float(e.ci95_high))
    return {
        "available":True,"metric":next(iter(metrics)),"unit":next(iter(units)),
        "k":k,"random_effects_mean":mu,"se":se_mu,"ci95":[lo,hi],
        "tau2":tau2,"Q":q,"I2_pct":max(0.0,(q-(k-1))/q*100.0) if q>0 and k>1 else 0.0,
        "methods":{e.source_id:m for e,_,_,m in usable},
        "study_ids":[e.source_id for e,_,_,_ in usable],
        "excluded_studies":excluded,
        "observed_transfer_envelope":[min(envelope),max(envelope)] if envelope else None,
        "interpretation":"study-level random-effects synthesis; no synthetic plots; CI95 is for pooled study mean, not target-AOI prediction interval",
    }

def harmonize_primary_plot_rows(rows, inventory_id, plot_area_ha, dbh_field="dbh_cm",
                                plot_field="plot_id", height_field="height_m"):
    """Create structural plot rows from open primary tree data."""
    from collections import defaultdict
    groups=defaultdict(list)
    for r in rows:
        try:d=float(r.get(dbh_field))
        except Exception:continue
        if not math.isfinite(d) or d<=0:continue
        pid=str(r.get(plot_field) or "").strip()
        if not pid:continue
        try:h=float(r.get(height_field)) if r.get(height_field) not in (None,"") else None
        except Exception:h=None
        groups[pid].append((d,h))
    out=[]
    for pid,trees in sorted(groups.items()):
        ba=sum(math.pi*(d/200.0)**2 for d,_ in trees)
        heights=[h for _,h in trees if h is not None and math.isfinite(h) and h>0]
        out.append({"inventory_id":inventory_id,"plot_id":pid,"plot_area_ha":float(plot_area_ha),
                    "n_stems":len(trees),"stems_ha":len(trees)/float(plot_area_ha),
                    "mean_dbh_cm":sum(d for d,_ in trees)/len(trees),
                    "basal_area_m2_ha":ba/float(plot_area_ha),
                    "mean_field_height_m":sum(heights)/len(heights) if heights else None,
                    "data_level":"primary_plot","synthetic":False})
    return out
