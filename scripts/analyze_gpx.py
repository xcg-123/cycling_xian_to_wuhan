"""Audit WGS84 GPX tracks. Raw elevation gain is diagnostic, not a verified climb total."""
import argparse,json,pathlib
import gpxpy
from pyproj import Geod
GEOD=Geod(ellps='WGS84')
def analyze(text):
 g=gpxpy.parse(text); segments=[s for t in g.tracks for s in t.segments]
 if not segments or not any(s.points for s in segments): raise ValueError('No track points; route-only GPX requires explicit conversion')
 total=0.; gain=0.; loss=0.; gaps=[]; points=0; missing=0; edges=0; elevation_edges=0
 for si,s in enumerate(segments):
  points+=len(s.points)
  for p in s.points:
   if not (-90<=p.latitude<=90 and -180<=p.longitude<=180): raise ValueError('Invalid coordinates')
   missing+=p.elevation is None
  for a,b in zip(s.points,s.points[1:]):
   d=GEOD.inv(a.longitude,a.latitude,b.longitude,b.latitude)[2]; total+=d; edges+=1
   if d>1000: gaps.append({'segment':si,'edge_m':round(d,1)})
   if a.elevation is not None and b.elevation is not None:
    elevation_edges+=1; dz=b.elevation-a.elevation; gain+=max(0,dz); loss+=max(0,-dz)
 return {'points':points,'segments':len(segments),'distance_km':round(total/1000,3),'missing_elevation_points':missing,'elevation_edge_coverage':elevation_edges/edges if edges else None,'raw_ascent_m':round(gain,1) if elevation_edges else None,'raw_descent_m':round(loss,1) if elevation_edges else None,'edges_over_1km_review':gaps,'notes':['Distance sums within each track segment only; gaps between segments are not bridged.','Input must be WGS84; GPX cannot reliably declare GCJ-02.','Sparse-point distances underestimate curves; long edges require review.','Raw elevation sums are noise-sensitive and partial if elevations are missing. No road legality or surface suitability inference.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('gpx');a=p.parse_args();print(json.dumps(analyze(pathlib.Path(a.gpx).read_text()),ensure_ascii=False,indent=2))
