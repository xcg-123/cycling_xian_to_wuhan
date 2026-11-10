"""Conservative route validation. GCJ-02 is never relabelled or exported as WGS84."""
import argparse,json,math,pathlib
import gpxpy
import gpxpy.gpx
from pyproj import Geod
GEOD=Geod(ellps='WGS84')

def point(value):
    if len(value)!=2: raise ValueError('Expected [longitude, latitude]')
    lon,lat=map(float,value)
    if not math.isfinite(lon) or not math.isfinite(lat) or not -180<=lon<=180 or not -90<=lat<=90:
        raise ValueError('Invalid coordinate')
    return [lon,lat]

def distance(a,b):
    return GEOD.inv(a[0],a[1],b[0],b[1])[2]

def positive(value):
    result=float(value)
    if not math.isfinite(result) or result<=0: raise ValueError('Expected positive finite distance')
    return result

def parse_amap_v5(data,path_index=0):
    if str(data.get('status'))!='1' or str(data.get('infocode'))!='10000':
        raise ValueError('No successful v5 business response')
    paths=data.get('route',{}).get('paths')
    if not isinstance(paths,list) or not 0<=path_index<len(paths): raise ValueError('No selected path')
    path=paths[path_index]; steps=path.get('steps')
    if not isinstance(steps,list) or not steps: raise ValueError('Missing road steps')
    segments=[]; roads=[]
    for i,step in enumerate(steps):
        polyline=step.get('polyline')
        if not isinstance(polyline,str) or not polyline: raise ValueError('Missing step polyline; request show_fields=polyline')
        coords=[point(p.split(',')) for p in polyline.split(';')]
        if len(coords)<2: raise ValueError('Step has fewer than two points')
        segments.append(coords)
        name=step.get('road_name') or step.get('road') or ''
        roads.append({'step':i,'name':name,'distance_m':step.get('distance'),
          'instruction':step.get('instruction'),
          'special_road_name_clue': any(word in str(name) for word in ['桥','隧道']),
          'special_road_type':'unknown; names are clues only',
          'returned_fields':sorted(step)})
    return {'source':'AMap official v5 bicycling','source_crs':'GCJ-02',
      'path_index':path_index,'path_count':len(paths),'reported_distance_m':positive(path['distance']),
      'segments':segments,'roads':roads,'test_only':True,
      'limitations':['Live response schema not verified until a successful authenticated request.',
       'No reliable bridge/tunnel inventory inferred from missing fields or road names.',
       'No road-bike suitability or current access certification.']}

def audit(route,max_edge_m=1000,max_join_gap_m=5,max_distance_difference=0.10):
    if route.get('source_crs') not in ('WGS84','GCJ-02'): raise ValueError('Unknown coordinate reference')
    if not route.get('source'): raise ValueError('Missing provenance')
    segments=[[point(p) for p in seg] for seg in route['segments']]
    if not segments or any(len(s)<2 for s in segments): raise ValueError('Empty or undersized segment')
    total=0.; gaps=[]; long_edges=[]; duplicates=0
    for si,s in enumerate(segments):
        if si:
            gap=distance(segments[si-1][-1],s[0])
            if gap>max_join_gap_m: gaps.append({'before_segment':si,'gap_m':round(gap,3)})
        for j,(a,b) in enumerate(zip(s,s[1:])):
            d=distance(a,b);total+=d;duplicates+=d==0
            if d>max_edge_m: long_edges.append({'segment':si,'edge':j,'length_m':round(d,3)})
    reported=route.get('reported_distance_m')
    diff=abs(total-positive(reported))/positive(reported) if reported is not None else None
    return {'source_crs':route['source_crs'],'point_count':sum(map(len,segments)),
      'segment_count':len(segments),'geometry_distance_m':round(total,3),
      'distance_metric':'WGS84 geodesic' if route['source_crs']=='WGS84' else 'GCJ-02 numeric-coordinate diagnostic only; not a WGS84 distance',
      'reported_distance_m':reported,'relative_distance_difference':diff,
      'join_gaps':gaps,'long_edges':long_edges,'duplicate_adjacent_points':duplicates,
      'thresholds':{'max_edge_m':max_edge_m,'max_join_gap_m':max_join_gap_m,'max_distance_difference':max_distance_difference},
      'geometry_screen_pass':not gaps and not long_edges and total>0 and (diff is None or diff<=max_distance_difference),
      'distance_crosscheck_available':diff is not None,
      'warning':'Numerical screen only; thresholds are review triggers, not a road safety guarantee. Segment gaps are never bridged.'}

def export_gpx(route):
    if route.get('source_crs')!='WGS84': raise ValueError('GPX export requires evidenced WGS84 input; GCJ-02 conversion is not implemented')
    result=audit(route)
    if not result['geometry_screen_pass']: raise ValueError('Geometry review required before GPX export')
    g=gpxpy.gpx.GPX();g.creator='cycling_xian_to_wuhan TEST_ONLY';g.name='TEST_ONLY - NOT A VALIDATED CYCLING ITINERARY'
    g.description='Source: '+str(route['source'])+'. Road suitability and legal access unverified.'
    t=gpxpy.gpx.GPXTrack();g.tracks.append(t)
    for coords in route['segments']:
        s=gpxpy.gpx.GPXTrackSegment();t.segments.append(s)
        s.points=[gpxpy.gpx.GPXTrackPoint(latitude=p[1],longitude=p[0]) for p in coords]
    xml=g.to_xml(version='1.1'); parsed=gpxpy.parse(xml)
    if sum(len(s.points) for t in parsed.tracks for s in t.segments)!=result['point_count']: raise ValueError('GPX roundtrip failed')
    return xml

def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--format',choices=['amap-v5','normalized'],required=True)
    p.add_argument('--path-index',type=int,default=0);p.add_argument('--output',required=True);p.add_argument('--gpx')
    a=p.parse_args();dest=pathlib.Path(a.output)
    if dest.exists() or (a.gpx and pathlib.Path(a.gpx).exists()): p.error('Output exists; choose a fresh path')
    try:
        raw=json.loads(pathlib.Path(a.input).read_text());route=parse_amap_v5(raw,a.path_index) if a.format=='amap-v5' else raw
        result=audit(route)
        # Validate all outputs before writing any; no partial GPX for GCJ-02 inputs.
        xml=export_gpx(route) if a.gpx else None
        with dest.open('x') as f: f.write(json.dumps({'route':route,'audit':result},ensure_ascii=False,indent=2)+'\n')
        if xml is not None:
            with pathlib.Path(a.gpx).open('x') as f: f.write(xml)
    except (ValueError,KeyError,TypeError,OSError) as e:
        p.exit(1,'Route validation failed ('+type(e).__name__+'); check schema, CRS and geometry.\n')
    print('Audit saved; road suitability remains unverified.')
    if not result['geometry_screen_pass']: p.exit(1,'Geometry screen flagged review items.\n')
if __name__=='__main__': main()
