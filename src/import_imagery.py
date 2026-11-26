"""Import authorized north-up imagery already georeferenced in EPSG:3857."""
import argparse,json
from pathlib import Path
from PIL import Image
from imagery_registry import register,worldfile_extent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path)
    p.add_argument('--provider',required=True);p.add_argument('--date');p.add_argument('--native-gsd',type=float)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--bounds',nargs=4,type=float,metavar=('WEST','SOUTH','EAST','NORTH'));g.add_argument('--world-file',type=Path)
    p.add_argument('--usage',choices=['reference_only','analysis_reviewed'],default='reference_only')
    p.add_argument('--rights-note',default='')
    a=p.parse_args()
    with Image.open(a.image) as im:w,h=im.size
    extent=a.bounds if a.bounds else worldfile_extent(a.world_file,w,h)
    m=register(a.image,extent,a.provider,a.date,a.usage,a.rights_note,a.native_gsd)
    print(json.dumps(m,indent=2))
if __name__=='__main__':main()
