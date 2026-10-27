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
    def test_full_native_carbon_pipeline_all_pools_and_anthropic_exclusion(self):
        # Complete synthetic integration gate: land-cover pixels, native
        # intersection, per-pool aggregation, units and exclusion of pasture.
        with tempfile.TemporaryDirectory() as d:
            tif=Path(d)/'mapbiomas_local.tif'
            with rasterio.open(tif,'w',driver='GTiff',width=20,height=10,
                               count=1,dtype='uint8',crs='EPSG:6933',
                               transform=from_origin(0,100,10,10),nodata=0) as dst:
                values=np.full((10,20),15,dtype='uint8')
                values[:,:10]=3
                dst.write(values,1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,200,100)],crs=6933)
            ibge=aoi.copy();ibge['legenda_1']='Floresta Ombrófila Densa'
            land=run_land_use(aoi,Path(d)/'out',mapbiomas_path=str(tif),ibge=ibge)
            self.assertIsNone(land['mapbiomas_failure'])
            self.assertAlmostEqual(land['unknown_cover_ha'],0,places=5)
            calls=[]
            pool_values=[60.0,12.0,3.0,1.0,4.0,70.0]
            def estimator(frame,phys):
                calls.append(phys)
                return {'components':[{'parametro':name,'tc':value,
                                        'fonte':'REF_SINTETICA_TESTE'}
                                       for name,value in zip(COMPARTMENTS,pool_values)]}
            result=summarize_native_carbon(aoi,gpd.read_file(land['vector_path']),estimator)
            self.assertEqual(len(calls),1)
            self.assertAlmostEqual(result['native_area_ha'],1.0,places=4)
            self.assertAlmostEqual(result['excluded_other_uses_ha'],1.0,places=4)
            self.assertAlmostEqual(result['known_total_tc'],150,places=4)
            self.assertAlmostEqual(result['known_total_tco2'],550,places=4)
            self.assertTrue(result['complete'])
            self.assertIsNone(result['total_uncertainty'])
            self.assertEqual(len(result['components']),len(COMPARTMENTS))
            self.assertTrue(all(c['known_total_tc'] is not None
                                for c in result['components']))

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

    def test_mapbiomas_failure_is_not_no_native_vegetation(self):
        with tempfile.TemporaryDirectory() as d:
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
            ibge=aoi.copy()
            ibge['legenda_1']='Floresta Ombrófila Densa'
            with patch('land_use_sar.raster_class_polygons', side_effect=UnicodeDecodeError('utf-8',b'\\xe3',0,1,'invalid start byte')):
                result=run_land_use(aoi,Path(d)/'out',ibge=ibge)
            self.assertEqual(result['cover_verification'],'COBERTURA_ATUAL_PARCIAL_OU_INDISPONIVEL')
            self.assertAlmostEqual(result['unknown_cover_ha'],1.0)
            self.assertEqual(result['classes'][0]['native_status'],None)
            self.assertTrue(any('Cobertura atual não verificada' in w for w in result['warnings']))

    def test_https_download_rejects_truncated_geotiff(self):
        import io
        from land_use_sar import _download_official_mapbiomas
        class TruncatedResponse:
            headers={'Content-Type':'image/tiff','Content-Length':'9000'}
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):return self.data.read(n)
            def __init__(self):self.data=io.BytesIO(b'II'+b'0'*2000)
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'mapbiomas.tif'
            with patch('urllib.request.urlopen',return_value=TruncatedResponse()):
                with self.assertRaisesRegex(ValueError,'truncado'):
                    _download_official_mapbiomas('https://example.test/data.tif',dest)
            self.assertFalse(dest.exists())
            self.assertFalse(dest.with_suffix('.tif.part').exists())

    def test_https_fallback_recovers_after_remote_timeout_message(self):
        with tempfile.TemporaryDirectory() as d:
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
            mapped=gpd.GeoDataFrame([dict(class_code=3,class_name='Formação Florestal',
                                            source='MAPBIOMAS',taxonomy='MapBiomas',
                                            geometry=box(0,0,100,100))],crs=6933)
            failures=[rasterio.errors.RasterioIOError('HTTP timeout')] * 3
            with patch('land_use_sar.raster_class_polygons',side_effect=failures+[mapped]):
                with patch('land_use_sar._download_official_mapbiomas',return_value=Path(d)/'official.tif') as download:
                    report=run_land_use(aoi,Path(d)/'output')
            download.assert_called_once()
            self.assertIsNone(report['mapbiomas_failure'])
            self.assertAlmostEqual(report['unknown_cover_ha'],0,places=4)

    def test_https_fallback_recovers_native_cover_after_vsicurl_failure(self):
        with tempfile.TemporaryDirectory() as d:
            local=Path(d)
            raster=local/'source.tif'
            with rasterio.open(raster,'w',driver='GTiff',height=20,width=20,count=1,
                               dtype='uint8',crs='EPSG:6933',
                               transform=from_origin(0,200,10,10)) as dst:
                dst.write(np.full((20,20),3,dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,200,200)],crs=6933)
            real_open=__import__('land_use_sar').raster_class_polygons
            attempts=[]
            def mocked_open(frame,path,legend=None):
                attempts.append(str(path))
                if str(path).startswith('https://'):
                    raise rasterio.errors.RasterioIOError(
                        '/vsicurl/ official map does not exist in the file system')
                return real_open(frame,str(path),legend)
            import io
            class Response:
                headers={'Content-Type':'image/tiff'}
                def __init__(self,contents):self.stream=io.BytesIO(contents)
                def __enter__(self):return self
                def __exit__(self,*args):self.stream.close()
                def read(self,n):return self.stream.read(n)
            with patch('pathlib.Path.home',return_value=local):
                with patch('land_use_sar.raster_class_polygons',side_effect=mocked_open):
                    with patch('urllib.request.urlopen',return_value=Response(raster.read_bytes())):
                        report=run_land_use(aoi,local/'output')
            self.assertIsNone(report['mapbiomas_failure'])
            self.assertTrue(report['mapbiomas_source'].endswith('.tif'))
            self.assertTrue(Path(report['mapbiomas_source']).exists())
            self.assertAlmostEqual(report['unknown_cover_ha'],0,places=4)
            self.assertGreaterEqual(len(attempts),4)

    def test_previously_working_mapbiomas_route_remains_first_priority(self):
        with tempfile.TemporaryDirectory() as d:
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
            mapped=gpd.GeoDataFrame([dict(class_code=3,class_name='Formação Florestal',
                                           source='MAPBIOMAS',taxonomy='MapBiomas',
                                           geometry=box(0,0,100,100))],crs=6933)
            with patch('land_use_sar.raster_class_polygons',return_value=mapped) as read:
                with patch('land_use_sar._download_official_mapbiomas') as download:
                    report=run_land_use(aoi,Path(d)/'out')
            self.assertIsNone(report['mapbiomas_failure'])
            self.assertEqual(read.call_count,1)
            download.assert_not_called()
            self.assertAlmostEqual(report['unknown_cover_ha'],0.0,places=4)

    def test_mapbiomas_retry_restores_native_carbon(self):
        with tempfile.TemporaryDirectory() as d:
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
            ibge=aoi.copy()
            ibge['legenda_1']='Floresta Ombrófila Densa'
            mapped=gpd.GeoDataFrame([dict(class_code=3,class_name='Formação Florestal',
                                            source='MAPBIOMAS',taxonomy='MapBiomas',
                                            geometry=box(0,0,100,100))],crs=6933)
            transient=UnicodeDecodeError('utf-8',b'\\xe3',0,1,'invalid start byte')
            with patch('land_use_sar.raster_class_polygons',side_effect=[transient,mapped]):
                result=run_land_use(aoi,Path(d)/'out',ibge=ibge)
            self.assertEqual(len(result['mapbiomas_access_attempts']),1)
            self.assertIsNone(result['mapbiomas_failure'])
            self.assertAlmostEqual(result['unknown_cover_ha'],0.0)
            called=[]
            def estimator(frame,phys):
                called.append(phys)
                return {'components':[{'parametro':'Biomassa aérea','tc':100}]}
            carbon=summarize_native_carbon(aoi,gpd.read_file(result['vector_path']),estimator)
            self.assertAlmostEqual(carbon['native_area_ha'],1.0)
            self.assertAlmostEqual(carbon['known_total_tc'],100.0,places=4)  # reprojection/area floating-point tolerance
            self.assertEqual(called,['Floresta Ombrófila Densa'])

    def test_auto_discover_cached_mapbiomas_raster(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            cached=home/'.enform_verde'/'mapbiomas'
            cached.mkdir(parents=True)
            from mapbiomas_zonal import YEAR
            path=cached/f'brazil_coverage-col11_{YEAR}.tif'
            arr=np.full((40,40),3,dtype='uint8')
            with rasterio.open(path,'w',driver='GTiff',height=40,width=40,
                               count=1,dtype='uint8',crs='EPSG:6933',
                               transform=from_origin(0,400,10,10)) as dst:
                dst.write(arr,1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,400,400)],crs=6933)
            with patch('pathlib.Path.home',return_value=home):
                with patch.dict('os.environ',{'ENFORM_MAPBIOMAS_LOCAL_TIF':''}):
                    report=run_land_use(aoi,home/'result')
            self.assertEqual(report['mapbiomas_source'],str(path))
            self.assertIsNone(report['mapbiomas_failure'])
            self.assertAlmostEqual(report['unknown_cover_ha'],0,places=4)

    def test_windows_local_mapbiomas_route_preserves_native_carbon(self):
        with tempfile.TemporaryDirectory() as d:
            raster=Path(d)/'official_mapbiomas_local.tif'
            with rasterio.open(raster,'w',driver='GTiff',height=1,width=2,count=1,dtype='uint8',crs=6933,transform=from_origin(0,10,10,10),nodata=0) as dst:
                dst.write(np.array([[3,15]],dtype='uint8'),1)
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,20,10)],crs=6933)
            ibge=aoi.copy();ibge['legenda_1']='Floresta Ombrófila Densa'
            with patch.dict('os.environ',{'ENFORM_MAPBIOMAS_LOCAL_TIF':str(raster)}):
                report=run_land_use(aoi,Path(d)/'output',ibge=ibge)
            self.assertEqual(report['mapbiomas_source'],str(raster))
            self.assertIsNone(report['mapbiomas_failure'])
            self.assertAlmostEqual(report['unknown_cover_ha'],0,places=4)
            nat=next(row for row in report['classes'] if row['native_status'] is True)
            self.assertAlmostEqual(nat['area_pct'],50,places=4)
            called=[]
            def estimator(frame,phys):
                called.append(phys)
                return {'components':[{'parametro':'Biomassa aérea','tc':10}]}
            result=summarize_native_carbon(aoi,gpd.read_file(report['vector_path']),estimator)
            self.assertAlmostEqual(result['known_total_tc'],0.1,places=4)
            self.assertEqual(called,['Floresta Ombrófila Densa'])

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
