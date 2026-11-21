Warning: truncated output (original token count: 48489)
Total output lines: 2778

import math,re,hashlib,time,zipfile,os
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np, requests
from scientific_calibration import SCIENTIFIC_INVENTORY_REGISTRY, saturation_audit, glcm_features, multiscale_texture, rank_external_evidence, fit_local_ensemble
from national_fallback import national_agb_fallback, inventory_fallback_gate
from sar_height_absence import secondary_cci_agb_decision
from structural_evidence import StructuralEvidence, evidence_se, random_effects_summary, harmonize_primary_plot_rows
from carbon_compartments import tapajos_litter_stock_component
ASF_SEARCH="https://api.daac.asf.alaska.edu/services/search/param"
CDSE_STAC="https://stac.dataspace.copernicus.eu/v1/search"
def _priority_height_route_state(*, cci_eligible, valid_height_pixels,
                                 fh_technical_errors=0, fh_incomplete=False):
    """Describe FH/CCI attempts without equating eligibility with success."""
    if cci_eligible and (int(fh_technical_errors or 0)>0 or fh_incomplete):
        return {"status":"FH_COM_FALHA_CCI_SEGUNDA_ROTA_TENTADA",
                "technical_error":True,"cci_promoted":False,
                "fh_technical_errors":int(fh_technical_errors or 0),
                "fh_incomplete":bool(fh_incomplete)}
    if cci_eligible:
        return {"status":"CCI_SEGUNDA_ROTA_TENTADA_SEM_AGB","technical_error":False,"cci_promoted":False}
    if int(valid_height_pixels or 0)>0:
        return {"status":"FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL","technical_error":False,"cci_promoted":False}
    return {"status":"ERRO_TECNICO_ROTA_PRIORITARIA","technical_error":True,"cci_promoted":False}


MODEL_REGISTRY=[
{"id":"ESA_BIOMASS_FP_AGB_L2B","biome":"*","physiognomy":"florestas no domínio válido do produto ESA","domain":"ESA BIOMASS Level-2B AGB; usar AGB e AGB_Std_Dev do produto, sem recalibrar como backscatter","bands":["P"],"sensor":"ESA BIOMASS P-band","algorithm":"produto geofísico oficial L2B","predictors":["AGB"],"coefficients":None,"validation":"usar metadados, máscaras/nodata e incerteza do ativo/versionamento; isso não substitui validação local","institution":"ESA","executable":True,"execution_mode":"direct_product","constraints":"exigir FP_AGB_L2B e cobertura da AOI; usar apenas pixels válidos conforme o ativo; reportar AGB_Std_Dev como incerteza fornecida pelo produto, nunca como erro local de validação; FP_FH__L2B é altura, não AGB"},
{"id":"ESA_CCI_BIOMASS_V7","biome":"*","physiognomy":"cobertura florestal global","domain":"mapa AGB CCI v7; série 2005–2012 e 2015–2024; produto EO multissensor","bands":["L","C"],"sensor":"ALOS-2 PALSAR-2 + Sentinel-1","algorithm":"BIOMASAR-L/BIOMASAR-C + fusão","predictors":["AGB"],"coefficients":None,"validation":"incerteza do produto CCI","institution":"ESA CCI Biomass","executable":True,"execution_mode":"direct_product","constraints":"produto histórico; não rotular como P-band nem como estimativa local calibrada"},
{"id":"CASINO_P_GROUND_CANCELLED_POWER_LAW","biome":"florestas tropicais (separar calibração de Caatinga)","physiognomy":"floresta tropical; limites de transferência precisam ser avaliados","domain":"CASINO/BIOMASS P-band: canopy backscatter por ground cancellation + amostras independentes com AGB; algoritmo calibrável, não coeficientes globais","bands":["P"],"sensor":"BIOMASS P-band interferométrico / produtos compatíveis","algorithm":"power law CB = k × AGB^alpha com estimação não linear robusta por cena e validação espacial agrupada","predictors":["ground_cancelled_canopy_backscatter_linear"],"coefficients":None,"validation":"publicação informa RMSD ≤27% em ao menos metade dos testes por sítio a 2,25 ha; referência independente: 142 parcelas, RMSD 20% (66 Mg/ha); airborne ESA campaigns em Guiana Francesa e Gabão","doi":"10.1016/j.rse.2020.112153","institution":"ESA / Politecnico di Milano / University of Sheffield / Chalmers","executable":False,"constraints":"não usar HH/HV comum, backscatter em dB ou PALSAR L como substitutos; exige canopy backscatter ground-cancelled e pontos nacionais pareados independentes"},
{"id":"PEREIRA_2018_VARZEA_POL","biome":"Amazônia","physiognomy":"várzea/floresta inundável","domain":"várzea amazônica; full-pol PALSAR; 18 amostras","bands":["L"],"sensor":"ALOS/PALSAR-1 PLR","algorithm":"GLM log-link com atributos polarimétricos","predictors":["V_ZD","Phi_alphaS1","Phi_alphaS2"],"coefficients":None,"r2":0.88,"rmse_mg_ha":74.59,"bias_mg_ha":-4.9,"validation":"cross-validation; erro relativo ~46%","doi":"10.3390/rs10091355","institution":"INPE/UNESP/colaboradores","executable":False,"constraints":"preditores e desempenho verificados; coeficientes numéricos não publicados na tabela principal, portanto não inventar execução"},
{"id":"PEREIRA_2018_VARZEA_XL","biome":"Amazônia","physiognomy":"várzea/floresta inundável","domain":"várzea amazônica; PALSAR + TerraSAR-X + Radarsat-2","bands":["L","X","C"],"sensor":"ALOS/PALSAR + TerraSAR-X + Radarsat-2","algorithm":"GLM multifrequência","predictors":["PL_HV_HH","RC2_HV_HH","TX_HH_dB"],"coefficients":None,"r2":0.88,"rmse_mg_ha":107.32,"bias_mg_ha":-11.4,"validation":"cross-validation","doi":"10.3390/rs10091355","institution":"INPE/UNESP/colaboradores","executable":False,"constraints":"usar para seleção/aferição; sem coeficientes publicados não executar numericamente"},

{"id":"CASSOL_2021","biome":"Amazônia","domain":"floresta secundária","bands":["L"],"sensor":"ALOS-2/PALSAR-2","doi":"10.1080/01431161.2021.1903615","institution":"INPE/NCEO"},
{"id":"CASSOL_2019_EQ13","biome":"Amazônia","physiognomy":"floresta secundária","domain":"Santarém, PA; florestas secundárias; quad-pol PALSAR-2","bands":["L"],"sensor":"ALOS-2/PALSAR-2 SLC quad-pol","algorithm":"MLR polarimétrica Eq.13","predictors":["Neumann_tau","tau_s3","T23_imag","SE_Pnorm","SE_norm","T12_realB"],"coefficients":{"intercept":-1151.1,"Neumann_tau":516.6,"tau_s3":0.96,"T23_imag":2809.1,"SE_Pnorm":592.91,"SE_norm":319.52,"T12_realB":2306.73},"r2":0.51,"rmse_mg_ha":38.7,"bias_mg_ha":2.1,"uncertainty_pct":18.6,"validation":"bootstrap 100 repetições, 80/20","doi":"10.3390/rs11010059","institution":"INPE/colaboradores","executable":True,"constraints":"somente com os seis atributos polarimétricos definidos no artigo; não aplicar a HH/HV simples"},
{"id":"NARVAES_2023_CENTRAL_AMAZON","biome":"Amazônia","physiognomy":"floresta tropical com estágios primário, exploração seletiva e sucessão; verificar equivalência local","domain":"região de Tapajós e entorno; 41 parcelas (33 calibração, 8 validação); ALOS/PALSAR full-pol L-band","spatial_domain":{"center_lon_lat":[-54.95,-3.067],"max_aoi_radius_km":35},"bands":["L"],"sensor":"ALOS/PALSAR full polarimetric","algorithm":"regressão linear múltipla, equação publicada (Eq. 4)","predictors":["sigma0_HH_db","Pv_db","alpha_S2_deg","Phi_S2_deg","Phi_S3_deg","tau_m_deg"],"predictor_units":{"sigma0_HH_db":"dB","Pv_db":"dB","alpha_S2_deg":"graus","Phi_S2_deg":"graus","Phi_S3_deg":"graus","tau_m_deg":"graus"},"coefficients":{"intercept":-1221.37,"sigma0_HH_db":-70.31,"Pv_db":1064.65,"alpha_S2_deg":6.28,"Phi_S2_deg":-2.42,"Phi_S3_deg":3.44,"tau_m_deg":6.05},"r2":0.67,"r2_validation":0.81,"rmse_mg_ha":56.9,"validation":"41 parcelas; 33 ajuste e 8 validação; Syx=56.9 Mg/ha; artigo informa R²=0.81 na validação","doi":"10.3390/f14050941","institution":"INPE / instituições colaboradoras","executable":True,"constraints":"aplicar somente a atributos extraídos de ALOS/PALSAR full-pol e dentro do geofence operacional conservador do estudo (AOI inteira a até 35 km do ponto de referência); Pv e sigma0_HH em dB, atributos Touzi em graus; não usar mosaico anual HH/HV ou Sentinel-1 dual-pol; transferência fora do Tapajós exige calibração independente"},
{"id":"VARZEA_2018","biome":"Amazônia","domain":"floresta de várzea","bands":["L","X"],"sensor":"ALOS/PALSAR + TerraSAR-X","algorithm":"regressão selecionada por CV","coefficients":None,"r2":0.46,"rmse_mg_ha":74.6,"validation":"cross-validation","doi":"10.3390/rs10091355","executable":False},
{"id":"YU_SAATCHI_2016_TROPICAL_SHRUBLAND_HV","biome":"Cerrado","physiognomy":"savana/cerrado/campo arbustivo; excluir cerradão e formações florestais densas","domain":"tropical shrubland/savanna, baixa a moderada biomassa; aplicação operacional conservadora <=100 Mg/ha e hard stop 155 Mg/ha","bands":["L"],"sensor":"ALOS/PALSAR L-band HV","algorithm":"inversão numérica de sigma0=A*x^alpha*(1-exp(-B*x))+C","predictors":["sigma0_HV_linear"],"coefficients":{"A":0.016429,"B":0.11013,"C":0.0,"alpha":0.2675},"validation":"ajuste empírico global por classe de floresta; L-band indicado principalmente para AGB <100 Mg/ha; não é calibração local brasileira","doi":"10.3390/rs8060522","institution":"NASA/JPL","executable":True,"execution_mode":"analytic_inverse","constraints":"usar somente HV L-band calibrado em potência linear; fitofisionomia savânica/arbustiva; rejeitar solução >100 Mg/ha para uso quantitativo operacional e sempre declarar incerteza de transferência"},
{"id":"CERRADO_RIO_VERMELHO_2020","biome":"Cerrado","domain":"vegetação lenhosa; Rio Vermelho","bands":["L"],"sensor":"ALOS-2/PALSAR-2 + Landsat 8 + LiDAR","algorithm":"Random Forest","coefficients":None,"r2":0.89,"rmse_mg_ha":7.58,"bias_mg_ha":0.43,"validation":"k-fold + jackknife; referência LiDAR","doi":"10.3390/rs12172685","executable":False},
{"id":"AFRICA_MITCHARD_2009_SAVANNA_L","biome":"referência externa — savana/woodland","physiognomy":"vegetação lenhosa de savana e woodland; análogo inicial somente para Cerrado aberto e de baixa biomassa","domain":"253 parcelas em quatro sítios de Camarões, Uganda e Moçambique; transferibilidade entre sítios africanos testada","bands":["L"],"sensor":"ALOS PALSAR L-band, polarização cruzada HV","algorithm":"relação empírica entre retroespalhamento HV e AGB lenhosa","predictors":["PALSAR_HV_backscatter"],"coefficients":None,"validation":"até ~150 Mg/ha: acurácia reportada de cerca de ±20%; erros aumentam com umidade, estrutura, topografia, calibração/geolocalização e alometria; validação entre sítios africanos","doi":"10.1029/2009GL040692","institution":"University of Leeds / colaboradores africanos","executable":False,"constraints":"referência de forma do modelo e domínio de baixa biomassa; não transferir coeficientes nem erro para o Cerrado; não inclui adequadamente gramíneas e fustes <10 cm; exige comparação/calibração com parcelas brasileiras"},
{"id":"AFRICA_BOUVET_2018_SAVANNA_PALSAR","biome":"referência externa — savana/woodland","physiognomy":"savanas e woodlands africanos; analogia mais plausível para savanas abertas/lenhosas do Cerrado","domain":"mapa continental 25 m; mosaico ALOS PALSAR L-band de 2010; exclui floresta densa e áreas sem vegetação; domínio reportado até ~85 Mg/ha","bands":["L"],"sensor":"ALOS PALSAR L-band","algorithm":"modelo direto backscatter–AGB e inversão Bayesiana, estratificada por sazonalidade seca/úmida","predictors":["PALSAR_backscatter","seasonal_stratum"],"coefficients":None,"validation":"cross-validation e comparação com LiDAR; RMSD reportado de 8–17 Mg/ha; métrica e validação africanas, não brasileiras","doi":"10.1016/j.rse.2017.12.030","institution":"CESBIO / instituições colaboradoras","executable":False,"constraints":"referência quantitativa para teste em baixa biomassa lenhosa; teto reportado ~85 Mg/ha e máscaras de classe; não extrapolar para cerradão, matas de galeria ou AGB total com gramíneas"},
{"id":"AFRICA_MERMOZ_2014_CAMEROON_PALSAR","biome":"referência externa — savana de Camarões","physiognomy":"savana de Camarões; análogo estrutural a testar em estratos abertos do Cerrado","domain":"mapeamento local com ALOS PALSAR e parcelas de campo; incertezas de inventário, SAR e biomassa explicitamente avaliadas","bands":["L"],"sensor":"ALOS PALSAR L-band, Fine Beam Dual Polarization e mosaico","algorithm":"regressão com parâmetros reduzidos após pré-processamento e redução de speckle","predictors":["PALSAR_backscatter","field_AGB"],"coefficients":None,"validation":"desenvolvido com dados in situ; métricas e coeficientes devem ser extraídos do artigo/suplemento antes de qualquer reprodução","doi":"10.1016/j.rse.2014.01.029","institution":"CESBIO / instituições colaboradoras","executable":False,"constraints":"benchmark metodológico, não equação transferível; recuperar texto integral/suplemento e confirmar polarizações, sazonalidade e desenho de validação"},
{"id":"AFRICA_GREATER_KRUGER_2018_PALSAR2","biome":"referência externa — savana natural","physiognomy":"savana natural do Greater Kruger, África do Sul","domain":"produto AGBD/cobertura 100 m; ALOS-2 PALSAR-2 ScanSAR, setembro de 2018; ajuste com parcelas de 1 ha de campo e LiDAR aéreo","bands":["L"],"sensor":"ALOS-2 PALSAR-2 ScanSAR","algorithm":"Power Law Model calibrado para savanas naturais; raster publicado serve como benchmark espacial","predictors":["PALSAR2_ScanSAR"],"coefficients":None,"validation":"produto NASA ORNL DAAC; independência do mapa de referência para teste cruzado a auditar antes do uso","doi":"10.3334/ORNLDAAC/2512","institution":"NASA ORNL DAAC / SavannaBio","executable":False,"constraints":"resolução 100 m e domínio de savana africana; não chamar pixels do produto publicado de parcelas nem usar o mapa como validação independente sem rastrear as parcelas/treino"},
{"id":"KUNTSCHIK_2004_CERRADAO_JERS1","biome":"Cerrado","physiognomy":"cerradão/fisionomias florestais","domain":"sudoeste de São Paulo","bands":["L"],"sensor":"JERS-1 SAR","algorithm":"regressão radar-biomassa","coefficients":None,"validation":"tese USP; equação confirmada, coeficientes pendentes de verificação integral","doi":"10.11606/T.41.2004.tde-14012005-084048","institution":"USP","executable":False},
{"id":"CAATINGA_S1_JESUS_2023","biome":"Caatinga","physiognomy":"Caatinga arbórea no Alto Sertão de Sergipe; validar estágio fenológico e fitofisionomia","domain":"19 parcelas 30×30 m; períodos verde, intermediário e seco; múltiplas regressões com atributos dual-pol","bands":["C"],"sensor":"Sentinel-1 VV/VH dual-pol","algorithm":"MLR por período fenológico; melhor equação no período intermediário; lista de coeficientes ainda deve ser transcrita e checada contra PDF/dados antes de executar","predictors":["VH/VV","DPSVI","H","alpha","VV"],"coefficients":None,"r2":0.73,"rmse_mg_ha":8.33,"validation":"19 parcelas no estudo; artigo resume R², r e RMSE; incerteza espacial/transferência precisa ser recalculada com pares independentes","doi":"10.1007/s40333-023-0017-4","institution":"Universidade Federal de Sergipe / colaboradores","executable":False,"constraints":"modelo local do Sergipe; não transferir nacionalmente sem recalibração por dados IFN/SFB/Embrapa regionais; índices dependem de fenologia e decomposição dual-pol"},
{"id":"ATLANTIC_2026_PALSAR2_S2","biome":"Mata Atlântica","physiognomy":"florestas montanas/topografia complexa","domain":"inventário de campo + PALSAR-2/Sentinel-2","bands":["L"],"sensor":"PALSAR-2 + Sentinel-2","algorithm":"machine learning multissensor","coefficients":None,"r2":0.64,"rmse_mg_ha":51.10,"validation":"benchmark com inventário de campo","doi":"10.1016/j.isprsjprs.2026.04.022","institution":"ISPRS JPRS","executable":False}

]
def _wkt(gdf):return gdf.to_crs(4326).geometry.union_all().wkt
def _scene_datetime(item):
    """UTC acquisition, not product publication/ingestion or download timestamp."""
    from sar_acquisition_time import acquisition_utc
    dt=acquisition_utc(item)
    return dt.isoformat() if dt is not None else ""

