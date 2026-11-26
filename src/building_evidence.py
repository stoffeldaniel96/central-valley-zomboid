"""Compare building observations without promoting either source to ground truth."""
import hashlib,json
from collections import Counter
from shapely.geometry import shape,mapping,box
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import CRS,Transformer
from workbench_data import ROOT,TO_MAP

def compare(geom,reference,tree):
    # All inputs are in the same local metric projection.
    nearby=tree.query(geom.buffer(2))
    overlaps=[];near=[]
    for i in nearby:
        i=int(i);g=reference[i]
        if geom.distance(g)>2:continue
        near.append(i)
        a=geom.intersection(g).area
        if a>0:
            overlaps.append((i,a/(geom.area+g.area-a),a/geom.area,a/g.area))
    overlaps.sort(key=lambda v:v[1],reverse=True)
    significant=[v for v in overlaps if max(v[2],v[3])>=.1]
    best=overlaps[0] if overlaps else None
    if best and best[1]>=.7 and len(significant)==1:status='matched'
    elif not near:status='coverage_candidate'
    else:status='review_overlap'
    return status,best,near

def load_evidence(path,manifest_path,osm_data):
    raw=path.read_bytes();m=json.loads(manifest_path.read_text())
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=m.get('sha256'):raise ValueError('Building snapshot checksum mismatch')
    d=json.loads(raw)
    if d.get('type')!='FeatureCollection':raise ValueError('Expected GeoJSON FeatureCollection')
    crs=CRS.from_proj4(json.loads((ROOT/'world.json').read_text())['projection'])
    local=Transformer.from_crs(3857,crs,always_xy=True)
    ref=[f for f in osm_data['features'] if f['kind']=='building' and f['geometry']['type'] in ('Polygon','MultiPolygon')]
    ref_geom=[transform(local.transform,shape(f['geometry'])) for f in ref]
    tree=STRtree(ref_geom);window=box(*osm_data['extent'])
    result=[];issues=[];seen=set();covered=set()
    for f in d['features']:
        props=f.get('properties') or {}
        id=str(props.get('id') or f.get('id') or '')
        try:
            if not id or id in seen:raise ValueError('Missing or duplicate source ID')
            seen.add(id)
            g=transform(TO_MAP.transform,shape(f['geometry']))
            if g.geom_type not in ('Polygon','MultiPolygon') or g.is_empty or not g.is_valid:raise ValueError('Invalid building footprint')
            if not g.intersects(window):continue
            metric=transform(local.transform,g)
            status,best,near=compare(metric,ref_geom,tree)
            sources=props.get('sources') or []
            # Presence of OSM in lineage is not independent corroboration.
            has_osm=any('openstreetmap' in str(s.get('dataset','')).lower() or str(s.get('dataset','')).lower()=='osm' for s in sources if isinstance(s,dict))
            if status=='matched':covered.add(best[0])
            result.append({'id':'overture/'+id,'kind':'overture_'+status,'geometry':mapping(g),'tags':props,
                'evidence':{'status':status,'contains_osm_lineage':has_osm,'lineage_present':bool(sources),'best_osm_id':ref[best[0]]['id'] if best else None,'best_iou':round(best[1],4) if best else None,'nearby_osm_ids':[ref[i]['id'] for i in near],'snapshot_sha256':digest}})
        except (ValueError,TypeError,KeyError,AttributeError) as e:issues.append({'id':id,'error':str(e)})
    counts=Counter(f['evidence']['status'] for f in result)
    return {'features':result,'issues':issues,'manifest':m,'counts':dict(counts),'osm_buildings':len(ref),'osm_without_high_iou_match':len(ref)-len(covered),'notes':'2 m proximity and 0.70 IoU are experimental matching thresholds. Candidates may be stale, roofprints, duplicates, or unmapped OSM lineage; not verified additions.'}
