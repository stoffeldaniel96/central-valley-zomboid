"""Read-only OSM normalization for the reconciliation viewer."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from pyproj import Transformer
from shapely.geometry import LineString,Polygon,MultiPolygon,mapping,box
from shapely.ops import linemerge

ROOT=Path(__file__).resolve().parents[1]
TO_MAP=Transformer.from_crs(4326,3857,always_xy=True)
TO_WGS=Transformer.from_crs(3857,4326,always_xy=True)

def pilot_extent():
    stats=json.loads((ROOT/'output/stats.json').read_text())
    w,s,e,n=stats['pilot_bbox']
    x,y=TO_MAP.transform(w,s);u,v=TO_MAP.transform(e,n)
    return [x,y,u,v]

def tags(element):
    return {t.attrib['k']:t.attrib['v'] for t in element.findall('tag')}

def kind(t):
    if t.get('building') and t['building']!='no':return 'building'
    if t.get('amenity')=='parking':return 'parking'
    if 'railway' in t:return 'rail'
    if 'highway' in t:return 'road'
    return None

def rings(lines):
    if not lines:return []
    merged=lines[0] if len(lines)==1 else linemerge(lines)
    parts=[merged] if merged.geom_type=='LineString' else list(merged.geoms)
    if any(not p.is_ring for p in parts):raise ValueError('Unclosed or nonsimple member ring')
    return [Polygon(p) for p in parts]

def assemble(outer,inner):
    shells=rings(outer);holes=rings(inner)
    if not shells:raise ValueError('No outer rings')
    assigned=[[] for _ in shells]
    for h in holes:
        candidates=[i for i,s in enumerate(shells) if s.contains(h)]
        if len(candidates)!=1:raise ValueError('Ambiguous or uncontained hole')
        assigned[candidates[0]].append(list(h.exterior.coords))
    polygons=[Polygon(s.exterior.coords,hs) for s,hs in zip(shells,assigned)]
    result=polygons[0] if len(polygons)==1 else MultiPolygon(polygons)
    if not result.is_valid or result.is_empty:raise ValueError('Invalid assembled multipolygon')
    return result

def normalize(path,extent):
    raw=path.read_bytes();root=ET.fromstring(raw)
    if root.tag!='osm' or root.find('remark') is not None:raise ValueError('Invalid OSM')
    nodes={n.attrib['id']:TO_MAP.transform(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    ways={w.attrib['id']:w for w in root.findall('way')}
    features=[];issues=[];represented=set();bounds=box(*extent)
    def line(w):
        return LineString([nodes[n.attrib['ref']] for n in w.findall('nd')])
    def add(id,k,t,g):
        if g.is_empty or not g.is_valid:raise ValueError('Invalid geometry')
        if g.intersects(bounds):
            features.append({'id':id,'kind':k,'tags':t,'geometry':mapping(g)})
    for rel in root.findall('relation'):
        t=tags(rel);k=kind(t);id='relation/'+rel.attrib['id']
        if t.get('type')!='multipolygon' or not k:continue
        try:
            outer=[];inner=[];members=[]
            for m in rel.findall('member'):
                if m.attrib['type']!='way':raise ValueError('Unsupported non-way member')
                role=m.get('role','')
                if role not in ('outer','inner',''):raise ValueError('Unsupported member role')
                ref=m.attrib['ref'];members.append(ref)
                (inner if role=='inner' else outer).append(line(ways[ref]))
            add(id,k,t,assemble(outer,inner))
            # Preserve member ways that have independent, different semantics.
            represented.update(ref for ref in members if kind(tags(ways[ref]))==k)
        except (ValueError,KeyError) as e:issues.append({'id':id,'error':str(e)})
    for ref,w in ways.items():
        t=tags(w);k=kind(t);id='way/'+ref
        if not k or ref in represented:continue
        try:
            g=line(w)
            if k in ('building','parking') or t.get('area')=='yes':
                if not g.is_ring:raise ValueError('Expected closed polygon')
                g=Polygon(g)
            add(id,k,t,g)
        except (ValueError,KeyError) as e:issues.append({'id':id,'error':str(e)})
    return {'crs':'EPSG:3857','extent':extent,'source_sha256':hashlib.sha256(raw).hexdigest(),'features':features,'issues':issues,'notes':'Complete intersecting features retained; viewer clips visually. Web Mercator coordinates are not ground meters.'}
