from pathlib import Path
import urllib.request,urllib.parse,hashlib,json,datetime,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]; q=(R/'output/pilot.overpass').read_text(); dest=R/'data/pilot.osm'
dest.parent.mkdir(exist_ok=True)
req=urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'CentralValleyMapPrototype/0.1'})
with urllib.request.urlopen(req,timeout=240) as response: raw=response.read()
root=ET.fromstring(raw)
if root.tag!='osm' or root.find('remark') is not None or not root.findall('way'): raise ValueError('Incomplete OSM response')
dest.write_bytes(raw); (R/'data/pilot.source.json').write_text(json.dumps({'source':req.full_url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'ways':len(root.findall('way')),'license':'ODbL'},indent=2));print(dest)
