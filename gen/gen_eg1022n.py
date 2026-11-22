#!/usr/bin/env python3
"""
Parametric generator for EG-1022N v2: a GF180MCU vertical NPN whose layout
draws the NPN schematic symbol.

Physical mapping of the symbol strokes
  base bar + emitter line  -> P-base (PWELL in DNWELL) only under the strokes
  emitter line + arrowhead -> N+ emitter, 0.54 um wide stripe (stock 0.54xL
                              family cross-section), 0.35 um gap to base P+
  base flanks              -> P+ base contact beside the emitter, metal1 strap
  collector line           -> N+ collector stripe in DNWELL (no P-base under it)
  outline of base strokes  -> N+ collector ring around the P-base (as in the
                              stock cells), metal1 with gaps where leads cross
  circle                   -> P+ substrate guard ring (outside DNWELL)
  base lead                -> metal1 to the left

Usage: python3 gen_eg1022n.py [out.mag]   (writes the .mag + preview png)
"""
import sys, time
import numpy as np
from scipy import ndimage

G = 0.005                   # raster grid, um (= Magic internal unit)
EXT = 20.5                  # half-extent of the raster, um
S2 = np.sqrt(0.5)

# ---------------------------------------------------------------- parameters
P = dict(
    # circle (P+ substrate guard ring)
    ring_r_in=19.4, ring_w=0.8,
    # base bar (P-base rectangle)
    bar_x=(-6.2, -3.2), bar_y=(-7.5, 7.5),
    # emitter stripe: start point, 45 deg down-right; arrowhead leg length
    em_p0=(-2.70, -1.60), em_w=0.54, arrow_leg=2.2, em_area_target=8.60,
    # cross-section (um), from the stock npn_00p54x16p00 cell / GF180 rules
    eb_gap=0.35,            # emitter N+ to base P+
    bp_w=0.60,              # base P+ flank width (holds 45-deg contacts)
    pw_sur=0.20,            # P-base surround of base P+ (>=0.12*sqrt2 on 45-deg edges)
    pw_nsd_gap=0.30,        # P-base to collector N+
    col_w=0.60,             # collector outline N+ width
    dnw_sur_pw=2.50,        # DNWELL surround of P-base (LPW.3)
    dnw_sur_nsd=0.65,       # DNWELL surround of N-ohmic (>=0.62)
    dnw_sub_gap=2.50,       # DNWELL to substrate P+ ring
    # collector line
    col_p0=(-2.60, 2.30), col_line_w=0.80, col_line_end_r=15.0,
    # leads
    lead_w=0.80, base_lead_x=-17.6, em_lead_end_r=17.6,
    # contacts
    ct=0.25, ct_pitch=0.50, diff_sur=0.065, m1_sur=0.055, m1_gap=0.30,
)

# ---------------------------------------------------------------- raster helpers
N = int(round(2 * EXT / G))
ax = (np.arange(N) + 0.5) * G - EXT
ax = ax.astype(np.float32)
X, Y = np.meshgrid(ax, ax)          # Y increases with row index


def dil(m, r):
    """octagonal dilation (contains the Euclidean disc of radius r), so all
    edges stay at 0/45/90 degrees: square(s) (+) diamond(t)"""
    if r <= 0:
        return m.copy()
    ks = int(np.ceil(r * (np.sqrt(2) - 1) / G - 1e-9))
    kt = int(np.ceil(r * (2 - np.sqrt(2)) / G - 1e-9))
    out = ndimage.distance_transform_cdt(~m, metric='taxicab') <= kt
    if ks:
        u = out.view(np.uint8)
        u = ndimage.maximum_filter1d(u, 2 * ks + 1, axis=0)
        u = ndimage.maximum_filter1d(u, 2 * ks + 1, axis=1)
        out = u.astype(bool)
    return out


def ero(m, r):
    return ~dil(~m, r)


def close_(m, r):
    return ero(dil(m, r), r)


