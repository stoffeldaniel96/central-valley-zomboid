"""Reproject DEM observations to the fixed pilot grid; retain unknown cells."""
import argparse,hashlib,json,math,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from pyproj import CRS,Transformer
from workbench_data import ROOT
from imagery_registry import register
from fetch_elevation import sha

def grid_spec(resolution):
    c=json.loads((ROOT/'world.json').read_text());x0,y0,x1,y1=json.loads((ROOT/'output/stats.json').read_text())['pilot_cells']
    cell=c['cell_tiles']*c['meters_per_tile'];bounds=[x0*cell,-y1*cell,x1*cell,-y0*cell]
    w=(bounds[2]-bounds[0])/resolution;h=(bounds[3]-bounds[1])/resolution
    if not math.isclose(w,round(w)) or not math.isclose(h,round(h)):raise ValueError('Resolution must evenly divide pilot extent')
    if w*h>20_000_000:raise ValueError('Grid exceeds 20 million cells')
    return CRS.from_proj4(c['projection']),bounds,int(round(w)),int(round(h))

def stats(z):
    valid=np.isfinite(z)
    if not valid.any():return {'valid_fraction':0,'min_m':None,'max_m':None,'median_m':None}
    return {'valid_fraction':float(valid.mean()),'min_m':float(np.min(z[valid])),'max_m':float(np.max(z[valid])),'median_m':float(np.median(z[valid]))}

def colorize(z):
    valid=np.isfinite(z)
    if not valid.any():raise ValueError('No valid DEM cells')
    lo,hi=np.percentile(z[valid],[2,98]);v=np.clip((np.where(valid,z,lo)-lo)/max(hi-lo,.01),0,1)
    # Elevation ramp, independent of any terrain material classification.
    colors=np.array([[36,64,124],[45,155,166],[148,187,99],[240,204,114],[190,98,62]],dtype=float)
    t=v*4;i=np.minimum(t.astype(int),3);f=(t-i)[...,None]
    rgb=(colors[i]*(1-f)+colors[i+1]*f).astype(np.uint8);rgb[~valid]=[90,90,90]
    return rgb,float(lo),float(hi)

def display_layer(z,src_crs,bounds,resolution,provider,meta):
    import rasterio
    from rasterio.warp import reproject,Resampling,transform_bounds
    from rasterio.transform import from_bounds
    h,w=z.shape;ext=transform_bounds(src_crs,3857,*bounds,densify_pts=21)
    # Display raster only; numeric source grid remains in local metric coordinates.
    disp=np.full((h,w),np.nan,dtype=np.float32)
    reproject(z,disp,src_transform=from_bounds(*bounds,w,h),src_crs=src_crs,src_nodata=np.nan,
              dst_transform=from_bounds(*ext,w,h),dst_crs='EPSG:3857',dst_nodata=np.nan,resampling=Resampling.bilinear)
    rgb,lo,hi=colorize(disp)
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'elevation.png';Image.fromarray(rgb).save(path)
        return register(path,list(ext),provider,usage='reference_only',rights_note='Derived preview of public USGS elevation observations; numeric grid stored separately.',metadata={**meta,'color_scale_m':[lo,hi],'nodata_color':'gray','display_only':True,'grid_spacing_m':resolution})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dem',nargs='+',type=Path,help='Explicit DEM files; otherwise use downloaded OPR files')
    p.add_argument('--resolution',type=float,default=.5)
    p.add_argument('--vertical-datum',required=True,help='Verified common source vertical datum, e.g. NAVD88 (Geoid18)')
    a=p.parse_args()
    if not math.isfinite(a.resolution) or a.resolution<=0:p.error('Invalid resolution')
    import rasterio
    from rasterio.warp import reproject,Resampling
    from rasterio.transform import from_bounds
    paths=a.dem or sorted((ROOT/'data/elevation/opr').glob('*.tif'))
    if not paths:p.error('No OPR DEMs; download or specify --dem')
    crs,bounds,w,h=grid_spec(a.resolution);affine=from_bounds(*bounds,w,h)
    z=np.full((h,w),np.nan,dtype=np.float32);sources=[];conflicts=0
    for path in paths:
        with rasterio.open(path) as ds:
            if not ds.crs or ds.count!=1:raise ValueError('Expected single-band georeferenced DEM')
            # Explicit operator datum/unit check; never infer elevations from XY CRS.
            if ds.units[0] and str(ds.units[0]).lower() not in ('m','meter','metre','meters','metres'):raise ValueError('Non-meter vertical units: '+str(ds.units))
            source=ds.read(1,masked=True).astype('float32').filled(np.nan)
            v=np.full_like(z,np.nan)
            reproject(source,v,src_transform=ds.transform,src_crs=ds.crs,src_nodata=np.nan,dst_transform=affine,dst_crs=crs,dst_nodata=np.nan,resampling=Resampling.bilinear)
            overlap=np.isfinite(z)&np.isfinite(v);conflicts+=int(np.count_nonzero(overlap & (np.abs(z-v)>.25)))
            take=~np.isfinite(z)&np.isfinite(v);z[take]=v[take]
            sources.append({'file':path.name,'sha256':sha(path),'crs':str(ds.crs),'source_resolution':list(ds.res),'source_units':ds.units,'covered_cells':int(np.isfinite(v).sum())})
    summary=stats(z)
    if not summary['valid_fraction']:raise ValueError('No DEM coverage in pilot')
    out=ROOT/'output/elevation';out.mkdir(parents=True,exist_ok=True)
    np.save(out/'ground.npy',z,allow_pickle=False)
    meta={'crs_wkt':crs.to_wkt(),'bounds_east_north_m':bounds,'shape':[h,w],'resolution_m':a.resolution,'vertical_datum':a.vertical_datum,'vertical_units':'m (operator verified)','sources':sources,'ground_sha256':sha(out/'ground.npy'),'overlap_disagreements_over_0_25m':conflicts,'overlap_policy':'first valid source wins; conflicts counted for review','stats':summary,'notes':'Bare-earth only. NaN means unknown; no fabricated elevation. Grid interval is not source accuracy. North-up rows.'}
    meta['display_layer_id']=display_layer(z,crs,bounds,a.resolution,'3DEP bare-earth elevation',{'vertical_datum':a.vertical_datum,'stats':summary})['id']
    (out/'ground.json').write_text(json.dumps(meta,indent=2));print(json.dumps({k:v for k,v in meta.items() if k!='crs_wkt'},indent=2))
if __name__=='__main__':main()
