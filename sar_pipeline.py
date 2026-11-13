import math,re,hashlib,time,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np, requests
from scientific_calibration import SCIENTIFIC_INVENTORY_REGISTRY, saturation_audit, glcm_features, multiscale_texture, rank_external_evidence, fit_local_ensemble
from national_fallback import national_agb_fallback, inventory_fallback_gate
from structural_evidence import StructuralEvidence, evidence_se, random_effects_summary, harmonize_primary_plot_rows
from carbon_compartments import tapajos_litter_stock_component
ASF_SEARCH="https://api.daac.asf.alaska.edu/services/search/param"
CDSE_STAC="https://stac.dataspace.copernicus.eu/v1/search"
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
                        "eligibility":"candidato; elegibilidade final depende de produto/polarização/interseção/modelo"})
        except Exception as e:
            out.append({"provider":"ASF/NASA","dataset":label,"band":band,"count":0,"items":[],"error":str(e)})
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
            "inventory_plots":zone["plots"],"inventory_source":zone["inventory_source"],
            "inventory_agb_reference_mean_mg_ha":zone["inventory_agb_mean_mg_ha"],
            "calibration":{"n_plots":m["n_plots"],"spatial_blocks":m["spatial_blocks"],
                           "RMSE_Mg_ha":m["cv_rmse_mg_ha"],"MAE_Mg_ha":m["cv_mae_mg_ha"],
                           "bias_Mg_ha":m["cv_bias_mg_ha"],"R2":m["cv_r2"],
                           "reference":"AGB de parcela calculada por Chave et al. 2014 a partir de DAP, altura total e densidade da madeira"},
            "validation_state":"SAR_CALCULADO_ERRO_PROVISORIO_SEM_VALIDACAO_FH_LOCAL",
            "limits":["uso restrito ao suporte espacial das parcelas cadastradas",
                      "referência AGB é alométrica, não destrutiva",
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
        raise RuntimeError("A base IBGE 2026 não cobre a AOI; o cálculo por fitofisionomia foi bloqueado.")
    result.attrs["source"]="IBGE, Base de Dados Espacial Vegetação 1:250.000, versão 2026"
    result.attrs["source_url"]=url
    result.attrs["class_field"]="legenda_1"
    result.attrs["automatic_local_cache"]=True
    return result,"legenda_1"

def process_real_sar(gdf,paths,biome="",phys="",ibge_physiognomy_gdf=None,ibge_class_field=None):
    if not paths:raise ValueError("Nenhum produto SAR/raster de biomassa foi fornecido.")
    stats=[];agb=None;unc=None;height=None
    class_stats={}
    class_audit=None
    ibge_load_error=None
    if ibge_physiognomy_gdf is None:
        try:
            ibge_physiognomy_gdf,ibge_class_field=_load_official_ibge_vegetation_local(gdf)
        except Exception as exc:
            # Keep the SAR raster result usable and expose the missing map fallback
            # as a diagnostic; do not discard measured pixels when public IBGE is offline.
            ibge_load_error=type(exc).__name__+": "+str(exc)[:400]
            ibge_physiognomy_gdf,ibge_class_field=None,None
    else:
        # The first IBGE legend is the phytophysiognomy/phytoecological region.
        fields={str(c).casefold():str(c) for c in ibge_physiognomy_gdf.columns}
        ibge_class_field=fields.get("legenda_1",ibge_class_field)
    if ibge_physiognomy_gdf is not None and not ibge_class_field:
        raise ValueError("Campo oficial IBGE legenda_1 não identificado.")
    from fitofisionomia_intersections import zonal_raster_by_ibge_class
    ibge_metadata=getattr(ibge_physiognomy_gdf,"attrs",{}) or {}
    for p in paths:
        rr=role(p);z=_zonal(gdf,p);z.update({"path":str(p),"role":rr})
        # Product processing time is not acquisition time. Read only explicit,
        # timezone-aware acquisition metadata from the opened GeoTIFF.
        try:
            from sar_acquisition_time import annotate_acquisition
            import rasterio
            with rasterio.open(p) as scene_raster:
                tags=scene_raster.tags()
            acquired=annotate_acquisition({"id":str(p),"properties":tags})
            z.update({k:acquired[k] for k in
                      ("acquisition_utc","acquisition_brasilia","acquisition_timezone",
                       "acquisition_status")})
        except Exception as exc:
            z["acquisition_utc"]=None
            z["acquisition_brasilia"]=None
            z["acquisition_status"]="METADADOS_AQUISICAO_INDISPONIVEIS"
            z["acquisition_warning"]=str(exc)[:180]
        stats.append(z)
        if ibge_physiognomy_gdf is not None:
            cz=zonal_raster_by_ibge_class(gdf,ibge_physiognomy_gdf,ibge_class_field,p)
            for row in cz["classes"]:
                row["raster_role"]=rr
                if rr=="AGB" and row.get("mean") is not None:
                    row["agb_mean_mg_ha"]=row["mean"]
                    row["agb_total_mg"]=row["mean"]*row["area_ha"]
                elif rr=="UNCERTAINTY":
                    row["uncertainty_mean_product_units_per_ha"]=row.get("mean")
                elif rr=="HEIGHT":
                    row["height_mean_m"]=row.get("mean")
            class_stats[rr]=cz
            class_audit={k:v for k,v in cz.items() if k not in ("classes","raster_path","class_field")}
            class_audit["classification_source"]=ibge_metadata.get("source","camada IBGE carregada pelo operador")
            class_audit["classification_version"]=ibge_metadata.get("source_version",ibge_metadata.get("source","versão não informada"))
        if rr=="AGB":agb=z["mean"]
        elif rr=="UNCERTAINTY":unc=z["mean"]
        elif rr=="HEIGHT":height=z
    if agb is not None:
        if not 0<=agb<=1500:raise ValueError("Raster AGB fora de faixa plausível; confirme unidades Mg/ha.")
        if unc is None:
            a=next(x for x in stats if x["role"]=="AGB");kind="não fornecida pelo produto; dispersão espacial reportada separadamente"
        else:kind="média zonal da camada de incerteza de pixel do produto; não é erro de validação local"
        out={"status":"SAR_PROCESSADO","agb_mg_ha":agb,"uncertainty_mg_ha":unc,
             "uncertainty_kind":kind,"stats":stats,
             "spatial_sd_mg_ha":next(x["sd"] for x in stats if x["role"]=="AGB"),
             "n_valid_pixels":next(x["n"] for x in stats if x["role"]=="AGB"),
             **_provenance("SAR","produto SAR/AGB efetivamente processado",product="raster AGB")}
        if ibge_physiognomy_gdf is not None:
            out["fitofisionomia_status"]="INTERSECAO_IBGE_PROCESSADA"
            out["fitofisionomia_area_audit"]=class_audit
            out["fitofisionomia_raster_stats"]=class_stats
            out["fitofisionomia_source"]=ibge_metadata.get("source","camada IBGE carregada pelo operador; confirmar versão oficial")
        else:
            out["fitofisionomia_status"]="CAMADA_IBGE_FITOFISIONOMIA_AUSENTE"
            out["fitofisionomia_warning"]="Resultado agregado da AOI não substitui cálculo individual por classe IBGE."
            if ibge_load_error:out["fitofisionomia_error"]=ibge_load_error
        if height is not None:
            out.update({"height_mean_m":height["mean"],"height_sd_m":height["sd"],"height_n_valid_pixels":height["n"],
                        "height_pixel_distribution":height.get("pixel_distribution"),
                        "height_interpretation":_height_interpretation(height.get("path"))})
        return out
    refs=[m for m in MODEL_REGISTRY if m["biome"]==biome]
    feats={x["role"]:x.get("mean") for x in stats if x.get("role") in ("HH","HV","VV","VH")}
    blocker=sar_agb_blocker(biome,phys,feats,aoi=gdf)
    out={"status":"SAR_ATRIBUTOS_SEM_MODELO","agb_mg_ha":None,"uncertainty_mg_ha":None,"stats":stats,"references":refs,"agb_blocker":blocker,"message":"SAR processado; AGB bloqueada por incompatibilidade explícita de preditores/modelo. Consulte agb_blocker."}
    if height is not None:
        out.update({"height_mean_m":height["mean"],"height_sd_m":height["sd"],"height_n_valid_pixels":height["n"],
                    "height_pixel_distribution":height.get("pixel_distribution"),
                    "height_interpretation":_height_interpretation(height.get("path"))})
    return out

def _height_interpretation(path):
    """Describe height product semantics without conflating band backscatter."""
    n=Path(str(path or "")).name.casefold()
    if "fp_fh" in n or ("biomass" in n and "fh" in n):
        return {"observable":"altura superior do dossel H100 (ESA BIOMASS FP_FH__L2B)","band":"P",
                "meaning":"produto de altura florestal; não é AGB nem altura total de cada árvore",
                "agb_inference_permitted":False}
    if any(k in n for k in ("tandem", "tan-dem", "tdx", "polinsar", "insar_height")):
        return {"observable":"altura interferométrica/centro de fase X-band (conforme algoritmo do produto)","band":"X",
                "meaning":"requer altura do terreno/DEM e validação de suporte; não é AGB",
                "agb_inference_permitted":False}
    if any(k in n for k in ("alos", "palsar", "nisar", "lband", "l_band")):
        return {"observable":"camada de altura derivada de produto L-band; algoritmo não identificável pelo nome do arquivo",
                "band":"L","meaning":"verificar documentação e definição do produto antes de usar",
                "agb_inference_permitted":False}
    return {"observable":"altura/cobertura estrutural em metros; sensor e definição não identificados pelo arquivo",
            "band":None,"meaning":"altura raster não implica AGB sem modelo compatível e validação",
            "agb_inference_permitted":False}


MAAP_STAC="https://catalog.maap.eo.esa.int/catalogue/"
BIOMASS_L2B_PRODUCT_TYPES=("FP_AGB_L2B","FP_FH__L2B")
# ESA BIOMASS (P-band) Level-2A Forest Height: open release 30/06/2026, 200 m,
# per image stack. L2B (merged FH/AGB) only from May 2027 (restricted before).
# Owner priority (09/11/2026): P-band BIOMASS height first for native formations.
BIOMASS_FH_L2A="FP_FH__L2A"
BIOMASS_PRODUCT_TYPES=BIOMASS_L2B_PRODUCT_TYPES+(BIOMASS_FH_L2A,)
def _biomass_item_product_types(item):
    """Return BIOMASS L2B product types evidenced by item/asset metadata."""
    props=item.get("properties") or {}; assets=item.get("assets") or {}
    evidence=" ".join([str(item.get("id") or ""),str(item.get("_product_type") or ""),str(props)," ".join(
        str(k)+" "+str(v.get("title") or "")+" "+str(v.get("href") or "")
        for k,v in assets.items())]).upper()
    return [product for product in BIOMASS_PRODUCT_TYPES if product in evidence]

def _biomass_catalog_summary(item):
    props=item.get("properties") or {}
    from sar_acquisition_time import annotate_acquisition
    a=annotate_acquisition(item)
    return {"id":item.get("id"),"datetime":props.get("datetime") or props.get("start_datetime"),
            "acquisition_utc":a["acquisition_utc"],
            "acquisition_brasilia":a["acquisition_brasilia"],
            "acquisition_status":a["acquisition_status"],
            "collection":item.get("_collection"),"stage":item.get("_stage"),
            "product_types":_biomass_item_product_types(item),"bbox":item.get("bbox"),
            "assets":[{"key":k,"title":v.get("title"),"type":v.get("type"),
                       "roles":v.get("roles"),"href":v.get("href")}
                      for k,v in (item.get("assets") or {}).items()]}

MAAP_TOKEN_URL="https://iam.maap.eo.esa.int/realms/esa-maap/protocol/openid-connect/token"
def maap_access_token(offline_token):
    if not offline_token:raise ValueError("Informe o offline token ESA MAAP. Ele não é armazenado pelo Enform Verde.")
    r=requests.post(MAAP_TOKEN_URL,data={"client_id":"offline-token","client_secret":"p1eL7uonXs6MDxtGbgKdPVRAmnGxHpVE","grant_type":"refresh_token","refresh_token":offline_token,"scope":"offline_access openid"},timeout=(5,15));r.raise_for_status()
    t=r.json().get("access_token")
    if not t:raise RuntimeError("A ESA MAAP não retornou access_token.")
    return t
def maap_search(gdf,collection,limit=50,product_type=None,return_audit=False):
    """Search official MAAP STAC with pagination and a GET/bbox fallback.

    STAC metadata search does not require passing the ESA offline token.
    This routine never equates an HTTP failure or incomplete pagination with
    true absence of products, and never logs private geometry or asset URLs.
    """
    from urllib.parse import urljoin, urlsplit
    geom=gdf.to_crs(4326).geometry.union_all()
    bbox=list(map(float,geom.bounds))
    page_size=max(1,min(100,int(limit)))
    base=MAAP_STAC+"search"
    body={"collections":[collection],"intersects":geom.__geo_interface__,
          "limit":page_size}
    # The official MAAP STAC documentation explicitly supports GET with bbox.
    # Avoid sortby initially because some deployments reject the extension.
    try:
        # ESA's documented GET bbox route returns products missed by POST
        # intersects in the real Borneo validation (10 Nov 2026). GET first.
        response=requests.get(base,params={
            "collections":collection,"bbox":",".join(map(str,bbox)),
            "limit":page_size},timeout=(8,30))
        if response.status_code in (400,404,405,415,422,500,501,502,503):
            response=requests.post(base,json=body,timeout=(8,30))
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("MAAP_STAC_SEARCH_FAILED:"+type(exc).__name__) from None
    payload=response.json()
    items=[];seen=set();pages=0;next_link=None
    while True:
        pages+=1
        for item in payload.get("features") or []:
            ident=(str(item.get("collection") or collection),str(item.get("id")))
            if ident in seen:continue
            seen.add(ident);items.append(item)
        next_link=next((l for l in payload.get("links") or []
                        if l.get("rel")=="next" and l.get("href")),None)
        if not next_link:break
        if pages>=20:
            raise RuntimeError("MAAP_STAC_PAGINATION_INCOMPLETE")
        href=urljoin(base,next_link["href"])
        if urlsplit(href).scheme!="https" or urlsplit(href).hostname!=urlsplit(base).hostname:
            raise RuntimeError("MAAP_STAC_UNTRUSTED_NEXT_PAGE")
        method=str(next_link.get("method") or "GET").upper()
        try:
            if method=="POST":
                response=requests.post(href,json=next_link.get("body") or body,
                                       timeout=(8,30))
            elif method=="GET":
                response=requests.get(href,timeout=(8,30))
            else:
                raise RuntimeError("MAAP_STAC_UNSUPPORTED_NEXT_METHOD")
            response.raise_for_status()
            payload=response.json()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("MAAP_STAC_PAGINATION_FAILED:"+type(exc).__name__) from None
    catalog_item_count=len(items)
    if product_type:
        items=[item for item in items if product_type in _biomass_item_product_types(item)]
    items=_newest_first(items)
    if return_audit:
        return items,{"catalog_search_complete":True,"pagination_complete":True,
            "pages_read":pages,"catalog_item_count":catalog_item_count,
            "matching_product_count":len(items),"pixel_read_complete":not bool(items),
            "valid_pixel_count":0 if not items else None,"technical_error_count":0}
    return items

def _maap_search_with_audit(gdf,collection,limit,product_type):
    """Return audit metadata when supported; mocks/legacy callers stay fail-closed."""
    try:
        result=maap_search(gdf,collection,limit=limit,product_type=product_type,return_audit=True)
    except TypeError as exc:
        if "return_audit" not in str(exc):raise
        items=maap_search(gdf,collection,limit=limit,product_type=product_type)
        return items,{"catalog_search_complete":False,"pagination_complete":False,
            "pixel_read_complete":False,"valid_pixel_count":None,"technical_error_count":1,
            "error_type":"AUDIT_METADATA_UNAVAILABLE"}
    if isinstance(result,tuple) and len(result)==2 and isinstance(result[1],dict):return result
    return result,{"catalog_search_complete":False,"pagination_complete":False,
        "pixel_read_complete":False,"valid_pixel_count":None,"technical_error_count":1,
        "error_type":"AUDIT_METADATA_UNAVAILABLE"}

def biomass_l2b_search(gdf,limit=100,return_audit=False):
    """Discover both official AGB and forest-height L2B products; retain their distinct roles."""
    from concurrent.futures import ThreadPoolExecutor,as_completed
    out=[]
    search_errors=[]
    successful_queries=0;query_audits=[]
    routes=(("BiomassLevel2b","OPERATIONAL",BIOMASS_L2B_PRODUCT_TYPES),
            ("BiomassLevel2bIOC","IOC",BIOMASS_L2B_PRODUCT_TYPES),
            ("BiomassLevel2a","OPERATIONAL_L2A",(BIOMASS_FH_L2A,)),
            ("BiomassLevel2aIOC","IOC_L2A",(BIOMASS_FH_L2A,)))
    results={}
    # These are four independent collections for the same AOI. Query them
    # concurrently once each; serial product-by-product searches duplicated
    # identical STAC pagination and delayed the fallback carbon routes.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(_maap_search_with_audit,gdf,collection,limit,None):collection
                 for collection,_,_ in routes}
        for future in as_completed(futures):
            collection=futures[future]
            try:results[collection]=future.result()
            except Exception as exc:results[collection]=(None,exc)
    for collection,stage,product_types in routes:
        all_items,query_audit=results[collection]
        if isinstance(query_audit,Exception):
            search_errors.append(collection+":"+type(query_audit).__name__)
            for product_type in product_types:
                query_audits.append({"route":collection,"product_type":product_type,
                    "catalog_search_complete":False,"pagination_complete":False,
                    "pixel_read_complete":False,"technical_error_count":1,
                    "error_type":type(query_audit).__name__})
            continue
        successful_queries+=1
        for product_type in product_types:
            query_audits.append({"route":collection,"product_type":product_type,**query_audit})
            for it in all_items:
                if product_type not in _biomass_item_product_types(it):continue
                z=dict(it); z["_collection"]=collection; z["_stage"]=stage
                z["_product_type"]=product_type; out.append(z)
    if successful_queries==0:
        raise RuntimeError("MAAP_ALL_COLLECTION_SEARCHES_FAILED: "+",".join(search_errors))
    unique={}
    for item in out:
        unique[(item.get("_collection"),item.get("id"),item.get("_product_type"))]=item
    out=list(unique.values())
    out=_newest_first(out)
    # Scientific product role and operational quality precede recency.
    # Within each equivalent class: most recent *acquisition* first.
    stage_rank={"OPERATIONAL":0,"IOC":1,"OPERATIONAL_L2A":2,"IOC_L2A":3}
    out.sort(key=lambda it:(stage_rank.get(it.get("_stage"),9),
                            0 if it.get("_product_type")=="FP_AGB_L2B" else 1))
    if return_audit:
        return out,{"queries":query_audits,"errors":search_errors,
            "height_queries_complete":all(q.get("catalog_search_complete") is True and q.get("pagination_complete") is True
                for q in query_audits if q.get("product_type") in (BIOMASS_FH_L2A,"FP_FH__L2B")),
            "height_catalog_item_count":sum(1 for item in out if item.get("_product_type") in (BIOMASS_FH_L2A,"FP_FH__L2B"))}
    return out

