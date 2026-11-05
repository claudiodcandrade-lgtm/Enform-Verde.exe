"""Map native physiognomy area from native-cover intersection, not IBGE potential map."""
from collections import defaultdict
from math import isfinite

def format_property_physiognomies(native, fmt):
    total=float(native.get("area_aoi_ha") or 0)
    if not isfinite(total) or total<=0:
        return "Não determinada — área total inválida."
    groups=defaultdict(lambda: {"area":0.0,"sources":set()})
    for st in native.get("strata") or []:
        name=str(st.get("physiognomy") or st.get("class_name") or "").strip()
        area=float(st.get("area_ha") or 0)
        if name and isfinite(area) and area>0:
            groups[name]["area"]+=area
            groups[name]["sources"].add(str(st.get("source") or "N/D"))
    if not groups:
        return ("Não determinada — nenhuma interseção de vegetação nativa com "
                "fitofisionomia foi mapeada; IBGE potencial não comprova ocorrência.")
    lines=[]
    for name,v in sorted(groups.items(),key=lambda item:-item[1]["area"]):
        ha=v["area"]; sources=v["sources"]
        origin=("SAR com referência IBGE" if sources and all(
                s.startswith("SAR_VALIDADO") for s in sources)
                else "interseção cartográfica anual MapBiomas + IBGE" if
                any("MAPBIOMAS" in s for s in sources)
                else "fonte de cobertura não validada localmente")
        lines.append(f"{name}: {fmt(ha,2)} ha ({fmt(100*ha/total,2)}% da propriedade) — {origin}")
    unknown=float(native.get("unknown_cover_area_ha") or 0)
    if isfinite(unknown) and unknown>0:
        lines.append(f"Área com cobertura indeterminada: {fmt(unknown,2)} ha ({fmt(100*unknown/total,2)}%).")
    lines.append("Área MAPEADA, não presença atual comprovada em campo. "
                 "IBGE fornece o nome; limites dependem da máscara de cobertura "
                 "e da validação SAR/observacional.")
    return "\n".join(lines)
