"""Generate KnoxMap v1 presets from the geographic index.

The preset bbox is an envelope, not an exact projected tile transform.
Do not independently compile and stitch these presets without validation.
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def make_preset(template, name, bbox):
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ValueError("Invalid WGS84 bbox")
    p = copy.deepcopy(template)
    p.update(name=name, west=w, south=s, east=e, north=n, shape=None)
    return p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sector', help='Exact sector ID from output/sectors.geojson; defaults to pilot')
    args = parser.parse_args()
    template = json.loads((ROOT/'config/knoxmap/pilot.knoxmap.json').read_text())
    if args.sector:
        features = json.loads((ROOT/'output/sectors.geojson').read_text())['features']
        feature = next((f for f in features if f['properties']['name']==args.sector), None)
        if feature is None:
            parser.error('Unknown sector ID; run build_index.py first')
        coords = feature['geometry']['coordinates'][0]
        bbox = [min(p[0] for p in coords),min(p[1] for p in coords),
                max(p[0] for p in coords),max(p[1] for p in coords)]
        name = 'CentralValley_'+args.sector
    else:
        bbox = json.loads((ROOT/'output/stats.json').read_text())['pilot_bbox']
        name = 'CentralValley_Turlock_Pilot'
    result = make_preset(template, name, bbox)
    out = ROOT/'output/presets'
    out.mkdir(parents=True,exist_ok=True)
    path = out/(name+'.knoxmap.json')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(path)

if __name__ == '__main__':
    main()
