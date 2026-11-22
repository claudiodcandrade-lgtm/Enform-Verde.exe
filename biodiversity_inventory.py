"""Microregional phytosociology summaries for the executive panel.

Only compatible, licensed inventory records are summarized. The qualitative
species list ranks taxa by mean basal-area dominance in the regional plots;
it describes likely occurrence, never observations made on the property.
"""
from __future__ import annotations

import csv
import math
import unicodedata
from collections import Counter, defaultdict


REQUIRED = {
    "inventory_id", "plot_id", "plot_area_ha", "biome", "physiognomy",
    "microregion", "species", "dbh_cm", "status", "inclusion_threshold_dap_cm",
    "sampling_design", "institution", "source_url", "licensed_for_use",
}
DBH_BINS_CM = ((5.0, 10.0), (10.0, 20.0), (20.0, 30.0),
               (30.0, 40.0), (40.0, 60.0), (60.0, math.inf))
HEIGHT_BINS_M = ((0.0, 5.0), (5.0, 10.0), (10.0, 15.0), (15.0, 20.0),
                 (20.0, 25.0), (25.0, 30.0), (30.0, 35.0), (35.0, 40.0),
                 (40.0, 45.0), (45.0, 50.0), (50.0, 55.0), (55.0, 60.0),
                 (60.0, math.inf))


