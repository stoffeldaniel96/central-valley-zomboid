"""Local-only geographic inspection and proposal server."""
import argparse,datetime,hashlib,json,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from shapely.geometry import shape,mapping
from shapely.ops import transform
from workbench_data import ROOT,normalize,pilot_extent,TO_WGS

def json_bytes(x):return json.dumps(x,allow_nan=False).encode()
def proposal(feature,geometry,rationale,source,evidence,extent):
    if not isinstance(rationale,str) or not rationale.strip() or len(rationale)>2000:raise ValueError('A concise rationale is required')
    if not isinstance(evidence,str) or not evidence.strip() or len(evidence)>2000:raise ValueError('Independent evidence notes required')
    old=shape(feature['geometry']);new=shape(geometry)
    if new.geom_type!=old.geom_type or not new.is_valid or new.is_empty:raise ValueError('Replacement must be valid and preserve geometry type')
    if new.geom_type not in ('Polygon','LineString'):raise ValueError('Complex geometries are inspection-only for now')
    if new.geom_type=='Polygon' and len(old.interiors)!=len(new.interiors):raise ValueError('Hole count must be preserved')
    if new.has_z:raise ValueError('Only 2D geometry supported')
    # Allow full feature edits only within the pilot; never truncate a source way.
    from shapely.geometry import box
    window=box(*extent)
    if not window.covers(old) or not window.covers(new):raise ValueError('Feature crosses pilot boundary; inspect only')
    return {'id':str(uuid.uuid4()),'feature_id':feature['id'],'property':'geometry','status':'proposed','before':feature['geometry'],'after':mapping(new),'crs':'EPSG:3857','source_sha256':source,'evidence_notes':evidence.strip(),'rationale':rationale.strip(),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':None}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    data=normalize(ROOT/'data/pilot.osm',pilot_extent());features={f['id']:f for f in data['features']}
    aerial=ROOT/'data/aerial';ledger=ROOT/'data/corrections.json';lock=Lock()
    def read_ledger():
        return json.loads(ledger.read_text()) if ledger.exists() else []
    def aerial_manifest():
        if not (aerial/'manifest.json').exists() or not (aerial/'pilot.jpg').exists():return None
        m=json.loads((aerial/'manifest.json').read_text())
        if hashlib.sha256((aerial/'pilot.jpg').read_bytes()).hexdigest()!=m.get('sha256'):return None
        return m
    data['aerial']=aerial_manifest()
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,content,ctype='application/json'):
            self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(content)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(content)
        def do_GET(self):
            if self.path=='/':self.reply(200,(ROOT/'workbench/index.html').read_bytes(),'text/html; charset=utf-8')
            elif self.path=='/api/data':self.reply(200,json_bytes(data))
            elif self.path=='/api/proposals':
                with lock:self.reply(200,json_bytes(read_ledger()))
            elif self.path=='/api/export':
                with lock:
                    entries=read_ledger()
                out={'type':'FeatureCollection','features':[{'type':'Feature','geometry':mapping(transform(TO_WGS.transform,shape(e['after']))),'properties':{k:v for k,v in e.items() if k not in ('before','after','crs')}} for e in entries if e['source_sha256']==data['source_sha256']]}
                self.reply(200,json_bytes(out),'application/geo+json')
            elif self.path=='/aerial.jpg' and data['aerial']:self.reply(200,(aerial/'pilot.jpg').read_bytes(),'image/jpeg')
            else:self.reply(404,b'{}')
        def do_POST(self):
            if self.path!='/api/proposals' or self.headers.get('Origin') not in (f'http://127.0.0.1:{a.port}',f'http://localhost:{a.port}'):
                self.reply(403,b'{}');return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=250000:raise ValueError('Invalid request size')
                b=json.loads(self.rfile.read(size))
                entry=proposal(features[b['feature_id']],b['geometry'],b['rationale'],data['source_sha256'],b['evidence_notes'],data['extent'])
                if data['aerial']:entry['displayed_aerial_id']=data['aerial']['id']
                with lock:
                    entries=read_ledger();entries.append(entry);temp=ledger.with_suffix('.tmp');temp.write_bytes(json_bytes(entries));temp.replace(ledger)
                self.reply(201,json_bytes(entry))
            except (ValueError,KeyError,TypeError) as e:self.reply(400,json_bytes({'error':str(e)}))
    print(f'Workbench: http://127.0.0.1:{a.port} | {len(features)} features, {len(data["issues"])} normalization issues',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()

if __name__=='__main__':main()
