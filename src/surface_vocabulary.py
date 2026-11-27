"""Measure reusable material-mask demand from actual ground_lab samples.
Not a sprite generator. Unknown and conflicting observations are not materials.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def analyze(samples,names,min_uses=10,max_changes=8):
    if samples.ndim!=3 or samples.shape[0]!=64:raise ValueError('Requires 8x8 (12.5cm) samples from ground_lab')
    if not np.isin(samples,np.arange(-1,len(names)+1)).all():raise ValueError('Unknown material IDs')
    sub=samples.transpose(1,2,0).reshape(*samples.shape[1:],8,8)
    valid=~np.any(sub<0,axis=(2,3));masks=[];summary={}
    for i,name in enumerate(names,1):
        mask=sub==i;ct=mask.sum(axis=(2,3));sel=(ct>0)&(ct<64)&valid
        masks.append(mask[sel])
        summary[name]={'full_tiles':int(((ct==64)&valid).sum()),'partial_placements':int(sel.sum()),'partial_with_unknown':int((sel&np.any(sub==0,axis=(2,3))).sum())}
    masks=np.concatenate(masks,axis=0) if masks else np.empty((0,8,8),bool)
    report={'classes':summary,'excluded_conflict_tiles':int((~valid).sum()),'mask_placements':len(masks),'min_uses':min_uses,'max_changed_samples':max_changes}
    if not len(masks):return {**report,'exact_oriented_masks':0,'notes':'No eligible partial masks'}
    unique,inv,counts=np.unique(masks.reshape(-1,64),axis=0,return_inverse=True,return_counts=True)
    rot=np.stack([np.rot90(masks,k,axes=(1,2)).reshape(-1,64) for k in range(4)],axis=1)
    packed=np.packbits(rot,axis=2).view('>u8').reshape(len(masks),4)
    _,rc=np.unique(packed.min(axis=1),return_counts=True)
    edge=np.zeros((8,8),bool);edge[[0,-1],:]=True;edge[:,[0,-1]]=True;edge=edge.ravel()
    freq=np.flatnonzero(counts>=min_uses);rare=np.flatnonzero(counts<min_uses)
    unresolved=np.zeros(len(counts),bool);dist=np.zeros(len(counts),int)
    # Match only within identical outer-sample signatures. Deterministic nearest frequent pattern.
    groups={}
    for i in freq:groups.setdefault(unique[i,edge].tobytes(),[]).append(i)
    for j in rare:
        candidates=groups.get(unique[j,edge].tobytes(),[])
        if candidates:
            dd=np.count_nonzero(unique[candidates]!=unique[j],axis=1);k=int(np.argmin(dd))
            if dd[k]<=max_changes:dist[j]=dd[k];continue
        unresolved[j]=True
    un=unresolved[inv];changed=dist[inv]
    report.update(exact_oriented_masks=len(counts),exact_oriented_masks_under_threshold=int((counts<min_uses).sum()),frequent_oriented_masks=len(freq),exact_frequent_placements=int(counts[freq].sum()),rotation_canonical_families=len(rc),rotation_families_under_threshold=int((rc<min_uses).sum()),rotation_placements_in_frequent_families=int(rc[rc>=min_uses].sum()),approximated_placements=int((changed>0).sum()),unresolved_placements=int(un.sum()),unresolved_unique_masks=int(unresolved.sum()),changed_sample_count=int(changed.sum()),changed_mask_area_m2=float(changed.sum()/64),max_changed_mask_area_per_placement_m2=float(changed.max()/64),edge_samples_changed=0)
    report['notes']='Binary material coverage masks only, not sprite counts. Rotation grouping is geometry only. Unknown=unobserved, conflict-containing tiles excluded. Mask error sums may double-count changes in overlapping materials. Substitution is diagnostic only: does not enforce disjoint material coverage, known/unknown boundaries, topology or continuous seams. No compiled geometry changed.'
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ground-dir',type=Path,required=True);p.add_argument('--min-uses',type=int,default=10);p.add_argument('--max-changes',type=int,default=8);a=p.parse_args()
    if a.min_uses<1 or not 0<=a.max_changes<=64:p.error('Invalid reuse thresholds')
    m=json.loads((a.ground_dir/'report.json').read_text());path=a.ground_dir/'materials.npz'
    if not path.exists():path=a.ground_dir/'ground.npz'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=m.get('materials_sha256',m.get('ground_npz_sha256')):p.error('Ground sample checksum mismatch')
    with np.load(path,allow_pickle=False) as z:report=analyze(z['material_subsamples'],m['material_audit']['classes'],a.min_uses,a.max_changes)
    report.update(sample_sha256=digest,candidate_sha256=m['material_audit']['candidate_sha256'],bounds_east_north_m=m['bounds_east_north_m'])
    out=a.ground_dir/'vocabulary.json';out.write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
