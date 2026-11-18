import importlib.util
import unittest
from pathlib import Path
script=Path(__file__).resolve().parents[1]/'tools'/'harvest_sfb_biomass_panel.py'
spec=importlib.util.spec_from_file_location('harvest_sfb',script)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
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
if __name__=='__main__':unittest.main()
