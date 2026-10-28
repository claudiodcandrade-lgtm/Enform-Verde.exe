"""International SAR crop-model and thesis discovery with transferability gates.

A literature model is NOT a trained model artifact. Candidate lookup never
authorizes a crop label, pixel map, yield forecast or disease diagnosis.
"""
from __future__ import annotations
import math

# Institution and canonical publication/repository URLs verified 2026-10-28.
# "implementation" is a route proposal, NOT proof of model weights packaged.
CANDIDATES = (
    {"id":"ESA_WORLDCEREAL_2024","institution":"ESA / VITO / IIASA",
     "kind":"operational_open_source_framework","origin":"international",
     "crops":("áreas cultivadas","milho","cereais"),
     "sensors":("Sentinel-1","Sentinel-2","Landsat-8"),
     "url":"https://github.com/WorldCereal/worldcereal-classification",
     "method":"Presto transformer + custom CatBoost; global cropland default / crop heads",
     "weights_reusable":True,"note":"Default cropland model exists; exact crop heads, spatial/seasonal coverage and calibration must be checked"},
    {"id":"IRRI_RIICE_2014","institution":"International Rice Research Institute (IRRI)",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("arroz",),"sensors":("SAR C","SAR X"),
     "url":"https://www.mdpi.com/2072-4292/6/11/10773",
     "method":"Multitemporal SAR phenological descriptors for rice; RIICE",
     "weights_reusable":False,"note":"Operational case studies in Asia; local transfer not demonstrated"},
    {"id":"IRRI_ORYZA_2017","institution":"International Rice Research Institute (IRRI)",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("arroz",),"sensors":("SAR C","SAR X"),
     "url":"https://doi.org/10.1088/1755-1315/54/1/012015",
     "method":"Multitemporal SAR + ORYZA mechanistic crop growth model",
     "weights_reusable":False,"note":"Yield requires local parameterization and independent predictive calibration"},
    {"id":"NATURE_RICE_S1_2019","institution":"Scientific Data (Nature Portfolio)",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("arroz",),"sensors":("Sentinel-1",),
     "url":"https://www.nature.com/articles/s41597-019-0036-3",
     "method":"Sentinel-1 temporal Random Forest rice mapping",
     "weights_reusable":False,"note":"South Asia reference; locally validate Brazilian rice"},
    {"id":"DLR_ORYNBAIKYZY_PHD_2023","institution":"DLR / Martin-Luther-Universität Halle-Wittenberg",
     "kind":"doctoral_thesis","origin":"international",
     "crops":("áreas cultivadas",),
     "sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://elib.dlr.de/198848/",
     "method":"Combined SAR/optical crop-type classification, PhD 2023",
     "weights_reusable":False,"note":"Thesis is a method reference; no executable coefficients/weights verified"},
    {"id":"TUDELFT_NIKAEIN_PHD_2025","institution":"Delft University of Technology",
     "kind":"doctoral_thesis","origin":"international",
     "crops":("áreas cultivadas",),
     "sensors":("Sentinel-1",),
     "url":"https://repository.tudelft.nl/record/uuid:d5c77c32-2f3e-455b-9187-06c76f9abc22",
     "method":"InSAR time-series and physics-guided crop growth modeling",
     "weights_reusable":False,"note":"Investigational methods; not proof of field scale yield capability"},
    {"id":"UMD_KHAN_PHD_2023","institution":"University of Maryland",
     "kind":"doctoral_thesis","origin":"international",
     "crops":("áreas cultivadas",),
     "sensors":("Sentinel-1",),
     "url":"https://drum.lib.umd.edu/items/a0e58179-a2a0-418d-be90-ccac475b504f",
     "method":"Generalized Sentinel-1 classification for sunflower",
     "weights_reusable":False,"note":"Sunflower source does not establish specificity for the required eight crops"},
    {"id":"UNAVARRA_ARIAS_PHD_2023","institution":"Universidad Pública de Navarra",
     "kind":"doctoral_thesis","origin":"international",
     "crops":("áreas cultivadas",),"sensors":("Sentinel-1",),
     "url":"https://academica-e.unavarra.es/entities/publication/ec975a59-015b-456d-99da-cb71d82f58dd",
     "method":"Sentinel-1 agricultural field time-series approaches",
     "weights_reusable":False,"note":"Evaluate exact crop labels, temporal sampling and replicable coefficients"},
    {"id":"IPB_SUGARCANE_THESIS_2023","institution":"IPB University, Indonesia",
     "kind":"graduate_thesis","origin":"international",
     "crops":("cana-de-açúcar",),"sensors":("Sentinel-1",),
     "url":"https://repository.ipb.ac.id/handle/123456789/123546?show=full",
     "method":"Multitemporal Sentinel-1 RF sugarcane growth stage",
     "weights_reusable":False,"published_overall_accuracy_mean":0.6538,
     "published_best_month_overall_accuracy":0.7333,
     "published_accuracy_source":"https://journal.ipb.ac.id/jika/article/view/48719",
     "published_accuracy_scope":"overall across six classes / study region Yogyakarta, not sugarcane class precision",
     "note":"Published 65.38% mean overall accuracy and 73.33% best month; both usable as research evidence without an arbitrary minimum. No local transfer validation or reusable weights demonstrated"},
    {"id":"THAI_SUGARCANE_S1S2_2026","institution":"Hydro-Informatics Institute / Srinakharinwirot University",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("cana-de-açúcar",),"sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://ph01.tci-thaijo.org/index.php/jsid/article/view/266216",
     "method":"RF multisensor VV/VH and red-edge indices",
     "weights_reusable":False,"note":"SAR-only was compared; best result relied on optical+SAR"},
    {"id":"PERU_INIA_COFFEE_2026","institution":"INIA Peru",
     "kind":"institutional_study","origin":"international",
     "crops":("café",),"sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://repositorio.inia.gob.pe/items/4a63c959-5c88-4bc4-845d-8f32b1b3f28e",
     "method":"Random Forest coffee mapping, SAR and optical fusion",
     "weights_reusable":False,"note":"Peru's tropical coffee results require test on conilon and local agroforestry"},
    {"id":"USP_MANOEL_PHD_2026","institution":"Universidade de São Paulo",
     "kind":"doctoral_thesis","origin":"brazil",
     "crops":("café",),"sensors":("Sentinel-1","Sentinel-2","Landsat-8"),
     "url":"https://teses.usp.br/teses/disponiveis/8/8135/tde-08072026-125841/pt-br.html",
     "method":"Random Forest multi-year Arabica with SAR/optical fusion",
     "weights_reusable":False,"note":"Arabica domain differs from Conilon and cannot be transferred without validation"},
    {"id":"UNICAMP_COFFEE_MSC_2025","institution":"Universidade Estadual de Campinas",
     "kind":"masters_dissertation","origin":"brazil",
     "crops":("café",),"sensors":("sensor Sentinel a confirmar",),
     "url":"https://repositorio.unicamp.br/acervo/detalhe/1552081",
     "method":"Neural network coffee monoculture mapping with Sentinel sensor fusion",
     "weights_reusable":False,"note":"Check full thesis for SAR input and accessible model implementation"},
    {"id":"CHINA_CITRUS_S1S2_2024","institution":"Jiangxi University of Science and Technology / Beijing Academy of Agriculture and Forestry Sciences",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("citros",),"sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://opaj.napstic.cn/periodicalArticle/0120240501379462",
     "method":"Random Forest temporal Sentinel-1 SAR and Sentinel-2 for citrus orchards",
     "weights_reusable":False,"note":"Gannan citrus in China; 90.084% OA is not 90% class precision; not a Brazilian trained model"},
    {"id":"CHINA_CITRUS_MSC_2026","institution":"Jiangxi University of Science and Technology",
     "kind":"masters_dissertation","origin":"international",
     "crops":("citros",),"sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://cnki.istiz.org.cn/kcms/detail/detail.aspx?dbcode=CMFD&dbname=CMFD2026&filename=1025687767.nh",
     "method":"SAR VH seasonality + Sentinel-2 for citrus mapping and crop suitability",
     "weights_reusable":False,"note":"Chinese MSc thesis; verify rights and predictors; Brazilian transfer untested"},
    {"id":"TUNISIA_CITRUS_S1S2_2024","institution":"PIAHS / research team in Cap Bon, Tunisia",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("citros",),"sensors":("Sentinel-1","Sentinel-2"),
     "url":"https://piahs.copernicus.org/articles/385/443/2024/index.html",
     "method":"Comparison of 22 machine-learning classifiers for citrus with Sentinel-1/2",
     "weights_reusable":False,"note":"Multi-sensor study; no inference weights or Brazilian calibration verified"},
    {"id":"SHIZUOKA_BEAN_MAIZE_S1_2025","institution":"Shizuoka University, Japan",
     "kind":"peer_reviewed_study","origin":"international",
     "crops":("feijão","milho"),"sensors":("Sentinel-1",),
     "url":"https://www.mdpi.com/2072-4292/17/12/2095",
     "method":"Attention LSTM, GRU and TCN temporal Sentinel-1 crop classification",
     "weights_reusable":False,"note":"Beans in Japanese experiment not verified as Phaseolus vulgaris; label only after species/domain validation"},
    {"id":"PUCRIO_CROP_SAR_THESIS_2018","institution":"PUC-Rio / Maxwell repository",
     "kind":"masters_dissertation","origin":"brazil",
     "crops":("áreas cultivadas",),"sensors":("Sentinel-1",),
     "url":"https://bdtd.ibict.br/vufind/Record/PUC_RIO-1_a7e2fb231ae52f44a9f0d45fb5c25fc3",
     "method":"Multitemporal Sentinel-1 deep learning AE, CNN and FCN versus RF textures",
     "weights_reusable":False,"note":"Research included tropical/temperate datasets; check whether trained model files available"},
    {"id":"KENYATTA_SORGHUM_PHD_2024","institution":"Kenyatta University, Kenya",
     "kind":"doctoral_thesis","origin":"international",
     "crops":("sorgo",),"sensors":("EO sensor unverified",),
     "url":"https://ir-library.ku.ac.ke/items/8a55af2b-58f7-45dd-b701-8e638e7d76ed",
     "method":"Crop area, spectral signatures and microclimatic characterization for sorghum",
     "weights_reusable":False,"note":"PhD cited as agronomic reference only; SAR input not verified, cannot activate SAR classifier"},
    {"id":"UFLA_SORGHUM_MAIZE_MSC_2023","institution":"Universidade Federal de Lavras, Brazil",
     "kind":"masters_dissertation","origin":"brazil",
     "crops":("sorgo","milho"),"sensors":("vegetation indices; SAR unverified",),
     "url":"https://repositorio.ufla.br/handle/1/58272",
     "method":"Maize/sorghum remote sensing and MLP prediction of sorghum yields",
     "weights_reusable":False,"note":"Remote sensing indices; NOT shown to use SAR. May guide yield baselines only"},
)

