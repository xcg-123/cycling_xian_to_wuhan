"""Opt-in official v4 cycling experiment; consult current official entitlement before use.
No GPX export: response coordinate system and road suitability require review.
"""
import argparse,json,os,pathlib,urllib.parse,urllib.request,urllib.error

def coordinate(s):
 try: lon,lat=map(float,s.split(','))
 except ValueError: raise argparse.ArgumentTypeError('Expected longitude,latitude')
 if not (-180<=lon<=180 and -90<=lat<=90): raise argparse.ArgumentTypeError('Out of range')
 return s
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--origin',required=True,type=coordinate);p.add_argument('--destination',required=True,type=coordinate);p.add_argument('--output',required=True);a=p.parse_args()
 key=os.environ.get('AMAP_API_KEY')
 if not key: p.exit(2,'AMAP_API_KEY is missing; configure securely outside Git.\n')
 query=urllib.parse.urlencode(dict(key=key,origin=a.origin,destination=a.destination))
 try:
  with urllib.request.urlopen('https://restapi.amap.com/v4/direction/bicycling?'+query,timeout=30) as r: data=json.load(r)
 except Exception as e: p.exit(1,'Request failed: '+type(e).__name__+' (URL and key suppressed).\n')
 # Defensive redaction even if the service echoes a supplied key.
 safe=json.dumps(data,ensure_ascii=False,indent=2).replace(key,'[REDACTED]')
 path=pathlib.Path(a.output)
 with path.open('x',encoding='utf-8') as f: f.write(safe+'\n')
 if data.get('errcode') not in (0,'0') or not data.get('data',{}).get('paths'): p.exit(1,'Response saved; no successful cycling path established.\n')
 print('Cycling response saved; GCJ-02/geometry/access review required before any GPX conversion.')
