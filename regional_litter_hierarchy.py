"""Serapilheira (standing litter) — defensible regional estimate with QUANTIFIED transfer error.

Why: the previous chain never let litter enter the total (V87.39 report: "a
serapilheira não entrou"), because single published values had no variance
and no transfer error. Here the transfer error is estimated EMPIRICALLY from
how much standing-litter stocks vary between independent forest sites in
Brazil (gravimetric inventories of the dry litter layer, not litterfall).

Model (log scale, site = independent unit):
    ln L_site ~ N(μ_g, τ²)
    μ̂_g = mean of ln(site means) of the k_g studies of the SAME phytophysiognomy
           and region as the AOI
    τ̂   = SD of ln(site means) over all k_F independent Brazilian FOREST sites
           (pooled heterogeneity; conservative because it mixes physiognomies)
    prediction for a new site: ln L* ~ μ̂_g + t_{k_F−1} · τ̂ · √(1 + 1/k_g)
Carbon: C = L* × f_C, f_C ~ Uniform(0,42; 0,50) (documented envelope; IPCC-type
fractions for leaf-dominated litter). Monte Carlo (fixed seed) propagates both.
Reported: mean tC/ha, SD, 90 % predictive interval; status experimental.
Within-site sampling error is small relative to τ and is NOT added again.

Never used: litterfall rates (Mg/ha/yr), IFN litter depth (no validated
depth→mass model), woody necromass, MapBiomas.
"""
from __future__ import annotations

import math

import numpy as np

# Independent site means of standing dry litter (Mg/ha). Only gravimetric
# stocks; one value per independent site/study.
FESV_SITES = (
    dict(key="SILVA_2009_SINOP_FESV", mg_ha=61453.3 / 12 / 1000.0, lon=-55.3238, lat=-11.4121,
         study=("Silva, Lobo, Bleich & Sanches (2009) Acta Amazonica 39(3):591–600 — floresta de "
                "transição Amazônia-Cerrado (semidecídua), Fazenda Maracaí ~50 km de Sinop-MT; 21 "
                "quadrados de 0,0625 m² por mês, mai/2004–abr/2005; média anual de 12 médias mensais "
                "(3,53–6,49 Mg/ha; CV temporal 16,6 %)"),
         url="https://acta.inpa.gov.br/fasciculos/39-3/PDF/v39n3a14.pdf"),
    dict(key="VOLPATO_2024_FESV_SUBMONTANA", mg_ha=8.70, lon=None, lat=None,
         study=("Volpato (2024) UFRRJ, tese, Tabela 8 — Floresta Estacional Sempre Verde Submontana, "
                "norte de Mato Grosso, 24 parcelas; ± não definido (não usado)"),
         url="https://rima.ufrrj.br/jspui/bitstream/20.500.14407/19957/1/2024%20-%20Maristela%20Volpato.Pdf"),
)
# Other independent Brazilian forest standing-litter sites (registry values,
# national_litter_inventory_registry.REFERENCES) used ONLY to estimate τ.
OTHER_FOREST_SITES = {"FOD_ES_TABULEIRO": 4.411, "FESD_ES_SUBMONTANA": 5.50, "FESD_BA_MONTANA": 6.30,
                      "FOM_RS_ARAU": 14.296, "FED_RS_SANTA_MARIA": 6.70, "FED_RS_ALTO_URUGUAI": 6.50,
                      "FES_RS_SUBTROPICAL": 13.404, "MATA_GALERIA_DF": 9.36}
FESV_REGION = (-59.0, -15.0, -52.0, -9.0)        # west, south, east, north (northern MT envelope)
CF_RANGE = (0.42, 0.50)


def pooled_forest_tau():
    vals = [s["mg_ha"] for s in FESV_SITES] + list(OTHER_FOREST_SITES.values())
    logs = np.log(vals)
    return float(np.std(logs, ddof=1)), len(vals)


def hierarchical_litter_estimate(site_means_mg_ha, *, n_mc=20000, seed=20261108):
    tau, k_forest = pooled_forest_tau()
    k = len(site_means_mg_ha)
    if k < 1:
        return None
    mu = float(np.mean(np.log(site_means_mg_ha)))
    sd_pred = tau * math.sqrt(1.0 + 1.0 / k)
    df = k_forest - 1
    rng = np.random.default_rng(seed)
    t_draw = rng.standard_t(df, n_mc)
    dry = np.exp(mu + sd_pred * t_draw)
    cf = rng.uniform(*CF_RANGE, n_mc)
    c = dry * cf
    q = lambda a, p: float(np.quantile(a, p))
    return {"geometric_mean_dry_mg_ha": math.exp(mu), "tau_ln": tau, "k_local_sites": k,
            "k_forest_sites": k_forest, "df": df, "predictive_sd_ln": sd_pred,
            "dry_p05_p50_p95": [q(dry, .05), q(dry, .5), q(dry, .95)],
            "mean_tc_ha": float(np.median(c)), "sd_tc_ha": float(np.std(c)),
            "range_tc_ha": [q(c, .05), q(c, .95)]}


def fesv_northern_mt_litter_component(biome, physiognomy, aoi):
    """Floresta Estacional Sempre-Verde, northern Mato Grosso (e.g. Sinop)."""
    from carbon_compartments import aoi_to_wgs84
    from native_carbon import normalize
    if normalize(biome) != "amazonia" or aoi is None:
        return None
    p = normalize(physiognomy).replace("-", " ")
    if "floresta estacional sempre verde" not in p:
        return None
    try:
        west, south, east, north = map(float, aoi_to_wgs84(aoi).total_bounds)
    except (ValueError, TypeError, AttributeError):
        return None
    w, s, e, n = FESV_REGION
    if not (w <= west <= east <= e and s <= south <= north <= n):
        return None
    est = hierarchical_litter_estimate([x["mg_ha"] for x in FESV_SITES])
    lo, hi = est["range_tc_ha"]
    return {
        "mean_tc_ha": est["mean_tc_ha"], "range_tc_ha": [lo, hi], "sd_tc_ha": est["sd_tc_ha"],
        "mean_dry_mg_ha": est["geometric_mean_dry_mg_ha"],
        "range_dry_mg_ha": [est["dry_p05_p50_p95"][0], est["dry_p05_p50_p95"][2]],
        "origin": "INVENTARIO_REGIONAL_HIERARQUICO",
        "include_in_total": True,
        "evidence_type": "standing_litter_dry_mass",
        "status": "ESTIMATIVA EXPERIMENTAL — erro de transferência quantificado por heterogeneidade entre sítios",
        "source": " | ".join(x["study"] for x in FESV_SITES),
        "url": FESV_SITES[0]["url"],
        "method": ("ln L* = média ln dos sítios FESV do norte de MT (k=%d) + t(%d)·τ·√(1+1/k); "
                   "τ = DP de ln estoque entre %d sítios florestais brasileiros independentes "
                   "(%.3f); C = L*·f_C, f_C ~ U(0,42; 0,50); Monte Carlo 20.000."
                   % (est["k_local_sites"], est["df"], est["k_forest_sites"], est["tau_ln"])),
        "uncertainty_kind": ("Intervalo PREDITIVO 90% para um sítio novo da mesma fitofisionomia "
                             "e região (inclui heterogeneidade entre sítios e fração de carbono); "
                             "não é medição da AOI nem IC95% de amostragem local"),
        "hierarchy_audit": est,
    }
