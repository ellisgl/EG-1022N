import numpy as np
from scipy import ndimage
d=np.load('masks.npz'); U=0.005
def touch(a,b):
    a=d[a];b=d[b]; L=0
    L+=(a[:-1]&b[1:]).sum()+(b[:-1]&a[1:]).sum()+(a[:,:-1]&b[:,1:]).sum()+(b[:,:-1]&a[:,1:]).sum()
    return L*U
def gap(a,b):
    dt=ndimage.distance_transform_edt(~d[b])*U; return dt[d[a]].min()
for a,b in [('ndiff','psubdiff'),('nsubdiff','psubdiff'),('ndiff','nsubdiff')]:
    print(f'{a}-{b}: butted edge length {touch(a,b):.2f} um, min spacing {gap(a,b):.3f} um')
