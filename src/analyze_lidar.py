"""Stream classified LAS/LAZ observations into separate diagnostic height grids."""
import argparse,json,math
from pathlib import Path
from collections import Counter
import numpy as np
from pyproj import CRS,Transformer
from workbench_data import ROOT
from build_elevation import display_layer,stats
from fetch_elevation import sha

def update_max(grid,rows,cols,z):
    # np.maximum.at handles repeated returns in the same cell.
    np.maximum.at(grid,(rows,cols),z)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--las',nargs='+',type=Path)
    p.add_argument('--vertical-datum',required=True);p.add_argument('--source-crs',help='Explicit horizontal CRS override only when source CRS is missing')
    a=p.parse_args()
    import laspy
    out=ROOT/'output/elevation';m=json.loads((out/'ground.json').read_text())
    if a.vertical_datum!=m['vertical_datum']:p.error('Vertical datum must match verified DEM datum; no vertical conversion performed')
    if sha(out/'ground.npy')!=m['ground_sha256']:raise ValueError('Ground grid checksum mismatch')
    ground=np.load(out/'ground.npy',allow_pickle=False);h,w=ground.shape
    x0,y0,x1,y1=m['bounds_east_north_m'];res=m['resolution_m'];crs=CRS.from_wkt(m['crs_wkt'])
    paths=a.las or sorted((ROOT/'data/elevation/lidar').glob('*.laz'))+sorted((ROOT/'data/elevation/lidar').glob('*.las'))
    if not paths:p.error('No LAS/LAZ files; download or specify --las')
    # Absolute heights, class-specific maxima. Negative infinity means no return.
    grids={k:np.full(ground.shape,-np.inf,dtype=np.float32) for k in ('surface','building','vegetation','bridge')}
    counts=Counter();sources=[];returns=0
    for path in paths:
        with laspy.open(path) as reader:
            source_crs=reader.header.parse_crs()
            if source_crs is None:
                if not a.source_crs:raise ValueError('Missing CRS: '+str(path))
                source_crs=CRS.from_user_input(a.source_crs)
            # Transform horizontal coordinates only. Z values remain original meters.
            if source_crs.is_compound:source_crs=source_crs.sub_crs_list[0]
            trans=Transformer.from_crs(source_crs,crs,always_xy=True)
            for pts in reader.chunk_iterator(500_000):
                x,y=trans.transform(np.asarray(pts.x),np.asarray(pts.y));z=np.asarray(pts.z)
                cl=np.asarray(pts.classification);valid=np.isfinite(x)&np.isfinite(y)&np.isfinite(z)&(x>=x0)&(x<x1)&(y>y0)&(y<=y1)
                valid&=~np.asarray(pts.withheld,dtype=bool)
                x,y,z,cl=x[valid],y[valid],z[valid],cl[valid]
                cols=np.floor((x-x0)/res).astype(int);rows=np.floor((y1-y)/res).astype(int)
                good=(cols>=0)&(cols<w)&(rows>=0)&(rows<h)
                rows,cols,z,cl=rows[good],cols[good],z[good],cl[good]
                counts.update(map(int,cl));returns+=len(cl)
                masks={'surface':np.isin(cl,[1,2,3,4,5,6,9,17]),'building':cl==6,'vegetation':np.isin(cl,[3,4,5]),'bridge':cl==17}
                for k,mask in masks.items():update_max(grids[k],rows[mask],cols[mask],z[mask])
            sources.append({'file':path.name,'sha256':sha(path),'horizontal_crs':str(source_crs),'point_count':reader.header.point_count})
    report={'source_files':sources,'vertical_datum':a.vertical_datum,'ground_sha256':m['ground_sha256'],'returns_in_pilot':returns,'classification_counts':dict(counts),'resolution_m':res,'layers':{},'notes':'Sparse maximum return per grid cell minus DEM. No interpolation. Unclassified returns may include buildings/trees; class 6/17 may be absent or incomplete. Not reconstructed roofs or bridge decks.'}
    for k,g in grids.items():
        g[~np.isfinite(g)]=np.nan
        height=g-ground;np.save(out/(k+'_above_ground.npy'),height,allow_pickle=False)
        s=stats(height);entry={'stats':s}
        if s['valid_fraction']:
            entry['display_layer_id']=display_layer(height,crs,[x0,y0,x1,y1],res,'LiDAR '+k+' above ground',{'stats':s,'vertical_datum':a.vertical_datum,'ground_sha256':m['ground_sha256']})['id']
        report['layers'][k]=entry
    (out/'lidar.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
