import subprocess, numpy as np, os, json, sys
PDK=os.environ.get('PDK_ROOT', os.path.expanduser('~/pdk'))
NG=f'{PDK}/gf180mcuC/libs.tech/ngspice'
CORNER=sys.argv[1] if len(sys.argv)>1 else 'typical'
HDR=f""".include {NG}/design.ngspice
.lib {NG}/sm141064.ngspice bjt_{CORNER}
.lib {NG}/sm141064.ngspice diode_typical
.include {os.getcwd()}/eg1022n.lib
"""
DEV={'eg1022n':'Xq c b 0 0 eg1022n','asdrawn':'Xq c b 0 0 eg1022n_asdrawn',
     'stock_0p54x4':'Xq c b 0 0 npn_00p54x04p00','stock_10x10':'Xq c b 0 0 npn_10p00x10p00',
     'v2':'Xq c b 0 0 eg1022n_v2','stock_0p54x16':'Xq c b 0 0 npn_00p54x16p00'}
def ng(net,tag):
    fn=f'out/{tag}.cir'; open(fn,'w').write(net)
    r=subprocess.run(['ngspice','-b',fn],capture_output=True,text=True)
    if r.returncode: print(r.stdout[-2000:],r.stderr[-2000:]); raise SystemExit(tag)
    return r.stdout
os.makedirs('out',exist_ok=True)
res={}
if __name__=="__main__":
 for d,inst in DEV.items():
     R={}
     for T in ([-40,27,125] if d in('eg1022n','stock_0p54x4','v2','stock_0p54x16') else [27]):
         ng(f"""* gummel {d}
 {HDR}
 .temp {T}
 {inst}
 Vc c 0 2
 Vb b 0 0.5
 .control
 dc Vb 0.2 1.0 2m
 let icc = -i(Vc)
 let ibb = -i(Vb)
 wrdata out/gummel_{d}_{T}.dat icc ibb
 .endc
 .end
 """,f'gummel_{d}_{T}')
     ng(f"""* output {d}
 {HDR}
 {inst}
 Vc c 0 0
 Ib 0 b 1u
 .control
 let ibs = ( 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5 )
 let k = 0
 while k < length(ibs)
  let ibv = ibs[k]
  alter Ib dc = ibv
  dc Vc 0 6 10m
  set fn = out/out_{d}_$&k.dat
  wrdata $fn -i(Vc)
  let k = k + 1
 end
 .endc
 .end
 """,f'out_{d}')
     if d!='asdrawn':
         res[d]=ng(f"""* ft {d}
 {HDR}
 {inst}
 Vc c 0 2
 Ib 0 b dc 1u ac 1
 .control
 let ibs = ( 1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4 )
 let k = 0
 while k < length(ibs)
  let ibv = ibs[k]
  alter Ib dc = ibv
  op
  let icdc = -i(Vc)
  ac dec 40 1e3 1e11
  let h21 = mag(-i(Vc))
  meas ac fx when h21=1 fall=1
  echo "FT" $&ibv $&op1.icdc $&fx
  let k = k + 1
 end
 .endc
 .end
 """,f'ft_{d}')
 json.dump(res,open('out/ft_stdout.json','w'))
 print('done')
