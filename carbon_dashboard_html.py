"""Standalone HTML dashboard renderer for Enform Verde native carbon reports.

Input must contain already-computed estimates and provenance. Does not
change carbon computations, invent uncertainty, or authorize nonnative carbon.
"""
from html import escape
from pathlib import Path
from math import isfinite

def pt(x):
    return f"{float(x):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def render_dashboard(report):
    """Return self-contained HTML with summary, compartment table and audit trail."""
    title = escape(str(report.get("fitofisionomia", "Vegetação nativa")))
    area = float(report.get("native_area_ha", 0))
    if area < 0:
        raise ValueError("Área negativa")
    comps = report.get("compartments", [])
    rows, audit = [], []
    for item in comps:
        label = escape(str(item.get("name", "Compartimento")))
        stock = item.get("tc_ha")
        status = "Não estimado" if stock is None else pt(stock) + " tC/ha"
        uncertainty = item.get("uncertainty_tc_ha")
        if uncertainty is None or stock is None:
            uncert = "Não quantificada"
        else:
            if float(uncertainty) < 0:
                raise ValueError("Incerteza negativa")
            pct = "indisponível" if float(stock) <= 0 else "±" + pt(100 * float(uncertainty) / float(stock)) + "%"
            uncert = "±" + pt(uncertainty) + " tC/ha (" + pct + ")"
        kind = escape(str(item.get("uncertainty_kind", "não informada")))
        rows.append("<tr><th scope='row'>" + label + "</th><td>" + status + "</td><td>" +
                    uncert + "<small>" + kind + "</small></td></tr>")
        audit.append("<details><summary>" + label + " — rota e fontes</summary><pre>" +
                     escape(str(item.get("provenance", "Não documentada"))) + "</pre></details>")
    total = report.get("partial_total_tc")
    if total is not None and (not isfinite(float(total)) or float(total) < 0):
        raise ValueError("Estoque total inválido")
    co2 = float(total) * 44 / 12 if total is not None else None
    density = float(total) / area if total is not None and area > 0 else None
    all_estimated = bool(comps) and all(item.get("tc_ha") is not None for item in comps)
    total_kind = "COMPLETO NOS COMPARTIMENTOS LISTADOS" if all_estimated and report.get("all_required_compartments_present") else "PARCIAL"
    notes = []
    for item in comps:
        if item.get("tc_ha") is not None and item.get("uncertainty_tc_ha") is None:
            notes.append(escape(str(item.get("name", "Compartimento"))) + ": incerteza não quantificada")
    if not report.get("total_uncertainty_method"):
        notes.append("Incerteza do total: NÃO QUANTIFICADA — sem covariâncias ou propagação validada")
    else:
        notes.append("Método de incerteza do total: " + escape(str(report["total_uncertainty_method"])))
    notes_html = "<ul>" + "".join("<li>" + n + "</li>" for n in notes) + "</ul>"
    total_text = pt(total) + " tC" if total is not None else "Não calculado"
    return """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Enform Verde — Painel</title><style>
body{font:16px system-ui,sans-serif;max-width:1100px;margin:auto;padding:24px;color:#20342b;background:#f6f8f6}
h1,h2{margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card,section{background:white;border:1px solid #d9e3dc;border-radius:12px;padding:18px;margin:12px 0}
.card strong{display:block;font-size:1.6rem;margin-top:8px}
table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:13px;border-bottom:1px solid #e1e6e2}
td small{display:block;color:#566c60;margin-top:4px}details{padding:12px;border-bottom:1px solid #e1e6e2}
pre{white-space:pre-wrap;overflow-wrap:anywhere} .note{color:#566c60}
</style><h1>Enform Verde — Estoques de carbono</h1>
<p class="note">Resultados exclusivamente para vegetação nativa confirmada</p>
<h2>""" + title + """</h2><div class="cards"><div class="card">Área nativa<strong>""" + pt(area) + """ ha</strong></div>
<div class="card">Estoque parcial conhecido<strong>""" + total_text + """</strong><small>""" + total_kind + """</small></div>\n<div class="card">Equivalente CO₂<strong>""" + (pt(co2) + " tCO₂e" if co2 is not None else "Não calculado") + """</strong></div>\n<div class="card">Densidade de carbono<strong>""" + (pt(density) + " tC/ha" if density is not None else "Não calculada") + """</strong></div></div>
<section><h2>Compartimentos e incertezas</h2><table><thead><tr><th>Compartimento</th>
<th>Estoque</th><th>Incerteza (tC/ha e %)</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table>
<p class="note">Incerteza do produto, dispersão espacial e IC95% não são intercambiáveis.
Ausências não foram imputadas. Estoque parcial não equivale a estoque completo.</p></section>
<section><h2>Limites de precisão e incertezas</h2>""" + notes_html + """</section>\n<section><h2>Rastreabilidade técnica</h2><p>Expanda cada compartimento para consultar a rota,
os modelos, as fontes e as limitações.</p>""" + "".join(audit) + "</section></html>"

def save_dashboard(report, path):
    Path(path).write_text(render_dashboard(report), encoding="utf-8")
