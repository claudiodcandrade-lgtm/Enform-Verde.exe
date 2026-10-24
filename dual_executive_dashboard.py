"""Executive dashboard with strictly separated native-carbon and cultivated-area analyses.

Display-only. Estimates and uncertainties must come from upstream validated
pipelines. Missing uncertainty is never replaced with a made-up number.
"""
from html import escape
from pathlib import Path
from math import isfinite
from carbon_dashboard_html import render_dashboard

def _pt(value):
    v = float(value)
    if not isfinite(v):
        raise ValueError("Número inválido")
    return f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def _cell(value, unit=""):
    return "Não disponível" if value is None else _pt(value) + (" " + unit if unit else "")

def _safe(value):
    return escape(str(value if value is not None else "Não informado"))

def render_cultivated_dashboard(report):
    """A crop panel; no carbon quantities are accepted or calculated here."""
    fields = report.get("fields", [])
    rows = []
    for field in fields:
        area = field.get("area_ha")
        if area is not None and float(area) < 0:
            raise ValueError("Área cultivada negativa")
        y = field.get("yield_t_ha")
        error = field.get("yield_uncertainty_t_ha")
        if error is not None and (not isfinite(float(error)) or float(error) < 0):
            raise ValueError("Incerteza de produtividade inválida")
        uncertainty = ("Não quantificada" if error is None else
                       "±" + _pt(error) + " t/ha (" +
                       ("±" + _pt(float(error) / float(y) * 100) + "%" if y is not None and float(y) > 0 else
                        "percentual indisponível") + ")")
        production = float(y) * float(area) if y is not None and area is not None else None
        production_uncertainty = (float(error) * float(area) if error is not None and area is not None else None)
        status = _safe(field.get("status", "Sem validação"))
        rows.append("<tr><td>" + _safe(field.get("crop", "Cultura não determinada")) +
                    "</td><td>" + _cell(area, "ha") +
                    "</td><td>" + _safe(field.get("phenology", "Não determinada")) +
                    "</td><td>" + _safe(field.get("stress_indicator", "Não determinado")) +
                    "</td><td>" + _cell(y, "t/ha") +
                    "</td><td>" + _cell(production, "t") +
                    "</td><td>" + uncertainty +
                    "</td><td>" + _cell(production_uncertainty, "t") +
                    "</td><td>" + status + "</td></tr>")
    details = "".join("<details><summary>" + _safe(f.get("crop", "Talhão")) +
                      " — fontes e validação</summary><pre>" +
                      _safe(f.get("provenance", "Não documentada")) + "</pre></details>"
                      for f in fields)
    return ("""<h2>Monitoramento de áreas cultivadas</h2>
<p>Indicadores de estresse não equivalem a diagnóstico de pragas ou doenças.</p>
<table><thead><tr><th>Cultura</th><th>Área</th><th>Fase</th><th>Estresse</th>
<th>Produtividade prevista</th><th>Produção prevista</th><th>Incerteza de produtividade</th>
<th>Incerteza de produção*</th><th>Status</th></tr></thead><tbody>""" +
            "".join(rows) + """</tbody></table>
<p>*Propagação apenas da incerteza de produtividade, considerando a área fixa;
não inclui incerteza de classificação/área. Não equivale automaticamente a IC95%.</p>
<p>Sem estimativa ou incerteza validada: indicação explícita de indisponibilidade.</p>
<h3>Fontes e rastreabilidade</h3>""" + details)

def render_dual_dashboard(*, native_carbon=None, cultivated=None):
    native = render_dashboard(native_carbon or {"native_area_ha": 0, "compartments": []})
    # Reuse the existing carbon HTML, retaining its layout and provenance.
    body_start = native.find("<h1>")
    body_end = native.rfind("</html>")
    native_fragment = native[body_start:body_end] if body_start >= 0 and body_end >= 0 else native
    crop_fragment = render_cultivated_dashboard(cultivated or {"fields": []})
    return ("""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Enform Verde — Painel executivo</title>
<style>
body{font:16px system-ui,sans-serif;max-width:1200px;margin:auto;padding:24px;color:#20342b;background:#f6f8f6}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card,section{background:white;border:1px solid #d9e3dc;border-radius:12px;padding:18px;margin:12px 0}
.card strong{display:block;font-size:1.6rem;margin-top:8px}
table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #e1e6e2}
details{padding:12px;border-bottom:1px solid #e1e6e2}pre{white-space:pre-wrap;overflow-wrap:anywhere}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}nav a{border:1px solid #a6b8aa;padding:10px 16px;border-radius:9px;color:inherit;text-decoration:none}
.panel{display:none}.panel:target{display:block}#carbon:not(:has(~ #cultivos:target)){display:block}
</style><h1>Enform Verde — Painel executivo</h1>
<nav><a href="#carbon">Carbono em formações nativas</a><a href="#cultivos">Monitoramento de áreas cultivadas</a></nav>
<div id="carbon" class="panel">""" + native_fragment +
            """</div><div id="cultivos" class="panel">""" + crop_fragment +
            """</div></html>""")

def save_dual_dashboard(path, *, native_carbon=None, cultivated=None):
    Path(path).write_text(render_dual_dashboard(native_carbon=native_carbon,
                                                cultivated=cultivated), encoding="utf-8")
