import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box
from native_carbon import summarize_native_carbon, COMPARTMENTS, native_class, estimate_native_components
from land_use_sar import run_land_use

class NativeCarbonTests(unittest.TestCase):
    def test_two_native_classes_are_weighted_and_other_uses_not_estimated(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([
            dict(class_name='FOD',source='IBGE+MAPBIOMAS',geometry=box(0,0,60,100)),
            dict(class_name='Savana',source='IBGE+MAPBIOMAS',geometry=box(60,0,80,100)),
            dict(class_name='Pastagem',source='MAPBIOMAS',geometry=box(80,0,100,100))],crs=6933)
        calls=[]
        def estimator(frame,label):
            calls.append(label)
            return {'components':[{'parametro':n,'tc':100 if label=='FOD' else 10} for n in COMPARTMENTS]}
        r=summarize_native_carbon(aoi,classes,estimator)
        self.assertEqual(calls,['FOD','Savana'])
        self.assertAlmostEqual(r['native_area_ha'],.8,places=5)
        self.assertAlmostEqual(r['excluded_other_uses_ha'],.2,places=5)
        self.assertAlmostEqual(r['known_total_tc'],6*(.6*100+.2*10),places=4)
        self.assertAlmostEqual(r['components'][0]['tc_on_all_native_area'],77.5,places=4)

    def test_missing_class_is_not_replaced_by_dominant_class(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([dict(class_name=n,source='IBGE+MAPBIOMAS',geometry=g) for n,g in [('FOD',box(0,0,50,100)),('Campo',box(50,0,100,100))]],crs=6933)
        def estimator(frame,label):return {'components':[{'parametro':'Biomassa aérea','tc':100}]} if label=='FOD' else {'components':[]}
        r=summarize_native_carbon(aoi,classes,estimator)
        self.assertAlmostEqual(r['known_total_tc'],50,places=5)
        self.assertIsNone(r['components'][0]['tc_on_all_native_area'])
        self.assertAlmostEqual(r['components'][0]['missing_native_area_ha'],.5,places=5)
        self.assertFalse(r['complete']);self.assertIsNone(r['total_uncertainty'])

    def test_silviculture_never_enters_native_carbon_regardless_of_source(self):
        for source in ('MAPBIOMAS','IBGE+MAPBIOMAS','SAR_VALIDADO+IBGE','SAR_VALIDADO'):
            for name in ('Silvicultura','Floresta plantada','Eucalipto','Pinus'):
                self.assertIs(native_class(name,source),False,(name,source))
        for source in ('IBGE+MAPBIOMAS','SAR_VALIDADO'):
            self.assertIsNone(native_class('Cobertura arbórea — origem não determinada',source))
            self.assertIsNone(native_class('Floresta natural ou plantada',source))
        self.assertFalse(native_class('Floresta Ombrófila Densa','IBGE+MAPBIOMAS',
                                     {'Floresta Ombrófila Densa':{'planted_forest':True}}))

    def test_ibge_potential_region_without_current_cover_is_not_native_proof(self):
        self.assertIsNone(native_class('Floresta Ombrófila Densa','IBGE'))
        for label in ['Pastagem','Silvicultura','Café','Citrus','Soja']:
            self.assertFalse(native_class(label,'MAPBIOMAS'))
        self.assertFalse(native_class('Cacau','SAR_VALIDADO',{'Cacau':{'parent':'vegetação natural'}}))
        self.assertFalse(native_class('Cacau','SAR_VALIDADO',{'Cacau':{'parent':'uso agropecuário'}}))

    def test_current_agricultural_mask_does_not_become_forest_by_ibge_region(self):
        with tempfile.TemporaryDirectory() as d:
            raster=Path(d)/'map.tif'
            with rasterio.open(raster,'w',driver='GTiff',height=1,width=2,count=1,dtype='uint8',crs=6933,transform=from_origin(0,10,10,10),nodata=0) as dst:dst.write(np.array([[3,15]],dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,20,10)],crs=6933)
            ibge=aoi.copy();ibge['legenda_1']='Floresta Ombrófila Densa'
            land=run_land_use(aoi,Path(d)/'out',mapbiomas_path=str(raster),ibge=ibge)
            rows=land['classes'];self.assertEqual(len(rows),2)
            natural=next(r for r in rows if r['native_status'] is True)
            pasture=next(r for r in rows if r['native_status'] is False)
            self.assertEqual(natural['source'],'IBGE+MAPBIOMAS')
            self.assertEqual(pasture['class_name'],'Pastagem')
            self.assertAlmostEqual(natural['area_pct'],50,places=4)

    def test_accepted_sar_use_overrides_both_maps_and_excludes_crop_carbon(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'forest.tif'
            with rasterio.open(path,'w',driver='GTiff',height=1,width=2,count=1,dtype='uint8',crs=6933,transform=from_origin(0,10,10,10),nodata=0) as dst:dst.write(np.array([[3,3]],dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,20,10)],crs=6933)
            ibge=aoi.copy();ibge['legenda_1']='Floresta Ombrófila Densa'
            predicted=gpd.GeoDataFrame([dict(class_name='Soja',source='SAR_VALIDADO',taxonomy='modelo',geometry=box(0,0,10,10))],crs=6933)
            with patch('land_use_sar.classify_config',return_value=(predicted,{'class_metadata':{'Soja':{'parent':'uso agropecuário'}}})):
                land=run_land_use(aoi,Path(d)/'out',config_path='TEST_ONLY',mapbiomas_path=str(path),ibge=ibge)
            soy=next(r for r in land['classes'] if r['class_name']=='Soja')
            self.assertEqual(soy['source'],'SAR_VALIDADO');self.assertIs(soy['native_status'],False)
            calls=[]
            def estimator(g,p):calls.append(p);return {'components':[]}
            summarize_native_carbon(aoi,gpd.read_file(land['vector_path']),estimator,land['validation']['class_metadata'])
            self.assertEqual(calls,['Floresta Ombrófila Densa'])

    def test_native_carbon_clips_external_class_geometry_and_rejects_overlap(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([dict(class_name='FOD',source='IBGE+MAPBIOMAS',geometry=box(0,0,200,100))],crs=6933)
        r=summarize_native_carbon(aoi,classes,lambda f,p:{'components':[{'parametro':'Biomassa aérea','tc':10}]})
        self.assertAlmostEqual(r['known_total_tc'],10,places=5)
        doubled=gpd.GeoDataFrame([dict(class_name=n,source='IBGE+MAPBIOMAS',geometry=box(0,0,100,100)) for n in ['FOD','Savana']],crs=6933)
        with self.assertRaisesRegex(ValueError,'sobrepostas'):
            summarize_native_carbon(aoi,doubled,lambda f,p:{'components':[]})

    def test_direct_carbon_stock_and_interval_survive_without_agb(self):
        frame=gpd.GeoDataFrame(geometry=[box(-50,-10,-49.999,-9.999)],crs=4326)
        stock={'mean_tc_ha':7,'range_tc_ha':[6,8],'source':'TEST DIRECT CARBON','method':'gravimetria','uncertainty_kind':'IC amostral parcial'}
        with patch('carbon_compartments.tapajos_necromass_components',return_value={}),patch('carbon_compartments.santo_ambrosio_litter_stock_component',return_value=stock),patch('carbon_compartments.infer_uf_from_aoi',return_value='PA'),patch('carbon_compartments.ifn_necromass_component',return_value=None):
            r=estimate_native_components(frame,'Floresta Ombrófila Densa','Amazônia',lambda *a:{},lambda *a:{})
        litter=next(c for c in r['components'] if c['parametro']=='Serapilheira')
        self.assertEqual(litter['tc'],7);self.assertEqual(litter['range_tc_ha'],[6,8])

    def test_report_and_excel_name_physiognomy_and_use_native_total(self):
        from types import SimpleNamespace
        from openpyxl import load_workbook
        from desktop_app import App
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([dict(class_name=n,source=source,geometry=g) for n,source,g in [('FOD','IBGE+MAPBIOMAS',box(0,0,60,100)),('Savana','IBGE+MAPBIOMAS',box(60,0,80,100)),('Pastagem','MAPBIOMAS',box(80,0,100,100))]],crs=6933)
        native=summarize_native_carbon(aoi,classes,lambda g,p:{'components':[{'parametro':n,'tc':100 if p=='FOD' else 10} for n in COMPARTMENTS]})
        with tempfile.TemporaryDirectory() as d:
            land={'vector_path':str(Path(d)/'classes.geojson'),'classes':[],'priority':'SAR; fallback IBGE/MapBiomas','method':'interseção','area_uncertainty':'não quantificada','warnings':[],'validation':None}
            text=SimpleNamespace(get=lambda:'Teste');captured=[]
            stub=SimpleNamespace(project={'land_use':land},name=text,biome=text,phys=text,sensor=text,res=None,tabs=[0,1,2,3],nb=SimpleNamespace(select=lambda v:None),status=SimpleNamespace(set=lambda v:None),_set=lambda w,t:captured.append(t))
            App._present_native_carbon(stub,native,land)
            self.assertIn('FITOFISIONOMIA À QUAL SE APLICA A ESTIMATIVA: FOD',captured[0])
            path=Path(d)/'native.xlsx'
            with patch('desktop_app.filedialog.asksaveasfilename',return_value=str(path)):App.export_excel(stub)
            wb=load_workbook(path)
            self.assertIn('372',wb['Resumo Executivo']['H10'].value)
            self.assertNotIn('465',wb['Resumo Executivo']['H10'].value)
            self.assertEqual(wb['Carbono por Formação']['A4'].value,'FOD')
            self.assertAlmostEqual(wb['Carbono por Formação']['F4'].value,60,places=4)

    def test_soil_provider_receives_native_stratum_not_whole_property(self):
        frame=gpd.GeoDataFrame(geometry=[box(-50,-10,-49.999,-9.999)],crs=4326)
        called=[]
        def sar(g,b,p):called.append(('sar',g.geometry.iloc[0].area));return {'agb_mg_ha':10,'data_origin':'SAR','source':'TEST'}
        def soil(g):called.append(('soil',g.geometry.iloc[0].area));return {'0–30 cm':{'tc_ha':5}}
        with patch('carbon_compartments.infer_uf_from_aoi',return_value='PA'),patch('carbon_compartments.ifn_necromass_component',return_value=None):
            r=estimate_native_components(frame,'Formação Campestre','Cerrado',sar,soil)
        self.assertEqual([x[0] for x in called],['sar','soil'])
        self.assertFalse(any(c['parametro']=='Biomassa subterrânea' for c in r['components']))
        self.assertEqual(next(c['tc'] for c in r['components'] if c['parametro']=='Solo 0–30 cm'),5)

if __name__=='__main__':unittest.main()