def band(p0, p1, w, vstart=False, vend=False):
    """stripe of width w from p0 to p1. Ends are flat, or (v*) V-shaped with a
    horizontal + vertical edge meeting on the centre line, which avoids 45-degree
    pointed corners that Magic's width check flags."""
    p0, p1 = np.array(p0), np.array(p1)
    d = p1 - p0
    L = np.hypot(*d)
    u = d / L
    rx, ry = X - p0[0], Y - p0[1]
    t = rx * u[0] + ry * u[1]
    n = -rx * u[1] + ry * u[0]
    m = np.abs(n) <= w / 2
    sx, sy = np.sign(u[0]), np.sign(u[1])
    m &= (((X - p0[0]) * sx >= 0) & ((Y - p0[1]) * sy >= 0)) if vstart else (t >= 0)
    m &= (((p1[0] - X) * sx >= 0) & ((p1[1] - Y) * sy >= 0)) if vend else (t <= L)
    return m


def rect(x0, x1, y0, y1):
    return (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)


CHAMF = 0.30   # flat cut on the arrowhead's two 45-degree acute corners


def tri_tip(T, a, x=None, y=None):
    """right isosceles triangle, right angle at tip T, pointing down-right,
    with its two acute corners cut square (no acute angles)"""
    x = X if x is None else x
    y = Y if y is None else y
    tx, ty = T
    return ((x <= tx) & (y >= ty) & ((tx - x) + (y - ty) <= a)
            & (x >= tx - a + CHAMF) & (y <= ty + a - CHAMF))


def area(m):
    return m.sum() * G * G


