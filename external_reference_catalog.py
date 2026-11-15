"""Governed selection of external reference datasets for SAR validation.

Catalogue status is NEVER evidence that a trained model passed validation.
Inputs are metadata only; no pseudo labels may be silently promoted to field truth.
"""
from __future__ import annotations

REFERENCE_SOURCES = {
 "goiatuba_2025_field":{"tier":"A","classes":"crops, pasture, native (verify labels)","url":"https://doi.org/10.5281/zenodo.17612590"},
 "worldcereal_reference":{"tier":"A_conditional","classes":"Brazilian crop reference subsets (verify provenance)","url":"https://esa-worldcereal.org/en/reference-data"},
 "sc_rice":{"tier":"A_conditional","classes":"Arroz","url":"https://doi.org/10.17632/3n8ms32thw.2"},
 "sfb_ifn":{"tier":"A_conditional","classes":"land use and exotic species","url":"https://dados.florestal.gov.br/"},
 "embrapa_silviculture":{"tier":"A_conditional","classes":"Eucalipto, Pinus (subject to release of plot-level records)","url":"https://www.embrapa.br/"},
 "mapbiomas_validation":{"tier":"B","classes":"interpreted land cover; NOT automatic field truth for genus","url":"https://brasil.mapbiomas.org/downloads/pontos-de-validacao/"},
 "conab_maps":{"tier":"C","classes":"crop maps (method-specific)","url":"https://www.gov.br/conab/pt-br"},
 "trazo_fields":{"tier":"C","classes":"field boundaries NOT crop truth","url":"https://source.coop/wri-data-lab/trazofields"}
}

def select_validation_source(source_id, *, records_available=False,
                             independently_audited=False,
                             model_training_overlap=False):
    row=REFERENCE_SOURCES[source_id]
    eligible=(row["tier"].startswith("A") and records_available
              and independently_audited and not model_training_overlap)
    return {"source_id":source_id,"source":row["url"],"tier":row["tier"],
            "eligible_for_independent_test":bool(eligible),
            "status":"READY_FOR_PAIRED_SAR_TEST" if eligible else "REFERENCE_ONLY",
            "reason":("A fonte isolada não comprova acurácia do Enform Verde."
                      if not eligible else "Ainda requer previsões SAR reais e estatística por classe.")}
