"""National, evidence-constrained standing-litter inventory fallback.

Literature inventory entries are standing stocks of dry litter, NOT annual
litterfall rates. Region screen is conservative: it limits experimental
transfer to the vicinity of published plots, NOT to a precisely surveyed
study-site polygon. Unquantified spatial-transfer uncertainty is never
relabeled as IC95%. Native classes only, after exact AOI land-cover clipping.

IFN SFB 2025 corrected litter tables expose 'Profundidade' in cm; depth
cannot be converted to tonnes without independently calibrated
density/dry-mass relationships for the same phytophysiognomy. The current
public IFN dataset is therefore a contextual measurement only, not a
carbon mass fallback. Inventory-derived masses can be added once audited.
"""
from __future__ import annotations
from native_carbon import normalize

IFN_SOURCE = "https://dados.florestal.gov.br/dataset/ifn-serapilheira-por-uf_disp-set2025"
IFN_METADATA = "https://dados.florestal.gov.br/dataset/97ab0c26-c5c7-421c-8fb7-e4dab47d35ea/resource/73b79435-4759-49ca-86b0-2682e5ccb1d1/download/metadados_ifn_serapilheira_disp-set2025.pdf"
# Coordinates: (west, south, east, north). Operational proximity envelope,
# never a legal/official study boundary. Match subtype with exact tokens.
REFERENCES = (
    dict(key="CAATINGA_ARBOREA_BA_CONTENDAS",biome="caatinga",
         terms=("caatinga arborea",),
         bbox=(-42.0,-14.5,-40.0,-12.5),dry_mg_ha=5.5889,
         study="Matos (2017), UESB, Caatinga arborea NAO manejada, testemunha, Contendas do Sincora BA; tabela 1: 5.588,9 kg/ha acumulados, oito parcelas por tratamento",
         url="https://www2.uesb.br/ppg/ppgciflor/wp-content/uploads/2020/08/PRISCILA-SILVA-MATOS.pdf"),
    dict(key="FESD_ES_SUBMONTANA",biome="mata atlantica",
         terms=("floresta estacional semidecidual","submontana"),
         bbox=(-42.0,-22.0,-39.0,-19.0),dry_mg_ha=5.50,
         study="Godinho et al. (2014), CERNE, Cachoeiro de Itapemirim/ES, 12 plots, seasonal standing litter",
         url="https://doi.org/10.1590/S0104-77602014000100002"),
    dict(key="FESD_BA_MONTANA",biome="mata atlantica",
         terms=("floresta estacional semidecidual","montana"),
         bbox=(-42.5,-17.0,-38.0,-13.0),dry_mg_ha=6.30,
         study="Barbosa et al. (2017), Floresta e Ambiente, Sudoeste BA, natural montane seasonal semideciduous",
         url="https://doi.org/10.1590/2179-8087.024315"),
    dict(key="FOD_ES_TABULEIRO",biome="mata atlantica",
         terms=("floresta ombrofila densa",),
         bbox=(-41.0,-20.0,-39.0,-18.0),dry_mg_ha=4.411,
         study="Correia et al. (2016), Revista Arvore, Reserva Natural Vale, Linhares/Jaguare ES, 30 plots, primary forest",
         url="https://doi.org/10.1590/0100-67622016000100002",
         published_plusminus_mg_ha=1.389),
    dict(key="FOM_RS_ARAU",biome="mata atlantica",
         terms=("floresta ombrofila mista",),
         bbox=(-51.0,-30.0,-49.5,-28.5),dry_mg_ha=14.296,
         study="Backes et al. (2005), Acta Botanica Brasilica, Sao Francisco de Paula RS, 72 standing-litter points",
         url="https://doi.org/10.1590/S0102-33062005000100015"),
    dict(key="FED_RS_SANTA_MARIA",biome="mata atlantica",
         terms=("floresta estacional decidual",),
         bbox=(-54.5,-31.0,-52.0,-28.0),dry_mg_ha=6.70,
         study="Ciencia Florestal (1993), Santa Maria RS, standing litter mantle 6.7 t/ha; exclude annual deposition 7.76 t/ha",
         url="https://doi.org/10.5902/19805098284"),
    dict(key="CERRADO_TIPICO_DF",biome="cerrado",
         terms=("cerrado tipico",),
         bbox=(-48.5,-16.5,-47.0,-15.0),dry_mg_ha=6.08,
         study="Estoque de Serapilheira em Tres Fisionomias no Cerrado do DF (2017), Fazenda Agua Limpa, standing litter 6.08 t/ha",
         url="https://doi.org/10.1590/2179-8087.126215"),
    dict(key="MATA_GALERIA_DF",biome="cerrado",
         terms=("mata de galeria",),
         bbox=(-48.5,-16.5,-47.0,-15.0),dry_mg_ha=9.36,
         study="Estoque de Serapilheira em Tres Fisionomias no Cerrado do DF (2017), Fazenda Agua Limpa, gallery forest standing litter 9.36 t/ha",
         url="https://doi.org/10.1590/2179-8087.126215"),
    dict(key="FED_RS_ALTO_URUGUAI",biome="mata atlantica",
         terms=("floresta estacional decidual",),
         bbox=(-54.5,-28.5,-51.5,-26.0),dry_mg_ha=6.50,
         study="Turchetto e Fortes (2014), Pesquisa Florestal Brasileira/Embrapa, Medio Alto Uruguai RS, estoque seco acumulado 6.50 t/ha (nao deposicao 7.14 t/ha/ano)",
         url="https://doi.org/10.4336/2014.pfb.34.80.735"),
    dict(key="FES_RS_SUBTROPICAL",biome="mata atlantica",
         terms=("floresta estacional", "subtropical"),
         bbox=(-54.5,-31.0,-52.0,-28.0),dry_mg_ha=13.404,
         study="Revista Arvore (2015), central RS, subtropical seasonal forest, standing litter (seasonal average 13.404 t/ha)",
         url="https://www.scielo.br/j/rarv/a/nJYGrQvZgkNgKNtQpCFRdCr/"),
)

