"""Harvest official SFB IFN biomass and equation reference tables."""
from __future__ import annotations
import csv, hashlib, io, json, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SOURCES={
 'biomass':('https://dados.florestal.gov.br/dataset/2d579a3b-29f7-41af-b35c-8fb8f51ef819/resource/06203c8a-c13e-498c-8804-f32e991c17ba/download/dadosabertos_dadosbiomassa_painelbiomassacarbono_snif_fonte_ifn_sfb.csv', DATA/'sfb_ifn_biomass_v1.csv'),
 'equations':('https://dados.florestal.gov.br/dataset/2d579a3b-29f7-41af-b35c-8fb8f51ef819/resource/a209cbbe-1dd6-4217-8662-658ed1e7e1e6/download/dadosabertos_equacoes_painelbiomassacarbono_snif_fonte_ifn_sfb.csv', DATA/'sfb_ifn_biomass_equations_v1.csv'),
}
REQUIRED={
 'biomass':{'ua','lon_pc','lat_pc','bioma','uf','tipologia_da_vegetacao','classe_uso_da_terra','equacoes','area_ha','agb_media_kg_por_ha','agb_variancia_por_ua','valor_r'},
 'equations':{'id','bioma','tipologia','equacao','autor','fonte'},
}
def _norm(s):
    text=unicodedata.normalize('NFKD',str(s).casefold())
    return ''.join(c for c in text if c.isalnum() and not unicodedata.combining(c))
def parse_table(blob, required):
    text=blob.decode('utf-8-sig')
    try: dialect=csv.Sniffer().sniff(text[:8192],delimiters=';,\t')
    except csv.Error: dialect=csv.excel; dialect.delimiter=';'
    reader=csv.DictReader(io.StringIO(text),dialect=dialect)
    rows=list(reader); columns=list(reader.fieldnames or [])
    normalized={_norm(c) for c in columns}
    missing={_norm(c) for c in required}-normalized
    if not rows or missing: raise ValueError(f'CSV SFB inválido: {len(rows)} linhas; colunas canônicas ausentes={sorted(missing)}')
    return rows,columns

def main():
    import requests
    DATA.mkdir(parents=True,exist_ok=True); manifest={'source':'Serviço Florestal Brasileiro / IFN — Painel de Biomassa e Carbono','retrieved_utc':datetime.now(timezone.utc).isoformat(),'assets':{}}
    for key,(url,path) in SOURCES.items():
        response=requests.get(url,timeout=90); response.raise_for_status(); blob=response.content
        if not blob or b'<html' in blob[:1000].lower(): raise RuntimeError(f'{key}: download vazio ou HTML')
        rows,columns=parse_table(blob,REQUIRED[key]); path.write_bytes(blob)
        manifest['assets'][key]={'url':url,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(blob).hexdigest(),'rows':len(rows),'columns':columns}
    (DATA/'sfb_ifn_biomass_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:{'rows':v['rows'],'sha256':v['sha256']} for k,v in manifest['assets'].items()},ensure_ascii=False))
if __name__=='__main__': main()
