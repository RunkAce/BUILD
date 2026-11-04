"""Dual blades: a matched pair of short swords designed AS a pair (Body = right blade, L = its X mirror).

Each blade is deliberately asymmetric so the mirrored pair reads as a set: the blade sweeps outward (+X) by a
pair sweep plus the race curve, and a hooked catcher tine (secondary, sword-breaker style) rises from the inner
(-X) end of the guard leaving a slot of negative space beside the blade, its root socket holding the motif2
glow gem (so the pair carries mirrored lights on its inner sides). The race blade dict drives
edge/tip/holes/notch/single_edge, the race guard is the cross-piece,
a slim throat langet clasps the root, a guard medallion with an accent rim holds the race motif inlay (focal),
and a short wrapped grip ends in the race pommel. Tine flavour: spikes -> barbed, round/organic -> curled ball
end, heavy/tool -> broad block, slender -> long and thin, faceted/clockwork -> angular.
Reads: blade dict, guard, pommel, grip_wraps, motif, motif2, silhouette, mats roles."""
import math

from shapely.geometry import Point, box
from shapely.ops import transform, unary_union

import core
import geo
from categories import _bladekit as K

ROOT = 0.12
GRIP_TOP, GRIP_BOT = -0.07, -0.72


def _tine(style, x_in, z0, gz):
    """Hooked catcher tine rising on the inner (-X) side; returns a polygon (x, z)."""
    s = K.sil(style)
    slender, heavy = bool(s.get('slender')), K.is_heavy(style)
    h = 0.78 + (0.12 if slender else 0.0) - (0.08 if heavy else 0.0)
    w0 = 0.11 if not heavy else 0.15
    w1 = 0.04 if not heavy else 0.07
    if slender:
        w0 *= 0.8
    out = 0.2 if not heavy else 0.22
    P = geo.bezier((x_in - out * 0.75, gz + 0.02), (x_in - out * 1.15, z0 + h * 0.4), (x_in - out * 1.05, z0 + h * 0.78),
                   (x_in - out * 0.3, z0 + h), 14)
    node = P[3]
    if s.get('faceted') or s.get('clockwork'):
        P = [P[0], P[5], P[10], P[14]]
    left, right = [], []
    n = len(P) - 1
    for i, (x, z) in enumerate(P):
        a = P[max(0, i - 1)]
        b = P[min(n, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / ln, tx / ln
        w = (w0 + (w1 - w0) * (i / n)) / 2
        left.append((x + nx * w, z + nz * w))
        right.append((x - nx * w, z - nz * w))
    tine = core.poly(left + right[::-1])
    tip = P[-1]
    if K.is_round(style):
        tine = tine.union(Point(*tip).buffer(w1 * 1.1 + 0.02, 12))
    else:
        # beak: the tine tip hooks in toward the blade
        tine = tine.union(core.poly([(tip[0] - w1 * 0.6, tip[1] - w1), (tip[0] + 0.09, tip[1] - 0.03),
                                     (tip[0] - w1 * 0.4, tip[1] + w1 * 0.7)]))
    if K.is_spiky(style):
        barbs = []
        for t in (0.35, 0.62):
            x, z = P[int(t * n)]
            barbs.append(core.poly([(x - 0.02, z - 0.05), (x - 0.13, z + 0.03), (x - 0.01, z + 0.07)]))
        tine = unary_union([tine] + barbs)
    return tine.buffer(0), node


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    s = K.sil(style)
    ch = K.chunk(style)
    heavy, slender = K.is_heavy(style), bool(s.get('slender'))
    edge, tip = bl.get('edge', 'straight'), bl.get('tip', 'point')
    body, glow = [], []

    L = 2.25 + (0.12 if slender else 0.0) - (0.1 if heavy else 0.0)
    W = 0.35 * K.clamp(bl.get('width', 1.0), 0.84, 1.22) * min(ch, 1.15) * (0.88 if slender else 1.0)
    single = bl.get('single_edge', False)
    shape = core.blade_outline(L, W, edge=edge, tip=tip, holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'),
                               single_edge=single)
    if not single:
        # paired asymmetry: the inner (-X) flank is narrower, so the mirrored pair leans its edges outward
        shape = transform(lambda x, z: (x * 0.72 if x < 0 else x, z), shape.segmentize(0.03)).buffer(0)
    shape = K.taper(shape, L, 0.1 if (heavy or tip == 'chisel') else 0.24)
    if K.is_spiky(style) and edge not in ('serrated', 'jagged'):
        x0 = shape.intersection(box(-2, 0.0, 0.0, 0.6)).bounds[0]
        teeth = unary_union([core.poly([(x0 + 0.02, z), (x0 - 0.12, z + 0.04), (x0 + 0.02, z + 0.1)])
                             for z in (L * 0.42, L * 0.54)])
        shape = shape.union(teeth).buffer(0)
    # porthole / coin slot (inlaid race holes), cut before the bend so it follows the blade
    shape, hole_parts = core.inlaid_hole(shape, bl.get('holes', 'none'), 0.5)
    k = min(0.16, 0.05 + 0.18 * s.get('curve', 0.0))
    shape = K.largest(core.bend(shape, k))
    hole_parts = [(n_, core.bend(g_, k), r_) for n_, g_, r_ in hole_parts]
    body.append(core.blade('Blade', core.place(shape, 0, ROOT - 0.06), L, col, M['primary'], thickness=0.12))
    body += core.inlay_parts('Blade', hole_parts, col, M, 0.12, place_fn=lambda g: core.place(g, 0, ROOT - 0.06))

    rx0, _, rx1, _ = shape.intersection(box(-2, 0.0, 2, 0.5)).bounds
    cx = (rx0 + rx1) / 2

    # --- guard (race) + inner catcher tine
    gw = (0.44 if not slender else 0.4) * min(ch, 1.2)
    gz = 0.0
    g = core.guard_shape(style, gw, 0.24)
    tine, root = _tine(style, rx0 - 0.03, ROOT, gz)
    body.append(core.plate('Guard', core.place(g, 0, gz), 0.25, col, M['secondary'], chamfer=0.04))
    body.append(core.plate('Catcher', tine, 0.17, col, M['secondary'], chamfer=0.03))

    # --- slim throat langet clasping the blade root, peeking above the guard
    gc = g.intersection(box(cx - 0.05, -2, cx + 0.05, 2))
    g_top = gz + (gc.bounds[3] if not gc.is_empty else 0.1)
    msz = 0.3 * min(ch, 1.1)
    med_z = gz + 0.03
    lw0, lw1 = rx0 - 0.05, rx1 + 0.05
    lang_top = max(g_top, med_z + msz * 0.5 + 0.04) + 0.16
    body.append(core.plate('Langet', K.langet_shape(style, lw0, lw1, ROOT - 0.18, lang_top), 0.17, col,
                           M['secondary'], chamfer=0.03))
    body.append(core.plate('GuardBand', box(lw0 - 0.04, gz - 0.2 * 0.24 - 0.01, lw1 + 0.04, gz - 0.2 * 0.24 + 0.075),
                           0.29, col, M['accent'], chamfer=0.022))
    # --- guard medallion (secondary) with the race motif inlay (focal)
    mr = msz * 0.5 + 0.045
    if K.is_round(style):
        med = Point(cx, med_z).buffer(mr, 20)
    elif s.get('faceted') or s.get('clockwork'):
        med = Point(cx, med_z).buffer(mr * 1.05, 6)
    elif K.is_heavy(style) or s.get('riveted'):
        med = box(cx - mr * 0.9, med_z - mr * 0.9, cx + mr * 0.9, med_z + mr * 0.9)
    else:
        med = Point(cx, med_z).buffer(mr * 1.12, 4)
    body.append(core.plate('Medallion', med, 0.31, col, M['secondary'], chamfer=0.03))
    body.append(core.plate('MedallionRim', med.difference(med.buffer(-0.035)), 0.33, col, M['accent'], chamfer=0.012))
    m = core.motif_plate('GuardMotif', style, msz, cx, med_z, 0.35, col, M['accent'])
    if m is not None:
        body.append(m)
    # --- motif2 glow gem where the catcher tine roots into the guard (inner side: the pair's mirrored lights)
    sock = Point(root[0], root[1]).buffer(0.085, 6 if (s.get('faceted') or s.get('clockwork')) else 12)
    body.append(core.plate('CatcherSocket', sock, 0.2, col, M['accent'], chamfer=0.02))
    gem = core.motif_plate('CatcherGem', style, 0.12, root[0], root[1], 0.24, col, M['glow'], key='motif2')
    if gem is not None:
        glow.append(gem)

    # --- grip + pommel
    body.append(core.collar('Collar', GRIP_TOP + 0.01, col, M['accent'], r=0.12, h=0.08))
    wraps = max(4, round(style.get('grip_wraps', 6) * 0.85))
    body.append(K.strap_grip('Grip', GRIP_BOT, GRIP_TOP, 0.09, wraps, col, M['grip'], segments=12, rpw=18))
    body.append(core.collar('LowerCollar', GRIP_BOT - 0.02, col, M['accent'], r=0.115, h=0.07))
    long_pommel = style.get('pommel') in ('spike', 'fang')
    psc = 1.25 * (0.82 if long_pommel else 1.0)
    body += core.pommel('Pommel', style, GRIP_BOT - 0.06, col, M['secondary'], scale=psc)

    grip = (0, 0, (GRIP_TOP + GRIP_BOT) / 2)
    tx, tz = max(shape.exterior.coords, key=lambda p: p[1])
    mirrors = {'L': 'Body'}
    if glow:
        mirrors['L_Glow'] = 'Glow'      # the pipeline strips Body faces under glow parts: mirror the glow too
    return dict(body=body, glow=glow, grip=grip, mirror_pieces=mirrors,
                attachments={'Grip': grip, 'VFX_Tip': (tx, 0, ROOT - 0.06 + tz), 'VFX_Guard': (0, 0, gz),
                             'VFX_Catcher': (root[0], 0, root[1])})
