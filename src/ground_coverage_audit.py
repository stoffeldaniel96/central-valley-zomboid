"""Audit mapped road centerlines against proposed pavement; never generate missing surfaces."""
import argparse,json,zipfile,hashlib,math
from pathlib import Path
from collections import defaultdict
from pyproj import CRS,Transformer
from shapely.geometry import shape,box,mapping
from shapely.ops import transform,unary_union
from workbench_data import ROOT

PAVED={'road_surface','parking_surface','driveway'}
ROADS={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service'}

def lines(g):
    if g.geom_type=='LineString' and not g.is_empty:yield g
    elif hasattr(g,'geoms'):
        for p in g.geoms:yield from lines(p)

def audit(benchmark,candidates,projection=None,tolerance=.5,min_gap=3):
    if not math.isfinite(tolerance) or not math.isfinite(min_gap) or tolerance<0 or min_gap<0:raise ValueError('Invalid thresholds')
    projection=projection or json.loads((ROOT/'world.json').read_text())['projection']
    local=CRS.from_proj4(projection);to=Transformer.from_crs(3857,local,always_xy=True);back=Transformer.from_crs(local,3857,always_xy=True)
    with zipfile.ZipFile(benchmark) as z:
        m=json.loads(z.read('benchmark.json'));osm=json.loads(z.read('osm.json'))
    if m['crs']!='EPSG:3857' or osm['crs']!='EPSG:3857':raise ValueError('Unexpected benchmark CRS')
    c=json.loads(Path(candidates).read_text());crs=c.get('crs',{}).get('properties',{}).get('name')
    if crs not in ('EPSG:3857','urn:ogc:def:crs:EPSG::3857'):raise ValueError('Expected projected candidate GeoJSON')
    window=transform(to.transform,box(*m['context_extent']));polys=[]
    for f in c['features']:
        if f['properties'].get('kind') not in PAVED:continue
        g=transform(to.transform,shape(f['geometry']))
        if not g.is_valid or g.geom_type not in ('Polygon','MultiPolygon'):raise ValueError('Invalid pavement polygon')
        polys.append(g.intersection(window))
    pavement=unary_union(polys);near=pavement.buffer(tolerance)
    rows=[];flags=[];skipped=defaultdict(int)
    for f in osm['features']:
        if f['kind']!='road':continue
        t=f['tags'];highway=t.get('highway','unknown');base=highway.removesuffix('_link')
        if base not in ROADS or t.get('bridge','no')!='no' or t.get('tunnel','no')!='no' or t.get('area')=='yes' or t.get('construction') or t.get('proposed'):
            skipped[highway]+=1;continue
        line=transform(to.transform,shape(f['geometry'])).intersection(window)
        parts=list(lines(line));length=sum(p.length for p in parts)
        if not length:continue
        raw=sum(p.difference(pavement).length for p in parts)
        gaps=[g for p in parts for g in lines(p.difference(near))]
        missing=sum(g.length for g in gaps)
        row={'id':f['id'],'name':t.get('name'),'highway':highway,'length_m':length,'outside_exact_m':raw,'outside_tolerance_m':missing,'flagged_gap_count':sum(g.length>=min_gap for g in gaps)};rows.append(row)
        for i,g in enumerate(gaps):
            if g.length<min_gap:continue
            flags.append({'type':'Feature','geometry':mapping(transform(back.transform,g)),'properties':{'id':f['id']+'/'+str(i),'osm_id':f['id'],'name':t.get('name'),'highway':highway,'length_m':g.length,'status':'review_only'}})
    groups={}
    for label,rr in [('non_service',[x for x in rows if x['highway']!='service']),('service',[x for x in rows if x['highway']=='service'])]:
        total=sum(x['length_m'] for x in rr);missing=sum(x['outside_tolerance_m'] for x in rr)
        groups[label]={'ways':len(rr),'length_m':total,'outside_exact_m':sum(x['outside_exact_m'] for x in rr),'outside_tolerance_m':missing,'covered_fraction':1-missing/total if total else None,'flagged_gaps':sum(x['flagged_gap_count'] for x in rr)}
    report={'benchmark_sha256':hashlib.sha256(Path(benchmark).read_bytes()).hexdigest(),'candidates_sha256':hashlib.sha256(Path(candidates).read_bytes()).hexdigest(),'tolerance_m':tolerance,'min_flag_length_m':min_gap,'groups':groups,'skipped_by_highway':dict(skipped),'ways':sorted(rows,key=lambda r:-r['outside_tolerance_m']),'limitations':'Road centerline coverage only, not pavement width, material truth, road topology or accuracy. OSM representation/date may differ. Service roads include parking aisles. No geometry generated or modified.'}
    return report,{'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'EPSG:3857'}},'features':flags}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--benchmark',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'output/ground_coverage');p.add_argument('--tolerance',type=float,default=.5);p.add_argument('--min-gap',type=float,default=3);a=p.parse_args()
    report,flags=audit(a.benchmark,a.candidates,tolerance=a.tolerance,min_gap=a.min_gap);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False));(a.out/'gaps.geojson').write_text(json.dumps(flags,indent=2,allow_nan=False));print(json.dumps(report['groups'],indent=2))
if __name__=='__main__':main()
