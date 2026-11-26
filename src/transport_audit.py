"""Non-authoritative vector comparison and experimental image alignment flags."""
import hashlib,json,math
from collections import Counter
from shapely.geometry import shape,mapping,box,LineString,Point
from shapely.ops import transform,substring,unary_union
from shapely.strtree import STRtree
from pyproj import CRS,Transformer
from workbench_data import ROOT,TO_MAP

def lines(g):
    if g.geom_type=='LineString':
        if g.length>0:yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms:yield from lines(part)

def gap_parts(line,reference,tree,tolerance=5,min_length=12):
    if not reference:return [line] if line.length>=min_length else []
    ids=tree.query(line.buffer(tolerance))
    nearby=[reference[int(i)] for i in ids]
    covered=unary_union(nearby).buffer(tolerance) if nearby else None
    gap=line.difference(covered) if covered is not None else line
    return [p for p in lines(gap) if p.length>=min_length]

def flag(id,kind,g,metadata,to_map):
    return {'id':id,'kind':kind,'geometry':mapping(transform(to_map.transform,g)),'tags':metadata,'evidence':{'status':'review_only',**metadata}}

def audit_vectors(osm,folder):
    local_crs=CRS.from_proj4(json.loads((ROOT/'world.json').read_text())['projection'])
    local=Transformer.from_crs(3857,local_crs,always_xy=True);back=Transformer.from_crs(local_crs,3857,always_xy=True)
    window=transform(local.transform,box(*osm['extent']))
    # Avoid classifying artificial gaps at the clipped boundary.
    interior=window.buffer(-10)
    result=[];issues=[];manifests=[]
    for name,kind in [('caltrans','road'),('fra','rail')]:
        path=folder/(name+'.geojson');mp=folder/(name+'.json')
        if not path.exists() or not mp.exists():continue
        try:
            raw=path.read_bytes();m=json.loads(mp.read_text())
            if hashlib.sha256(raw).hexdigest()!=m['sha256']:raise ValueError('Snapshot checksum mismatch')
            refs=[];raw_refs=[]
            for f in json.loads(raw)['features']:
                g=transform(TO_MAP.transform,shape(f['geometry']))
                if not g.is_valid or g.is_empty:raise ValueError('Invalid reference geometry')
                for i,l in enumerate(lines(transform(local.transform,g))):
                    if not l.intersects(window):continue
                    rid=name+'/'+str(f['id'])+'/'+str(i)
                    refs.append(l);raw_refs.append((rid,l,f['properties']))
            if not refs:raise ValueError('No reference lines intersect pilot; cannot assess coverage')
            candidates=[]
            for f in osm['features']:
                if f['kind']!=kind:continue
                for l in lines(transform(local.transform,shape(f['geometry']))):
                    candidates.append((f,l))
            osm_lines=[l for f,l in candidates];ot=STRtree(osm_lines);rt=STRtree(refs)
            tolerance=5 if kind=='road' else 3
            for rid,l,props in raw_refs:
                result.append(flag(rid,'reference_'+kind,l,{'source':name,'properties':props,'snapshot_sha256':m['sha256']},back))
                for j,part in enumerate(lines(l.intersection(interior))):
                    for k,gap in enumerate(gap_parts(part,osm_lines,ot,tolerance)):
                        result.append(flag(f'gap/{rid}/{j}/{k}','transport_gap',gap,{'source':name,'reference_id':rid,'feature_kind':kind,'length_m':round(gap.length,2),'tolerance_m':tolerance,'interpretation':'Reference corridor outside OSM buffer; possible missing connection, alignment difference or representation mismatch.'},back))
            # Flag offset evidence in either direction, but never assert OSM-only is erroneous.
            for f,l in candidates:
                for j,part in enumerate(lines(l.intersection(interior))):
                    for k,gap in enumerate(gap_parts(part,refs,rt,tolerance)):
                        result.append(flag(f'osm-gap/{name}/{f["id"]}/{j}/{k}','transport_disagreement',gap,{'source':name,'osm_id':f['id'],'feature_kind':kind,'length_m':round(gap.length,2),'tolerance_m':tolerance,'interpretation':'OSM corridor outside reference buffer; reference may omit service roads or individual tracks.'},back))
            manifests.append(m)
        except (ValueError,OSError,KeyError,TypeError) as exc:issues.append({'source':name,'error':str(exc)})
    return result,issues,manifests

