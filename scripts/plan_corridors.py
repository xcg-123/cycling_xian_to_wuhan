"""Source-backed corridor collection. Credentialed responses stay in ignored data/private.
Caches successful/failed requests; never blindly retries or emits credential-bearing URLs.
"""
import argparse,concurrent.futures,datetime,json,os,pathlib,time,urllib.parse,urllib.request
from amap_probe import NoRedirect,redact
ROOT=pathlib.Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/private/planning-20261112'
PLACES={
'start':'陕西省西安市西安交通大学兴庆校区南门','lantian':'陕西省蓝田县人民政府','shangzhou':'陕西省商洛市商州区人民政府','danfeng':'陕西省丹凤县人民政府','shangnan':'陕西省商南县人民政府','xixia':'河南省西峡县人民政府','neixiang':'河南省内乡县人民政府','nanyang':'河南省南阳市卧龙区人民政府','tanghe':'河南省唐河县人民政府','tongbai':'河南省桐柏县人民政府','suizhou':'湖北省随州市曾都区人民政府','anlu':'湖北省安陆市人民政府','xiaogan':'湖北省孝感市孝南区人民政府','finish':'湖北省武汉市汉阳区人民政府',
'luanzhen':'陕西省西安市长安区滦镇街道办事处','guanghuojie':'陕西省宁陕县广货街镇人民政府','ningshan':'陕西省宁陕县人民政府','shiquan':'陕西省石泉县人民政府','hanyin':'陕西省汉阴县人民政府','ankang':'陕西省安康市汉滨区人民政府','xunyang':'陕西省旬阳市人民政府','baihe':'陕西省白河县人民政府','shiyan':'湖北省十堰市张湾区人民政府','gucheng':'湖北省谷城县人民政府','xiangyang':'湖北省襄阳市襄城区人民政府',
'weinan':'陕西省渭南市临渭区人民政府','huayin':'陕西省华阴市人民政府','tongguan':'陕西省潼关县人民政府','lingbao':'河南省灵宝市人民政府','lushi':'河南省卢氏县人民政府',
'xinye':'河南省新野县人民政府','yicheng':'湖北省宜城市人民政府','zhongxiang':'湖北省钟祥市人民政府','jingshan':'湖北省京山市人民政府','hanchuan':'湖北省汉川市人民政府'}
CORRIDORS={
'A':['start','lantian','shangzhou','danfeng','shangnan','xixia','neixiang','nanyang','tanghe','tongbai','suizhou','anlu','xiaogan','finish'],
'B':['start','luanzhen','guanghuojie','ningshan','shiquan','hanyin','ankang','xunyang','baihe','shiyan','gucheng','xiangyang','suizhou','anlu','xiaogan','finish'],
'C':['start','weinan','huayin','tongguan','lingbao','lushi','xixia','neixiang','nanyang','tanghe','tongbai','suizhou','anlu','xiaogan','finish'],
'D':['start','lantian','shangzhou','danfeng','shangnan','xixia','neixiang','nanyang','xinye','xiangyang','yicheng','zhongxiang','jingshan','hanchuan','finish']}
def fetch(name,endpoint,params):
    dest=CACHE/(name+'.json')
    if dest.exists(): return json.loads(dest.read_text())
    key=os.environ.get('AMAP_API_KEY')
    if not key: raise RuntimeError('Missing secure binding')
    url='https://restapi.amap.com'+endpoint+'?'+urllib.parse.urlencode(dict(params,key=key))
    t=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with urllib.request.build_opener(NoRedirect()).open(url,timeout=50) as r:
            b=r.read(20_000_001)
            if len(b)>20_000_000: raise RuntimeError('Size limit')
            data=redact(json.loads(b),key)
    except Exception as e: raise RuntimeError('Request '+name+' failed: '+type(e).__name__) from None
    CACHE.mkdir(exist_ok=True,parents=True)
    with dest.open('x') as f:json.dump(data,f,ensure_ascii=False)
    with (CACHE/(name+'.meta.json')).open('x') as f:json.dump({'endpoint':endpoint,'parameters':params,'retrieved_at_utc':t,'source_crs':'GCJ-02','public_release':'not authorized; raw geometry stays private'},f,ensure_ascii=False,indent=2)
    os.chmod(dest,0o600);time.sleep(.5)
    return data

def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['geocode','routes']);a=p.parse_args()
    loc={}
    for k,q in PLACES.items():
        if a.task=='geocode':d=fetch('geo-'+k,'/v3/geocode/geo',{'address':q})
        else:d=json.loads((CACHE/('geo-'+k+'.json')).read_text())
        results=d.get('geocodes',[])
        if d.get('status')!='1' or not results:print('GEOCODE FAILED',k,d.get('infocode'),flush=True);continue
        g=results[0];loc[k]=g['location']
        if a.task=='geocode': print(k,len(results),g.get('formatted_address'),g['location'],g.get('level'),flush=True)
    if a.task=='routes':
        edges=list(dict.fromkeys((x,y) for ns in CORRIDORS.values() for x,y in zip(ns,ns[1:])))
        def one(edge):
            x,y=edge
            if x not in loc or y not in loc: return (x,y,'MISSING PLACE')
            try:
                d=fetch(x+'--'+y,'/v5/direction/bicycling',{'origin':loc[x],'destination':loc[y],'show_fields':'polyline,navi,cost'})
                paths=d.get('route',{}).get('paths',[])
                return (x,y,d.get('infocode'),paths[0].get('distance') if paths else 'NO PATH')
            except RuntimeError as e:return (x,y,str(e))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for result in pool.map(one,edges):print(*result,flush=True)
if __name__=='__main__':main()
