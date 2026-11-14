"""Pre-field EXPERIMENTAL predictions from actual Enform Verde analysis outputs.

Does NOT create field observations, calibration samples, confidence intervals or
scientific homologation. Numerical values appear only when an upstream
source-backed model has actually produced a compatible numerical estimate.
The deliverables let users later collect independent field measurements and
test errors, coverage and calibration.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "enform.pre_field_predictions.v1"
C_TO_CO2 = 44.0 / 12.0
POOL_METHOD = {
    "Biomassa aérea": "Parcelas estratificadas; DAP, altura, espécie e alometria compatível; georreferenciar.",
    "Biomassa subterrânea": "Amostragem de raízes ou alometria calibrada em parcelas independentes; domínio fitofisionômico.",
    "Necromassa aérea": "Inventário independente de madeira morta em pé e caída; volumes, densidades e carbono.",
    "Necromassa subterrânea": "Inventário direto apropriado de raízes mortas, sem inferir por alometria de biomassa viva.",
    "Serapilheira": "Coletas gravimétricas georreferenciadas por parcela e massa seca/carbono.",
    "Solo 0–100 cm": "Amostras por profundidade 0–5, 5–15, 15–30, 30–60 e 60–100 cm; densidade, fragmentos e carbono.",
    "Produtividade agrícola": "Colheita independente por talhão e safra; área efetivamente colhida e massa corrigida para umidade.",
}


def _num(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) and n >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _bounds(pair, center):
    if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or
            center is None):
        return None
    lo, hi = _num(pair[0]), _num(pair[1])
    return [lo, hi] if lo is not None and hi is not None and lo <= center <= hi else None


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        allow_nan=False, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _safe_id(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value))[:48].strip("_") or "unknown"


def _choose_interval(component, value):
    # Respect the scientific semantics supplied by the original product.
    published = _bounds(component.get("range_tc_ha"), value)
    if published:
        return published, "FAIXA_DA_FONTE_OU_CENARIO_NAO_CALIBRADA_AOI"
    if component.get("parametro") == "Biomassa aérea":
        agb = component.get("agb_range_mg_ha")
        if isinstance(agb, (list, tuple)) and len(agb) == 2:
            converted = [_num(agb[0]), _num(agb[1])]
            if all(x is not None for x in converted):
                result = _bounds([v * 0.47 for v in converted], value)
                if result:
                    return result, "FAIXA_AGB_PUBLICADA_CONVERTIDA_C0_47_SEM_CALIBRACAO_AOI"
    if component.get("parametro") == "Biomassa subterrânea":
        conditional = _bounds(component.get("root_prediction_interval_tc_ha"), value)
        if conditional:
            return conditional, "INTERVALO_ALOMETRICO_CONDICIONAL_NAO_VALIDADO_NA_AOI"
    if component.get("parametro") == "Solo 0–100 cm":
        official = component.get("official_uncertainty") or {}
        if official.get("status") == "ENVELOPE_MARGINAL_OFICIAL":
            result = _bounds(official.get("sum_bounds_envelope_tc_ha"), value)
            if result:
                return result, "ENVELOPE_DE_LIMITES_MARGINAIS_OFICIAIS_NAO_IC95_CONJUNTO"
    return None, "INCERTEZA_PREDITIVA_AOI_NAO_QUANTIFICADA"


def _component_prediction(stratum, component, index, analysis_id):
    value = _num(component.get("tc"))
    area = _num(component.get("area_basis_ha"))
    if area is None:
        area = _num(stratum.get("area_ha"))
    method = str(component.get("metodo") or "")
    origin = str(component.get("origem") or "N/D")
    source = str(component.get("fonte") or "N/D")
    interval, interval_kind = _choose_interval(component, value)
    invalid_labels = {"", "n/d", "nao estimado", "não estimado", "sem dado compatível",
                      "desconhecido", "none", "null", "indisponível", "indisponivel"}
    fitted = (
        value is not None and area is not None and area > 0
        and method.strip().casefold() not in invalid_labels
        and source.strip().casefold() not in invalid_labels
        and origin.strip().casefold() not in invalid_labels
        and bool(str(component.get("parametro") or "").strip())
    )
    density = value if fitted else None
    stock = value * area if fitted else None
    row = {
        "prediction_id": f"{_safe_id(analysis_id)}-S{index[0]:03d}-C{index[1]:02d}",
        "analysis_id": analysis_id,
        "kind": "carbono_nativo",
        "status": "PROJECAO_EXPERIMENTAL_PARA_VALIDACAO" if fitted else "N/D",
        "physiognomy": str(stratum.get("physiognomy") or ""),
        "land_cover_source": str(stratum.get("source") or ""),
        "compartment": str(component.get("parametro") or ""),
        "unit": "tC/ha",
        "density_predicted_tc_ha": density,
        "area_basis_ha": area if fitted else None,
        "stock_predicted_tC": stock,
        "stock_predicted_tCO2e": stock * C_TO_CO2 if stock is not None else None,
        "density_range_tc_ha": interval if fitted else None,
        "stock_range_tC": [v * area for v in interval] if fitted and interval else None,
        "uncertainty_kind": interval_kind if fitted else "N/D",
        "spatial_sd_descriptive_tc_ha": _num(component.get("spatial_sd_tc_ha")),
        "origin": origin,
        "model": method,
        "source": source,
        "source_url": component.get("source_url"),
        "source_sha256_claim": component.get("source_sha256"),
        "source_bytes_verified": False,
        "scientifically_homologated": False,
        "target_aoi_ci95_validated": False,
        "field_validation_pending": True,
        "contributes_to_existing_carbon_total": bool(component.get("include_in_total", False)),
        "limitation": str(component.get("obs") or "Ausência de modelo, medição ou incerteza compatível"),
        "field_protocol": POOL_METHOD.get(str(component.get("parametro")), "Medição independente de campo, em unidades compatíveis."),
    }
    if not fitted:
        row["reason"] = "Sem estimativa numérica com fonte e método aplicáveis nesta classe"
    row["trace_sha256"] = _sha(row)
    return row


def _yield_prediction(forecast, analysis_id):
    from experimental_audit import audit_yield_forecast, eligible_experimental_yield
    forecast = forecast if isinstance(forecast, dict) else {}
    audit = audit_yield_forecast(forecast, analysis_id=analysis_id)
    eligible = eligible_experimental_yield(forecast)
    result = audit.get("result") if eligible else None
    point = result.get("yield_t_ha") if result else None
    area = _num(forecast.get("crop_area_ha"))
    row = {
        "prediction_id": f"{_safe_id(analysis_id)}-AGRI-001",
        "analysis_id": analysis_id,
        "kind": "produtividade_agricola",
        "status": "PROJECAO_EXPERIMENTAL_PARA_VALIDACAO" if eligible else "N/D",
        "compartment": "Produtividade agrícola",
        "crop": str(forecast.get("crop") or "N/D"),
        "unit": "t/ha",
        "predicted_t_ha": point if eligible else None,
        "prediction_range_t_ha": result.get("range_t_ha") if result else None,
        "area_basis_ha": area if eligible else None,
        "predicted_production_t": result.get("production_t") if result else None,
        "uncertainty_kind": forecast.get("uncertainty_kind") if eligible else "N/D",
        "model": forecast.get("model_id"),
        "source": forecast.get("training_source"),
        "source_sha256_claim": (audit.get("source") or {}).get("sha256_claim"),
        "source_bytes_verified": False,
        "scientifically_homologated": False,
        "target_aoi_ci95_validated": False,
        "field_validation_pending": True,
        "field_protocol": POOL_METHOD["Produtividade agrícola"],
        "limitation": "PAM microrregional não é observação da fazenda; intervalo somente no domínio declarado.",
    }
    if not eligible:
        row["reason"] = str(audit.get("reason") or "previsão ainda não elegível para publicação experimental")
    row["trace_sha256"] = _sha(row)
    return row


def build_pre_field_manifest(native, *, analysis_id, land=None, source_sha=None):
    """Generate frozen machine-auditable candidate estimates, never fake field data.

    A point estimate without a defensible interval is still useful for a
    future test, but it explicitly carries unavailable predictive uncertainty.
    The independent scientific release gate remains unchanged.
    """
    if not isinstance(native, dict) or not isinstance(native.get("strata"), list):
        raise ValueError("Resultados reais de análise nativa ausentes")
    if not isinstance(analysis_id, str) or not analysis_id.strip():
        raise ValueError("Identificador de análise obrigatório")
    predictions = []
    for si, stratum in enumerate(native["strata"], start=1):
        for ci, component in enumerate(stratum.get("components") or [], start=1):
            predictions.append(_component_prediction(stratum, component, (si,ci), analysis_id))
    land = land if isinstance(land, dict) else {}
    if isinstance(land.get("yield_forecast"), dict):
        predictions.append(_yield_prediction(land["yield_forecast"], analysis_id))
    available = sum(p["status"] == "PROJECAO_EXPERIMENTAL_PARA_VALIDACAO" for p in predictions)
    manifest = {
        "schema": SCHEMA, "analysis_id": analysis_id,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_code_sha": source_sha,
        "status": "CANDIDATOS_EXPERIMENTAIS_PARA_TESTE_EM_CAMPO",
        "predictions_count": len(predictions),
        "predictions_with_numeric_model": available,
        "predictions_without_model": len(predictions)-available,
        "existing_native_stock_tC": _num(native.get("known_total_tc")),
        "existing_native_stock_is_complete": bool(native.get("complete")),
        "native_strata_area_ha": _num(native.get("native_area_ha")),
        "sample_design": {
            "target_confidence": 0.95, "target_relative_error": 0.05,
            "design": "Amostragem estratificada aleatória ou sistemática com início aleatório;"
                      " parcelas independentes do treinamento e da seleção do modelo.",
            "sample_size": "DEFINIR_APOS_PILOTO_COM_CV_OBSERVADO_E_CORRECAO_FINITA",
            "independence": "Parcela e talhão espacialmente independentes de treinamento e ajuste.",
            "field_variables": "DAP, altura, fitofisionomia, biomassa viva, necromassa direta,"
                               " serapilheira, SOC e densidade 0–100 cm, área e produção agrícola",
            "validation_metrics": ["n_independent_sites","bias","MAE","RMSE","R2",
                                   "relative_error","prediction_interval_coverage"],
            "observations_supplied": False,
        },
        "scientifically_homologated": False,
        "observed_validation_evidence": False,
        "predictions": predictions,
        "warning": "Valores são resultados modelados ou cenários condicionais; sem observação"
                   " independente na propriedade, não constituem estoque certificado ou IC95% de campo.",
    }
    manifest["trace_sha256"] = _sha(manifest)
    return manifest


def field_measurement_rows(manifest):
    """Return paired blank field-measurement rows: never prepopulate observations."""
    rows = []
    for p in manifest.get("predictions") or []:
        predicted = (p.get("density_predicted_tc_ha") if p.get("kind")=="carbono_nativo"
                     else p.get("predicted_t_ha"))
        rows.append({
            "prediction_id": p["prediction_id"], "analysis_id": manifest["analysis_id"],
            "fitofisionomia": p.get("physiognomy") or "",
            "compartimento_cultura": p.get("compartment") or p.get("crop") or "",
            "valor_modelado": predicted if predicted is not None else "",
            "unidade": p.get("unit") or "",
            "area_modelada_ha": p.get("area_basis_ha") or "",
            "data_coleta_utc": "", "parcela_talhao_id": "", "grupo_espacial_independente": "",
            "latitude": "", "longitude": "", "valor_medido_campo": "",
            "metodo_campo": "", "laboratorio": "", "fonte_primaria": "",
            "documento_fonte_sha256": "", "observacao": "",
        })
    return rows


def write_pre_field_evidence(out_dir, manifest):
    """Atomic JSON and blank CSV template; no synthetic observations are written."""
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    output = {}
    path = root / "previsoes_experimentais_pre_campo.json"
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False,
                                default=str),encoding="utf-8")
    temp.replace(path)
    output["predictions_json"] = str(path)
    rows = field_measurement_rows(manifest)
    template = root / "planilha_entrada_medicoes_campo.csv"
    headers = (list(rows[0]) if rows else [
        "prediction_id","analysis_id","fitofisionomia","compartimento_cultura",
        "valor_modelado","unidade","area_modelada_ha","data_coleta_utc",
        "parcela_talhao_id","grupo_espacial_independente","latitude","longitude",
        "valor_medido_campo","metodo_campo","laboratorio","fonte_primaria",
        "documento_fonte_sha256","observacao"])
    with template.open("w",newline="",encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream,fieldnames=headers,delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    output["field_template_csv"] = str(template)
    return output
