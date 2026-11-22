"""Geometry -> model parameters for EG-1022N v2 (uses the stock-calibrated mesh)."""
import numpy as np, json, sys
from scipy import ndimage
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mesh import base_R, coll_R, G as GM
from calib import shape_factor
GEN='../gen/'
d=np.load(GEN+'EG1022N_V2_masks.npz'); G5=0.005; EXT=20.5; k=int(round(GM/G5))
def ds(m): n=m.shape[0]//k*k; return m[:n,:n].reshape(n//k,k,n//k,k).mean((1,3))>0.5
# contacts from the .mag
ct={'psubdiffcont':[], 'nsubdiffcont':[], 'ndiffc':[]}; lay=None
for ln in open(GEN+'EG1022N_V2.mag'):
    if ln.startswith('<<'): lay=ln.split()[1]
    elif ln.startswith('rect') and lay in ct: ct[lay].append(list(map(int,ln.split()[1:5])))
N=d['PB'].shape[0]
def cmask(name):
    m=np.zeros((N,N),bool); o=int(EXT/G5)
    for x0,y0,x1,y1 in ct[name]: m[y0+o:y1+o, x0+o:x1+o]=True
    return m
def perim(m):
    cs=plt.contour(m.astype(float),levels=[0.5]); L=0
    for seg in cs.allsegs[0]: L+=np.sum(np.hypot(*np.diff(seg,axis=0).T))
    plt.close(); return L*G5
geo=dict(eA=d['E'].sum()*G5**2, pA=d['PB'].sum()*G5**2, dA=d['DNW'].sum()*G5**2)
sl=(slice(None,None,4),)*2
geo.update(eP=perim(d['E'][sl])*4, pP=perim(d['PB'][sl])*4, dP=perim(d['DNW'][sl])*4)
print({k:round(v,2) for k,v in geo.items()})
CB=ds(cmask('psubdiffcont')); CC=ds(cmask('nsubdiffcont'))
L=dict(pwell=ds(d['PB']), pplus_comp=ds(d['PP']), emitter=ds(d['E']), contact=CB|CC|ds(cmask('ndiffc')),
       dnwell=ds(d['DNW']), nplus_coll=ds(d['NSD']))
rs_pw,rsp=np.load('fitvals.npy')
Rbx=base_R(L,rs_pw); Rbi=shape_factor(L['emitter'])*rsp
kc=coll_R(L,1000)/1000
RC=9.067+58.986*kc   # stock-calibrated (see calib2.py)
print(f'Rbx={Rbx:.1f} Rbi={Rbi:.1f} RB={Rbx+Rbi:.1f}  RC={RC:.1f}  (kc={kc:.4f})')
fit=dict(IS=(1.632e-19,4.545e-20,'e'),ISE=(-3.668e-18,1.667e-17,'e'),CJE=(9.684e-16,1.563e-16,'e'),IKF=(4.704e-05,4.192e-04,'e'),
         CJC=(3.216e-16,5.458e-16,'p'),ISC=(2.03e-19,2.9e-18,'p'),CJS=(2.299e-16,7.237e-16,'d'),ISS=(2.001e-18,1.002e-18,'d'))
g=dict(e=(geo['eA'],geo['eP']),p=(geo['pA'],geo['pP']),d=(geo['dA'],geo['dP']))
v={kk:a*g[t][0]+b*g[t][1] for kk,(a,b,t) in fit.items()}
# same emitter family as npn_00p54x16p00 -> take its BF/VAF/BR/RE
v.update(BF=8.4987,VAF=37.389,BR=0.079582,RB=round(Rbx+Rbi,1),RBM=round(Rbx,1),RE=14.121,RC=round(RC,1))
v.update(geo)
json.dump(v,open('params_v2.json','w'),indent=1)
for kk,x in v.items(): print(f'{kk:4s} {x:.4g}')
