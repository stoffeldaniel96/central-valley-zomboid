"""Measure local relief relative to a broad terrain trend; diagnostic only."""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def decompose(z,spacing,sigma):
    if z.ndim!=2 or min(z.shape)<3 or not all(math.isfinite(x) and x>0 for x in (spacing,sigma)):raise ValueError('Invalid grid or scale')
    valid=np.isfinite(z)
    if not valid.any():raise ValueError('No elevation observations')
    if valid.all():
        trend=gaussian_filter(z.astype(np.float32,copy=False),sigma/spacing,mode='reflect')
    else:
        weight=gaussian_filter(valid.astype(np.float32),sigma/spacing,mode='reflect')
        total=gaussian_filter(np.where(valid,z,0).astype(np.float32),sigma/spacing,mode='reflect')
        trend=np.divide(total,weight,out=np.full_like(total,np.nan),where=weight>=.95)
    trend=np.where(valid,trend,np.nan)
    return trend,z-trend

def stats(a):
    v=a[np.isfinite(a)]
    if not v.size:return None
    return {'min':float(v.min()),'max':float(v.max()),'median':float(np.median(v)),'p95':float(np.percentile(v,95))}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ground-dir',type=Path,default=ROOT/'output/elevation');p.add_argument('--sigma-m',type=float,default=50);p.add_argument('--out',type=Path,default=ROOT/'output/terrain_relief');a=p.parse_args()
    m=json.loads((a.ground_dir/'ground.json').read_text());path=a.ground_dir/'ground.npy'
    if m.get('vertical_units')!='m' or sha(path)!=m['ground_sha256']:p.error('Ground checksum or units invalid')
    z=np.load(path,allow_pickle=False)
    if list(z.shape)!=m['shape']:p.error('Ground shape mismatch')
    res=m['resolution_m'];trend,relief=decompose(z,res,a.sigma_m)
    gy,gx=np.gradient(trend,res);grade=np.hypot(gx,gy)*100
    valid=np.isfinite(relief);v=np.abs(relief[valid])
    if not v.size:p.error('No supported local relief samples')
    a.out.mkdir(parents=True,exist_ok=True)
    np.save(a.out/'trend.npy',trend,allow_pickle=False);np.save(a.out/'relief.npy',relief,allow_pickle=False)
    report={'source_ground_sha256':m['ground_sha256'],'crs_wkt':m['crs_wkt'],'bounds_east_north_m':m['bounds_east_north_m'],'resolution_m':res,'shape':m['shape'],'source_vertical_datum':m['vertical_datum'],'sigma_m':a.sigma_m,'filter':'Gaussian reflect, truncate=4; normalized weights for incomplete grid, >=95% support, no fill of missing cells','edge_warning_m':4*a.sigma_m,'valid_fraction':float(valid.mean()),'observed_elevation_m':stats(z),'trend_elevation_m':stats(trend),'trend_grade_percent':stats(grade),'local_relief_m':stats(relief),'absolute_relief_exceeds_fraction':{str(t):float((v>t).mean()) for t in (.1,.15,.25,.5,1,2)},'trend_sha256':sha(a.out/'trend.npy'),'relief_sha256':sha(a.out/'relief.npy'),'status':'diagnostic_not_approved_sanitized_terrain','limitations':'Trend may absorb real hills and embankments or create adjacent false depressions; boundary reflection is provisional. No semantic protection, water flow, deck clearance, or cross-region continuity enforced. Never use this output as a final world height field. Original DEM unchanged.'}
    (a.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in report.items() if k!='crs_wkt'},indent=2,allow_nan=False))
if __name__=='__main__':main()
