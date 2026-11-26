"""Read-only local game asset file inventory; does not extract or redistribute art."""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
EXT={'.pack','.tiles','.png','.dds','.fbx','.x','.obj','.gltf','.glb'}

def inventory(root):
    media=root/'media'
    if not media.is_dir(): raise ValueError('Expected ProjectZomboid installation root containing media/')
    for f in sorted(media.rglob('*')):
        if f.is_file() and f.suffix.lower() in EXT:
            yield [f.relative_to(root).as_posix(),f.suffix.lower(),f.stat().st_size]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'output/assets');a=p.parse_args()
    rows=list(inventory(a.game));a.out.mkdir(parents=True,exist_ok=True)
    with (a.out/'files.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['relative_path','extension','bytes']);w.writerows(rows)
    summary={'files':len(rows),'bytes':sum(r[2] for r in rows),'by_extension':dict(Counter(r[1] for r in rows)),'status':'file_inventory_only','limitations':'Pack and tile definitions are not decoded; no sprite counts, directions or missing variants inferred.'}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
