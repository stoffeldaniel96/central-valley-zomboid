"""Acquire a small OSM snapshot; reuse validated local cache by default."""
import argparse, datetime, hashlib, json, math, time
from pathlib import Path
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ENDPOINTS=("https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter")

def validate(raw):
    root=ET.fromstring(raw)
    if root.tag!='osm' or root.find('remark') is not None or not root.findall('way'):
        raise ValueError('Incomplete or invalid OSM XML')
    nodes={n.attrib['id'] for n in root.findall('node')}
    missing=sum(nd.attrib['ref'] not in nodes for w in root.findall('way') for nd in w.findall('nd'))
    if missing: raise ValueError(f'{missing} missing way node references')
    return root

def query_for(bbox):
    w,s,e,n=bbox
    if not all(math.isfinite(v) for v in bbox) or not (-180<=w<e<=180 and -90<=s<n<=90):
        raise ValueError('Invalid bbox')
    box=f'{s},{w},{n},{e}'
    return f'[out:xml][timeout:90];(way["highway"]({box});way["building"]({box});way["amenity"="parking"]({box});way["railway"]({box});relation["type"="multipolygon"]["building"]({box});relation["type"="multipolygon"]["amenity"="parking"]({box}););(._;>>;);out body;'

def atomic_write(path,raw):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_bytes(raw);temp.replace(path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refresh',action='store_true')
    p.add_argument('--from-osm',type=Path,help='Import a complete local OSM XML snapshot instead of querying')
    p.add_argument('--endpoint',action='append',help='Override public endpoints; specify more than once for fallback')
    a=p.parse_args()
    dest=ROOT/'data/pilot.osm'; manifest=ROOT/'data/pilot.source.json'
    dest.parent.mkdir(exist_ok=True)
    bbox=json.loads((ROOT/'output/stats.json').read_text())['pilot_bbox']
    w,s,e,n=bbox; bbox=[w-.003,s-.003,e+.003,n+.003]
    q=query_for(bbox); qhash=hashlib.sha256(q.encode()).hexdigest()
    if dest.exists() and not a.refresh and not a.from_osm:
        try:
            raw=dest.read_bytes();validate(raw)
            m=json.loads(manifest.read_text())
            if m.get('sha256')==hashlib.sha256(raw).hexdigest() and m.get('query_sha256')==qhash:
                print(f'Using validated cached snapshot: {dest}');return
            print('Existing cache does not match current query; leaving it intact until replacement succeeds.')
        except (OSError,ValueError,ET.ParseError) as e: print(f'Cache cannot be verified: {e}')
    if a.from_osm:
        raw=a.from_osm.read_bytes();root=validate(raw);source='local:'+a.from_osm.name
        coverage='unverified_local_extent'
    else:
        endpoints=a.endpoint or ENDPOINTS
        last=None
        for i,endpoint in enumerate(endpoints):
            print(f'Querying {endpoint}',flush=True)
            try:
                req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'CentralValleyMapPrototype/0.2 (https://github.com/stoffeldaniel96/central-valley-zomboid)'})
                with urllib.request.urlopen(req,timeout=150) as response: raw=response.read()
                root=validate(raw);source=endpoint;coverage='requested_bbox_with_padding';break
            except urllib.error.HTTPError as exc:
                last=exc;print(f'HTTP {exc.code}: {exc.reason}')
                if exc.code==429:
                    p.exit(1,'Rate limited. Stop and retry later or use a local extract; no endpoint rotation.\n')
                if exc.code not in (408,500,502,503,504): raise
                if exc.headers.get('Retry-After'):
                    p.exit(1,'Server requested a cooldown. Retry later or use a local extract.\n')
            except (urllib.error.URLError,TimeoutError,ValueError,ET.ParseError) as exc:
                last=exc;print(f'Acquisition failed: {exc}')
            if i+1<len(endpoints): time.sleep(15)
        else: p.exit(1,f'No valid snapshot acquired ({last}). Existing files unchanged. Retry later or use --from-osm PATH.\n')
    m={'source':source,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'query_sha256':qhash if not a.from_osm else None,'requested_bbox':bbox,'coverage':coverage,'ways':len(root.findall('way')),'nodes':len(root.findall('node')),'license':'ODbL'}
    atomic_write(dest,raw);atomic_write(manifest,json.dumps(m,indent=2).encode());print(dest)

if __name__=='__main__':main()
