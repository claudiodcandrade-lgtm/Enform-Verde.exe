"""Conservative land-use taxonomy for integrated production systems.

ILF: crop + trees; IPF: livestock/pasture + trees; ILPF: crop + livestock + trees.
Co-occurrence must be independently supported in the same management unit and
observation period; mere neighboring polygons do not prove integration.
"""
from __future__ import annotations

SYSTEM_COMPONENTS = {
    "ILF": frozenset(("lavoura", "floresta")),
    "IPF": frozenset(("pecuaria", "floresta")),
    "ILPF": frozenset(("lavoura", "pecuaria", "floresta")),
}

def identify_integrated_system(evidence, *, minimum_confidence=0.90):
    """Fail closed unless component evidence is validated and spatially linked.

    evidence: mapping component -> {present, confidence, validated, unit_id,
    period, source}. Returns a candidate only when the complete required
    component set shares an independently identified unit and period.
    """
    result={"class_name":None,"status":"NAO_COMPROVADO","sources":{},
            "reason":"componentes integrados não demonstrados"}
    if not isinstance(evidence,dict) or not 0 < minimum_confidence <= 1:
        return result
    accepted=set()
    units=set()
    periods=set()
    for component in ("lavoura","pecuaria","floresta"):
        item=evidence.get(component)
        if not isinstance(item,dict):
            continue
        try:
            confidence=float(item.get("confidence",0))
        except (ValueError,TypeError):
            continue
        if (item.get("present") is True and item.get("validated") is True
            and minimum_confidence <= confidence <= 1
            and item.get("unit_id") and item.get("period") and item.get("source")):
            accepted.add(component)
            units.add(str(item["unit_id"]))
            periods.add(str(item["period"]))
            result["sources"][component]=item["source"]
    if len(units)!=1 or len(periods)!=1:
        result["reason"]="evidências não demonstram a mesma unidade e período"
        return result
    if accepted == SYSTEM_COMPONENTS["ILPF"]:
        label="ILPF"
    elif accepted == SYSTEM_COMPONENTS["ILF"]:
        label="ILF"
    elif accepted == SYSTEM_COMPONENTS["IPF"]:
        label="IPF"
    else:
        result["reason"]="conjunto de componentes insuficiente"
        return result
    result.update({"class_name":label,"status":"CANDIDATO_COM_EVIDENCIAS",
                   "reason":"coocorrência documentada; confirmar integração por manejo",
                   "unit_id":next(iter(units)),"period":next(iter(periods))})
    return result

def validated_precision_interval(correct, total):
    """95% Wilson interval for independent accepted predictions; not area error."""
    from math import sqrt
    if not isinstance(correct,int) or not isinstance(total,int) or total<1 or not 0<=correct<=total:
        return None
    z=1.959963984540054
    p=correct/total
    d=1+z*z/total
    center=(p+z*z/(2*total))/d
    half=z*sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return {"precision":p,"ci95":[max(0,center-half),min(1,center+half)],
            "sample_size":total,"uncertainty_type":"precision of accepted class; not area confidence interval"}


SCIENTIFIC_ROUTES = {
    "ilpf_spatial_unet":{"method":"U-Net","institution":"Embrapa Solos / UERJ",
        "reference":"https://www.alice.cnptia.embrapa.br/handle/doc/1178498",
        "task":"spatial candidate detection","ready":False},
    "ilp_temporal_rf":{"method":"Random Forest","institution":"Embrapa Territorial / UNICAMP",
        "reference":"https://www.alice.cnptia.embrapa.br/handle/doc/1175472",
        "task":"crop-pasture temporal patterns","ready":False},
    "ilp_planetscope_temporal":{"method":"temporal deep learning",
        "reference":"https://www.sciencedirect.com/science/article/pii/S0034425723004376",
        "task":"crop-pasture time series","ready":False},
}

def model_route_status(route):
    """References do not become operational until fitted weights and local validation exist."""
    entry=SCIENTIFIC_ROUTES.get(route)
    if entry is None:
        return {"operational":False,"reason":"rota desconhecida"}
    return {"operational":bool(entry["ready"]),"reference":entry["reference"],
            "reason":"modelo documentado, pesos e validacao local pendentes" if not entry["ready"] else "validado"}