SUPPORTED_CROPS = ("milho","soja","sorgo","café","cana-de-açúcar",
                   "arroz","feijão","citros","áreas cultivadas")
SOURCE_TYPES = frozenset(("doctoral_thesis","masters_dissertation",
                          "graduate_thesis","peer_reviewed_study",
                          "institutional_study","operational_open_source_framework"))


def candidates_for_crop(crop, *, include_general=True):
    """Identify research and training routes without claiming trained deployment."""
    if crop not in SUPPORTED_CROPS:
        raise ValueError("unsupported crop")
    names = {crop}
    if include_general and crop != "áreas cultivadas":
        names.add("áreas cultivadas")
    return [dict(m) for m in CANDIDATES if set(m["crops"]) & names]


def assess_external_model_transfer(*, candidate_id, crop, sensors, evidence):
    """Demand in-domain external artifact and Brazilian spatial/temporal holdout.

    Any independently measured and published accuracy can qualify as research
    evidence, without a minimum percentage. Published validation is distinct
    from Brazilian domain validation and from executable model weights. This
    is only provenance preflight; it never executes or authorizes a pixel label.
    """
    result = {"eligible":False,"preflight_passed":False,"errors":[],"model":candidate_id,
              "operational_label":"áreas cultivadas" if crop in SUPPORTED_CROPS else None}
    c = next((m for m in CANDIDATES if m["id"]==candidate_id),None)
    errors = result["errors"]
    if c is None:
        errors.append("unknown model reference")
        return result
    if crop not in c["crops"]:
        errors.append("crop not directly covered by candidate")
    if not isinstance(sensors,(tuple,list,set)) or not set(c["sensors"]).issubset(set(sensors)):
        errors.append("required source sensor modalities are unavailable")
    e = evidence if isinstance(evidence,dict) else {}
    for key in ("artifact_sha256","model_version","predictor_manifest",
                "training_institution","target_physiognomy","target_season"):
        if e.get(key) in (None,""):
            errors.append("missing model transfer evidence: "+key)
    digest=str(e.get("artifact_sha256") or "")
    if len(digest)!=64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
        errors.append("invalid model artifact digest")
    # Any published, measured accuracy from a recognized source may be used.
    # Do not compare metrics from different definitions or crops as equivalent.
    accuracy_key = next((key for key in ("class_precision","overall_accuracy",
                                        "published_accuracy") if e.get(key) is not None),None)
    if accuracy_key is None:
        errors.append("published quantitative accuracy is required for model research preflight")
    else:
        try:
            value=float(e[accuracy_key])
            if not math.isfinite(value) or value<0 or value>1:
                raise ValueError()
        except (TypeError,ValueError):
            errors.append("invalid reported accuracy: must be a fraction from 0 to 1")
    if not e.get("accuracy_metric") and accuracy_key!="class_precision":
        errors.append("accuracy metric definition required (e.g. overall accuracy)")
    if not (e.get("validation_source") or e.get("published_accuracy_source")):
        errors.append("source of measured accuracy required")
    if e.get("n_independent") is not None:
        try:
            if int(e["n_independent"])<=0:
                raise ValueError()
        except (TypeError,ValueError):
            errors.append("invalid independent validation sample size")
    if e.get("precision_wilson_lower95") is not None:
        try:
            bound=float(e["precision_wilson_lower95"])
            if not math.isfinite(bound) or not 0<=bound<=1:
                raise ValueError()
        except (TypeError,ValueError):
            errors.append("invalid Wilson lower interval bound")
    local=(e.get("independent_brazil_test") is True
           and e.get("temporal_holdout") is True
           and e.get("spatial_holdout") is True)
    result["validation_scope"]="independent_brazil_holdout" if local else "published_original_domain_only"
    result["accuracy_threshold"]=None
    result["measured_accuracy"]=float(e[accuracy_key]) if accuracy_key and not any("invalid reported accuracy" in x for x in errors) else None
    result["published_accuracy_source"]=e.get("validation_source") or e.get("published_accuracy_source")
    # This function screens user-supplied *claims*. It does not execute model
    # inference, validate a raster independently, or verify the supplied hashes
    # against files. Accordingly it must never grant operational eligibility.
    result["preflight_passed"]=not errors
    result["eligible"]=False
    if not errors:
        errors.append("preflight only: executable inference, applicable-domain checks and local uncertainty remain unverified")
    result["operational_label"]="áreas cultivadas"
    return result
