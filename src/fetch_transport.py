"""Cache bounded independent road/rail observations from ArcGIS REST services."""
import argparse,datetime,hashlib,json,urllib.parse,urllib.request
from workbench_data import ROOT
SOURCES={
    'caltrans':('road','https://caltrans-gis.dot.ca.gov/arcgis/rest/services/chhighway/All_Roads/MapServer/0'),
    'fra':('rail','https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Lines_NS/FeatureServer/0')
}
def request(url,params):
    req=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode(),headers={'User-Agent':'CentralValleyWorkbench/0.3'})
    with urllib.request.urlopen(req,timeout=120) as response:d=json.load(response)
    if 'error' in d:raise RuntimeError(str(d['error']))
    return d

def acquire(name,bbox):
    kind,url=SOURCES[name]
    params={'f':'json','where':'1=1','geometry':','.join(map(str,bbox)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'}
    ids=request(url+'/query',{**params,'returnIdsOnly':'true'})
    oid=ids.get('objectIdFieldName')
    if not oid or 'objectIds' not in ids:raise ValueError('Missing object ID response')
    ids=sorted(set(ids['objectIds'] or []))
    if len(ids)>20000:raise ValueError('Too many objects for pilot query')
    features=[]
    for i in range(0,len(ids),200):
        batch=ids[i:i+200]
        result=request(url+'/query',{'f':'json','objectIds':','.join(map(str,batch)),'outFields':'*','returnGeometry':'true','outSR':4326,'returnZ':'false','returnM':'false'})
        sr=result.get('spatialReference',{})
        if sr.get('latestWkid',sr.get('wkid'))!=4326:raise ValueError('Unexpected response CRS')
        got={f['attributes'][oid] for f in result['features']}
        if got!=set(batch) or result.get('exceededTransferLimit'):raise ValueError('Incomplete feature batch')
        for f in result['features']:
            paths=f.get('geometry',{}).get('paths')
            if not paths or any(len(p)<2 for p in paths):raise ValueError('Missing or unsupported polyline geometry')
            paths=[[xy[:2] for xy in p] for p in paths]
            features.append({'type':'Feature','id':str(f['attributes'][oid]),'properties':f['attributes'],'geometry':{'type':'LineString' if len(paths)==1 else 'MultiLineString','coordinates':paths[0] if len(paths)==1 else paths}})
    return {'type':'FeatureCollection','features':features}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--refresh',action='store_true');p.add_argument('--source',choices=SOURCES,action='append');a=p.parse_args()
    bbox=json.loads((ROOT/'output/stats.json').read_text())['pilot_bbox']
    # Include a margin so boundary comparisons have nearby reference lines.
    w,s,e,n=bbox;bbox=[w-.001,s-.001,e+.001,n+.001]
    out=ROOT/'data/transport';out.mkdir(parents=True,exist_ok=True)
    failed=[]
    for name in a.source or SOURCES:
        dest=out/(name+'.geojson');manifest=out/(name+'.json')
        try:
            if not a.refresh and dest.exists() and manifest.exists():
                m=json.loads(manifest.read_text())
                if m.get('bbox')==bbox and m.get('sha256')==hashlib.sha256(dest.read_bytes()).hexdigest():
                    print('Using cached',name);continue
            d=acquire(name,bbox);raw=json.dumps(d,allow_nan=False).encode()
            m={'source':name,'kind':SOURCES[name][0],'url':SOURCES[name][1],'bbox':bbox,'sha256':hashlib.sha256(raw).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'features':len(d['features']),'rights_review':'pending' if name=='caltrans' else 'US government public domain per NTAD layer metadata','notes':'Network representation, not surveyed individual lanes/tracks. Caltrans incorporates TIGER; source vintage and positional accuracy require review.'}
            for path,b in ((dest,raw),(manifest,json.dumps(m,indent=2).encode())):
                tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(b);tmp.replace(path)
            print(name,len(d['features']),'features')
        except (OSError,ValueError,RuntimeError,KeyError) as exc:
            failed.append(name);print(name,'failed:',exc)
    if failed:raise SystemExit('Failed sources: '+', '.join(failed)+'; other valid snapshots retained')
if __name__=='__main__':main()
