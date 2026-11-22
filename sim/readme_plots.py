#!/usr/bin/env python3
"""README performance figures for EG-1022N V2 (writes docs/perf_*.png).

Needs the simulation outputs in sim/out/ (run run.py, run2.py and analyze.py first).
Colour roles follow a validated categorical palette (first three slots, all-pairs
CVD-safe); every series is also direct-labelled, so identity is never colour-only.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
DOCS = os.path.join(HERE, '..', 'docs')
os.makedirs(DOCS, exist_ok=True)

# --- roles -------------------------------------------------------------------
SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
DEV = {   # key: (label, short direct label, series colour)
    'v2':            ('EG-1022N V2', 'V2', '#2a78d6'),
    'stock_0p54x16': ('stock npn_00p54x16p00', 'stock 0.54×16', '#eb6834'),
    'eg1022n':       ('V1 disc, emitter gap fixed', 'V1 (gap fixed)', '#1baf7a'),
}
LW = 1.5  # points (~2 px)

plt.rcParams.update({
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
    'axes.edgecolor': GRID, 'axes.linewidth': 0.75, 'axes.labelcolor': INK2,
    'axes.titlecolor': INK, 'axes.titlesize': 11, 'axes.titleweight': 'semibold',
    'axes.titlelocation': 'left', 'axes.labelsize': 9,
    'xtick.color': INK2, 'ytick.color': INK2, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.75, 'grid.linestyle': '-',
    'axes.spines.top': False, 'axes.spines.right': False,
    'legend.frameon': False, 'legend.fontsize': 8, 'legend.labelcolor': INK2,
    'font.family': 'DejaVu Sans', 'lines.solid_capstyle': 'round', 'lines.solid_joinstyle': 'round',
})


def end_label(ax, x, y, text, color, dx=4, dy=0, ha='left'):
    """series-coloured end dot + ink-coloured direct label"""
    ax.plot([x], [y], 'o', ms=5, color=color, mec=SURFACE, mew=1.2, zorder=4)
    ax.annotate(text, (x, y), xytext=(dx if ha == 'left' else -dx, dy), textcoords='offset points',
                ha=ha, va='center', fontsize=8, color=INK2)


def gummel(d):
    a = np.loadtxt(os.path.join(OUT, f'gummel_{d}_27.dat'))
    return a[:, 0], a[:, 1], np.abs(a[:, 3])


# --- 1. DC: Gummel (V2) + current gain (3 devices) ----------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.0))
vb, ic, ib = gummel('v2')
c = DEV['v2'][2]
a1.semilogy(vb, ic, color=c, lw=LW, label='$I_C$')
a1.semilogy(vb, ib, color=c, lw=LW, ls=(0, (4, 2)), label='$I_B$')
k = np.searchsorted(vb, 0.9)
end_label(a1, vb[k], ic[k], '$I_C$', c, dy=6, dx=-6, ha='right')
end_label(a1, vb[k], ib[k], '$I_B$', c, dy=-8)
a1.set(xlim=(0.4, 1.0), ylim=(1e-11, 1e-2), xlabel='$V_{BE}$ (V)', ylabel='Current (A)')
a1.set_title('V2 Gummel plot  ($V_{CE}$ = 2 V, 27 °C)')
a1.legend(loc='upper left')

for d, (lab, short, col) in DEV.items():
    vb, ic, ib = gummel(d)
    m = (ic > 1e-9) & (ic < 5e-3)
    a2.semilogx(ic[m], ic[m] / ib[m], color=col, lw=LW, label=lab)
    j = np.argmax(ic[m] / ib[m])
    end_label(a2, ic[m][j], (ic[m] / ib[m])[j], f'{short}  β={(ic[m] / ib[m])[j]:.1f}', col,
              dx={'v2': 4, 'stock_0p54x16': 10, 'eg1022n': 4}[d],
              dy={'v2': 9, 'stock_0p54x16': -48, 'eg1022n': 9}[d],
              ha={'v2': 'left', 'stock_0p54x16': 'right', 'eg1022n': 'right'}[d])
a2.set(xlim=(1e-9, 5e-3), ylim=(0, 10), xlabel='$I_C$ (A)', ylabel='β = $I_C$ / $I_B$')
a2.set_title('Current gain')
a2.legend(loc='lower center')
fig.tight_layout()
fig.savefig(os.path.join(DOCS, 'perf_dc.png'), dpi=150)
plt.close(fig)

# --- 2. Speed: fT, C_BC, C_CS (small multiples) -------------------------------
P1 = json.load(open(os.path.join(HERE, 'params.json')))
P2 = json.load(open(os.path.join(HERE, 'params_v2.json')))
CJ = {  # zero-bias C_BC, C_CS (F); V1 C_BC includes the collector-stripe diode on the P-base
    'v2': (P2['CJC'], P2['CJS']),
    'stock_0p54x16': (3.540e-14, 8.211e-14),
    'eg1022n': (P1['CJC'] + 8.32e-12 * 0.00095 + 30e-6 * 1.33e-10, P1['CJS']),
}
ft = json.load(open(os.path.join(OUT, 'ft.json')))
fig, (b1, b2, b3) = plt.subplots(1, 3, figsize=(13, 4.0))
for d, (lab, short, col) in DEV.items():
    r = sorted([x for x in ft if x['dev'] == d and x['ft']], key=lambda x: x['ic'])
    I = np.array([x['ic'] for x in r]); F = np.array([x['ft'] for x in r]) / 1e9
    b1.loglog(I, F, color=col, lw=LW, label=lab)
    end_label(b1, I[-1], F[-1], short, col)
    v = np.linspace(0, 5, 200)
    cbc = CJ[d][0] / (1 + v / 0.63391) ** 0.31113 * 1e15
    ccs = CJ[d][1] / (1 + v / 0.35175) ** 0.14716 * 1e15
    b2.plot(v, cbc, color=col, lw=LW, label=lab)
    b3.plot(v, ccs, color=col, lw=LW, label=lab)
    j = 100   # V = 2.5 V
    dy = -10 if d == 'stock_0p54x16' else 9
    end_label(b2, v[j], cbc[j], f'{short}: {cbc[0]:.0f} fF at 0 V', col, dx=0, dy=dy, ha='left')
    end_label(b3, v[j], ccs[j], f'{short}: {ccs[0]:.0f} fF at 0 V', col, dx=0, dy=dy, ha='left')
b1.set(xlim=(5e-8, 5e-3), xlabel='$I_C$ (A)', ylabel='$f_T$ (GHz)')
b1.set_title('$f_T$ vs collector current  ($V_{CE}$ = 2 V)')
b1.legend(loc='upper left')
b2.set(xlim=(0, 5), ylim=(0, 360), xlabel='Reverse bias $V_{CB}$ (V)', ylabel='Capacitance (fF)')
b2.set_title('Base–collector capacitance')
b3.set(xlim=(0, 5), ylim=(0, 360), xlabel='Reverse bias $V_{CS}$ (V)', ylabel='Capacitance (fF)')
b3.set_title('Collector–substrate capacitance')
b2.legend(loc='upper center')
b3.legend(loc='upper center')
fig.text(0.01, 0.005, 'fT is capacitance-limited: the PDK NPN models have no transit time, '
         'so these are upper bounds at high current.', fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(os.path.join(DOCS, 'perf_speed.png'), dpi=150)
plt.close(fig)

# --- 3. Output characteristics (V2) -------------------------------------------
IBO = [0.2, 0.5, 1, 2, 5, 10]
fig, ax = plt.subplots(figsize=(6.5, 4.0))
c = DEV['v2'][2]
for k, ibv in enumerate(IBO):
    a = np.loadtxt(os.path.join(OUT, f'out_v2_{k}.dat'))
    ax.plot(a[:, 0], a[:, 1] * 1e6, color=c, lw=LW)
    ax.annotate(f'$I_B$ = {ibv:g} µA', (a[-1, 0], a[-1, 1] * 1e6),
                xytext=(4, {0.2: -8, 0.5: 0, 1: 8}.get(ibv, 0)),
                textcoords='offset points', va='center', fontsize=8, color=INK2)
ax.set(xlim=(0, 7.2), ylim=(0, None), xlabel='$V_{CE}$ (V)', ylabel='$I_C$ (µA)')
ax.set_xticks(range(0, 7))
ax.set_title('V2 output characteristics  (27 °C)')
fig.tight_layout()
fig.savefig(os.path.join(DOCS, 'perf_output.png'), dpi=150)
plt.close(fig)
print('wrote docs/perf_dc.png, docs/perf_speed.png, docs/perf_output.png')
