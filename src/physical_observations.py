"""Independent evidence observations, not authoritative physical world geometry."""
import datetime,uuid
from shapely.geometry import shape,mapping,box
from shapely.ops import unary_union

CLASSES={'road_surface':'Polygon','parking_surface':'Polygon','driveway':'Polygon','sidewalk':'Polygon','median':'Polygon','grass':'Polygon','bare_soil':'Polygon','gravel':'Polygon','roof_outline':'Polygon','canopy':'Polygon','curb':'LineString','track_centerline':'LineString','painted_line':'LineString','fence':'LineString','crosswalk':'Polygon','unknown_surface':'Polygon'}
def create(body,extent,images):
    kind=body['kind']
    if kind not in CLASSES:raise ValueError('Unknown physical observation class')
    g=shape(body['geometry'])
    if g.geom_type!=CLASSES[kind] or not g.is_valid or g.is_empty or g.has_z:raise ValueError('Invalid observation geometry for class')
    if not box(*extent).covers(g):raise ValueError('Observation crosses pilot bounds')
    source=body['image_source']
    if not isinstance(source,str) or not source:raise ValueError('Select DWR imagery first')
    candidates=[m for m in images if (m.get('metadata',{}).get('mosaic_group') or m['id'])==source and m.get('metadata',{}).get('source','').endswith('/San_Joaquin_Valley_2021/ImageServer')]
    used=[m for m in candidates if box(*m['extent']).intersects(g)]
    if not used or not unary_union([box(*m['extent']) for m in used]).buffer(.001).covers(g):raise ValueError('Observation outside selected DWR coverage')
    note=body.get('notes','')
    if not isinstance(note,str) or len(note)>2000:raise ValueError('Invalid notes')
    return {'id':'observation/'+str(uuid.uuid4()),'kind':kind,'geometry':mapping(g),'crs':'EPSG:3857','status':'proposed','observation_type':'manual_visual','sources':[{'id':m['id'],'sha256':m['sha256'],'acquisition_window':m.get('metadata',{}).get('acquisition_window')} for m in used],'notes':note.strip(),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limitations':'Image-visible feature only; material, wall footprint, height, present-day existence and mechanical semantics not established.'}