# ---------------------------------------------------------------- geometry
def build(P):
    d_em = np.array([S2, -S2])
    a = P['arrow_leg']
    p0 = np.array(P['em_p0'])

    def geom(t):
        T = p0 + t * d_em
        return T, T + np.array([-a / 3, a / 3])

    def em_area(t):
        # exact-ish area on a local 5 nm window (cheap)
        T, cen = geom(t)
        g = np.arange(min(p0[0], T[0] - a) - 1, max(p0[0], T[0]) + 1, G) + G / 2
        h = np.arange(min(p0[1], T[1]) - 1, max(p0[1], T[1] + a) + 1, G) + G / 2
        x, y = np.meshgrid(g, h)
        tri = tri_tip(T, a, x, y)
        u = d_em
        rx, ry = x - p0[0], y - p0[1]
        tt = rx * u[0] + ry * u[1]
        nn = -rx * u[1] + ry * u[0]
        L = np.hypot(*(cen - p0))
        st = ((x - p0[0]) >= 0) & ((y - p0[1]) <= 0) & (tt <= L) & (np.abs(nn) <= P['em_w'] / 2)
        return (tri | st).sum() * G * G

    # solve stripe length for the target emitter area (extracts as a stock bucket)
    lo, hi = a, 20.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if em_area(mid) < P['em_area_target']:
            lo = mid
        else:
            hi = mid
    T, cen = geom((lo + hi) / 2)
    E = tri_tip(T, a) | band(p0, cen, P['em_w'], vstart=True)

    bar = rect(P['bar_x'][0], P['bar_x'][1], P['bar_y'][0], P['bar_y'][1])
    bar_pp = ero(bar, P['pw_sur'])
    near_E = dil(E, P['eb_gap'])
    PP = close_(bar_pp | dil(E, P['eb_gap'] + P['bp_w']), 0.25) & ~near_E   # base P+ (notches filled)
    PB = close_(dil(PP | E, P['pw_sur']) | bar, 0.5)                     # P-base

    # collector N+ : outline around P-base + collector line to the circle
    col_out = dil(PB, P['pw_nsd_gap'] + P['col_w']) & ~dil(PB, P['pw_nsd_gap'])
    cq0 = np.array(P['col_p0'])
    cl_len = P['col_line_end_r'] - np.hypot(*cq0) * 0.0
    cq1 = cq0 + np.array([S2, S2]) * 1.0
    # extend line until its far end reaches col_line_end_r from the centre
    t = 0.0
    while np.hypot(*(cq0 + t * np.array([S2, S2]))) < P['col_line_end_r']:
        t += 0.01
    cq1 = cq0 + t * np.array([S2, S2])
    col_line = band(cq0, cq1, P['col_line_w'], vend=True)
    NSD = close_(col_out | col_line, 0.3) & ~dil(PB, P['pw_nsd_gap'])

    DNW = close_(dil(PB, P['dnw_sur_pw']) | dil(NSD, P['dnw_sur_nsd']), 1.3)

    # substrate ring
    R = np.hypot(X, Y)
    SUB = (R >= P['ring_r_in']) & (R <= P['ring_r_in'] + P['ring_w'])

    # leads (metal1 only)
    bl = rect(P['base_lead_x'], P['bar_x'][0] + 0.5, -P['lead_w'] / 2, P['lead_w'] / 2)
    t = 0.0
    while np.hypot(*(T + t * d_em)) < P['em_lead_end_r']:
        t += 0.01
    el_end = T + t * d_em
    el = band(cen, el_end, P['lead_w'], vend=True)

    # metal1 nets
    M_E = E | el
    keep_E = dil(M_E, P['m1_gap'])
    M_B = ((bar_pp | (dil(E, P['eb_gap'] + P['bp_w']) & ~near_E)) & PP & ~keep_E) | (bl & ~keep_E)
    M_B = close_(M_B, 0.25) & PP | (bl & ~keep_E)
    M_B = dil(ero(M_B & ~dil(M_E, P['m1_gap']), 0.12), 0.12)          # drop slivers
    keep_B = dil(M_B, P['m1_gap'])
    M_C = NSD & ~dil(M_E | M_B, P['m1_gap'])
    M_C = dil(ero(M_C, 0.12), 0.12) & ~dil(M_E | M_B, P['m1_gap'])   # drop slivers
    M_S = SUB.copy()

    L = dict(PB=PB, DNW=DNW, E=E, PP=PP, NSD=NSD, SUB=SUB,
             M_E=M_E, M_B=M_B, M_C=M_C, M_S=M_S)
    pts = dict(T=T, cen=cen, p0=p0, cq0=cq0, cq1=cq1, el_end=el_end)
    return L, pts


