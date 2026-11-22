from calib import *
import numpy as np
names=['00p54x04p00','05p00x05p00','10p00x10p00']
stock={n:dict(np.load(f'npn_{n}.npz')) for n in names}
RB=np.array([167,71.419,65.442]); RC=np.array([14.542,12.655,10.146]); AE=np.array([2.16,25,100])
for n,L in stock.items():
    dt=ndimage.distance_transform_edt(~L['emitter'])*G; print(n,'emitter->p+ gap %.2f um'%dt[L['pplus_comp']].min())
kb=np.array([base_R(stock[n],1000)/1000 for n in names]); sf=np.array([shape_factor(stock[n]['emitter']) for n in names])
kc=np.array([coll_R(stock[n],1000)/1000 for n in names])
A=np.c_[kb,sf]; (rs_pw,rsp),*_=np.linalg.lstsq(A,RB,rcond=None)
print('BASE fit: rs_pw=%.0f ohm/sq  pinched Rsp=%.0f ohm/sq  pred'%(rs_pw,rsp),A@[rs_pw,rsp],'vs',RB)
for lab,M in [('Rv const',np.c_[np.ones(3),kc]),('Rv/Ae',np.c_[1/AE,kc])]:
    c,*_=np.linalg.lstsq(M,RC,rcond=None); print('COLL fit',lab,c,'pred',M@c,'vs',RC)
L=load_ours(); 
Lc=dict(L); Lc['nplus_coll']=L['nplus_coll']&~L['pwell']
sfo=shape_factor(L['emitter'])
np.save('fitvals.npy',[rs_pw,rsp])
gap=0.35
print('OURS base: Rbi=%.1f'%(sfo*rsp),' Rbx(as drawn, butted)=%.1f'%base_R(L,rs_pw),' Rbx(p+ pulled back %.2fum, ring kept)=%.1f'%(gap,base_R(L,rs_pw,gap=gap,keep_ring=0.3)))
c1,*_=np.linalg.lstsq(np.c_[np.ones(3),kc],RC,rcond=None); c2,*_=np.linalg.lstsq(np.c_[1/AE,kc],RC,rcond=None)
ko=coll_R(Lc,1000)/1000
print('OURS coll mesh k=%.4f -> RC(Rv const)=%.1f  RC(Rv/Ae)=%.1f'%(ko,c1[0]+c1[1]*ko,c2[0]/2.94+c2[1]*ko))
