import numpy as np
# name: (emitterA, emitterP, pwellA, pwellP, dnwA, dnwP), params
D={
'10x10':((100,40,139.2,47.2,282.2,67.2),dict(IS=1.8108e-17,ISE=2.9626e-16,CJE=1.031e-13,CJC=7.053e-14,CJS=1.135e-13,ISC=1.5816e-16,ISS=6.32e-16,BF=10.83,IKF=0.021028,RB=65.442,RE=6.9007,RC=10.146,VAF=95.696,BR=.258)),
'5x5':((25,20,46.2,27.2,139.2,47.2),dict(IS=5.1456e-18,ISE=2.5923e-16,CJE=2.733e-14,CJC=2.972e-14,CJS=6.618e-14,ISC=1.2536e-16,ISS=3.26e-16,BF=10.05,IKF=.01158,RB=71.419,RE=12.809,RC=12.655,VAF=77.8,BR=.166)),
'0.54x16':((8.64,33.08,41.7,40.3,167.4,60.3),dict(IS=2.8872e-18,ISE=5.2003e-16,CJE=1.354e-14,CJC=3.540e-14,CJS=8.211e-14,ISC=1.0425e-16,ISS=3.95e-16,BF=8.4987,IKF=.013121,RB=137.43,RE=14.121,RC=12.9,VAF=37.4,BR=.0796)),
'0.54x8':((4.32,17.08,22.9,24.3,108.6,44.3),dict(IS=1.4309e-18,ISE=2.6232e-16,CJE=6.857e-15,CJC=2.064e-14,CJS=5.703e-14,ISC=7.3712e-17,ISS=2.62e-16,BF=8.4,IKF=.0077487,RB=141.94,RE=14.573,RC=13.434,VAF=37.4,BR=.070)),
'0.54x4':((2.16,9.08,13.6,16.3,79.3,36.3),dict(IS=7.6696e-19,ISE=1.3419e-16,CJE=3.513e-15,CJC=1.326e-14,CJS=4.449e-14,ISC=6.2655e-17,ISS=1.95e-16,BF=8.39,IKF=.0048817,RB=167,RE=17.058,RC=14.542,VAF=37.4,BR=.0578)),
}
names=list(D)
def fit(par,ia,ip,log=False):
    A=np.array([[D[n][0][ia],D[n][0][ip]] for n in names]); y=np.array([D[n][1][par] for n in names])
    c,*_=np.linalg.lstsq(A,y,rcond=None); pred=A@c
    print(f'{par:4s} per-area {c[0]:.4g}  per-perim {c[1]:.4g}   max rel err {np.max(np.abs(pred/y-1))*100:.0f}%')
    return c
# our device
ours=dict(eA=2.538,eP=2.4*(2+2**.5),pA=852.94,pP=2*np.pi*16.5,dA=1098.22,dP=2*np.pi*18.65)
print('ours',ours)
r={}
for p,ia,ip in [('IS',0,1),('ISE',0,1),('CJE',0,1),('IKF',0,1),('CJC',2,3),('ISC',2,3),('CJS',4,5),('ISS',4,5)]:
    c=fit(p,ia,ip); key={0:('eA','eP'),2:('pA','pP'),4:('dA','dP')}[ia]
    r[p]=c[0]*ours[key[0]]+c[1]*ours[key[1]]
for k,v in r.items(): print(f'{k} = {v:.4g}   (0.54x4 stock: {D["0.54x4"][1][k]:.4g})')
