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

class SarAccessFailureTests(unittest.TestCase):
    def test_palsar_401_never_reports_pixels_or_biomass(self):
        import requests
        from sar_pipeline import planetary_alos_palsar
        response=requests.Response()
        response.status_code=401
        response.url='https://planetarycomputer.microsoft.com/api/stac/v1/search'
        error=requests.exceptions.HTTPError('401 Unauthorized',response=response)
        aoi=gpd.GeoDataFrame(geometry=[box(-55,-4,-54.9,-3.9)],crs=4326)
        with patch('sar_pipeline.requests.post',side_effect=error) as request:
            result=planetary_alos_palsar(aoi,'unused')
        request.assert_called_once()
        self.assertFalse(result['available'])
        self.assertEqual(result['access_status'],'AUTH_REQUIRED')
        self.assertEqual(result['pixel_state'],'NAO_PROCESSADO')
        self.assertEqual(result['stats'],[])
        self.assertEqual(result['paths'],[])
        self.assertIn('401',result['errors'][0])


class StrictNecromassPhysiognomyTests(unittest.TestCase):
    def test_unstratified_ifn_biome_uf_necromass_is_not_transferred(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.0,-4.0,-54.99,-3.99)],crs=4326)
        def sar_estimator(frame,biome,physiognomy):
            return {'agb_mg_ha': 100., 'data_origin': 'SAR_QUANTITATIVO',
                    'source': 'Teste sintético'}
        with patch('carbon_compartments.tapajos_necromass_components',return_value={}), patch(
            'carbon_compartments.ifn_necromass_component',
            side_effect=AssertionError('IFN biome×UF is not fitophysiognomy-matched')
        ):
            result=estimate_native_components(
                aoi,'Floresta Estacional Semidecidual','Mata Atlântica',
                sar_estimator,lambda frame: {}
            )
        necro=[x for x in result['components'] if x['parametro']=='Necromassa aérea']
        self.assertEqual(necro, [])


class DisjointNecromassAggregationTests(unittest.TestCase):
    def test_standing_and_fallen_direct_stocks_are_both_counted(self):
        frame=gpd.GeoDataFrame(geometry=[box(-55.0,-4.0,-54.99,-3.99)],crs=4326)
        direct={
            'Necromassa aérea — madeira morta caída': {
                'mean_tc_ha':32.0,'range_tc_ha':[28.3,35.7],
                'source':'Inventário direto microrregional','origin':'INVENTARIO_DIRETO'
            },
            'Necromassa aérea — madeira morta em pé': {
                'mean_tc_ha':8.7,'range_tc_ha':[7.4,10.0],
                'source':'Inventário direto microrregional','origin':'INVENTARIO_DIRETO'
            },
        }
        with patch('carbon_compartments.tapajos_necromass_components',return_value=direct):
            result=estimate_native_components(
                frame,'Floresta Ombrófila Densa','Amazônia',
                lambda *args: {},lambda *args: {},
            )
        necro=[c for c in result['components'] if c['parametro']=='Necromassa aérea']
        self.assertEqual(len(necro),1)
        self.assertAlmostEqual(necro[0]['tc'],40.7)
        self.assertAlmostEqual(necro[0]['range_tc_ha'][0],35.7)
        self.assertAlmostEqual(necro[0]['range_tc_ha'][1],45.7)
        self.assertIn('NÃO é IC95%',necro[0]['obs'])

    def test_total_does_not_inherit_partial_fallen_interval(self):
        frame=gpd.GeoDataFrame(geometry=[box(-55,-4,-54.99,-3.99)],crs=4326)
        stocks={
            'Necromassa aérea — madeira morta caída':{
                'mean_tc_ha':32.0,'range_tc_ha':[28.3,35.7],
                'uncertainty_kind':'IC95% publicado','source':'Inventário microrregional'},
            'Necromassa aérea — madeira morta em pé':{
                'mean_tc_ha':8.7,'source':'Inventário microrregional'},
        }
        with patch('carbon_compartments.tapajos_necromass_components',return_value=stocks):
            result=estimate_native_components(frame,'Floresta Ombrófila Densa',
                'Amazônia',lambda *args:{},lambda *args:{})
        stock=next(x for x in result['components'] if x['parametro']=='Necromassa aérea')
        self.assertAlmostEqual(stock['tc'],40.7)
        self.assertIsNone(stock['range_tc_ha'])
        self.assertEqual(stock['obs'],'Incerteza conjunta não quantificada')

    def test_invalid_direct_stock_cannot_silently_replace_second_stock(self):
        frame=gpd.GeoDataFrame(geometry=[box(-55,-4,-54.99,-3.99)],crs=4326)
        stocks={
            'Necromassa aérea — madeira morta caída':{
                'mean_tc_ha':float('nan'),'source':'Inventário microrregional'},
            'Necromassa aérea — madeira morta em pé':{
                'mean_tc_ha':8.7,'source':'Inventário microrregional'},
        }
        with patch('carbon_compartments.tapajos_necromass_components',return_value=stocks):
            result=estimate_native_components(frame,'Floresta Ombrófila Densa',
                'Amazônia',lambda *args:{},lambda *args:{})
        self.assertFalse(any(x['parametro']=='Necromassa aérea'
            for x in result['components']))

    def test_ambiguous_total_and_subpool_are_not_summed(self):
        frame=gpd.GeoDataFrame(geometry=[box(-55.0,-4.0,-54.99,-3.99)],crs=4326)
        overlapping={
            'Necromassa aérea':{'mean_tc_ha':40.7,'source':'Inventário local'},
            'Necromassa aérea — madeira morta em pé':{
                'mean_tc_ha':8.7,'source':'Inventário local'
            },
        }
        with patch('carbon_compartments.tapajos_necromass_components',return_value=overlapping):
            result=estimate_native_components(
                frame,'Floresta Ombrófila Densa','Amazônia',
                lambda *args: {},lambda *args: {},
            )
        self.assertFalse(any(c['parametro']=='Necromassa aérea' for c in result['components']))


