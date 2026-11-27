"""Conservative refinement of verified unified terrain V1."""
import argparse,json,math
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.ndimage import label,find_objects,distance_transform_edt,gaussian_filter
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import mapping
from pyproj import CRS
from PIL import Image
from unified_terrain import sha,load_features,smooth,ROOT

def score(z,ref,res):
    count=0;cost=0.;peak=0.
    for a in (0,1):
        e=np.maximum(np.abs(np.diff(z,axis=a))/res-np.maximum(.08,np.abs(np.diff(ref,axis=a))/res),0)
        count+=int((e>1e-5).sum());cost+=float(np.sum(e*e,dtype=np.float64));peak=max(peak,float(e.max()))
    return count,cost,peak

def area(z,ref,eligible,res):
    gy,gx=np.gradient(z,res);g=np.hypot(gx,gy);del gx,gy
    gy,gx=np.gradient(ref,res);old=np.hypot(gx,gy)
    return float(((g>=.08)&(old<.08)&eligible).sum()*res**2)

def components(mask):
    labs,_=label(mask,structure=np.ones((3,3),int));counts=np.bincount(labs.ravel())
    return labs,{(sl[0].start,sl[1].start,sl[0].stop,sl[1].stop,int(counts[i])):i for i,sl in enumerate(find_objects(labs),1)}

def relax(z,free,steps=12):
    out=z.copy()
    for _ in range(steps):
        d=(out[:-2,1:-1]+out[2:,1:-1]+out[1:-1,:-2]+out[1:-1,2:])*.25-out[1:-1,1:-1]
        out[1:-1,1:-1]+=np.where(free[1:-1,1:-1],.65*d,0)
    return out

