"""Identify local relief and proposed level foundation groups. Diagnostic, not compiler."""
import argparse,json,math,hashlib,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.ndimage import label,find_objects,distance_transform_edt
from shapely.geometry import Polygon,shape,box,mapping
from shapely.ops import transform
from pyproj import CRS,Transformer
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from terrain_relief import decompose,sha
ROOT=Path(__file__).resolve().parents[1]

def footprints(osm,benchmark,local,bounds):
    window=box(*bounds);to=Transformer.from_crs(4326,local,always_xy=True)
    root=ET.parse(osm).getroot();nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    result=[];skipped=[]
    for way in root.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')};refs=[n.attrib['ref'] for n in way.findall('nd')]
        if tags.get('building') in (None,'no','proposed','construction'):continue
        id='way/'+way.attrib['id']
        if len(refs)<4 or refs[0]!=refs[-1] or any(i not in nodes for i in refs):skipped.append(id);continue
        g=transform(to.transform,Polygon([nodes[i] for i in refs]))
        if not g.is_valid:skipped.append(id);continue
        if g.intersects(window):result.append((id,g))
    if benchmark:
        to=Transformer.from_crs(3857,local,always_xy=True)
        with zipfile.ZipFile(benchmark) as f:ev=json.loads(f.read('building_evidence.json'))
        if ev['crs']!='EPSG:3857':raise ValueError('Unexpected building evidence CRS')
        for f in ev['features']:
            if f['kind']!='overture_coverage_candidate':continue
            g=transform(to.transform,shape(f['geometry']))
            if g.is_valid and g.intersects(window):result.append((f['id'],g))
    return result,skipped

def identify(relief,mask,bounds,spacing,seed=.5,grow=.25,min_area=4):
    if not 0<grow<=seed or min_area<=0:raise ValueError('Invalid relief thresholds')
    h,w=relief.shape;features=[];selected=np.zeros(relief.shape,bool)
    for sign in (-1,1):
        v=relief*sign;lab,n=label(v>=grow,structure=np.ones((3,3),int))
        count=np.bincount(lab.ravel());peaks=np.zeros(n+1,np.float32)
        np.maximum.at(peaks,lab.ravel(),np.where(np.isfinite(v),v,0).ravel())
        keep=(count*spacing**2>=min_area)&(peaks>=seed);keep[0]=False;selected|=keep[lab]
        for i,sl in enumerate(find_objects(lab),1):
            if not keep[i]:continue
            rr,cc=sl;region=lab[sl]==i;q=np.unravel_index(np.argmax(np.where(region,v[sl],-np.inf)),region.shape)
            row=rr.start+q[0];col=cc.start+q[1]
            features.append({'sign':'raised' if sign==1 else 'depressed','area_m2':float(count[i]*spacing**2),'peak_relief_m':float(sign*peaks[i]),'peak_east_north_m':[float(bounds[0]+(col+.5)*spacing),float(bounds[3]-(row+.5)*spacing)],'bounds_east_north_m':[bounds[0]+cc.start*spacing,bounds[3]-rr.stop*spacing,bounds[0]+cc.stop*spacing,bounds[3]-rr.start*spacing],'footprint_overlap_m2':float(np.count_nonzero(region&mask[sl])*spacing**2),'edge_touch':rr.start==0 or cc.start==0 or rr.stop==h or cc.stop==w})
    return selected,sorted(features,key=lambda f:abs(f['peak_relief_m']),reverse=True)

