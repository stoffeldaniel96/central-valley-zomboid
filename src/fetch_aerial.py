"""Cache an independent NAIP image and its actual exported extent."""
import argparse,datetime,hashlib,json,urllib.parse,urllib.request
from pathlib import Path
from workbench_data import ROOT,pilot_extent

BASE='https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer'
def get(url,params=None):
    if params:url+='?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'CentralValleyWorkbench/0.1'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--year',type=int,help='Restrict mosaic to specified acquisition year; verify coverage')
    p.add_argument('--refresh',action='store_true')
    a=p.parse_args();out=ROOT/'data/aerial';out.mkdir(parents=True,exist_ok=True)
    extent=pilot_extent();bbox=','.join(map(str,extent));year=a.year
    if year is not None and not 2000<=year<=2100:p.error('Invalid year')
    manifest=out/'manifest.json'
    if manifest.exists() and not a.refresh:
        m=json.loads(manifest.read_text())
        if m.get('requested_extent')==extent and m.get('requested_year')==year:
            image=out/'pilot.jpg'
            if image.exists() and hashlib.sha256(image.read_bytes()).hexdigest()==m.get('sha256'):
                print('Using cached aerial snapshot');return
    where='Category=1'+(f' AND Year={year}' if year else '')
    catalog=json.loads(get(BASE+'/query',{'f':'json','where':where,'geometry':bbox,'geometryType':'esriGeometryEnvelope','inSR':3857,'spatialRel':'esriSpatialRelIntersects','outFields':'OBJECTID,Name,Year,acquisition_date,resolution_value,resolution_units,agency','returnGeometry':'false'}))
    if 'error' in catalog:raise RuntimeError(catalog['error'])
    candidates=[f['attributes'] for f in catalog.get('features',[])]
    if not candidates:raise RuntimeError('No matching imagery catalog records')
    params={'f':'json','bbox':bbox,'bboxSR':3857,'imageSR':3857,'size':'4000,4000','format':'jpg','compressionQuality':95,'adjustAspectRatio':'true','renderingRule':json.dumps({'rasterFunction':'NaturalColor'})}
    if year:params['mosaicRule']=json.dumps({'mosaicMethod':'esriMosaicAttribute','where':where,'sortField':'Year','sortValue':'3000','ascending':True,'mosaicOperation':'MT_FIRST'})
    result=json.loads(get(BASE+'/exportImage',params))
    if 'error' in result:raise RuntimeError(result['error'])
    href=result['href'];u=urllib.parse.urlparse(href)
    if u.scheme!='https' or not (u.hostname and (u.hostname.endswith('.nationalmap.gov') or u.hostname.endswith('.usgs.gov'))):raise RuntimeError('Unexpected imagery download host')
    raw=get(href)
    if not raw.startswith(b'\xff\xd8'):raise ValueError('Expected JPEG')
    e=result['extent']
    sr=e.get('spatialReference',{})
    if sr.get('latestWkid',sr.get('wkid')) not in (3857,102100,102113):raise ValueError('Unexpected export CRS')
    m={'id':'naip-'+hashlib.sha256(raw).hexdigest()[:16],'provider':'USGS/USDA NAIP','service':BASE,'license':'Public domain NAIP; review individual provenance','rights_review':'pending','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_year':year,'observed_at':None,'requested_extent':extent,'extent':[e[k] for k in ('xmin','ymin','xmax','ymax')],'crs':'EPSG:3857','width':result['width'],'height':result['height'],'sha256':hashlib.sha256(raw).hexdigest(),'catalog_candidates':candidates,'catalog_truncated':catalog.get('exceededTransferLimit',False),'export_parameters':params,'notes':'Catalog records are candidates, not proof of contributing imagery or exact vintage. Confirm coverage and registration; exported pixel spacing is not source resolution.'}
    for path,data in [(out/'pilot.jpg',raw),(manifest,json.dumps(m,indent=2).encode())]:
        temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);temp.replace(path)
    print(json.dumps({k:v for k,v in m.items() if k not in ('catalog_candidates','export_parameters')},indent=2))

if __name__=='__main__':main()
