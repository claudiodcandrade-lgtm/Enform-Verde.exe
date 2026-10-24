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

def _crop_age_display(field):
    value = field.get("probable_crop_age_days")
    if (field.get("crop_age_validation_status") != "validated" or
            field.get("sar_freshness_status") != "cenas_recentes_identificadas" or value is None):
        return "Indisponível — sem idade fenológica validada"
    try:
        value = float(value)
        if not isfinite(value) or value < 0:
            return "Indisponível — idade inválida"
    except (TypeError, ValueError):
        return "Indisponível — idade inválida"
    return _pt(value) + " dias"

def _health_display(field):
    allowed = {"bom": "Bom", "médio": "Médio", "medio": "Médio", "ruim": "Ruim"}
    status = str(field.get("apparent_phytosanitary_state", "")).strip().casefold()
    if (field.get("phytosanitary_validation_status") != "validated" or
            field.get("sar_freshness_status") != "cenas_recentes_identificadas" or status not in allowed):
        return "Indisponível"
    return allowed[status]

def _verified_yield_interval(field):
    if field.get("forecast_status") != "previsao_validada":
        return None
    value = field.get("yield_t_ha")
    interval = field.get("prediction_interval_t_ha")
    try:
        value = float(value)
        lower, upper = float(interval["lower"]), float(interval["upper"])
        if not all(isfinite(x) for x in (value, lower, upper)) or lower < 0 or upper < lower or not lower <= value <= upper:
            raise ValueError
    except (TypeError, KeyError, ValueError):
        return None
    return value, lower, upper

def _yield_display(field):
    if field.get("forecast_status") != "previsao_validada":
        return "Bloqueada — modelo/validação insuficientes"
    values = _verified_yield_interval(field)
    if values is None:
        return "Bloqueada — intervalo preditivo ausente ou inválido"
    value, lower, upper = values
    return _pt(value) + " t/ha (" + _pt(lower) + "–" + _pt(upper) + " t/ha)"

def render_cultivated_dashboard(report):
    """A crop panel; no carbon quantities are accepted or calculated here."""
    fields = report.get("fields", [])
    rows = []
    for field in fields:
        area = field.get("area_ha")
        if area is not None and float(area) < 0:
            raise ValueError("Área cultivada negativa")
        valid_yield = _verified_yield_interval(field)
        y = valid_yield[0] if valid_yield is not None else None
        raw_error = field.get("yield_uncertainty_t_ha")
        if raw_error is not None and (not isfinite(float(raw_error)) or float(raw_error) < 0):
            raise ValueError("Incerteza de produtividade inválida")
        error = raw_error if valid_yield is not None else None
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
                    "</td><td>" + _safe(_crop_age_display(field)) +
                    "</td><td>" + _safe(_health_display(field)) +
                    "</td><td>" + _safe(_yield_display(field)) +
                    "</td><td>" + _cell(production, "t") +
                    "</td><td>" + uncertainty +
                    "</td><td>" + _cell(production_uncertainty, "t") +
                    "</td><td>" + status + "</td></tr>")
    details = "".join("<details><summary>" + _safe(f.get("crop", "Talhão")) +
                      " — fontes e validação</summary><pre>" +
                      _safe(f.get("provenance", "Não documentada")) + "</pre></details>"
                      for f in fields)
    return ("""<h2>Monitoramento de áreas cultivadas</h2>
<p>Idade e estado fitossanitário aparente dependem de evidência SAR atual e validação apropriada. Estado aparente não é diagnóstico de doença ou praga.</p>
<table><thead><tr><th>Cultura</th><th>Área</th><th>Idade provável da lavoura</th><th>Estado fitossanitário aparente</th>
<th>Previsão de safra</th><th>Produção prevista</th><th>Incerteza de produtividade</th>
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
