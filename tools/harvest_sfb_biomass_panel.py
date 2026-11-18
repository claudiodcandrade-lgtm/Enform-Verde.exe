"""Harvest official SFB IFN biomass and equation reference tables."""
from __future__ import annotations
import csv, hashlib, io, json, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import re
import time

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

def download_blob(url, destination, *, session=None, max_attempts=5, chunk_size=1024*1024, sleep=time.sleep):
    """Download a public SFB CSV with bounded retries and HTTP Range resume.

    Never replaces the validated destination with a partial file. A partial
    response is resumed only with a matching Content-Range; if the server
    ignores Range, the response is safely restarted from byte zero.
    """
    import requests
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    part=destination.with_name(destination.name+'.download-part')
    # A leftover from an interrupted earlier invocation has no persisted
    # validator, so start a fresh transfer. Retries within this invocation
    # retain the part file and resume it safely.
    part.unlink(missing_ok=True)
    client=session or requests.Session()
    validator=None
    last_error=None
    for attempt in range(max_attempts):
        offset=part.stat().st_size if part.exists() else 0
        headers={'Accept-Encoding':'identity'}
        if offset:
            headers['Range']=f'bytes={offset}-'
            if validator:
                headers['If-Range']=validator
        try:
            with client.get(url,headers=headers,timeout=(15,90),stream=True) as response:
                if response.status_code==416:
                    match=re.search(r'bytes \*/(\d+)',response.headers.get('Content-Range',''))
                    if match and offset==int(match.group(1)):
                        return _finish_download_part(part)
                    part.unlink(missing_ok=True)
                    validator=None
                    raise requests.exceptions.ChunkedEncodingError('Range 416 com arquivo parcial incompleto; reiniciando')
                response.raise_for_status()
                response_validator=response.headers.get('ETag') or response.headers.get('Last-Modified')
                if offset and validator and response_validator and validator!=response_validator:
                    part.unlink(missing_ok=True)
                    validator=response_validator
                    raise requests.exceptions.ChunkedEncodingError('O objeto remoto mudou durante o download; reiniciando')
                if offset and response.status_code==206:
                    match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+|\*)',response.headers.get('Content-Range',''))
                    if not match or int(match.group(1))!=offset:
                        part.unlink(missing_ok=True)
                        raise requests.exceptions.ChunkedEncodingError('Content-Range não corresponde ao offset solicitado')
                    expected_total=None if match.group(3)=='*' else int(match.group(3))
                    mode='ab'
                else:
                    # A 200 response to Range means the provider ignored it;
                    # replace the partial bytes instead of duplicating them.
                    offset=0
                    expected_total=int(response.headers['Content-Length']) if response.headers.get('Content-Length','').isdigit() else None
                    mode='wb'
                validator=response_validator or validator
                with part.open(mode) as stream:
                    for block in response.iter_content(chunk_size=chunk_size):
                        if block:
                            stream.write(block)
            received=part.stat().st_size
            if expected_total is not None and received!=expected_total:
                raise requests.exceptions.ChunkedEncodingError(
                    f'Download incompleto: {received} de {expected_total} bytes')
            return _finish_download_part(part)
        except (requests.exceptions.RequestException, OSError) as exc:
            last_error=exc
            if attempt+1>=max_attempts:
                break
            sleep(min(2**attempt,8))
    part.unlink(missing_ok=True)
    raise RuntimeError(f'Falha ao baixar CSV SFB após {max_attempts} tentativas: {last_error}') from last_error

def _finish_download_part(part):
    blob=part.read_bytes()
    if not blob:
        raise RuntimeError('Download SFB vazio')
    part.unlink(missing_ok=True)
    return blob

def main():
    import requests
    DATA.mkdir(parents=True,exist_ok=True); manifest={'source':'Serviço Florestal Brasileiro / IFN — Painel de Biomassa e Carbono','retrieved_utc':datetime.now(timezone.utc).isoformat(),'assets':{}}
    for key,(url,path) in SOURCES.items():
        blob=download_blob(url,path)
        if not blob or b'<html' in blob[:1000].lower(): raise RuntimeError(f'{key}: download vazio ou HTML')
        rows,columns=parse_table(blob,REQUIRED[key])
        temp=path.with_name(path.name+'.validated.tmp')
        temp.write_bytes(blob); temp.replace(path)
        manifest['assets'][key]={'url':url,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(blob).hexdigest(),'rows':len(rows),'columns':columns}
    (DATA/'sfb_ifn_biomass_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:{'rows':v['rows'],'sha256':v['sha256']} for k,v in manifest['assets'].items()},ensure_ascii=False))
if __name__=='__main__': main()
