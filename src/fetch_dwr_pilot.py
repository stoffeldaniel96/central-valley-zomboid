"""Download a bounded, aligned DWR pilot mosaic, resumable by completed patch."""
import argparse,hashlib,json,math,tempfile,time,urllib.parse,urllib.error
from pathlib import Path
from PIL import Image
from pyproj import Transformer
from workbench_data import ROOT,pilot_extent
from probe_imagery import SERVICES,catalog
from fetch_aerial import get
from fetch_elevation import retry_delay,save_json,sha
from imagery_registry import register,list_layers,REGISTRY

def plan(extent,pixel_m,patch_px):
    x,y,u,v=extent
    lat=Transformer.from_crs(3857,4326,always_xy=True).transform((x+u)/2,(y+v)/2)[1]
    step=pixel_m/math.cos(math.radians(lat))
    w=math.ceil((u-x)/step);h=math.ceil((v-y)/step)
    # One common pixel grid, extend only east and south by less than one pixel.
    patches=[]
    for row in range(math.ceil(h/patch_px)):
        for col in range(math.ceil(w/patch_px)):
            left=col*patch_px;top=row*patch_px
            pw=min(patch_px,w-left);ph=min(patch_px,h-top)
            patches.append({'key':f'{row}-{col}','width':pw,'height':ph,'extent':[x+left*step,v-(top+ph)*step,x+(left+pw)*step,v-top*step]})
    return {'extent':[x,v-h*step,x+w*step,v],'width':w,'height':h,'step_3857':step,'pixel_m_requested':pixel_m,'patch_px':patch_px,'patches':patches}

def paced_get(url,params,interval):
    for attempt in range(5):
        time.sleep(interval)
        try:return get(url,params)
        except urllib.error.HTTPError as e:
            code=e.code;header=e.headers.get('Retry-After') if e.headers else None;e.close()
            if code not in (429,500,502,503,504):raise
            delay=retry_delay(header,attempt)
            if attempt==4 or delay>600:raise RuntimeError(f'HTTP {code}; stop and resume later (delay {delay}s)') from e
            print(f'HTTP {code}, retry after {delay}s',flush=True);time.sleep(delay)

def acquire(p,group,records,interval):
    base=SERVICES['dwr']
    params={'f':'json','bbox':','.join(map(str,p['extent'])),'bboxSR':3857,'imageSR':3857,'size':f"{p['width']},{p['height']}",'format':'jpg','compressionQuality':100,'adjustAspectRatio':'false','mosaicRule':json.dumps({'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':[1],'mosaicOperation':'MT_FIRST'})}
    d=json.loads(paced_get(base+'/exportImage',params,interval))
    if 'error' in d:raise RuntimeError(str(d['error']))
    e=d['extent'];sr=e['spatialReference'];extent=[e[k] for k in ('xmin','ymin','xmax','ymax')]
    if sr.get('latestWkid',sr.get('wkid')) not in (3857,102100,102113):raise ValueError('Unexpected CRS')
    if max(abs(a-b) for a,b in zip(extent,p['extent']))>.001 or (d['width'],d['height'])!=(p['width'],p['height']):raise ValueError('Server changed grid extent or dimensions')
    url=urllib.parse.urlparse(d['href'])
    if url.scheme!='https' or not url.hostname or not url.hostname.endswith('.water.ca.gov'):raise ValueError('Unexpected export host')
    raw=paced_get(d['href'],None,interval)
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'patch.jpg';path.write_bytes(raw)
        with Image.open(path) as im:
            if im.format!='JPEG' or im.size!=(p['width'],p['height']):raise ValueError('Invalid image')
            # Detect wholly constant images; partial coverage still needs visual review.
            if all(lo==hi for lo,hi in im.convert('RGB').getextrema()):raise ValueError('Blank/constant export')
        return register(path,extent,'California DWR San Joaquin Valley 2021',usage='reference_only',native_gsd=.0762001524,metadata={'mosaic_group':group,'mosaic_patch':p['key'],'catalog_candidates':records,'export_parameters':params,'source':base,'acquisition_window':'2021-03-28 to 2021-05-12','note':'Reference only; actual coverage, registration and downstream permissions require review.'})

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel-m',type=float,default=.08)
    ap.add_argument('--patch-px',type=int,default=4000)
    ap.add_argument('--interval',type=float,default=10)
    ap.add_argument('--download',action='store_true',help='Explicitly execute acquisition; default plan only')
    ap.add_argument('--limit',type=int,help='Maximum new patches this run')
    a=ap.parse_args()
    if not .075<=a.pixel_m<=1 or not 512<=a.patch_px<=4000 or not math.isfinite(a.interval) or a.interval<1 or (a.limit is not None and a.limit<1):ap.error('Invalid grid or pacing')
    grid=plan(pilot_extent(),a.pixel_m,a.patch_px)
    group='dwr-pilot-'+hashlib.sha256(json.dumps(grid,sort_keys=True).encode()).hexdigest()[:12]
    out=ROOT/'output/imagery';out.mkdir(parents=True,exist_ok=True)
    existing={}
    for m in list_layers():
        meta=m.get('metadata',{})
        if meta.get('mosaic_group')==group:
            path=REGISTRY/m['id']/'original'
            if path.is_file() and sha(path)==m['sha256']:existing[meta['mosaic_patch']]=m['id']
    def report():
        result={'group':group,**grid,'completed':existing,'status':'complete' if len(existing)==len(grid['patches']) else 'partial','notes':'Complete means all patches acquired, not validated coverage or registration.'}
        save_json(out/(group+'.json'),result)
        print(f"{group}: {len(existing)}/{len(grid['patches'])} cached | {grid['width']} x {grid['height']} pixels",flush=True)
    report()
    if not a.download:return
    records=catalog(SERVICES['dwr'],pilot_extent())
    if not any(x['OBJECTID']==1 for x in records):raise ValueError('Expected raster ID 1 not in pilot catalog')
    count=0
    for p in grid['patches']:
        if p['key'] in existing:continue
        if a.limit is not None and count>=a.limit:break
        print('Acquiring patch',p['key'],flush=True)
        try:m=acquire(p,group,records,a.interval)
        except (OSError,ValueError,RuntimeError,KeyError) as e:
            report();ap.exit(1,f'Patch {p["key"]} failed: {e}\nCompleted patches retained. Re-run to resume.\n')
        existing[p['key']]=m['id'];count+=1;report()
if __name__=='__main__':main()