def plot_agb_reference_chave2014(records, *, plot_area_ha):
    """Create an inventory plot AGB response using the published Chave model.

    Per-tree AGB (kg) = 0.0673 * (rho * D^2 * H)^0.976, with D in cm,
    H in m and wood density rho in g cm-3. This is an inventory-derived
    calibration response, not a property estimate or a claim of local model
    validation. Missing tree heights/densities are never imputed here.
    """
    area = float(plot_area_ha)
    if not math.isfinite(area) or area <= 0:
        raise ValueError("Área de parcela inválida")
    live = [r for r in records if _norm(r.get("status")) in {"alive", "viva", "vivo", "live"}]
    if not live:
        raise ValueError("Parcela sem árvores vivas elegíveis")
    total_kg = 0.0
    for row in live:
        try:
            d = float(row["dbh_cm"])
            h = float(row["height_m"])
            rho = float(row["wood_density_g_cm3"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Alometria Chave 2014 requer DAP, altura medida e densidade da madeira por árvore") from exc
        if not all(math.isfinite(x) and x > 0 for x in (d, h, rho)):
            raise ValueError("DAP, altura e densidade devem ser positivos e finitos")
        total_kg += 0.0673 * (rho * d * d * h) ** 0.976
    return {
        "agb_ref_mg_ha": total_kg / 1000.0 / area,
        "model": "Chave et al. 2014 pantropical tree-level allometry",
        "formula": "0.0673 × (ρ × DAP² × H)^0.976",
        "units": {"dbh": "cm", "height": "m", "wood_density": "g/cm³", "output": "Mg/ha"},
        "n_live_trees": len(live),
        "property_observation": False,
        "status": "REFERENCIA_ALOMETRICA_DE_INVENTARIO_NAO_VALIDACAO_LOCAL",
        "uncertainty_note": "Propagar incerteza de alometria, densidade, altura, amostragem e transferência; esta função não calcula esses componentes.",
    }


def _dbh_bin_id(low, high):
    return f"dbh_{int(low)}_{'plus' if math.isinf(high) else int(high)}_cm"


def load_biodiversity_inventory_csv(path, *, max_rows=500_000):
    """Read and validate a harmonized, licensed tree-level inventory CSV."""
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError("CSV fitossociológico sem campos obrigatórios: " + ", ".join(missing))
        rows = []
        for line, row in enumerate(reader, start=2):
            if line > max_rows + 1:
                raise ValueError(f"CSV excede o limite de {max_rows} registros")
            if str(row.get("licensed_for_use", "")).strip().casefold() not in {"true", "1", "sim", "yes"}:
                raise ValueError(f"linha {line}: licença de uso não confirmada")
            try:
                area = float(row["plot_area_ha"])
                dbh = float(row["dbh_cm"])
                threshold = float(row["inclusion_threshold_dap_cm"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"linha {line}: área, DAP ou limite de inclusão inválido") from exc
            if not all(math.isfinite(x) for x in (area, dbh, threshold)) or area <= 0 or dbh < threshold:
                raise ValueError(f"linha {line}: registro fora do limite/área de parcela")
            if not all(str(row.get(k, "")).strip() for k in
                       ("inventory_id", "plot_id", "biome", "physiognomy", "microregion", "status", "institution", "source_url")):
                raise ValueError(f"linha {line}: proveniência, parcela ou taxonomia ausente")
            published=str(row.get("species") or row.get("scientific_name") or "").strip()
            scientific=str(row.get("scientific_name") or "").strip()
            if not published:
                raise ValueError(f"linha {line}: nome científico/táxon ausente")
            # A legacy `species` field may contain a vernacular or an
            # unnormalized label. Preserve it for grouping, but never relabel
            # it as a scientific name unless the source supplied that field.
            row["name_as_published"]=published
            row["scientific_name"]=scientific or "N/D — fonte sem nome científico explícito"
            row["common_name"]=str(row.get("common_name") or "N/D — não informado no inventário").strip()
            row["species"]=scientific
            rows.append(dict(row))
    if not rows:
        raise ValueError("CSV fitossociológico sem árvores válidas")
    return rows


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(c for c in text if c.isalnum() and not unicodedata.combining(c))


def _t_critical_975(df):
    table = (12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262,
             2.228, 2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101,
             2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052,
             2.048, 2.045, 2.042)
    return table[df - 1] if 1 <= df <= len(table) else 1.96


def summarize_top10_species(records, *, biome, physiognomy, microregion):
    """Rank species by plot incidence; report plot-level basal-area means.

    A 95% t interval is emitted only for declared simple-random, equal-weight
    independent plots. It is a source-region sampling interval, not an AOI
    transfer interval. All-species basal area remains the stand estimate.
    """
    if not records:
        return {"status": "N/D", "reason": "INVENTARIO_FITOSSOCIOLOGICO_NAO_CARREGADO"}
    wanted = (_norm(biome), _norm(physiognomy), _norm(microregion))
    selected = [r for r in records if (_norm(r.get("biome")), _norm(r.get("physiognomy")),
                                       _norm(r.get("microregion"))) == wanted]
    scope = "MICRORREGIONAL"
    # If there is no matching microregion, widen only the geographic scope;
    # biome and physiognomy remain exact. This is an explicit regional
    # reference, never a silent transfer across vegetation types.
    if not selected:
        selected = [r for r in records if (_norm(r.get("biome")),
                                             _norm(r.get("physiognomy"))) == wanted[:2]]
        scope = "REGIONAL"
    if not selected:
        return {"status": "N/D", "reason": "SEM_INVENTARIO_COMPATIVEL_NA_FITOFISIONOMIA_E_MICRORREGIAO",
                "target": {"biome": biome, "physiognomy": physiognomy, "microregion": microregion}}
    designs = {_norm(r.get("sampling_design")) for r in selected}
    thresholds = {float(r["inclusion_threshold_dap_cm"]) for r in selected}
    plot_area = {}
    plots = defaultdict(list)
    for row in selected:
        key = (str(row["inventory_id"]), str(row["plot_id"]))
        area = float(row["plot_area_ha"])
        if key in plot_area and not math.isclose(plot_area[key], area, rel_tol=0, abs_tol=1e-10):
            return {"status": "N/D", "reason": "AREA_DA_PARCELA_INCONSISTENTE", "plot": key}
        plot_area[key] = area
        plots[key].append(row)
    if len(thresholds) != 1:
        return {"status": "N/D", "reason": "LIMITES_DAP_INCOMPATIVEIS_ENTRE_FONTES"}
    plot_ids = sorted(plots)
    nplots = len(plot_ids)
    equal_plot_area = all(math.isclose(plot_area[pid], plot_area[plot_ids[0]], rel_tol=0, abs_tol=1e-10)
                          for pid in plot_ids)
    ci_eligible = designs == {"simplerandom"} and equal_plot_area
    species_plots = defaultdict(set)
    species_ba = defaultdict(lambda: [0.0] * nplots)
    species_common = defaultdict(Counter)
    total_ba = [0.0] * nplots
    dbh_distribution = { _dbh_bin_id(lo, hi): {"lower_cm": lo,
        "upper_cm": (None if math.isinf(hi) else hi), "stems_ha_by_plot": [0.0] * nplots,
        "basal_area_m2_ha_by_plot": [0.0] * nplots} for lo, hi in DBH_BINS_CM }
    stems = Counter()
    sources = {}
    for index, pid in enumerate(plot_ids):
        for row in plots[pid]:
            if _norm(row.get("status")) not in {"alive", "viva", "vivo", "live"}:
                continue
            sp = str(row.get("scientific_name") or "").strip()
            if not sp or sp.startswith("N/D"):
                sp = str(row.get("name_as_published") or row.get("species") or "").strip()
            common=str(row.get("common_name") or "N/D — não informado no inventário").strip()
            if common and not common.startswith("N/D"):species_common[sp][common]+=1
            d = float(row["dbh_cm"])
            ba = math.pi * (d / 200.0) ** 2 / plot_area[pid]
            species_plots[sp].add(pid)
            species_ba[sp][index] += ba
            total_ba[index] += ba
            for lo, hi in DBH_BINS_CM:
                if lo <= d < hi:
                    key = _dbh_bin_id(lo, hi)
                    dbh_distribution[key]["stems_ha_by_plot"][index] += 1.0 / plot_area[pid]
                    dbh_distribution[key]["basal_area_m2_ha_by_plot"][index] += ba
                    break
            stems[sp] += 1
            sources[(row["institution"], row["source_url"])] = None
    mean_total = sum(total_ba) / nplots
    # Forestry dominance is represented by mean species basal area (m²/ha).
    # Plot incidence/frequency is shown alongside it, but does not determine rank.
    ranked = sorted(species_plots, key=lambda sp: (-sum(species_ba[sp]) / nplots, -len(species_plots[sp]), _norm(sp)))
    top = []
    for sp in ranked[:10]:
        vals = species_ba[sp]
        mean = sum(vals) / nplots
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (nplots - 1)) if nplots > 1 else None
        interval = None
        if nplots > 1 and ci_eligible:
            half = _t_critical_975(nplots - 1) * sd / math.sqrt(nplots)
            interval = [max(0.0, mean - half), mean + half]
        mean_ba=mean
        common=(species_common[sp].most_common(1)[0][0] if species_common[sp]
                else "N/D — não informado no inventário")
        representative=max((r for pid in plot_ids for r in plots[pid]
                            if str(r.get("scientific_name") or "").strip()==sp),
                           key=lambda r: len(str(r.get("scientific_name") or "")), default=None)
        scientific=(str(representative.get("scientific_name") or "").strip()
                    if representative else "N/D — fonte sem nome científico explícito")
        top.append({"species": sp,"name_as_published":sp,"scientific_name":scientific,"common_name":common,
                    "dominance_basis":"área basal média da espécie nas parcelas (m²/ha)",
                    "mean_basal_area_m2_ha":mean_ba,
                    "relative_dominance_pct":100*mean_ba/mean_total if mean_total>0 else None,
                    "plot_incidence_n": len(species_plots[sp]),
                    "frequency_pct": 100 * len(species_plots[sp]) / nplots,
                    "sd_between_plots_m2_ha": sd,
                    "ci95_source_region_m2_ha": interval})
    sd_total = math.sqrt(sum((v - mean_total) ** 2 for v in total_ba) / (nplots - 1)) if nplots > 1 else None
    total_ci = None
    if nplots > 1 and ci_eligible:
        half = _t_critical_975(nplots - 1) * sd_total / math.sqrt(nplots)
        total_ci = [max(0.0, mean_total - half), mean_total + half]
    distribution_rows=[]
    for bin_id, item in dbh_distribution.items():
        ba_values=item["basal_area_m2_ha_by_plot"]
        stem_values=item["stems_ha_by_plot"]
        ba_mean=sum(ba_values)/nplots
        stem_mean=sum(stem_values)/nplots
        ba_sd=math.sqrt(sum((v-ba_mean)**2 for v in ba_values)/(nplots-1)) if nplots>1 else None
        ba_ci=None
        if nplots>1 and ci_eligible:
            half=_t_critical_975(nplots-1)*ba_sd/math.sqrt(nplots)
            ba_ci=[max(0.0,ba_mean-half),ba_mean+half]
        distribution_rows.append({"bin_id":bin_id,"lower_cm":item["lower_cm"],"upper_cm":item["upper_cm"],
            "mean_stems_ha":stem_mean,"mean_basal_area_m2_ha":ba_mean,
            "sd_basal_area_between_plots_m2_ha":ba_sd,"ci95_source_region_m2_ha":ba_ci})
    counts = [n for n in stems.values() if n > 0]
    nstems = sum(counts)
    shannon = -sum((n / nstems) * math.log(n / nstems) for n in counts) if nstems else None
    height_rows=[]
    height_complete=True
    for pid in plot_ids:
        heights=[]
        for row in plots[pid]:
            if _norm(row.get("status")) not in {"alive", "viva", "vivo", "live"}:
                continue
            try:
                value=float(row.get("height_m"))
            except (TypeError,ValueError):
                height_complete=False;break
            if not math.isfinite(value) or value<0:
                height_complete=False;break
            heights.append(value)
        if not height_complete:break
        if heights:
            counts_h=[sum(lo<=v<hi for v in heights) for lo,hi in HEIGHT_BINS_M]
            height_rows.append([100*c/len(heights) for c in counts_h])
    height_distribution=None
    if height_complete and height_rows:
        height_distribution={"status":"REFERENCIA_ALTURA_INVENTARIO_REGIONAL",
            "method":"frequência média por parcela das alturas medidas em árvores; não é altura de dossel SAR",
            "n_plots":len(height_rows),"n_live_trees":sum(sum(r["status"].casefold() in {"alive","viva","vivo","live"} for r in plots[pid]) for pid in plot_ids),
            "bins":[{"lower_m":lo,"upper_m":(None if math.isinf(hi) else hi),
                "label":(f"{int(lo)}–{int(hi)} m" if math.isfinite(hi) else "≥60 m"),
                "mean_frequency_pct":sum(row[i] for row in height_rows)/len(height_rows)}
                for i,(lo,hi) in enumerate(HEIGHT_BINS_M)],
            "source_scope":"inventário compatível por bioma, fitofisionomia e microrregião; média regional, não observação da propriedade"}
    else:
        height_distribution={"status":"N/D","reason":"ALTURAS_MEDIDAS_INCOMPLETAS_NO_INVENTARIO_COMPATIVEL" if not height_complete else "ALTURAS_MEDIDAS_NAO_DISPONIVEIS_NO_INVENTARIO_COMPATIVEL"}
    return {
        "status": "REFERENCIA_FITOSSOCIOLOGICA_REGIONAL",
        "biome": biome, "physiognomy": physiognomy, "microregion": microregion,
        "geographic_scope": scope,
        "source_microregions": sorted({str(r.get("microregion") or "N/D") for r in selected}),
        "inventory_n_plots": nplots, "inventory_n_live_stems": nstems,
        "species_richness_observed": len(species_plots), "shannon_h_descriptive": shannon,
        "inclusion_threshold_dap_cm": next(iter(thresholds)),
        "top10_by_dominance": top,
        "top10_by_plot_incidence": top,  # compatibility alias; order is now dominance rank
        "species_occurrence_label":"espécies de ocorrência mais provável",
        "top10_mean_basal_area_sum_m2_ha": sum(x["mean_basal_area_m2_ha"] for x in top),
        "community_mean_basal_area_m2_ha": mean_total,
        "community_sd_between_plots_m2_ha": sd_total,
        "community_ci95_source_region_m2_ha": total_ci,
        "dbh_distribution_scheme_id": "dbh_5_10_20_30_40_60plus_v2_total_ba_plus_class_shares",
        "dbh_distribution_by_plot_mean": distribution_rows,
        "inventory_tree_height_distribution":height_distribution,
        "interval_scope": "IC95 amostral da região de origem apenas; incerteza de transferência para a propriedade não quantificada",
        "sampling_design": sorted(designs),
        "institutions": sorted({k[0] for k in sources}),
        "source_urls": sorted({k[1] for k in sources}),
        "property_observation": False,
        "interpretation": "Lista qualitativa de espécies de ocorrência mais provável, priorizando agregação de inventários da mesma fitofisionomia e microrregião; quando ausente, amplia para mesma fitofisionomia e bioma e identifica o escopo regional. Rankeada por dominância em área basal média por parcela, incluindo parcelas sem a espécie como zero. Nome vulgar e científico são apresentados somente quando informados ou normalizados com proveniência; nome ambíguo permanece como publicado e não é promovido a nome científico. A estimativa da comunidade inclui todas as espécies; top 10 não é inventário da propriedade nem substitui espécies raras.",
    }
