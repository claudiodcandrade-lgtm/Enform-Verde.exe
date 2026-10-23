"""Synthetic fixtures test code only, never scientific accuracy."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box, Point, mapping
from land_use_sar import validation_report, partition_land_use, raster_class_polygons, classify_config, run_land_use

class LandUseTests(unittest.TestCase):
    def layer(self,rows):
        return gpd.GeoDataFrame([dict(class_name=n,source=s,taxonomy=s,geometry=g) for n,s,g in rows],crs=6933)

    def test_high_scores_need_independent_validation(self):
        self.assertFalse(validation_report(['Soja']*49,['Soja']*49,[.999]*49)['gates']['Soja']['eligible'])
        self.assertTrue(validation_report(['Soja']*50,['Soja']*50,[.95]*50)['gates']['Soja']['eligible'])
        self.assertFalse(validation_report(['Soja']*25+['Outro']*25,['Soja']*50,[.999]*50)['gates']['Soja']['eligible'])

    def test_priority_and_no_double_count(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        sar=self.layer([('Soja','SAR_VALIDADO',box(0,0,20,100))])
        ibge=self.layer([('FOD Aluvial','IBGE',box(0,0,70,100))])
        mb=self.layer([('Pastagem','MAPBIOMAS',box(0,0,100,100))])
        _,r=partition_land_use(aoi,[sar,ibge,mb]);by={x['class_name']:x for x in r['classes']}
        for label,area in [('Soja',.2),('FOD Aluvial',.5),('Pastagem',.3)]:
            self.assertAlmostEqual(by[label]['area_ha'],area,places=5)
        self.assertAlmostEqual(sum(x['area_pct'] for x in r['classes']),100)

    def test_conflicting_same_source_uses_fallback(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        conflict=self.layer([('A','SAR_VALIDADO',box(0,0,75,100)),('B','SAR_VALIDADO',box(25,0,100,100))])
        _,r=partition_land_use(aoi,[conflict,self.layer([('IBGE','IBGE',box(0,0,100,100))])])
        self.assertAlmostEqual(next(x['area_ha'] for x in r['classes'] if x['source']=='IBGE'),.5,places=5)

    def test_edge_cell_and_nodata(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'classes.tif'
            with rasterio.open(path,'w',driver='GTiff',height=1,width=2,count=1,dtype='uint8',crs=6933,transform=from_origin(0,10,10,10),nodata=0) as dst:dst.write(np.array([[3,0]],dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(5,0,15,10)],crs=6933)
            _,r=partition_land_use(aoi,[raster_class_polygons(aoi,path)])
            for row in r['classes']:self.assertAlmostEqual(row['area_pct'],50,places=4)
            self.assertEqual(len(r['classes']),2)

    def test_missing_model_and_map_retains_ibge(self):
        with tempfile.TemporaryDirectory() as d:
            aoi=gpd.GeoDataFrame(geometry=[box(-50,-10,-49.99,-9.99)],crs=4326)
            ibge=aoi.copy();ibge['legenda_1']='FOD'
            r=run_land_use(aoi,d,mapbiomas_path=str(Path(d)/'absent.tif'),ibge=ibge)
            self.assertEqual(r['status'],'FALLBACK_CARTOGRAFICO');self.assertEqual(r['classes'][0]['source'],'IBGE');self.assertIsNone(r['validation'])

    def fixture(self,directory):
        root=Path(directory);transform=from_origin(500000,9000000,1000,1000)
        values=np.ones((2,180,180),dtype='float32');values[:,90:,:]=10
        with rasterio.open(root/'features.tif','w',driver='GTiff',height=180,width=180,count=2,dtype='float32',crs=32722,transform=transform,nodata=-9999) as dst:
            dst.write(values);dst.descriptions=('VV','VH');dst.update_tags(sensor='S1',processing='RTC linear',period='2025')
        records=[]
        for role,col in [('train',5),('calibration',45),('validation',100)]:
            for label,offset in [('Pastagem',5),('Floresta',100)]:
                for k in range(60):
                    x,y=transform*(col+2*(k%20)+.5,offset+2*(k//20)+.5)
                    records.append(dict(label=label,split=role,unit_id=role+label+str(k),geometry=Point(x,y)))
        refs=gpd.GeoDataFrame(records,crs=32722);refs.to_file(root/'points.geojson',driver='GeoJSON')
        aoi=gpd.GeoDataFrame(geometry=[box(600000,8870000,610000,8990000)],crs=32722)
        domain=gpd.GeoDataFrame(geometry=[box(499000,8819000,681000,9001000)],crs=32722).to_crs(4326).geometry.iloc[0]
        cfg=dict(institution='TEST SYNTHETIC ONLY',reference_url='https://example.invalid/test',publication_url='https://example.invalid/test',reference_kind='independent_observations',sensor='S1',processing='RTC linear',period='2025',features=[dict(name=n,unit='linear',source='SAR') for n in ['VV','VH']],classes={'Pastagem':{'parent':'uso agropecuário'},'Floresta':{'parent':'vegetação natural'}},domain=mapping(domain),samples='points.geojson',feature_raster='features.tif')
        config=root/'config.json';config.write_text(json.dumps(cfg));return config,aoi,refs

    def test_complete_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            config,aoi,_=self.fixture(d);polygons,r=classify_config(aoi,config,Path(d)/'out')
            self.assertGreater(r['eligible_pixels'],0);self.assertEqual(r['n_validation'],120)
            self.assertIn('validation_multiclass_brier',r);self.assertTrue(all(g['eligible'] for g in r['gates'].values()))
            self.assertFalse(polygons.empty);self.assertTrue((Path(d)/'out'/'validacao_sar.json').exists())

    def test_pseudolabels_and_repeated_units_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            config,aoi,refs=self.fixture(d);cfg=json.loads(config.read_text());cfg['reference_kind']='MapBiomas';config.write_text(json.dumps(cfg))
            with self.assertRaisesRegex(ValueError,'independentes'):classify_config(aoi,config,Path(d)/'out')
            cfg['reference_kind']='independent_observations';config.write_text(json.dumps(cfg))
            refs.loc[1,'unit_id']=refs.loc[0,'unit_id'];refs.to_file(Path(d)/'points.geojson',driver='GeoJSON')
            with self.assertRaisesRegex(ValueError,'unidade independente'):classify_config(aoi,config,Path(d)/'out')

    def test_spatial_validation_leakage_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            config,aoi,refs=self.fixture(d)
            test_index=refs.index[refs.split=='validation'][0]
            refs.loc[test_index,'geometry']=refs.loc[0,'geometry']
            refs.to_file(Path(d)/'points.geojson',driver='GeoJSON')
            with self.assertRaisesRegex(ValueError,'vazamento espacial'):
                classify_config(aoi,config,Path(d)/'out')

    def test_land_use_only_excel_does_not_invent_zero_carbon(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from openpyxl import load_workbook
        from desktop_app import App
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"land-use.xlsx"
            text=SimpleNamespace(get=lambda:"Teste")
            land={'classes':[{'class_name':'FOD','area_ha':1,'area_pct':100,'source':'IBGE','taxonomy':'IBGE'}],
                  'method':'interseção','vector_path':'classes.geojson','validation':None,'warnings':['sem modelo']}
            stub=SimpleNamespace(project={'area_ha':1,'land_use':land},name=text,biome=text,phys=text,sensor=text,
                                 status=SimpleNamespace(set=lambda value:None))
            with patch('desktop_app.filedialog.asksaveasfilename',return_value=str(path)):
                App.export_excel(stub)
            wb=load_workbook(path)
            self.assertIsNone(wb['Resumo Executivo']['C9'].value)
            self.assertEqual(wb['Resumo Executivo']['E9'].value,'NÃO CALCULADO')
            self.assertEqual(wb['Uso do Solo']['A4'].value,'FOD')

    def test_sensor_and_domain_contract(self):
        with tempfile.TemporaryDirectory() as d:
            config,aoi,_=self.fixture(d)
            with rasterio.open(Path(d)/'features.tif','r+') as dst:dst.update_tags(sensor='other')
            with self.assertRaisesRegex(ValueError,'Sensor/processamento'):classify_config(aoi,config,Path(d)/'out')
            outside=gpd.GeoDataFrame(geometry=[box(-40,-5,-39,-4)],crs=4326)
            with self.assertRaisesRegex(ValueError,'fora do domínio'):classify_config(outside,config,Path(d)/'out')

if __name__=='__main__':unittest.main()
