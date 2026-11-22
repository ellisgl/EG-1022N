import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl, sys
from matplotlib.path import Path
from scipy import ndimage
G=0.05  # um grid
RS_NP, RS_PP = 6.3, 7.0
def solve(cond_rs, hot, gnd):
    """cond_rs: sheet R per pixel (nan = insulator). hot: V=1 pixels, gnd: V=0. returns resistance"""
    H,W=cond_rs.shape; ok=~np.isnan(cond_rs); idx=-np.ones((H,W),int)
    free=ok&~hot&~gnd; idx[free]=np.arange(free.sum()); n=free.sum()
    rows=[];cols=[];vals=[]; b=np.zeros(n)
    for dy,dx in [(0,1),(1,0)]:
        a=cond_rs[:H-dy,:W-dx]; c=cond_rs[dy:,dx:]
        g=2.0/(a+c); m=~np.isnan(g)
        ya,xa=np.nonzero(m); yb,xb=ya+dy,xa+dx; gg=g[m]
        for (p,q) in [((ya,xa),(yb,xb)),((yb,xb),(ya,xa))]:
            ip=idx[p]; iq=idx[q]; fp=ip>=0
            rows.append(ip[fp]); cols.append(ip[fp]); vals.append(gg[fp])
            both=fp&(iq>=0); rows.append(ip[both]); cols.append(iq[both]); vals.append(-gg[both])
            hq=fp&hot[q]; np.add.at(b,ip[hq],gg[hq])
    A=sp.csr_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(n,n))
    v=spl.spsolve(A.tocsc(),b); V=np.zeros((H,W)); V[hot]=1; V[free]=v
    # current out of hot
    I=0
    for dy,dx in [(0,1),(1,0)]:
        a=cond_rs[:H-dy,:W-dx]; c=cond_rs[dy:,dx:]; g=np.nan_to_num(2.0/(a+c))
        Va=V[:H-dy,:W-dx]; Vb=V[dy:,dx:]; ha=hot[:H-dy,:W-dx]; hb=hot[dy:,dx:]
        I+=(g*(Va-Vb)*(ha&~hb)).sum()+(g*(Vb-Va)*(hb&~ha)).sum()
    return 1/I
def base_R(L, rs_pw, gap=None, keep_ring=None):
    pw,pp,em,ct=L['pwell'],L['pplus_comp'],L['emitter'],L['contact']
    pp=pp.copy()
    if gap is not None:   # enforce gap between emitter and p+
        d=ndimage.distance_transform_edt(~em)*G
        if keep_ring: pp|=(d>gap)&(d<=gap+keep_ring)&pw
        pp&=d>gap
    rs=np.full(pw.shape,np.nan); rs[pw]=rs_pw; rs[pp]=RS_PP; rs[em]=1e-3
    return solve(rs, em, ct&pp)
def coll_R(L, rs_dn):
    dn,np_,em,ct=L['dnwell'],L['nplus_coll'],L['emitter'],L['contact']
    rs=np.full(dn.shape,np.nan); rs[dn]=rs_dn; rs[np_]=RS_NP; rs[em]=1e-3
    return solve(rs, em, ct&np_)