def _download(url,out,token=None):
    h={"Authorization":"Bearer "+token} if token else {}
    # Bound stalled proxy/TLS reads so one unavailable asset cannot hold up
    # the carbon analysis and the alternate biomass routes indefinitely.
    with requests.get(url,headers=h,stream=True,timeout=(8,30)) as r:
        r.raise_for_status()
        with open(out,"wb") as f:
            for c in r.iter_content(8*1024*1024):
                if c:f.write(c)
    return str(out)
def _biomass_product_assets(item,product_type="FP_AGB_L2B"):
    out=[]
    l2a_archives=[]
    for k,a in (item.get("assets") or {}).items():
        href=a.get("href",""); typ=(a.get("type") or "").lower(); roles=[str(x).lower() for x in (a.get("roles") or [])]
        if not href:continue
        name=(k+" "+href+" "+str(a.get("title") or "")).lower()
        suffix=href.lower().split("?")[0]
        is_archive=suffix.endswith(".zip") or "zip" in typ or "/zipper/" in suffix
        if product_type==BIOMASS_FH_L2A:
            # Prefer the FH GeoTIFF. Some official MAAP products expose only
            # a ZIP via /data/zipper/... (URL has no .zip extension).
            # Allow the product archive only as a fallback, never quicklooks.
            if is_archive and (k.lower() in ("product","download","enclosure","data")
                               or "product" in roles or "data" in roles):
                # Official MAAP can name the ZIP asset "download" and serve
                # it via /data/zipper/ with no extension/MIME ZIP.
                l2a_archives.append((k,href))
                continue
            if not suffix.endswith((".tif",".tiff")) and "tiff" not in typ:
                continue
            is_agb=False
            is_fh=any(x in name for x in ("fh","height"))
        elif product_type=="FP_FH__L2B":
            is_agb=False
            is_fh=any(x in name for x in ("fh","height","canopy","forest_height","fp_fh__l2b"))
        else:
            is_agb=any(x in name for x in ("agb","biomass","fp_agb_l2b"))
            is_fh=False
        generic=(product_type in _biomass_item_product_types(item) and
                 (is_archive or suffix.endswith((".tif",".tiff")) or "geotiff" in typ or
                  "data" in roles or "product" in roles))
        if any(t in name for t in ("uncert", "std_dev", "stddev", "quality", "mask", "flag", "sigma")):
            continue
        if product_type=="FP_AGB_L2B" and (is_agb or generic):
            out.append((k,href))
        elif product_type in ("FP_FH__L2B",BIOMASS_FH_L2A) and (is_fh or generic):
            out.append((k,href))
    # Direct height GeoTIFFs are preferred, but ZIP archives must still be
    # attempted when those files fail to download or decode.
    return out+l2a_archives

def _extract_biomass_agb_assets(path,outdir):
    p=Path(path); outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower() in (".tif",".tiff"):return [str(p)]
    if p.suffix.lower()==".zip":
        hits=[]
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                n=info.filename.lower()
                if info.is_dir() or not n.endswith((".tif",".tiff")):continue
                if not any(k in n for k in ("agb","biomass","std","uncert","sigma")):continue
                target=outdir/Path(info.filename).name
                with z.open(info) as src, open(target,"wb") as dst:
                    while True:
                        chunk=src.read(8*1024*1024)
                        if not chunk:break
                        dst.write(chunk)
                hits.append(str(target))
        return hits
    return []

def _extract_biomass_height_assets(path,outdir):
    """Extract only named FH/height rasters; exclude QA and uncertainty layers."""
    p=Path(path); outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower() in (".tif", ".tiff"):
        return [] if any(k in p.name.casefold() for k in ("uncert", "std_dev", "stddev", "quality", "mask", "flag", "sigma")) else [str(p)]
    if p.suffix.lower()!=".zip":return []
    hits=[]
    with zipfile.ZipFile(p) as z:
        for info in z.infolist():
            name=info.filename.casefold()
            if info.is_dir() or not name.endswith((".tif", ".tiff")):continue
            if any(k in name for k in ("uncert", "std_dev", "stddev", "quality", "mask", "flag", "sigma")):continue
            if not any(k in name for k in ("fh", "height", "canopy")):continue
            target=outdir/Path(info.filename).name
            with z.open(info) as src, open(target,"wb") as dst:
                while True:
                    chunk=src.read(8*1024*1024)
                    if not chunk:break
                    dst.write(chunk)
            hits.append(str(target))
    return hits

def _raster_assets(item):
    out=[]
    for k,a in (item.get("assets") or {}).items():
        href=a.get("href",""); typ=(a.get("type") or "").lower()
        if href and (href.lower().endswith((".tif",".tiff")) or "geotiff" in typ):out.append((k,href))
    return out
