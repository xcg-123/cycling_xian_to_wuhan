"""Extract an explicitly ordered connected OSM way chain, NOT a bicycle router.
OSM API geographic coordinates are retained as WGS84; no GCJ conversion occurs.
Raw OSM may contain contributor metadata; only selected road tags are exported.
"""
import argparse,datetime,hashlib,json,pathlib,xml.etree.ElementTree as ET
from route_pipeline import audit,export_gpx
TAGS={'highway','name','bicycle','access','vehicle','motorroad','oneway','oneway:bicycle','surface','smoothness','cycleway','bridge','tunnel'}
def extract(raw,way_ids,source_url,retrieved_at):
    root=ET.fromstring(raw)
    nodes={n.attrib['id']:[float(n.attrib['lon']),float(n.attrib['lat'])] for n in root.findall('node')}
    ways={w.attrib['id']:w for w in root.findall('way')};segments=[];roads=[];last=None
    for ident in way_ids:
        w=ways[ident];refs=[n.attrib['ref'] for n in w.findall('nd')]
        if last is not None and refs[0]!=last: raise ValueError('Ways do not join in stored direction')
        tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag') if t.attrib['k'] in TAGS}
        if 'highway' not in tags: raise ValueError('Not a road way')
        if tags.get('oneway')=='-1': raise ValueError('Reversed oneway requires separate review')
        if tags.get('highway') in {'motorway','motorway_link','trunk','trunk_link','steps','construction'} or tags.get('motorroad')=='yes': raise ValueError('Excluded road class')
        if any(tags.get(k) in {'no','private'} for k in ['access','vehicle','bicycle']): raise ValueError('Explicit access restriction')
        segments.append([nodes[ref] for ref in refs]);last=refs[-1]
        roads.append({'osm_way_id':ident,'osm_version':w.attrib.get('version'),'osm_timestamp':w.attrib.get('timestamp'),'tags':tags,'node_ids':refs,'bicycle_permission':'tagged_yes' if tags.get('bicycle') in {'yes','designated'} else 'unknown'})
    return {'source':'OpenStreetMap contributors; API way geometry ONLY, NOT a bicycle route','source_url':source_url,'retrieved_at_utc':retrieved_at,'raw_sha256':hashlib.sha256(raw).hexdigest(),'source_crs':'WGS84','coordinate_processing':'Identity: OSM lon/lat retained; no GCJ-02 transform','segments':segments,'roads':roads,'test_only':True,'attribution':'© OpenStreetMap contributors','license':'ODbL 1.0 https://opendatacommons.org/licenses/odbl/1-0/','limitations':['No routing algorithm or current bicycle access certification.','Missing surface and bicycle tags remain unknown.','No independent positional accuracy verification or elevation data.']}
def main():
    p=argparse.ArgumentParser();p.add_argument('osm');p.add_argument('--ways',nargs='+',required=True);p.add_argument('--source-url',required=True);p.add_argument('--retrieved-at',required=True);p.add_argument('--output',required=True);p.add_argument('--gpx',required=True);a=p.parse_args()
    for name in [a.output,a.gpx]:
        if pathlib.Path(name).exists(): p.error('Output exists')
    route=extract(pathlib.Path(a.osm).read_bytes(),a.ways,a.source_url,a.retrieved_at)
    xml=export_gpx(route);result=audit(route)
    with pathlib.Path(a.output).open('x') as f:f.write(json.dumps({'route':route,'audit':result},ensure_ascii=False,indent=2)+'\n')
    with pathlib.Path(a.gpx).open('x') as f:f.write(xml)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
