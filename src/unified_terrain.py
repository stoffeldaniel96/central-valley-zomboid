"""Shared terrain fit with planar pad and protected-relief constraints (trial only)."""
import argparse,hashlib,json,math,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.ndimage import gaussian_filter,label,find_objects,distance_transform_edt
from shapely.geometry import Polygon,MultiPolygon,LineString,shape,box,mapping
from shapely.ops import transform,linemerge
from shapely.strtree import STRtree
from pyproj import CRS,Transformer
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

def rings(lines):
    if not lines:return []
    m=lines[0] if len(lines)==1 else linemerge(lines)
    parts=[m] if m.geom_type=='LineString' else list(m.geoms)
    if any(not p.is_ring for p in parts):raise ValueError('Unclosed member ring')
    return [Polygon(p) for p in parts]

def assemble(outer,inner):
    shells=rings(outer);holes=[[] for _ in shells]
    for h in rings(inner):
        ix=[i for i,s in enumerate(shells) if s.contains(h)]
        if len(ix)!=1:raise ValueError('Ambiguous hole')
        holes[ix[0]].append(list(h.exterior.coords))
    p=[Polygon(s.exterior.coords,h) for s,h in zip(shells,holes)]
    return MultiPolygon(p) if len(p)!=1 else p[0]

def load_features(osm,local,bounds,overture=None,benchmark=None):
    root=ET.fromstring(osm.read_bytes());window=box(*bounds);to=Transformer.from_crs(4326,local,always_xy=True)
    nodes={n.attrib['id']:to.transform(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')};ways={w.attrib['id']:w for w in root.findall('way')}
    buildings=[];routes={k:[] for k in ('road','rail','water','stacked','passage')};issues=[];review=[];represented=set()
    def tags(w):return {a.attrib['k']:a.attrib['v'] for a in w.findall('tag')}
    def line(w):return LineString([nodes[n.attrib['ref']] for n in w.findall('nd')])
    def kind(t):
        if t.get('building') not in (None,'no','proposed','construction'):return 'building'
        if t.get('water') or t.get('natural')=='water' or t.get('waterway') in ('river','canal','stream','ditch','drain','riverbank'):return 'water'
    def add(arr,id,g):
        if g.is_empty or not g.is_valid:raise ValueError('Invalid geometry')
        if g.intersects(window):arr.append((id,g))
    def width(t,default):
        try:
            w=float(t.get('width',''))
            if 0<w<=100:return w
        except ValueError:pass
        try:return min(40,max(default,float(t.get('lanes',0))*3.3))
        except ValueError:return default
    for rel in root.findall('relation'):
        t=tags(rel);k=kind(t);id='relation/'+rel.attrib['id']
        if not k or t.get('type')!='multipolygon':continue
        try:
            outer=[];inner=[];refs=[]
            for m in rel.findall('member'):
                if m.get('type')!='way' or m.get('role','') not in ('','inner','outer'):raise ValueError('Unsupported relation member')
                ref=m.get('ref');refs.append(ref);(inner if m.get('role')=='inner' else outer).append(line(ways[ref]))
            add(buildings if k=='building' else routes[k],id,assemble(outer,inner));represented.update(ref for ref in refs if kind(tags(ways[ref]))==k)
        except (ValueError,KeyError) as e:issues.append({'id':id,'reason':str(e)})
    for ref,w in ways.items():
        t=tags(w);id='way/'+ref;k=kind(t);hw=t.get('highway');rw=t.get('railway')
        if not (k or hw or rw) or ref in represented:continue
        try:
            g=line(w)
            if k=='building':
                if not g.is_ring:raise ValueError('Open building footprint')
                add(buildings,id,Polygon(g));continue
            road=hw in ('motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service','track') or bool(hw and hw.endswith('_link'))
            rail=rw in ('rail','light_rail','narrow_gauge','tram','disused','abandoned')
            if t.get('tunnel')=='building_passage':add(routes['passage'],id,g.buffer(width(t,4)/2));continue
            if (hw or rail) and (t.get('bridge','no')!='no' or t.get('tunnel','no')!='no'):
                add(routes['stacked'],id,g.buffer(width(t,6)/2));continue
            if k=='water':add(routes['water'],id,Polygon(g) if g.is_ring and (t.get('natural')=='water' or t.get('water') or t.get('waterway')=='riverbank') else g.buffer(width(t,4)/2))
            if road:add(routes['road'],id,g.buffer(width(t,4 if hw=='service' else 7)/2))
            if rail:add(routes['rail'],id,g.buffer(width(t,6)/2))
        except (ValueError,KeyError) as e:issues.append({'id':id,'reason':str(e)})
    counts={'osm_buildings':len(buildings)};ref=[g for _,g in buildings];tree=STRtree(ref);candidates=[]
    if overture:
        digest=sha(overture);m=json.loads((overture.parent/'manifest.json').read_text())
        if m.get('sha256')!=digest:raise ValueError('Overture manifest checksum mismatch')
        d=json.loads(overture.read_text());source={'mode':'full_local_snapshot_extent_not_independently_verified','sha256':digest}
        if d.get('type')!='FeatureCollection':raise ValueError('Invalid Overture GeoJSON')
        candidates=[('overture/'+str((f.get('properties') or {}).get('id') or f.get('id') or ''),f['geometry'],to) for f in d['features']]
    elif benchmark:
        with zipfile.ZipFile(benchmark) as f:d=json.loads(f.read('building_evidence.json'))
        if d['crs']!='EPSG:3857':raise ValueError('Unexpected benchmark CRS')
        conv=Transformer.from_crs(3857,local,always_xy=True);candidates=[(f['id'],f['geometry'],conv) for f in d['features'] if f['kind'].startswith('overture_')];source={'mode':'partial_B01_only','sha256':sha(benchmark)}
    else:source={'mode':'OSM_only'}
    seen=set();matched=added=0
    for id,geom,conv in candidates:
        try:
            if id=='overture/' or id in seen:raise ValueError('Missing/duplicate ID')
            seen.add(id);g=transform(conv.transform,shape(geom))
            if not g.is_valid or g.geom_type not in ('Polygon','MultiPolygon') or g.is_empty:raise ValueError('Invalid footprint')
            if not g.intersects(window):continue
            near=[int(i) for i in tree.query(g.buffer(2)) if g.distance(ref[int(i)])<=2]
            if near:
                iou=[g.intersection(ref[i]).area/g.union(ref[i]).area for i in near]
                if max(iou)>=.7 and sum(v>=.1 for v in iou)==1:matched+=1
                else:review.append((id,g));issues.append({'id':id,'reason':'Nearby/overlapping OSM footprint; reconcile'})
            else:buildings.append((id,g));added+=1
        except (ValueError,KeyError,TypeError) as e:issues.append({'id':id,'reason':str(e)})
    counts.update(overture_added=added,overture_matched=matched,overture_overlap_review=len(review));return buildings,routes,review,issues,counts,source

def fit(z,bounds,spacing,buildings,routes,review,sigma=50,seed=.5,grow=.25,halo=8,blend=3):
    if not np.isfinite(z).all():raise ValueError('Complete DEM required for this trial')
    aff=from_bounds(*bounds,z.shape[1],z.shape[0])
    def mask(items):
        return rasterize([(mapping(g),1) for _,g in items],out_shape=z.shape,transform=aff,fill=0,all_touched=True,dtype='uint8').astype(bool) if items else np.zeros(z.shape,bool)
    pads=mask(buildings);masks={k:mask(v) for k,v in routes.items()};review_mask=mask(review)
    print('Broad grade and local relief...',flush=True);trend=gaussian_filter(z,sigma/spacing,mode='reflect');relief=z-trend;selected=np.zeros(z.shape,bool)
    for sign in (-1,1):
        v=relief*sign;lab,n=label(v>=grow,structure=np.ones((3,3),int));count=np.bincount(lab.ravel());peaks=np.zeros(n+1,np.float32);np.maximum.at(peaks,lab.ravel(),v.ravel());keep=(count*spacing**2>=4)&(peaks>=seed);keep[0]=False;selected|=keep[lab]
    del lab,v,count,peaks,keep,trend
    gy,gx=np.gradient(gaussian_filter(relief,1/spacing),spacing);route_relief=(np.hypot(gx,gy)>=.08)&(masks['road']|masks['rail']);del gx,gy
    hard=selected|route_relief|masks['water']|masks['stacked']|masks['rail']|masks['passage']|review_mask
    groups,n=label(pads,structure=np.ones((3,3),int));records=[];accepted=[];blocked=review_mask.copy()
    print('Checking foundation constraints...',flush=True)
    for i,sl in enumerate(find_objects(groups),1):
        core=groups[sl]==i;v=relief[sl][core];med=float(np.median(v));target=0. if abs(med)<=.25 else med
        reasons=[k for k,m in [('significant_relief',selected),('steep_route',route_relief),('rail',masks['rail']),('water',masks['water']),('stacked',masks['stacked']),('passage',masks['passage']),('overlap_review',review_mask)] if np.any(core&m[sl])]
        if np.any(core&masks['road'][sl]&(np.abs(relief[sl]-target)>.05)):reasons.append('road_grade_or_footprint_overlap')
        if any(a.start==0 or a.stop==size for a,size in zip(sl,z.shape)):reasons.append('edge_foundation')
        if reasons:blocked[sl]|=core
        else:accepted.append((i,sl,target))
        records.append({'id':i,'target_m':target,'area_m2':float(core.sum()*spacing**2),'max_change_m':float(np.max(np.abs(v-target))),'reasons':reasons,'status':'blocked' if reasons else 'proposed_level','pixel_bounds':[sl[0].start,sl[1].start,sl[0].stop,sl[1].stop]})
    hard|=blocked
    if hard.any():dist=distance_transform_edt(~hard).astype(np.float32)*spacing;out=relief*(1-smooth(dist/halo));guard=smooth(dist/blend);del dist
    else:out=np.zeros_like(z);guard=np.ones_like(z)
    weights=np.zeros_like(z);sums=np.zeros_like(z);strength=np.zeros_like(z);rad=math.ceil(blend/spacing)+1
    for i,sl,target in accepted:
        rr,cc=sl;win=(slice(max(0,rr.start-rad),min(z.shape[0],rr.stop+rad)),slice(max(0,cc.start-rad),min(z.shape[1],cc.stop+rad)))
        core=groups[win]==i;w=(1-smooth(distance_transform_edt(~core)*spacing/blend)).astype(np.float32)
        weights[win]+=w;sums[win]+=w*target;strength[win]=np.maximum(strength[win],w)
    target=np.divide(sums,weights,out=np.zeros_like(sums),where=weights>0);strength*=guard;out=out*(1-strength)+target*strength
    for i,sl,t in accepted:
        core=groups[sl]==i;out[sl][core]=t
        if np.ptp(out[sl][core])!=0:raise AssertionError('Nonplanar proposed pad')
    if not np.array_equal(out[hard],relief[hard]):raise AssertionError('Protected samples altered')
    blocked|=masks['stacked']|masks['passage'];edge=min(math.ceil(4*sigma/spacing),min(z.shape)//2);edge_mask=np.zeros(z.shape,bool);edge_mask[:edge]=True;edge_mask[-edge:]=True;edge_mask[:,:edge]=True;edge_mask[:,-edge:]=True
    status=np.zeros(z.shape,np.uint8);status[hard]=1;status[pads&~blocked]=2;status[blocked]=3
    report={'pad_groups':n,'proposed_level_pads':len(accepted),'blocked_pads':n-len(accepted),'proposed_zero_pads':sum(t==0 for _,_,t in accepted),'protected_samples':int(hard.sum()),'protected_relief_percent':float(selected.mean()*100),'road_steep_area_m2':float(route_relief.sum()*spacing**2),'flat_within_1cm_percent':float((np.abs(out)<=.01).mean()*100),'blocked_area_m2':float(blocked.sum()*spacing**2),'provisional_edge_area_percent':float(edge_mask.mean()*100),'max_protected_change_m':float(np.max(np.abs(out[hard]-relief[hard]))) if hard.any() else 0.,'min_m':float(out.min()),'max_m':float(out.max()),'route_features':{k:len(v) for k,v in routes.items()},'route_area_m2':{k:float(v.sum()*spacing**2) for k,v in masks.items()},'conflict_counts':dict(Counter(k for rec in records for k in rec['reasons'])),'pads':records}
    return out,status,edge_mask,report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ground-dir',type=Path,default=ROOT/'output/elevation');p.add_argument('--osm',type=Path,default=ROOT/'data/pilot.osm');p.add_argument('--overture',type=Path,default=ROOT/'data/buildings/overture.geojson');p.add_argument('--benchmark',type=Path);p.add_argument('--allow-partial',action='store_true');p.add_argument('--out',type=Path,default=ROOT/'output/unified_terrain');a=p.parse_args()
    if not a.overture.exists() and not a.allow_partial:p.error('Full Overture snapshot missing; run fetch_buildings.py or use --allow-partial explicitly')
    m=json.loads((a.ground_dir/'ground.json').read_text());path=a.ground_dir/'ground.npy'
    if m.get('vertical_units')!='m' or sha(path)!=m['ground_sha256']:p.error('Invalid ground hash or units')
    z=np.load(path,allow_pickle=False);bounds=m['bounds_east_north_m'];spacing=m['resolution_m']
    if list(z.shape)!=m['shape'] or not math.isclose(bounds[2]-bounds[0],z.shape[1]*spacing) or not math.isclose(bounds[3]-bounds[1],z.shape[0]*spacing):p.error('DEM geometry mismatch')
    print('Loading geographic constraints...',flush=True);b,r,review,issues,counts,source=load_features(a.osm,CRS.from_wkt(m['crs_wkt']),bounds,a.overture if a.overture.exists() else None,a.benchmark)
    print('Fitting terrain and level pads...',flush=True);out,status,edge,report=fit(z,bounds,spacing,b,r,review)
    a.out.mkdir(parents=True,exist_ok=True)
    for n,v in [('terrain',out),('constraint_status',status),('edge_review',edge)]:np.save(a.out/(n+'.npy'),v,allow_pickle=False)
    palette=np.array([[209,216,205],[88,141,183],[78,166,105],[211,79,76]],np.uint8);Image.fromarray(palette[status]).resize((1024,1024),Image.Resampling.NEAREST).save(a.out/'constraints.png')
    report.update(status='experimental_not_compilable',source_ground_sha256=m['ground_sha256'],osm_sha256=sha(a.osm),overture=source,footprint_counts=counts,issues=issues,bounds_east_north_m=bounds,resolution_m=spacing,crs_wkt=m['crs_wkt'],vertical_datum=m['vertical_datum'],outputs={n:sha(a.out/(n+'.npy')) for n in ('terrain','constraint_status','edge_review')},parameters={'sigma_m':50,'seed_m':.5,'grow_m':.25,'halo_m':8,'pad_blend_m':3,'road_grade':.08},limitations='Provisional: footprint reconciliation, external transport/water evidence, entrances, drainage and deck heights not solved. Road buffers are assumed widths, not pavement. Protected local residual is not original absolute grade. Edge context missing. Status 0 ordinary/taper, 1 protected, 2 proposed planar pad, 3 blocked; edge_review is independent. No engine compilation permitted.')
    (a.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in report.items() if k not in ('pads','issues','crs_wkt')},indent=2))
if __name__=='__main__':main()
