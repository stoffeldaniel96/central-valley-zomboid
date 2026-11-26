"""Read-only OSM XML orientation diagnostics; no snapping or topology edits."""
import argparse, csv, json, math, hashlib
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from pyproj import CRS, Transformer

ROOT=Path(__file__).resolve().parents[1]

def metrics(dx,dy):
    length=math.hypot(dx,dy)
    bearing=math.degrees(math.atan2(dx,dy))%180
    d4=abs((bearing+45)%90-45)
    d8=abs((bearing+22.5)%45-22.5)
    return length,bearing,d4,d8

def classify(tags):
    if 'highway' in tags: return 'road'
    if 'building' in tags and tags['building']!='no': return 'building'
    if tags.get('amenity')=='parking': return 'parking'
    if 'railway' in tags: return 'rail'
    return None

def analyze(path,projection,bin_m=256):
    transform=Transformer.from_crs(4326,CRS.from_proj4(projection),always_xy=True)
    root=ET.parse(path).getroot()
    if root.tag!='osm' or root.find('remark') is not None: raise ValueError('Invalid or incomplete OSM XML')
    nodes={n.attrib['id']:transform.transform(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    rows=[]; bins=defaultdict(lambda:[0.,0.,0.,0.,0]); hist=defaultdict(float); missing=0
    for way in root.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
        kind=classify(tags)
        if not kind: continue
        refs=[n.attrib['ref'] for n in way.findall('nd')]
        for i,(a,b) in enumerate(zip(refs,refs[1:])):
            if a not in nodes or b not in nodes: missing+=1; continue
            x,y=nodes[a]; u,v=nodes[b]
            length,angle,d4,d8=metrics(u-x,v-y)
            if length==0: continue
            drift=length*math.sin(math.radians(d8))
            rows.append([way.attrib['id'],i,kind,length,angle,d4,d8,drift,x,y,u,v])
            hist[(kind,int(angle)//5*5)]+=length
            # Split at every spatial-bin boundary; allocate length rather than midpoint-only bias.
            cuts={0.,1.}
            for p,q in ((x,u),(y,v)):
                if p==q: continue
                for j in range(math.floor(min(p,q)/bin_m)+1,math.ceil(max(p,q)/bin_m)):
                    t=(j*bin_m-p)/(q-p)
                    if 0<t<1: cuts.add(t)
            cuts=sorted(cuts)
            for lo,hi in zip(cuts,cuts[1:]):
                mid=(lo+hi)/2; k=(kind,math.floor((x+(u-x)*mid)/bin_m),math.floor(-(y+(v-y)*mid)/bin_m))
                weight=length*(hi-lo); z=bins[k];z[0]+=weight;z[1]+=weight*d4;z[2]+=weight*d8;z[3]+=weight*(d8<=5);z[4]+=weight*(d4<=5)
    return rows,bins,hist,missing,len(root.findall('relation'))

def write_csv(path,header,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--osm',type=Path,default=ROOT/'data/pilot.osm');p.add_argument('--out',type=Path,default=ROOT/'output/geometry');p.add_argument('--bin-m',type=int,default=256);a=p.parse_args()
    if a.bin_m<=0:p.error('bin size must be positive')
    projection=json.loads((ROOT/'world.json').read_text())['projection']
    rows,bins,hist,missing,relations=analyze(a.osm,projection,a.bin_m)
    a.out.mkdir(parents=True,exist_ok=True)
    write_csv(a.out/'segments.csv',['way_id','segment','kind','length_m','bearing_axis_deg','cardinal_error_deg','octilinear_error_deg','fixed_start_lateral_m','x0_east','y0_north','x1_east','y1_north'],rows)
    write_csv(a.out/'heatmap.csv',['kind','x_bin','south_bin','length_m','mean_cardinal_error','mean_octilinear_error','octilinear_within_5deg_fraction','cardinal_within_5deg_fraction'],([*k,z[0],z[1]/z[0],z[2]/z[0],z[3]/z[0],z[4]/z[0]] for k,z in sorted(bins.items())))
    write_csv(a.out/'histogram.csv',['kind','bearing_axis_bin_deg','length_m'],([*k,v] for k,v in sorted(hist.items())))
    summary={'source_sha256':hashlib.sha256(a.osm.read_bytes()).hexdigest(),'projection':projection,'bin_m':a.bin_m,'segments':len(rows),'missing_node_segments':missing,'relations_not_analyzed':relations,'status':'diagnostic_only','notes':['Ways only; no multipolygon relation assembly, source reconciliation or snapping.','Five degree tolerance is exploratory; fixed-start lateral displacement is not a topology-preserving snap cost.','Input extent may include padding.']}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