def _newest_first(items):
    from sar_acquisition_time import order_by_acquisition
    return order_by_acquisition(items)

def discover_asf(gdf,limit=25):
    """Discover candidate scenes. NISAR is explicitly restricted to L2 GCOV when possible."""
    out=[]
    queries=[
      ("ALOS PALSAR","L",{}),
      ("NISAR L2 GCOV","L",{"dataset":"NISAR","processingLevel":"GCOV"}),
      ("SENTINEL-1","C",{})]
    for label,band,extra in queries:
        try:
            params={"dataset":("NISAR" if label.startswith("NISAR") else label),"intersectsWith":_wkt(gdf),
                    "output":"geojson","maxResults":limit}
            params.update(extra)
            r=requests.get(ASF_SEARCH,params=params,timeout=(5,15)); r.raise_for_status()
            js=r.json(); fs=js.get("features",[])
            pagination_complete=not any(l.get("rel")=="next" for l in (js.get("links") or []))
            # Defensive GCOV filter because catalogue parameter behavior can vary.
            if label.startswith("NISAR"):
                gc=[x for x in fs if "GCOV" in (str(x.get("properties",{}))+" "+str(x.get("id",""))).upper()]
                if gc: fs=gc
            items=[]
            for x in fs:
                p=x.get("properties",{}) or {}
                urls=[]
                for k,v in p.items():
                    if isinstance(v,str) and v.startswith("http") and ("url" in k.lower() or "download" in k.lower()):
                        urls.append(v)
                # Prefer science HDF5 for NISAR.
                urls.sort(key=lambda u:(0 if u.lower().split("?")[0].endswith((".h5",".hdf5")) else 1,len(u)))
                polraw=p.get("polarization") or p.get("polarizations") or p.get("beamModeType") or ""
                if isinstance(polraw,(list,tuple)): pols=[str(v).upper() for v in polraw]
                else:
                    txt=str(polraw).upper().replace(","," ").replace("/"," ")
                    pols=[q for q in ("HH","HV","VH","VV") if q in txt]
                full_pol=set(("HH","HV","VV")).issubset(set(pols)) or set(("HH","VH","VV")).issubset(set(pols))
                items.append({"id":p.get("sceneName") or x.get("id"),"properties":p,
                              "download_url":urls[0] if urls else None,"raw":x,
                              "polarizations":pols,"full_pol_candidate":full_pol})
            items=_newest_first(items)
            out.append({"provider":"ASF/NASA","dataset":label,"band":band,"count":len(fs),"items":items,
                        "catalog_search_complete":True,"pagination_complete":pagination_complete,
                        "technical_error_count":0,
                        "eligibility":"candidato; elegibilidade final depende de produto/polarização/interseção/modelo"})
        except Exception as e:
            out.append({"provider":"ASF/NASA","dataset":label,"band":band,"count":0,"items":[],"error":str(e),
                        "catalog_search_complete":False,"pagination_complete":False,"technical_error_count":1})
    return out
