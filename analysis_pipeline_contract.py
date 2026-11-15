"""AOI identity and fail-closed publication contracts for analysis runs."""
from __future__ import annotations

import hashlib
import json


def geometry_hash(frame) -> str:
    """Hash canonical AOI geometry together with its declared source CRS."""
    if frame is None or getattr(frame, "empty", True):
        raise ValueError("AOI vazia; não é possível identificar a execução.")
    crs = getattr(frame, "crs", None)
    if crs is None:
        raise ValueError("CRS da AOI ausente; publicação bloqueada.")
    try:
        import shapely
        geom = frame.to_crs("EPSG:4326").geometry.make_valid().union_all()
        geom = shapely.normalize(geom)
        payload = {
            "source_crs": crs.to_wkt(),
            "canonical_crs": "EPSG:4326",
            "geometry_wkb_sha256": hashlib.sha256(geom.wkb).hexdigest(),
        }
    except Exception as exc:
        raise ValueError("Falha ao gerar hash da geometria AOI: " + type(exc).__name__) from exc
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_result_for_publication(start_hash, current_frame, result, *, required_keys=(),
                                    allow_declared_error_status=False):
    """Validate stage identity and shape before displaying results.

    A declared technical status can be displayed as a partial/N-D diagnostic
    when the caller opts in. This does not make the stage successful and does
    not permit it to supply analytical classes or values. Internal exceptions,
    stale AOIs and malformed output remain hard failures.
    """
    if not start_hash or geometry_hash(current_frame) != start_hash:
        raise ValueError("HASH_AOI_DIVERGENTE — resultado pertence a outra geometria; publicação bloqueada.")
    if not isinstance(result, dict):
        raise ValueError("RESULTADO_INVALIDO — etapa não retornou objeto estruturado.")
    if result.get("error"):
        raise ValueError("ERRO_INTERNO_NA_ETAPA — " + str(result["error"])[:300])
    status = str(result.get("status") or "").upper()
    if (status.startswith(("ERRO", "FAILED", "FAILURE"))
            and not allow_declared_error_status):
        raise ValueError("ETAPA_COM_ERRO — " + status)
    missing = [key for key in required_keys if key not in result]
    if missing:
        raise ValueError("SAIDA_INCOMPLETA — campos ausentes: " + ", ".join(missing))
    return True
