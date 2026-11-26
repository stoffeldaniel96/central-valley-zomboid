import json,csv,math
from pathlib import Path
from pyproj import Transformer,CRS
R=Path(__file__).resolve().parents[1]; O=R/'output'; O.mkdir(exist_ok=True)
c=json.loads((R/'world.json').read_text()); t=Transformer.from_crs(4326,CRS.from_proj4(c['projection']),always_xy=True); inv=Transformer.from_crs(CRS.from_proj4(c['projection']),4326,always_xy=True)
w,s,e,n=c['requested_bbox']; pts=[t.transform(w+(e-w)*i/100,s+(n-s)*j/100) for i in range(101) for j in (0,100)]+[t.transform(x,s+(n-s)*i/100) for i in range(101) for x in (w,e)]
C=c['cell_tiles']; xmin=math.floor(min(x for x,y in pts)/C); xmax=math.ceil(max(x for x,y in pts)/C); ymin=math.floor(-max(y for x,y in pts)/C); ymax=math.ceil(-min(y for x,y in pts)/C)
def feature(name,a,b,d,f):
    coords=[inv.transform(x*C,-y*C) for x,y in [(a,b),(d,b),(d,f),(a,f),(a,b)]]
    return {'type':'Feature','properties':{'name':name,'cells':[a,b,d,f]},'geometry':{'type':'Polygon','coordinates':[coords]}}
x,y=t.transform(-120.8466,37.4947); px=math.floor(x/C)-4; py=math.floor(-y/C)-4
pilot=feature('Downtown Turlock',px,py,px+8,py+8); world=feature('Central Valley',xmin,ymin,xmax,ymax)
rows=[]; features=[]
for j in range(ymin//16,(ymax-1)//16+1):
 for i in range(xmin//16,(xmax-1)//16+1):
  a,b,d,f=max(i*16,xmin),max(j*16,ymin),min((i+1)*16,xmax),min((j+1)*16,ymax)
  name=f'S_{i}_{j}'; rows.append(dict(id=name,x0=a,y0=b,x1=d,y1=f)); features.append(feature(name,a,b,d,f))
for name,fs in [('bounds',[world,pilot]),('sectors',features)]: (O/f'{name}.geojson').write_text(json.dumps({'type':'FeatureCollection','features':fs},indent=2))
with (O/'sectors.csv').open('w',newline='') as h:
 wr=csv.DictWriter(h,fieldnames=rows[0]);wr.writeheader();wr.writerows(rows)
coords=pilot['geometry']['coordinates'][0]; bbox=[min(p[0] for p in coords),min(p[1] for p in coords),max(p[0] for p in coords),max(p[1] for p in coords)]
stats=dict(global_cells=[xmin,ymin,xmax,ymax],dimensions_cells=[xmax-xmin,ymax-ymin],dimensions_m=[(xmax-xmin)*C,(ymax-ymin)*C],area_km2=(xmax-xmin)*(ymax-ymin)*C*C/1e6,sectors=len(rows),pilot_cells=[px,py,px+8,py+8],pilot_bbox=bbox,game_offset_cells=[-xmin,-ymin]);(O/'stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
w,s,e,n=bbox; pad=.003
(O/'pilot.overpass').write_text(f'[out:xml][timeout:180];\n(way({s-pad},{w-pad},{n+pad},{e+pad});relation["type"="multipolygon"]({s-pad},{w-pad},{n+pad},{e+pad}););\n(._;>>;);out meta;\n')
