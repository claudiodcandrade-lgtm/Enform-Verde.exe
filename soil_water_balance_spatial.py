"""Dynamic, modelled effective soil-water storage (FAO-56 root-zone bucket).

Not measured volumetric moisture. Dry / central / wet results are sensitivity
scenarios, not 95% confidence intervals. The pedological unit's name alone
never supplies a numerical field-capacity, wilting-point or AD value.
ZARC AD1-AD6 ranges: SPA/MAPA 2026, to be checked against crop/UF ordinances.
"""
from __future__ import annotations
from datetime import date
from math import isfinite

AD_CLASSES = {
    "AD1":(.34,.46),"AD2":(.46,.61),"AD3":(.61,.80),
    "AD4":(.80,1.06),"AD5":(1.06,1.40),"AD6":(1.40,1.84)
}

def _num(value,label,minimum=None,maximum=None):
    try: x=float(value)
    except (TypeError,ValueError): raise ValueError(label+": value absent or nonnumeric")
    if not isfinite(x) or (minimum is not None and x<minimum) or (maximum is not None and x>maximum):
        raise ValueError(label+": value outside physical limits")
    return x

def available_capacity_mm(root_depth_m,*,ad_mm_cm=None,theta_fc=None,
                          theta_wp=None,coarse_fraction=0.):
    """Total available plant water above permanent wilting, mm of root zone."""
    zr=_num(root_depth_m,"root depth",.05,3.)
    rock=_num(coarse_fraction,"coarse fragments",0.,.8)
    if ad_mm_cm is None:
        if theta_fc is None or theta_wp is None:
            raise ValueError("numeric available-water capacity or retention data required")
        fc=_num(theta_fc,"theta_fc",0.,.8)
        wp=_num(theta_wp,"theta_wp",0.,.8)
        if fc<=wp:raise ValueError("FC must exceed PWP")
        ad_mm_cm=10.*(fc-wp)
    ad=_num(ad_mm_cm,"AD mm/cm",.01,4.)
    return ad*100.*zr*(1.-rock)

def pedotransfer_saxton_rawls(sand_fraction, clay_fraction, organic_matter_pct):
    """Saxton & Rawls (2006), FC -33kPa and PWP -1500kPa.

    Texture inputs S/C are 0–1 mass fractions, OM is percentage (0–30).
    Structure and compaction are not inferred from soil name; preserve
    separate coarse-fragment and rain-infiltration sensitivity assumptions.
    """
    s=_num(sand_fraction,"sand fraction",0.,1.)
    c=_num(clay_fraction,"clay fraction",0.,1.)
    om=_num(organic_matter_pct,"organic matter pct",0.,30.)
    if s+c>1.001:raise ValueError("sand + clay exceeds 100 percent")
    wp_t=(-.024*s+.487*c+.006*om+.005*s*om-.013*c*om+.068*s*c+.031)
    wp=wp_t+(.14*wp_t-.02)
    fc_t=(-.251*s+.195*c+.011*om+.006*s*om-.027*c*om+.452*s*c+.299)
    fc=fc_t+(1.283*fc_t**2-.374*fc_t-.015)
    if not 0<wp<fc<.8:raise ValueError("pedotransfer predicted implausible retention")
    return {"theta_fc":fc,"theta_wp":wp,"ad_mm_cm":10*(fc-wp),
            "source":"Saxton & Rawls (2006) pedotransfer from texture and OM",
            "measured_soil_water":False,
            "uncertainty":"transfer to Brazilian soil units requires local validation"}

def _date(r):
    x=r.get("date")
    if isinstance(x,date):return x
    s=str(x)
    if len(s)>=10 and s[4]=="-":return date.fromisoformat(s[:10])
    if len(s)>=8 and s[:8].isdigit():return date(int(s[:4]),int(s[4:6]),int(s[6:8]))
    raise ValueError("weather observation requires a date")

