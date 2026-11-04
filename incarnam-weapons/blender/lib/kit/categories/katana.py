"""Katana: single-edged curved blade, race-styled tsuba, long wrapped tsuka, kashira cap.

Structure (z up): a single-edged blade (edge on -X, thick spine on +X) whose edge texture follows the race edge,
whose kissaki follows the race tip (point/clip -> classic kissaki, chisel -> angular tanto point, hook -> beaked
tip, split -> swallowtail), with race negative space (slot -> long bo-hi window, rings -> spine portholes) and
race notch (teeth -> saw spine, scoop -> back notch), swept into a sori with core.bend (more for curving races);
a raised spine strip; the race motif as a horimono inlay above the habaki; an accent habaki carrying the motif2
glow gem (single emissive accent); a horizontal tsuba = race base form + the race guard outline, with motif2
sukashi cut-outs and an accent rim between seppa washers; an oval diamond-wrapped tsuka with motif menuki; and
a kashira cap flavoured by the race pommel.
Reads: blade dict, guard, pommel, grip_wraps, motif, motif2, silhouette (chunky, slender, heavy/tool, curve,
spikes, round/organic/portals, faceted, clockwork, riveted, theatrical/swashbuckler), mats roles."""
import math

from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

import core
import geo
from categories import _bladekit as K
from categories import _polearm as P

ROOT = 0.16                      # blade root (top of the habaki seat)
TSUBA_Z = 0.0
TSUKA_TOP, TSUKA_BOT = -0.08, -1.22
FLAT = 0.8                       # oval tsuka cross-section (Y / X)


def _edge_x(edge, t, i, xe, seed=3):
    """Cutting-edge x (negative) at parameter t along the body, with the race edge texture."""
    w = 1.0 - 0.16 * t
    if edge == 'leaf':
        w *= 0.92 + 0.16 * math.sin(math.pi * min(1.0, t * 1.05))
    elif edge == 'broad':         # katana keeps its taper: broad races only lose the narrowing
        w *= 1.0 + 0.1 * t
    elif edge == 'wavy':
        w *= 0.93 + 0.1 * math.sin(t * math.pi * 7)
    elif edge == 'crystal':
        w *= 0.9 + 0.14 * (1 if i % 4 < 2 else 0)
    elif edge == 'jagged':
        w *= 0.88 + 0.16 * (((i * 7 + seed) % 5) / 4)
    elif edge == 'serrated' and 0.12 < t < 0.88:
        w *= 1.0 if i % 2 == 0 else 0.86
    return xe * w


def outline(L, W, bl):
    """Katana blade (root z=0 .. tip z=L), spine on +X (straight), edge on -X."""
    edge, tip = bl.get('edge', 'straight'), bl.get('tip', 'point')
    xs, xe = W * 0.4, -W * 0.6
    tl = L * (0.17 if tip in ('point', 'clip') else 0.13)
    Lb = L - tl
    n = 40
    edge_pts = [(_edge_x(edge, i / n, i, xe), Lb * i / n) for i in range(n + 1)]
    xe_t = edge_pts[-1][0]
    spine_top = Lb + tl * 0.45
    if tip == 'chisel':           # tanto-like angular point
        tip_pts = [(xe_t * 0.95, Lb + tl * 0.18), (xs * 0.7, L)]
        spine_top = L - tl * 0.12
    elif tip == 'hook':           # beaked tip curling over the edge
        tip_pts = geo.bezier((xe_t, Lb), (xe_t * 1.05, Lb + tl * 0.45), (xe_t * 1.2, Lb + tl * 0.8),
                             (xe_t * 1.05, L), 8)[1:]
        tip_pts += geo.bezier((xe_t * 1.05, L), (xe_t * 0.4, L - tl * 0.05), (xs * 0.6, Lb + tl * 0.7),
                              (xs, Lb + tl * 0.3), 8)[1:-1]
        spine_top = Lb + tl * 0.3
    elif tip == 'split':          # swallowtail
        tip_pts = [(xe_t * 0.9, Lb + tl * 0.55), (xe_t * 0.55, L * 0.995), (xe_t * 0.1, Lb + tl * 0.55),
                   (xs * 0.45, L)]
        spine_top = Lb + tl * 0.62
    else:                         # classic kissaki (point / clip)
        tip_pts = geo.bezier((xe_t, Lb), (xe_t * 1.0, Lb + tl * 0.62), (xs * 0.2, L - tl * 0.05),
                             (xs * 0.62, L), 10)[1:]
    spine = [(xs, spine_top), (xs, 0.0)]
    shape = core.poly(edge_pts + tip_pts + spine)
    notch = bl.get('notch', 'none')
    if notch == 'teeth':          # saw-back near the root
        teeth = [core.poly([(xs - 0.01, z), (xs + W * 0.22, z + 0.04), (xs - 0.01, z + 0.11)])
                 for z in (L * 0.2, L * 0.27, L * 0.34)]
        shape = unary_union([shape] + teeth)
    elif notch == 'scoop':        # back notch under the kissaki
        zc = Lb * 0.86
        shape = shape.difference(Point(xs + W * 0.08, zc).buffer(W * 0.26, 16))
    holes = bl.get('holes', 'none')
    if holes == 'slot':           # bo-hi window along the spine
        x0, x1 = xs - W * 0.33, xs - W * 0.15
        win = core.poly([(x0, L * 0.12), (x1, L * 0.11), (x1, L * 0.56), ((x0 + x1) / 2, L * 0.62), (x0, L * 0.56)])
        shape = shape.difference(win)
    elif holes == 'rings':        # spine portholes
        for k in range(3):
            shape = shape.difference(Point(xs - W * 0.26, L * (0.16 + 0.09 * k)).buffer(W * 0.1, 12))
    return K.largest(shape.buffer(0)), xs, xe