class RootBiomassSourcePriorityTests(unittest.TestCase):
    def test_microrregional_root_component_suppresses_generic_allometry(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-55.0,-4.0,-54.99,-3.99)],crs=4326)
        def sar_estimator(frame,biome,physiognomy):
            return {
                'agb_mg_ha': 100.0,
                'data_origin': 'SAR_QUANTITATIVO',
                'source': 'Teste controlado de regressão',
                'regional_components': {
                    'Biomassa subterrânea — inventário microrregional': {
                        'mean_tc_ha': 19.5,
                        'origin': 'INVENTARIO_MICRORREGIONAL',
                        'source': 'Parcela validada - exemplo sintético',
                    },
                },
            }
        result=estimate_native_components(
            aoi,'Floresta Ombrófila Densa','Amazônia',
            sar_estimator,lambda frame: {},
        )
        roots=[row for row in result['components']
               if row['parametro']=='Biomassa subterrânea']
        self.assertEqual(len(roots),1)
        self.assertEqual(roots[0]['tc'],19.5)
        self.assertEqual(roots[0]['origem'],'INVENTARIO_MICRORREGIONAL')


class NativeCarbonTests(unittest.TestCase):

    def test_two_native_classes_are_weighted_and_other_uses_not_estimated(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([
            dict(class_name='FOD',source='SAR_VALIDADO+IBGE',geometry=box(0,0,60,100)),
            dict(class_name='Savana',source='SAR_VALIDADO+IBGE',geometry=box(60,0,80,100)),
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
        classes=gpd.GeoDataFrame([dict(class_name=n,source='SAR_VALIDADO+IBGE',geometry=g) for n,g in [('FOD',box(0,0,50,100)),('Campo',box(50,0,100,100))]],crs=6933)
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
            self.assertEqual(calls,[])

    def test_native_carbon_clips_external_class_geometry_and_rejects_overlap(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,100,100)],crs=6933)
        classes=gpd.GeoDataFrame([dict(class_name='FOD',source='SAR_VALIDADO+IBGE',geometry=box(0,0,200,100))],crs=6933)
        r=summarize_native_carbon(aoi,classes,lambda f,p:{'components':[{'parametro':'Biomassa aérea','tc':10}]})
        self.assertAlmostEqual(r['known_total_tc'],10,places=5)
        doubled=gpd.GeoDataFrame([dict(class_name=n,source='SAR_VALIDADO+IBGE',geometry=box(0,0,100,100)) for n in ['FOD','Savana']],crs=6933)
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
        classes=gpd.GeoDataFrame([dict(class_name=n,source=source,geometry=g) for n,source,g in [('FOD','SAR_VALIDADO+IBGE',box(0,0,60,100)),('Savana','SAR_VALIDADO+IBGE',box(60,0,80,100)),('Pastagem','MAPBIOMAS',box(80,0,100,100))]],crs=6933)
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
            self.assertAlmostEqual(wb['Carbono por Formação']['G4'].value,60,places=4)
            self.assertAlmostEqual(wb['Carbono por Formação']['H4'].value,60*44/12,places=4)
            self.assertEqual(wb['Carbono por Formação']['H3'].value,'Estoque tCO₂e')

    def test_soil_provider_receives_native_stratum_not_whole_property(self):
        frame=gpd.GeoDataFrame(geometry=[box(-50,-10,-49.999,-9.999)],crs=4326)
        called=[]
        def sar(g,b,p):called.append(('sar',g.geometry.iloc[0].area));return {'agb_mg_ha':10,'data_origin':'SAR','source':'TEST'}
        def soil(g):called.append(('soil',g.geometry.iloc[0].area));return {'0–30 cm':{'tc_ha':5},'0–100 cm':{'tc_ha':999}}
        with patch('carbon_compartments.infer_uf_from_aoi',return_value='PA'),patch('carbon_compartments.ifn_necromass_component',return_value=None):
            r=estimate_native_components(frame,'Formação Campestre','Cerrado',sar,soil)
        self.assertEqual([x[0] for x in called],['sar','soil'])
        self.assertFalse(any(c['parametro']=='Biomassa subterrânea' for c in r['components']))
        self.assertEqual(next(c['tc'] for c in r['components'] if c['parametro']=='Solo 0–100 cm'),999)
        self.assertFalse(any(c['parametro']=='Solo 0–30 cm' for c in r['components']))

if __name__=='__main__':unittest.main()


class WaterExclusionAndOrderingRegression(unittest.TestCase):
    def test_water_never_counts_as_native_even_with_ibge_overlay(self):
        for source in ('IBGE+MAPBIOMAS','SAR_VALIDADO+IBGE','MAPBIOMAS'):
            for label in ("Corpo d'água continental",'Rio, Lago e Oceano'):
                self.assertIs(native_class(label,source),False)

    def test_dense_forest_is_first_and_water_excluded(self):
        aoi=gpd.GeoDataFrame(geometry=[box(0,0,300,100)],crs='EPSG:6933')
        classes=gpd.GeoDataFrame([
            {"class_name":"Corpo d'água continental",'source':'IBGE+MAPBIOMAS','geometry':box(0,0,100,100)},
            {'class_name':'Floresta Ombrófila Aberta','source':'SAR_VALIDADO+IBGE','geometry':box(100,0,200,100)},
            {'class_name':'Floresta Ombrófila Densa','source':'SAR_VALIDADO+IBGE','geometry':box(200,0,300,100)},
        ],crs='EPSG:6933')
        calls=[]
        def estimator(frame,phys):
            calls.append(phys)
            return {'components':[{'parametro':'Biomassa aérea','tc':100.0,'fonte':'teste'}]}
        result=summarize_native_carbon(aoi,classes,estimator)
        self.assertEqual(calls,['Floresta Ombrófila Densa','Floresta Ombrófila Aberta'])
        self.assertEqual([s['class_name'] for s in result['strata']],calls)
        self.assertAlmostEqual(result['native_area_ha'],2.0)
        self.assertAlmostEqual(result['excluded_other_uses_ha'],1.0)
        self.assertAlmostEqual(result['known_total_tc'],200.0,places=5)  # allow sub-gram floating-point geometry rounding



class MapBiomasExcludedFromCurrentCoverRegression(unittest.TestCase):
    """V87.36–V87.39: MapBiomas is never queried for current cover/carbon.

    Replaces former tests that required MapBiomas retrieval/fallback routes
    (cache, HTTPS, retry, local file) to define native cover. Live Sentinel-1
    screening is stubbed so the result is deterministic offline.
    """
    def _run(self, **kw):
        nd={'status':'N/D_DADOS','reason':'teste offline'}
        with tempfile.TemporaryDirectory() as d, \
             patch('recent_sar_landcover.run_recent_sar_screen',return_value=nd), \
             patch('land_use_sar._download_official_mapbiomas') as dl, \
             patch('land_use_sar.raster_class_polygons') as rcp:
            aoi=gpd.GeoDataFrame(geometry=[box(0,0,200,100)],crs=6933)
            ibge=aoi.copy();ibge['legenda_1']='Floresta Ombrófila Densa'
            land=run_land_use(aoi,Path(d)/'out',ibge=ibge,**kw)
            calls=[]
            def estimator(frame,phys):
                calls.append(phys); return {'components':[{'parametro':'Biomassa aérea','tc':10}]}
            native=summarize_native_carbon(aoi,gpd.read_file(land['vector_path']),estimator)
            return land,native,calls,dl,rcp

    def test_mapbiomas_is_not_queried_and_cannot_define_native_cover(self):
        with patch.dict('os.environ',{'ENFORM_MAPBIOMAS_LOCAL_TIF':'/tmp/naoexiste.tif'}):
            land,native,calls,dl,rcp=self._run(mapbiomas_path='/tmp/qualquer.tif')
        dl.assert_not_called(); rcp.assert_not_called()
        self.assertIsNone(land['mapbiomas_source'])
        self.assertTrue(str(land['mapbiomas_failure']).startswith('DESATIVADO'))
        self.assertFalse(any(str(r['source']).startswith('MAPBIOMAS') for r in land['classes']))
        self.assertTrue(all(r['native_status'] is None for r in land['classes']))
        self.assertAlmostEqual(land['unknown_cover_ha'],2.0,places=5)       # whole AOI N/D, not 0
        self.assertEqual(calls,[])                                          # no native carbon
        self.assertIsNone(native['known_total_tc'])
        self.assertAlmostEqual(native['unknown_cover_area_ha'],2.0,places=4)

    def test_ibge_forest_region_never_names_unclassified_area_as_forest(self):
        land,_,_,_,_=self._run()
        self.assertNotIn('Floresta Ombrófila Densa',[r['class_name'] for r in land['classes']])
