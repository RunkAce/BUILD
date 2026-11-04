"""Greatsword: big two-handed blade with real negative space, chunky guard, long two-hand grip.

Structure (z up): a broad race blade (edge/tip/notch/single_edge; slight sweep for curving races) whose
negative space follows the race blade dict (slot -> long tapered window, rings -> three bezelled portholes,
none -> raised central ridge), clasped at the root by a race-shaped ricasso langet (secondary) that carries
the race motif inlay (focal); spiky races get flame spurs above the langet. An oversized race guard with an
accent band and a boss holding the motif2 gem (the single glow accent). Tall solid guards (disk / tsuba-like)
switch to a shield layout: accent rim (+ rivets for mechanical races), the motif inlaid on the guard face, a short
collar langet, and the motif2 glow gem moved to the pommel waist. A long wrapped grip split by a hand band
(Grip / GripSecondary); collars; a heavy race pommel.
Reads: blade dict, guard, pommel, grip_wraps, motif, motif2, silhouette (chunky, slender, heavy/tool, curve,
spikes/barbs/thorns/feral, round/organic/portals, faceted/clockwork, riveted), mats roles."""
import math

from shapely.geometry import Point, box
from shapely.ops import unary_union

import core
from categories import _bladekit as K

ROOT = 0.04                       # blade root (inside the guard)
GRIP_TOP, GRIP_BOT = -0.13, -1.4
GRIP_MID = -0.74


def _blade_shape(style, L, W):
    bl = style.get('blade', {})
    s = K.sil(style)
    single = bl.get('single_edge', False)
    hw = W / 2
    shape = core.blade_outline(L, W, edge=bl.get('edge', 'straight'), tip=bl.get('tip', 'point'), holes='none',
                               notch=bl.get('notch', 'none'), single_edge=single)
    # always taper (>= ~15% narrower where the tip begins): heavy / broad blades included, or they read as slabs
    k = 0.22 if K.is_heavy(style) or bl.get('edge') == 'broad' else (0.22 if s.get('slender') else 0.17)
    shape = K.taper(shape, L, k)
    # widening edges (broad) can cancel the taper: measure and taper again until the shoulder under the tip is
    # at least ~22% narrower than the blade just above the langet (the visible root)
    tip_len = {'point': 0.24, 'clip': 0.2, 'split': 0.22, 'chisel': 0.1, 'hook': 0.18, 'spade': 0.26}.get(
        bl.get('tip', 'point'), 0.22) * L

    def _w(z):
        sl = shape.intersection(box(-3, z - 0.02, 3, z + 0.02))
        return (sl.bounds[2] - sl.bounds[0]) if not sl.is_empty else None

    for _ in range(3):
        w0, w1 = _w(L * 0.28), _w(L - tip_len - 0.05)
        if not (w0 and w1) or w1 / w0 <= 0.78:
            break
        shape = K.taper(shape, L, min(0.3, w1 / w0 - 0.76))
    return shape, single, hw


