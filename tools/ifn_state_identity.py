#!/usr/bin/env python3
"""Dependency-free canonical IFN/SFB UF identity shared by acquisition and audits.

This module must be importable in scientific gate jobs that intentionally do
not install requests, openpyxl, or geospatial dependencies.
"""
import re
import unicodedata

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapa",
    "BA": "Bahia", "CE": "Ceara", "DF": "Distrito Federal", "ES": "Espirito Santo",
    "GO": "Goias", "MA": "Maranhao", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Para", "PB": "Paraiba", "PE": "Pernambuco",
    "PI": "Piaui", "PR": "Parana", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondonia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "Sao Paulo", "TO": "Tocantins",
}
def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"[^A-Z0-9]+", "_", "".join(c for c in value if not unicodedata.combining(c)).upper()).strip("_")


def canonical_state(value):
    """Normalize official IFN state codes or full state names to a two-letter UF.

    Never treat a non-empty but unrecognized state as an independent UF:
    doing so could silently inflate plot counts or conceal source conflicts.
    """
    key = norm(value)
    if not key:
        return ""
    if key in STATE_NAMES:
        return key
    matches = [code for code, name in STATE_NAMES.items() if norm(name) == key]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"unrecognized UF/estado value: {value!r}")