def image_audit(osm,sampler,high_resolution=False):
    """Find lateral shifts with stronger paired edge contrast along straight stretches.
    This is an image signal, not semantic road/rail segmentation or a proposed correction.
    """
    import numpy as np
    from imagery_analysis import rail_pair_scores
    local_crs=CRS.from_proj4(json.loads((ROOT/'world.json').read_text())['projection'])
    local=Transformer.from_crs(3857,local_crs,always_xy=True);back=Transformer.from_crs(local_crs,3857,always_xy=True)
    window=transform(local.transform,box(*osm['extent'])).buffer(-18)
    offsets=np.linspace(-12,12,97 if high_resolution else 25)
    baseline=len(offsets)//2
    def sample(x,y):
        a,b=back.transform(x,y)
        return sampler.sample(a,b)
    flags=[];tested=0
    for f in osm['features']:
        kind=f['kind'];t=f['tags']
        if kind not in ('road','rail') or t.get('bridge','no')!='no' or t.get('tunnel','no')!='no':continue
        if kind=='road' and t.get('highway') not in ('primary','secondary','tertiary','residential','unclassified','trunk','motorway','service'):continue
        if kind=='rail' and t.get('railway') not in ('rail','light_rail','tram','narrow_gauge'):continue
        widths=[2.5,4,6,8] if kind=='road' else [1.5,2.5,4]
        g=transform(local.transform,shape(f['geometry']))
        for pi,part in enumerate(lines(g.intersection(window))):
            for i,start in enumerate(range(0,int(part.length),30)):
                seg=substring(part,start,min(start+30,part.length))
                if seg.geom_type!='LineString' or seg.length<20:continue
                a,b=seg.coords[0],seg.coords[-1];dx=b[0]-a[0];dy=b[1]-a[1];chord=math.hypot(dx,dy)
                if chord/seg.length<.98:continue
                chordline=LineString([a,b])
                if any(Point(p).distance(chordline)>1 for p in seg.coords):continue
                nx,ny=-dy/chord,dx/chord
                tgrid=np.linspace(.1,.9,40 if high_resolution else 16)
                cx=a[0]+dx*tgrid;cy=a[1]+dy*tgrid
                sampler.used.clear()
                scores=[]
                for halfwidth in widths:
                    contrasts=[]
                    for side in (-1,1):
                        pos=offsets[:,None]+side*halfwidth
                        inside=pos-side*.7;outside=pos+side*.7
                        p=sample(cx+nx*inside,cy+ny*inside);q=sample(cx+nx*outside,cy+ny*outside)
                        if p is None or q is None:break
                        contrasts.append(np.abs(p-q))
                    if len(contrasts)==2:
                        scores.append(np.median(np.minimum(*contrasts),axis=1))
                if not scores:continue
                score=np.max(scores,axis=0);method='paired_corridor_edges'
                if kind=='rail' and high_resolution:
                    rail=rail_pair_scores(sample,cx,cy,nx,ny,offsets)
                    if rail is not None and float(np.max(rail))>=8:
                        score=rail;method='gauge_constrained_rail_ridges'
                tested+=1
                best=int(np.argmax(score));base=float(score[baseline]);peak=float(score[best]);shift=float(offsets[best])
                # Require material gain and avoid maxima at search boundary.
                if (1.5 if high_resolution else 3)<=abs(shift)<12 and peak>=(8 if method=='gauge_constrained_rail_ridges' else 12) and peak-base>= (5 if high_resolution else 7) and peak>=1.5*max(base,1):
                    shifted=LineString([(x+nx*shift,y+ny*shift) for x,y in seg.coords])
                    flags.append(flag(f'image/{f["id"]}/{pi}/{i}','image_alignment',shifted,{'osm_id':f['id'],'feature_kind':kind,'shift_m_signed_left':shift,'baseline_edge_score':round(base,2),'candidate_edge_score':round(peak,2),'imagery_digest':sampler.digest,'imagery_ids':sorted(sampler.used),'method':method,'interpretation':'Stronger paired image edge contrast at an offset; could be curb, parallel track, shadow, adjacent road or registration error.'},back))
    return flags,tested

def main():
    import argparse
    from workbench_data import normalize,pilot_extent
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skip-image',action='store_true');p.add_argument('--image-source',default='dwr',help='dwr, naip, or explicit DWR snapshot/group ID');a=p.parse_args()
    osm=normalize(ROOT/'data/pilot.osm',pilot_extent())
    features,issues,sources=audit_vectors(osm,ROOT/'data/transport')
    tested=0;image_hash=None;image_sources=[];image_digest=None
    if not a.skip_image:
        try:
            from imagery_analysis import Sampler,select
            sampler=Sampler(select(a.image_source))
            image_sources=sampler.sources;image_digest=sampler.digest
            if a.image_source=='naip':image_hash=image_sources[0]['sha256']
            print('Analyzing',len(image_sources),'image patches',flush=True)
            image_flags,tested=image_audit(osm,sampler,high_resolution=a.image_source!='naip')
            features.extend(image_flags)
        except (ImportError,OSError,ValueError,KeyError) as e:
            p.exit(1,f'Image audit failed: {e}\nExisting audit left unchanged. Use --skip-image for vectors only.\n')
    out=ROOT/'output/transport';out.mkdir(parents=True,exist_ok=True)
    counts=dict(Counter(f['kind'] for f in features))
    data={'source_sha256':osm['source_sha256'],'extent':osm['extent'],'aerial_sha256':image_hash,'image_source':None if a.skip_image else a.image_source,'image_sources':image_sources,'image_digest':image_digest,'analysis_assumption':'DWR local analysis permitted by project working assumption; rights not independently verified' if not a.skip_image and a.image_source!='naip' else None,'sources':sources,'features':features,'issues':issues,'counts':counts,'image_windows_tested':tested,'status':'review_only','notes':'Vector gaps are not confirmed missing roads. Image flags are heuristic paired corridor edge or rail ridge contrast, not semantic segmentation. No geometry altered.'}
    temp=out/'audit.tmp';temp.write_text(json.dumps(data,allow_nan=False));temp.replace(out/'audit.json')
    print(json.dumps({k:v for k,v in data.items() if k not in ('features','sources')},indent=2))
if __name__=='__main__':main()
