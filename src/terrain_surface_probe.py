"""Independent B01 four-corner surface diagnostic; no third-party mod dependencies."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np

def analyze(packet):
    with zipfile.ZipFile(packet) as z:
        m=json.loads(z.read('report.json'));raw=z.read('shared_ground.npz')
    if hashlib.sha256(raw).hexdigest()!=m['shared_ground_sha256']:raise ValueError('Packet checksum mismatch')
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        h=z['height_m'].astype(np.float64);status=z['constraint_status'];edge=z['edge_review']
    if h.shape!=(516,516) or status.shape!=h.shape or edge.shape!=h.shape or m['height_grid_spacing_m']!=.5 or not np.isfinite(h).all():raise ValueError('Unsupported benchmark grid')
    a,b,c,d=m['metric_bounds'];A,B,C,D=m['height_grid_bounds_with_halo']
    if c-a!=256 or d-b!=256 or (A,B,C,D)!=(a-1,b-1,c+1,d+1):raise ValueError('Unaligned packet')
    n=(h[1:514:2,1:514:2]+h[2:515:2,1:514:2]+h[1:514:2,2:515:2]+h[2:515:2,2:515:2])/4
    nw,ne,sw,se=n[:-1,:-1],n[:-1,1:],n[1:,:-1],n[1:,1:]
    truth=h[2:-2,2:-2];eligible=(status[2:-2,2:-2]!=3)&~edge[2:-2,2:-2]
    surfaces={k:np.empty_like(truth) for k in ('bilinear','nw_se','ne_sw')}
    for iy,y in enumerate((.25,.75)):
        for ix,x in enumerate((.25,.75)):
            surfaces['bilinear'][iy::2,ix::2]=nw*(1-x)*(1-y)+ne*x*(1-y)+sw*(1-x)*y+se*x*y
            surfaces['nw_se'][iy::2,ix::2]=(nw*(1-x)+ne*(x-y)+se*y) if x>=y else (nw*(1-y)+sw*(y-x)+se*x)
            surfaces['ne_sw'][iy::2,ix::2]=(nw*(1-x-y)+ne*x+sw*y) if x+y<=1 else (ne*(1-y)+sw*(1-x)+se*(x+y-1))
    def stats(v):
        v=np.abs(v)
        if not v.size:return None
        return {'median_m':float(np.median(v)),'p95_m':float(np.percentile(v,95)),'p99_m':float(np.percentile(v,99)),'max_m':float(v.max()),'over_5cm':int((v>.05).sum()),'over_10cm':int((v>.1).sum())}
    report={'status':'offline_geometry_only','source_packet_sha256':hashlib.sha256(Path(packet).read_bytes()).hexdigest(),'source_height_packet_sha256':m['shared_ground_sha256'],'node_shape':list(n.shape),'core_samples':int(truth.size),'eligible_samples':int(eligible.sum()),'world_cell':m['world_cell'],'signed_height_node_range_m':[float(n.min()),float(n.max())],'errors':{k:{'all':stats(v-truth),'unblocked':stats((v-truth)[eligible])} for k,v in surfaces.items()},'limitations':'One-meter corner nodes are bilinearly resampled from experimental V3 half-meter center samples. Both triangulations tested independently; Better Terrain interpolation/units not verified. No game physics, continuous footprint or topology validation. Shared corner heights enforce equal linear edges, not engine support.'}
    return report,n

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('output/terrain_surface_probe'));a=p.parse_args();r,n=analyze(a.packet);a.out.mkdir(parents=True,exist_ok=True);np.save(a.out/'nodes_m.npy',n.astype('<f4'),allow_pickle=False);r['nodes_sha256']=hashlib.sha256((a.out/'nodes_m.npy').read_bytes()).hexdigest();(a.out/'report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