def discover_cdse(gdf,limit=25):
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__
    try:
        r=requests.post(CDSE_STAC,json={"collections":["sentinel-1-grd"],"intersects":geom,"limit":limit,"sortby":[{"field":"properties.datetime","direction":"desc"}]},timeout=(5,15));r.raise_for_status();fs=r.json().get("features",[])
        return {"provider":"Copernicus Data Space","dataset":"Sentinel-1 GRD","band":"C","count":len(fs),"items":[{"id":x.get("id"),"datetime":x.get("properties",{}).get("datetime")} for x in fs]}
    except Exception as e:return {"provider":"Copernicus Data Space","dataset":"Sentinel-1 GRD","band":"C","count":0,"items":[],"error":str(e)}
def discover_sar(gdf):
    """Refresh catalogue, sort acquisitions by date, and report Brasília time."""
    from sar_acquisition_time import summarize_catalog_acquisition
    sources=discover_asf(gdf)+[discover_cdse(gdf)]
    for source in sources:
        if isinstance(source.get("items"),list):
            stamp=summarize_catalog_acquisition(source["items"])
            source["items"]=stamp["items"]
            source["latest_acquisition"]=stamp["latest"]
            source["acquisition_policy"]=stamp["date_policy"]
            source["acquisition_warning"]=stamp["warning"]
    return sources
def _zonal(gdf,path):
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    with rasterio.open(path) as src:
        gj=transform_geom("EPSG:4326",src.crs,gdf.to_crs(4326).geometry.union_all().__geo_interface__)
        arr,_=mask(src,[gj],crop=True,filled=False);a=np.ma.array(arr[0]).compressed();a=a[np.isfinite(a)]
        if src.nodata is not None:a=a[a!=src.nodata]
        if role(path)=="HEIGHT":a=a[a>=0]
        if not len(a):raise ValueError("Raster sem pixels válidos de altura não negativos dentro do polígono.")
        result={"mean":float(a.mean()),"sd":float(a.std(ddof=1)) if len(a)>1 else 0.0,"n":int(len(a)),"min":float(a.min()),"max":float(a.max())}
        if role(path)=="HEIGHT":
            # Fixed 5 m bins with an open upper class make histograms
            # comparable across native strata. These are actual valid SAR
            # raster pixels clipped by the requested AOI geometry.
            edges=np.array([0,5,10,15,20,25,30,35,40,45,50,55,60,np.inf],dtype=float)
            valid=a[np.isfinite(a)]
            counts,_=np.histogram(valid,bins=edges)
            result["pixel_distribution"]={"status":"SAR_PIXELS_HISTOGRAMMED",
                "bin_width_m":5,"valid_pixel_n":int(len(valid)),
                "bins":[{"lower_m":float(lo),"upper_m":(float(hi) if np.isfinite(hi) else None),
                    "label":(f"{int(lo)}–{int(hi)} m" if np.isfinite(hi) else "≥60 m"),
                    "pixel_count":int(count)} for lo,hi,count in zip(edges[:-1],edges[1:],counts)],
                "source_raster":Path(path).name,
                "scope":"Pixels SAR válidos dentro da geometria da AOI processada; não extrapolado para pixels sem dados."}
        return result
def role(path):
    n=Path(path).name.lower()
    # Sigma0 is the backscatter measurement, not an uncertainty layer. Check
    # explicit uncertainty tokens and avoid the old sigma substring trap.
    tokens=set(re.split(r"[^a-z0-9]+",n))
    if (any(x in tokens for x in ("uncertainty","uncert","stderr","stddev","rmse","variance","sd"))
        or "std_dev" in n or "standard_deviation" in n or "agb_sd" in n
        or ("sigma" in tokens and not any(x in tokens for x in ("sigma0","hh","hv","vv","vh")))):
        return "UNCERTAINTY"
    if any(x in tokens for x in ("height","canopyheight","chm","fh")):return "HEIGHT"
    if any(x in n for x in ["agb","biomass","biomassa"]):return "AGB"
    for p in ("hh","hv","vv","vh"):
        if re.search(r"(^|[_-])"+p+r"([_.-]|$)",n):return p.upper()
    return "SAR"
def _provenance(origin, source, sensor=None, band=None, product=None, model=None, scene_ids=None):
    return {"data_origin":origin,"source":source,"sensor":sensor,"band":band,"product":product,"model_id":model,"scene_ids":scene_ids or []}

def _invert_yu_saatchi_sigma0(sig,A,B,C,alpha,lo=0.0,hi=155.0):
    """Invert Yu & Saatchi (2016) Eq. 2 on its monotonic low-biomass domain."""
    sig=float(sig)
    def f(x): return A*(x**alpha)*(1.0-math.exp(-B*x))+C
    if sig < f(lo)-1e-12 or sig > f(hi)+1e-12:return None
    a,b=lo,hi
    for _ in range(90):
        m=(a+b)/2.0
        if f(m)<sig:a=m
        else:b=m
    return (a+b)/2.0

def yu_saatchi_tropical_shrubland_agb(stats,biome,phys):
    """Quantitative ALOS/PALSAR HV route for low-biomass tropical savanna/shrubland only."""
    if str(biome or "").casefold()!="cerrado":return None
    p=str(phys or "").casefold()
    eligible=any(k in p for k in ("savana","cerrado","campo"))
    excluded=any(k in p for k in ("cerradão","cerradao","floresta","mata"))
    if not eligible or excluded:return None
    hv=next((x for x in stats if str(x.get("polarization","")).upper()=="HV" and x.get("mean_db") is not None),None)
    if not hv:return None
    A,B,C,alpha=0.016429,0.11013,0.0,0.2675
    mean_db=float(hv["mean_db"]); sd_db=max(0.0,float(hv.get("sd_db") or 0.0))
    sigma=10.0**(mean_db/10.0)
    agb=_invert_yu_saatchi_sigma0(sigma,A,B,C,alpha)
    if agb is None or agb>100.0:return None
    # Spatial sensitivity envelope only; model-transfer uncertainty remains explicit and unquantified.
    vals=[]
    for db in (mean_db-sd_db,mean_db+sd_db):
        q=_invert_yu_saatchi_sigma0(10.0**(db/10.0),A,B,C,alpha)
        if q is not None:vals.append(q)
    spread=max([abs(q-agb) for q in vals] or [0.0])
    return {"status":"SAR_PROCESSADO","agb_mg_ha":float(agb),"uncertainty_mg_ha":float(spread),
            "uncertainty_kind":"propagação da dispersão espacial HV (±1 DP) pela equação; NÃO inclui erro de transferência do modelo global",
            "data_origin":"SAR_L_PALSAR_YU_SAATCHI_2016","source":"Yu & Saatchi (2016), Remote Sensing 8:522, DOI 10.3390/rs8060522",
            "sensor":"ALOS/PALSAR","band":"L","product":"mosaico anual HH/HV","model_id":"YU_SAATCHI_2016_TROPICAL_SHRUBLAND_HV",
            "stats":stats,"scene_ids":sorted({str(x.get("scene")) for x in stats if x.get("scene")}),
            "limits":["aplicação restrita a Cerrado/savana não florestal","AGB operacional <=100 Mg/ha; hard domain do ajuste 155 Mg/ha",
                      "modelo global por classe ecológica; requer validação local para uso de inventário regulatório/creditício"]}

TAPAJOS_HEIGHT_STRUCTURE_MODELS={
    "PF_SLF":{
        "model_id":"TAPAJOS_PF_SLF_H100_G_V1",
        "coefficient_k":0.4092378415295996,
        "n_plots":16,"spatial_blocks":4,
        "cv_rmse_mg_ha":26.649861368192365,"cv_mae_mg_ha":21.661665504659965,
        "cv_bias_mg_ha":-0.8328583034468249,"cv_r2":0.8788969494824688,
        "g_domain":[15.921469046279583,31.26701504411778],
        "h100_domain":[19.956,34.104],"agb_reference_domain":[164.46042188046076,424.93701722288324],
        "field_dap_min_cm":10,
    },
    "SF":{
        "model_id":"TAPAJOS_SF_H100_G_V1",
        "coefficient_k":0.2945481254115913,
        "n_plots":14,"spatial_blocks":3,
        "cv_rmse_mg_ha":17.55081844680108,"cv_mae_mg_ha":11.514999715209187,
        "cv_bias_mg_ha":5.496318377648255,"cv_r2":0.8390477392612594,
        "g_domain":[1.4582299204241205,16.920969890611822],
        "h100_domain":[8.435999999999998,28.70799999999999],
        "agb_reference_domain":[4.364544247344407,138.23684901148718],
        "field_dap_min_cm":5,
    }
}
TAPAJOS_STRUCTURE_ZONES=[
    {"zone_id":"TAPAJOS_PF_8_11_HIGH","stage":"PF_SLF","plots":[8,9,10,11],
     "bbox":[-54.9805,-2.9400,-54.9784,-2.9335],
     "basal_area_m2_ha":26.777591962941827,"basal_area_sd_m2_ha":2.996066381172428,
     "inventory_agb_mean_mg_ha":346.33136276411136,
     "inventory_source":"ORNL DAAC 1552 — PF plots 8–11"},
    {"zone_id":"TAPAJOS_SF_21_23_LOW","stage":"SF","plots":[21,22,23],
     "bbox":[-54.9843,-3.1152,-54.9827,-3.1108],
     "basal_area_m2_ha":2.284585027246419,"basal_area_sd_m2_ha":1.2686015817800564,
     "inventory_agb_mean_mg_ha":7.4736528472679025,
     "inventory_source":"ORNL DAAC 1552 — SF plots 21–23"},
]
MODEL_REGISTRY.extend([
    {"id":"TAPAJOS_PF_SLF_H100_G_V1","biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa — primária ou exploração seletiva",
     "domain":"Tapajós ORNL 1552, PF+SLF; G e H100 dentro do domínio observado",
     "bands":["P"],"sensor":"ESA BIOMASS FP_FH__L2B ou altura SAR H100 compatível",
     "algorithm":"AGB = 0.4092378415 × G × H100; G de inventário local e H100 SAR",
     "predictors":["H100_SAR_m","G_inventory_m2_ha"],"coefficients":{"k":0.4092378415295996},
     "r2":0.8788969494824688,"rmse_mg_ha":26.649861368192365,
     "validation":"leave-spatial-block-out interno, 16 parcelas / 4 blocos; resposta Chave 2014, não destrutiva",
     "doi":"10.3334/ORNLDAAC/1552","institution":"ORNL DAAC / calibração Enform sobre dados públicos",
     "executable":True,"execution_mode":"height_structure_local",
     "constraints":"somente zonas de estrutura horizontal cadastradas; H100 deve ser produto SAR compatível; RMSE não inclui erro do FH SAR"},
    {"id":"TAPAJOS_SF_H100_G_V1","biome":"Amazônia","physiognomy":"floresta secundária",
     "domain":"Tapajós ORNL 1552, SF; G e H100 dentro do domínio observado",
     "bands":["P"],"sensor":"ESA BIOMASS FP_FH__L2B ou altura SAR H100 compatível",
     "algorithm":"AGB = 0.2945481254 × G × H100; G de inventário local e H100 SAR",
     "predictors":["H100_SAR_m","G_inventory_m2_ha"],"coefficients":{"k":0.2945481254115913},
     "r2":0.8390477392612594,"rmse_mg_ha":17.55081844680108,
     "validation":"leave-spatial-block-out interno, 14 parcelas / 3 blocos; resposta Chave 2014, não destrutiva",
     "doi":"10.3334/ORNLDAAC/1552","institution":"ORNL DAAC / calibração Enform sobre dados públicos",
     "executable":True,"execution_mode":"height_structure_local",
     "constraints":"somente zonas de estrutura horizontal cadastradas; H100 deve ser produto SAR compatível; RMSE não inclui erro do FH SAR"}
])

