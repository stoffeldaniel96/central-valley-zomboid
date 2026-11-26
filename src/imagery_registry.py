"""Immutable, local imagery snapshots with a display tile pyramid.
No remote acquisition or automatic rights determination.
"""
import hashlib,json,math,re,shutil,tempfile
from pathlib import Path
from PIL import Image
from workbench_data import ROOT

REGISTRY=ROOT/'data/imagery'
ID=re.compile(r'[0-9a-f]{24}')
TILE=512

def validate_extent(extent):
    if len(extent)!=4 or not all(math.isfinite(v) for v in extent):raise ValueError('Invalid extent')
    x,y,u,v=extent
    if not -20037509<=x<u<=20037509 or not -20048967<=y<v<=20048967:raise ValueError('Expected valid EPSG:3857 bounds')
    return list(extent)

def worldfile_extent(path,width,height):
    a,d,b,e,c,f=map(float,path.read_text().split())
    if b!=0 or d!=0 or a<=0 or e>=0:raise ValueError('Only north-up world files in EPSG:3857 supported')
    return validate_extent([c-a/2,f+e*(height-.5),c+a*(width-.5),f-e/2])

def register(path,extent,provider,observed_at=None,usage='reference_only',rights_note='',native_gsd=None,registry=REGISTRY,metadata=None):
    extent=validate_extent(extent)
    if usage not in ('reference_only','analysis_reviewed'):raise ValueError('Invalid usage')
    if not provider.strip():raise ValueError('Provider required')
    if usage=='analysis_reviewed' and not rights_note.strip():raise ValueError('Record actual analysis permission and provenance')
    if native_gsd is not None and (not math.isfinite(native_gsd) or native_gsd<=0):raise ValueError('Invalid native resolution')
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    with Image.open(path) as source:
        if source.format not in ('PNG','JPEG','TIFF'):raise ValueError('Expected PNG, JPEG or TIFF')
        w,h=source.size
        if w*h>64_000_000:raise ValueError('Split imagery into smaller georeferenced patches (64M pixel cap)')
        if source.getexif().get(274,1)!=1:raise ValueError('Normalize EXIF orientation before importing')
        image=source.convert('RGB')
    info={'sha256':digest,'provider':provider,'observed_at':observed_at,'usage':usage,'rights_note':rights_note,'native_gsd_m':native_gsd,'registration':'unverified','extent':extent,'crs':'EPSG:3857','width':w,'height':h,'metadata':metadata or {}}
    id=hashlib.sha256(json.dumps(info,sort_keys=True,allow_nan=False).encode()).hexdigest()[:24]
    registry.mkdir(parents=True,exist_ok=True);dest=registry/id
    if dest.exists():return json.loads((dest/'manifest.json').read_text())
    temp=Path(tempfile.mkdtemp(prefix='import-',dir=registry))
    try:
        (temp/'original').write_bytes(raw)
        # Full-resolution normalized image is for explicitly reviewed local analysis only.
        if usage=='analysis_reviewed':image.save(temp/'analysis.png')
        levels=[];level=0
        while True:
            lw,lh=image.size
            cols=math.ceil(lw/TILE);rows=math.ceil(lh/TILE)
            for y in range(rows):
                for x in range(cols):
                    tile=image.crop((x*TILE,y*TILE,min(lw,(x+1)*TILE),min(lh,(y+1)*TILE)))
                    tile.save(temp/f'{level}-{x}-{y}.png')
            levels.append({'level':level,'width':lw,'height':lh,'cols':cols,'rows':rows})
            if max(lw,lh)<=TILE:break
            image=image.resize((math.ceil(lw/2),math.ceil(lh/2)),Image.Resampling.LANCZOS);level+=1
        info.update(id=id,tile_size=TILE,levels=levels)
        (temp/'manifest.json').write_text(json.dumps(info,indent=2,allow_nan=False))
        temp.rename(dest)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return info

def list_layers(registry=REGISTRY):
    result=[]
    if not registry.exists():return result
    for folder in sorted(registry.iterdir()):
        if not ID.fullmatch(folder.name):continue
        try:
            m=json.loads((folder/'manifest.json').read_text())
            if m['id']!=folder.name:continue
            validate_extent(m['extent']);result.append(m)
        except (OSError,ValueError,KeyError):continue
    return result

def tile_path(id,level,x,y,registry=REGISTRY):
    if not ID.fullmatch(id) or min(level,x,y)<0:return None
    folder=registry/id
    try:
        m=json.loads((folder/'manifest.json').read_text())
        l=next(l for l in m['levels'] if l['level']==level)
        if x>=l['cols'] or y>=l['rows']:return None
    except (OSError,ValueError,KeyError,StopIteration):return None
    p=folder/f'{level}-{x}-{y}.png'
    return p if p.is_file() else None
