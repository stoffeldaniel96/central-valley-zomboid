"""Discover bounded USGS 3DEP products; explicitly select downloads."""
import argparse,datetime,hashlib,json,urllib.parse,urllib.request
from pathlib import Path
from workbench_data import ROOT

API='https://tnmaccess.nationalmap.gov/api/v1/products'
DATASETS={'opr':'Original Product Resolution (OPR) Digital Elevation Model (DEM)',
          'dem1m':'Digital Elevation Model (DEM) 1 meter',
          'lidar':'Lidar Point Cloud (LPC)'}
OUT=ROOT/'data/elevation'

def query(dataset,bbox):
    items=[];offset=0
    while True:
        params={'datasets':dataset,'bbox':','.join(map(str,bbox)),'max':100,'offset':offset}
        url=API+'?'+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={'User-Agent':'CentralValleyWorkbench/0.4'})
        with urllib.request.urlopen(req,timeout=90) as response:d=json.load(response)
        if 'items' not in d:raise ValueError('Invalid catalog response: '+str(d)[:400])
        batch=d['items'];items.extend(batch)
        total=int(d.get('total',len(items)))
        if len(items)>=total:break
        if not batch:raise ValueError('Incomplete catalog response')
        offset+=len(batch)
        if offset>=2000:raise ValueError('Catalog exceeds 2000 items; use a smaller extent')
    return items

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def save_json(path,obj):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(obj,indent=2),encoding='utf-8');temp.replace(path)

def discover():
    bbox=json.loads((ROOT/'output/stats.json').read_text())['pilot_bbox']
    report={'bbox':bbox,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'api':API,'products':{},'issues':[]}
    for key,dataset in DATASETS.items():
        try:
            items=query(dataset,bbox);report['products'][key]=items
            print(key,len(items),'products',flush=True)
            for i,item in enumerate(items):
                print(f'  {key}:{i} {item.get("title")} | {item.get("sizeInBytes")} bytes')
        except (OSError,ValueError,KeyError,TypeError) as e:report['issues'].append({'dataset':key,'error':str(e)});print(key,e)
    save_json(OUT/'catalog.json',report)
    print('Catalog:',OUT/'catalog.json')

def allowed(url):
    u=urllib.parse.urlsplit(url);host=u.hostname or ''
    return u.scheme=='https' and not u.username and not u.password and (host.endswith('.usgs.gov') or host.endswith('.nationalmap.gov') or host=='prd-tnm.s3.amazonaws.com' or host.startswith('prd-tnm.s3.') and host.endswith('.amazonaws.com'))

def download(key,index,item,max_bytes):
    url=item.get('downloadURL')
    if not isinstance(url,str) or not allowed(url):raise ValueError('Unexpected download URL: '+str(url))
    name=Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).name
    if not name or Path(name).suffix.lower() not in ('.tif','.tiff','.laz','.las'):raise ValueError('Unsupported product file: '+name)
    expected=item.get('sizeInBytes') or 0
    if int(expected)>max_bytes:raise ValueError('Product exceeds configured download cap')
    folder=OUT/key;folder.mkdir(exist_ok=True)
    # URL-derived prefix prevents same-named products from distinct projects colliding.
    dest=folder/(hashlib.sha256(url.encode()).hexdigest()[:12]+'-'+name)
    manifest=dest.with_suffix(dest.suffix+'.json')
    if dest.exists() and manifest.exists():
        m=json.loads(manifest.read_text())
        if m.get('url')==url and m.get('sha256')==sha(dest):
            print('Using cached',dest);return
    temp=dest.with_suffix(dest.suffix+'.part');n=0
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CentralValleyWorkbench/0.4'})
        with urllib.request.urlopen(req,timeout=180) as response,temp.open('wb') as f:
            if not allowed(response.geturl()):raise ValueError('Unexpected redirected host')
            length=response.headers.get('Content-Length')
            if length and int(length)>max_bytes:raise ValueError('Response exceeds configured download cap')
            while b:=response.read(1024*1024):
                n+=len(b)
                if n>max_bytes:raise ValueError('Download exceeded cap')
                f.write(b)
        if not n or (length and n!=int(length)):raise ValueError('Incomplete download')
        with temp.open('rb') as f:magic=f.read(4)
        if Path(name).suffix.lower() in ('.laz','.las'):
            if magic!=b'LASF':raise ValueError('Expected LAS/LAZ')
        elif magic not in (b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+'):raise ValueError('Expected TIFF')
        m={'url':url,'sha256':sha(temp),'bytes':n,'dataset':key,'catalog_index':index,'catalog_item':item,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'vertical_datum':'verify from product metadata; not inferred from horizontal CRS'}
        temp.replace(dest);save_json(manifest,m);print('Saved',dest)
    finally:
        if temp.exists():temp.unlink()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download',action='append',metavar='KIND:INDEX',help='Select products from saved catalog, repeatable')
    p.add_argument('--match',help='Optional case-insensitive project substring')
    p.add_argument('--kind',choices=DATASETS,help='Required with --match; download matching products')
    p.add_argument('--max-mb',type=int,default=500,help='Per-product cap in decimal MB')
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if not a.download and not a.match:discover();return
    if a.max_mb<=0:p.error('Invalid download cap')
    report=json.loads((OUT/'catalog.json').read_text())
    chosen=[]
    for selection in a.download or []:
        key,i=selection.split(':');i=int(i)
        if i<0:p.error('Negative index')
        chosen.append((key,i,report['products'][key][i]))
    if a.match:
        if not a.kind:p.error('--match requires --kind')
        chosen.extend((a.kind,i,item) for i,item in enumerate(report['products'].get(a.kind,[])) if a.match.lower() in json.dumps(item).lower())
    if not chosen:p.error('No matching products; inspect catalog')
    for key,i,item in chosen:download(key,i,item,a.max_mb*1_000_000)

if __name__=='__main__':main()
