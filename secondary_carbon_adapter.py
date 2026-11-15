"""Optional, class-exact secondary carbon fallback, never replacing native SAR.

The existing native-carbon estimators keep precedence. This module only fills
missing compartments with independently documented inventory evidence, and
reports descriptive/conditional uncertainty separately from homologated CIs.

Inputs are explicitly supplied licensed records. It does NOT invent national
default stocks, use biome means as fitophysiognomy evidence, download data or
turn the existence of a bibliography entry into a plot observation.
"""
from __future__ import annotations

from evidence_hierarchy import select_stock_evidence

CARBON_FACTOR = 0.47  # existing application operational fraction; conditional


def _row(component, picked, conversion=1.0):
    value = picked["stock"] * conversion
    lo, hi = [x * conversion for x in picked["range"]]
    return {
        "parametro": component, "tc": value,
        "origem": "ESTIMATIVA_SECUNDARIA_COM_FAIXA",
        "fonte": picked["source"], "fonte_url": picked["source_url"],
        "metodo": ("Referência compatível por bioma e fitofisionomia, seleção "
                   "microrregional prioritária; erro de transferência explícito"),
        "obs": (picked["uncertainty_kind"]
                + "; FAIXA DESCRITIVA, não IC95% do imóvel"
                + ("; fração C fixa 0,47 (incerteza adicional não quantificada)"
                   if conversion != 1.0 else "")),
        "range_tc_ha": [lo, hi],
        "uncertainty_kind": picked["uncertainty_kind"],
        "confidence_interval_validated": False,
        "scientifically_homologated": False,
        "geographic_tier": picked["geographic_tier"],
        "evidence_level": picked["evidence_level"],
        "transfer_uncertainty_source": picked.get("transfer_validation"),
    }


def secondary_native_components(evidence, *, biome, physiognomy):
    """Return optional formatted components plus rejection/coverage diagnostics.

    'Necromassa aérea' is emitted only after BOTH directly measured standing
    and downed carbon stocks are independently resolved; a partial deadwood
    reference is never silently represented as complete aerial necromass.
    """
    if not isinstance(evidence, (list, tuple)):
        raise ValueError("inventory evidence must be an explicit record list")
    specs = {
        "agb": ("Biomassa aérea", "Mg/ha", CARBON_FACTOR),
        "roots": ("Biomassa subterrânea", "tC/ha", 1.0),
        "litter": ("Serapilheira", "tC/ha", 1.0),
        "soil_0_100": ("Solo 0–100 cm", "tC/ha", 1.0),
        "standing_deadwood": ("Necromassa em pé", "tC/ha", 1.0),
        "downed_deadwood": ("Necromassa caída", "tC/ha", 1.0),
    }
    selected = {}
    audit = {}
    for pool, (label, unit, factor) in specs.items():
        item = select_stock_evidence(
            evidence, biome=biome, physiognomy=physiognomy,
            pool=pool, unit=unit)
        audit[pool] = {
            "available": item["available"], "reason": item.get("reason"),
            "rejections": item.get("rejections", []),
            "source": item.get("source"),
            "uncertainty_kind": item.get("uncertainty_kind"),
        }
        if item["available"]:
            selected[pool] = _row(label, item, factor)
    rows = [selected[k] for k in ("agb", "roots", "litter", "soil_0_100")
            if k in selected]
    standing, downed = selected.get("standing_deadwood"), selected.get("downed_deadwood")
    if standing and downed:
        rows.append({
            "parametro": "Necromassa aérea",
            "tc": standing["tc"] + downed["tc"],
            "origem": "ESTIMATIVA_SECUNDARIA_COM_FAIXA",
            "fonte": standing["fonte"] + "; " + downed["fonte"],
            "metodo": "Soma de inventários compatíveis de madeira morta em pé e caída, sem sobreposição",
            "obs": ("Soma conservadora dos envelopes marginais; covariância e cobertura "
                    "conjunta não verificadas; NÃO é IC95% da AOI"),
            "range_tc_ha": [
                standing["range_tc_ha"][0] + downed["range_tc_ha"][0],
                standing["range_tc_ha"][1] + downed["range_tc_ha"][1],
            ],
            "confidence_interval_validated": False,
            "scientifically_homologated": False,
            "subpools": ["standing_deadwood", "downed_deadwood"],
        })
    elif standing or downed:
        audit["deadwood_partial"] = (
            "Um subcompartimento medido; necromassa aérea TOTAL não calculada "
            "por ausência do outro subcompartimento")
    return {"components": rows, "audit": audit,
            "status": "EXPERIMENTAL_SECONDARY_STOCKS_NOT_HOMOLOGATED"}
