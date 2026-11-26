"""Inspect public imagery catalog coverage; optionally acquire a bounded reference patch."""
import argparse,datetime,json,math, tempfile,urllib.parse
from pathlib import Path
from PIL import Image
from pyproj import Transformer
from fetch_aerial import get
from workbench_data import ROOT,pilot_extent,TO_MAP
from imagery_registry import register

SERVICES={'naip':'https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer','plus':'https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPPlus/ImageServer','dwr':'https://gis.water.ca.gov/arcgisimg/rest/services/Aerial_Photography/San_Joaquin_Valley_2021/ImageServer'}

def catalog(base,extent):
    fields='OBJECTID,Name,MinPS,MaxPS,LowPS,HighPS,Category,Tag,GroupName,ProductName' if base==SERVICES['dwr'] else 'OBJECTID,Name,Year,agency,vendor,acquisition_date,resolution_value,resolution_units'
    params={'f':'json','where':'Category=1','geometry':','.join(map(str,extent)),'geometryType':'esriGeometryEnvelope','inSR':3857,'spatialRel':'esriSpatialRelIntersects','returnGeometry':'false'}
    ids=json.loads(get(base+'/query',{**params,'returnIdsOnly':'true'}))
    if 'error' in ids or 'objectIds' not in ids:raise RuntimeError(str(ids.get('error','Missing catalog IDs')))
    ids=sorted(set(ids['objectIds'] or []))
    if len(ids)>2000:raise ValueError('Catalog too large for pilot')
    records=[]
    for i in range(0,len(ids),40):
        batch=ids[i:i+40]
        d=json.loads(get(base+'/query',{'f':'json','objectIds':','.join(map(str,batch)),'outFields':fields,'returnGeometry':'false'}))
        if 'error' in d or d.get('exceededTransferLimit'):raise RuntimeError(str(d.get('error','Truncated catalog')))
        got=[f['attributes'] for f in d.get('features',[])]
        if {r['OBJECTID'] for r in got}!=set(batch):raise ValueError('Incomplete catalog batch')
        records.extend(got)
    return records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',choices=SERVICES,default='plus')
    p.add_argument('--bbox',nargs=4,type=float,metavar=('WEST','SOUTH','EAST','NORTH'),help='WGS84 bounding box; defaults to pilot')
    p.add_argument('--export',action='store_true',help='Register a bounded reference patch; no automatic analysis')
    p.add_argument('--pixel-m',type=float,default=.2,help='Requested approximate ground sample interval, not native resolution')
    p.add_argument('--raster-id',type=int,help='Lock to a catalog raster ID, where it covers the requested patch')
    a=p.parse_args();base=SERVICES[a.source]
    if a.bbox:
        w,s,e,n=a.bbox
        if not -180<=w<e<=180 or not -85<=s<n<=85:p.error('Invalid WGS84 bounds')
        extent=[*TO_MAP.transform(w,s),*TO_MAP.transform(e,n)]
    else:extent=pilot_extent()
    records=catalog(base,extent)
    out=ROOT/'output/imagery';out.mkdir(parents=True,exist_ok=True)
    report={'service':base,'extent':extent,'crs':'EPSG:3857','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records}
    (out/(a.source+'-catalog.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    if not a.export:return
    if not .05<=a.pixel_m<=2:p.error('Pixel interval must be 0.05–2 m')
    if a.raster_id is not None and a.raster_id not in {r['OBJECTID'] for r in records}:p.error('Raster ID not in local catalog')
    x,y,u,v=extent
    lat=Transformer.from_crs(3857,4326,always_xy=True).transform((x+u)/2,(y+v)/2)[1]
    scale=math.cos(math.radians(lat))
    w=math.ceil((u-x)*scale/a.pixel_m);h=math.ceil((v-y)*scale/a.pixel_m)
    if max(w,h)>4000:p.error('Requested patch exceeds 4000 pixels per side; use a smaller bbox or coarser pixel interval')
    if not records:p.error('No imagery candidates')
    params={'f':'json','bbox':','.join(map(str,extent)),'bboxSR':3857,'imageSR':3857,'size':f'{w},{h}','format':'jpg','compressionQuality':100,'adjustAspectRatio':'false'}
    if a.raster_id is not None:params['mosaicRule']=json.dumps({'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':[a.raster_id],'mosaicOperation':'MT_FIRST'})
    d=json.loads(get(base+'/exportImage',params))
    if 'error' in d:raise RuntimeError(d['error'])
    href=d['href'];url=urllib.parse.urlparse(href)
    if url.scheme!='https' or not url.hostname or not (url.hostname.endswith(('.nationalmap.gov','.usgs.gov')) or (a.source=='dwr' and url.hostname.endswith('.water.ca.gov'))):raise ValueError('Unexpected export host')
    e=d['extent'];sr=e['spatialReference']
    if sr.get('latestWkid',sr.get('wkid')) not in (3857,102100,102113):raise ValueError('Unexpected image CRS')
    raw=get(href)
    with tempfile.TemporaryDirectory() as folder:
        file=Path(folder)/'patch.jpg';file.write_bytes(raw)
        with Image.open(file) as im:
            if im.format!='JPEG' or im.size!=(d['width'],d['height']):raise ValueError('Invalid export dimensions/format')
        m=register(file,[e[k] for k in ('xmin','ymin','xmax','ymax')],('California DWR San Joaquin Valley 2021' if a.source=='dwr' else f'USGS {a.source.upper()}'),usage='reference_only',native_gsd=.0762001524 if a.source=='dwr' else None,metadata={'catalog_candidates':records,'export_parameters':params,'source':base,'acquisition_window':'2021-03-28 to 2021-05-12' if a.source=='dwr' else None,'requested_ground_pixel_m':a.pixel_m,'note':'Catalog is not verified contributing imagery. Native resolution and reuse terms unverified.'})
    print('Registered imagery layer:',m['id'])

if __name__=='__main__':main()