def refine(z,s,edge,ref,records,route,res):
    if any(a.shape!=z.shape for a in (s,edge,ref,route)) or not np.isfinite(z).all() or not np.isfinite(ref).all():raise ValueError('Invalid grid')
    out=z.copy();status=s.copy();reasons=Counter();accepted=[];eligible=(s!=3)&~edge
    before=area(z,ref,eligible,res);base=score(z,ref,res)
    labs,lookup=components(s==3)
    # Constrained smoothing of ordinary ground only; keep prior constraints and routes fixed.
    free=(s==0)&~edge&~route
    trial=relax(z,free,8);sc=score(trial,ref,res)
    smoothed=sc[0]<=base[0] and sc[1]<base[1] and sc[2]<=base[2]+1e-5
    if smoothed:out=trial
    del trial,free
    for p in sorted(records,key=lambda p:(p['max_change_m'],p['id'])):
        if p['status']!='blocked' or p['reasons']!=['significant_relief']:continue
        if p['max_change_m']>.35:reasons['change_budget']+=1;continue
        y,x,Y,X=p['pixel_bounds'];i=lookup.get(tuple(p['pixel_bounds']+[round(p['area_m2']/res**2)]))
        if i is None:reasons['unmatched_component']+=1;continue
        core=labs[y:Y,x:X]==i
        if np.any((edge[y:Y,x:X]|route[y:Y,x:X])[core]):reasons['edge_or_transport']+=1;continue
        rad=math.ceil(9/res)+2;w=(slice(max(0,y-rad),min(z.shape[0],Y+rad)),slice(max(0,x-rad),min(z.shape[1],X+rad)))
        core=labs[w]==i;old=out[w].copy();truth=ref[w];target=float(p['target_m']);fixed=((status[w]!=0)|route[w]|edge[w])&~core
        free=~fixed&~core;dist=distance_transform_edt(~core)*res;prev=score(old,truth,res);best=None
        for radius in (3,6,9):
            weight=(1-smooth(dist/radius)).astype(np.float32);weight[fixed]=0
            candidate=old+(target-old)*weight;candidate[core]=target
            candidate=relax(candidate,free&(dist<radius));candidate[core]=target
            sc=score(candidate,truth,res)
            if sc[0]>prev[0] or sc[1]>prev[1]+1e-8 or sc[2]>prev[2]+1e-5:continue
            if best is None or (sc[1],sc[0],radius)<best[0]:best=((sc[1],sc[0],radius),candidate)
        if best is None:reasons['transition_grade']+=1;continue
        out[w]=best[1];status[w][core]=2;accepted.append({'id':p['id'],'target_m':target,'area_m2':p['area_m2'],'blend_m':best[0][2]})
    released=(s==3)&(status==2);immutable=((s!=0)|edge|route)&~released
    if not np.array_equal(out[immutable],z[immutable]):raise AssertionError('Immutable samples changed')
    del labs,lookup
    labs,lookup=components(status==2);ids={p['id'] for p in accepted};checked=0
    for p in records:
        if p['status']!='proposed_level' and p['id'] not in ids:continue
        y,x,Y,X=p['pixel_bounds'];i=lookup.get(tuple(p['pixel_bounds']+[round(p['area_m2']/res**2)]))
        if i is None or not np.allclose(out[y:Y,x:X][labs[y:Y,x:X]==i],p['target_m'],rtol=0,atol=1e-6):raise AssertionError('Pad not planar or unmatched')
        checked+=1
    return out,status,{'released_pads':len(accepted),'released_zero_pads':sum(p['target_m']==0 for p in accepted),'released_area_m2':float(released.sum()*res**2),'accepted':accepted,'retained_relief_only_reasons':dict(reasons),'verified_planar_groups':checked,'remaining_blocked_pads':sum(p['status']=='blocked' for p in records)-len(accepted),'immutable_sample_count':int(immutable.sum()),'immutable_max_change_m':0.,'smoothing_accepted':smoothed,'new_steep_area_v1_m2':before,'new_steep_area_v2_same_domain_m2':area(out,ref,eligible,res),'new_steep_area_v2_expanded_domain_m2':area(out,ref,(status!=3)&~edge,res),'edge_excess_v1':base,'edge_excess_v2':score(out,ref,res),'flat_within_1cm_percent':float((np.abs(out)<=.01).mean()*100)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--v1-dir',type=Path,default=ROOT/'output/unified_terrain');p.add_argument('--v1-report',type=Path);p.add_argument('--ground-dir',type=Path,default=ROOT/'output/elevation');p.add_argument('--osm',type=Path,default=ROOT/'data/pilot.osm');p.add_argument('--out',type=Path,default=ROOT/'output/unified_terrain_v2');a=p.parse_args()
    rp=a.v1_report or a.v1_dir/'report.json';r=json.loads(rp.read_text());m=json.loads((a.ground_dir/'ground.json').read_text());gp=a.ground_dir/'ground.npy'
    if sha(gp)!=m['ground_sha256'] or m['ground_sha256']!=r['source_ground_sha256'] or sha(a.osm)!=r['osm_sha256']:p.error('Source hash mismatch')
    if any(m[k]!=r[k] for k in ('bounds_east_north_m','resolution_m','crs_wkt')) or m['vertical_units']!='m':p.error('Source grid mismatch')
    if a.out.resolve() in (a.v1_dir.resolve(),a.ground_dir.resolve()):p.error('Output must be separate')
    arrays={}
    for n in ('terrain','constraint_status','edge_review'):
        path=a.v1_dir/(n+'.npy')
        if sha(path)!=r['outputs'][n]:p.error(n+' checksum mismatch')
        arrays[n]=np.load(path,allow_pickle=False)
    z=np.load(gp,allow_pickle=False);res=m['resolution_m'];bounds=m['bounds_east_north_m']
    print('Reconstructing route protection and local relief...',flush=True);_,routes,_,_,_,_=load_features(a.osm,CRS.from_wkt(m['crs_wkt']),bounds)
    items=[(mapping(g),1) for group in routes.values() for _,g in group];route=rasterize(items,out_shape=z.shape,transform=from_bounds(*bounds,z.shape[1],z.shape[0]),fill=0,all_touched=True,dtype='uint8').astype(bool) if items else np.zeros(z.shape,bool)
    ref=z-gaussian_filter(z,r['parameters']['sigma_m']/res,mode='reflect');del z
    print('Refining slopes and eligible foundations...',flush=True);out,s,q=refine(arrays['terrain'],arrays['constraint_status'],arrays['edge_review'],ref,r['pads'],route,res)
    a.out.mkdir(parents=True,exist_ok=True)
    for n,v in [('terrain',out),('constraint_status',s),('edge_review',arrays['edge_review'])]:np.save(a.out/(n+'.npy'),v,allow_pickle=False)
    palette=np.array([[209,216,205],[88,141,183],[78,166,105],[211,79,76]],np.uint8);Image.fromarray(palette[s]).resize((1024,1024),Image.Resampling.NEAREST).save(a.out/'constraints.png')
    q.update(status='experimental_not_compilable',source_report_sha256=sha(rp),source_ground_sha256=m['ground_sha256'],osm_sha256=r['osm_sha256'],source_outputs=r['outputs'],outputs={n:sha(a.out/(n+'.npy')) for n in ('terrain','constraint_status','edge_review')},bounds_east_north_m=bounds,resolution_m=res,crs_wkt=m['crs_wkt'],vertical_datum=m['vertical_datum'],policy='Exact matched relief-only components, <=0.35m adjustment, outside route and edge masks; no worsening of local forward-edge excess count, squared excess or maximum. Prior constraints unchanged except released pads.',limitations='Numerical trial, not geographic approval; assumed OSM widths; missing water, entrances, deck clearance and engine tests. IDs refer to V1 report.')
    (a.out/'report.json').write_text(json.dumps(q,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in q.items() if k not in ('accepted','crs_wkt')},indent=2))
if __name__=='__main__':main()