def tapajos_inventory_structure_zone(gdf):
    """Return a registered local horizontal-structure support only if AOI fits inside it."""
    try:
        w,s,e,n=gdf.to_crs(4326).geometry.union_all().bounds
    except Exception:
        return None
    tol=1e-9
    for z in TAPAJOS_STRUCTURE_ZONES:
        zw,zs,ze,zn=z["bbox"]
        if w>=zw-tol and s>=zs-tol and e<=ze+tol and n<=zn+tol:
            return dict(z)
    return None

def tapajos_h100_structure_agb(gdf,sar_height,biome="",phys=""):
    """Estimate AGB from SAR H100 + local inventory basal area inside strict Tapajos supports."""
    if str(biome or "").strip().casefold() not in ("amazônia","amazonia"):
        return None
    # GTDX GEDI/TanDEM-X RH98 is not H100. Enforce compatibility at the model boundary,
    # not only in automatic_pipeline, so direct callers cannot bypass the scientific gate.
    if (sar_height or {}).get("height_definition_compatible_with_H100") is False:
        return {"status":"SAR_HEIGHT_STRUCTURE_BLOCKED","agb_mg_ha":None,
                "reason":"Altura SAR disponível, mas definição incompatível com H100; requer conversão validada",
                "data_origin":"SAR_HEIGHT_INCOMPATIBLE_H100"}
    zone=tapajos_inventory_structure_zone(gdf)
    if not zone:return None
    try:h=float((sar_height or {}).get("height_mean_m"))
    except Exception:return None
    if not math.isfinite(h) or h<=0:return None
    m=TAPAJOS_HEIGHT_STRUCTURE_MODELS[zone["stage"]]
    g=float(zone["basal_area_m2_ha"])
    hlo,hhi=m["h100_domain"]; glo,ghi=m["g_domain"]
    if not (hlo<=h<=hhi and glo<=g<=ghi):
        return {"status":"SAR_HEIGHT_STRUCTURE_BLOCKED","agb_mg_ha":None,
                "data_origin":"SAR_P_HEIGHT_X_INVENTORY_STRUCTURE",
                "reason":"H100 SAR ou área basal fora do domínio observado da calibração local",
                "height_mean_m":h,"basal_area_m2_ha":g,"height_domain_m":m["h100_domain"],
                "basal_area_domain_m2_ha":m["g_domain"],"zone":zone,"model_id":m["model_id"]}
    k=float(m["coefficient_k"]); agb=k*g*h
    g_spatial_sensitivity=abs(k*h*float(zone["basal_area_sd_m2_ha"]))
    # Published regional structure totals are consulted for every FH × inventory
    # result. They are a plausibility baliza (not plot-level calibration); the
    # actual predictor G remains the eligible local inventory support above.
    try:
        from inventory_agb_comparison import published_horizontal_inventory_baliza
        horizontal_audit=published_horizontal_inventory_baliza(
            biome=biome,physiognomy=phys)
    except Exception as exc:
        horizontal_audit={"status":"ERRO_TECNICO_LEITURA_REFERENCIAS_HORIZONTAIS",
                          "diagnostic":type(exc).__name__,"references":[],
                          "not_used_as_plot_calibration":True}
    return {"status":"SAR_PROCESSADO","agb_mg_ha":float(agb),
            "uncertainty_mg_ha":float(m["cv_rmse_mg_ha"]),
            "uncertainty_kind":"RMSE leave-spatial-block-out do modelo G×H100 contra AGB alométrica Chave-2014; NÃO inclui erro de medição/transferência do produto FH SAR",
            "spatial_structure_sensitivity_mg_ha":float(g_spatial_sensitivity),
            "data_origin":"SAR_P_HEIGHT_X_INVENTORY_STRUCTURE",
            "source":"ESA BIOMASS FP_FH__L2B/H100 × estrutura horizontal ORNL DAAC 1552",
            "sensor":"ESA BIOMASS","band":"P","product":"FP_FH__L2B + inventário estrutural local",
            "model_id":m["model_id"],"height_mean_m":h,
            "height_sd_m":(sar_height or {}).get("height_sd_m"),
            "height_n_valid_pixels":(sar_height or {}).get("height_n_valid_pixels"),
            "height_definition":"H100 = média das 100 árvores mais altas/ha",
            "basal_area_m2_ha":g,"basal_area_sd_m2_ha":float(zone["basal_area_sd_m2_ha"]),
            "published_horizontal_inventory_baliza":horizontal_audit,
            "inventory_plots":zone["plots"],"inventory_source":zone["inventory_source"],
            "inventory_agb_reference_mean_mg_ha":zone["inventory_agb_mean_mg_ha"],
            "calibration":{"n_plots":m["n_plots"],"spatial_blocks":m["spatial_blocks"],
                           "RMSE_Mg_ha":m["cv_rmse_mg_ha"],"MAE_Mg_ha":m["cv_mae_mg_ha"],
                           "bias_Mg_ha":m["cv_bias_mg_ha"],"R2":m["cv_r2"],
                           "reference":"AGB de parcela calculada por Chave et al. 2014 a partir de DAP, altura total e densidade da madeira"},
            "validation_state":"SAR_CALCULADO_ERRO_PROVISORIO_SEM_VALIDACAO_FH_LOCAL",
            "limits":["uso restrito ao suporte espacial das parcelas cadastradas",
                      "referência AGB é alométrica, não destrutiva",
                      "balizas de BA/densidade/DAP totalizadas são preservadas separadas e não são tratadas como parcela nem como calibração",
                      "RMSE mede o modelo estrutural dentro de Tapajós e não valida o erro do produto SAR H100"]}

def sar_agb_blocker(biome,phys,available_features=None,aoi=None):
    """Explain exactly why processed SAR cannot yet produce defensible AGB."""
    available=set((available_features or {}).keys())
    candidates=[]
    for m in MODEL_REGISTRY:
        if not m.get("executable") or m.get("execution_mode")=="direct_product":continue
        if m.get("biome") not in (biome,"*"):continue
        pred=list(m.get("predictors") or [])
        missing=[p for p in pred if p not in available]
        candidates.append({"model_id":m.get("id"),"sensor":m.get("sensor"),"predictors":pred,
                           "available_predictors":[p for p in pred if p in available],
                           "missing_predictors":missing,"constraints":m.get("constraints"),
                           "rmse_mg_ha":m.get("rmse_mg_ha")})
    candidates.sort(key=lambda x:(len(x["missing_predictors"]),x.get("rmse_mg_ha") is None,x.get("rmse_mg_ha") or 1e9))
    return {"available_features":sorted(available),"candidate_models":candidates[:6],
            "primary_blocker":("nenhum modelo executável cadastrado para o bioma" if not candidates else
                               "faltam preditores exigidos pelo modelo executável mais próximo"),
            "closest_model":candidates[0] if candidates else None}

