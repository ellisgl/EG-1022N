import numpy as np, json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
P=json.load(open('params.json'))
DEVS=['v2','stock_0p54x16','eg1022n','stock_0p54x4']
LAB={'v2':'EG-1022N v2 (strokes layout)','stock_0p54x16':'stock npn_00p54x16p00 (LVS model)','eg1022n':'v1 disc, gap fixed','stock_0p54x4':'stock npn_00p54x04p00','stock_10x10':'stock npn_10p00x10p00 (what Magic tagged)','asdrawn':'EG-1022N as drawn (E–B silicide short)'}
COL={'v2':'#1b9e5a','stock_0p54x16':'#8e44ad','eg1022n':'#2a6fdb','stock_0p54x4':'#e07b00','stock_10x10':'#6a6a6a','asdrawn':'#c0392b'}
def g(d,T=27):
    a=np.loadtxt(f'out/gummel_{d}_{T}.dat'); return a[:,0],a[:,1],a[:,3]
M={}
fig,ax=plt.subplots(1,2,figsize=(12,4.5))
for d in DEVS:
    vb,ic,ib=g(d)
    ax[0].semilogy(vb,np.abs(ic),color=COL[d],label=LAB[d]+' Ic'); ax[0].semilogy(vb,np.abs(ib),'--',color=COL[d])
    if d=='asdrawn': continue
    beta=ic/ib; m=(ic>1e-10)
    ax[1].semilogx(ic[m],beta[m],color=COL[d],label=LAB[d])
    k=np.argmax(beta*m)
    vbe=lambda I: float(np.interp(np.log(I),np.log(ic),vb))
    M[d]=dict(beta_peak=float(beta[k]),ic_at_peak=float(ic[k]),vbe_1u=vbe(1e-6),vbe_10u=vbe(1e-5),vbe_100u=vbe(1e-4),
              beta_1u=float(np.interp(np.log(1e-6),np.log(ic),beta)),beta_100u=float(np.interp(np.log(1e-4),np.log(ic),beta)),beta_1m=float(np.interp(np.log(1e-3),np.log(ic),beta)))
M['asdrawn']={}
ax[0].set_ylim(1e-13,1); ax[0].set_xlabel('V_BE (V)'); ax[0].set_ylabel('|I| (A)  solid=Ic, dashed=Ib'); ax[0].set_title('Gummel plot, V_CE = 2 V, 27 °C'); ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
ax[1].set_xlim(1e-9,1e-2); ax[1].set_ylim(0,12); ax[1].set_xlabel('I_C (A)'); ax[1].set_ylabel('β = Ic/Ib'); ax[1].set_title('Current gain'); ax[1].legend(fontsize=7); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig('gummel_beta.png',dpi=110); plt.close()
# temperature
for d in ['v2','stock_0p54x16','eg1022n','stock_0p54x4']:
    V={}
    for T in [-40,27,125]:
        vb,ic,ib=g(d,T); V[T]=float(np.interp(np.log(1e-5),np.log(ic),vb)); M[d][f'beta_10uA_{T}C']=float(np.interp(np.log(1e-5),np.log(ic),ic/ib))
    M[d]['dVbe_dT_10uA_mV_per_K']=(V[125]-V[-40])/165*1e3
# output curves + Early
fig,ax=plt.subplots(1,2,figsize=(12,4.5))
IBO=[2e-7,5e-7,1e-6,2e-6,5e-6,1e-5]
for j,d in enumerate(['v2','asdrawn']):
    for k,ibv in enumerate(IBO):
        a=np.loadtxt(f'out/out_{d}_{k}.dat'); ax[j].plot(a[:,0],a[:,1]*1e6,color=COL[d],alpha=.4+.1*k)
        ax[j].text(6.05,a[-1,1]*1e6,f'{ibv*1e6:g} µA',fontsize=7,va='center')
    ax[j].set_title(LAB[d]); ax[j].set_xlabel('V_CE (V)'); ax[j].set_ylabel('I_C (µA)'); ax[j].grid(alpha=.3); ax[j].set_xlim(0,6.8)
