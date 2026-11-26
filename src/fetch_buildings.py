"""Download a bounded Overture building evidence snapshot, never merge into OSM."""
import argparse, hashlib, json, subprocess, sys, datetime, importlib.metadata
from pathlib import Path
from workbench_data import ROOT

CLI = "from importlib.metadata import distribution; next(e for e in distribution('overturemaps').entry_points if e.group=='console_scripts' and e.name=='overturemaps').load()()"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refresh',action='store_true')
    p.add_argument('--from-geojson',type=Path,help='Use local Overture building GeoJSON instead of download')
    a=p.parse_args()
    bbox=json.loads((ROOT/'output/stats.json').read_text())['pilot_bbox']
    out=ROOT/'data/buildings';out.mkdir(parents=True,exist_ok=True)
    dest=out/'overture.geojson';manifest=out/'manifest.json'
    if not a.refresh and not a.from_geojson and dest.exists() and manifest.exists():
        m=json.loads(manifest.read_text())
        if m.get('requested_bbox')==bbox and m.get('sha256')==hashlib.sha256(dest.read_bytes()).hexdigest():
            print('Using cached building evidence:',dest);return
    tmp=out/'download.tmp.geojson'
    try:
        if a.from_geojson:
            raw=a.from_geojson.read_bytes()
            version=None;release_hint=None;mode='local_import_extent_unverified'
        else:
            try:version=importlib.metadata.version('overturemaps')
            except importlib.metadata.PackageNotFoundError:p.error('Install optional client: py -m pip install overturemaps')
            latest=subprocess.run([sys.executable,'-c',CLI,'releases','latest'],capture_output=True,text=True)
            release_hint=latest.stdout.strip() if latest.returncode==0 else None
            cmd=[sys.executable,'-c',CLI,'download','--bbox='+','.join(map(str,bbox)),'-f','geojson','--type=building','-o',str(tmp)]
            subprocess.run(cmd,check=True)
            raw=tmp.read_bytes();mode='bounded_latest_download'
        d=json.loads(raw)
        if d.get('type')!='FeatureCollection' or not isinstance(d.get('features'),list) or not d['features']:
            raise ValueError('Expected nonempty GeoJSON FeatureCollection')
        m={'provider':'Overture Maps Foundation','theme':'buildings','license':'ODbL','attribution':'https://docs.overturemaps.org/attribution/','sha256':hashlib.sha256(raw).hexdigest(),'requested_bbox':bbox,'mode':mode,'client_version':version,'release_hint_before_download':release_hint,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'features':len(d['features']),'notes':'Latest release hint is not a pinned release. Preserve per-feature sources. Imported extent and vintage require independent verification.'}
        tmp.write_bytes(raw);tmp.replace(dest)
        temp=manifest.with_suffix('.tmp');temp.write_text(json.dumps(m,indent=2));temp.replace(manifest)
        print(json.dumps(m,indent=2))
    finally:
        if tmp.exists():tmp.unlink()

if __name__=='__main__':main()
