"""All inputs below are SYNTHETIC fixtures, never observations of a real road."""
import copy,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from route_pipeline import parse_amap_v5,audit,export_gpx
from amap_probe import redact,NoRedirect
import gpxpy

def response():
    return {'status':'1','infocode':'10000','route':{'paths':[{'distance':'184.8','steps':[
      {'road_name':'SYNTHETIC_测试桥','distance':'92.4','polyline':'109,34;109.001,34'},
      {'road_name':'SYNTHETIC_普通路','distance':'92.4','polyline':'109.001,34;109.002,34'}]}]}}
class Routes(unittest.TestCase):
    def test_v5_steps_and_distance(self):
        r=parse_amap_v5(response());a=audit(r)
        self.assertTrue(a['geometry_screen_pass']);self.assertEqual(len(r['roads']),2)
        self.assertTrue(r['roads'][0]['special_road_name_clue']);self.assertIn('unknown',r['roads'][0]['special_road_type'])
    def test_business_error(self):
        with self.assertRaises(ValueError): parse_amap_v5({'status':'0','infocode':'10001'})
    def test_missing_polyline(self):
        x=response();del x['route']['paths'][0]['steps'][0]['polyline']
        with self.assertRaises(ValueError): parse_amap_v5(x)
    def test_reject_nan(self):
        x=response();x['route']['paths'][0]['steps'][0]['polyline']='nan,34;109,34'
        with self.assertRaises(ValueError): parse_amap_v5(x)
    def test_gap_not_bridged(self):
        r=parse_amap_v5(response());r['segments'][1]=[[110,34],[110.001,34]]
        a=audit(r);self.assertFalse(a['geometry_screen_pass']);self.assertEqual(len(a['join_gaps']),1)
        self.assertLess(a['geometry_distance_m'],200)
    def test_sparse_edge(self):
        r=parse_amap_v5(response());r['segments']=[[[109,34],[110,34]]]
        self.assertTrue(audit(r)['long_edges'])
    def test_distance_disagreement(self):
        r=parse_amap_v5(response());r['reported_distance_m']=10000
        self.assertFalse(audit(r)['geometry_screen_pass'])
    def test_gcj_gpx_refused(self):
        with self.assertRaises(ValueError): export_gpx(parse_amap_v5(response()))
    def test_wgs84_synthetic_roundtrip(self):
        # Independent WGS84 synthetic input. This is NOT a GCJ-02 conversion.
        r={'source':'SYNTHETIC UNIT TEST ONLY','source_crs':'WGS84','segments':[[[0,0],[0.001,0]]],'test_only':True}
        xml=export_gpx(r);g=gpxpy.parse(xml)
        self.assertEqual(g.version,'1.1');self.assertEqual(len(g.tracks[0].segments[0].points),2)
        self.assertIn('TEST_ONLY',g.name);self.assertIsNone(g.tracks[0].segments[0].points[0].elevation)
    def test_secret_redaction(self):
        key='SYNTHETIC secret / value'
        from urllib.parse import quote_plus
        result=redact({'echo':key,'query':quote_plus(key),'nested':[key]},key)
        self.assertNotIn(key,str(result));self.assertNotIn(quote_plus(key),str(result))
    def test_redirect_refused(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://example.com'))
if __name__=='__main__': unittest.main(verbosity=2)