def download_maap_agb(gdf,offline_token,cache,items=None):
    items=items if items is not None else biomass_l2b_search(gdf,limit=100)
    agb_items=[it for it in items if it.get("_product_type","FP_AGB_L2B")=="FP_AGB_L2B"]
    fh_items=[it for it in items if it.get("_product_type")=="FP_FH__L2B"]
    if not agb_items:return {"available":False,"paths":[],"items":len(items),"agb_items":0,
                            "fh_items":len(fh_items),"height_catalog_items":[_biomass_catalog_summary(it) for it in fh_items[:50]],
                            "reason":"FP_AGB_L2B sem cobertura; FP_FH__L2B de altura não substitui AGB"}
    token=None; token_loaded=False
    Path(cache).mkdir(parents=True,exist_ok=True);paths=[];errors=[]
    for it in agb_items[:4]:
        for k,url in _biomass_product_assets(it,"FP_AGB_L2B")[:2]:
            base=Path(url.split("?")[0]).name or (it.get("id","biomass")+"_"+k)
            p=Path(cache)/(it.get("id","biomass")+"_"+base)
            try:
                if not p.exists():
                    try:_download(url,p,None)
                    except Exception as e:
                        status=getattr(getattr(e,"response",None),"status_code",None)
                        if not offline_token or status not in (401,403):raise
                        if not token_loaded:token=maap_access_token(offline_token);token_loaded=True
                        _download(url,p,token)
                paths.extend(_extract_biomass_agb_assets(p,Path(cache)/(it.get("id","biomass")+"_extracted")))
            except Exception as e:errors.append(str(e))
        if paths:break
    return {"available":bool(paths),"paths":paths,"items":len(items),"agb_items":len(agb_items),
            "fh_items":len(fh_items),"height_catalog_items":[_biomass_catalog_summary(it) for it in fh_items[:50]],
            "reason":None if paths else "FP_AGB_L2B catalogado, mas COG AGB/AGB_Std_Dev não foi recuperado",
            "errors":errors[:5]}

def download_maap_height(gdf,offline_token,cache,items=None):
    """Download ESA BIOMASS FH height products without routing them through AGB."""
    items=items if items is not None else biomass_l2b_search(gdf,limit=100)
    fh_items=[it for it in items if it.get("_product_type") in ("FP_FH__L2B",BIOMASS_FH_L2A)]
    if not fh_items:
        return {"available":False,"paths":[],"items":len(items),"fh_items":0,
                "reason":"nenhum produto ESA BIOMASS FH (L2B ou L2A, banda P) cobre a AOI; altura SAR não calculável nesta rota"}
    Path(cache).mkdir(parents=True,exist_ok=True); paths=[]; errors=[]; token=None; token_loaded=False
    for it in fh_items[:4]:
        for key,url in _biomass_product_assets(it,it.get("_product_type") or "FP_FH__L2B")[:2]:
            base=Path(url.split("?")[0]).name or (it.get("id","biomass")+"_FH_"+key)
            asset_type=str((it.get("assets") or {}).get(key,{}).get("type") or "").lower()
            if ("zip" in asset_type or "/zipper/" in url.lower()) and not base.lower().endswith(".zip"):
                base += ".zip"
            target=Path(cache)/(it.get("id","biomass")+"_"+base)
            try:
                if not target.exists():
                    try:_download(url,target,None)
                    except Exception as e:
                        status=getattr(getattr(e,"response",None),"status_code",None)
                        if not offline_token or status not in (401,403):raise
                        if not token_loaded:token=maap_access_token(offline_token);token_loaded=True
                        _download(url,target,token)
                paths.extend(_extract_biomass_height_assets(target,Path(cache)/(it.get("id","biomass")+"_height")))
            except Exception as e:errors.append(str(it.get("id"))+" / "+key+": "+str(e))
        if paths:break
    return {"available":bool(paths),"paths":paths,"items":len(items),"fh_items":len(fh_items),
            "height_catalog_items":[_biomass_catalog_summary(it) for it in fh_items[:50]],
            "reason":None if paths else "FP_FH__L2B catalogado, mas raster de altura não foi recuperado",
            "errors":errors[:5]}

def _preserve_sar_canopy_height(result, height, audit=None):
    """Preserve independently processed SAR-derived canopy height on any AGB route.

    AGB source may be ESA P, L-band, CCI or a literature fallback; the
    independent P-band FH / GEDI–TanDEM-X InSAR height must never be replaced
    by inventory tree heights or radar backscatter. It remains missing when
    the actual height product did not cover the AOI or had invalid pixels.
    """
    out=dict(result or {})
    if audit is not None and out.get("audit") is None:
        out["audit"]=audit
    if audit and audit.get("height_absence_certificate"):
        out["height_absence_certificate"]=audit["height_absence_certificate"]
    if not isinstance(height,dict):
        out.setdefault("height_route_status","SEM_PRODUTO_DE_ALTURA_SAR_VALIDO")
        return out
    try:
        value=float(height.get("height_mean_m"))
    except (ValueError, TypeError):
        value=float("nan")
    if not math.isfinite(value) or value<=0:
        out.setdefault("height_route_status","ALTURA_SAR_INVALIDA_OU_N_D")
        return out
    result_height=dict(height)
    # Retain product identity, pixel count, uncertainty, definitions and URL;
    # no automatic conversion of GEDI/TanDEM-X RH98 into BIOMASS H100.
    out["sar_height"]=result_height
    out.update({k:v for k,v in result_height.items() if k.startswith("height_")})
    out["height_route_status"]="ALTURA_SAR_PROCESSADA"
    out["height_data_origin"]="SAR_DERIVED_PRODUCT_WITH_PROVENANCE"
    return out


HEIGHT_PRIORITY_BIOMES=("Amazônia","Pantanal","Cerrado","Mata Atlântica","Caatinga")
def height_scope_contract(biome=None,physiognomy=None):
    """National request policy; per-AOI coverage and error remain product-gated."""
    return {
        "requested_biomes":list(HEIGHT_PRIORITY_BIOMES),
        "aoi_biome":str(biome or ""),
        "aoi_ibge_physiognomy":str(physiognomy or ""),
        "search_policy":"Query ESA BIOMASS FP_FH__L2B P-band for each AOI, independent of biome/physiognomy; do not infer coverage from mission-wide goals.",
        "priority":"ESA BIOMASS FP_FH__L2B where actual AOI pixels are available and valid.",
        "fallback":"GTDX ORNL 2298 TanDEM-X InSAR + GEDI only where its delivered pantropical rasters overlap the AOI; documented coverage includes the Amazon Basin, not all five Brazilian biomes.",
        "class_policy":"Report height by IBGE physiognomy for valid pixels; preserve no-data and flag physiognomies where a forest-canopy-height metric is not scientifically defined.",
        "error_policy":"Carry product-provided pixel uncertainty or a documented validation error. Within-AOI pixel SD is spatial dispersion, not measurement error; never substitute it for product error.",
        "status":"AOI_SPECIFIC_COVERAGE_AND_ERROR_REQUIRED"
    }
GTDX_COLLECTION_ID="C2883623174-ORNL_CLOUD"
GTDX_HEIGHT_SOURCE="ORNL DAAC 2298 — altura GEDI–TanDEM-X InSAR"
def _gtdx_height_summary(height_stats, uncertainty_stats, height_path, uncertainty_path):
    """Build a height-only GTDX result; preserve the product per-pixel standard error."""
    mean=float(height_stats["mean"]); pixel_se_mean=float(uncertainty_stats["mean"])
    if not (math.isfinite(mean) and mean>0 and math.isfinite(pixel_se_mean) and pixel_se_mean>=0):
        raise ValueError("Altura/erro padrão GTDX inválido.")
    return {"status":"SAR_ALTURA_PROCESSADA","available":True,
            "height_mean_m":mean,"height_sd_m":float(height_stats["sd"]),
            "height_n_valid_pixels":int(height_stats["n"]),
            "height_standard_error_pixel_zonal_mean_m":pixel_se_mean,
            "height_error_kind":"média zonal dos erros padrão de estimativa por pixel informados pelo produto (m); não é RMSE local nem erro padrão da média da AOI",
            "height_metric":"altura do dossel calibrada com GEDI RH98; não equivale automaticamente a H100",
            "height_definition_compatible_with_H100":False,
            "height_interpretation":{"observable":"altura do dossel GEDI–TanDEM-X",
              "band":"X (TanDEM-X InSAR) + referência GEDI",
              "meaning":"altura do dossel estimada por fusão InSAR–GEDI, calibrada a GEDI RH98; não é AGB nem H100 sem conversão validada",
              "agb_inference_permitted":False},
            "product":"Pantropical Forest Height and Biomass from GEDI and TanDEM-X Data Fusion",
            "product_id":"ORNLDAAC/2298","sensor":"TanDEM-X InSAR calibrado com GEDI",
            "band":"X","source":GTDX_HEIGHT_SOURCE,
            "height_path":str(height_path),"height_uncertainty_path":str(uncertainty_path),
            "height_uncertainty_source":"height_uncertainty_amazon_25m.tif — erro padrão da estimativa por pixel; média zonal em metros",
            "height_years":"TanDEM-X 2011–2020; GEDI 2019–2021"}
def download_gtdx_height(gdf,edl_user="",edl_password="",edl_token="",cache=None):
    """Download Amazon 25 m canopy-height and per-pixel standard-error COGs through authenticated Earthdata CMR."""
    cache=Path(cache or Path.home()/".enform_verde"/"sar"/"gtdx_height")
    cache.mkdir(parents=True,exist_ok=True)
    session,state=_earthaccess_requests_session(edl_user,edl_password,edl_token)
    authenticated=session is not None
    if session is None:
        # CMR metadata and some public ORNL COG endpoints may be readable without
        # an Earthdata session. Attempt that route before reporting an auth block.
        session=requests.Session()
        state={**(state or {}),"available":True,"method":"anonymous_public_CMR_attempt",
               "authenticated":False}
    west,south,east,north=map(float,gdf.to_crs(4326).geometry.union_all().bounds)
    params={"collection_concept_id":GTDX_COLLECTION_ID,
            "bounding_box":f"{west},{south},{east},{north}","page_size":200}
    try:
        entries=[];page=1;hits=None
        while page<=20:
            page_params=dict(params,page_num=page)
            response=session.get("https://cmr.earthdata.nasa.gov/search/granules.json",params=page_params,timeout=(5,20))
            response.raise_for_status()
            if hits is None:
                raw_hits=getattr(response,"headers",{}).get("CMR-Hits")
                hits=int(raw_hits) if raw_hits is not None else None
            page_entries=response.json().get("feed",{}).get("entry",[])
            entries.extend(page_entries)
            if hits is None or len(entries)>=hits or not page_entries:break
            page+=1
        cmr_pagination_complete=(hits is not None and len(entries)>=hits)
        if hits==0:cmr_pagination_complete=True
        if page>20 and hits is not None and len(entries)<hits:cmr_pagination_complete=False
        wanted={"height_amazon_25m.tif":None,"height_uncertainty_amazon_25m.tif":None}
        for entry in entries:
            candidates=list(entry.get("links",[]) or [])
            candidates.extend((entry.get("umm",{}).get("RelatedUrls",[]) or []))
            for link in candidates:
                href=link.get("href") or link.get("URL") or ""
                name=Path(href.split("?",1)[0]).name.casefold()
                for key in wanted:
                    if name==key:wanted[key]=href
        if not all(wanted.values()):
            return {"available":False,"reason":"CMR não retornou os COGs de altura e incerteza Amazon 25 m.",
                    "collection_id":GTDX_COLLECTION_ID,"cmr_entries":len(entries),"cmr_hits":hits,
                    "catalog_search_complete":cmr_pagination_complete,
                    "pagination_complete":cmr_pagination_complete,
                    "pixel_read_complete":bool(cmr_pagination_complete and not entries),
                    "valid_pixel_count":0 if cmr_pagination_complete and not entries else None,
                    "technical_error_count":0 if cmr_pagination_complete else 1,"auth_state":state}
        paths={}
        for name,url in wanted.items():
            target=cache/name
            if not target.exists() or target.stat().st_size==0:
                partial=target.with_suffix(target.suffix+".part")
                try:
                    with session.get(url,stream=True,timeout=(8,45)) as response:
                        response.raise_for_status()
                        with open(partial,"wb") as out:
                            for chunk in response.iter_content(8*1024*1024):
                                if chunk:out.write(chunk)
                    partial.replace(target)
                except Exception:
                    partial.unlink(missing_ok=True);raise
            paths[name]=target
        h=_zonal(gdf,paths["height_amazon_25m.tif"])
        u=_zonal(gdf,paths["height_uncertainty_amazon_25m.tif"])
        result=_gtdx_height_summary(h,u,paths["height_amazon_25m.tif"],paths["height_uncertainty_amazon_25m.tif"])
        result.update({"cmr_entries":len(entries),"cmr_hits":hits,
                       "catalog_search_complete":cmr_pagination_complete,
                       "pagination_complete":cmr_pagination_complete,
                       "pixel_read_complete":True,"valid_pixel_count":int(h["n"]),
                       "technical_error_count":0,"auth_state":state,"uncertainty_pixels":int(u["n"]),
                       "warning":"Produto de altura SAR–GEDI independente do ESA BIOMASS; não aplicar modelo G×H100 sem equivalência/validação.",
                       "access_route":"Earthdata autenticado" if authenticated else "tentativa pública sem autenticação"})
        return result
    except Exception as exc:
        return {"available":False,"reason":type(exc).__name__+": "+str(exc)[:500],
                "collection_id":GTDX_COLLECTION_ID,"catalog_search_complete":False,
                "pagination_complete":False,"pixel_read_complete":False,
                "valid_pixel_count":None,"technical_error_count":1,"auth_state":state}

