import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from analyze_gpx import analyze
from pyproj import Transformer
from shapely.geometry import LineString
import networkx as nx
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

def gpx(body): return '<gpx version="1.1" creator="SYNTHETIC_TEST_ONLY" xmlns="http://www.topografix.com/GPX/1/1"><trk>'+body+'</trk></gpx>'
class Pipeline(unittest.TestCase):
 def test_distance_and_missing_height(self):
  r=analyze(gpx('<trkseg><trkpt lat="0" lon="0"/><trkpt lat="0" lon="0.01"/></trkseg>'))
  self.assertAlmostEqual(r['distance_km'],1.113,places=3);self.assertIsNone(r['raw_ascent_m']);self.assertEqual(r['missing_elevation_points'],2)
 def test_no_bridging_segments(self):
  r=analyze(gpx('<trkseg><trkpt lat="0" lon="0"/></trkseg><trkseg><trkpt lat="30" lon="110"/></trkseg>'))
  self.assertEqual(r['distance_km'],0)
 def test_elevation_gain_loss(self):
  r=analyze(gpx('<trkseg><trkpt lat="0" lon="0"><ele>10</ele></trkpt><trkpt lat="0" lon="0.001"><ele>30</ele></trkpt><trkpt lat="0" lon="0.002"><ele>25</ele></trkpt></trkseg>'))
  self.assertEqual((r['raw_ascent_m'],r['raw_descent_m']),(20,5))
 def test_empty_rejected(self):
  with self.assertRaises(ValueError): analyze(gpx(''))
 def test_projection_roundtrip(self):
  f=Transformer.from_crs(4326,32649,always_xy=True);b=Transformer.from_crs(32649,4326,always_xy=True)
  lon,lat=b.transform(*f.transform(109,34));self.assertAlmostEqual(lon,109);self.assertAlmostEqual(lat,34)
 def test_raster_sample_and_nodata(self):
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:4326',transform=from_origin(108,35,0.01,0.01),nodata=-9999) as ds:
    ds.write(np.array([[100,120],[150,-9999]],dtype='float32'),1)
    self.assertEqual(float(next(ds.sample([(108.005,34.995)]))[0]),100)
    self.assertEqual(float(next(ds.sample([(108.015,34.985)]))[0]),-9999)
 def test_graph_restriction_filter(self):
  g=nx.DiGraph();g.add_edge('a','b',length=1,bicycle='no');g.add_edge('a','c',length=2,bicycle='yes');g.add_edge('c','b',length=2,bicycle='yes')
  allowed=nx.subgraph_view(g,filter_edge=lambda a,b:g[a][b]['bicycle']!='no')
  self.assertEqual(nx.shortest_path(allowed,'a','b',weight='length'),['a','c','b'])
  self.assertTrue(LineString([(0,0),(1,1)]).is_valid)
if __name__=='__main__': unittest.main(verbosity=2)
