import numpy as np, sys
from collections import defaultdict
U=0.005  # um per internal unit
rects=defaultdict(list); layer=None
for ln in open(sys.argv[1]):
    if ln.startswith('<<'): layer=ln.split()[1]
    elif ln.startswith('rect') and layer not in ('labels',):
        _,a,b,c,d=ln.split()[:5]; rects[layer].append(tuple(map(int,(a,b,c,d))))
allr=np.array([r for v in rects.values() for r in v])
x0,y0=allr[:,0].min(),allr[:,1].min(); x1,y1=allr[:,2].max(),allr[:,3].max()
print('bbox um',(x1-x0)*U,(y1-y0)*U, 'origin',x0,y0)
W,H=x1-x0,y1-y0
M={}
for k,v in rects.items():
    m=np.zeros((H,W),bool)
    for a,b,c,d in v: m[b-y0:d-y0, a-x0:c-x0]=True
    M[k]=m
np.savez_compressed('masks.npz',x0=x0,y0=y0,**M)
def ap(m):
    a=m.sum()*U*U
    p=(np.abs(np.diff(m.astype(np.int8),axis=0)).sum()+np.abs(np.diff(m.astype(np.int8),axis=1)).sum()
       +m[0].sum()+m[-1].sum()+m[:,0].sum()+m[:,-1].sum())*U
    return a,p
for k,m in M.items(): print(f'{k:14s} area {ap(m)[0]:9.2f} um2  perim(manhattan) {ap(m)[1]:8.2f} um')
pb=M['pbase']; dn=M['deepnwell']
for name,m in [('ndiff&pbase (emitter)',M['ndiff']&pb),('ndiff&~pbase',M['ndiff']&~pb),
  ('psubdiff&pbase (base tap)',M['psubdiff']&pb),('psubdiff&~dnwell (sub tap)',M['psubdiff']&~dn),
  ('psubdiff&dnwell&~pbase',M['psubdiff']&dn&~pb),('nsubdiff&dnwell',M['nsubdiff']&dn),('nsubdiff&pbase',M['nsubdiff']&pb),
  ('pbase&~dnwell',pb&~dn)]:
    print(f'{name:28s} area {ap(m)[0]:9.3f}  perim {ap(m)[1]:8.2f}')
