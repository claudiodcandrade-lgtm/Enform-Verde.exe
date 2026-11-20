"""Clear per-compartment stocks for the desktop executive dashboard."""
from __future__ import annotations

import math

from executive_carbon_report import uncertainty_for_pool


COMPARTMENTS = (
    "Biomassa aérea",
    "Biomassa subterrânea",
    "Necromassa aérea",
    "Necromassa subterrânea",
    "Serapilheira",
    "Solo 0–100 cm",
)


def carbon_dashboard_rows(native: dict) -> list[dict]:
    """Aggregate known stock and defensible uncertainty without imputing N/D.

    AGB follows the owner's conservative rho=1 rule; soil spatial SD is pooled
    descriptively. Neither is mislabeled as a prediction interval.
    """
    strata = native.get("strata") or []
    native_area = float(native.get("native_area_ha") or 0.0)
    output = []
    for name in COMPARTMENTS:
        rows = [
            component
            for stratum in strata
            for component in (stratum.get("components") or [])
            if component.get("parametro") == name
            and isinstance(component.get("total_tc"), (int, float))
            and isinstance(component.get("tc"), (int, float))
            and component.get("total_tc") is not None
            and component.get("tc") is not None
        ]
        area = sum(float(row.get("quantified_area_ha", row.get("area_ha") or 0.0)) for row in rows)
        stock = sum(float(row["total_tc"]) for row in rows) if rows else None
        density = stock / area if stock is not None and area > 0 else None

        uncertainty_values = []
        sensitivity_values = []
        for row in rows:
            estimate = uncertainty_for_pool(row)
            if estimate.get("scope") == "sensitivity":
                sensitivity_values.append(estimate)
            elif estimate.get("absolute_tc_ha") is not None:
                uncertainty_values.append((row, estimate))

        uncertainty = None
        sensitivity = None
        uncertainty_kind = "N/D — erro de modelo/transferência não quantificado"
        if rows and len(uncertainty_values) == len(rows):
            if len(rows) == 1:
                uncertainty = float(uncertainty_values[0][1]["absolute_tc_ha"])
                uncertainty_kind = str(uncertainty_values[0][1].get("kind") or "tipo não informado")
            elif name in ("Biomassa aérea", "Biomassa subterrânea", "Necromassa aérea",
                          "Necromassa subterrânea") and area > 0:
                uncertainty = sum(
                    float(row.get("quantified_area_ha", row.get("area_ha") or 0.0))
                    * float(estimate["absolute_tc_ha"])
                    for row, estimate in uncertainty_values
                ) / area
                uncertainty_kind = "combinação conservadora entre estratos (ρ=1; biomassa correlacionada); " + "; ".join(
                    sorted({str(estimate.get("kind") or "tipo não informado")
                            for _, estimate in uncertainty_values})
                )
            elif name == "Solo 0–100 cm" and all(
                    "desvio-padrão espacial" in str(estimate.get("kind"))
                    for _, estimate in uncertainty_values) and area > 0:
                mean = density
                variance = sum(
                    (float(row.get("quantified_area_ha", row.get("area_ha") or 0.0)) / area)
                    * (float(estimate["absolute_tc_ha"]) ** 2 + (float(row["tc"]) - mean) ** 2)
                    for row, estimate in uncertainty_values
                )
                uncertainty = math.sqrt(max(0.0, variance))
                uncertainty_kind = "DP espacial descritivo combinado entre estratos; NÃO é erro de predição nem IC95%"
            elif all(row.get("uncertainty_independence") == "independent_strata"
                     for row, _ in uncertainty_values) and area > 0:
                uncertainty = math.sqrt(sum(
                    (float(row.get("quantified_area_ha", row.get("area_ha") or 0.0))
                     * float(estimate["absolute_tc_ha"])) ** 2
                    for row, estimate in uncertainty_values
                )) / area
                uncertainty_kind = "combinação entre estratos independentes; " + "; ".join(
                    sorted({str(estimate.get("kind") or "tipo não informado")
                            for _, estimate in uncertainty_values})
                )
            else:
                uncertainty_kind = "N/D — covariância entre estratos não documentada"
        elif sensitivity_values:
            sensitivity_rows = [(row, uncertainty_for_pool(row)) for row in rows]
            sensitivity = (sum(
                float(row.get("quantified_area_ha", row.get("area_ha") or 0.0))
                * float(estimate["absolute_tc_ha"])
                for row, estimate in sensitivity_rows if estimate.get("scope") == "sensitivity"
            ) / area if area > 0 else None)
            uncertainty_kind = "N/D — há apenas sensibilidade parcial, não incerteza total"
        elif rows:
            missing = sorted({str(estimate.get("kind") or "incerteza não quantificada")
                              for row in rows
                              for estimate in [uncertainty_for_pool(row)]
                              if estimate.get("absolute_tc_ha") is None})
            uncertainty_kind = "N/D — " + "; ".join(missing)

        if not rows:
            status = "N/D — nenhum estoque elegível"
        elif native_area > 0 and area + 1e-6 < native_area:
            status = "PARCIAL — cobertura quantificada inferior à área nativa"
        elif native_area <= 0:
            status = "PARCIAL — área nativa não quantificada"
        else:
            status = "QUANTIFICADO"

        output.append({
            "compartment": name,
            "tc_ha": density,
            "stock_tc": stock,
            "uncertainty_tc_ha": uncertainty,
            "uncertainty_percent": (100.0 * uncertainty / density
                                     if uncertainty is not None and density is not None and density > 0 else None),
            "uncertainty_kind": uncertainty_kind,
            "sensitivity_tc_ha": sensitivity,
            "sensitivity_percent": (100.0 * sensitivity / density
                                    if sensitivity is not None and density is not None and density > 0 else None),
            "sensitivity_kind": sensitivity_values[0].get("kind") if sensitivity_values else None,
            "area_ha": area if rows else None,
            "status": status,
        })
    return output
