import numpy as np
from scipy import ndimage
d=np.load('masks.npz'); U=0.005; x0,y0=int(d['x0']),int(d['y0'])
def comps(m,name):
    lab,n=ndimage.label(m)
    print(name,'components',n)
    for i,sl in enumerate(ndimage.find_objects(lab)):
        sub=(lab[sl]==i+1); a=sub.sum()*U*U
        if a<0.05: continue
        # Crofton perimeter estimate: mean over directions of projected width * pi
        ys,xs=np.nonzero(sub); 
        print(f'  #{i} area {a:8.3f} bbox x[{(sl[1].start+x0)*U:.2f},{(sl[1].stop+x0)*U:.2f}] y[{(sl[0].start+y0)*U:.2f},{(sl[0].stop+y0)*U:.2f}]')
    return lab,n
for k in ['ndiff','ndiffc','nsubdiffcont','psubdiffcont','pbase','deepnwell','nsubdiff']:
    comps(d[k],k)
