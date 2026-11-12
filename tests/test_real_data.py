"""Real OSM geometry regression plus explicitly synthetic API contract checks."""
import json,math,pathlib,sys,unittest,xml.etree.ElementTree as ET
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from route_pipeline import audit,road_type,parse_amap_v5
from extract_osm_sample import extract
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RealData(unittest.TestCase):
    def test_real_osm_gpx_coordinates_match(self):
        route=json.loads((ROOT/'data/evidence/phase4/osm-road-sample.json').read_text())['route']
        g=ET.parse(ROOT/'data/evidence/phase4/TEST_ONLY-osm-road-geometry.gpx').getroot()
        ns={'g':'http://www.topografix.com/GPX/1/1'}
        self.assertEqual(g.attrib['version'],'1.1');self.assertIn('creator',g.attrib)
        segs=g.findall('g:trk/g:trkseg',ns);self.assertEqual(len(segs),3)
        for seg,coords in zip(segs,route['segments']):
            pts=seg.findall('g:trkpt',ns)
            self.assertEqual([[float(p.attrib['lon']),float(p.attrib['lat'])] for p in pts],coords)
            self.assertTrue(all(p.find('g:ele',ns) is None for p in pts))
        self.assertEqual([r['osm_way_id'] for r in route['roads']],['263609699','763969650','763969656'])
        for prev,nxt in zip(route['roads'],route['roads'][1:]): self.assertEqual(prev['node_ids'][-1],nxt['node_ids'][0])
        self.assertTrue(audit(route)['geometry_screen_pass'])
    def test_real_distance_independent_formula(self):
        route=json.loads((ROOT/'data/evidence/phase4/osm-road-sample.json').read_text())['route'];length=0
        for seg in route['segments']:
            for a,b in zip(seg,seg[1:]):
                lon1,lat1,lon2,lat2=map(math.radians,[*a,*b])
                h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
                length+=6371008.8*2*math.asin(math.sqrt(h))
        self.assertLess(abs(length-audit(route)['geometry_distance_m'])/length,0.005)
        self.assertTrue(2000<length<5000)
    def test_documented_type_not_name_guess(self):
        self.assertEqual(road_type({'navi':{'walk_type':'23'}})['label'],'tunnel')
        self.assertEqual(road_type({'walk_type':'22'})['label'],'bridge')
        self.assertIn('unknown',road_type({'road_name':'测试桥'}))
    def test_documented_step_distance(self):
        # SYNTHETIC; field names from live official documentation, not a live route.
        d={'status':'1','infocode':'10000','route':{'paths':[{'distance':'100','steps':[{'step_distance':'100','polyline':'109,34;109.001,34'}]}]}}
        self.assertEqual(parse_amap_v5(d)['roads'][0]['distance_m'],'100')
    def test_extractor_rejects_disconnected_and_restricted(self):
        # SYNTHETIC failure fixture, distinct from real OSM observations above.
        raw=b'<osm><node id="1" lon="0" lat="0"/><node id="2" lon="0.001" lat="0"/><way id="a"><nd ref="1"/><nd ref="2"/><tag k="highway" v="secondary"/></way><way id="b"><nd ref="1"/><nd ref="2"/><tag k="highway" v="secondary"/><tag k="bicycle" v="no"/></way></osm>'
        with self.assertRaises(ValueError):extract(raw,['a','b'],'synthetic','synthetic')
        with self.assertRaises(ValueError):extract(raw,['b'],'synthetic','synthetic')
if __name__=='__main__':unittest.main()
