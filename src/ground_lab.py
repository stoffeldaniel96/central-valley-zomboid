"""Ground-first metric terrain and native-grid approximation laboratory.
Not a PZ compiler. Signed local Z and continuous evidence remain authoritative.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from pyproj import CRS,Transformer
from shapely.geometry import box,shape
from shapely.ops import transform,unary_union
from shapely import contains_xy
from workbench_data import ROOT
from fetch_elevation import sha

def fixture(x,y):
    # A sloping plane, recessed drainage channel and diagonal grade.
    # All coordinates in meters, deliberately crossing reference Z=0.
    return .035*(x-32)+.018*(y-32)-2.4*np.maximum(0,1-np.abs(x-20-.25*y)/6)

def dem_sampler(path,meta,zero):
    if meta.get('vertical_units')!='m' or sha(path)!=meta['ground_sha256']:raise ValueError('DEM units or checksum invalid')
    z=np.load(path,mmap_mode='r',allow_pickle=False)
    if list(z.shape)!=meta['shape']:raise ValueError('DEM shape mismatch')
    a,b,c,d=meta['bounds_east_north_m'];res=meta['resolution_m'];h,w=z.shape
    if not math.isclose(c-a,w*res) or not math.isclose(d-b,h*res):raise ValueError('DEM extent mismatch')
    def sample(x,y):
        x,y=np.broadcast_arrays(x,y)
        px=(x-a)/res-.5;py=(d-y)/res-.5
        valid=(px>=0)&(px<w-1)&(py>=0)&(py<h-1)
        ix=np.clip(np.floor(px).astype(int),0,w-2);iy=np.clip(np.floor(py).astype(int),0,h-2)
        fx=px-ix;fy=py-iy
        # No extrapolation and no interpolation over missing observations.
        v=(1-fy)*((1-fx)*z[iy,ix]+fx*z[iy,ix+1])+fy*((1-fx)*z[iy+1,ix]+fx*z[iy+1,ix+1])-zero
        return np.where(valid,v,np.nan)
    return sample

def metric_window(bounds):
    a,b,c,d=bounds
    if not all(math.isfinite(v) for v in bounds) or not a<c or not b<d:raise ValueError('Invalid bounds')
    a,b,c,d=math.floor(a),math.floor(b),math.ceil(c),math.ceil(d)
    if max(c-a,d-b)>512:raise ValueError('Ground lab limited to 512m per side')
    return a,b,c,d

def error_stats(err):
    e=np.abs(np.asarray(err));e=e[np.isfinite(e)]
    if not e.size:return {'count':0,'median_m':None,'p95_m':None,'max_m':None}
    return {'count':int(e.size),'median_m':float(np.median(e)),'p95_m':float(np.percentile(e,95)),'max_m':float(np.max(e))}

def approximate(sample,bounds,grade_step=.025,height_step=.05,storey=3):
    a,b,c,d=metric_window(bounds)
    x,y=np.meshgrid(np.arange(a,c)+.5,np.arange(d-1,b-1,-1)+.5)
    xv,yv=np.meshgrid(np.arange(a,c+1),np.arange(d,b-1,-1))
    vertices=sample(xv,yv)
    center=sample(x,y)
    # Planes fitted from four shared corner values. East and north gradients.
    nw,ne,sw,se=vertices[:-1,:-1],vertices[:-1,1:],vertices[1:,:-1],vertices[1:,1:]
    gx=(ne+se-nw-sw)/2;gy=(nw+ne-sw-se)/2
    valid=np.isfinite(center)&np.isfinite(gx)&np.isfinite(gy)
    # Compare to eight-direction slope proxies, not a claim of engine support.
    angle=np.arctan2(gy,gx);direction=np.rint(np.where(valid,angle,0)/(np.pi/4)).astype(int)%8
    ux=np.cos(direction*np.pi/4);uy=np.sin(direction*np.pi/4)
    grade=np.maximum(0,np.rint((gx*ux+gy*uy)/grade_step)*grade_step)
    qx=grade*ux;qy=grade*uy;qc=np.rint(center/height_step)*height_step
    qx=np.where(valid,qx,np.nan);qy=np.where(valid,qy,np.nan);qc=np.where(valid,qc,np.nan)
    # Explicit signed floor semantics; -0.1 belongs to level -1, never 0.
    levels=np.where(valid,np.floor(qc/storey),np.nan)
    relief=(np.abs(qx)+np.abs(qy))/2
    crosses=valid&(np.floor((qc-relief)/storey)!=np.floor((qc+relief)/storey))
    errors=[];flat_errors=[]
    for oy in (-.375,-.125,.125,.375):
        for ox in (-.375,-.125,.125,.375):
            truth=sample(x+ox,y+oy)
            errors.append(np.where(valid,qc+qx*ox+qy*oy-truth,np.nan))
            flat_errors.append(np.where(valid,qc-truth,np.nan))
    # Shared boundary endpoints expose cracks hidden by center-only evaluation.
    seam=[]
    for t in (-.5,.5):
        seam.append((qc[:,:-1]+qx[:,:-1]*.5+qy[:,:-1]*t)-(qc[:,1:]-qx[:,1:]*.5+qy[:,1:]*t))
        seam.append((qc[:-1,:]-qy[:-1,:]*.5+qx[:-1,:]*t)-(qc[1:,:]+qy[1:,:]*.5+qx[1:,:]*t))
    finite=vertices[np.isfinite(vertices)]
    signatures={}
    for di,gr in zip(direction[valid],grade[valid]):
        key='flat' if gr==0 else f'd{di}:g{round(float(gr),6)}'
        signatures[key]=signatures.get(key,0)+1
    report={'bounds_east_north_m':[a,b,c,d],'native_grid_shape':list(center.shape),'valid_tiles':int(valid.sum()),'unknown_tiles':int(valid.size-valid.sum()),'signed_z_range_m':[float(finite.min()),float(finite.max())] if finite.size else None,'negative_center_tiles':int((valid&(center<0)).sum()),'negative_proxy_level_tiles':int((valid&(levels<0)).sum()),'cross_storey_tiles':int(crosses.sum()),'flat_proxy_error':error_stats(np.concatenate([e.ravel() for e in flat_errors])),'slope_proxy_error':error_stats(np.concatenate([e.ravel() for e in errors])),'slope_proxy_shared_edge_disagreement':error_stats(np.concatenate([e.ravel() for e in seam])),'grade_step':grade_step,'height_step_m':height_step,'experimental_storey_m':storey,'slope_family_counts':signatures,'rare_slope_families_under_10':{k:v for k,v in signatures.items() if v<10},'notes':'Proxy errors relative to sampled input, not surveyed truth. Eight-direction and storey parameters experimental, not native engine capability. Shared-edge disagreement is not resolved by hiding it.'}
    return report,{'vertices':vertices,'center':center,'proxy_center':qc,'proxy_east_grade':qx,'proxy_north_grade':qy,'proxy_level':levels,'valid':valid,'cross_storey':crosses}

def write_obj(path,vertices,bounds):
    """Continuous shared-vertex surface; missing observations leave holes."""
    a,b,c,d=bounds;h,w=vertices.shape
    ids=np.zeros((h,w),dtype=np.int64);n=0
    with path.open('w',encoding='ascii') as f:
        f.write('# East X, north Y, signed height Z; meters; inspection mesh only\n')
        for row,col in np.argwhere(np.isfinite(vertices)):
            n+=1;ids[row,col]=n;f.write(f'v {a+col:.6f} {d-row:.6f} {vertices[row,col]:.6f}\n')
        for row in range(h-1):
            for col in range(w-1):
                nw,ne,sw,se=ids[row,col],ids[row,col+1],ids[row+1,col],ids[row+1,col+1]
                if nw and sw and ne:f.write(f'f {nw} {sw} {ne}\n')
                if ne and sw and se:f.write(f'f {ne} {sw} {se}\n')

def material_audit(path,local,bounds):
    """Independent proposed surfaces; union same class; do not resolve conflicts by priority."""
    src=json.loads(path.read_text())
    if src.get('crs',{}).get('properties',{}).get('name') not in ('EPSG:3857','urn:ogc:def:crs:EPSG::3857'):raise ValueError('Supply explicitly EPSG:3857 candidates')
    to_local=Transformer.from_crs(3857,local,always_xy=True)
    classes={'road_surface':'pavement','parking_surface':'pavement','driveway':'pavement','sidewalk':'sidewalk','grass':'grass','bare_soil':'soil','gravel':'gravel','unknown_surface':'unknown'}
    # Painted islands are decoration, roof outlines are not ground, curb/rail lines are separate assemblies.
    grouped={};a,b,c,d=bounds;window=box(a,b,c,d)
    for feature in src['features']:
        kind=feature.get('properties',{}).get('kind')
        if kind not in classes:continue
        g=transform(to_local.transform,shape(feature['geometry']))
        if not g.is_valid:raise ValueError('Invalid candidate geometry')
        g=g.intersection(window)
        if not g.is_empty:grouped.setdefault(classes[kind],[]).append(g)
    names=sorted(grouped);geoms=[unary_union(grouped[n]) for n in names]
    x,y=np.meshgrid(np.arange(a,c)+.5,np.arange(d-1,b-1,-1)+.5)
    def classify(xx,yy):
        result=np.zeros(xx.shape,dtype=np.int16)
        for i,g in enumerate(geoms,1):
            hit=contains_xy(g,xx,yy);result=np.where(hit,np.where(result==0,i,-1),result)
        return result
    base=classify(x,y);mixed=np.zeros(base.shape,bool);mismatch=known=conflict=0
    samples=[]
    for dy in (-.375,-.125,.125,.375):
        for dx in (-.375,-.125,.125,.375):
            sub=classify(x+dx,y+dy);samples.append(sub)
            mixed|=sub!=base
            comparable=(sub>0)&(base>0)
            mismatch+=int((comparable&(sub!=base)).sum());known+=int(comparable.sum());conflict+=int((sub<0).sum())
    sub=np.stack(samples);exact={n:float(g.area) for n,g in zip(names,geoms)}
    metrics={'candidate_sha256':sha(path),'classes':names,'exact_proposed_union_area_m2':exact,'center_sample_area_m2':{n:int((base==i).sum()) for i,n in enumerate(names,1)},'subtile_sample_area_m2':{n:float((sub==i).sum()/16) for i,n in enumerate(names,1)},'mixed_or_boundary_tiles':int(mixed.sum()),'unknown_center_tiles':int((base==0).sum()),'conflicting_center_tiles':int((base<0).sum()),'conflicting_subtile_samples':conflict,'known_to_known_mismatch_fraction':mismatch/known if known else None,'notes':'Proposed geometry only; area excludes conflicting classifications from sampled counts; unknown is not grass. Center/quarter-meter sample comparison does not determine rendering fidelity. No geometry edited.'}
    return metrics,base,sub

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',action='store_true')
    p.add_argument('--benchmark',type=Path,help='B01 benchmark ZIP with context extent');p.add_argument('--bounds',type=float,nargs=4,help='Local east/north meters')
    p.add_argument('--zero-elevation-m',type=float,help='Explicit persistent world vertical reference in DEM datum; never per benchmark')
    p.add_argument('--candidates',type=Path,help='Optional projected physical candidate GeoJSON')
    p.add_argument('--grade-step',type=float,default=.025);p.add_argument('--height-step',type=float,default=.05);p.add_argument('--storey-m',type=float,default=3)
    a=p.parse_args()
    if any(not math.isfinite(v) or v<=0 for v in (a.grade_step,a.height_step,a.storey_m)):p.error('Positive finite proxy parameters required')
    cfg=json.loads((ROOT/'world.json').read_text());local=CRS.from_proj4(cfg['projection'])
    if a.benchmark:
        import zipfile
        with zipfile.ZipFile(a.benchmark) as z:m=json.loads(z.read('benchmark.json'))
        if m['crs']!='EPSG:3857':p.error('Unexpected benchmark CRS')
        bounds=transform(Transformer.from_crs(3857,local,always_xy=True).transform,box(*m['context_extent'])).bounds
    else:bounds=a.bounds or [0,0,64,64]
    bounds=metric_window(bounds)
    if a.fixture:
        if a.benchmark or a.candidates:p.error('Synthetic fixture must not be mixed with geographic observations')
        sample=fixture;source={'type':'synthetic_fixture','zero_elevation_m':0,'datum':'synthetic'}
    else:
        if not a.benchmark and not a.bounds:p.error('Select a geographic benchmark or explicit bounds')
        if a.zero_elevation_m is None or not math.isfinite(a.zero_elevation_m):p.error('Explicit --zero-elevation-m required; use one persistent regional value')
        folder=ROOT/'output/elevation';m=json.loads((folder/'ground.json').read_text())
        if not CRS.from_wkt(m['crs_wkt']).equals(local):p.error('DEM projection mismatch')
        sample=dem_sampler(folder/'ground.npy',m,a.zero_elevation_m)
        source={'type':'observed_dem','sha256':m['ground_sha256'],'datum':m['vertical_datum'],'zero_elevation_m':a.zero_elevation_m}
    report,arrays=approximate(sample,bounds,a.grade_step,a.height_step,a.storey_m)
    report['source']=source;report['crs_wkt']=None if a.fixture else local.to_wkt()
    if not report['valid_tiles']:p.error('No valid elevation tiles in window')
    if a.candidates:
        report['material_audit'],arrays['material_center'],arrays['material_subsamples']=material_audit(a.candidates,local,bounds)
    out=ROOT/'output/ground_lab'/('fixture' if a.fixture else 'benchmark');out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'ground.npz',**arrays)
    write_obj(out/'ground.obj',arrays['vertices'],report['bounds_east_north_m'])
    report['ground_npz_sha256']=sha(out/'ground.npz');report['mesh_sha256']=sha(out/'ground.obj')
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in report.items() if k!='crs_wkt'},indent=2,allow_nan=False));print('Saved:',out)
if __name__=='__main__':main()
