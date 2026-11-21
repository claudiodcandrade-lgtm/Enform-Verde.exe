import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
script=Path(__file__).resolve().parents[1]/'tools'/'harvest_sfb_biomass_panel.py'
spec=importlib.util.spec_from_file_location('harvest_sfb',script)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class FakeRequestException(Exception): pass
class FakeChunkedEncodingError(FakeRequestException): pass
class FakeHTTPError(FakeRequestException): pass
fake_requests=SimpleNamespace(exceptions=SimpleNamespace(RequestException=FakeRequestException,
 ChunkedEncodingError=FakeChunkedEncodingError),Session=object)
class HarvestSfbTests(unittest.TestCase):
 def test_parse_official_semicolon_csv(self):
  payload=('ua;bioma;agb_media_kg_por_ha\nU1;Amazônia;120000\n').encode()
  rows,cols=module.parse_table(payload,{'ua','bioma','agb_media_kg_por_ha'})
  self.assertEqual(rows[0]['agb_media_kg_por_ha'],'120000')
 def test_refuse_incomplete_table(self):
  with self.assertRaises(ValueError):module.parse_table(b'ua;bioma\nU1;Amazonia\n',{'ua','agb_media_kg_por_ha'})
 def test_header_normalization_handles_accents(self):
  payload=('equações;bioma\n1;Amazônia\n').encode()
  rows,_=module.parse_table(payload,{'equacoes','bioma'})
  self.assertEqual(len(rows),1)
 def test_interrupted_download_resumes_with_verified_range(self):
  payload=b'header;value\n' + b'x'*100
  class Response:
   def __init__(self,status,headers,chunks): self.status_code=status;self.headers=headers;self.chunks=chunks
   def raise_for_status(self):
    if self.status_code>=400: raise FakeHTTPError(str(self.status_code))
   def iter_content(self,chunk_size):
    for part in self.chunks:
     if isinstance(part,Exception): raise part
     yield part
   def __enter__(self): return self
   def __exit__(self,*args): return False
  class Session:
   def __init__(self): self.calls=[]
   def get(self,url,**kwargs):
    self.calls.append(kwargs)
    if len(self.calls)==1:
     return Response(200,{'Content-Length':str(len(payload)),'ETag':'"v1"'},[payload[:50],FakeChunkedEncodingError('connection reset')])
    start=int(kwargs['headers']['Range'].split('=')[1][:-1])
    return Response(206,{'Content-Range':f'bytes {start}-{len(payload)-1}/{len(payload)}','ETag':'"v1"'},[payload[start:]])
  session=Session()
  with TemporaryDirectory() as td:
   with patch.dict('sys.modules',{'requests':fake_requests}):
    out=module.download_blob('https://example.test/panel.csv',Path(td)/'panel.csv',session=session,sleep=lambda _:None)
  self.assertEqual(out,payload)
  self.assertEqual(session.calls[1]['headers']['Range'],'bytes=50-')
  self.assertEqual(session.calls[1]['headers']['If-Range'],'"v1"')
 def test_server_ignoring_range_restarts_instead_of_appending(self):
  payload=b'fresh-complete-object'
  class Response:
   def __init__(self,chunks): self.status_code=200;self.headers={'Content-Length':str(len(payload)),'ETag':'"v1"'};self.chunks=chunks
   def raise_for_status(self): pass
   def iter_content(self,chunk_size):
    for part in self.chunks:
     if isinstance(part,Exception): raise part
     yield part
   def __enter__(self): return self
   def __exit__(self,*args): return False
  class Session:
   def __init__(self): self.calls=[]
   def get(self,url,**kwargs):
    self.calls.append(kwargs)
    if len(self.calls)==1:return Response([payload[:7],FakeChunkedEncodingError('connection reset')])
    return Response([payload])
  session=Session()
  with TemporaryDirectory() as td:
   with patch.dict('sys.modules',{'requests':fake_requests}):
    out=module.download_blob('https://example.test/panel.csv',Path(td)/'panel.csv',session=session,sleep=lambda _:None)
  self.assertEqual(out,payload)
  self.assertIn('Range',session.calls[1]['headers'])
if __name__=='__main__':unittest.main()
