# Generates eg1022n.lib : geometry-scaled model for EG-1022N plus variants
eA,eP=2.94,2.4*(2+2**.5)          # emitter (triangle, 2.4um legs)
pA,pP=852.94,103.67               # pbase (PWELL) disc
dA,dP=1098.22,117.18              # DNWELL disc
fit=dict(IS=(1.632e-19,4.545e-20,'e'),ISE=(-3.668e-18,1.667e-17,'e'),CJE=(9.684e-16,1.563e-16,'e'),IKF=(4.704e-05,4.192e-04,'e'),
         CJC=(3.216e-16,5.458e-16,'p'),ISC=(2.03e-19,2.9e-18,'p'),CJS=(2.299e-16,7.237e-16,'d'),ISS=(2.001e-18,1.002e-18,'d'))
g=dict(e=(eA,eP),p=(pA,pP),d=(dA,dP))
v={k:a*g[t][0]+b*g[t][1] for k,(a,b,t) in fit.items()}
v.update(BF=8.6,VAF=42,BR=0.07,RB=211,RBM=201,RE=15,RC=26)
STRIPE_A,STRIPE_PJ=8.32e-12,30e-6   # collector n+ drawn on top of P-base
def model(name,v):
    return f""".model {name} npn level=1 tref=25
+ is='{v['IS']:.4e}*is_cor_npn' bf='{v['BF']}*bf_cor_npn' nf=1.001 vaf={v['VAF']} ikf={v['IKF']:.4e} nkf=0.584
+ ise={v['ISE']:.4e} ne=1.48 br={v['BR']} nr=0.998 var=25.2 ikr=0.0038951 isc={v['ISC']:.4e} nc=1.284
+ rb='{v['RB']}*rb_cor_npn' irb=0.00045303 rbm='{v['RBM']}*rb_cor_npn' re='{v['RE']}*re_cor_npn' rc='{v['RC']}*rc_cor_npn'
+ cje='{v['CJE']:.4e}*cje_cor_npn' vje=0.70172 mje=0.32071 cjc='{v['CJC']:.4e}*cjc_cor_npn' vjc=0.63391 mjc=0.31113 xcjc=1
+ cjs={v['CJS']:.4e} vjs=0.35175 mjs=0.14716 subs=1 iss={v['ISS']:.4e}
+ xtb=0 xti=3 eg=1.17 tnf1=5e-5 tnr1=1e-4 tne1=4e-4 tbf1=0.0058206 tbr1=0.0009 tbf2=-6.2e-7 af=1 kf=0
"""
lib=f"""* EG-1022N geometry-scaled models (generated). Requires bjt_typical + diode_typical libs.
.subckt eg1022n c b e s
Q0 c b e s eg1022n_q
Dstripe b c diode_nd2ps_06v0 area={STRIPE_A} pj={STRIPE_PJ}
{model('eg1022n_q',v)}.ends
* As drawn: emitter n+ butted to base p+ under continuous salicide -> E-B short
.subckt eg1022n_asdrawn c b e s
Xq c b e s eg1022n
Rsil e b 5
.ends
"""
open('eg1022n.lib','w').write(lib)
import json; json.dump(v,open('params.json','w'),indent=1)
for k,x in v.items(): print(f'{k:4s} {x:.4g}')