CCI_V7_GEOTIFF_ROOT="https://data.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/geotiff"
CCI_V7_GEOTIFF_ALT_ROOT="https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/geotiff"
# Inspect newer years as they arrive; availability is confirmed only by complete
# official raster+uncertainty downloads, never by guessing a future release.
CCI_V7_YEARS=tuple(range(max(2024,time.gmtime().tm_year),2023,-1))+(2023,2022,2021,2020,2019,2018,2017,2016,2015,2012,2011,2010,2009,2008,2007,2006,2005)

def _cci_v7_tile_ids(gdf):
    """Return 10-degree CCI GeoTIFF tile ids intersecting AOI.

    Latitude encodes the northernmost tile row (N00 spans -10..0);
    longitude encodes the westernmost column (W060 spans -60..-50).
    """
    import math
    w,s,e,n=gdf.to_crs(4326).geometry.union_all().bounds
    eps=1e-10
    lon0=math.floor(w/10.0)*10
    lon1=math.floor((e-eps)/10.0)*10
    north0=math.ceil(n/10.0)*10
    north1=math.ceil((s+eps)/10.0)*10
    out=[]; north=north0
    while north>=north1:
        lat=("N" if north>=0 else "S")+f"{abs(int(north)):02d}"
        west=lon0
        while west<=lon1:
            lon=("E" if west>=0 else "W")+f"{abs(int(west)):03d}"
            out.append(lat+lon); west+=10
        north-=10
    return sorted(set(out))

def _cci_v7_urls(gdf,year):
    urls=[]
    for tile in _cci_v7_tile_ids(gdf):
        for var in ("AGB","AGB_SD"):
            name=f"{tile}_ESACCI-BIOMASS-L4-{var}-MERGED-100m-{int(year)}-fv7.0.tif"
            urls.append({"tile":tile,"variable":var,"name":name,
                         "url":f"{CCI_V7_GEOTIFF_ROOT}/{int(year)}/{name}"})
    return urls

def cci_history(gdf,cache,offline_token=None):
    """Acquire latest ESA CCI Biomass v7 GeoTIFFs, then MAAP v5.01 fallback."""
    cache=Path(cache); cache.mkdir(parents=True,exist_ok=True)
    errors=[]; attempted=[]
    for year in CCI_V7_YEARS:
        specs=_cci_v7_urls(gdf,year)
        year_paths=[]; ok=True
        for spec in specs:
            target=cache/spec["name"]
            if target.exists() and target.stat().st_size>0:
                year_paths.append(str(target)); continue
            last_error=None
            for root in (CCI_V7_GEOTIFF_ROOT, CCI_V7_GEOTIFF_ALT_ROOT):
                url=f'{root}/{int(year)}/{spec["name"]}'
                attempted.append(url)
                partial=target.with_name(target.name+".part")
                try:
                    if partial.exists(): partial.unlink()
                    _download(url,partial,None)
                    partial.replace(target)
                    last_error=None
                    break
                except Exception as e:
                    last_error=e
                    try:
                        if partial.exists(): partial.unlink()
                    except OSError:
                        pass
            if last_error is not None:
                ok=False
                errors.append(f'{year} {spec["tile"]} {spec["variable"]}: {type(last_error).__name__}: {last_error}')
                break
            year_paths.append(str(target))
        if ok and year_paths and any(role(p)=="AGB" for p in year_paths):
            return {"available":True,"paths":year_paths,"items":len(specs),
                    "collection":"CEDA/ESA CCI Biomass v7.0","version":"7.0","year":int(year),
                    "resolution_m":100,"tiles":_cci_v7_tile_ids(gdf),
                    "source":"ESA CCI Open Data / CEDA","attempted_urls":attempted,
                    "errors":errors[:8]}
    # Compatibility only: older MAAP local CCI collection.
    items=[]; collections_tried=["CCIBiomassV5.01"]
    try: items=maap_search(gdf,"CCIBiomassV5.01",limit=100)
    except Exception as e: errors.append("MAAP v5.01: "+str(e))
    if not items:
        return {"available":False,"paths":[],"items":0,"collections_tried":collections_tried,
                "version":"7.0","tiles":_cci_v7_tile_ids(gdf),"attempted_urls":attempted,
                "errors":errors[:8]}
    token=maap_access_token(offline_token) if offline_token else None
    paths=[]
    for it in items:
        for k,url in _raster_assets(it):
            if any(x in (k.lower()+url.lower()) for x in ("agb","biomass","uncert","std")):
                p=cache/("cci_"+Path(url.split("?")[0]).name)
                try:
                    if not p.exists():_download(url,p,token)
                    paths.append(str(p))
                except Exception as e:errors.append("MAAP asset: "+str(e))
    return {"available":bool(paths),"paths":paths,"items":len(items),
            "collection":"CCIBiomassV5.01","version":"5.01","year":None,
            "resolution_m":100,"tiles":_cci_v7_tile_ids(gdf),
            "collections_tried":collections_tried,"errors":errors[:8]}

LITERATURE=[
{"biome":"Amazônia","phys":["secund","sucess"],"mean":None,"rmse":38.7,"bias":2.1,"r2":0.51,"cv":"bootstrap 100 repetições; 80/20","source":"Cassol et al. 2019","doi":"10.3390/rs11010059","note":"referência de desempenho; média AGB não extraída para fallback"},
{"biome":"Amazônia","phys":["várzea","varzea","aluvial"],"mean":None,"rmse":74.6,"bias":None,"r2":0.46,"cv":"cross-validation","source":"Martins et al. 2018","doi":"10.3390/rs10091355","note":"referência L-band várzea; média não usada sem valor compatível"},
{"biome":"Cerrado","phys":["cerrado","savanna","savana"],"mean":None,"rmse":7.58,"bias":0.43,"r2":0.89,"cv":"k-fold/jackknife","source":"Silva et al. 2020","doi":"10.3390/rs12172685","note":"Rio Vermelho; referência de desempenho, não média nacional"}
]
BUILTIN_LITERATURE=[]
PRIMARY_PLOT_DATA_PRIORITY=True
# Evidence hierarchy: georeferenced published primary plot data > primary plot data with
# recoverable sampling design > microlocal published summaries > regional summaries.
# Generic biome-wide means are forbidden.
def literature_fallback(biome,phys,library_rows=None,location=None,aoi=None):
    """Use only eligible local/regional evidence; published aggregates never become SAR pixels.

    At present the only built-in numeric fallback is a strictly geofenced Tapajós
    reference. Other regions require explicit reviewed library_rows; biome-only
    values are intentionally rejected.
    """
    # Peer-reviewed Tapajós summary for the km-83 acceptance AOI. It is an
    # external stand-level reference, not plot–pixel SAR calibration.
    def _tapajos_reference():
        if str(biome or "").strip().casefold() not in ("amazônia","amazonia"):
            return None
        p=str(phys or "").casefold()
        if "floresta ombrófila densa" not in p and "floresta ombrofila densa" not in p:
            return None
        if aoi is None:
            return None
        try:
            g=aoi.to_crs("EPSG:4326"); c=g.geometry.union_all().centroid
            from pyproj import Geod
            geod=Geod(ellps="WGS84")
            _,_,dist=geod.inv(float(c.x),float(c.y),-54.95,-3.067)
            distance_km=float(abs(dist)/1000)
            # A centroid check alone could accept an AOI extending far beyond
            # the local evidence domain. Require every exterior vertex to fit.
            geom=g.geometry.union_all()
            polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
            max_vertex_km=0.0
            for poly in polys:
                for coord in poly.exterior.coords:
                    x,y=coord[0],coord[1]
                    _,_,d=geod.inv(float(x),float(y),-54.95,-3.067)
                    max_vertex_km=max(max_vertex_km,abs(d)/1000)
        except Exception:
            return None
        if distance_km>35.0 or max_vertex_km>35.0:
            return None
        def _inside_reference_domain(lon,lat,radius_km):
            """Require the complete AOI exterior to remain near each component study site."""
            max_dist=0.0
            for poly in polys:
                for x,y,*_ in poly.exterior.coords:
                    _,_,d=geod.inv(float(x),float(y),float(lon),float(lat))
                    max_dist=max(max_dist,abs(d)/1000)
            return max_dist<=radius_km
        n1=n2=6; m1,m2=298.11,248.92; s1,s2=29.40,61.78
        n=n1+n2; mean=(n1*m1+n2*m2)/n
        # The paper reports plots grouped in just two spatial sites. Treating all
        # 12 plots as independent for a t prediction interval would overstate the
        # degrees of freedom. Publish a descriptive envelope, not a confidence interval.
        lower=max(0.0,min(m1-s1,m2-s2)); upper=max(m1+s1,m2+s2)
        # Necromass is never inferred from allometry, live biomass, or stand-level literature.
        # Only direct forest-inventory means, stratified by IBGE physiognomy and region,
        # may be reported. No compatible inventory estimate is packaged for this AOI.
        regional_components={}
        litter=tapajos_litter_stock_component(biome,phys,aoi)
        if litter:
            regional_components["Serapilheira — estoque no piso florestal"]=litter
        return {"available":True,"agb_mg_ha":mean,"uncertainty_mg_ha":max(mean-lower,upper-mean),
                "agb_range_mg_ha":[lower,upper],
                "uncertainty_kind":"envelope descritivo entre médias de dois sítios ± DP intrassítio; não é IC95%, intervalo preditivo nem erro SAR",
                "source":"Santos, Camargo & Oliveira Jr. (2018), Ciência Florestal 28(3):1049–1059, DOI 10.5902/1980509833388",
                "doi":"10.5902/1980509833388","url":"https://www.scielo.br/j/cflo/a/Y7zf8xHmVZWndCh6xYhJCwn/?lang=pt",
                "data_origin":"LITERATURA_MICRORREGIONAL","method":"média igualmente ponderada das duas médias publicadas (6 parcelas por sítio); envelope descritivo min(média do sítio−DP), max(média do sítio+DP), sem inferência de 95% por haver somente dois sítios independentes",
                "n_plots":n,"n_independent_sites":2,"distance_from_km83_km":distance_km,
                "site_means_mg_ha":{"km72":m1,"km117":m2},"site_sd_mg_ha":{"km72":s1,"km117":s2},
                "regional_components":regional_components,
                "sar_processed":False,"sar_metrics":{"RMSE":None,"MAE":None,"bias":None,"R2":None},
                "limits":["resultado secundário agregado; não é calibração nem validação SAR","dois sítios independentes separados por cerca de 45 km","dado de 2010; incerteza alométrica e de transferência temporal não incluída integralmente","não gerar mapa AGB pixel a pixel a partir desta média"],
                "note":"Estimativa de referência microrregional para AOI de floresta ombrófila densa situada até 35 km do km 83; não é uma equação SAR."}
    tapajos=_tapajos_reference()
    if tapajos:return tapajos
    rows=list(library_rows or []); p=(phys or "").lower(); loc=(location or "").lower(); ranked=[]
    centroid=None
    if aoi is not None:
        try:
            c=aoi.to_crs("EPSG:4326").geometry.union_all().centroid; centroid=(float(c.x),float(c.y))
        except Exception: centroid=None
    for r in rows:
        if r.get("biome") not in (biome,"*") or r.get("mean") is None: continue
        rp=[str(x).lower() for x in (r.get("phys") or [])]
        if rp and p and not any(x in p or p in x for x in rp): continue
        geo=" ".join(str(r.get(k,"")) for k in ("locality","municipality","region","state")).lower()
        geo_score=0
        coords=r.get("center_lon_lat")
        if centroid and coords and r.get("max_distance_km") is not None:
            from pyproj import Geod
            _,_,dist=Geod(ellps="WGS84").inv(centroid[0],centroid[1],float(coords[0]),float(coords[1]))
            if abs(dist)/1000<=float(r["max_distance_km"]):geo_score=4
        if loc and loc in geo:geo_score=max(geo_score,4)
        if geo_score==0:continue # no biome-only, state-only, or unlocated transfer
        primary=bool(r.get("plot_data") or r.get("primary_plot_data") or r.get("plot_rows")); georef=bool(r.get("plot_coordinates") or r.get("plot_geometries")); design=bool(r.get("sampling_design") or r.get("plot_area_m2"))
        evidence=4 if primary and georef else (3 if primary and design else (2 if primary else 1)); ranked.append(((evidence,geo_score),r))
    if not ranked:return None
    ranked.sort(key=lambda x:x[0],reverse=True); r=ranked[0][1]
    return {"available":True,"agb_mg_ha":float(r["mean"]),"uncertainty_pct":float(r.get("uncertainty_pct",30)),"source":r.get("source","inventário publicado"),"data_origin":"LITERATURA_MICRORREGIONAL","primary_plot_data":bool(r.get("plot_data") or r.get("primary_plot_data") or r.get("plot_rows")),"plot_georeferenced":bool(r.get("plot_coordinates") or r.get("plot_geometries")),"sar_processed":False,"sar_metrics":{"RMSE":None,"MAE":None,"bias":None,"R2":None},"note":"Fallback externo; não é resultado SAR. Prioridade máxima para dados primários de parcelas."}
