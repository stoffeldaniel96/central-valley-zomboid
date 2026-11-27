"""Read-only local vanilla .tiles inspection; reports properties, not game art."""
import argparse, hashlib, io, json, struct
from collections import Counter
from pathlib import Path

KEYS=('SlopedSurfaceDirection','SlopedSurfaceHeightMin','SlopedSurfaceHeightMax')
FLOOR_KEYS=('solidfloor','RenderLayer','diamondFloor','FloorMaterial','FootstepMaterial','CarSlowFactor')

def parse(data):
    f=io.BytesIO(data)
    def u():
        b=f.read(4)
        if len(b)!=4:raise ValueError('truncated integer')
        return struct.unpack('<I',b)[0]
    def s():
        b=f.readline(65537)
        if not b.endswith(b'\n') or len(b)>65536:raise ValueError('invalid LF string')
        return b[:-1].rstrip(b'\r').decode('utf8')
    if f.read(4)!=b'tdef':raise ValueError('unrecognized tdef magic')
    version=u();n=u()
    if n>4096:raise ValueError('invalid tileset count')
    result={}
    for _ in range(n):
        name,image=s(),s();cols,rows,ident,total=u(),u(),u(),u()
        if not 0<cols<=4096 or not 0<rows<=4096 or total>65536:raise ValueError('invalid sheet dimensions/count')
        for i in range(total):
            k=u()
            if k>4096:raise ValueError('invalid property count')
            props={}
            for _ in range(k):
                key,value=s(),s();props[key]=value
            tile=f'{name}_{i}'
            if tile in result:raise ValueError('duplicate tile '+tile)
            result[tile]=props
    if f.read(1):raise ValueError('unexpected trailing data')
    return version,result

def inspect(root):
    media=root/'media';paths=sorted(set(media.glob('*.tiles'))|set((media/'tile_definitions').glob('*.tiles')))
    if not paths:raise ValueError('No vanilla tiledefs found; supply Project Zomboid installation root')
    paths.sort(key=lambda p:('.patch.tiles' in p.name,p.as_posix()));allprops={};sources={};files=[];issues=[]
    for p in paths:
        data=p.read_bytes();meta={'path':p.relative_to(root).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        try:
            version,tiles=parse(data);meta.update(version=version,tiles=len(tiles))
            for tile,props in tiles.items():
                if tile in allprops and '.patch.tiles' not in p.name:issues.append({'tile':tile,'reason':'duplicate base definition','file':meta['path']})
                if '.patch.tiles' in p.name and tile not in allprops:continue
                allprops.setdefault(tile,{}).update(props);sources.setdefault(tile,[]).append(meta['path'])
        except (ValueError,UnicodeError) as e:meta['error']=str(e)
        files.append(meta)
    slope=[{'tile':t,'properties':v,'sources':sources[t]} for t,v in sorted(allprops.items()) if any(k in v for k in KEYS)]
    floors={k:dict(Counter(v[k] for v in allprops.values() if k in v)) for k in FLOOR_KEYS}
    selected={t:allprops.get(t) for t in ('blends_natural_01_0','blends_natural_01_16','blends_natural_01_64','blends_street_01_32','blends_street_01_80','floors_exterior_tilesandstone_01_3')}
    return {'files':files,'issues':issues,'tiles':len(allprops),'slope_count':len(slope),'slope_property_values':{k:dict(Counter(x['properties'][k] for x in slope if k in x['properties'])) for k in KEYS},'slope_tiles':slope,'floor_property_values':floors,'control_palette':selected,'limitations':'Static tile definitions only; no art, runtime or collision inspection. Patch order lexical within base/patch groups; actual load order not verified. Parse failures reported; missing values not proof of absence.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('output/native_tile_contract.json'));a=p.parse_args();r=inspect(a.game_dir);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2));print(f"{r['tiles']} merged tiles; {r['slope_count']} slope tiles; {sum('error' in f for f in r['files'])} parse errors. Saved {a.out}")
if __name__=='__main__':main()
