"""Auditable additive low/central/high carbon envelopes for mapped native strata.

These are arithmetic sums of compatible source bounds, NOT a joint 95% CI.
If any included quantified pool lacks defensible bounds, the full minimum
and maximum are N/D. Pools with N/D central stock are never treated as zero.
"""
from math import isfinite

CO2_FACTOR = 44.0 / 12.0


def _number(value):
    try:
        result = float(value)
        return result if isfinite(result) and result >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _bounds(component):
    central = _number(component.get("tc"))
    if central is None:
        return None
    bounds = component.get("range_tc_ha")
    if bounds is None and component.get("parametro") == "Biomassa aérea":
        agb = component.get("agb_range_mg_ha")
        if isinstance(agb, (list, tuple)) and len(agb) == 2:
            bounds = [_number(agb[0]) * 0.47 if _number(agb[0]) is not None else None,
                      _number(agb[1]) * 0.47 if _number(agb[1]) is not None else None]
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
        return None
    low, high = (_number(v) for v in bounds)
    if low is None or high is None or not low <= central <= high:
        return None
    return low, high


def scenario_envelope(native):
    """Return per-pool and complete-known-stock envelope if fully supported.

    Missing pool means full-property scenarios remain N/D. Partial bounded
    subtotal is disclosed separately and must never be labelled whole-property.
    """
    area = _number(native.get("native_area_ha")) or 0.0
    results = []
    known = 0.0
    low_sum = 0.0
    high_sum = 0.0
    missing_bounds = []
    missing_stocks = []
    for st in native.get("strata") or []:
        for component in st.get("components") or []:
            name = str(component.get("parametro") or "N/D")
            label = str(st.get("physiognomy") or st.get("class_name") or "N/D")
            stock = _number(component.get("total_tc"))
            if stock is None:
                missing_stocks.append(label + ": " + name)
                continue
            known += stock
            basis = _number(component.get("quantified_area_ha"))
            if basis is None:
                missing_bounds.append(label + ": " + name + " — área não determinada")
                continue
            bounds = _bounds(component)
            if bounds is None:
                missing_bounds.append(label + ": " + name)
                results.append({"physiognomy":label, "compartment":name, "area_ha":basis,
                                "low_tc":None, "central_tc":stock, "high_tc":None,
                                "status":"LIMITES N/D", "uncertainty_kind":component.get("obs")})
                continue
            low, high = bounds
            low_stock, high_stock = low * basis, high * basis
            low_sum += low_stock
            high_sum += high_stock
            results.append({"physiognomy":label, "compartment":name, "area_ha":basis,
                            "low_tc":low_stock, "central_tc":stock, "high_tc":high_stock,
                            "status":"ENVELOPE DE FONTE", "uncertainty_kind":component.get("obs")})
    # If any stocked pool lacks bounds, even the known subtotal cannot have
    # a defensible aggregate minimum/maximum. Unknown pools remain separate.
    all_known_bounded = bool(results) and not missing_bounds
    return {
        "rows":results,
        "known_total_tc":known if results or missing_stocks else None,
        "minimum_known_tc":low_sum if all_known_bounded else None,
        "maximum_known_tc":high_sum if all_known_bounded else None,
        "minimum_known_tco2e":low_sum * CO2_FACTOR if all_known_bounded else None,
        "central_known_tco2e":known * CO2_FACTOR if results or missing_stocks else None,
        "maximum_known_tco2e":high_sum * CO2_FACTOR if all_known_bounded else None,
        "minimum_known_tco2e_ha":low_sum * CO2_FACTOR / area if all_known_bounded and area else None,
        "central_known_tco2e_ha":known * CO2_FACTOR / area if (results or missing_stocks) and area else None,
        "maximum_known_tco2e_ha":high_sum * CO2_FACTOR / area if all_known_bounded and area else None,
        "native_area_ha":area,
        "missing_bounds":missing_bounds,
        "missing_stocks":missing_stocks,
        "complete":bool(native.get("complete")) and all_known_bounded and not missing_stocks,
        "interpretation":"Soma aritmética de limites de fonte; NÃO é IC95% conjunto. "
                         "Se qualquer limite do estoque conhecido faltar, mínimo/máximo = N/D; "
                         "se qualquer compartimento faltar, total da propriedade = PARCIAL."
    }
