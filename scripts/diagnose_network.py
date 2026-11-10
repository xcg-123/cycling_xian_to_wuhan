"""Anonymous representative probes. No credentials, no verbose request logging."""
import argparse,datetime,json,pathlib,subprocess,tempfile,urllib.parse,fnmatch
TARGETS={
 'amap_v5_no_key':'https://restapi.amap.com/v5/direction/bicycling?origin=108.980000,34.250000&destination=108.990000,34.250000&show_fields=polyline',
 'amap_docs':'https://lbs.amap.com/api/webservice/guide/api/newroute',
 'osm_small_bbox':'https://api.openstreetmap.org/api/0.6/map?bbox=108.979,34.248,108.981,34.250',
 'allowed_control':'https://raw.githubusercontent.com/gboeing/osmnx/main/README.md'}
def probe(name,url):
 with tempfile.TemporaryDirectory() as d:
  h=pathlib.Path(d)/'headers'; b=pathlib.Path(d)/'body'
  p=subprocess.run(['curl','--silent','--show-error','--connect-timeout','10','--max-time','25','--dump-header',str(h),'--output',str(b),'--write-out','%{json}',url],capture_output=True,text=True)
  try: meta=json.loads(p.stdout)
  except ValueError: meta={}
  headers=h.read_text(errors='replace') if h.exists() else ''
  # Only diagnostic headers; never persist Set-Cookie or proxy credentials.
  safe=[line for line in headers.splitlines() if line.lower().startswith(('http/','x-proxy','x-denied','x-envoy','content-type:','server:'))]
  body=b.read_text(errors='replace')[:1000] if b.exists() else ''
  return dict(id=name,url=url,time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),curl_exit=p.returncode,http_connect=meta.get('http_connect'),http_code=meta.get('http_code'),ssl_verify_result=meta.get('ssl_verify_result'),headers=safe,error=p.stderr.strip(),body_excerpt=body)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
 dest=pathlib.Path(a.output)
 if dest.exists(): p.error('Output exists; use a new filename to preserve evidence')
 rows=[probe(k,v) for k,v in TARGETS.items()]
 policy_path=pathlib.Path('/etc/codex/network-policy.json')
 policy=json.loads(policy_path.read_text()) if policy_path.exists() else {}
 hosts=[x['host'] for x in policy.get('http_network_policy',{}).get('egress_rules',[])]
 for row in rows:
  host=urllib.parse.urlsplit(row['url']).hostname
  row['startup_policy_allows_host']=any(fnmatch.fnmatchcase(host,x) for x in hosts) if policy else None
 dest.write_text(json.dumps({'phase':'anonymous connectivity; no API authentication attempted','policy_mode':policy.get('http_network_policy',{}).get('type'),'probes':rows},ensure_ascii=False,indent=2)+'\n')
 for x in rows: print(x['id'],x['curl_exit'],x['http_connect'],x['http_code'],x['headers'],x['error'])
