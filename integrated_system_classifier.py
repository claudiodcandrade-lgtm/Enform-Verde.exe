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
