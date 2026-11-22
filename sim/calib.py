import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
from scipy import ndimage
from mesh import *
def shape_factor(em):
    """intrinsic base: uniform injection over emitter, V=0 on emitter boundary, Rs=1. returns Rbi/Rs (power-equivalent)"""
    em=np.pad(em,1); H,W=em.shape; idx=-np.ones((H,W),int); idx[em]=np.arange(em.sum()); n=em.sum()
    A=sp.lil_matrix((n,n)); 
    ys,xs=np.nonzero(em)
    D=sp.diags([4.0]*n,0,format='lil'); rows=[];cols=[]
    for dy,dx in [(0,1),(1,0),(0,-1),(-1,0)]:
        j=idx[ys+dy,xs+dx]; m=j>=0; rows+=list(np.nonzero(m)[0]); cols+=list(j[m])
    A=sp.csr_matrix((np.full(len(rows),-1.0),(rows,cols)),shape=(n,n))+sp.identity(n)*4
    s=np.full(n,1.0/n)  # total current 1 split evenly
    V=spl.spsolve(A.tocsc(),s)
    return (s*V).sum()
def load_ours():
    d=np.load('masks.npz'); k=10  # 0.005->0.05 um
    ds=lambda m: m[:m.shape[0]//k*k,:m.shape[1]//k*k].reshape(m.shape[0]//k,k,m.shape[1]//k,k).mean((1,3))>0.5
    pb=ds(d['pbase']); 
    L=dict(pwell=pb,dnwell=ds(d['deepnwell']),emitter=ds(d['ndiff']|d['ndiffc'])&pb,
      pplus_comp=ds(d['psubdiff']|d['psubdiffcont'])&pb, contact=ds(d['psubdiffcont'])|ds(d['nsubdiffcont'])|ds(d['ndiffc']),
      nplus_coll=ds(d['nsubdiff']|d['nsubdiffcont'])&ds(d['deepnwell']))
    L['nplus_coll_offbase']=L['nplus_coll']&~pb
    return L
if __name__=='__main__':
    stock={n:dict(np.load(f'npn_{n}.npz')) for n in ['00p54x04p00','05p00x05p00','10p00x10p00']}
    RB={'00p54x04p00':167,'05p00x05p00':71.419,'10p00x10p00':65.442}; RC={'00p54x04p00':14.542,'05p00x05p00':12.655,'10p00x10p00':10.146}
    ours=load_ours()
    for n,L in list(stock.items())+[('OURS',ours)]:
        print(n,'emitter px',L['emitter'].sum(),'shape factor %.4f'%shape_factor(L['emitter']))
    # collector: R_mesh(rs_dn) for each
    for rs in [100,300,1000]:
        print('rs_dn',rs,{n:round(coll_R(L,rs),2) for n,L in stock.items()})
    for rs in [500,1000,3250]:
        print('rs_pw',rs,{n:round(base_R(L,rs),2) for n,L in stock.items()})