def tsuba_shape(style, R):
    """Race tsuba: base form from the silhouette + the race guard outline, with motif2 sukashi cut-outs."""
    s = K.sil(style)
    if K.is_round(style):
        base = Point(0, 0).buffer(R, 28)
    elif s.get('faceted'):
        base = Point(0, 0).buffer(R * 1.05, 6)
    elif s.get('clockwork'):
        base = core.GUARDS['gear'](R / 0.6, R)
    elif s.get('heavy') or s.get('tool') or s.get('riveted'):   # kaku-gata: square with well-rounded corners
        base = box(-R * 0.74, -R * 0.74, R * 0.74, R * 0.74).buffer(R * 0.22, 5)
    else:                         # four-lobed (mokko-like)
        base = unary_union([Point(dx, dz).buffer(R * 0.62, 16) for dx, dz in
                            ((R * 0.4, 0), (-R * 0.4, 0), (0, R * 0.36), (0, -R * 0.36))])
    g = core.guard_shape(style, 0.5, 0.36)
    x0, z0, x1, z1 = g.bounds
    sc = (R * 2.5) / max(x1 - x0, 1e-6)
    g = affinity.scale(affinity.translate(g, 0, -(z0 + z1) / 2), sc, min(sc, R * 1.6 / max(z1 - z0, 1e-6)),
                       origin=(0, 0))
    shape = unary_union([base, g]).buffer(0)
    shape = K.largest(shape)
    shape = core.poly(list(shape.exterior.coords)[:-1])          # drop guard-internal holes
    return shape


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    s = K.sil(style)
    ch = K.chunk(style)
    heavy, slender = K.is_heavy(style), bool(s.get('slender'))
    body, glow = [], []

    L = 3.3 + (0.14 if slender else 0.0) - (0.12 if heavy else 0.0) - (0.3 if P.tassel_kind(style) else 0.0)
    # a katana stays a katana: race width only nudges it (0.85-1.0) and chunkiness is ignored here;
    # heavy races read through a thicker kasane + mune instead of a wider (cleaver) blade
    W = 0.37 * K.clamp(bl.get('width', 1.0), 0.85, 1.0) * (0.9 if slender else 1.0)
    bt = 0.11 + (0.035 if heavy else 0.0) + 0.02 * max(0.0, min(ch, 1.15) - 1.0) / 0.15
    shape, xs, xe = outline(L, W, bl)
    # porthole / coin slot (inlaid race holes) just above the horimono
    shape, hole_parts = core.inlaid_hole(shape, bl.get('holes', 'none'), 0.17 + min(W * 0.86, 0.34) * 1.12)
    k = min(0.12, 0.05 + 0.14 * s.get('curve', 0.0))
    # spine strip (thick mune) along the back of the blade body
    strip = shape.intersection(box(xs - W * 0.15, 0.0, xs + 1.0, L * 0.8)).buffer(0)
    shape_b = core.bend(shape, k)
    strip_b = K.largest(core.bend(strip, k)) if not strip.is_empty else None
    body.append(core.blade('Blade', core.place(shape_b, 0, ROOT), L, col, M['primary'], thickness=bt, bevel=0.055))
    body += core.inlay_parts('Blade', [(n_, core.bend(g_, k), r_) for n_, g_, r_ in hole_parts], col, M, bt,
                             place_fn=lambda g: core.place(g, 0, ROOT))
    if strip_b is not None and strip_b.area > 0.01:
        body.append(core.plate('Spine', core.place(strip_b, 0, ROOT), bt + 0.025 + (0.015 if heavy else 0.0), col, M['primary'], chamfer=0.018))

    # --- habaki (accent) gripping the blade root, carrying the motif2 glow gem
    hx0, hx1 = xe - 0.045, xs + 0.045
    hab = core.poly([(hx0 - 0.015, TSUBA_Z + 0.03), (hx1 + 0.015, TSUBA_Z + 0.03), (hx1, ROOT + 0.09),
                     (hx0 + 0.05, ROOT + 0.04)])
    body.append(core.plate('Habaki', hab, bt + 0.06, col, M['accent'], chamfer=0.025))
    hc = (hx0 + hx1) / 2
    gem = core.motif_plate('HabakiGem', style, 0.14, hc, (TSUBA_Z + ROOT) / 2 + 0.04, 0.21, col, M['glow'], key='motif2')
    if gem is not None:
        glow.append(gem)
    # horimono: the race motif inlaid on the blade above the habaki (focal)
    msz = min(W * 0.86, 0.34)
    m = core.motif_plate('Horimono', style, msz, (xe + xs) / 2 + W * 0.04, ROOT + 0.09 + msz * 0.62 + 0.05, bt + 0.035,
                         col, M['accent'])
    if m is not None:
        body.append(m)

    # --- seppa + tsuba (horizontal) with accent rim and sukashi cut-outs
    R = min(0.42, 0.45 * min(ch, 1.12))
    ts = tsuba_shape(style, R)
    solid = ts
    cut = K.motif_shape(style, R * 0.44, key='motif2')
    inner = ts.buffer(-0.05)
    if cut is not None:
        for dx, dz in ((R * 0.62, 0.0), (-R * 0.62, 0.0)):
            c = core.place(cut, dx, dz)
            if inner.contains(c):
                ts = ts.difference(c)
    t_t = 0.11
    tsu = K.horizontal(core.plate('Tsuba', ts, t_t, col, M['secondary'], chamfer=0.02), TSUBA_Z)
    body.append(tsu)
    rim = solid.difference(solid.buffer(-0.035))
    body.append(K.horizontal(core.plate('TsubaRim', rim, t_t + 0.022, col, M['accent'], chamfer=0.012), TSUBA_Z))
    sr = max(abs(xe), xs) + 0.05
    for zz, nm in ((TSUBA_Z + t_t / 2 + 0.012, 'SeppaTop'), (TSUBA_Z - t_t / 2 - 0.012, 'SeppaBot')):
        body.append(K.band(nm, zz, sr, col, M['accent'], h=0.024, segments=10, scale_xy=(1, 0.55)))

    # --- tsuka: fuchi, oval diamond wrap over a pale core, menuki, kashira
    tr = 0.098 * (1.04 if heavy else 1.0)
    body.append(K.band('Fuchi', TSUKA_TOP + 0.0, tr + 0.03, col, M['accent'], h=0.1, segments=10,
                       scale_xy=(1, FLAT)))
    wraps = max(6, min(10, round(style.get('grip_wraps', 6) * 1.2)))
    body.append(K.strap_grip('Tsuka', TSUKA_BOT, TSUKA_TOP - 0.04, tr, wraps, col, M['grip'], segments=12, rpw=12,
                             flatten=FLAT, diamond=True))
    body.append(geo.lathe('TsukaCore', [(0.0, TSUKA_BOT), (tr * 1.035, TSUKA_BOT), (tr * 1.035, TSUKA_TOP - 0.04),
                                        (0.0, TSUKA_TOP - 0.04)], segments=12, col=col, material=M['haft'],
                          scale_xy=(1, FLAT)))
    zm = (TSUKA_TOP + TSUKA_BOT) / 2
    for side in (-1, 1):
        mk = core.motif_plate(f'Menuki{side + 1}', style, 0.17, 0.0, zm + side * 0.04, 0.05, col, M['accent'])
        if mk is not None:
            mk.location.y = side * (tr * FLAT + 0.012)
            body.append(mk)
    kb = TSUKA_BOT + 0.02
    pk = style.get('pommel', 'cap')
    dome = {'orb': [(tr + 0.02, kb), (tr + 0.03, kb - 0.05), (tr * 0.8, kb - 0.12), (0.0, kb - 0.15)],
            'faceted': [(tr + 0.025, kb), (tr + 0.03, kb - 0.06), (tr * 0.55, kb - 0.12), (0.0, kb - 0.13)]}.get(
        pk, [(tr + 0.022, kb), (tr + 0.03, kb - 0.06), (tr * 0.7, kb - 0.1), (0.0, kb - 0.11)])
    body.append(geo.lathe('Kashira', [(0.0, kb + 0.02), (tr + 0.02, kb + 0.02)] + dome,
                          segments=6 if pk == 'faceted' else 10, col=col, material=M['secondary'],
                          scale_xy=(1, FLAT), smooth_angle=35))
    kz = kb - 0.1
    # race pommel personality below the kashira (cap races keep the plain cap)
    if pk != 'cap':
        psc = {'spike': 0.62, 'fang': 0.66, 'orb': 0.78, 'faceted': 0.8, 'ring': 0.9}.get(pk, 0.75)
        body += core.pommel('KashiraEnd', style, kz + 0.005, col, M['accent'], scale=psc)
    # cord tassel for showy races (theatrical / swashbuckler) and a gourd charm for segmented ones
    body += P.hanging(style, ctx, kz - 0.02, 0.1, name='Sageo')

    grip_a = (0, 0, TSUKA_TOP - 0.28)
    grip_b = (0, 0, TSUKA_BOT + 0.3)
    tx, tz = max(shape_b.exterior.coords, key=lambda p: p[1])
    return dict(body=body, glow=glow, grip=grip_a,
                attachments={'Grip': grip_a, 'GripSecondary': grip_b, 'VFX_Tip': (tx, 0, ROOT + tz),
                             'VFX_Guard': (0, 0, TSUBA_Z), 'VFX_Mid': (0, 0, ROOT + L * 0.5)})
