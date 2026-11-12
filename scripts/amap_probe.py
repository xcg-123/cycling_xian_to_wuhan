"""Official v5 bicycling client. Key comes only from AMAP_API_KEY; no GPX conversion.
Anonymous connectivity uses diagnose_network.py. Run this only for authentication/routing.
"""
import argparse,datetime,json,os,pathlib,urllib.parse,urllib.request,urllib.error
from route_pipeline import point
ENDPOINT='https://restapi.amap.com/v5/direction/bicycling'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None  # Never forward a credential-bearing request to a redirected host.
def coordinate(s):
    try: point(s.split(','))
    except (ValueError,TypeError): raise argparse.ArgumentTypeError('Expected valid longitude,latitude')
    return s

def redact(value,key):
    if isinstance(value,dict): return {redact(k,key):redact(v,key) for k,v in value.items()}
    if isinstance(value,list): return [redact(v,key) for v in value]
    if isinstance(value,str):
        for token in (key,urllib.parse.quote(key,safe=''),urllib.parse.quote_plus(key)):
            if token: value=value.replace(token,'[REDACTED]')
    return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--origin',required=True,type=coordinate);p.add_argument('--destination',required=True,type=coordinate)
    p.add_argument('--input-crs',required=True,choices=['GCJ-02']);p.add_argument('--output',required=True)
    a=p.parse_args();key=os.environ.get('AMAP_API_KEY')
    if not key: p.exit(2,'AMAP_API_KEY is missing; configure securely outside Git.\n')
    dest=pathlib.Path(a.output)
    if dest.exists(): p.error('Output exists; use a fresh path')
    params=dict(key=key,origin=a.origin,destination=a.destination,show_fields='polyline,navi,cost')
    url=ENDPOINT+'?'+urllib.parse.urlencode(params)
    try:
        opener=urllib.request.build_opener(NoRedirect())
        with opener.open(url,timeout=30) as response:
            body=response.read(5_000_001)
            if len(body)>5_000_000: p.exit(1,'Response exceeds 5 MB safety limit.\n')
            data=json.loads(body)
    except urllib.error.HTTPError as e:
        p.exit(1,'HTTP failure '+str(e.code)+'; URL/body suppressed, redirects refused.\n')
    except Exception as e:
        p.exit(1,'Transport or JSON failure: '+type(e).__name__+'; URL and key suppressed.\n')
    data=redact(data,key)
    with dest.open('x',encoding='utf-8') as f: f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    if not isinstance(data,dict) or str(data.get('status'))!='1' or str(data.get('infocode'))!='10000' or not data.get('route',{}).get('paths'):
        p.exit(1,'Response saved; no successful v5 cycling path established. Inspect sanitized JSON.\n')
    print('v5 route response saved. GCJ-02; run route_pipeline.py for geometry audit. No GPX exported.')
if __name__=='__main__': main()
