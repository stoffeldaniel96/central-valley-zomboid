"""Export a reproducible local benchmark view without changing observations."""
import hashlib,io,json,math,zipfile
from pathlib import Path
from shapely.geometry import box,shape
from PIL import Image

def capture(data,bounds,image_path):
    if len(bounds)!=4 or not all(math.isfinite(v) for v in bounds):
        raise ValueError('Invalid view bounds')
    x0,y0,x1,y1=bounds
    if x0>=x1 or y0>=y1:raise ValueError('Empty view')
    window=box(*bounds).intersection(box(*data['extent']))
    if window.is_empty or window.area<=0:raise ValueError('View is outside pilot')
    # Include a small contextual margin, without clipping feature geometry.
    context=window.buffer(40).intersection(box(*data['extent']))
    layers={}
    for name,fs in (
        ('osm',data['features']),
        ('building_evidence',(data.get('building_evidence') or {}).get('features',[])),
        ('transport_audit',(data.get('transport_audit') or {}).get('features',[]))):
        layers[name]=[f for f in fs if shape(f['geometry']).intersects(context)]
    meta={'schema_version':1,'crs':'EPSG:3857','view_extent':list(window.bounds),
          'context_extent':list(context.bounds),'pilot_extent':data['extent'],
          'source_sha256':data['source_sha256'],'counts':{k:len(v) for k,v in layers.items()},
          'building_manifest':(data.get('building_evidence') or {}).get('manifest'),
          'transport_metadata':{k:v for k,v in (data.get('transport_audit') or {}).items() if k!='features'},
          'aerial_manifest':data.get('aerial'),'notes':'Full intersecting features, not clipped. Context buffer is 40 Web Mercator units, not ground meters. Crop retains original image pixel grid. Audit flags are review candidates only.'}
    image_bytes=None
    if data.get('aerial'):
        m=data['aerial'];raw=image_path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=m['sha256']:raise ValueError('Aerial snapshot changed; restart workbench')
        a,b,c,d=m['extent'];w,h=m['width'],m['height'];sx=(c-a)/w;sy=(d-b)/h
        ex0,ey0,ex1,ey1=context.bounds
        l=max(0,math.floor((ex0-a)/sx));r=min(w,math.ceil((ex1-a)/sx))
        t=max(0,math.floor((d-ey1)/sy));bt=min(h,math.ceil((d-ey0)/sy))
        if l<r and t<bt:
            with Image.open(io.BytesIO(raw)) as im:
                if im.size!=(w,h):raise ValueError('Aerial image dimensions mismatch')
                buf=io.BytesIO();im.crop((l,t,r,bt)).save(buf,format='PNG');image_bytes=buf.getvalue()
            meta['aerial_crop']={'file':'aerial.png','extent':[a+l*sx,d-bt*sy,a+r*sx,d-t*sy],
                'width':r-l,'height':bt-t,'pixel_window':[l,t,r,bt],'sha256':hashlib.sha256(image_bytes).hexdigest()}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('benchmark.json',json.dumps(meta,indent=2,allow_nan=False))
        for name,fs in layers.items():
            z.writestr(name+'.json',json.dumps({'crs':'EPSG:3857','features':fs},allow_nan=False))
        if image_bytes is not None:z.writestr('aerial.png',image_bytes)
    return out.getvalue()
