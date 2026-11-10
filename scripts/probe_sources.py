"""Bounded public, official URL probes; no login, private API or TLS bypass."""
import argparse, concurrent.futures, datetime, hashlib, json, pathlib, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
'amap_docs':'https://lbs.amap.com/api/webservice/guide/api/direction',
'amap_v5':'https://lbs.amap.com/api/webservice/guide/api/newroute',
'amap_web':'https://www.amap.com/',
'amap_api_no_key':'https://restapi.amap.com/v4/direction/bicycling?origin=108.98,34.25&destination=108.99,34.25',
'xingzhe':'https://www.imxingzhe.com/',
'xingzhe_help':'https://www.imxingzhe.com/help/',
'osm_api':'https://api.openstreetmap.org/api/0.6/map?bbox=108.979,34.248,108.981,34.250',
'osm_wiki':'https://wiki.openstreetmap.org/wiki/Key:bicycle',
'osm_copyright':'https://www.openstreetmap.org/copyright',
'overpass':'https://overpass-api.de/api/status',
'geofabrik':'https://download.geofabrik.de/asia/china.html',
'copernicus':'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM',
'opentopodata':'https://api.opentopodata.org/v1/srtm90m?locations=34.25,108.98',
'srtm':'https://www.earthdata.nasa.gov/data/instruments/srtm',
'brouter':'https://brouter.de/brouter-web/',
'ors':'https://openrouteservice.org/dev/#/api-docs',
'weather':'https://www.cma.gov.cn/',
'shaanxi_roads':'https://jtyst.shaanxi.gov.cn/',
'hubei_roads':'https://jtt.hubei.gov.cn/',
'henan_roads':'https://jtyst.henan.gov.cn/'
}
def probe(item):
 key,url=item; now=datetime.datetime.now(datetime.timezone.utc).isoformat(); status=None; err=None
 req=urllib.request.Request(url,headers={'User-Agent':'CyclingFeasibilityResearch/0.1 (bounded public-source check)'})
 try:
  with urllib.request.urlopen(req,timeout=22) as r:
   status=r.status; body=r.read(750001); ctype=r.headers.get('Content-Type',''); final=r.url
 except urllib.error.HTTPError as e:
  status=e.code; body=e.read(750001); ctype=e.headers.get('Content-Type',''); final=url
 except Exception as e:
  body=b''; ctype=''; final=url; err=type(e).__name__+': '+str(e)
 out=ROOT/'data/evidence'; out.mkdir(parents=True,exist_ok=True)
 (out/(key+'.txt')).write_text(body.decode('utf-8',errors='replace'),encoding='utf-8')
 return dict(id=key,url=url,final_url=final,checked_at_utc=now,http_status=status,content_type=ctype,bytes=len(body),truncated=len(body)>750000,sha256=hashlib.sha256(body).hexdigest(),error=err,evidence='data/evidence/'+key+'.txt')
SOFTWARE={
'gpxpy_readme':'https://raw.githubusercontent.com/tkrajina/gpxpy/master/README.md',
'osmnx_readme':'https://raw.githubusercontent.com/gboeing/osmnx/main/README.md',
'brouter_readme':'https://raw.githubusercontent.com/abrensch/brouter/master/README.md',
'brouter_road_profile':'https://raw.githubusercontent.com/abrensch/brouter/master/misc/profiles2/fastbike.brf',
'rasterio_readme':'https://raw.githubusercontent.com/rasterio/rasterio/main/README.rst'}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--software',action='store_true'); a=p.parse_args()
 selected=SOFTWARE if a.software else SOURCES
 filename='software_sources.json' if a.software else 'probes.json'
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: results=list(ex.map(probe,selected.items()))
 (ROOT/'data/evidence'/filename).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 for r in results: print(r['id'],r['http_status'],r['bytes'],r['error'] or '')
