"""B01 ground-only native control; local experimental output, not a production compiler."""
import argparse, hashlib, json, struct, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from pyproj import CRS, Transformer
from shapely.geometry import shape, box
from shapely.ops import transform, unary_union
from shapely import contains_xy

BOUNDS=(-768,512,-512,768)
N=256
# Palette and B42 format reference: MIT osm2zomboid. Validate installed game tiles.
PALETTE={-1:'blends_natural_01_0',0:'blends_natural_01_64',1:'blends_natural_01_16',2:'blends_street_01_32',3:'blends_street_01_80',4:'floors_exterior_tilesandstone_01_3'}
CLASSES={'grass':1,'gravel':2,'road_surface':3,'parking_surface':3,'driveway':3,'sidewalk':4}

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def material_grid(path,crs):
    d=json.loads(path.read_text())
    if d.get('crs',{}).get('properties',{}).get('name') not in ('EPSG:3857','urn:ogc:def:crs:EPSG::3857'):raise ValueError('Use projected candidate GeoJSON')
    to=Transformer.from_crs(3857,crs,always_xy=True);groups={i:[] for i in range(1,5)}
    for f in d['features']:
        k=CLASSES.get(f['properties'].get('kind'))
        if k is None:continue
        g=transform(to.transform,shape(f['geometry']))
        if not g.is_valid or g.geom_type not in ('Polygon','MultiPolygon'):raise ValueError('Invalid material polygon')
        groups[k].append(g.intersection(box(*BOUNDS)))
    a,b,c,d=BOUNDS;x,y=np.meshgrid(np.arange(a,c)+.5,np.arange(d-1,b-1,-1)+.5)
    out=np.zeros((N,N),np.int8)
    for k,gg in groups.items():
        if gg:
            hit=contains_xy(unary_union(gg),x,y);out[hit]=np.where(out[hit]==0,k,-1)
    return out

def native_cell(path,cx,cy,materials):
    """Single Z0 floor, one tile per square; LOTH/LOTP v1, no rooms or solid objects."""
    if materials.shape!=(N,N) or not np.isin(materials,list(PALETTE)).all():raise ValueError('Bad material grid')
    names=sorted(set(PALETTE[int(i)] for i in np.unique(materials)));ids={n:i for i,n in enumerate(names)}
    index=np.array([ids.get(PALETTE[i],0) for i in range(-1,5)],dtype=np.int32)[materials+1]
    path.mkdir(parents=True,exist_ok=False)
    header=b'LOTH'+struct.pack('<ii',1,len(names))+b''.join(n.encode()+b'\n' for n in names)+struct.pack('<6i',8,8,0,0,0,0)+bytes(1024)
    blocks=[]
    for bx in range(32):
        for by in range(32):
            tile=index[by*8:by*8+8,bx*8:bx*8+8].T.ravel()
            records=np.empty((64,3),dtype='<i4');records[:,0]=2;records[:,1]=-1;records[:,2]=tile;blocks.append(records.tobytes())
    start=12+8192;table=b''.join(struct.pack('<II',start+i*768,0) for i in range(1024))
    pack=struct.pack('<4siI',b'LOTP',1,1024)+table+b''.join(blocks)
    (path/f'{cx}_{cy}.lotheader').write_bytes(header);(path/f'world_{cx}_{cy}.lotpack').write_bytes(pack)
    (path/f'chunkdata_{cx}_{cy}.bin').write_bytes(b'\x00\x01'+bytes(1024))
    blob=(path/f'world_{cx}_{cy}.lotpack').read_bytes();decoded=np.empty_like(index)
    for bx in range(32):
        for by in range(32):
            offset,zero=struct.unpack_from('<II',blob,12+8*(bx*32+by));rec=np.frombuffer(blob,dtype='<i4',count=192,offset=offset).reshape(64,3)
            if zero or not (rec[:,0]==2).all() or not (rec[:,1]==-1).all():raise ValueError('Bad lotpack')
            decoded[by*8:by*8+8,bx*8:bx*8+8]=rec[:,2].reshape(8,8).T
    if not np.array_equal(decoded,index):raise ValueError('Roundtrip failed')
    return names