def process_nisar_gcov(gdf,h5_path):
    """Read calibrated NISAR L2 GCOV covariance terms and derive polygon statistics.
    GCOV values are gamma0 power; no fabricated AGB is returned without a compatible model."""
    import h5py
    from pyproj import CRS, Transformer
    from shapely.ops import transform as shp_transform
    terms={}
    with h5py.File(h5_path,"r") as h:
        base="/science/LSAR/GCOV/grids/frequencyA"
        if base not in h: raise ValueError("Arquivo não contém NISAR L2 GCOV frequencyA.")
        g=h[base]
        x=np.asarray(g["xCoordinates"][:],dtype=float); y=np.asarray(g["yCoordinates"][:],dtype=float)
        epsg=None
        for key in ("projection","projectionEPSG","epsg"):
            if key in g:
                try: epsg=int(np.asarray(g[key])[()])
                except: pass
        if epsg is None:
            # GCOV commonly stores projection metadata on datasets/groups.
            for obj in (g, h["/science/LSAR/GCOV"]):
                for key,val in obj.attrs.items():
                    if "epsg" in str(key).lower():
                        try: epsg=int(val)
                        except: pass
        if epsg is None: raise ValueError("EPSG do grid GCOV não identificado.")
        geom=gdf.to_crs(epsg).geometry.union_all()
        minx,miny,maxx,maxy=geom.bounds
        ix=np.where((x>=minx)&(x<=maxx))[0]; iy=np.where((y>=miny)&(y<=maxy))[0]
        if not len(ix) or not len(iy): raise ValueError("GCOV sem interseção com o polígono.")
        x0,x1=int(ix.min()),int(ix.max())+1; y0,y1=int(iy.min()),int(iy.max())+1
        # Pixel-centre mask, robust to ascending/descending y.
        xx,yy=np.meshgrid(x[x0:x1],y[y0:y1])
        try:
            import shapely
            mask=shapely.contains_xy(geom,xx,yy)
        except Exception:
            from shapely.geometry import Point
            mask=np.vectorize(lambda a,b: geom.contains(Point(float(a),float(b))))(xx,yy)
        for name in ("HHHH","HVHV","VVVV","VHVH","RHRH","RVRV"):
            if name not in g: continue
            a=np.asarray(g[name][y0:y1,x0:x1],dtype=float)
            v=a[mask & np.isfinite(a) & (a>0)]
            if not len(v): continue
            db=10*np.log10(v)
            terms[name]={"mean_power":float(v.mean()),"mean_db":float(db.mean()),"sd_db":float(db.std(ddof=1)) if len(db)>1 else 0.0,"n":int(len(v))}
    if not terms: raise ValueError("Nenhum termo polarimétrico GCOV válido dentro do polígono.")
    features={}
    if "HHHH" in terms: features["L_HH_dB"]=terms["HHHH"]["mean_db"]
    hv="HVHV" if "HVHV" in terms else ("VHVH" if "VHVH" in terms else None)
    if hv: features["L_HV_dB"]=terms[hv]["mean_db"]
    if "VVVV" in terms: features["L_VV_dB"]=terms["VVVV"]["mean_db"]
    if "L_HH_dB" in features and "L_HV_dB" in features: features["L_HV_HH_dB"]=features["L_HV_dB"]-features["L_HH_dB"]
    return {"status":"NISAR_GCOV_PROCESSADO","features":features,"terms":terms,"product":"NISAR L2 GCOV PROVISIONAL","band":"L"}

def select_executable_model(biome,phys,features,aoi=None):
    """Strict compatibility includes declared spatial domain and exact predictors."""
    pp=(phys or "").lower()
    cand=[]
    for m in MODEL_REGISTRY:
        if not m.get("executable") or m.get("execution_mode")=="direct_product": continue
        if m.get("biome") not in (biome,"*"): continue
        domain=m.get("spatial_domain")
        if domain:
            # A regional equation is not eligible without a georeferenced AOI.
            if aoi is None: continue
            try:
                from pyproj import Geod
                g=aoi.to_crs("EPSG:4326").geometry.union_all()
                polys=list(g.geoms) if g.geom_type=="MultiPolygon" else ([g] if g.geom_type=="Polygon" else [])
                if not polys: continue
                lon,lat=domain["center_lon_lat"]; max_km=float(domain["max_aoi_radius_km"]); max_vertex_km=0.0
                geod=Geod(ellps="WGS84")
                for poly in polys:
                    for x,y,*_ in poly.exterior.coords:
                        _,_,d=geod.inv(float(x),float(y),float(lon),float(lat))
                        max_vertex_km=max(max_vertex_km,abs(d)/1000.0)
                if max_vertex_km>max_km: continue
            except Exception:
                continue
        mp=(m.get("physiognomy") or "").lower()
        if mp and pp and not any(t in pp for t in re.split(r"[/,; ]+",mp) if len(t)>4): continue
        pred=m.get("predictors") or []
        if pred and all(p in features for p in pred): cand.append(m)
    cand.sort(key=lambda m:(m.get("rmse_mg_ha") is None,m.get("rmse_mg_ha") or 1e9))
    return cand[0] if cand else None

def analyze_nisar_gcov(gdf,h5_path,biome,phys):
    q=process_nisar_gcov(gdf,h5_path); m=select_executable_model(biome,phys,q["features"],aoi=gdf)
    if not m:
        blocker=sar_agb_blocker(biome,phys,q["features"],aoi=gdf)
        return {"status":"SAR_ATRIBUTOS_SEM_MODELO","agb_mg_ha":None,"data_origin":"SAR_NAO_PROCESSADO",
                "source":"NISAR L2 GCOV processado; sem equação executável compatível",
                "product":q["product"],"band":"L","features":q["features"],"terms":q["terms"],
                "agb_blocker":blocker,
                "message":"NISAR GCOV foi processado, mas os preditores disponíveis não satisfazem uma equação validada no domínio desta AOI. Consulte agb_blocker para a lista exata do que falta."}
    r=execute_registered_model(m["id"],q["features"])
    return {"status":"SAR_PROCESSADO","agb_mg_ha":r["agb_mg_ha"],"uncertainty_mg_ha":r.get("rmse_mg_ha"),
            "uncertainty_kind":"RMSE de validação do modelo","data_origin":"SAR_L_MODELO","source":m.get("source") or m.get("doi"),
            "sensor":"NISAR","band":"L","product":q["product"],"model_id":m["id"],"features":q["features"],"terms":q["terms"]}

EARTH_SEARCH_STAC="https://earth-search.aws.element84.com/v1/search"
CDSE_ODATA="https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_TOKEN_URL="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_PROCESS_URL="https://sh.dataspace.copernicus.eu/process/v1"

def cdse_access_token(client_id,client_secret):
    """Obtain a short-lived CDSE OAuth2 token using client_credentials."""
    if not client_id or not client_secret:
        raise ValueError("CDSE Client ID e Client Secret são necessários para a Process API.")
    r=requests.post(CDSE_TOKEN_URL,data={"grant_type":"client_credentials","client_id":client_id,"client_secret":client_secret},
                    headers={"Content-Type":"application/x-www-form-urlencoded"},timeout=(5,15))
    r.raise_for_status()
    token=(r.json() or {}).get("access_token")
    if not token: raise RuntimeError("CDSE não retornou access_token.")
    return token