# ---------------------------------------------------------------- contacts
def place_contacts(diff, metal, centrelines, P):
    """greedy contact placement on candidate points that fit diff+metal surround.
    Contacts are exact ct x ct squares on the 5 nm grid."""
    n = int(round(P['ct'] / G))                     # contact size in pixels
    def sq_ero(m, r):                               # fits a square of half-size r?
        k = int(np.ceil(r / G))
        u = m.view(np.uint8)
        u = ndimage.minimum_filter1d(u, 2 * k + 1, axis=0)
        u = ndimage.minimum_filter1d(u, 2 * k + 1, axis=1)
        return u.astype(bool)
    h = P['ct'] / 2
    ok = sq_ero(diff, h + P['diff_sur']) & sq_ero(metal, h + P['m1_sur'])
    pitch = P['ct_pitch']
    acc, grid = [], {}
    for (x, y) in centrelines:
        j0 = int(round((x + EXT) / G)) - n // 2      # lower-left pixel of the square
        i0 = int(round((y + EXT) / G)) - n // 2
        ic, jc = i0 + n // 2, j0 + n // 2
        if not (0 <= ic < N and 0 <= jc < N) or not ok[ic, jc]:
            continue
        cx, cy = (j0 + n / 2) * G - EXT, (i0 + n / 2) * G - EXT
        key = (int(cx // pitch), int(cy // pitch))
        near = [grid[(key[0] + dx, key[1] + dy)] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if (key[0] + dx, key[1] + dy) in grid]
        if any(max(abs(cx - qx), abs(cy - qy)) < pitch for lst in near for qx, qy, _, _ in lst):
            continue
        grid.setdefault(key, []).append((cx, cy, i0, j0))
        acc.append((cx, cy, i0, j0))
    m = np.zeros_like(diff)
    for _, _, i0, j0 in acc:
        m[i0:i0 + n, j0:j0 + n] = True
    return m, acc


def centreline_samples(mask, step=0.05):
    """sample points along the medial axis (skeleton) of a mask"""
    sk = ndimage.distance_transform_edt(mask)
    mx = ndimage.maximum_filter(sk, size=5)
    ridge = (sk == mx) & mask & (sk > 0)
    ii, jj = np.nonzero(ridge)
    pts = list(zip(ax[jj].astype(float), ax[ii].astype(float)))
    pts.sort(key=lambda p: (round(float(np.arctan2(p[1], p[0])), 2), float(np.hypot(*p))))
    return pts[::4]


# ---------------------------------------------------------------- .mag writer
def to_rects(m):
    """row run-length + vertical merge -> list of (x0,y0,x1,y1) in raster cells"""
    rects, open_ = [], {}
    for i in range(m.shape[0] + 1):
        runs = set()
        if i < m.shape[0]:
            row = np.concatenate([[0], m[i].astype(np.int8), [0]])
            d = np.diff(row)
            runs = set(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))
        nxt = {}
        for r, i0 in open_.items():
            if r in runs:
                nxt[r] = i0
            else:
                rects.append((r[0], i0, r[1], i))
        for r in runs:
            if r not in nxt:
                nxt[r] = i
        open_ = nxt
    return rects


def notch_tris(full):
    """1-pixel staircase notches of a 0/45/90-degree mask -> half-pixel
    triangles that make the 45-degree edges exact (Magic split tiles)"""
    p = np.pad(full, 1)
    W, E_, S, Nn = p[1:-1, :-2], p[1:-1, 2:], p[:-2, 1:-1], p[2:, 1:-1]
    e = ~full
    out = []
    for d, m in [('sw', e & W & S & ~Nn & ~E_), ('se', e & E_ & S & ~Nn & ~W),
                 ('ne', e & E_ & Nn & ~S & ~W), ('nw', e & W & Nn & ~S & ~E_)]:
        ii, jj = np.nonzero(m)
        out += [(j, i, d) for i, j in zip(ii, jj)]
    return out


def write_mag(fn, layers, labels):
    k = int(round(G / 0.005))                  # raster cell -> magic units
    o = int(round(EXT / 0.005))
    with open(fn, 'w') as f:
        f.write(f"magic\ntech gf180mcuC\nmagscale 1 10\ntimestamp {int(time.time())}\n")
        for name, m, full in layers:
            if not m.any():
                continue
            f.write(f"<< {name} >>\n")
            for (x0, y0, x1, y1) in to_rects(m):
                f.write(f"rect {x0*k-o} {y0*k-o} {x1*k-o} {y1*k-o}\n")
            if full is not None:
                for (j, i, d) in notch_tris(full):
                    f.write(f"tri {j*k-o} {i*k-o} {(j+1)*k-o} {(i+1)*k-o} {d}\n")
        f.write("<< labels >>\n")
        for i, (name, layer, (x0, y0, x1, y1)) in enumerate(labels):
            c = lambda v: int(round(v / 0.005))
            f.write(f"rlabel {layer} {c(x0)} {c(y0)} {c(x1)} {c(y1)} 0 {name}\n")
            f.write(f"port {i+1} nsew\n")
        f.write("<< end >>\n")


# ---------------------------------------------------------------- main
def main(out='EG1022N_V2.mag'):
    L, pts = build(P)
    E, PP, NSD, SUB = L['E'], L['PP'], L['NSD'], L['SUB']

    CE, ce = place_contacts(E, L['M_E'], centreline_samples(E), P)
    CB, cb = place_contacts(PP, L['M_B'], centreline_samples(PP), P)
    CC, cc = place_contacts(NSD, L['M_C'], centreline_samples(NSD), P)
    th = np.linspace(-np.pi, np.pi, 4000, endpoint=False)
    rr = P['ring_r_in'] + P['ring_w'] / 2
    CS, cs = place_contacts(SUB, L['M_S'], list(zip(rr * np.cos(th), rr * np.sin(th))), P)

    lab = lambda x, y, w=0.3: (x - w / 2, y - w / 2, x + w / 2, y + w / 2)
    el = pts['el_end'] - 0.3 * np.array([S2, -S2])
    labels = [
        ('c', 'metal1', lab(*(pts['cq1'] - 0.3 * np.array([S2, S2])))),
        ('b', 'metal1', lab(P['base_lead_x'] + 0.3, 0.0)),
        ('e', 'metal1', lab(*el)),
        ('s', 'metal1', lab(rr, 0.0)),
    ]
    M1 = L['M_E'] | L['M_B'] | L['M_C'] | L['M_S']
    CT = CE | CB | CC | CS
    # (name, mask to write as rects, full shape used for 45-degree triangles)
    # the round substrate ring is left as a plain staircase (it is DRC clean)
    layers = [
        ('deepnwell', L['DNW'], L['DNW']),
        ('pbase', L['PB'], L['PB']),
        ('ndiff', E & ~CE, E),
        ('ndiffc', CE, None),
        ('psubdiff', (PP | SUB) & ~(CB | CS), PP),
        ('psubdiffcont', CB | CS, None),
        ('nsubdiff', NSD & ~CC, NSD),
        ('nsubdiffcont', CC, None),
        ('metal1', M1 & ~CT, M1 & ~dil(SUB, 0.1)),
    ]
    write_mag(out, layers, labels)

    print(f"wrote {out}")
    print(f"  emitter area {area(E):.3f} um2, P-base {area(L['PB']):.1f} um2, "
          f"DNWELL {area(L['DNW']):.1f} um2")
    print(f"  contacts: E {len(ce)}  B {len(cb)}  C {len(cc)}  S {len(cs)}")
    dsub = ndimage.distance_transform_edt(~SUB) * G
    print(f"  DNWELL to substrate ring min gap {dsub[L['DNW']].min():.2f} um")
    np.savez_compressed(out.replace('.mag', '_masks.npz'), **L)
    preview(out.replace('.mag', '_preview.png'), L, CE | CB | CC | CS)


def preview(fn, L, CT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    st = 8
    img = np.ones(L['PB'][::st, ::st].shape + (3,))
    for k, c, a in [('DNW', (.55, .55, .55), .45), ('PB', (.88, .70, .35), .7),
                    ('NSD', (.2, .45, 1), .8), ('PP', (1, .45, .6), .8), ('SUB', (1, .45, .6), .8),
                    ('E', (.1, .8, .1), .9)]:
        m = L[k][::st, ::st][..., None]
        img = np.where(m, img * (1 - a) + np.array(c) * a, img)
    M = (L['M_E'] | L['M_B'] | L['M_C'] | L['M_S'])[::st, ::st][..., None]
    img = np.where(M, img * 0.6 + np.array([.55, .6, 1.0]) * 0.4, img)
    img = np.where(CT[::st, ::st][..., None], np.zeros(3), img)
    fig, axs = plt.subplots(figsize=(8, 8))
    axs.imshow(img, origin='lower', extent=[-EXT, EXT, -EXT, EXT])
    axs.set_title('EG-1022N v2  grey=DNWELL tan=P-base green=N+ emitter blue=N+ collector '
                  'pink=P+ (base/sub) lilac=metal1', fontsize=7)
    plt.savefig(fn, dpi=110)
    plt.close()


if __name__ == '__main__':
    main(*sys.argv[1:])
