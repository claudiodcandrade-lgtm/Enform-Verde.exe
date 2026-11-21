"""Auditable worldwide crop classifier and labelled-data source catalogue.

A publicly released training set, source code, paper or pretrained backbone
does NOT by itself constitute an installed fitted classifier. Separate
executable, commercial licence, input modality, crop vocabulary, spatial
domain, recency, calibration and independent Brazilian evidence gates.

Do not assign published source accuracies to Enform predictions or use
EuroCropsML Sentinel-2 features as Sentinel-1-only input.
"""
from __future__ import annotations

from pathlib import Path
import os

PROVIDERS = (
    {
        "id": "esa_worldcereal",
        "name": "ESA WorldCereal / VITO / IIASA / Wageningen",
        "type": "executable_global_crop_pipeline",
        "code_url": "https://github.com/WorldCereal/worldcereal-classification",
        "docs_url": "https://worldcereal.github.io/worldcereal-documentation/processing/overview.html",
        "training_url": "https://zenodo.org/records/18769612",
        "license": "MIT (software); individual reference data licences differ",
        "modalities": ("Sentinel-1", "Sentinel-2", "auxiliary"),
        "execution": "openEO/CDSE or locally configured WorldCereal",
        "default_scope": "temporary cropland and supported crop types; region/season dependent",
        "crop_vocabulary_guarantee": False,
        "requires_external_processing": True,
        "requires_independent_brazil_validation": True,
        "priority": 1,
    },
    {
        "id": "agroimpacts_croptypemapper",
        "name": "Enabling Crop Analytics at Scale / agroimpacts crop type mapper",
        "type": "code_for_training_and_inference",
        "code_url": "https://github.com/agroimpacts/croptypemapper",
        "docs_url": "https://github.com/agroimpacts/croptypemapper",
        "training_url": "https://registry.opendata.aws/radiant-mlhub/",
        "license": "verify source repository and dataset/weight licence before deployment",
        "modalities": ("Sentinel-1", "Sentinel-2"),
        "execution": "locally fitted CNN/LSTM with matched S1/S2 data",
        "default_scope": "crop labels vary by fitted weights and reference dataset",
        "crop_vocabulary_guarantee": False,
        "requires_external_processing": True,
        "requires_independent_brazil_validation": True,
        "priority": 2,
    },
    {
        "id": "worldcereal_reference_data",
        "name": "ESA WorldCereal harmonized reference datasets v1.1.0",
        "type": "labelled_training_reference_only",
        "code_url": "https://github.com/WorldCereal/worldcereal-classification",
        "docs_url": "https://worldcereal.github.io/worldcereal-documentation/rdm/overview.html",
        "training_url": "https://zenodo.org/records/18769612",
        "license": "record-level CC-BY 4.0; each constituent dataset has own licence",
        "modalities": ("in-situ crop labels",),
        "execution": "training/validation reference only; not a raster classifier",
        "default_scope": "worldwide labels, availability varies by region/date",
        "crop_vocabulary_guarantee": False,
        "requires_external_processing": True,
        "requires_independent_brazil_validation": True,
        "priority": 3,
    },
    {
        "id": "radiant_ml_hub",
        "name": "Radiant Earth MLHub",
        "type": "labelled_training_reference_only",
        "code_url": "https://registry.opendata.aws/radiant-mlhub/",
        "docs_url": "https://registry.opendata.aws/radiant-mlhub/",
        "training_url": "https://registry.opendata.aws/radiant-mlhub/",
        "license": "dataset-specific licence verification mandatory",
        "modalities": ("ground truth", "Sentinel-1 dataset dependent", "Sentinel-2 dataset dependent"),
        "execution": "download suitable labelled dataset and train separately",
        "default_scope": "dataset-specific regions and crop classes",
        "crop_vocabulary_guarantee": False,
        "requires_external_processing": True,
        "requires_independent_brazil_validation": True,
        "priority": 4,
    },
    {
        "id": "eurocropsml",
        "name": "EuroCropsML / Technical University of Munich and partners",
        "type": "labelled_training_reference_only",
        "code_url": "https://github.com/dida-do/eurocropsml",
        "docs_url": "https://www.nature.com/articles/s41597-025-04952-7",
        "training_url": "https://doi.org/10.5281/zenodo.8229128",
        "license": "verify dataset item-level conditions",
        "modalities": ("Sentinel-2",),
        "execution": "optical few-shot benchmarks; NOT an SAR-trained classifier",
        "default_scope": "Europe; 706683 Sentinel-2 samples, 176 categories",
        "crop_vocabulary_guarantee": False,
        "requires_external_processing": True,
        "requires_independent_brazil_validation": True,
        "priority": 5,
    },
)


def international_crop_sources():
    return [dict(p) for p in sorted(PROVIDERS, key=lambda x: x["priority"])]


def installation_diagnostic(*, environ=None, model_dir=None):
    """Identify configured executable paths; never claim training is complete.

    No arbitrary downloads, dependencies, remote job submissions or new
    classifier weights are installed by merely listing providers.
    """
    env = os.environ if environ is None else environ
    root = Path(model_dir) if model_dir is not None else Path(
        env.get("ENFORM_SAR_MODELS_DIR") or (Path.home() / ".enform_verde" / "modelos_sar"))
    configured = root.is_dir() and any(root.glob("*.json"))
    worldcereal_head = env.get("ENFORM_WORLDCEREAL_CROPTYPE_HEAD", "").strip()
    head_available = bool(worldcereal_head and Path(worldcereal_head).is_file()
                          and Path(worldcereal_head).suffix.lower() == ".zip")
    return {
        "priority": "calibrated current SAR classifier > current SAR pixel evidence > historical MapBiomas map",
        "installed_sar_candidate_manifest": bool(configured),
        "worldcereal_custom_head_file_present": head_available,
        "worldcereal_ready_for_automatic_brazil_inference": False,
        "worldcereal_reason": (
            "Ter um head local não comprova openEO operacional, credenciais/CDSE, "
            "janelas sazonais nem desempenho transferido ao Brasil; "
            "usar worldcereal-classification em ambiente com acesso autorizado."),
        "global_sources": international_crop_sources(),
        "caveat": (
            "Código, artigos, mapas e amostras internacionais disponíveis não "
            "equivalem a pesos executáveis nem validação independente da propriedade."),
    }
