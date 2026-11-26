"""Cross-patch local image sampling; DWR use is a project assumption."""
import hashlib,json
from functools import lru_cache
import numpy as np
from PIL import Image
from imagery_registry import REGISTRY,list_layers
from fetch_elevation import sha
from workbench_data import ROOT

def select(source):
    if source=='naip':
        p=ROOT/'data/aerial'
        return [(json.loads((p/'manifest.json').read_text()),p/'pilot.jpg')]
    groups={}
    for m in list_layers():
        if not m.get('metadata',{}).get('source','').endswith('/San_Joaquin_Valley_2021/ImageServer'):continue
        groups.setdefault(m.get('metadata',{}).get('mosaic_group') or m['id'],[]).append(m)
    if source=='dwr':
        if not groups:raise ValueError('No DWR imagery registered; acquire a patch first')
        source=max(groups,key=lambda k:(sum(m['width']*m['height'] for m in groups[k]),k))
    if source not in groups:raise ValueError('Unknown DWR snapshot/group: '+source)
    return [(m,REGISTRY/m['id']/'original') for m in sorted(groups[source],key=lambda x:x['id'])]

class Sampler:
    def __init__(self,items):
        if not items:raise ValueError('No imagery')
        self.items=items
        for m,p in items:
            if sha(p)!=m['sha256']:raise ValueError('Image checksum mismatch: '+m['id'])
        self.sources=[{k:m.get(k) for k in ('id','sha256','extent','width','height','provider','registration','native_gsd_m','usage')} for m,p in items]
        self.digest=hashlib.sha256(json.dumps(self.sources,sort_keys=True).encode()).hexdigest()
        self.used=set()
        self.gray=lru_cache(maxsize=4)(self._load)
    def _load(self,i):
        m,p=self.items[i]
        with Image.open(p) as im:
            if im.size!=(m['width'],m['height']):raise ValueError('Image dimensions mismatch')
            return np.asarray(im.convert('L'),dtype=np.uint8)
    def sample(self,x,y):
        x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
        result=np.full(x.shape,np.nan,dtype=np.float32)
        for i,(m,p) in enumerate(self.items):
            a,b,c,d=m['extent'];w,h=m['width'],m['height']
            valid=(x>=a)&(x<c)&(y>b)&(y<=d)&np.isnan(result)
            if not valid.any():continue
            g=self.gray(i);self.used.add(m['id'])
            xx=np.clip((x[valid]-a)/(c-a)*w-.5,0,w-1)
            yy=np.clip((d-y[valid])/(d-b)*h-.5,0,h-1)
            ix=xx.astype(int);iy=yy.astype(int);fx=xx-ix;fy=yy-iy
            jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1)
            result[valid]=(1-fy)*((1-fx)*g[iy,ix]+fx*g[iy,jx])+fy*((1-fx)*g[jy,ix]+fx*g[jy,jx])
        return result if np.isfinite(result).all() else None

def rail_pair_scores(sample,cx,cy,nx,ny,offsets):
    """Approximate standard-gauge rail-head ridge hypothesis, not rail identification."""
    scores=[]
    for half in (.72,.76,.80):
        pair=[]
        for side in (-1,1):
            pos=offsets[:,None]+side*half
            center=sample(cx+nx*pos,cy+ny*pos)
            lo=sample(cx+nx*(pos-.20),cy+ny*(pos-.20))
            hi=sample(cx+nx*(pos+.20),cy+ny*(pos+.20))
            if center is None or lo is None or hi is None:break
            contrast=np.maximum(np.minimum(center-lo,center-hi),np.minimum(lo-center,hi-center))
            pair.append(np.maximum(contrast,0))
        if len(pair)==2:scores.append(np.median(np.minimum(*pair),axis=1))
    return np.max(scores,axis=0) if scores else None