def build(terrain,candidates,out,cell):
    m=json.loads((terrain/'report.json').read_text());arrays={}
    for key in ('terrain','constraint_status','edge_review'):
        p=terrain/(key+'.npy')
        if sha(p)!=m['outputs'][key]:raise ValueError(key+' hash mismatch')
        arrays[key]=np.load(p,allow_pickle=False)
    a,b,c,d=m['bounds_east_north_m'];res=m['resolution_m'];x0,y0,x1,y1=BOUNDS
    if res!=.5 or any(v.shape!=(round((d-b)/res),round((c-a)/res)) for v in arrays.values()):raise ValueError('Expected aligned 0.5m terrain grid')
    if not (a<=x0-1 and x1+1<=c and b<=y0-1 and y1+1<=d):raise ValueError('Benchmark plus halo outside terrain')
    def crop(v):return v[round((d-y1-1)/res):round((d-y0+1)/res),round((x0-a-1)/res):round((x1-a+1)/res)]
    h=crop(arrays['terrain']);s=crop(arrays['constraint_status']);e=crop(arrays['edge_review'])
    if not np.isfinite(h).all():raise ValueError('Missing terrain')
    mat=material_grid(candidates,CRS.from_wkt(m['crs_wkt']));out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'shared_ground.npz',height_m=h.astype('<f4'),constraint_status=s,edge_review=e,material_center=mat)
    core=h[2:-2,2:-2];centers=core.reshape(N,2,N,2).mean(axis=(1,3));edge=np.ptp(core.reshape(N,2,N,2),axis=(1,3))
    cx,cy=cell;mod=out/'CV_B01_Flat_Control';folder=mod/'common/media/maps/CV_B01_Flat_Control';native_cell(folder,cx,cy,mat)
    yy,xx=np.where(mat==3)
    if not len(xx):raise ValueError('No pavement spawn')
    i=np.argmin((xx-128)**2+(yy-128)**2);sx,sy=int(xx[i]),int(yy[i]);wx,wy=cx*N+sx,cy*N+sy
    (folder/'map.info').write_text(f'title=Central Valley B01 Flat Control\ndescription=Experimental ground-only map; incomplete surfaces and no elevation.\nfixed2x=true\nzoomX={wx}\nzoomY={wy}\nzoomS=14\n')
    (folder/'spawnpoints.lua').write_text(f'function SpawnPoints()\n return {{ unemployed = {{ {{ posX = {wx}, posY = {wy}, posZ = 0 }} }} }}\nend\n')
    (folder/'objects.lua').write_text('objects = {}\n')
    info='name=Central Valley B01 Flat Control\nid=CV_B01_Flat_Control\ndescription=Experimental flat ground-only control.\nversionMin=42.0.0\n'
    (mod/'42').mkdir();(mod/'42/mod.info').write_text(info);(mod/'mod.info').write_text(info)
    (mod/'ATTRIBUTION.txt').write_text('Map evidence: OpenStreetMap contributors (ODbL), https://www.openstreetmap.org/copyright\nDWR 2021 aerial reference, derived provisional surface observations; local R&D only.\nB42 format and palette reference: osm2zomboid, MIT, https://github.com/jinxlover/osm2zomboid\nNo game art or source imagery included.\n')
    colors=np.array([[220,70,80],[65,69,74],[110,155,94],[185,158,114],[113,142,166],[220,210,183]],np.uint8);im=Image.fromarray(colors[mat+1]);im.resize((1024,1024),Image.Resampling.NEAREST).save(out/'materials.png');im.save(folder/'thumb.png');im.save(mod/'42/poster.png')
    report={'status':'flat_native_control_not_game_verified','metric_bounds':BOUNDS,'world_cell':cell,'world_transform':'world x = east - west + cellX*256; world y = north - northing + cellY*256; z positive up','crs_wkt':m['crs_wkt'],'height_grid_bounds_with_halo':[x0-1,y0-1,x1+1,y1+1],'height_grid_spacing_m':.5,'height_grid_convention':'north-up cell centers, signed metres; 1m halo on all sides','source_terrain_sha256':m['outputs']['terrain'],'candidate_sha256':sha(candidates),'shared_ground_sha256':sha(out/'shared_ground.npz'),'material_counts':{str(i):int((mat==i).sum()) for i in range(-1,5)},'height_min_max_m':[float(core.min()),float(core.max())],'tiles_center_abs_z_over_10cm':int((np.abs(centers)>.1).sum()),'tiles_subsample_range_over_10cm':int((edge>.1).sum()),'blocked_or_edge_samples':int(((s[2:-2,2:-2]==3)|e[2:-2,2:-2]).sum()),'palette':PALETTE,'spawn_world':[wx,wy,0],'native_tile_roundtrip':True,'native_files':{p.name:sha(p) for p in folder.iterdir() if p.suffix in ('.lotheader','.lotpack','.bin')},'limitations':'Native control deliberately all Z0. Unknown/conflicting areas use test-only placeholders; no markings, rails, buildings, vehicles, navigation zones or elevation physics. Verify game version and tile IDs; no automatic install. Shared heightfield not a Better Terrain import format.'}
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='crs_wkt'},indent=2))

def inspect(root,out):
    """Read-only workshop inventory; no file contents or binaries copied except mod.info."""
    root=root.resolve();files=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        entry={'path':str(p.relative_to(root)),'bytes':p.stat().st_size}
        if p.suffix.lower() in ('.jar','.zip'):
            try:
                with zipfile.ZipFile(p) as z:entry['archive_entries']=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()][:20000]
            except (OSError,zipfile.BadZipFile) as exc:entry['archive_error']=str(exc)
        if p.name.lower()=='mod.info':entry['metadata']=p.read_text(encoding='utf8',errors='replace')[:12000]
        files.append(entry)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'files':files},indent=2));print(f'{len(files)} files recorded in {out}')

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True);b=sub.add_parser('build');b.add_argument('--terrain-dir',type=Path,required=True);b.add_argument('--candidates',type=Path,required=True);b.add_argument('--out',type=Path,required=True);b.add_argument('--cell0',type=int,nargs=2,required=True);i=sub.add_parser('inspect');i.add_argument('--workshop-dir',type=Path,required=True);i.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.mode=='build':build(a.terrain_dir,a.candidates,a.out,a.cell0)
    else:
        if not a.workshop_dir.is_dir():p.error('Workshop folder not found')
        inspect(a.workshop_dir,a.out)
if __name__=='__main__':main()
