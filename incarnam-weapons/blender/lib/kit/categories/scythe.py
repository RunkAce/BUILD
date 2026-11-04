"""Two-handed scythe. Long haft + a big curved single-edged blade sweeping out from a race socket.

Reads: blade dict (edge/tip/width/holes/notch shape the blade; the edge treatment lands on the concave cutting
edge), guard (seat plate under the socket), pommel (butt), motif (heel inlay = focal), motif2 (back fin /
finial / charm), grip_wraps, silhouette (curve -> blade curl, chunky -> scale, spikes/barbs/feral/thorns/horns ->
back spike + spur, heavy/tool/riveted/steam -> counterweight, clockwork -> gear counterweight, slender, faceted,
organic/segmented/theatrical/swashbuckler haft dressing), mats roles (primary blade, secondary socket, accent
inlays/bands, haft, grip, glow = socket cabochon).
Layout: butt at z=0, haft up to the socket, blade sweeps toward +X and curls down, back piece toward -X.
"""
import math

from mathutils import Vector
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import transform, unary_union

import core
import geo
from categories import _polearm as P

HAFT_TOP = 4.8          # top of the haft / bottom of the socket block
GRIP_A, GRIP_B = 1.0, 2.75


def _flag(s, *keys):
    return any(s.get(k) for k in keys)


def _biggest(shape):
    if shape.geom_type == 'MultiPolygon':
        return max(shape.geoms, key=lambda g: g.area)
    return shape


def _slab(name, shape, t, col, mat, bw=0.05):
    """Thick block with a two-step faceted bevel (socket blocks, counterweights)."""
    return geo.slab(name, shape=shape, core_t=t, edge_t=t * 0.55, bevel_w=bw,
                    levels=[(0.0, t * 0.28), (bw * 0.45, t * 0.42), (bw, t / 2)], col=col, material=mat,
                    smooth_angle=28)


def _chamfer_box(x0, z0, x1, z1, c):
    return core.poly([(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1),
                      (x0, z1 - c), (x0, z0 + c)])


# ------------------------------------------------------------------ blade
def blade_shape(style, c, hole_parts=None):
    """Single-edged blade, tapered, bent into an arc, rotated to sweep toward +X with the edge underneath.
    Returns (shape, L, W) with the heel (root) at x=0 spanning roughly z in [-W/2, +0.2W]."""
    bl = style.get('blade', {})
    s = P.sil(style)
    k = 0.82 + 0.18 * c
    L = 2.7 * k * (1.05 if s.get('horns') else 1.0) * (1.04 if s.get('slender') else 1.0)
    W = 0.78 * bl.get('width', 1.0) * k
    hw = W / 2
    tip = bl.get('tip', 'point')
    if tip == 'chisel':                 # a chiselled scythe reads broken: use a clipped point instead
        tip = 'clip'
    edge = bl.get('edge', 'straight')
    shape = core.blade_outline(L, W, edge=edge, tip=tip, holes='none', notch=bl.get('notch', 'none'),
                               single_edge=True, seed=len(style.get('id', '')))
    # holes sized for a scythe (kept in the broad heel half, between spine and edge)
    holes = bl.get('holes', 'none')
    cx = hw * 0.29
    if holes == 'slot':
        shape = shape.difference(core.poly([(cx - hw * 0.1, L * 0.36), (cx + hw * 0.16, L * 0.36),
                                            (cx + hw * 0.1, L * 0.56), (cx - hw * 0.0, L * 0.6),
                                            (cx - hw * 0.1, L * 0.54)]))
    elif holes == 'rings':
        for j, zz in enumerate((0.42, 0.54, 0.64)):
            shape = shape.difference(Point(cx, L * zz).buffer(hw * (0.24 - 0.04 * j), 14))
    hp = []
    if holes in core.INLAID_HOLES:      # one seated porthole / coin slot just past the heel motif
        shape, hp = core.inlaid_hole(shape, holes, L * 0.4)
    curv = 0.36 + 0.5 * s.get('curve', 0.0)
    if s.get('horns'):
        curv += 0.06

    def xf(g):
        # taper heel -> tip (scythe blades are widest at the heel)
        g = transform(lambda x, z, *a: (x * (1.0 - 0.38 * max(0.0, min(1.0, z / L)) ** 1.2), z),
                      g.segmentize(0.03)).buffer(0)
        g = core.bend(g, curv)
        # +Z -> +X (blade sweeps outward), +X (edge side, concave) -> -Z (underneath); lift the root a touch
        return affinity.rotate(g, -76, origin=(0, 0))
    shape = xf(shape)
    if hole_parts is not None:
        hole_parts += [(n_, xf(g_).buffer(0), r_) for n_, g_, r_ in hp]
    return _biggest(shape.buffer(0)), L, W