def ifn_litter_context():
    return {"source": IFN_SOURCE, "metadata":IFN_METADATA,
            "version":"IFN retificado 24/10/2025",
            "observed_variable": "Profundidade (cm), five points/UA",
            "usable_for_carbon":False,
            "reason":"IFN público mede espessura, não massa seca. É necessário modelo massa/espessura validado na mesma classe, com propagação e erro de transferência."}

def published_national_litter_component(biome, physiognomy, aoi):
    """Return an exploratory inventory-based scenario or None; never a false IC."""
    from carbon_compartments import aoi_to_wgs84
    b,p=normalize(biome),normalize(physiognomy)
    if aoi is None:
        return None
    try:
        west,south,east,north=map(float,aoi_to_wgs84(aoi).total_bounds)
    except (TypeError,ValueError,AttributeError):
        return None
    candidates=[]
    for record in REFERENCES:
        if b!=record["biome"] or not all(term in p for term in record["terms"]):
            continue
        w,s,e,n=record["bbox"]
        if not (w<=west<=east<=e and s<=south<=north<=n):
            continue
        candidates.append(record)
    if not candidates:
        return None
    # Prefer the most specific compatible descriptor, never fuzzy nearest
    # physiognomy or national mean from an ecologically unrelated class.
    best=sorted(candidates,key=lambda r:(-len(r["terms"]),r["key"]))[0]
    mean=float(best["dry_mg_ha"])
    # .47 is documented only as an experimental default fraction; the
    # 0.42-.50 range is a sensitivity envelope, NOT sampling uncertainty.
    # Published +/- numbers are retained but never assigned a probability.
    out={
       "mean_dry_mg_ha":mean,"mean_tc_ha":mean*.47,
       "range_tc_ha":[mean*.42,mean*.50],
       "carbon_fraction_experimental":0.47,
       "carbon_fraction_envelope":[.42,.50],
       "method":"Estoque de material seco gravimetricamente observado em inventario publicado, transferido EXPERIMENTALMENTE somente para a mesma fitofisionomia dentro de envelope geografico restrito. tC/ha = massa seca Mg/ha x fC; fC exploratorio 0,47; envelope de sensibilidade 0,42–0,50, SEM cobertura estatistica. Erro de transferencia, amostragem e sazonalidade N/D; NAO e medicao da AOI ou de SAR.",
       "source":best["study"],"url":best["url"],
       "source_record_id":best["key"],"source_study_bbox":best["bbox"],
       "status":"ESTIMATIVA EXPERIMENTAL INVENTARIAL REGIONAL — SEM IC95% TRANSFERIVEL",
       "origin":"EXPERIMENTAL_FISICO",
       "uncertainty_kind":"Envelope fisico de fracao de carbono; erro de extrapolacao territorial N/D; NAO e IC95% nem faixa de confianca ou intervalo preditivo",
       "n_independent_units":None,"include_in_total":False,
       "ifn_context":ifn_litter_context(),
       "evidence_type":"standing_litter_dry_mass",
    }
    if "published_plusminus_mg_ha" in best:
        out["published_plusminus_dry_mg_ha"]=best["published_plusminus_mg_ha"]
        out["spread_caveat"]="O simbolo +/- do artigo NAO foi interpretado como IC/SD/SE e nao foi incorporado ao envelope de fracao de carbono."
    return out