def cdse_sentinel1_process(gdf,cache,client_id="",client_secret="",access_token="",days=30):
    """Request real Sentinel-1 GRD VV/VH pixels from CDSE Sentinel Hub Process API.
    Output is an orthorectified, terrain-corrected FLOAT32 GeoTIFF. Discovery,
    authentication, pixel processing and zonal use are recorded separately.
    """
    token=access_token or cdse_access_token(client_id,client_secret)
    gg=gdf.to_crs(4326); minx,miny,maxx,maxy=map(float,gg.total_bounds)
    now=time.time(); frm=time.strftime("%Y-%m-%dT00:00:00Z",time.gmtime(now-days*86400))
    to=time.strftime("%Y-%m-%dT23:59:59Z",time.gmtime(now))
    evalscript="""//VERSION=3
function setup(){return {input:["VV","VH","dataMask"],output:{id:"default",bands:3,sampleType:"FLOAT32"}}}
function evaluatePixel(s){return [s.VV,s.VH,s.dataMask]}"""
    body={"input":{"bounds":{"bbox":[minx,miny,maxx,maxy],"properties":{"crs":"http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
                   "data":[{"type":"sentinel-1-grd","dataFilter":{"timeRange":{"from":frm,"to":to},"mosaickingOrder":"mostRecent"},
                            "processing":{"orthorectify":True,"backCoeff":"GAMMA0_TERRAIN","demInstance":"COPERNICUS_30",
                                          "speckleFilter":{"type":"LEE","windowSizeX":5,"windowSizeY":5}}}]},
          "output":{"width":1024,"height":1024,"responses":[{"identifier":"default","format":{"type":"image/tiff"}}]},
          "evalscript":evalscript}
    r=requests.post(CDSE_PROCESS_URL,json=body,headers={"Authorization":"Bearer "+token,"Accept":"image/tiff"},timeout=(8,45))
    r.raise_for_status()
    Path(cache).mkdir(parents=True,exist_ok=True)
    out=Path(cache)/("S1_GRD_RTC_"+time.strftime("%Y%m%d",time.gmtime(now))+"_VV_VH.tif")
    out.write_bytes(r.content)
    z=_zonal(gdf,str(out)); z["path"]=str(out); z["role"]="Sentinel-1 GRD RTC Gamma0 VV/VH"
    return {"available":True,"paths":[str(out)],"stats":[z],"provider":"Copernicus Data Space Ecosystem / Sentinel Hub Process API",
            "time_range":[frm,to],"processing":"orthorectify + GAMMA0_TERRAIN + COPERNICUS_30 + Lee 5x5",
            "pixel_state":"PROCESSADO","errors":[]}

def public_sentinel1_cog(gdf,cache,limit=12,cdse_token=""):
    """Legacy catalogue/direct-asset route retained as a fallback when Process API credentials are absent."""
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__
    now=datetime.now(timezone.utc)
    body={"collections":["sentinel-1-grd"],"intersects":geom,"limit":limit,
          "datetime":(now-timedelta(days=30)).isoformat().replace("+00:00","Z")+"/"+now.isoformat().replace("+00:00","Z"),
          "sortby":[{"field":"properties.datetime","direction":"desc"}]}
    r=requests.post(CDSE_STAC,json=body,timeout=(5,15)); r.raise_for_status()
    items=r.json().get("features",[])
    items=_newest_first(items)
    Path(cache).mkdir(parents=True,exist_ok=True)
    paths=[]; scene_ids=[]; errors=[]
    for it in items[:4]:
        assets=it.get("assets") or {}; scene_ids.append(it.get("id")); candidates=[]
        for k,v in assets.items():
            href=(v or {}).get("href",""); kl=k.lower(); typ=((v or {}).get("type") or "").lower()
            if href.startswith("http") and (".tif" in href.lower() or "geotiff" in typ):
                candidates.append((0 if any(p in kl for p in ("vh","hv","vv","hh")) else 1,k,href))
        for _,k,href in sorted(candidates)[:2]:
            out=Path(cache)/(str(it.get("id","s1"))+"_"+re.sub(r"[^A-Za-z0-9_.-]+","_",k)+".tif")
            try:
                if not out.exists(): _download(href,out,cdse_token or None)
                paths.append(str(out))
            except Exception as e: errors.append(str(it.get("id"))+" / "+k+": "+str(e))
    stats=[]
    for p in paths:
        try:
            z=_zonal(gdf,p); z["path"]=p; z["role"]=role(p); stats.append(z)
        except Exception as e: errors.append(Path(p).name+": "+str(e))
    return {"available":bool(items),"paths":paths,"items":len(items),"scene_ids":scene_ids,"stats":stats,
            "provider":"Copernicus Data Space Ecosystem catalogue/direct asset fallback","errors":errors}

def inpe_sentinel1_rtc(gdf,*,days=30,limit=6):
    """Read actual public INPE Sentinel-1 RTC VV/VH COG pixels over an AOI.

    This is an independent, credential-free fallback for biomass pipeline SAR
    evidence. The measurements are ancillary C-band backscatter and are never
    converted to AGB without a separately accepted calibration model.
    """
    from datetime import datetime,timedelta,timezone
    from shapely.geometry import mapping
    from sentinel1_inpe import search_sentinel1_inpe_rtc
    if not isinstance(days,int) or not 1<=days<=3650:raise ValueError("days must be from 1 to 3650")
    if not isinstance(limit,int) or not 1<=limit<=40:raise ValueError("limit must be from 1 to 40")
    geom=gdf.to_crs(4326).geometry.union_all()
    if geom.is_empty:raise ValueError("INPE Sentinel-1 AOI is empty")
    end=datetime.now(timezone.utc)
    found=search_sentinel1_inpe_rtc(mapping(geom),start_utc=end-timedelta(days=days),end_utc=end)
    scenes=found.get("scenes",[])[:limit]
    if not scenes:
        return {"available":False,"provider":"INPE Sentinel-1 RTC COG","collection":found.get("collection"),
                "catalogued":0,"scene_ids":[],"stats":[],"errors":[],"pixel_state":"SEM_CENAS_COMPATIVEIS",
                "pagination_complete":found.get("pagination_complete",False)}
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    stats=[];errors=[];scene_ids=[]
    for scene in scenes:
        scene_ids.append(scene.get("id"))
        pair=[];scene_stats=[]
        for pol in ("vv","vh"):
            asset=(scene.get("assets") or {}).get(pol) or {}
            href=asset.get("href")
            try:
                if not href or not str(href).startswith("https://data.inpe.br/"):
                    raise ValueError("INPE RTC asset missing or outside official host")
                import tls_setup
                with rasterio.Env(**tls_setup.gdal_env(),GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                                  GDAL_HTTP_MAX_RETRY="3",GDAL_HTTP_TIMEOUT="45"):
                    with rasterio.open(href) as src:
                        if src.crs is None:raise ValueError("INPE RTC COG missing CRS")
                        local_geom=transform_geom("EPSG:4326",src.crs,mapping(geom))
                        data,_=mask(src,[local_geom],crop=True,filled=False)
                        values=np.asarray(np.ma.array(data[0]).compressed(),dtype=np.float64)
                        values=values[np.isfinite(values)&(values>0)]
                        if not len(values):raise ValueError("INPE RTC COG has no valid pixels inside AOI")
                        scene_stats.append({"scene":scene.get("id"),"acquisition_utc":scene.get("acquisition_utc"),
                            "polarization":pol.upper(),"n":int(len(values)),"mean":float(values.mean()),
                            "median":float(np.median(values)),"sd":float(values.std(ddof=1)) if len(values)>1 else 0.0,
                            "min":float(values.min()),"max":float(values.max()),"crs":src.crs.to_string(),
                            "unit":"INPE RTC gamma0 native linear power","pixel_state":"PROCESSADO"})
                pair.append(pol)
            except Exception as exc:
                errors.append({"scene":scene.get("id"),"polarization":pol.upper(),
                               "error_type":type(exc).__name__,"error":str(exc)[:240]})
        if pair==["vv","vh"]:
            stats.extend(scene_stats)
            if len({x["scene"] for x in stats})>=min(3,limit):break
    return {"available":bool(stats),"provider":"INPE Sentinel-1 RTC COG","collection":found.get("collection"),
            "catalogued":len(scenes),"scene_ids":scene_ids,"stats":stats,"errors":errors,
            "pixel_state":"PROCESSADO" if stats else "CATALOGO_OK_PIXEL_READ_FAILED",
            "pagination_complete":found.get("pagination_complete",False),
            "warning":"INPE Sentinel-1 RTC VV/VH C-band pixels are ancillary evidence, not AGB estimates."}

def _jaxa_mosaic_gamma0_db(dn,cf=-83.0):
    """JAXA global mosaic DN -> gamma0 dB: 10*log10(DN^2)+CF."""
    a=np.asarray(dn,dtype=np.float64)
    with np.errstate(divide="ignore",invalid="ignore"):
        return 10.0*np.log10(np.square(a))+float(cf)

def _planetary_sign_asset(unsigned_href, *, max_attempts=3, sleep=None):
    """Sign one Planetary Computer asset, respecting transient rate limits.

    The returned URL is used only for raster access; never log signed SAS tokens.
    401/403 are not retried, and exhausted 429s retain their HTTP error status.
    """
    import random
    from datetime import datetime, timezone
    from email.utils import parsedate_to_datetime
    if not isinstance(unsigned_href, str) or not unsigned_href.startswith("https://"):
        raise ValueError("unsigned Planetary Computer asset must use HTTPS")
    sleep = sleep or time.sleep
    endpoint = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
    max_attempts = max(1, min(int(max_attempts), 5))
    for attempt in range(max_attempts):
        try:
            # Bound proxy/TLS stalls so a failed sign service cannot prevent
            # the pipeline from reaching its remaining SAR and inventory routes.
            response = requests.get(endpoint, params={"href": unsigned_href}, timeout=(15, 45))
            response.raise_for_status()
            signed = response.json()["href"]
            if not isinstance(signed, str) or not signed.startswith("https://"):
                raise ValueError("invalid signed Planetary Computer asset URL")
            return signed
        except requests.exceptions.RequestException as exc:
            code = getattr(getattr(exc, "response", None), "status_code", None)
            transient = code in (429, 500, 502, 503, 504) or isinstance(
                exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))
            if not transient or attempt + 1 >= max_attempts:
                raise
            header = getattr(getattr(exc, "response", None), "headers", {}) or {}
            retry = header.get("Retry-After")
            delay = None
            if retry is not None:
                try:
                    delay = float(retry)
                except (ValueError, TypeError):
                    try:
                        date = parsedate_to_datetime(str(retry))
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        delay = (date - datetime.now(timezone.utc)).total_seconds()
                    except (ValueError, TypeError, OverflowError, IndexError):
                        pass
            # Cap retry delay; never bypass provider quotas or retry indefinitely.
            # If the server asks for more than our bounded 15-second wait,
            # stop instead of retrying before the service permits it.
            if delay is not None and delay > 15.0:
                raise
            backoff = min(8.0, 2.0 ** attempt) + random.uniform(0.0, 0.25)
            sleep(max(backoff, max(0.0, delay)) if delay is not None else backoff)
    raise AssertionError("unreachable")


def planetary_alos_palsar(gdf,cache,limit=12):
    """Credential-free L-band route: JAXA ALOS/PALSAR annual 25 m mosaic on Planetary Computer.
    Processes real HH/HV pixels inside the AOI. No AGB is fabricated without calibration."""
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__; bbox=list(map(float,gdf.to_crs(4326).total_bounds))
    body={"collections":["alos-palsar-mosaic"],"bbox":bbox,"limit":limit,"sortby":[{"field":"properties.datetime","direction":"desc"}]}
    api="https://planetarycomputer.microsoft.com/api/stac/v1/search"
    try:
        rr=requests.post(api,json=body,timeout=(5,15))
        rr.raise_for_status()
        items=rr.json().get("features",[])
    except requests.exceptions.RequestException as exc:
        # A catalog 401/403 is not evidence of missing SAR or zero biomass.
        # Return an auditable data-access failure so alternative calibrated
        # providers may run, while mandatory real-pixel CI gates still fail.
        code=getattr(getattr(exc,"response",None),"status_code",None)
        return {"available":False,"items":0,"scene_ids":[],"paths":[],
                "stats":[],"errors":[f"ALOS/PALSAR STAC indisponível (HTTP {code}): {exc}"],
                "asset_keys_by_scene":[],"missing_polarizations":["HH","HV"],
                "provider":"JAXA ALOS/PALSAR Annual Mosaic via Microsoft Planetary Computer",
                "band":"L","pixel_state":"NAO_PROCESSADO",
                "access_status":"AUTH_REQUIRED" if code in (401,403) else "REMOTE_UNAVAILABLE"}
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    stats=[]; errors=[]; scene_ids=[]; paths=[]; selected_item=None
    items=_newest_first(items)
    for it in items:
        scene_ids.append(it.get("id")); assets=it.get("assets") or {}
        scene_stats=[]; scene_paths=[]
        for pol in ("HH","HV"):
            a=assets.get(pol) or assets.get(pol.lower())
            if not a or not a.get("href"):continue
            try:
                href=_planetary_sign_asset(a["href"])
                import tls_setup
                with rasterio.Env(**tls_setup.gdal_env(),GDAL_HTTP_MULTIRANGE="YES",GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES"):
                    with rasterio.open(href) as src:
                        gj=transform_geom("EPSG:4326",src.crs,geom); ar,_=mask(src,[gj],crop=True,filled=False)
                        v=np.ma.array(ar[0]).compressed(); v=v[np.isfinite(v)&(v>0)]
                        if not len(v):continue
                        db=_jaxa_mosaic_gamma0_db(v,-83.0)
                        scene_stats.append({"scene":it.get("id"),"polarization":pol.upper(),"n":int(len(v)),"mean_dn":float(v.mean()),"mean_db":float(db.mean()),"sd_db":float(db.std(ddof=1)) if len(db)>1 else 0.0,"calibration":"JAXA gamma0 dB = 10*log10(DN^2)-83","pixel_state":"PROCESSADO"})
                        scene_paths.append(a["href"])
            except Exception as e:errors.append(str(it.get("id"))+" / "+pol+": "+str(e))
        # Never combine HH and HV from different acquisition scenes in one dual-pol model.
        if {"HH","HV"}.issubset({str(x.get("polarization","")).upper() for x in scene_stats}):
            stats=scene_stats; paths=scene_paths; selected_item=it; break
        if len(scene_stats)>len(stats):
            stats=scene_stats; paths=scene_paths; selected_item=it
    from sar_acquisition_time import annotate_acquisition
    selected=annotate_acquisition(selected_item) if selected_item else {}
    return {"available":bool(items),"items":len(items),"scene_ids":scene_ids,
            "selected_scene_id":selected_item.get("id") if selected_item else None,
            "selected_acquisition_utc":selected.get("acquisition_utc"),
            "selected_acquisition_brasilia":selected.get("acquisition_brasilia"),
            "catalog_acquisition": [dict(id=x.get("id"), acquisition_utc=annotate_acquisition(x)["acquisition_utc"]) for x in items[:limit]],
            "paths":paths,"stats":stats,"errors":errors,"asset_keys_by_scene":[{"scene":it.get("id"),"keys":sorted((it.get("assets") or {}).keys())} for it in items],"missing_polarizations":[pol for pol in ("HH","HV") if not any(str(x.get("polarization","")).upper()==pol for x in stats)],"provider":"JAXA ALOS/PALSAR Annual Mosaic via Microsoft Planetary Computer","band":"L","pixel_state":"PROCESSADO" if stats else "NAO_PROCESSADO"}

def lband_dualpol_diagnostic(stats,biome="",phys="",prior_agb_mg_ha=None):
    """Summarize dual-pol L-band evidence and saturation risk without inventing an AGB regression."""
    by={str(x.get("polarization","")).upper():x for x in (stats or [])}
    if "HH" not in by or "HV" not in by:return None
    hh=float(by["HH"]["mean_db"]); hv=float(by["HV"]["mean_db"])
    hh_lin=10.0**(hh/10.0); hv_lin=10.0**(hv/10.0)
    denom=hh_lin+hv_lin
    rfdi=(hh_lin-hv_lin)/denom if denom>0 else None
    ratio=(hv_lin/hh_lin) if hh_lin>0 else None
    contrast=hh-hv
    b=str(biome or "").casefold(); p=str(phys or "").casefold()
    moist=("amaz" in b and ("ombrofila densa" in p or "ombrófila densa" in p or "floresta densa" in p))
    prior=float(prior_agb_mg_ha) if prior_agb_mg_ha is not None else None
    # Published L-band literature reports tropical moist-forest sensitivity loss around
    # ~150–200 Mg/ha; Cartus et al. (2016) restricted tropical-moist fitting to <=155 Mg/ha.
    high_biomass=bool(prior is not None and prior>155.0)
    saturation_risk="high" if moist and high_biomass else ("moderate" if moist else "context_dependent")
    quantitative_ok=not (moist and high_biomass)
    return {
      "hh_gamma0_db":hh,"hv_gamma0_db":hv,"hh_minus_hv_db":contrast,
      "hv_over_hh_linear":ratio,"rfdi":rfdi,
      "prior_agb_mg_ha":prior,
      "saturation_risk":saturation_risk,
      "quantitative_agb_from_dualpol_permitted":quantitative_ok,
      "role":"SAR_ESTRATIFICADOR" if not quantitative_ok else "SAR_CANDIDATO_REQUER_CALIBRACAO_LOCAL",
      "reason":("floresta tropical úmida com AGB de referência acima do domínio de sensibilidade dual-pol L-band; usar HH/HV para diagnóstico/estratificação, não para converter diretamente em AGB"
                if not quantitative_ok else
                "dual-pol fisicamente utilizável, mas ainda exige equação local/regional calibrada com pares parcela–pixel independentes"),
      "references":[
        {"source":"Cartus et al. (2016), Remote Sensing 8:522","doi":"10.3390/rs8060522",
         "note":"sensibilidade L-band global; ajuste de floresta tropical úmida limitado a AGB <=155 Mg/ha"},
        {"source":"Mitchard et al. (2009), Geophysical Research Letters 36:L23401","doi":"10.1029/2009GL040692",
         "note":"HV mais sensível que HH; perda de sensibilidade em biomassa alta"},
        {"source":"Narvaes et al. (2023), Forests 14:941","doi":"10.3390/f14050941",
         "note":"Tapajós: modelo quantitativo robusto exige atributos full-pol adicionais a HH"}
      ]
    }

def planetary_sentinel1_cog(gdf,cache,limit=8):
    """Public, credential-free Sentinel-1 GRD pixel route via Microsoft Planetary Computer.
    Reads signed Cloud-Optimized GeoTIFF windows for the AOI and reports actual VV/VH pixel statistics.
    This proves SAR pixel processing; it does not fabricate AGB from C-band alone."""
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__
    now=datetime.now(timezone.utc)
    body={"collections":["sentinel-1-grd"],"intersects":geom,"limit":limit,
          "datetime":(now-timedelta(days=30)).isoformat().replace("+00:00","Z")+"/"+now.isoformat().replace("+00:00","Z"),
          "sortby":[{"field":"properties.datetime","direction":"desc"}]}
    api="https://planetarycomputer.microsoft.com/api/stac/v1/search"
    # The public STAC API intermittently returns 502/503/504 on live gates.
    # Retry transient server failures without changing the search or inventing pixels.
    import time
    for attempt in range(3):
        try:
            # A five-second connect timeout is too short for the public
            # planetary STAC endpoint from slower Windows networks. Retry
            # transient failures with bounded backoff while keeping TLS on.
            rr=requests.post(api,json=body,timeout=(15,45))
            rr.raise_for_status()
            items=rr.json().get("features",[])
            break
        except requests.exceptions.RequestException as exc:
            code=getattr(getattr(exc,'response',None),'status_code',None)
            transient=code in (429,500,502,503,504) or isinstance(
                exc,(requests.exceptions.Timeout,requests.exceptions.ConnectionError))
            if not transient or attempt>=2:
                raise
            time.sleep(2*(attempt+1))
    if not items:return {"available":False,"paths":[],"items":0,"stats":[],"errors":["sem cenas Sentinel-1 GRD no AOI"]}
    items=_newest_first(items)
    Path(cache).mkdir(parents=True,exist_ok=True); stats=[]; paths=[]; errors=[]; scene_ids=[]
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    selected_item=None; partial_stats=[]; partial_paths=[]
    for it in items[:min(limit,8)]:
        scene_ids.append(it.get("id")); assets=it.get("assets") or {}
        scene_stats=[]; scene_paths=[]
        for pol in ("vh","vv","hv","hh"):
            a=assets.get(pol)
            if not a or not a.get("href"):continue
            try:
                unsigned=a["href"]; href=_planetary_sign_asset(unsigned)
                with rasterio.open(href) as src:
                    # Sentinel-1 GRD COGs may expose geolocation through GCPs instead of a dataset CRS.
                    # WarpedVRT resolves those GCPs to EPSG:4326 before AOI masking.
                    if src.crs is None:
                        from rasterio.vrt import WarpedVRT
                        with WarpedVRT(src,crs="EPSG:4326") as vrt:
                            arr,_=mask(vrt,[geom],crop=True,filled=False)
                    else:
                        gj=transform_geom("EPSG:4326",src.crs,geom)
                        arr,_=mask(src,[gj],crop=True,filled=False)
                    v=np.ma.array(arr[0]).compressed(); v=v[np.isfinite(v) & (v>0)]
                    if not len(v):raise ValueError("sem pixels válidos no polígono")
                    # GRD DN values are real SAR image pixels. Keep native-domain stats and dB only when values are power-like positive.
                    z={"scene":it.get("id"),"acquisition_utc":(it.get("properties") or {}).get("datetime"),
                       "polarization":pol.upper(),"n":int(len(v)),"mean":float(v.mean()),
                       "sd":float(v.std(ddof=1)) if len(v)>1 else 0.0,"min":float(v.min()),
                       "max":float(v.max()),"pixel_state":"PROCESSADO"}
                    scene_stats.append(z); scene_paths.append(unsigned)
                if {"VV","VH"}.issubset({v["polarization"] for v in scene_stats}):break
            except Exception as e:errors.append(str(it.get("id"))+" / "+pol+": "+str(e))
        # Publish a scene only when both VV and VH were actually read from that
        # same acquisition. Keep incomplete reads separately for diagnostics.
        polarizations={v["polarization"] for v in scene_stats}
        if {"VV","VH"}.issubset(polarizations):
            stats=scene_stats; paths=scene_paths; selected_item=it
            break
        if len(scene_stats)>len(partial_stats):
            partial_stats=scene_stats; partial_paths=scene_paths
    from sar_acquisition_time import annotate_acquisition
    selected=annotate_acquisition(selected_item) if selected_item else {}
    return {"available":bool(stats),"paths":paths,"items":len(items),"scene_ids":scene_ids,
            "selected_scene_id":selected_item.get("id") if selected_item else None,
            "selected_acquisition_utc":selected.get("acquisition_utc"),
            "selected_acquisition_brasilia":selected.get("acquisition_brasilia"),
            "catalog_acquisition":[dict(id=x.get("id"), acquisition_utc=annotate_acquisition(x)["acquisition_utc"]) for x in items[:limit]],
            "stats":stats,"partial_stats":partial_stats,"partial_paths":partial_paths,
            "provider":"Microsoft Planetary Computer / Sentinel-1 GRD COG","errors":errors,
            "pixel_state":"PROCESSADO" if stats else "VV_VH_PAIR_INCOMPLETE" if partial_stats else "NAO_PROCESSADO"}

SUPPORTED_NATIONAL_BIOMES=("Amazônia","Cerrado","Caatinga","Mata Atlântica","Pantanal")
SFB_IFN_BIOMASS_REFERENCE={
    "source":"Serviço Florestal Brasileiro / SNIF / IFN — Painel de Biomassa e Carbono, versão 2025",
    "url":"https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono",
    "scope":"federal dataset with published state-level spatial granularity; filters include biome and vegetation type",
    "role":"national inventory benchmark/allometry catalogue; never a local AOI raster or plot-pixel SAR calibration by itself",
    "equation_count":222,
}

def _canonical_biome_name(biome):
    b=str(biome or "").strip().casefold()
    aliases={"amazonia":"Amazônia","amazônia":"Amazônia","cerrado":"Cerrado","caatinga":"Caatinga",
             "mata atlantica":"Mata Atlântica","mata atlântica":"Mata Atlântica","pantanal":"Pantanal"}
    return aliases.get(b,str(biome or "").strip())

def national_predictive_route_matrix(biome,phys,aoi=None,features=None):
    """Return an auditable national route diagnosis without inventing a biome-wide AGB value.

    Coverage means every supported IBGE class can be diagnosed and routed. It does
    not mean that every class has a published executable SAR equation. Direct
    products remain subject to runtime spatial/quality coverage; IFN/SFB summaries
    are national/state benchmarks, not local AOI predictions.
    """
    b=_canonical_biome_name(biome); p=str(phys or "").strip()
    supported=b in SUPPORTED_NATIONAL_BIOMES
    routes=[
      {"route":"ESA_BIOMASS_FP_AGB_L2B","kind":"direct_spatial_product","eligible":"runtime_check",
       "reason":"priority P-band AGB product when the AOI is inside the official product domain and quality flags pass"},
      {"route":"ESA_CCI_BIOMASS_V7","kind":"direct_spatial_product","eligible":"runtime_check",
       "reason":"historical multissensor AGB product; used only after raw P/L/C processing attempts and with product uncertainty"},
    ]
    refs=[]
    for m in MODEL_REGISTRY:
        if m.get("execution_mode")=="direct_product": continue
        if m.get("biome") not in (b,"*"): continue
        item={"id":m.get("id"),"sensor":m.get("sensor"),"domain":m.get("domain"),
              "executable":bool(m.get("executable")),"predictors":m.get("predictors") or [],
              "constraints":m.get("constraints")}
        if not m.get("executable"):
            item["eligibility"]="reference_only"
        elif features is None:
            item["eligibility"]="requires_exact_predictors_and_domain_check"
        else:
            chosen=select_executable_model(b,p,features,aoi=aoi)
            item["eligibility"]="eligible_now" if chosen and chosen.get("id")==m.get("id") else "ineligible_now"
        refs.append(item)
    lit=literature_fallback(b,p,aoi=aoi) if (supported and aoi is not None) else None
    if not lit and supported:
        lit=national_agb_fallback(b,p,aoi=aoi)
    local_numeric=bool(lit and lit.get("available") and lit.get("agb_mg_ha") is not None)
    if features is not None and supported:
        chosen=select_executable_model(b,p,features,aoi=aoi)
        local_numeric=local_numeric or bool(chosen)
    if not supported:
        state="unsupported_biome_scope"
    elif lit and lit.get("data_origin")=="MODELAGEM_LITERATURA_HIERARQUICA":
        state="hierarchical_model_fallback_available"
    elif local_numeric:
        state="local_numeric_reference_available"
    else:
        state="runtime_product_check_required"
    return {"supported_biome":supported,"biome":b,"physiognomy":p,
            "supported_scope":list(SUPPORTED_NATIONAL_BIOMES),
            "local_numeric_state":state,"biome_mean_permitted":False,
            "direct_product_routes":routes,"registered_model_routes":refs,
            "regional_numeric_fallback":lit,
            "ifn_sfb_reference":dict(SFB_IFN_BIOMASS_REFERENCE),
            "policy":"Priorizar produto/modelo SAR calibrado e domínio válido. Se nenhuma rota quantitativa compatível sobreviver, fornecer AGB por modelagem hierárquica de evidência brasileira, tão fitofisionômica/regional quanto possível, sempre com limite de incerteza explícito; nunca rotular esse fallback como SAR."}

def _earthaccess_requests_session(edl_user="",edl_password="",edl_token=""):
    """Return an authenticated NASA Earthdata requests session without console prompts.
    Priority: explicit GUI credentials/token -> environment -> Windows _netrc/.netrc.
    Nothing is persisted by Enform Verde."""
    try:
        import os, earthaccess
        env_keys=("EARTHDATA_USERNAME","EARTHDATA_PASSWORD","EARTHDATA_TOKEN")
        old={k:os.environ.get(k) for k in env_keys}
        strategy=None; source=None
        try:
            if edl_token:
                os.environ["EARTHDATA_TOKEN"]=str(edl_token); os.environ.pop("EARTHDATA_USERNAME",None); os.environ.pop("EARTHDATA_PASSWORD",None)
                strategy="environment"; source="explicit_token"
            elif edl_user and edl_password:
                os.environ["EARTHDATA_USERNAME"]=str(edl_user); os.environ["EARTHDATA_PASSWORD"]=str(edl_password); os.environ.pop("EARTHDATA_TOKEN",None)
                strategy="environment"; source="explicit_user_password"
            elif os.environ.get("EARTHDATA_TOKEN") or (os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD")):
                strategy="environment"; source="environment"
            else:
                home=Path.home(); netrc=os.environ.get("NETRC")
                candidates=[Path(netrc)] if netrc else [home/"_netrc",home/".netrc"]
                if any(p.exists() for p in candidates):
                    strategy="netrc"; source="netrc"
            if not strategy:return None,{"available":False,"reason":"Earthdata credentials not configured","source":None}
            auth=earthaccess.login(strategy=strategy,persist=False)
            if not getattr(auth,"authenticated",False):
                return None,{"available":False,"reason":"Earthdata authentication rejected","source":source}
            session=earthaccess.get_requests_https_session()
            return session,{"available":True,"reason":"authenticated","source":source}
        finally:
            for k,v in old.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
    except Exception as e:
        return None,{"available":False,"reason":type(e).__name__+": "+str(e)[:240],"source":"earthaccess"}

def automatic_pipeline(gdf,biome,phys,offline_token="",cache=None,library_rows=None,edl_user="",edl_password="",edl_token="",cdse_token="",cdse_client_id="",cdse_client_secret="",biomass_catalog_items=None,biomass_search_audit=None):
    cache=cache or str(Path.home()/".enform_verde"/"sar")
    from datetime import datetime, timezone
    audit={"priority":"P(ESA) > L(NASA/ASF) > X(local/licensed) > C(Copernicus CDSE) > CCI",
           "selection":"MOST_RECENT_ELIGIBLE_WITHIN_SCIENTIFIC_PRIORITY",
           "catalog_checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "recency_rule":"fresh live provider search per AOI; true sensing datetime, not ingestion; newest within compatible product class; unknown dates last",
           "providers":{"earthdata":"independent","copernicus_cdse":"independent","esa_maap":"independent","local":"independent"},
           "biomass_l2b":None,"asf":None,"sentinel1_public":None,"cci":None,"warnings":[]}
    audit["national_route_matrix"]=national_predictive_route_matrix(biome,phys,aoi=gdf)
    audit["height_scope"]=height_scope_contract(biome,phys)

    # 1 — ESA BIOMASS P-band / official L2B AGB.
    if biomass_catalog_items is not None:
        l2items=list(biomass_catalog_items)
        biomass_search_audit=dict(biomass_search_audit or {})
        if not biomass_search_audit:
            biomass_search_audit={"queries":[],"errors":["AUDIT_METADATA_UNAVAILABLE"],
                                  "height_queries_complete":False}
    else:
        try:
            search_result=biomass_l2b_search(gdf,limit=100,return_audit=True)
            if isinstance(search_result,tuple) and len(search_result)==2:
                l2items,biomass_search_audit=search_result
            else:
                l2items=search_result
                biomass_search_audit={"queries":[],"errors":["AUDIT_METADATA_UNAVAILABLE"],"height_queries_complete":False}
        except Exception as e:
            l2items=[];biomass_search_audit={"queries":[],"errors":[type(e).__name__],"height_queries_complete":False}
            audit["warnings"].append("BIOMASS catálogo: "+str(e))
    audit["biomass_search_audit"]=biomass_search_audit
    audit["biomass_l2b"]={"count":len(l2items),"operational_count":sum(1 for x in l2items if x.get("_stage")=="OPERATIONAL"),"ioc_count":sum(1 for x in l2items if x.get("_stage")=="IOC"),"products_discovered":{p:sum(1 for x in l2items if x.get("_product_type")==p) for p in BIOMASS_PRODUCT_TYPES},"items":[_biomass_catalog_summary(x) for x in l2items[:50]],"access_policy":"BiomassLevel2a/2b e IOC; FP_FH__L2A, FP_FH__L2B e FP_AGB_L2B separados; altura FH não implica AGB"}
    # P-band FH is independent from AGB. In 2026 the operational height
    # products are primarily FP_FH__L2A, NOT L2B. A successful live Sinop
    # FH L2A pixel read must reach this automatic route.
    sar_height=None
    fh_products=("FP_FH__L2B", BIOMASS_FH_L2A)
    fh_items=[it for it in l2items if it.get("_product_type") in fh_products]
    audit["biomass_height_catalog"]={
        "fh_count":len(fh_items),
        "product_types":sorted({it.get("_product_type") for it in fh_items})}
    if fh_items:
        try:
            hd=download_maap_height(gdf,offline_token,Path(cache)/"biomass_height",items=fh_items)
            audit["biomass_height"]=hd
            # A FH-only product must not be passed through the AGB classifier
            # just to extract height. Read true georeferenced zonal pixels.
            for height_path in hd.get("paths") or []:
                if role(height_path)!="HEIGHT":
                    continue
                try:
                    z=_zonal(gdf,height_path)
                    if not (z["n"]>0 and math.isfinite(z["mean"]) and z["mean"]>0):
                        continue
                    chosen=next((it for it in fh_items
                                 if str(it.get("id") or "") in str(height_path)),fh_items[0])
                    product_type=chosen.get("_product_type") or BIOMASS_FH_L2A
                    sar_height={
                        "height_mean_m":z["mean"],
                        "height_sd_m":z["sd"],
                        "height_n_valid_pixels":z["n"],
                        "height_pixel_distribution":z.get("pixel_distribution"),
                        "height_definition_compatible_with_H100":True,
                        "height_metric":"ESA BIOMASS upper forest canopy height H100",
                        "height_error_kind":"spatial standard deviation; not measurement uncertainty",
                        "height_interpretation":{
                            "observable":"altura superior do dossel H100",
                            "band":"P",
                            "meaning":"FH mede altura florestal, não biomassa aérea nem árvores individuais",
                            "agb_inference_permitted":False},
                        "product":product_type,"sensor":"ESA BIOMASS","band":"P",
                        "source":"ESA BIOMASS "+product_type+" — altura superior do dossel (H100)",
                        "paths":[str(height_path)],
                        "scene_ids":[chosen.get("id")],
                        "height_route_status":"ALTURA_SAR_PROCESSADA"}
                    audit["biomass_height"]["zonal_height"]=sar_height
                    break
                except (OSError,ValueError,RuntimeError) as exc:
                    audit["warnings"].append("BIOMASS FH raster: "+type(exc).__name__)
            if hd.get("paths") and not sar_height:
                audit["warnings"].append("BIOMASS FH rasters recovered, but no valid georeferenced height pixels in AOI")
        except Exception as exc:
            audit["biomass_height"]={"available":False,"reason":type(exc).__name__+": "+str(exc)[:180]}
    # ESA BIOMASS FH L2A/L2B has priority. If unavailable, use the
    # official ORNL GEDI–TanDEM-X InSAR height+SE product over the Amazon.
    if not sar_height:
        try:
            gtdx=download_gtdx_height(gdf,edl_user,edl_password,edl_token,Path(cache)/"gtdx_height")
            audit["gtdx_height"]=gtdx
            if gtdx.get("available"):
                sar_height={k:v for k,v in gtdx.items() if k.startswith("height_")}
                sar_height.update({k:gtdx[k] for k in ("product","product_id","sensor","band","source") if k in gtdx})
        except Exception as e:
            audit["gtdx_height"]={"available":False,"reason":str(e)}
    from sar_height_absence import build_height_absence_certificate
    audit["height_absence_certificate"]=build_height_absence_certificate(
        biomass_search_audit,audit.get("biomass_height"),audit.get("gtdx_height"))
    height_structure_estimate=None
    if sar_height and sar_height.get("height_definition_compatible_with_H100",True):
        try:
            height_structure_estimate=tapajos_h100_structure_agb(gdf,sar_height,biome,phys)
            audit["height_structure_model"]=height_structure_estimate
        except Exception as e:
            audit["height_structure_model"]={"status":"ERROR","reason":str(e)}
    # Download/read the official L2B product bundle. Open products are attempted without credentials first;
    # an ESA MAAP token is used only when the catalogue asset is technically protected.
    if l2items:
        try:
            d=download_maap_agb(gdf,offline_token,Path(cache)/"biomass",items=l2items)
            audit["biomass_l2b"]["download"]=d
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
        audit["alos_palsar_public"]={"catalogued":al.get("items",0),"scene_ids":al.get("scene_ids",[]),"pixel_state":al.get("pixel_state"),"stats":al.get("stats",[]),"errors":al.get("errors",[])[:4]}
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
        if pc.get("stats"):
            audit["sentinel1_public"]={"route":"Microsoft Planetary Computer signed COG","catalogued":pc.get("items",0),"scene_ids":pc.get("scene_ids",[]),"pixel_state":"PROCESSADO","stats":pc.get("stats",[])}
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
            "pagination_complete":s1inpe.get("pagination_complete")}
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
            audit["sentinel1_public"]={"route":"Sentinel Hub Process API","downloaded":len(c.get("paths",[])),"pixel_state":"PROCESSADO","time_range":c.get("time_range"),"processing":c.get("processing")}
        else:
            c=public_sentinel1_cog(gdf,Path(cache)/"sentinel1_cdse",cdse_token=cdse_token)
            audit["sentinel1_public"]={"route":"catalogue/direct asset fallback","catalogued":c.get("items",0),"downloaded":len(c.get("paths",[])),"scene_ids":c.get("scene_ids",[])}
        if c.get("stats"):
            audit.setdefault("processed_without_agb",[]).append({"source":"Sentinel-1 C","provider":c.get("provider"),"paths":c.get("paths",[]),"stats":c.get("stats",[])})
            audit["warnings"].append("Sentinel-1 C-band processado, mas sem modelo AGB calibrado/validado compatível; busca SAR continua.")
    except Exception as e: audit["warnings"].append("Sentinel-1 CDSE Process API/download: "+str(e))

    # 5 — CCI derived AGB is last quantitative fallback, never ahead of raw P/L processing.
    try:
        cci=cci_history(gdf,Path(cache)/"cci",offline_token or None)
        audit["cci"]={"count":cci.get("items",0),"downloaded":len(cci.get("paths",[])),
                      "version":cci.get("version"),"year":cci.get("year"),
                      "resolution_m":cci.get("resolution_m"),"tiles":cci.get("tiles",[]),
                      "source":cci.get("source"),"errors":cci.get("errors",[])[:8]}
        if cci.get("paths"):
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
    except Exception as e: audit["cci"]={"error":str(e)}

    # Mark the end of every configured live/direct route reached above. A
    # technical failure is not scene absence: preserve it in the audit, but
    # permit a separately labelled inventory contingency only when all
    # configured biomass routes completed without a quantitative AGB/height product.
    audit["sar_sources_exhausted"]=True
    # Only biomass-quantitative AGB or an eligible canopy-height product
    # blocks an inventory contingency. Ancillary SAR pixels (e.g. Sentinel-1
    # C-band screening) are retained in the audit but are not an AGB estimate.
    sar_processed=bool(sar_height)
    audit["sar_pixel_processing_status"]=(
        "ALTURA_SAR_PROCESSADA_SEM_MODELO_AGB" if sar_height else
        "PIXELS_AUXILIARES_PROCESSADOS_SEM_AGB_OU_ALTURA_QUANTITATIVA" if audit.get("processed_without_agb") else
        "NENHUM_PIXEL_SAR_UTILIZAVEL_APOS_ROTAS_CONFIGURADAS")
    fallback_gate=inventory_fallback_gate(
        sar_processed,audit.get("warnings",[]),
        sources_exhausted=bool(audit.get("sar_sources_exhausted")),
        height_processed=bool(sar_height))
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
    result={"status":("SAR_PROCESSADO_SEM_MODELO_AGB" if auxiliary_sar or sar_height else "SAR_NAO_PROCESSADO"),
            "agb_mg_ha":None,"uncertainty_mg_ha":None,
            "data_origin":("SAR_ALTURA_SEM_MODELO_AGB" if sar_height else
                           "SAR_ATRIBUTOS_ESTRATIFICADORES" if auxiliary_sar else "SAR_NAO_PROCESSADO"),
            "source":("pixels de altura SAR reais processados; sem equação AGB quantitativa compatível no domínio científico"
                      if sar_height else "pixels SAR auxiliares reais processados; sem altura/AGB quantitativa compatível"
                      if auxiliary_sar else "nenhum arquivo SAR pôde ser baixado/processado nesta execução"),
            "audit":audit,"literature_reference":lit,"sar_attempted_first":True,
            "inventory_fallback_gate":fallback_gate,
            "message":("Pixels SAR auxiliares foram lidos, mas não há altura/AGB quantitativa de biomassa compatível; após esgotar as rotas de biomassa, pode-se emitir cenário separado de inventário, preservando a trilha e sem chamar inventário de SAR."
                       if audit.get("processed_without_agb") else ("SAR sem pixels utilizáveis após esgotar as rotas configuradas; emitir cenário condicional de inventário e preservar cada falha técnica, sem declarar ausência de cenas."
                       if fallback_gate["eligible"] else "Rotas SAR ainda não esgotadas; a estimativa de inventário permanece bloqueada."))}
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