def daily_storage(daily,*,capacity_mm,lat_deg,kc=1.,p=.5,
                  initial_fraction=.5,infiltration_fraction=1.,irrigation_mm=0.):
    """FAO-56 root zone depletion. Explicit initial root-water assumption."""
    from crop_climate_favorability import et0_hargreaves
    taw=_num(capacity_mm,"TAW",.01,1000.)
    latitude=_num(lat_deg,"latitude",-90,90)
    kc=_num(kc,"Kc",0.,2.5)
    p=_num(p,"depletion fraction",.05,.95)
    initial=_num(initial_fraction,"initial soil water fraction",0.,1.)
    infiltration=_num(infiltration_fraction,"infiltration fraction",0.,1.)
    irrigation=_num(irrigation_mm,"irrigation assumption",0.,200.)
    dr=taw*(1.-initial);series=[];prev=None
    for row in sorted(daily,key=_date):
        d=_date(row)
        if prev is not None and (d-prev).days!=1:
            raise ValueError("weather daily series has an unfilled gap")
        prev=d
        rain=_num(row.get("PRECTOTCORR"),"precipitation",0.,600.)
        high=_num(row.get("T2M_MAX"),"maximum temperature",-30.,65.)
        low=_num(row.get("T2M_MIN"),"minimum temperature",-40.,60.)
        if high<low:raise ValueError("Tmax below Tmin")
        et0=et0_hargreaves(high,low,latitude,d.timetuple().tm_yday)
        etc=kc*et0;raw=p*taw
        ks=1. if dr<=raw else max(0.,(taw-dr)/max(taw-raw,1e-9))
        eta=ks*etc
        effective_rain=infiltration*rain
        unbounded=dr-effective_rain-irrigation+eta
        drainage=max(0.,-unbounded)
        dr=max(0.,min(taw,unbounded))
        storage=taw-dr
        series.append({"date":d.isoformat(),"rain_mm":rain,
            "effective_precipitation_mm":effective_rain,
            "et0_mm":et0,"etc_mm":etc,"eta_mm":eta,
            "ks":ks,"storage_mm":storage,
            "fraction_available":storage/taw,
            "deficit_mm":max(0.,etc-eta),"drainage_mm":drainage})
    if not series:raise ValueError("daily weather series empty")
    idx=max(0,len(series)-8)
    return {"as_of":series[-1]["date"],"storage_mm":series[-1]["storage_mm"],
        "fraction_available":series[-1]["fraction_available"],
        "root_zone_capacity_mm":taw,
        "water_deficit_mm":sum(s["deficit_mm"] for s in series),
        "drainage_excess_mm":sum(s["drainage_mm"] for s in series),
        "stress_days":sum(s["ks"]<.999 for s in series),
        "storage_change_7d_mm":series[-1]["storage_mm"]-series[idx]["storage_mm"],
        "days":len(series),"daily":series}

def scenarios(daily,*,root_depth_m,lat_deg,ad_class=None,ad_mm_cm=None,
              theta_fc=None,theta_wp=None,coarse_fraction=0.,
              kc=1.,p=.5,initial_fraction=None):
    """Dry/central/wet storage, not a probabilistic CI or current measurement."""
    if ad_class is not None:
        if ad_class not in AD_CLASSES:raise ValueError("unknown AD class")
        lo,hi=AD_CLASSES[ad_class];ad_values=(lo,(lo+hi)/2,hi)
        soil_source="ZARC AD class range; numeric class observed or mapped"
    else:
        if ad_mm_cm is not None:
            ad=_num(ad_mm_cm,"AD mm/cm",.01,4.)
        else:
            if theta_fc is None or theta_wp is None:
                return {"status":"N/D_SEM_PARAMETROS_HIDRAULICOS",
                    "reason":"mapa pedologico sem AD, thetaFC/PMP ou pedotransferencia calibrada",
                    "storage_measured":False}
            ad=10.*(_num(theta_fc,"FC")-_num(theta_wp,"PWP"))
        if ad<=0:raise ValueError("soil retention difference must be positive")
        ad_values=(ad*.8,ad,ad*1.2)
        soil_source="numeric AD or retention; +/-20% assumed sensitivity"
    init_values=([.2,.5,.8] if initial_fraction is None else
                 [_num(initial_fraction,"initial fraction",0.,1.)]*3)
    inf_values=(.65,.85,1.)
    estimates={}
    for name,ad,init,inf in zip(("seco","central","umido"),ad_values,init_values,inf_values):
        capacity=available_capacity_mm(root_depth_m,ad_mm_cm=ad,
                                      coarse_fraction=coarse_fraction)
        estimates[name]=daily_storage(daily,capacity_mm=capacity,lat_deg=lat_deg,
                       kc=kc,p=p,initial_fraction=init,
                       infiltration_fraction=inf)
    central=estimates["central"]
    return {"status":"ARMAZENAMENTO_HIDRICO_MODELADO",
            "measurement_type":"simulated_not_observed",
            "scenario_type":"deterministic_sensitivity_not_95pct_CI",
            "source_soil":soil_source,"source_climate":"daily observed/grid weather input",
            "soil_parameters":{"ad_class":ad_class,"ad_mm_cm":ad_mm_cm,
                "theta_fc":theta_fc,"theta_wp":theta_wp,
                "coarse_fraction":coarse_fraction,"root_depth_m":root_depth_m},
            "assumptions":{"initial_fraction_by_scenario":init_values,
                "infiltration_fraction_by_scenario":inf_values,
                "irrigation_assumed_mm_per_day":0.},
            "as_of":central["as_of"],
            "storage_mm_by_scenario":{k:v["storage_mm"] for k,v in estimates.items()},
            "deficit_mm_by_scenario":{k:v["water_deficit_mm"] for k,v in estimates.items()},
            "stress_days_by_scenario":{k:v["stress_days"] for k,v in estimates.items()},
            "storage_trend_7d_mm_by_scenario":{k:v["storage_change_7d_mm"] for k,v in estimates.items()},
            "root_zone_capacity_mm_by_scenario":{k:v["root_zone_capacity_mm"] for k,v in estimates.items()},
            "model_daily_central":central["daily"]}