def _load_official_ibge_vegetation_local(aoi_gdf):
    """Fetch the public IBGE 2026 vegetation archive and locally select AOI map units.

    The property geometry stays on the user's machine. Only the national public
    dataset is downloaded; spatial overlay is performed locally.
    """
    import os, tempfile, zipfile
    import geopandas as gpd
    import pandas as pd
    import pyogrio
    from pyproj import CRS, Transformer

    # SAR unit tests and callers without vector geometry may still process raster
    # assets; simply withhold class-wise overlay when no usable AOI is supplied.
    try:
        if aoi_gdf is None or not len(aoi_gdf) or aoi_gdf.crs is None:
            return None,None
    except (TypeError,AttributeError):
        return None,None
    local_appdata=os.environ.get("LOCALAPPDATA")
    root=(Path(local_appdata)/"Enform Verde"/"data"/"IBGE" if local_appdata
          else Path.home()/".cache"/"enform-verde"/"IBGE")
    root.mkdir(parents=True,exist_ok=True)
    archive_path=root/"vege_area_2026.zip"
    url=("https://geoftp.ibge.gov.br/informacoes_ambientais/vegetacao/"
         "vetores/escala_250_mil/versao_2026/vege_area.zip")

    def valid_archive(path):
        try:
            with zipfile.ZipFile(path) as z:
                return any(n.casefold().endswith(".shp") for n in z.namelist())
        except (OSError,zipfile.BadZipFile):
            return False

    if not valid_archive(archive_path):
        archive_path.unlink(missing_ok=True)
        fd,tmp_name=tempfile.mkstemp(prefix="ibge-vegetation-",suffix=".part",dir=root)
        os.close(fd); tmp=Path(tmp_name)
        try:
            with requests.get(url,stream=True,timeout=(8,45),
                              headers={"User-Agent":"Enform-Verde/3.24.33"}) as response:
                response.raise_for_status()
                with tmp.open("wb") as stream:
                    for chunk in response.iter_content(1024*1024):
                        if chunk: stream.write(chunk)
            if tmp.stat().st_size<1_000_000 or not valid_archive(tmp):
                raise RuntimeError("O arquivo obtido não é um pacote vetorial IBGE válido.")
            tmp.replace(archive_path)
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                "Não foi possível obter o mapa oficial de vegetação IBGE 2026. "
                "Conecte a internet ou carregue uma camada oficial local. "
                "A geometria da propriedade não foi enviada. Detalhe: "+str(exc)
            ) from exc

    aoi=aoi_gdf.to_crs("EPSG:4326")
    west,south,east,north=map(float,aoi.total_bounds)
    if not all(math.isfinite(v) for v in (west,south,east,north)) or west>=east or south>=north:
        raise ValueError("A AOI não possui limites válidos para a interseção IBGE.")
    parts=[]
    with zipfile.ZipFile(archive_path) as z:
        members=[name for name in z.namelist() if name.casefold().endswith(".shp")]
    if not members:
        raise RuntimeError("O arquivo IBGE não contém shapefiles de vegetação.")

    for member in members:
        vsi="/vsizip/"+archive_path.resolve().as_posix()+"/"+member
        try:
            info=pyogrio.read_info(vsi)
            fields={str(x).casefold():str(x) for x in info.get("fields",[])}
            field=fields.get("legenda_1")
            if not field: continue
            src_crs=CRS.from_user_input(info.get("crs") or "EPSG:4674")
            transformer=Transformer.from_crs("EPSG:4326",src_crs,always_xy=True)
            bbox=transformer.transform_bounds(west,south,east,north,densify_pts=21)
            bounds=info.get("total_bounds")
            if bounds is not None and len(bounds)==4:
                if bounds[2]<bbox[0] or bounds[0]>bbox[2] or bounds[3]<bbox[1] or bounds[1]>bbox[3]:
                    continue
            part=gpd.read_file(vsi,bbox=bbox,columns=[field],engine="pyogrio")
            if len(part):
                part=part[part[field].notna()].to_crs("EPSG:4326")
                if len(part): parts.append(part[[field,"geometry"]])
        except Exception:
            continue
    if not parts:
        raise RuntimeError("O mapa oficial não retornou polígonos IBGE legenda_1 na extensão da AOI.")
    result=gpd.GeoDataFrame(pd.concat(parts,ignore_index=True),geometry="geometry",crs="EPSG:4326")
    aoi_geom=aoi.geometry.union_all()
    result=result[result.geometry.notna() & ~result.geometry.is_empty]
    result=result[result.geometry.intersects(aoi_geom)].copy()
    if result.empty:
        raise RuntimeError("A base IBGE 2026 não cobre a AOI; o cálculo por fitofis…28489 tokens truncated…  biomass_search_audit,audit.get("biomass_height"),audit.get("gtdx_height"))
    height_structure_estimate=None
    if sar_height and sar_height.get("height_definition_compatible_with_H100",True):
        try:
            height_structure_estimate=tapajos_h100_structure_agb(gdf,sar_height,biome,phys)
            # Keep the audit acyclic: the returned estimate receives `audit` below.
            audit["height_structure_model"]=(
                {key:value for key,value in height_structure_estimate.items()
                 if key!="audit"} if isinstance(height_structure_estimate,dict)
                else height_structure_estimate)
            if height_structure_estimate is None:
                audit["height_structure_model"]={
                    "status":"FH_DISPONIVEL_SEM_EQUACAO_REGIONAL_COMPATIVEL",
                    "reason":"FH foi lido, mas não existe equação FH×inventário com suporte espacial, estrutura horizontal harmonizada e calibração de AGB compatíveis para esta região/fitofisionomia.",
                    "horizontal_inventory_references":(audit.get("published_inventory_evidence") or {}).get("horizontal_structure_references",[]),
                    "not_used_as_agb_predictor":True,
                    "not_added_to_stock_total":True,
                    "next_route":"CCI_AGB; se indisponível, média de inventários AGB pertinentes com incerteza e limitações explícitas"}
        except Exception as e:
            audit["height_structure_model"]={"status":"ERROR","reason":str(e)}
    # Download/read the official L2B product bundle. Open products are attempted without credentials first;
    # an ESA MAAP token is used only when the catalogue asset is technically protected.
    if l2items:
        try:
            agb_items=[it for it in l2items if it.get("_product_type","FP_AGB_L2B")=="FP_AGB_L2B"]
            agb_cache_key=("biomass_agb_download",str(Path(cache).resolve()),
                tuple(sorted(str(it.get("id") or "") for it in agb_items)))
            agb_cache_hit=bool(pipeline_route_cache is not None and
                               agb_cache_key in pipeline_route_cache)
            if agb_cache_hit:
                d=dict(pipeline_route_cache[agb_cache_key])
            else:
                d=download_maap_agb(gdf,offline_token,Path(cache)/"biomass",items=l2items)
                if pipeline_route_cache is not None:
                    pipeline_route_cache[agb_cache_key]=dict(d)
            audit["biomass_l2b"]["download"]=d
            audit["biomass_l2b"]["download"]["analysis_download_cache"]=("HIT" if agb_cache_hit else "MISS")
            if d.get("paths"):
                pr=process_real_sar(gdf,d["paths"],biome,phys)
                pr["audit"]=audit; pr["paths"]=d["paths"]; pr["data_origin"]="SAR_P_BIOMASS_FP_AGB_L2B"
                pr["source"]="ESA BIOMASS FP_AGB_L2B — produto geofísico oficial P-band"
                pr["sensor"]="ESA BIOMASS"; pr["band"]="P"; pr["product"]="FP_AGB_L2B"
                pr["model_id"]="ESA_BIOMASS_FP_AGB_L2B"
                pr=_preserve_sar_canopy_height(pr,sar_height,audit)
                pr["uncertainty_kind"]=("média zonal de AGB_Std_Dev do produto ESA; incerteza do produto, não erro local de validação"
                    if pr.get("uncertainty_mg_ha") is not None else
                    "produto não forneceu camada AGB_Std_Dev legível; dispersão espacial reportada à parte, sem erro local validado")
                if height_structure_estimate and height_structure_estimate.get("agb_mg_ha") is not None:
                    # When both measured P-band H100 and the local horizontal
                    # inventory support are valid, the approved experimental
                    # height×structure equation is the carbon estimate. Keep
                    # official BIOMASS AGB as an independent comparison.
                    direct_comparison={"agb_mg_ha":pr.get("agb_mg_ha"),
                        "uncertainty_mg_ha":pr.get("uncertainty_mg_ha"),
                        "uncertainty_kind":pr.get("uncertainty_kind"),
                        "source":pr.get("source"),"product":pr.get("product"),
                        "data_origin":pr.get("data_origin"),
                        "n_valid_pixels":pr.get("n_valid_pixels")}
                    height_result=dict(height_structure_estimate)
                    height_result["audit"]=audit
                    height_result["paths"]=(sar_height or {}).get("paths",[])
                    height_result["official_agb_product_comparison"]=direct_comparison
                    height_result["agb_selection_reason"]=(
                        "H100 SAR × área basal do inventário local: suporte espacial e domínio da calibração compatíveis; "
                        "AGB oficial mantida como comparação independente")
                    return _preserve_sar_canopy_height(height_result,sar_height,audit)
                if height_structure_estimate:
                    pr["height_structure_comparison"]=height_structure_estimate
                return _preserve_sar_canopy_height(pr,sar_height,audit)
        except Exception as e:audit["warnings"].append("BIOMASS P download/process: "+str(e))
        if not offline_token:
            audit["warnings"].append("BIOMASS L2B localizado, mas o ativo científico não pôde ser lido anonimamente. Se o catálogo exigir autenticação técnica, informe ESA MAAP Long-Lasting Token.")

    # Height-first local route: if official P-band H100 exists and the AOI has
    # measured horizontal structure, estimate AGB before falling back to lower bands.
    if height_structure_estimate and height_structure_estimate.get("agb_mg_ha") is not None:
        height_structure_estimate["audit"]=audit
        height_structure_estimate["paths"]=(sar_height or {}).get("paths",[])
        return _preserve_sar_canopy_height(height_structure_estimate,sar_height,audit)

    # 2 — Public L-band first: ALOS/PALSAR annual mosaic, no user credentials.
    try:
        al=planetary_alos_palsar(gdf,Path(cache)/"alos_palsar")
        audit["alos_palsar_public"]={"catalogued":al.get("items",0),"scene_ids":al.get("scene_ids",[]),"pixel_state":al.get("pixel_state"),"stats":al.get("stats",[]),"errors":al.get("errors",[])[:4],
            "catalog_search_complete":al.get("catalog_search_complete"),"pagination_complete":al.get("pagination_complete"),
            "technical_error_count":al.get("technical_error_count")}
        if al.get("stats"):
            prior=(audit.get("national_route_matrix") or {}).get("regional_numeric_fallback") or {}
            ldiag=lband_dualpol_diagnostic(al.get("stats",[]),biome,phys,prior.get("agb_mg_ha"))
            audit["lband_dualpol_diagnostic"]=ldiag
            avail={"sigma0_HH_db":next((x.get("mean_db") for x in al.get("stats",[]) if str(x.get("polarization","")).upper()=="HH"),None),
                   "sigma0_HV_db":next((x.get("mean_db") for x in al.get("stats",[]) if str(x.get("polarization","")).upper()=="HV"),None)}
            avail={k:v for k,v in avail.items() if v is not None}
            audit["agb_blocker"]=sar_agb_blocker(biome,phys,avail,aoi=gdf)
            low_agb=yu_saatchi_tropical_shrubland_agb(al.get("stats",[]),biome,phys)
            if low_agb is not None:
                low_agb["audit"]=audit; low_agb["paths"]=al.get("paths",[])
                audit["quantitative_lband_model"]="YU_SAATCHI_2016_TROPICAL_SHRUBLAND_HV"
                return _preserve_sar_canopy_height(low_agb,sar_height,audit)
            audit.setdefault("processed_without_agb",[]).append({"source":"ALOS/PALSAR L","provider":al.get("provider"),"paths":al.get("paths",[]),"stats":al.get("stats",[]),"diagnostic":ldiag})
            if ldiag and not ldiag.get("quantitative_agb_from_dualpol_permitted",False):
                audit["warnings"].append("ALOS/PALSAR L-band dual-pol processado e radiometricamente plausível, porém classificado como SAR estratificador devido à saturação esperada em floresta tropical úmida de alta biomassa; AGB quantitativa exige full-pol/P-band ou calibração local independente.")
    except Exception as e:audit["warnings"].append("ALOS/PALSAR público: "+str(e))

    # 2b — NISAR/ALOS scene catalogue; authenticate through official earthaccess first.
    asf=discover_asf(gdf,limit=50); audit["asf"]=asf
    lcount=sum(x["count"] for x in asf if x["band"]=="L")
    ea_session,ea_state=_earthaccess_requests_session(edl_user,edl_password,edl_token)
    audit["earthaccess"]=ea_state
    if lcount and (ea_session is not None or edl_token or (edl_user and edl_password)):
        try:
            from lband_preprocess import preprocess_lband
            cands=[it for group in asf if group.get("band")=="L" for it in group.get("items",[]) if it.get("download_url")]
            def _rank(it):
                t=(str(it.get("id",""))+" "+str(it.get("properties",{}))).upper()
                if "NISAR" in t and "GCOV" in t:return 0
                if "NISAR" in t:return 1
                if it.get("full_pol_candidate"):return 2
                return 3
            # Scientific sensor/product priority first, newest real acquisition within it.
            cands=_newest_first(cands)
            cands=sorted(cands,key=_rank)
            audit["recency_policy"]="spectral priority first; NISAR GCOV/full-pol first; newest acquisition first within each product class; rejected scenes are logged and next newest is tried"
            audit["lband_candidate_readiness"]={
                "candidate_count":len(cands),
                "full_pol_candidates":sum(1 for x in cands if x.get("full_pol_candidate")),
                "gcov_candidates":sum(1 for x in cands if "GCOV" in (str(x.get("id",""))+" "+str(x.get("properties",{}))).upper()),
                "note":"download authentication and scientific model readiness are separate gates; full-pol/GCOV is prioritized because quantitative AGB models need more than dual-pol HH/HV in dense forest"
            }
            for cand in cands[:8]:
                try:
                    url=cand["download_url"]; dl=Path(cache)/"asf"; dl.mkdir(parents=True,exist_ok=True)
                    target=dl/Path(url.split("?")[0]).name
                    if not target.exists():
                        sess=ea_session or requests.Session()
                        if ea_session is None:
                            if edl_token:
                                sess.headers.update({"Authorization":"Bearer "+edl_token})
                            else:
                                sess.auth=(edl_user,edl_password)
                        with sess.get(url,stream=True,timeout=(8,45),allow_redirects=True) as rr:
                            rr.raise_for_status()
                            with open(target,"wb") as out:
                                for chunk in rr.iter_content(8*1024*1024):
                                    if chunk: out.write(chunk)
                    if target.suffix.lower() in (".h5",".hdf5") and "NISAR" in (str(cand.get("id",""))+" "+str(cand.get("properties",{}))).upper():
                        pr=analyze_nisar_gcov(gdf,target,biome,phys)
                        audit["asf_download"]={"scene":cand.get("id"),"processed":"NISAR_GCOV_HDF5","features":pr.get("features")}
                        if pr.get("agb_mg_ha") is not None: pr["audit"]=audit; pr["paths"]=[str(target)]; return _preserve_sar_canopy_height(pr,sar_height,audit)
                        # Preserve the processed scene in the audit, but continue through all SAR sources before any literature fallback.
                        audit.setdefault("processed_without_agb",[]).append({"source":"NISAR_GCOV","scene":cand.get("id"),"paths":[str(target)],"features":pr.get("features")})
                        continue
                    pre=preprocess_lband(target,dl/("proc_"+target.stem))
                    if pre.get("rasters"):
                        pr=process_real_sar(gdf,pre["rasters"],biome,phys); pr["audit"]=audit; pr["data_origin"]="SAR_L"; pr["paths"]=pre["rasters"]
                        if pr.get("agb_mg_ha") is not None: return _preserve_sar_canopy_height(pr,sar_height,audit)
                        audit.setdefault("processed_without_agb",[]).append({"source":"L_BAND","scene":cand.get("id"),"paths":pre["rasters"]})
                        continue
                except Exception as e: audit["warnings"].append("Cena L "+str(cand.get("id"))+": "+str(e))
        except Exception as e: audit["warnings"].append("ASF L-band: "+str(e))
    elif lcount: audit["warnings"].append(f"{lcount} produto(s) L-band localizados; download protegido requer Earthdata Login. O programa tentou earthaccess via credenciais informadas, variáveis EARTHDATA_* e _netrc/.netrc; estado: "+str((audit.get("earthaccess") or {}).get("reason"))+".")

    # 3 — X-band: no public automatic archive is assumed. Local/licensed X rasters are processed by process_real_sar.
    audit["x_band"]={"status":"rota local/licenciada","note":"TerraSAR-X/TanDEM-X não é inventado como download público automático."}

    # 4 — Real public Sentinel-1 C-band. First use the credential-free Planetary Computer COG route.
    pc=None
    try:
        pc=planetary_sentinel1_cog(gdf,Path(cache)/"sentinel1_public")
        pc_route={"route":"Microsoft Planetary Computer signed COG",
            "catalogued":pc.get("items",0),"scene_ids":pc.get("scene_ids",[]),
            "pixel_state":"PROCESSADO" if pc.get("stats") else
                ("ERRO_TECNICO" if pc.get("errors") else "SEM_PIXELS_COMPATIVEIS"),
            "stats":pc.get("stats",[]),"rate_limited":bool(pc.get("rate_limited",False)),
            "errors":pc.get("errors",[])[:6],"catalog_search_complete":pc.get("catalog_search_complete"),
            "pagination_complete":pc.get("pagination_complete"),"technical_error_count":pc.get("technical_error_count")}
        _record_sentinel1_public_route(audit,"MPC",pc_route)
        if pc.get("stats"):
            audit.setdefault("processed_without_agb",[]).append({"source":"Sentinel-1 C","provider":pc.get("provider"),"paths":pc.get("paths",[]),"stats":pc.get("stats",[])})
            audit["warnings"].append("Sentinel-1 C-band: pixels reais processados. AGB não é inferida de C-band isolada em floresta densa sem modelo validado.")
        else:
            audit["warnings"].append("Sentinel-1 Planetary Computer: "+("; ".join(pc.get("errors",[])[:3]) or "sem pixels processados"))
    except Exception as e: audit["warnings"].append("Sentinel-1 Planetary Computer: "+str(e))

    # Independent Brazil-wide official source. Query and read it even when MPC
    # succeeds so the audit compares real acquisition dates instead of assuming
    # a provider priority is the same as a recency priority.
    try:
        s1inpe=inpe_sentinel1_rtc(gdf,days=30,limit=8)
        inpe_stats=s1inpe.get("stats",[])
        inpe_dates=[x.get("acquisition_utc") for x in inpe_stats if x.get("acquisition_utc")]
        audit["sentinel1_inpe"]={"provider":s1inpe.get("provider"),
            "collection":s1inpe.get("collection"),"catalogued":s1inpe.get("catalogued",0),
            "scene_ids":s1inpe.get("scene_ids",[]),"pixel_state":s1inpe.get("pixel_state"),
            "latest_pixel_acquisition_utc":max(inpe_dates) if inpe_dates else None,
            "stats":inpe_stats,"errors":s1inpe.get("errors",[]),
            "pagination_complete":s1inpe.get("pagination_complete"),
            "catalog_search_complete":s1inpe.get("catalog_search_complete"),
            "technical_error_count":s1inpe.get("technical_error_count")}
        if inpe_stats:
            audit.setdefault("processed_without_agb",[]).append({"source":"Sentinel-1 C",
                "provider":s1inpe.get("provider"),"stats":inpe_stats})
            audit["warnings"].append("Sentinel-1 INPE RTC: pixels VV/VH reais processados; não há conversão para AGB sem modelo calibrado e validado compatível.")
        else:
            audit["warnings"].append("Sentinel-1 INPE RTC: "+str(s1inpe.get("pixel_state")))
    except Exception as e:
        audit["sentinel1_inpe"]={"pixel_state":"ERRO_TECNICO","error_type":type(e).__name__,"error":str(e)[:300]}
        audit["warnings"].append("Sentinel-1 INPE RTC: "+type(e).__name__+": "+str(e)[:240])

    # Secondary Sentinel-1 route: CDSE Process API/direct assets.
    try:
        if cdse_client_id and cdse_client_secret:
            c=cdse_sentinel1_process(gdf,Path(cache)/"sentinel1_cdse",client_id=cdse_client_id,client_secret=cdse_client_secret)
            cdse_route={"route":"Sentinel Hub Process API","downloaded":len(c.get("paths",[])),
                "pixel_state":"PROCESSADO" if c.get("stats") else "SEM_PIXELS_COMPATIVEIS",
                "time_range":c.get("time_range"),"processing":c.get("processing"),
                "stats":c.get("stats",[])}
        else:
            c=public_sentinel1_cog(gdf,Path(cache)/"sentinel1_cdse",cdse_token=cdse_token)
            cdse_route={"route":"catalogue/direct asset fallback","catalogued":c.get("items",0),
                "downloaded":len(c.get("paths",[])),"scene_ids":c.get("scene_ids",[]),
                "pixel_state":"PROCESSADO" if c.get("stats") else
                    ("ERRO_TECNICO" if c.get("errors") else "SEM_PIXELS_COMPATIVEIS"),
                "stats":c.get("stats",[]),"errors":c.get("errors",[])[:6],
                "catalog_search_complete":c.get("catalog_search_complete"),
                "pagination_complete":c.get("pagination_complete"),
                "technical_error_count":c.get("technical_error_count")}
        _record_sentinel1_public_route(audit,"CDSE",cdse_route)
        if c.get("stats"):
            audit.setdefault("processed_without_agb",[]).append({"source":"Sentinel-1 C","provider":c.get("provider"),"paths":c.get("paths",[]),"stats":c.get("stats",[])})
            audit["warnings"].append("Sentinel-1 C-band processado, mas sem modelo AGB calibrado/validado compatível; busca SAR continua.")
    except Exception as e: audit["warnings"].append("Sentinel-1 CDSE Process API/download: "+str(e))

    # 5 — After the FH × horizontal-inventory attempt, CCI is the independent
    # second direct AGB route. FH errors remain in the audit and do not get
    # relabelled as absence or suppress this route.
    cci_gate=secondary_cci_agb_decision(
        audit.get("height_absence_certificate"),
        valid_height_pixels=bool(sar_height and int(sar_height.get("height_n_valid_pixels") or 0)>0))
    try:
        # This is an independent second product route. The FH route's technical
        # state remains explicit in priority_selection_gate and is not cleared.
        cci_download_skipped=not cci_gate["eligible"]
        if cci_download_skipped:
            cci={"items":0,"paths":[],"errors":[],"download_skipped":True,
                 "catalog_search_complete":False,"pagination_complete":False,
                 "technical_error_count":0}
        else:
            cci=_cci_history_for_analysis(gdf,Path(cache)/"cci",offline_token or None,pipeline_route_cache)
        audit["cci"]={"count":cci.get("items",0),"downloaded":len(cci.get("paths",[])),
                      "version":cci.get("version"),"year":cci.get("year"),
                      "resolution_m":cci.get("resolution_m"),"tiles":cci.get("tiles",[]),
                      "source":cci.get("source"),"errors":cci.get("errors",[])[:8],
                      "paths":cci.get("paths",[]),
                      "download_skipped":cci_download_skipped,
                      "catalog_search_complete":cci.get("catalog_search_complete"),
                      "pagination_complete":cci.get("pagination_complete"),
                      "technical_error_count":cci.get("technical_error_count")}
        is_humid_tropical=("amaz" in str(biome or "").casefold()
            and any(term in str(phys or "").casefold() for term in
                    ("ombrófila densa","ombrofila densa","floresta densa","terra firme")))
        audit["cci"]["saturation_risk_note"]=(
            "Risco elevado de saturação e compressão da resposta em floresta tropical úmida; CCI não deve ser usado como verdade de campo nem como estimativa final não calibrada. Comparar com inventários compatíveis e relatar incerteza de transferência."
            if is_humid_tropical else
            "Produto regional/global derivado de SAR; requer calibração e validação compatíveis antes de ser apresentado como estimativa local.")
        audit["cci"]["priority_selection_gate"]=cci_gate
        audit["cci"]["inventory_use_contract"]={
            "role":"CCI é estimativa secundária independente acompanhada por comparação regional de inventários compatíveis",
            "inventory_calibration_applied":False,
            "reason":"Não há, nesta rota, conjunto harmonizado e suficiente de pares AGB parcela–pixel CCI por região para estimar viés/coeficientes de recalibração. Referências horizontais (G, DAP, altura) sem expansão e referências AGB sem pareamento ficam separadas como comparação, não calibração.",
            "inventory_sources_consulted":list((audit.get("published_inventory_evidence") or {}).get("sources") or []),
            "ifn_microdata_consulted":True,
            "not_added_to_stock_total":True}
        if int(cci.get("technical_error_count") or 0)>0:
            audit["warnings"].append("ESA CCI teve erro técnico durante busca/leitura; a contingência por inventários fica bloqueada até corrigir a rota.")
        elif cci_gate.get("eligible") and (cci.get("catalog_search_complete") is not True
                or cci.get("pagination_complete") is not True):
            audit["warnings"].append("ESA CCI não concluiu a busca/paginação; a contingência por inventários fica bloqueada.")
        if cci.get("paths") and cci_gate["eligible"]:
            audit["cci"]["selection_status"]="ELEGIVEL_COMO_CONTINGENCIA_AGB"
            audit["cci"]["selection_reason"]=cci_gate["reason"]
            pr=process_real_sar(gdf,cci["paths"],biome,phys)
            pr["audit"]=audit; pr["paths"]=cci["paths"]; pr["historical"]=True
            pr["data_origin"]="SAR_DERIVED_CCI"
            pr["source"]="ESA CCI Biomass v"+str(cci.get("version") or "")+" — produto L4 multissensor derivado de SAR"
            pr["sensor"]="Sentinel-1/Envisat ASAR + ALOS/PALSAR (composição conforme o ano do produto)"
            pr["band"]="C+L"; pr["product"]="ESA CCI Biomass AGB"
            pr["model_id"]="ESA_CCI_BIOMASS_V7" if str(cci.get("version","")).startswith("7") else "ESA_CCI_BIOMASS_V5_01"
            pr["product_year"]=cci.get("year"); pr["resolution_m"]=cci.get("resolution_m")
            # Annual reference year is NOT instantaneous acquisition; state lag.
            pr["acquisition_status"]="PRODUTO_ANUAL_COMPOSTO_SEM_HORA_DE_CENA"
            pr["year_reference_utc"]=cci.get("year")
            pr["historical_lag_years"]=(datetime.now(timezone.utc).year-int(cci["year"])) if cci.get("year") is not None else None
            audit["cci"]["most_recent_published_year_retrieved"]=cci.get("year")
            pr["cci_tiles"]=cci.get("tiles",[])
            if pr.get("uncertainty_mg_ha") is not None:
                pr["uncertainty_kind"]="média zonal da camada AGB_SD do ESA CCI; desvio-padrão do produto, não erro local de validação"
            return _preserve_sar_canopy_height(pr,sar_height,audit)
        elif cci_gate.get("eligible"):
            audit["cci"]["selection_status"]=(
                "ERRO_TECNICO_NA_SEGUNDA_ROTA" if int(cci.get("technical_error_count") or 0)>0 else
                "BUSCA_DA_SEGUNDA_ROTA_INCOMPLETA" if cci.get("catalog_search_complete") is not True
                    or cci.get("pagination_complete") is not True else
                "CONSULTA_CONCLUIDA_SEM_PRODUTO_COMPATIVEL")
            audit["cci"]["selection_reason"]=(
                "Falha técnica no acesso/leitura ESA CCI; ver erros registrados." if
                    int(cci.get("technical_error_count") or 0)>0 else
                "Catálogo/paginação ESA CCI incompletos; não se afirma ausência." if
                    cci.get("catalog_search_complete") is not True or
                    cci.get("pagination_complete") is not True else
                "Consulta concluída sem raster AGB compatível para esta AOI.")
        if not cci_gate["eligible"]:
            route_state=_priority_height_route_state(
                cci_eligible=False,
                valid_height_pixels=(sar_height or {}).get("height_n_valid_pixels"))
            if route_state["status"]=="FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL":
                audit["priority_height_route_gate"]={"status":route_state["status"],
                    "reason":"Pixels FH válidos foram lidos; ESA CCI permanece bloqueado. Não há modelo AGB compatível aplicado a este domínio.",
                    "cci_candidate_available":bool(cci.get("paths")),"cci_promoted":False}
            else:
                audit["priority_height_route_gate"]={"status":route_state["status"],
                    "reason":cci_gate["reason"],"cci_candidate_available":bool(cci.get("paths")),
                    "cci_promoted":False}
            if cci.get("paths"):
                audit["cci"]["selection_status"]="ADIADA_ERRO_OU_AUSENCIA_NAO_COMPROVADA_NA_ROTA_PRIORITARIA"
                audit["cci"]["selection_reason"]=cci_gate["reason"]
            elif cci_download_skipped:
                audit["cci"]["selection_status"]="NAO_ADQUIRIDO_GATE_BLOQUEADO"
                audit["cci"]["selection_reason"]=cci_gate["reason"]
            if route_state["status"]=="FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL":
                audit["warnings"].append(
                    "FH foi lido, mas não há modelo AGB aplicável; ESA CCI não foi adquirido porque o gate exige ausência real de FH e calibração CCI–inventário validada.")
            elif cci.get("paths"):
                audit["warnings"].append(
                    "ESA CCI foi localizado, mas não promovido: "+cci_gate["reason"]+
                    ". Corrigir/concluir a rota FH antes de selecionar contingência.")
            else:
                audit["warnings"].append(
                    "ESA CCI não foi adquirido: rota FH/GTDX incompleta ou calibração CCI–inventário ausente; resolver a condição auditada antes de selecionar contingência.")
        else:
            fh_failed=bool((cci_gate or {}).get("fh_technical_errors_preserved") or
                           (cci_gate or {}).get("fh_incomplete_routes_preserved"))
            audit["priority_height_route_gate"]={
                "status":"FH_ERROS_PRESERVADOS_CCI_SEGUNDA_ROTA_APLICADA" if fh_failed and cci.get("paths") else
                         "FH_ERROS_PRESERVADOS_CCI_SEGUNDA_ROTA_SEM_PRODUTO" if fh_failed else
                         "CCI_SEGUNDA_ROTA_APLICADA" if cci.get("paths") else
                         "CCI_SEGUNDA_ROTA_CONSULTADA_SEM_PRODUTO",
                "reason":cci_gate["reason"],"cci_candidate_available":bool(cci.get("paths")),
                "cci_promoted":bool(cci.get("paths")),
                "fh_technical_errors_preserved":(cci_gate or {}).get("fh_technical_errors_preserved",0),
                "fh_incomplete_routes_preserved":(cci_gate or {}).get("fh_incomplete_routes_preserved",False),
                "fh_absence_asserted":(cci_gate or {}).get("fh_absence_asserted",False)}
    except Exception as e:
        cci={"items":0,"paths":[],"errors":[type(e).__name__+": "+str(e)[:250]],
             "technical_error_count":1,"catalog_search_complete":False,"pagination_complete":False}
        audit["cci"]={"error":str(e),"technical_error_count":1,
            "catalog_search_complete":False,"pagination_complete":False}
        audit["warnings"].append("ESA CCI falhou tecnicamente; fallback de inventário bloqueado.")

    # Mark terminal routes. Inventory fallback means no AGB model was available,
    # not that SAR coverage was absent; technical failures still block it.
    audit["sar_sources_exhausted"]=True
    sar_processed=bool(sar_height or audit.get("processed_without_agb"))
    audit["sar_pixel_processing_status"]=(
        "ALTURA_SAR_PROCESSADA_SEM_MODELO_AGB" if sar_height else
        "PIXELS_AUXILIARES_PROCESSADOS_SEM_AGB_OU_ALTURA_QUANTITATIVA" if audit.get("processed_without_agb") else
        "NENHUM_PIXEL_SAR_UTILIZAVEL_APOS_ROTAS_CONFIGURADAS")
    certificate=_scene_absence_certificate(audit)
    audit["scene_absence_certificate"]=certificate
    fallback_gate=inventory_fallback_gate(
        sar_processed,audit.get("warnings",[]),
        sources_exhausted=bool(audit.get("sar_sources_exhausted") and
            isinstance(cci_gate,dict) and cci_gate.get("eligible") is True and
            cci.get("catalog_search_complete") is True and
            cci.get("pagination_complete") is True and
            int(cci.get("technical_error_count") or 0)==0),
        height_processed=bool(sar_height),
        coverage_absence_confirmed=certificate.get("eligible") is True,
        scenes_found=bool(audit.get("biomass_l2b",{}).get("count")
            or audit.get("alos_palsar_public",{}).get("catalogued")
            or sum(int(x.get("count") or 0) for x in audit.get("asf",[]) if isinstance(x,dict))
            or audit.get("sentinel1_inpe",{}).get("catalogued")
            or sum(int(x.get("catalogued") or 0) for x in (audit.get("sentinel1_provider_routes") or {}).values())),
        quantitative_agb_unavailable=True)
    audit["inventory_fallback_gate"]=fallback_gate
    lit=None
    if fallback_gate["eligible"]:
        lit=literature_fallback(biome,phys,library_rows,aoi=gdf)
        if not lit:
            lit=national_agb_fallback(biome,phys,aoi=gdf)
    if lit:
        lit["sar_processed"]=False
        lit["sar_pixel_audit"]=[]
    auxiliary_sar=bool(audit.get("processed_without_agb"))
    priority_route_state=_priority_height_route_state(
        cci_eligible=bool(isinstance(cci_gate,dict) and cci_gate.get("eligible")),
        valid_height_pixels=(sar_height or {}).get("height_n_valid_pixels"),
        fh_technical_errors=(cci_gate or {}).get("fh_technical_errors_preserved",0),
        fh_incomplete=(cci_gate or {}).get("fh_incomplete_routes_preserved",False))
    priority_route_error=priority_route_state["technical_error"]
    has_processed_sar=bool(auxiliary_sar or sar_height)
    result={"status":("ERRO_TECNICO_ROTA_PRIORITARIA" if priority_route_error and not has_processed_sar else
                       "SAR_PROCESSADO_SEM_MODELO_AGB" if auxiliary_sar or sar_height else "SAR_NAO_PROCESSADO"),
            "priority_height_route_status":priority_route_state["status"],
            "agb_mg_ha":None,"uncertainty_mg_ha":None,
            "data_origin":("SAR_ALTURA_SEM_MODELO_AGB" if sar_height else
                           "SAR_ATRIBUTOS_ESTRATIFICADORES" if auxiliary_sar else "SAR_NAO_PROCESSADO"),
            "source":("pixels de altura SAR reais processados; sem equação AGB quantitativa compatível no domínio científico"
                      if sar_height else "pixels SAR auxiliares reais processados; sem altura/AGB quantitativa compatível"
                      if auxiliary_sar else "nenhum arquivo SAR pôde ser baixado/processado nesta execução"),
            "audit":audit,"literature_reference":lit,"sar_attempted_first":True,
            "inventory_fallback_gate":fallback_gate,
            "message":(("Falha ou auditoria incompleta na rota prioritária BIOMASS FH/GTDX: "+str(cci_gate.get("reason"))+
                        ". "+("ESA CCI foi mantido apenas como candidato e não foi selecionado. " if (audit.get("cci") or {}).get("paths") else "")+
                        ("Pixels SAR auxiliares foram lidos, mas não há altura/AGB quantitativa compatível. " if has_processed_sar and not sar_height else "")+
                        "Corrigir a rota técnica e repetir a análise.")
                       if priority_route_error else
                       "Pixels SAR auxiliares foram lidos, mas não há altura/AGB quantitativa de biomassa compatível; após esgotar as rotas de biomassa, pode-se emitir cenário separado de inventário, preservando a trilha e sem chamar inventário de SAR."
                       if audit.get("processed_without_agb") else ("SAR sem pixels utilizáveis após esgotar as rotas configuradas; emitir cenário condicional de inventário e preservar cada falha técnica, sem declarar ausência de cenas."
                       if fallback_gate["eligible"] else "Rotas SAR ainda não esgotadas; a estimativa de inventário permanece bloqueada."))}
    if lit and lit.get("agb_mg_ha") is not None:
        result.update(status="AGB_CONTINGENCIAL_MEDIA_INVENTARIOS" if
            lit.get("status")=="ESTIMATIVA_CONTINGENCIAL_MEDIA_INVENTARIOS_MULTIFONTE" else
            "AGB_CONTINGENCIAL_INVENTARIO_COMPATIVEL",
            agb_mg_ha=lit.get("agb_mg_ha"),
            uncertainty_mg_ha=lit.get("uncertainty_mg_ha"),
            data_origin=lit.get("data_origin") or "LITERATURA_SECUNDARIA",
            source=lit.get("source") or "Inventários florestais compatíveis",
            agb_selection_reason="Rotas FH×inventário e ESA CCI não produziram estimador quantitativo; cenário separado pela média de inventários pertinentes.")
    if 'class_stats' in locals() and class_audit is not None:
        result["fitofisionomia_status"]="INTERSECAO_IBGE_PROCESSADA"
        result["fitofisionomia_area_audit"]=class_audit
        result["fitofisionomia_raster_stats"]=class_stats
        result["fitofisionomia_source"]=ibge_metadata.get("source","camada IBGE carregada pelo operador; confirmar versão oficial")
    return _preserve_sar_canopy_height(result,sar_height,audit)

def execute_registered_model(model_id,features):
    m=next((x for x in MODEL_REGISTRY if x["id"]==model_id),None)
    if not m or not m.get("executable"):raise ValueError("Modelo não executável ou ausente.")
    co=m.get("coefficients") or {};pred=m.get("predictors") or []
    missing=[x for x in pred if x not in features]
    if missing:raise ValueError("Preditores obrigatórios ausentes: "+", ".join(missing))
    y=float(co.get("intercept",0.0))
    for x in pred:y+=float(co[x])*float(features[x])
    return {"agb_mg_ha":max(0.0,y),"model":model_id,"rmse_mg_ha":m.get("rmse_mg_ha"),"bias_mg_ha":m.get("bias_mg_ha"),"validation":m.get("validation"),"doi":m.get("doi")}

def fit_catalog_reference(model_id, observations, agb_mg_ha, spatial_groups, target_features=None):
    """Recalibrate a catalogued model family from real matched local plots/pixels.

    This does not recover or imitate unpublished coefficients. It fits a new local
    model using only the reference's declared predictors and returns grouped
    out-of-fold errors. At least five independent spatial groups are mandatory.
    ``observations`` must be a DataFrame with the exact predictor columns.
    """
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    m=next((x for x in MODEL_REGISTRY if x["id"]==model_id),None)
    if not m: raise ValueError("Referência/modelo não cadastrado.")
    predictors=list(m.get("predictors") or [])
    if not predictors: raise ValueError("A referência não declara preditores operacionais; recupere-os da fonte primária antes de ajustar.")
    missing=[x for x in predictors if x not in observations.columns]
    if missing: raise ValueError("Preditores SAR obrigatórios ausentes: "+", ".join(missing))
    X=observations[predictors].apply(pd.to_numeric,errors="coerce").to_numpy(float)
    y=np.asarray(agb_mg_ha,dtype=float).reshape(-1); groups=np.asarray(spatial_groups).astype(str).reshape(-1)
    if len(X)!=len(y) or len(y)!=len(groups): raise ValueError("Cada linha exige atributos SAR, AGB de parcela e grupo espacial correspondentes.")
    good=np.isfinite(X).all(axis=1)&np.isfinite(y)&(y>=0)&(groups!="")&(groups!="None")
    X,y,groups=X[good],y[good],groups[good]
    min_n=max(20,4*(len(predictors)+1)); labels=np.unique(groups)
    if len(y)<min_n: raise ValueError(f"Recalibração local recusada: exige ao menos {min_n} pares parcela–pixel completos; encontrou {len(y)}.")
    if len(labels)<5: raise ValueError(f"Recalibração local recusada: exige 5 grupos espaciais independentes; encontrou {len(labels)}.")
    cv=GroupKFold(n_splits=min(5,len(labels))); pred=np.full(len(y),np.nan)
    for tr,te in cv.split(X,y,groups):
        if len(tr)<=len(predictors): raise ValueError("Grupo espacial deixa amostra de treino menor que o número de coeficientes.")
        model=LinearRegression().fit(X[tr],y[tr]); pred[te]=model.predict(X[te])
    residual=pred-y
    metrics={"n_pairs":int(len(y)),"independent_groups":int(len(labels)),"RMSE_Mg_ha":float(np.sqrt(mean_squared_error(y,pred))),
        "MAE_Mg_ha":float(mean_absolute_error(y,pred)),"bias_Mg_ha":float(np.mean(residual)),"R2":float(r2_score(y,pred)),
        "validation":"GroupKFold espacial out-of-fold; grupos inteiros mantidos fora do treino",
        "residual_quantiles_Mg_ha":[float(v) for v in np.quantile(residual,[0.025,0.975])]}
    fitted=LinearRegression().fit(X,y)
    out={"model_id":model_id,"reference_source":m.get("doi"),"reference_equation_used":False,
        "calibration_type":"recalibração local independente; não replica os coeficientes publicados",
        "predictors":predictors,"coefficients":{"intercept":float(fitted.intercept_),**{k:float(v) for k,v in zip(predictors,fitted.coef_)}},
        "metrics":metrics,"transfer_scope":"somente a fitofisionomia, região, sensores e período representados pelos pares fornecidos",
        "uncertainty":"quantis empíricos dos resíduos OOF; não são intervalo de confiança universal"}
    if target_features is not None:
        absent=[p for p in predictors if p not in target_features]
        if absent: raise ValueError("Preditores SAR do alvo ausentes: "+", ".join(absent))
        vals=np.asarray([float(target_features[p]) for p in predictors],dtype=float).reshape(1,-1)
        if not np.isfinite(vals).all(): raise ValueError("Preditores do alvo contêm valor não finito.")
        out["target_agb_mg_ha"]=max(0.0,float(fitted.predict(vals)[0]))
        out["target_residual_range_mg_ha"]=[max(0.0,out["target_agb_mg_ha"]+metrics["residual_quantiles_Mg_ha"][0]),
            max(0.0,out["target_agb_mg_ha"]+metrics["residual_quantiles_Mg_ha"][1])]
    return out

def model_registry_rows():
    rows=[{k:m.get(k) for k in ("id","biome","physiognomy","domain","sensor","algorithm","predictors","coefficients","rmse_mg_ha","bias_mg_ha","r2","validation","doi","institution","executable","constraints")} for m in MODEL_REGISTRY]
    for x in SCIENTIFIC_INVENTORY_REGISTRY:
        rows.append({"id":x["id"],"biome":x["biome"],"physiognomy":x["physiognomy"],"domain":x["region"],
                     "sensor":"inventário/literatura","algorithm":"referência externa / prior; não agrupada automaticamente",
                     "predictors":None,"coefficients":None,"rmse_mg_ha":None,"bias_mg_ha":None,"r2":None,
                     "validation":x["role"],"doi":x.get("doi"),"institution":x["institution"],"executable":False,
                     "constraints":x["transfer_rule"]})
    return rows

def scientific_calibration_report(biome, physiognomy, agb_mg_ha=None, bands=(), region=""):
    """Auditable evidence + saturation report exposed to UI/export layers."""
    return {"evidence":rank_external_evidence(biome,physiognomy,region),
            "saturation":saturation_audit(agb_mg_ha,bands) if agb_mg_ha is not None else None,
            "policy":"inventários externos = priors/validação externa; calibração SAR local exige parcelas coincidentes"}
