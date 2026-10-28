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
            self.assertIn('validation_multiclass_brier',r);self.assertTrue(r['gates']['Pastagem']['eligible']);self.assertFalse(r['gates']['Floresta']['eligible'])
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

    def test_validated_sar_crop_precedes_mapbiomas_crop_layer(self):
        from unittest.mock import patch
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        sar=self.layer([('Soja','SAR_VALIDADO',box(0,0,60,100))])
        mb=self.layer([('Áreas cultivadas','MAPBIOMAS',box(0,0,100,100))])
        validation={'class_metadata':{'Soja':{'parent':'uso agropecuário'}}}
        with tempfile.TemporaryDirectory() as d, \
             patch('land_use_sar.classify_config',return_value=(sar,validation)), \
             patch('land_use_sar.raster_class_polygons',return_value=mb):
            result=run_land_use(aoi,d,config_path='SAR_TEST',mapbiomas_path='TEST_ONLY')
        rows=result['classes']
        sar_row=next(row for row in rows if row['source']=='SAR_VALIDADO')
        map_row=next(row for row in rows if row['source']=='MAPBIOMAS')
        self.assertEqual(sar_row['class_name'],'Soja')
        self.assertAlmostEqual(sar_row['area_ha'],0.6,places=5)
        self.assertAlmostEqual(map_row['area_ha'],0.4,places=5)
        self.assertEqual(result['priority'],'SAR com confiança demonstrada; nas lacunas, IBGE para fitofisionomia e MapBiomas para uso/cobertura atual')

if __name__=='__main__':unittest.main()

class NativeNamingTests(unittest.TestCase):
    def test_ibge_only_names_preserving_structure(self):
        from land_use_sar import name_native_from_ibge
        a=gpd.GeoDataFrame([dict(class_name='Floresta',source='SAR_VALIDADO',taxonomy='SAR',geometry=box(0,0,10,10))],crs=6933)
        ref=gpd.GeoDataFrame([dict(class_name='Savana Arborizada',geometry=box(0,0,10,10)),dict(class_name='Floresta Ombrófila Densa',geometry=box(20,0,30,10))],crs=6933)
        result=name_native_from_ibge(a,ref)
        self.assertEqual(result.iloc[0].class_name,'Floresta Ombrófila Densa')
        self.assertEqual(result.iloc[0].source,'SAR_VALIDADO+IBGE')
        self.assertIn('floresta',result.iloc[0].taxonomy)
        self.assertFalse(any('dist' in c for c in result.columns))
        self.assertAlmostEqual(result.geometry.area.sum(),100)

    def test_height_contract_and_broad_classes(self):
        from land_use_sar import native_height_contract,native_formation
        self.assertIsNone(native_formation('Floresta Ombrófila Densa'))
        self.assertEqual(native_formation('Formação campestre'),'campo')
        cfg={'features':[dict(name='H',unit='m',source='SAR'),dict(name='U',unit='m',source='SAR')]}
        self.assertIsNone(native_height_contract(cfg))
        cfg['native_structure']=dict(height_feature='H',uncertainty_feature='U',validation_reference='institutional validation',uncertainty_kind='interval_half_width')
        self.assertEqual(native_height_contract(cfg),(0,1))
        cfg['features'][0]['source']='optical'
        self.assertIsNone(native_height_contract(cfg))

    def test_backscatter_without_height_cannot_override_native(self):
        with tempfile.TemporaryDirectory() as d:
            config,aoi,_=LandUseTests().fixture(d)
            polygons,_=classify_config(aoi,config,Path(d)/'out')
            self.assertNotIn('Floresta',set(polygons.class_name))
            self.assertNotIn('Grupo: vegetação natural',set(polygons.class_name))

    def test_cartographic_crop_without_independent_confidence_is_generic(self):
        from unittest.mock import patch
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,10,10)],crs=6933)
        mb=gpd.GeoDataFrame([dict(class_name='Soja',source='MAPBIOMAS',taxonomy='MapBiomas',geometry=box(0,0,10,10))],crs=6933)
        with tempfile.TemporaryDirectory() as d, patch('land_use_sar.raster_class_polygons',return_value=mb):
            result=run_land_use(aoi,d)
            self.assertEqual(result['classes'][0]['class_name'],'Áreas cultivadas')
            self.assertIs(result['classes'][0]['native_status'],False)
            self.assertEqual(result['original_source_distributions'][0]['classes'][0]['class_name'],'Soja')


