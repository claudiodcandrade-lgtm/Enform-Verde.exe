"""Human-readable summary of Enform Verde native-carbon reports.

Only show estimates for strata with positive area. Never confuse uncertainty
of a raster product with spatial dispersion or a confidence interval.
"""
def format_pt(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_stratum(name, area_ha, compartments, provenance=None):
    if area_ha <= 0:
        return ""
    lines = [f"FITOFISIONOMIA: {name}", f"Área nativa: {format_pt(area_ha)} ha"]
    if provenance:
        lines.append(f"Fonte SAR: {provenance.get('source', 'não informada')}")
        lines.append(f"Período de referência: {provenance.get('year', 'não informado')}")
    for label, data in compartments.items():
        if data.get('status') == 'not_estimated' or data.get('tc_ha') is None:
            lines.append(f"{label}: NÃO ESTIMADO — {data.get('reason', 'fonte/modelo indisponível')}")
            continue
        lines.append(f"{label}: {format_pt(data['tc_ha'])} tC/ha; "
                     f"{format_pt(data['tc_ha'] * 44 / 12)} tCO₂e/ha")
        if data.get('total_tc') is not None:
            lines.append(f"  Estoque total: {format_pt(data['total_tc'])} tC")
        if data.get('product_sd_mg_ha') is not None:
            lines.append(f"  Incerteza do produto: {format_pt(data['product_sd_mg_ha'])} Mg biomassa/ha"
                         " (não equivale a IC95% do total)")
        if data.get('spatial_sd_tc_ha') is not None:
            lines.append(f"  Desvio-padrão espacial: {format_pt(data['spatial_sd_tc_ha'])} tC/ha"
                         " (não equivale a erro de predição)")
        if data.get('ci95_tc_ha') is not None:
            low, high = data['ci95_tc_ha']
            lines.append(f"  IC95% publicado: {format_pt(low)}–{format_pt(high)} tC/ha"
                         " (não inclui necessariamente erro de transferência)")
        if data.get('uncertainty_note'):
            lines.append(f"  Limitação: {data['uncertainty_note']}")
    lines.append("Incertezas dos compartimentos não devem ser somadas como se fossem independentes.")
    return "\n".join(lines)