def level_pads(relief,mask,selected,spacing,zero_tol=.25,blend_m=2):
    """Trial only: group touching raster pads. Overlaps explicitly unresolved."""
    if not np.isfinite(relief).all():raise ValueError('Pad trial requires complete supported relief; do not fill missing data')
    if not mask.any():raise ValueError('No foundation observations')
    pads,n=label(mask,structure=np.ones((3,3),int));heights=np.zeros(n+1,np.float32);records=[]
    for i,sl in enumerate(find_objects(pads),1):
        core=pads[sl]==i;v=relief[sl][core];med=float(np.median(v));target=0 if abs(med)<=zero_tol else med;heights[i]=target
        overlap=bool(np.any(selected[sl]&core))
        records.append({'group':i,'target_m':float(heights[i]),'area_m2':float(core.sum()*spacing**2),'observed_local_range_m':float(v.max()-v.min()),'max_abs_change_m':float(np.max(np.abs(v-target))),'status':'relief_conflict_review' if overlap else 'proposed','pixel_bounds':[sl[0].start,sl[1].start,sl[0].stop,sl[1].stop]})
    dist,ix=distance_transform_edt(~mask,return_indices=True);nearest=pads[ix[0],ix[1]]
    t=np.clip(dist*spacing/blend_m,0,1).astype(np.float32);t=t*t*(3-2*t)
    trial=relief*t+heights[nearest]*(1-t);trial[mask]=heights[pads[mask]]
    return trial,pads,records

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ground-dir',type=Path,default=ROOT/'output/elevation');p.add_argument('--osm',type=Path,default=ROOT/'data/pilot.osm');p.add_argument('--benchmark',type=Path);p.add_argument('--sigma-m',type=float,default=50);p.add_argument('--seed-m',type=float,default=.5);p.add_argument('--grow-m',type=float,default=.25);p.add_argument('--min-area-m2',type=float,default=4);p.add_argument('--zero-tolerance-m',type=float,default=.25);p.add_argument('--blend-m',type=float,default=2);p.add_argument('--out',type=Path,default=ROOT/'output/terrain_constraints');a=p.parse_args()
    if any(not math.isfinite(x) or x<=0 for x in (a.sigma_m,a.seed_m,a.grow_m,a.min_area_m2,a.blend_m)) or not math.isfinite(a.zero_tolerance_m) or a.zero_tolerance_m<0:p.error('Invalid trial parameters')
    m=json.loads((a.ground_dir/'ground.json').read_text());path=a.ground_dir/'ground.npy'
    if m.get('vertical_units')!='m' or sha(path)!=m['ground_sha256']:p.error('Invalid DEM units or checksum')
    z=np.load(path,allow_pickle=False);bounds=m['bounds_east_north_m'];spacing=m['resolution_m'];h,w=z.shape
    if list(z.shape)!=m['shape'] or not math.isclose(bounds[2]-bounds[0],w*spacing) or not math.isclose(bounds[3]-bounds[1],h*spacing):p.error('DEM geometry mismatch')
    print('Loading footprint observations...',flush=True);build,skipped=footprints(a.osm,a.benchmark,CRS.from_wkt(m['crs_wkt']),bounds)
    if not build:p.error('No building footprints')
    mask=rasterize([(mapping(g),1) for _,g in build],out_shape=z.shape,transform=from_bounds(*bounds,w,h),fill=0,all_touched=True,dtype='uint8').astype(bool)
    print('Computing local relief...',flush=True);trend,relief=decompose(z,spacing,a.sigma_m)
    print('Identifying relief and foundation conflicts...',flush=True);selected,features=identify(relief,mask,bounds,spacing,a.seed_m,a.grow_m,a.min_area_m2)
    print('Trial foundation leveling...',flush=True);trial,pads,records=level_pads(relief,mask,selected,spacing,a.zero_tolerance_m,a.blend_m)
    a.out.mkdir(parents=True,exist_ok=True)
    for name,arr in [('relief_mask',selected),('pad_groups',pads),('pad_trial',trial)]:np.save(a.out/(name+'.npy'),arr,allow_pickle=False)
    report={'status':'diagnostic_not_approved_terrain','source_ground_sha256':m['ground_sha256'],'osm_sha256':sha(a.osm),'benchmark_sha256':sha(a.benchmark) if a.benchmark else None,'bounds_east_north_m':bounds,'resolution_m':spacing,'crs_wkt':m['crs_wkt'],'source_vertical_datum':m['vertical_datum'],'parameters':{'sigma_m':a.sigma_m,'seed_m':a.seed_m,'grow_m':a.grow_m,'min_area_m2':a.min_area_m2,'zero_tolerance_m':a.zero_tolerance_m,'blend_m':a.blend_m},'source_footprints':len(build),'skipped_osm_ways':skipped,'pad_groups':len(records),'pad_area_m2':float(mask.sum()*spacing**2),'pad_groups_zero':sum(x['target_m']==0 for x in records),'pad_groups_nonzero':sum(x['target_m']!=0 for x in records),'pad_groups_overlapping_relief':sum(x['status']=='relief_conflict_review' for x in records),'relief_features':len(features),'raised_features':sum(x['sign']=='raised' for x in features),'depressed_features':sum(x['sign']=='depressed' for x in features),'relief_area_percent':float(selected.mean()*100),'features':features,'pads':records,'outputs':{name:sha(a.out/(name+'.npy')) for name in ('relief_mask','pad_groups','pad_trial')},'limitations':'Closed OSM building ways and optional benchmark Overture coverage candidates only; no relations or full Overture coverage. Footprint is not verified foundation. Touching raster pads grouped; 2m nearest-pad smoothstep blend may introduce seams where pad targets differ. Conflict flags are review obligations, not permission to flatten. Trial changes conflict areas for measurement only. No final flattening, drainage, road, bridge or clearance constraints enforced.'}
    (a.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in report.items() if k not in ('features','pads','crs_wkt','skipped_osm_ways')},indent=2,allow_nan=False))
if __name__=='__main__':main()
