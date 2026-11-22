import gdstk, numpy as np, os
PDK = os.environ.get('PDK_ROOT', os.path.expanduser('~/pdk'))
from matplotlib.path import Path
from mesh import G
def raster(polys,x0,y0,W,H):
    m=np.zeros((H,W),bool); yy,xx=np.mgrid[0:H,0:W]; pts=np.c_[(xx.ravel()+.5)*G+x0,(yy.ravel()+.5)*G+y0]
    for p in polys: m|=Path(p.points).contains_points(pts).reshape(H,W)
    return m
def stock(name):
    lib=gdstk.read_gds(f'{PDK}/gf180mcuC/libs.ref/gf180mcu_fd_pr/gds/{name}.gds'); c=lib.top_level()[0]
    P=lambda l:gdstk.boolean([p for p in c.get_polygons() if (p.layer,p.datatype)==(l,0)],[],'or')
    (x0,y0),(x1,y1)=c.bounding_box(); W=int((x1-x0)/G)+1; H=int((y1-y0)/G)+1
    r={k:raster(P(l),x0,y0,W,H) for k,l in dict(dnwell=12,pwell=204,comp=22,nplus=32,pplus=31,contact=33).items()}
    L=dict(dnwell=r['dnwell'],pwell=r['pwell'],contact=r['contact'])
    L['emitter']=r['comp']&r['nplus']&r['pwell']; L['pplus_comp']=r['comp']&r['pplus']&r['pwell']
    L['nplus_coll']=r['comp']&r['nplus']&r['dnwell']&~r['pwell']
    return L
if __name__=='__main__':
    for n in ['npn_00p54x04p00','npn_05p00x05p00','npn_10p00x10p00']:
        np.savez_compressed(n+'.npz',**stock(n)); print('saved',n)
