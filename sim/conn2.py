import numpy as np
from scipy import ndimage
d=np.load('masks.npz'); U=0.005; x0,y0=int(d['x0']),int(d['y0'])
cond=d['metal1']|d['nsubdiffcont']|d['psubdiffcont']|d['ndiffc']
m1,n=ndimage.label(cond)
def at(x,y): return int(m1[int(round(y/U))-y0,int(round(x/U))-x0])
print('nets',n,'labels: c',at(10.95,13.55),'e',at(9.7,-10.65),'b',at(-8,0),'s',at(19.5,0))
for k in ['nsubdiffcont','psubdiffcont','ndiffc']:
    lab,nn=ndimage.label(d[k]); cm=ndimage.center_of_mass(d[k],lab,range(1,nn+1))
    print(k,sorted(set(at((c[1]+x0)*U,(c[0]+y0)*U) for c in cm)))
for i in range(1,n+1):
    ys,xs=np.nonzero(m1==i); print('net',i,'area %.1f'%(len(ys)*U*U),'bbox x %.1f..%.1f y %.1f..%.1f'%((xs.min()+x0)*U,(xs.max()+x0)*U,(ys.min()+y0)*U,(ys.max()+y0)*U))