def heel_spur(style, W, c):
    """Spiky races: a backward barb on the spine just past the heel."""
    s = P.sil(style)
    if not _flag(s, 'spikes', 'barbs', 'feral', 'thorns'):
        return None
    x0 = 0.34 * c
    top = 0.2 * W
    return core.poly([(x0 - 0.1 * c, top - 0.04), (x0 + 0.12 * c, top - 0.04), (x0 - 0.16 * c, top + 0.24 * c)])


# ------------------------------------------------------------------ back piece (-X side of the socket)
def back_piece(style, ctx, zc, sx0, c, D):
    """Back spike / counterweight / fin, seated into the socket's -X wall at x=sx0 (< 0). Returns (parts, xmin)."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts = []
    if s.get('clockwork'):
        R = 0.2 * c
        g = core.GUARDS['gear'](R / 0.6, R)
        xc = sx0 - R * 0.72
        parts.append(_slab('BackGear', core.place(g, xc, zc), 0.14, col, M['primary'], bw=0.03))
        parts.append(geo.lathe('BackAxle', [(0.0, -0.11), (0.06, -0.11), (0.06, 0.11), (0.0, 0.11)], segments=8,
                               col=col, material=M['accent']))
        parts[-1].rotation_euler = (math.radians(90), 0, 0)
        parts[-1].location = (xc, 0, zc)
        stub = box(xc, zc - 0.05, sx0 + 0.04, zc + 0.05)
        parts.append(core.plate('BackStub', stub, 0.1, col, M['secondary'], chamfer=0.015))
        return parts, xc - R
    if s.get('portals'):
        # twin counter-blade: a smaller mirrored crescent sweeping the other way (duality of the pair of gates)
        cb, Lc, Wc = blade_shape(style, c)
        cb = affinity.scale(core.mirror(cb), 0.5, 0.5, origin=(0, 0))
        Lc *= 0.5
        cb = core.place(cb, sx0 + 0.1, zc - 0.02)
        parts.append(core.blade('CounterBlade', _biggest(cb.buffer(0)), Lc, col, M['primary'], thickness=0.11,
                                bevel=0.05))
        return parts, cb.bounds[0]
    if s.get('tool'):
        # prospector's pick: a long tapered beak curling down off the heel, clamped by an accent band
        Ls = 0.62 * c
        hb = 0.11 * c
        drop = 0.34 * c
        top = geo.bezier((sx0 + 0.06, zc + hb), (sx0 - Ls * 0.45, zc + hb * 0.95), (sx0 - Ls * 0.85, zc - hb * 0.1),
                         (sx0 - Ls, zc - drop), 10)
        bot = geo.bezier((sx0 - Ls, zc - drop), (sx0 - Ls * 0.78, zc - hb * 0.95), (sx0 - Ls * 0.4, zc - hb),
                         (sx0 + 0.06, zc - hb), 10)
        parts.append(core.blade('BackPick', core.poly(top + bot[1:]), Ls, col, M['primary'], thickness=0.13,
                                bevel=0.045))
        parts.append(core.plate('BackPickBand', _chamfer_box(sx0 - 0.1 * c, zc - hb * 1.3, sx0 + 0.04, zc + hb * 1.3,
                                                             0.02), 0.2, col, M['accent'], chamfer=0.02))
        return parts, sx0 - Ls
    if _flag(s, 'heavy', 'tool', 'riveted', 'steam'):
        # cylindrical counterweight along -X with a face cap and a band
        Lc = 0.42 * c
        R = 0.14 * c
        prof = [(0.0, 0.0), (R * 0.8, 0.0), (R, 0.06), (R, Lc - 0.08), (R * 1.12, Lc - 0.06), (R * 1.12, Lc),
                (R * 0.6, Lc + 0.03), (0.0, Lc + 0.03)]
        cw = geo.lathe('Counterweight', prof, segments=8, col=col, material=M['primary'], smooth_angle=30)
        cw.rotation_euler = (0, math.radians(-90), 0)          # +Z -> -X
        cw.location = (sx0 + 0.06, 0, zc)
        parts.append(cw)
        bd = core.collar('CounterBand', 0, col, M['accent'], r=R * 1.06, h=0.07, segments=8)
        bd.rotation_euler = (0, math.radians(-90), 0)
        bd.location = (sx0 + 0.06 - Lc * 0.42, 0, zc)
        parts.append(bd)
        m2 = style.get('motif2')
        if m2:
            shp = m2(R * 1.3)
            if shp is not None and not shp.is_empty:
                pl = core.plate('CounterFace', shp, 0.05, col, M['accent'], chamfer=0.012)
                core.face_on(pl)
                pl.location = (sx0 + 0.06 - Lc - 0.035, 0, zc)
                parts.append(pl)
        return parts, sx0 + 0.06 - Lc - 0.06
    if _flag(s, 'spikes', 'barbs', 'feral', 'thorns', 'horns'):
        # curved back spike: a beak sweeping out and up (horns: longer, curling higher)
        Ls = (0.7 if s.get('horns') else 0.55) * c
        lift = (0.42 if s.get('horns') else 0.2) * c
        hb = 0.11 * c
        top = geo.bezier((sx0 + 0.06, zc + hb), (sx0 - Ls * 0.4, zc + hb), (sx0 - Ls * 0.8, zc + lift * 0.5),
                         (sx0 - Ls, zc + lift), 10)
        bot = geo.bezier((sx0 - Ls, zc + lift), (sx0 - Ls * 0.7, zc + lift * 0.1), (sx0 - Ls * 0.35, zc - hb),
                         (sx0 + 0.06, zc - hb), 10)
        sp = core.poly(top + bot[1:])
        parts.append(core.blade('BackSpike', sp, Ls, col, M['primary'], thickness=0.12, bevel=0.045))
        return parts, sx0 - Ls
    # quiet races: a short fin plus the motif2 charm seated on its end
    Lf = 0.28 * c
    hb = 0.09 * c
    fin = core.poly([(sx0 + 0.05, zc - hb), (sx0 - Lf, zc - hb * 0.55), (sx0 - Lf - 0.05, zc),
                     (sx0 - Lf, zc + hb * 0.55), (sx0 + 0.05, zc + hb)])
    parts.append(_slab('BackFin', fin, 0.14, col, M['secondary'], bw=0.03))
    xmin = sx0 - Lf - 0.05
    m2 = style.get('motif2')
    if m2:
        S2 = 0.3 * c
        shp = m2(S2)
        if shp is not None and not shp.is_empty:
            b = shp.bounds
            cx = xmin + 0.04 - b[2]          # overlap the fin tip by 0.04
            parts.append(core.plate('BackCharm', core.place(shp, cx, zc), 0.1, col, M['accent'], chamfer=0.015))
            xmin = cx + b[0]
    return parts, xmin


# ------------------------------------------------------------------ build
def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    c = P.chunk(style)
    r = P.haft_r(style)
    seg = P.haft_segments(style)
    body, glow = [], []

    # --- haft, grips, butt
    zt = HAFT_TOP
    body += P.haft(style, ctx, 0.0, zt - 0.22, keep_clear=[(GRIP_A, GRIP_B)])
    body += P.grip_zone(style, ctx, GRIP_A, GRIP_B)
    body += P.butt(style, ctx, 0.0)

    # --- blade first (the socket is fitted around its heel)
    sw = 0.19 * c                                # socket half-width
    hole_parts = []
    bshape, L, W = blade_shape(style, c, hole_parts)
    bx0, bz0, bx1, bz1 = bshape.bounds
    D = 0.27                                     # socket depth (blade is 0.13 -> root hidden inside)
    zs0 = zt
    root = bshape.intersection(box(-0.01, -5, sw * 1.6, 5))
    rz0, rz1 = root.bounds[1], root.bounds[3]
    zh = zs0 + 0.2 * c - rz0                     # heel bottom sits 0.2 above the haft top
    zs1 = zh + rz1 + 0.12 * c                    # socket top just above the spine
    blade = core.place(bshape, -sw * 0.5, zh)
    spur = heel_spur(style, W, c)
    if spur is not None:
        blade = unary_union([blade, core.place(spur, -sw * 0.5, zh)]).buffer(0)
    blade = _biggest(blade)
    body.append(core.blade('Blade', blade, L, col, M['primary'], thickness=0.13, bevel=0.065))
    body += core.inlay_parts('Blade', hole_parts, col, M, 0.13, place_fn=lambda g: core.place(g, -sw * 0.5, zh))

    # --- socket: coffin-shaped clamp (secondary) tapering into the neck; race guard seat under it
    sh = zs1 - zs0
    half = [(sw * 0.62, zs1), (sw, zs1 - 0.1 * c), (sw * 1.04, zs0 + sh * 0.42), (sw * 0.62, zs0)]
    body.append(_slab('Socket', core.poly(geo.mirror_x([(0, zs1)] + half + [(0, zs0)])), D, col, M['secondary'],
                      bw=0.045))
    prof = [(0.0, zt - 0.42), (r * 1.02, zt - 0.42), (r * 1.3, zt - 0.2), (sw * 0.6, zt - 0.03), (sw * 0.64, zt + 0.06),
            (0.0, zt + 0.06)]
    body.append(geo.lathe('Neck', prof, segments=seg, col=col, material=M['accent'], smooth_angle=35))
    body.append(P.band('NeckBand', zt - 0.43, r * 1.3, col, M['accent'], h=0.06, segments=seg))
    body.append(P.guard_plate('Seat', style, sw * 1.6, 0.12 * c, zt + 0.02, D + 0.06, col, M['secondary'],
                              chamfer=0.03, max_h=0.24 * c))
    # heel band: a ferrule that hugs the blade where it leaves the socket (seated into the socket wall)
    strip = blade.intersection(box(sw - 0.04, zs0 - 1.0, sw + 0.1 * c, zs1 + 1.0))
    if not strip.is_empty:
        hb = _biggest(strip.buffer(0.035, join_style='mitre', mitre_limit=2.0))
        hb = hb.intersection(box(sw - 0.04, zs0 - 1.0, sw + 0.1 * c, zs1 + 1.0))
        body.append(core.plate('HeelBand', _biggest(hb.buffer(0)), 0.19, col, M['accent'], chamfer=0.025))
    zh_mid = zh + (rz0 + rz1) / 2

    # --- focal: race motif inlaid through the blade heel (proud of both faces)
    xa, xb = sw + 0.16 * c, sw + 0.16 * c + 0.62 * c
    heel = blade.intersection(box(xa, zh - 1.0, xb, zh + 1.0))
    fn = style.get('motif')
    if fn and not heel.is_empty:
        hb = heel.bounds
        hh = hb[3] - hb[1]
        cen = heel.centroid
        inner = blade.buffer(-0.035)
        best = None
        # upright, or laid along the blade (tall emblems like feathers read better lying with the sweep)
        for rot, base in ((0.0, min(hh * 0.8, (xb - xa) * 1.1)), (-76.0, min(hh * 1.25, (xb - xa) * 1.5))):
            size = base
            for _ in range(6):
                shp = fn(size)
                if shp is None or shp.is_empty:
                    break
                if rot:
                    shp = affinity.rotate(shp, rot, origin=(0, 0))
                b0 = shp.bounds
                mx = max(xa + (b0[2] - b0[0]) * 0.5, cen.x)
                m = core.place(shp, mx, cen.y)
                ratio = m.intersection(inner).area / max(m.area, 1e-9)
                if ratio > 0.97:
                    if best is None or m.area > best.area:
                        best = m
                    break
                size *= 0.88
        if best is not None:
            best = best.intersection(inner).buffer(0)
            if not best.is_empty and best.area > 0.004:
                body.append(core.plate('HeelMotif', best, 0.16, col, M['accent'], chamfer=0.02))

    # --- glow: cabochon on the socket front with an accent bezel (the single emissive accent)
    gz = zs0 + sh * 0.4
    gR = 0.085 * c
    bez = geo.lathe('Bezel', [(0.0, 0.0), (gR * 1.45, 0.0), (gR * 1.45, 0.03), (gR * 1.1, 0.05), (0.0, 0.05)],
                    segments=6 if s.get('faceted') else 10, col=col, material=M['accent'])
    bez.rotation_euler = (math.radians(90), 0, 0)
    bez.location = (0, -D / 2 + 0.02, gz)
    body.append(bez)
    glow.append(P.lens('Gem', gR, col, M['glow'], depth=0.07, segments=6 if s.get('faceted') else 10, x=0,
                       z=gz, y=-D / 2 - 0.02))

    # --- back spike / counterweight / fin toward -X
    bp, xmin = back_piece(style, ctx, zh_mid + 0.04, -sw, c, D)
    body += bp

    # --- finial on the socket top
    cap = [(0.0, zs1 - 0.04), (sw * 0.62, zs1 - 0.04), (sw * 0.7, zs1 + 0.02), (sw * 0.45, zs1 + 0.08),
           (0.0, zs1 + 0.09)]
    body.append(geo.lathe('Cap', cap, segments=seg, col=col, material=M['accent'], smooth_angle=35))
    top = zs1 + 0.09
    if _flag(s, 'spikes', 'barbs', 'feral', 'thorns'):
        body.append(P.spike('TopSpike', (0, 0, zs1 + 0.05), (0, 0, 1), 0.34 * c, 0.055 * c, col, M['primary']))
        top = zs1 + 0.05 + 0.34 * c
    elif s.get('horns'):
        for sx in (1, -1):
            body.append(P.spike(f'TopHorn{sx}', (sx * sw * 0.4, 0, zs1 + 0.03), (sx * 0.5, 0, 1), 0.26 * c,
                                0.05 * c, col, M['primary']))
        top = zs1 + 0.25 * c
    else:
        body.append(P.gem('TopBead', zs1 + 0.12, 0.06 * c, col, M['accent'], faceted=bool(s.get('faceted')),
                          segments=6 if s.get('faceted') else 8))
        top = zs1 + 0.12 + 0.06 * c

    # --- neck badge + hanging charm (theatrical / swashbuckler / segmented races), opposite the blade
    b = P.badge('NeckBadge', style, zt - 0.72, r * 1.3, col, M['accent'], size=0.14)
    if b is not None:
        body.append(P.band('NeckBadgeBand', zt - 0.72, r * 1.3, col, M['secondary'], h=0.12, segments=seg))
        body.append(b)
    body += P.hanging(style, ctx, zt - 0.5, -r * 1.3)

    grip_hi = GRIP_B - 0.3
    grip_lo = GRIP_A + 0.3
    tip = max(bshape.exterior.coords, key=lambda p: p[0])
    return dict(body=body, glow=glow, grip=(0, 0, grip_hi),
                attachments={'Grip': (0, 0, grip_hi), 'GripSecondary': (0, 0, grip_lo),
                             'VFX_Head': (0, 0, gz), 'VFX_Tip': (tip[0] - sw * 0.5, 0, tip[1] + zh),
                             'VFX_Blade': ((sw + bx1) * 0.5, 0, zh - W * 0.3), 'VFX_Butt': (0, 0, -0.2)})