def _ridge(single, rx0, hw, z0, z1):
    """Raised central fuller ridge (tapers to a point), on the blade centre or toward the spine."""
    rw = hw * 0.16
    rxc = (rx0 + hw * 0.32) if single else 0.0
    return core.poly([(rxc - rw, z0), (rxc + rw, z0), (rxc + rw * 0.8, z1 - 0.35), (rxc, z1),
                      (rxc - rw * 0.8, z1 - 0.35)])


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    s = K.sil(style)
    ch = K.chunk(style)
    heavy, slender = K.is_heavy(style), bool(s.get('slender'))
    body, glow = [], []

    L = 3.95 + (0.25 if slender else 0.0) - (0.15 if heavy else 0.0)
    W = 1.04 * K.clamp(bl.get('width', 1.0), 0.84, 1.2) * ch * (0.88 if slender else 1.0)
    W = min(W * (1.22 if bl.get('single_edge') else 1.0), 1.22)
    shape, single, hw = _blade_shape(style, L, W)
    # blade extent at the root (single-edged blades are offset: spine at -0.42 hw)
    rx0, _, rx1, _ = shape.intersection(box(-2, 0, 2, 0.6)).bounds
    cx = (rx0 + rx1) / 2
    # guard first: the langet must rise clear of the guard's centre so its motif inlay reads
    gw = max((1.0 if not slender else 0.92) * ch, W * 0.5 + 0.42)
    g = core.guard_shape(style, gw, 0.42)
    gz = -0.06
    gc = g.intersection(box(cx - 0.06, -3, cx + 0.06, 3))
    g_top = gz + (gc.bounds[3] if not gc.is_empty else 0.15)
    lx0, lx1 = rx0 - 0.065, rx1 + 0.065
    # tall solid guards (disk / tsuba-like) become a shield: the motif sits on the guard face instead
    shield = g_top - gz > 0.45 and g.contains(Point(cx, 0.25))
    if shield:
        msz = 0.5
        mz = gz + 0.14
        lang_top = g_top - ROOT + 0.24
    else:
        msz = min((lx1 - lx0) * 0.72, 0.46)
        mz = max(ROOT + 0.12 + msz * 0.5, g_top + msz * 0.5 + 0.05)
        lang_top = max(0.62 + (0.06 if slender else 0.0), mz + msz * 0.5 + 0.12 - ROOT)

    # --- flame spurs / barbs above the langet (spiky races)
    if K.is_spiky(style):
        spurs = []
        zs = (lang_top + 0.06, lang_top + 0.42) if s.get('feral') or s.get('barbs') else (lang_top + 0.06,)
        for z in zs:
            spurs.append(core.poly([(rx1 - 0.04, z - 0.02), (rx1 + 0.17, z + 0.04), (rx1 - 0.03, z + 0.3)]))
            if not single:
                spurs.append(core.poly([(rx0 + 0.04, z - 0.02), (rx0 - 0.17, z + 0.04), (rx0 + 0.03, z + 0.3)]))
        shape = unary_union([shape] + spurs).buffer(0)

    # --- negative space (the race blade dict asks for it) or a raised ridge
    holes = bl.get('holes', 'none')
    extras = []                                           # (name, local shape, thickness, material)
    body_len = L * 0.76
    if holes == 'slot':
        sx = cx if single else 0.0
        sw = hw * (0.2 if single else 0.24)
        z0, z1 = lang_top + 0.12, body_len * 0.86
        win = core.poly([(sx - sw * 0.55, z0), (sx + sw * 0.55, z0), (sx + sw, z0 + 0.25), (sx + sw * 0.85, z1 - 0.3),
                         (sx, z1), (sx - sw * 0.85, z1 - 0.3), (sx - sw, z0 + 0.25)])
        shape = shape.difference(win)
    elif holes == 'rings':
        hx = (rx0 + hw * 0.28) if single else 0.0
        r = hw * (0.22 if single else 0.27)
        for k in range(2):                                 # at most two portholes on a greatsword
            c = Point(hx, lang_top + 0.4 + r + k * (r * 2 + 0.34)).buffer(r, 9)
            shape = shape.difference(c)
            extras.append((f'HoleBezel{k}', Point(hx, c.centroid.y).buffer(r + 0.045, 9).difference(c), 0.19,
                           M['accent']))
    elif holes in core.INLAID_HOLES:              # one big seated porthole / coin slot just above the langet
        shape, hp = core.inlaid_hole(shape, holes, lang_top + 0.06)
        for suffix, e, role in hp:
            extras.append((suffix, e, 0.2 if role == 'rim' else 0.09,
                           M['accent'] if role == 'rim' else (M.get('glass') or M['secondary'])))
        # ... plus a fuller ridge running on from above the hole so the upper blade is not a blank slab
        h_top = max((e.bounds[3] for _, e, _ in hp), default=lang_top + 0.3)
        extras.append(('Ridge', _ridge(single, rx0, hw, h_top + 0.14, max(body_len * 0.8, h_top + 1.3)), 0.19, M['primary']))
    elif holes == 'motif':
        m = K.motif_shape(style, hw * 1.1)
        if m is not None:
            shape = shape.difference(core.place(m, cx, lang_top + 0.6))
    else:
        extras.append(('Ridge', _ridge(single, rx0, hw, lang_top - 0.05, body_len * 0.78), 0.19, M['primary']))
    shape = K.largest(shape.buffer(0))

    # --- gentle sweep for curving races
    curv = 0.1 * s.get('curve', 0.0) if s.get('curve', 0.0) > 0.12 else 0.0
    if curv:
        shape = core.bend(shape, curv)
        extras = [(n, core.bend(e, curv), t, m) for n, e, t, m in extras]
    body.append(core.blade('Blade', core.place(shape, 0, ROOT), L, col, M['primary'], thickness=0.15,
                           bevel=0.075))
    for n, e, t, m in extras:
        body.append(core.plate(n, core.place(e, 0, ROOT), t, col, m, chamfer=0.02))

    # --- ricasso langet (secondary) clasping the root + race motif inlay (focal)
    lang = K.langet_shape(style, lx0, lx1, -0.1, ROOT + lang_top)
    body.append(core.plate('Langet', lang, 0.23, col, M['secondary'], chamfer=0.035))
    m = core.motif_plate('RootMotif', style, msz, cx, mz, 0.39 if shield else 0.29, col, M['accent'])
    if m is not None:
        body.append(m)
    if K.is_mech(style) and not shield:
        for i, x in enumerate((lx0 + 0.075, lx1 - 0.075)):
            body.append(K.stud(f'LangetRivet{i}', x, max(g_top + 0.08, mz - msz * 0.3), 0.042, 0.29, col,
                               M['accent']))

    # --- chunky guard + accent band + boss with the motif2 glow gem
    body.append(core.plate('Guard', core.place(g, 0, gz), 0.33, col, M['secondary'], chamfer=0.045))
    if shield:
        gp = core.place(g, 0, gz).simplify(0.01)
        body.append(core.plate('GuardRim', gp.difference(gp.buffer(-0.045)), 0.36, col, M['accent'], chamfer=0.015))
        if K.is_mech(style):
            for i in range(6):
                a = math.pi / 2 + i * math.pi / 3
                rr = (g_top - gz) - 0.12
                body.append(K.stud(f'GuardRivet{i}', cx + rr * math.cos(a), gz + rr * math.sin(a), 0.04, 0.39, col,
                                   M['accent']))
    else:
        bw = max(lx1 - lx0, 0.3) / 2 + 0.05
        body.append(core.plate('GuardBand', box(cx - bw, gz - 0.06, cx + bw, gz + 0.05), 0.37, col, M['accent'],
                               chamfer=0.03))
    boss_r = 0.15
    if s.get('faceted') or s.get('clockwork'):
        boss = Point(cx, gz - 0.005).buffer(boss_r, 6)
    elif s.get('heavy') or s.get('tool') or s.get('riveted'):
        boss = box(cx - boss_r * 0.9, gz - boss_r * 0.9, cx + boss_r * 0.9, gz + boss_r * 0.9)
    else:
        boss = Point(cx, gz - 0.005).buffer(boss_r, 10)
    if not shield:
        body.append(core.plate('GuardBoss', boss, 0.41, col, M['accent'], chamfer=0.03))
        gem = core.motif_plate('BossGem', style, boss_r * 1.45, cx, gz - 0.005, 0.45, col, M['glow'], key='motif2')
        if gem is not None:
            glow.append(gem)

    # --- long two-hand grip split by a hand band
    wraps = max(7, min(11, round(style.get('grip_wraps', 6) * 1.45)))
    gr = 0.098 * (1.04 if heavy else 1.0)
    body.append(core.collar('Collar', GRIP_TOP + 0.01, col, M['accent'], r=0.135, h=0.09))
    body.append(K.strap_grip('Grip', GRIP_BOT, GRIP_TOP, gr, wraps, col, M['grip'], segments=10, rpw=11))
    body.append(core.collar('HandBand', GRIP_MID, col, M['accent'], r=gr + 0.025, h=0.075))
    body.append(core.collar('LowerCollar', GRIP_BOT - 0.02, col, M['accent'], r=0.125, h=0.08))

    # --- heavy race pommel
    long_pommel = style.get('pommel') in ('spike', 'fang')
    psc = (1.42 if not slender else 1.3) * (0.82 if long_pommel else 1.0)
    pz = GRIP_BOT - 0.06
    body += core.pommel('Pommel', style, pz, col, M['secondary'], scale=psc)
    if shield:                      # the glow accent moves to the pommel waist when the guard carries the motif
        glow += K.pommel_gems(style, pz, psc, col, M['glow'], max_size=0.22)

    grip_a = (0, 0, (GRIP_TOP + GRIP_MID) / 2)
    grip_b = (0, 0, (GRIP_MID + GRIP_BOT) / 2)
    tip_z = ROOT + L
    return dict(body=body, glow=glow, grip=grip_a,
                attachments={'Grip': grip_a, 'GripSecondary': grip_b, 'VFX_Tip': (0, 0, tip_z),
                             'VFX_Guard': (0, 0, gz), 'VFX_Mid': (0, 0, ROOT + L * 0.5)})
