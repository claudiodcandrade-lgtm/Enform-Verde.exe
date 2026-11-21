"""Priority hierarchy for crop identifiers (user rule, 2026-11-03).

1. Brazilian models/algorithms (Embrapa — any unit —, ESALQ/USP, UFV, UFLA,
   INPE, UNICAMP, INPA and similar Brazilian institutions);
2. if none is usable: models developed for African savannas, CIRAD first;
3. if still none: models from any region, from solid peer-reviewed work.

Experimental models are allowed only when (a) the uncertainty is quantifiable
— an independently measured accuracy with its sample size, so a Wilson 95 %
interval can be computed — and (b) the mathematics is auditable: documented
method, predictor manifest and an executable artefact identified by SHA-256.

A higher tier is never skipped silently: every rejected higher-tier candidate
is returned with its reason. Without any usable model the output is
"área cultivada — cultura não identificada" (N/D), never a guessed crop.
"""
from __future__ import annotations

import math
import unicodedata

BRAZIL_KEYWORDS = ("embrapa", "esalq", "usp", "universidade de sao paulo", "ufv", "vicosa",
                   "ufla", "lavras", "inpe", "unicamp", "campinas", "inpa", "unesp", "ufrgs",
                   "ufg", "ufmt", "ufpr", "ufsm", "ufmg", "unb", "puc-rio", "iac ",
                   "instituto agronomico", "conab", "ibge", "brazil", "brasil")
AFRICA_KEYWORDS = ("cirad", "isra", "inera", "fofifa", "agrhymet", "icrisat", "iita", "ier mali",
                   "senegal", "burkina", "mali", "niger", "madagascar", "kenya", "ghana",
                   "nigeria", "zambia", "malawi", "mozambique", "tanzania", "ethiopia")
TIER_LABEL = {1: "Brasil (instituição brasileira)",
              2: "Savanas africanas (CIRAD com prioridade)",
              3: "Internacional (publicação científica sólida)"}


def _norm(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return text.casefold()


def tier_of(candidate):
    """Return (tier, sub_rank). sub_rank 0 = CIRAD inside tier 2."""
    origin = _norm(candidate.get("origin"))
    inst = _norm(candidate.get("institution"))
    if origin == "brazil" or any(k in inst for k in BRAZIL_KEYWORDS):
        return 1, 0
    if origin == "african_savanna" or any(k in inst for k in AFRICA_KEYWORDS):
        return 2, (0 if "cirad" in inst else 1)
    return 3, 0


def wilson_interval(correct, n, z=1.959963984540054):
    if n <= 0 or not 0 <= correct <= n:
        raise ValueError("invalid counts")
    p = correct / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def usability(candidate, status):
    """Decide whether a candidate can run, and with which uncertainty.

    ``status`` is what the installation actually has for this candidate:
    artifact_sha256, artifact_verified (hash re-checked on disk), predictor_manifest,
    method_documented, accuracy (fraction), n_independent (int), validation_scope
    ('brazil_independent' | 'published_original_domain'), crop.
    """
    reasons = []
    s = status or {}
    digest = str(s.get("artifact_sha256") or "")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
        reasons.append("sem artefato executável identificado por SHA-256")
    if s.get("artifact_verified") is not True:
        reasons.append("hash do artefato não reconferido no disco")
    if not s.get("predictor_manifest"):
        reasons.append("sem manifesto de preditores (matemática não auditável)")
    if not (s.get("method_documented") or candidate.get("method")):
        reasons.append("método não documentado")
    acc, n = s.get("accuracy"), s.get("n_independent")
    interval = None
    try:
        acc = float(acc); n = int(n)
        if not (0 <= acc <= 1 and n > 0):
            raise ValueError
        interval = wilson_interval(round(acc * n), n)
    except (TypeError, ValueError):
        reasons.append("incerteza não quantificável: falta acurácia independente com n")
    scope = s.get("validation_scope")
    if scope not in ("brazil_independent", "published_original_domain"):
        reasons.append("escopo de validação não declarado")
    usable = not reasons
    return {"usable": usable, "reasons": reasons,
            "status": ("validated_brazil" if usable and scope == "brazil_independent"
                       else "experimental_transfer" if usable else "not_usable"),
            "accuracy": acc if interval else None, "n_independent": n if interval else None,
            "accuracy_wilson95": interval,
            "transfer_error_quantified": usable and scope == "brazil_independent"}


def select_identifier(crop, candidates, statuses):
    """Pick the identifier following the tier rule.

    candidates: iterable of registry dicts (id, institution, origin, crops, ...).
    statuses: {candidate_id: installation status} — absent means not installed.
    """
    pool = [c for c in candidates if crop in c.get("crops", ())]
    ranked = []
    for c in pool:
        tier, sub = tier_of(c)
        use = usability(c, (statuses or {}).get(c["id"]))
        lower = use["accuracy_wilson95"][0] if use["accuracy_wilson95"] else -1.0
        ranked.append((tier, sub, -lower, c["id"], c, use))
    ranked.sort(key=lambda r: r[:4])
    trail = []
    for tier, sub, _, cid, c, use in ranked:
        if use["usable"]:
            return {"crop": crop, "selected": cid, "tier": tier, "tier_label": TIER_LABEL[tier],
                    "institution": c.get("institution"), "status": use["status"],
                    "accuracy_wilson95": use["accuracy_wilson95"],
                    "transfer_error_quantified": use["transfer_error_quantified"],
                    "label_allowed": True, "rejected_higher_priority": trail,
                    "note": ("Modelo experimental: acurácia medida fora do domínio brasileiro; "
                             "erro de transferência ainda não medido no Brasil."
                             if use["status"] == "experimental_transfer" else
                             "Validação independente no Brasil declarada.")}
        trail.append({"id": cid, "tier": tier, "institution": c.get("institution"),
                      "reasons": use["reasons"]})
    return {"crop": crop, "selected": None, "tier": None, "label_allowed": False,
            "status": "not_available", "rejected_higher_priority": trail,
            "output_label": "Área cultivada — cultura não identificada (sem identificador utilizável)"}
