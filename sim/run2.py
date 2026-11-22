import subprocess, os, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from run import HDR, DEV, ng   # reuses gummel already produced by run.py
jobs=[]
IBO=[2e-7,5e-7,1e-6,2e-6,5e-6,1e-5]
IBF=[1e-8,2e-8,5e-8,1e-7,2e-7,5e-7,1e-6,2e-6,5e-6,1e-5,2e-5,5e-5,1e-4,2e-4]
def out_job(d,inst,k,ib):
    ng(f"""* out
{HDR}
{inst}
Vc c 0 0
Ib 0 b {ib}
.control
dc Vc 0 6 10m
wrdata out/out_{d}_{k}.dat -i(Vc)
.endc
.end
""",f'out_{d}_{k}')
def ft_job(d,inst,ib):
    s=ng(f"""* ft
{HDR}
{inst}
Vc c 0 2
Ib 0 b dc {ib} ac 1
.control
op
print -i(Vc) v(b)
ac dec 50 1e3 1e11
let h21 = mag(-i(Vc))
meas ac fx when h21=1 fall=1
meas ac h21lf find h21 at=1e3
.endc
.end
""",f'ft_{d}_{ib}')
    ic=float(re.search(r'-i\(vc\)\s*=\s*([-\d.eE+]+)',s).group(1)); vb=float(re.search(r'v\(b\)\s*=\s*([-\d.eE+]+)',s).group(1))
    m=re.search(r'fx\s*=\s*([-\d.eE+]+)',s); h=re.search(r'h21lf\s*=\s*([-\d.eE+]+)',s)
    return dict(dev=d,ib=ib,ic=ic,vbe=vb,ft=float(m.group(1)) if m else None,h21lf=float(h.group(1)))
with ThreadPoolExecutor(12) as ex:
    fs=[ex.submit(out_job,d,i,k,ib) for d,i in DEV.items() for k,ib in enumerate(IBO)]
    ff=[ex.submit(ft_job,d,i,ib) for d,i in DEV.items() if d!='asdrawn' for ib in IBF]
    [f.result() for f in fs]; ft=[f.result() for f in ff]
json.dump(ft,open('out/ft.json','w'),indent=0)
for r in ft: print(r)