def inventory_litter_transfer_model(reference, *, biome, physiognomy, carbon_fraction=0.47):
    """Quantify a class-matched standing-litter transfer ONLY with audited error.

    E[L_C] = mean_dry_Mg_ha * carbon_fraction (tC/ha).
    SE[mean_dry] = SD_between_independent_units / sqrt(n_eff).
    SD[transfer prediction] = sqrt(SE[mean_dry]^2 + SD_transfer^2).
    A normal 90% predictive interval is provisional and is NOT an empirically
    verified coverage interval for a new Brazilian AOI. The carbon fraction is
    held fixed; uncertainty in it must be included by a separately calibrated
    model before claiming total uncertainty. If transfer SD is absent, do NOT
    manufacture a 90/95% CI from the study SD.
    """
    import math
    from native_carbon import normalize
    def pos(k):
        try:
            v=float(reference.get(k))
            return v if math.isfinite(v) and v>0 else None
        except (ValueError,TypeError,OverflowError):
            return None
    if not isinstance(reference,dict):
        return None
    if (normalize(reference.get("biome"))!=normalize(biome) or
        normalize(reference.get("physiognomy"))!=normalize(physiognomy)):
        return None
    mean=pos("standing_dry_mass_mg_ha")
    if mean is None or reference.get("measurement")!="standing_litter_dry_mass":
        return None
    if not (0.35<=carbon_fraction<=0.60):
        return None
    if not reference.get("source_url") or not reference.get("institution"):
        return None
    if reference.get("source_tier") not in ("microrregional","regional"):
        return None
    result={
        "mean_dry_mg_ha":mean,"mean_tc_ha":mean*carbon_fraction,
        "source":reference["institution"]+" — "+reference["source_url"],
        "source_url":reference["source_url"],
        "source_tier":reference["source_tier"],
        "origin":"EXPERIMENTAL_FISICO",
        "include_in_total":False,
        "evidence_type":"standing_litter_dry_mass",
        "method":("Transferência de massa seca observada apenas para a mesma fitofisionomia; "
                  "estoque tC/ha = Mg seco/ha × fração de C. Não substituir estoque por "
                  "fluxo de queda anual, espessura IFN ou biomassa lenhosa."),
        "uncertainty_kind":"Erro de transferência não quantificado; IC95% indisponível",
        "scientifically_homologated":False,
    }
    n=pos("independent_sample_units")
    sd=pos("dry_mass_sd_mg_ha")
    transfer=pos("externally_validated_transfer_sd_mg_ha")
    if (n is not None and n>=5 and sd is not None and transfer is not None
        and reference.get("transfer_validation_independent") is True
        and reference.get("transfer_validation_physiognomy")==physiognomy
        and reference.get("transfer_validation_region")):
        se=sd/math.sqrt(n)
        predictive_sd=math.sqrt(se*se+transfer*transfer)
        out_lower=max(0.0,(mean-1.6448536269514722*predictive_sd)*carbon_fraction)
        out_upper=(mean+1.6448536269514722*predictive_sd)*carbon_fraction
        result.update(
            range_tc_ha=[out_lower,out_upper],
            inventory_sample_mean_se_dry_mg_ha=se,
            transfer_sd_dry_mg_ha=transfer,
            uncertainty_kind=("Intervalo preditivo normal 90% CONDICIONAL a desvio-padrão "
                              "de transferência estimado em validação independente; não é "
                              "IC95% nem comprovação de cobertura na AOI."),
            status="ESTIMATIVA EXPERIMENTAL COM INFERÊNCIA DE TRANSFERÊNCIA AUDITÁVEL")
    else:
        result["status"]="ESTIMATIVA EXPERIMENTAL SEM ERRO DE TRANSFERÊNCIA VERIFICADO"
        result["uncertainty_missing"]=(
            "Exigir n independente, SD de estoque seco, SD de transferência "
            "validado externamente na mesma fitofisionomia e domínio regional.")
    return result
