"""Uncertainty propagation primitives for Enform Verde (no scientific calibration implied).

Pure standard-library module. All input stocks in tC/ha; covariance in (tC/ha)^2.
"""
from math import sqrt, isfinite
from statistics import NormalDist

def aggregate_stock(areas_ha, means_tc_ha, covariance_tc2_ha2):
    """Return total tC, standard error and normal-approximation 95% interval.

    covariance must describe *area-level estimate errors*, including shared systematic
    components and spatial dependence; do not use pixel SDs as independent errors.
    """
    n = len(areas_ha)
    if n == 0 or len(means_tc_ha) != n or len(covariance_tc2_ha2) != n:
        raise ValueError("dimension mismatch")
    if any(len(row) != n for row in covariance_tc2_ha2):
        raise ValueError("covariance dimension mismatch")
    if any(not isfinite(x) or x < 0 for x in areas_ha):
        raise ValueError("invalid area")
    if any(not isfinite(x) or x < 0 for x in means_tc_ha):
        raise ValueError("invalid carbon stock")
    for i in range(n):
        for j in range(n):
            x = covariance_tc2_ha2[i][j]
            if not isfinite(x) or abs(x-covariance_tc2_ha2[j][i]) > 1e-9:
                raise ValueError("invalid/asymmetric covariance")
        if covariance_tc2_ha2[i][i] < 0:
            raise ValueError("negative variance")
    # An area-vector variance >= 0 is not sufficient to establish a valid
    # covariance matrix. Use a rank-tolerant LDL' decomposition to reject
    # indefinite matrices, including those with zero-variance variables that
    # falsely carry nonzero covariance.
    scale=max(1.0,max(abs(x) for row in covariance_tc2_ha2 for x in row))
    tolerance=1e-10*scale
    lower=[[0.0]*n for _ in range(n)]
    diagonal=[0.0]*n
    for i in range(n):
        residual=covariance_tc2_ha2[i][i]-sum(
            lower[i][k]**2*diagonal[k] for k in range(i))
        if residual < -tolerance:
            raise ValueError("covariance matrix is not positive semidefinite")
        diagonal[i]=max(0.0,residual)
        lower[i][i]=1.0
        for j in range(i+1,n):
            cross=covariance_tc2_ha2[j][i]-sum(
                lower[j][k]*lower[i][k]*diagonal[k] for k in range(i))
            if diagonal[i] <= tolerance:
                if abs(cross) > tolerance:
                    raise ValueError("nonzero covariance for a zero-variance direction")
            else:
                lower[j][i]=cross/diagonal[i]
    total = sum(a*m for a,m in zip(areas_ha,means_tc_ha))
    variance = sum(areas_ha[i]*areas_ha[j]*covariance_tc2_ha2[i][j]
                   for i in range(n) for j in range(n))
    if variance < -1e-8:
        raise ValueError("covariance not positive semidefinite along area vector")
    se = sqrt(max(variance, 0))
    z = NormalDist().inv_cdf(.975)
    return {"stock_tC":total,"se_tC":se,
            "ci95_tC":(max(0.,total-z*se),total+z*se),
            "stock_tCO2e":total*44/12,
            "ci95_tCO2e":(max(0.,total-z*se)*44/12,(total+z*se)*44/12),
            "interval_method":"normal_approximation_clipped_at_zero",
            "coverage_validated":False}

def soil_horizon_stock_tc_ha(thickness_cm, bulk_density_g_cm3, carbon_fraction,
                             coarse_fragment_fraction=0.):
    """Stock tC/ha = thickness(cm)*bulk density(g/cm3)*C fraction*100*(1-rock fraction)."""
    x=(thickness_cm,bulk_density_g_cm3,carbon_fraction,coarse_fragment_fraction)
    if any(not isfinite(v) for v in x) or thickness_cm<=0 or bulk_density_g_cm3<=0 or not 0<=carbon_fraction<=1 or not 0<=coarse_fragment_fraction<1:
        raise ValueError("invalid horizon")
    return thickness_cm*bulk_density_g_cm3*carbon_fraction*100*(1-coarse_fragment_fraction)