class EmptyMapBiomasCoverageRegression(unittest.TestCase):
    def test_empty_mapbiomas_never_counts_as_verified_cover(self):
        from unittest.mock import patch
        empty=gpd.GeoDataFrame(columns=['class_code','class_name','source','taxonomy','geometry'],
                               geometry='geometry',crs='EPSG:6933')
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs='EPSG:6933')
        with tempfile.TemporaryDirectory() as directory, patch('land_use_sar.raster_class_polygons',return_value=empty):
            result=run_land_use(aoi,directory,mapbiomas_path='test-raster.tif')
        self.assertIsNotNone(result['mapbiomas_failure'])
        self.assertEqual(result['cover_verification'],'COBERTURA_ATUAL_PARCIAL_OU_INDISPONIVEL')


class MapBiomasOutsideRasterRegression(unittest.TestCase):
    def test_aoi_outside_raster_returns_empty_geodataframe(self):
        with tempfile.TemporaryDirectory() as directory:
            raster=Path(directory)/'small.tif'
            with rasterio.open(raster,'w',driver='GTiff',height=10,width=10,
                               count=1,dtype='uint8',crs='EPSG:6933',
                               transform=from_origin(0,10,1,1),nodata=0) as dst:
                dst.write(np.full((10,10),3,dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(100,100,110,110)],crs='EPSG:6933')
            result=raster_class_polygons(aoi,str(raster))
            self.assertTrue(result.empty)
            self.assertEqual(result.crs,rasterio.crs.CRS.from_epsg(6933))


class LargeMapBiomasRegression(unittest.TestCase):
    def test_large_raster_window_is_tiled_without_four_million_cell_rejection(self):
        from land_use_sar import raster_class_polygons
        with tempfile.TemporaryDirectory() as directory:
            raster=Path(directory)/'large_classes.tif'
            width=2100
            height=2100  # 4,410,000 pixels, formerly rejected
            with rasterio.open(raster,'w',driver='GTiff',height=height,width=width,
                               count=1,dtype='uint8',crs='EPSG:6933',
                               transform=from_origin(0,height,1,1),nodata=0,
                               tiled=True,blockxsize=256,blockysize=256) as dst:
                block=np.full((256,256),3,dtype='uint8')
                for _,window in dst.block_windows(1):
                    dst.write(block[:int(window.height),:int(window.width)],1,window=window)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,width,height)],crs='EPSG:6933')
            result=raster_class_polygons(aoi,str(raster))
            self.assertFalse(result.empty)
            self.assertEqual(set(result.class_code),{3})
            self.assertAlmostEqual(result.geometry.area.sum(),width*height,places=3)


class LargePartitionRegression(unittest.TestCase):
    def test_many_same_class_fragments_dissolve_before_partition(self):
        # Synthetic stress case: 2,500 adjacent fragments of one class.
        # The partition must conserve area without per-fragment subtraction.
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,500,500)],crs='EPSG:6933')
        fragments=[dict(class_name='Formação Florestal',source='MAPBIOMAS',
                        taxonomy='MapBiomas',geometry=box(x,y,x+10,y+10))
                   for x in range(0,500,10) for y in range(0,500,10)]
        layer=gpd.GeoDataFrame(fragments,crs='EPSG:6933')
        _,report=partition_land_use(aoi,[layer])
        self.assertEqual(len(report['classes']),1)
        self.assertAlmostEqual(report['classes'][0]['area_ha'],25.0,places=6)
        self.assertAlmostEqual(report['classes'][0]['area_pct'],100.0,places=6)


class GeosOverlayRecoveryRegression(unittest.TestCase):
    def test_precision_fallback_preserves_polygon_area(self):
        from unittest.mock import patch
        from shapely.errors import GEOSException
        import shapely
        from land_use_sar import _robust_polygon_overlay
        left=box(0,0,100,100)
        right=box(50,0,100,100)
        original=shapely.difference
        calls=[0]
        def fail_once(a,b,**kwargs):
            calls[0]+=1
            if calls[0]==1:
                raise GEOSException('Unable to determine overlay result geometry dimension')
            return original(a,b,**kwargs)
        with patch('shapely.difference',side_effect=fail_once):
            result=_robust_polygon_overlay(left,right,'difference')
        self.assertEqual(calls[0],2)
        self.assertAlmostEqual(result.area,5000.0,places=3)

    def test_irrecoverable_overlay_fails_closed(self):
        from unittest.mock import patch
        from shapely.errors import GEOSException
        from land_use_sar import _robust_polygon_overlay
        with patch('shapely.difference',side_effect=GEOSException('unrecoverable')):
            with self.assertRaisesRegex(ValueError,'nenhuma área foi aceita'):
                _robust_polygon_overlay(box(0,0,100,100),box(50,0,100,100),'difference')