for d in DEVS:
    a=np.loadtxt(f'out/out_{d}_2.dat'); v,i=a[:,0],a[:,1]; s=(v>=2)&(v<=4); p=np.polyfit(v[s],i[s],1)
    M[d]['VA_early_at_Ib1u']=float(p[1]/p[0]); M[d]['Ic_Ib1u_Vce2']=float(np.interp(2,v,i))
    M[d]['Vce_sat_10pct']=float(v[np.argmax(i>0.9*np.interp(2,v,i))])
a=np.loadtxt('out/out_asdrawn_5.dat'); M['asdrawn']['Ic_at_Ib10u_Vce3']=float(np.interp(3,a[:,0],a[:,1]))
plt.tight_layout(); plt.savefig('output.png',dpi=110); plt.close()
# fT
ft=json.load(open('out/ft.json'))
fig,ax=plt.subplots(figsize=(7,4.5))
TF=100e-12
for d in DEVS:
    r=[x for x in ft if x['dev']==d and x['ft']]; ic=np.array([x['ic'] for x in r]); f=np.array([x['ft'] for x in r])
    ax.loglog(ic,f,color=COL[d],label=LAB[d]+' (PDK model, τF=0)')
    f2=1/(1/f+2*np.pi*TF); ax.loglog(ic,f2,':',color=COL[d])
    M[d]['ft_capOnly_at_10uA']=float(np.exp(np.interp(np.log(1e-5),np.log(ic),np.log(f))))
    M[d]['ft_capOnly_at_100uA']=float(np.exp(np.interp(np.log(1e-4),np.log(ic),np.log(f))))
    M[d]['ft_tf100p_at_100uA']=1/(1/M[d]['ft_capOnly_at_100uA']+2*np.pi*TF)
ax.set_xlabel('I_C (A)'); ax.set_ylabel('f_T (Hz)'); ax.set_title('Transition frequency, V_CE = 2 V  (dotted: assumed τF = 100 ps)'); ax.legend(fontsize=7); ax.grid(alpha=.3,which='both')
plt.tight_layout(); plt.savefig('ft.png',dpi=110); plt.close()
# junction caps (analytic from model)
cj=lambda c0,vj,m,vr: c0/(1+vr/vj)**m
P2=json.load(open('params_v2.json'))
stock={'v2':dict(CJE=P2['CJE'],CJC=P2['CJC'],CJS=P2['CJS'],RB=P2['RB']),'stock_0p54x16':dict(CJE=1.354e-14,CJC=3.540e-14,CJS=8.211e-14,RB=137.43),'stock_0p54x4':dict(CJE=3.513e-15,CJC=1.326e-14,CJS=4.449e-14,RB=167)}
ours=dict(CJE=P['CJE'],CJC=P['CJC']+8.32e-12*0.00095+30e-6*1.33e-10,CJS=P['CJS'],RB=P['RB'])
for d,c in [('eg1022n',ours)]+list(stock.items()):
    M[d].update(Cje0_fF=c['CJE']*1e15,Cbc0_fF=c['CJC']*1e15,Cbc_2V_fF=cj(c['CJC'],0.63391,0.31113,2)*1e15,Ccs0_fF=c['CJS']*1e15,Ccs_2V_fF=cj(c['CJS'],0.35175,0.14716,2)*1e15,RB=c['RB'])
    fT=M[d]['ft_tf100p_at_100uA']; M[d]['fmax_est_100uA']=float(np.sqrt(fT/(8*np.pi*c['RB']*cj(c['CJC'],0.63391,0.31113,2))))
json.dump(M,open('metrics.json','w'),indent=1)
for d,m in M.items():
    print('==',d); [print(f'   {k:26s} {v:.4g}') for k,v in m.items()]
