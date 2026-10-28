"""Discover locally installed, source-auditable SAR land-use model configurations.

This discovery does not download undocumented model weights, infer a crop, or
claim that published foreign-domain accuracy has been reproduced in Brazil.
The selected configuration must still PASS classify_config's actual independent
holdout on SAR pixels before it overrides a cartographic fallback.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def discover_installed_sar_configs(aoi, *, registry_dir=None, environ=None, max_candidates=6):
    """Return candidate config paths, diagnostics; reject obvious incompatible files.

    Default installation: ~/.enform_verde/modelos_sar/ativo.json followed by
    other JSON configs in that directory. Environment variables:
      ENFORM_LAND_USE_SAR_CONFIG = explicitly installed config file
      ENFORM_SAR_MODELS_DIR = alternate installed directory
    Candidate ranking here is user-active first, NOT an inferred scientific
    ranking. Actual performance must be measured by independent validation.
    """
    from shapely.geometry import shape
    from carbon_compartments import aoi_to_wgs84

    if not isinstance(max_candidates, int) or not 1 <= max_candidates <= 20:
        raise ValueError("max_candidates must be between 1 and 20")
    env = os.environ if environ is None else environ
    root = Path(registry_dir) if registry_dir is not None else Path(
        env.get("ENFORM_SAR_MODELS_DIR") or (Path.home() / ".enform_verde" / "modelos_sar")
    )
    diagnostics = []
    candidates = []
    override = str(env.get("ENFORM_LAND_USE_SAR_CONFIG", "") or "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    if root.is_dir():
        candidates.append(root / "ativo.json")
        discovered=sorted(root.glob("*.json"), key=lambda p: p.name.casefold())
        # This is a desktop analysis, not a filesystem indexer. A model store
        # with thousands of manifests must not freeze the user interface.
        if len(discovered)>50:
            diagnostics.append("Catálogo SAR com mais de 50 JSON; "
                               "apenas as primeiras configurações são examinadas.")
        candidates.extend(discovered[:50])
    else:
        diagnostics.append("Identificadores SAR não instalados no diretório " + str(root) + ".")
    seen = set()
    accepted = []
    geom = aoi_to_wgs84(aoi).geometry.union_all()
    for path in candidates:
        try:
            canonical = path.resolve()
            if canonical in seen:
                continue
            seen.add(canonical)
            if not canonical.is_file():
                if path.name != "ativo.json" or override:
                    diagnostics.append("Configuração SAR indisponível: " + str(path))
                continue
            if canonical.stat().st_size > 256 * 1024:
                raise ValueError("configuração JSON excede 256 KiB")
            raw = json.loads(canonical.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("a configuração não é um objeto JSON")
            required = ("institution", "reference_url", "publication_url", "sensor",
                        "processing", "period", "features", "classes", "domain",
                        "samples", "feature_raster")
            if any(not raw.get(k) for k in required):
                raise ValueError("faltam referências, sensor, domínio, amostras ou atributos")
            if raw.get("reference_kind") != "independent_observations":
                raise ValueError("referências não constituem observações independentes")
            if not any(isinstance(f, dict) and f.get("source") == "SAR"
                       and f.get("name") and f.get("unit") for f in raw["features"]):
                raise ValueError("sem preditores SAR documentados")
            domain = shape(raw["domain"])
            if not domain.is_valid or not domain.covers(geom):
                raise ValueError("fora do domínio espacial documentado desta AOI")
            base = canonical.parent
            for key in ("samples", "feature_raster"):
                file = (base / str(raw[key])).resolve()
                if not file.is_file() or file.stat().st_size <= 0:
                    raise ValueError("dados de inferência/validação ausentes: " + key)
            accepted.append(str(canonical))
            if len(accepted) >= max_candidates:
                diagnostics.append("Limite explícito de " + str(max_candidates) +
                                   " modelos instalados; descoberta incompleta.")
                break
        except Exception as exc:
            # Invalid user-installed geometry or damaged JSON must never crash
            # the complete AOI analysis; record the exact failure and abstain.
            diagnostics.append("Configuração SAR recusada [" + path.name + "]: " +
                               type(exc).__name__ + ": " + str(exc)[:200])
    if not accepted:
        diagnostics.append(
            "Nenhum identificador SAR executável compatível instalado; "
            "usar mapa de cobertura atual com a fonte declarada, sem atribuir "
            "classes ao SAR ou simular acurácia."
        )
    return accepted, diagnostics
