"""Chain weapon usable at range: a held HANDLE (body) and a thrown HEAD (separate piece 'Head'), joined at runtime by
the WarlinkChain system, which strings style['chain_link'] links between the two 'ChainEnd' attachments.

Handle (z up, grip at the origin side): race pommel, wrapped grip between collars, race guard with a glow lens
pair (the single emissive accent), a chain REEL (flanges + core with motif2 badges; gear / bamboo / riveted /
spiked / rounded variants), then an eyelet lug carrying a seated end ring; ChainEnd = top of that ring.

Head (built beside the handle at +X, pointing up): one of
  dart    chain-blade / rope-dart: race blade outline (edge/tip/holes/notch) on a langet socket with the motif
          inlay, race guard, ferrule, eyelet + ring at the tail (ChainEnd)        [default]
  sickle  thrown kama: short haft with a hooked single-edge race blade bent off a motif socket block, back spur
          for spiky races, eyelet + ring at the haft tail                         [curving / hooked / horned / feral]
  weight  meteor weight: a chunky emblem slab (the race motif itself when compact, else a race-shaped puck
          carrying the motif inlay), motif2 boss, gear teeth / rivets / flanges, eyelet + ring on top
                                                                                  [heavy / tool / riveted / clockwork /
                                                                                   round / portals / segmented]
Override with style['head']['chain'] = 'dart' | 'sickle' | 'weight'.
"""
import math

from mathutils import Matrix, Vector
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

import core
import geo
from categories import _bladekit as B
from categories import _polearm as P

HX = 0.9          # head display offset along +X (keeps the head clear of the handle: no hidden-face culling)


def head_kind(style):
    k = style.get('head', {}).get('chain')
    if k in ('dart', 'sickle', 'weight'):
        return k
    s = B.sil(style)
    bl = style.get('blade', {})
    if s.get('heavy') or s.get('tool') or s.get('riveted') or s.get('clockwork') or s.get('round') or \
            s.get('portals') or s.get('segmented'):
        return 'weight'
    if s.get('curve', 0.0) >= 0.2 or bl.get('tip') == 'hook' or s.get('horns') or s.get('feral'):
        return 'sickle'
    return 'dart'


def xform(objs, mtx):
    for o in objs:
        if o is not None:
            o.matrix_basis = mtx @ o.matrix_basis
    return objs


# ------------------------------------------------------------------ shared: eyelet lug + seated end ring
def lug_shape(style, R, neck_w, neck_len, up=True):
    """Eyelet lug outline centred on its hole at (0, 0); neck runs toward -Z (up=True) or +Z (up=False)."""
    s = B.sil(style)
    if s.get('faceted') or s.get('clockwork'):
        head = core.poly([(R * math.cos(math.radians(90 + 60 * i)), R * math.sin(math.radians(90 + 60 * i)))
                          for i in range(6)])
    elif B.is_heavy(style):
        c = R * 0.35
        head = core.poly([(-R, -R), (R, -R), (R, R - c), (R - c, R), (-R + c, R), (-R, R - c)])
    elif B.is_spiky(style):
        head = unary_union([Point(0, 0).buffer(R, 14), core.poly([(-R * 0.6, R * 0.6), (0, R * 1.55),
                                                                   (R * 0.6, R * 0.6)])])
    else:
        head = Point(0, 0).buffer(R, 18)
    neck = box(-neck_w / 2, -neck_len, neck_w / 2, 0)
    shp = unary_union([head, neck]).buffer(0.01).buffer(-0.01)
    if not up:
        shp = affinity.scale(shp, 1, -1, origin=(0, 0))
    return shp


def eyelet(name, style, ctx, x, zh, up=True, R=0.1, hole=0.05, neck_len=0.14, mat=None, ring_mat=None):
    """Lug with an eyelet hole centred (x, zh) + an end ring looped through the outer bar.
    Returns (parts, chain_end_point)."""
    col, M = ctx['col'], ctx['mats']
    shp = lug_shape(style, R, R * 1.1, neck_len, up).difference(Point(0, 0).buffer(hole, 14))
    parts = [core.plate(f'{name}Lug', core.place(shp, x, zh), 0.1, col, mat or M['secondary'], chamfer=0.022)]
    sgn = 1 if up else -1
    bar_mid = hole + (R - hole) * 0.5                     # centre line of the outer bar of the lug
    rc = zh + sgn * bar_mid
    rr = bar_mid * 0.98                                   # ring passes through the hole centre
    wire = min(0.022, hole * 0.42)
    ring = geo.ring(f'{name}Ring', rr, wire, sides=6, samples=18, col=col, material=ring_mat or M['accent'],
                    axis='X')
    ring.location = (x, 0, rc)
    parts.append(ring)
    return parts, (x, 0.0, rc + sgn * rr)


# ------------------------------------------------------------------ handle (body)
def reel(style, ctx, z0, z1, c, seg):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    parts = []
    rf, rc_ = 0.17 * c, 0.095 * c
    fh = 0.07
    rounded = B.is_round(style)
    # core drum
    if s.get('segmented'):
        prof = [(0.0, z0), (rc_, z0), (rc_ * 1.15, (z0 + z1) / 2 - 0.02), (rc_ * 1.25, (z0 + z1) / 2),
                (rc_ * 1.15, (z0 + z1) / 2 + 0.02), (rc_, z1), (0.0, z1)]
    else:
        prof = [(0.0, z0), (rc_, z0), (rc_ * 0.92, (z0 + z1) / 2), (rc_, z1), (0.0, z1)]
    parts.append(geo.lathe('ReelCore', prof, segments=seg, col=col, material=M['primary'], smooth_angle=40))
    # flanges
    for i, zf in enumerate((z0 + fh / 2, z1 - fh / 2)):
        if s.get('clockwork'):
            g = core.GUARDS['gear'](rf * 1.6, rf)
            g = core.poly(list(B.largest(g).exterior.coords))
            g = B.fit(g, rf * 2.1)
            fl = core.plate(f'ReelFlange{i}', g, fh, col, M['secondary'], chamfer=0.012)
            parts.append(B.horizontal(fl, zf))
        else:
            if rounded:
                fp = [(0.0, zf - fh / 2), (rf * 0.85, zf - fh / 2), (rf, zf), (rf * 0.85, zf + fh / 2), (0.0, zf + fh / 2)]
            else:
                fp = [(0.0, zf - fh / 2), (rf, zf - fh / 2), (rf + 0.012, zf), (rf, zf + fh / 2), (0.0, zf + fh / 2)]
            parts.append(geo.lathe(f'ReelFlange{i}', fp, segments=seg, col=col, material=M['secondary'],
                                   smooth_angle=35))
            if B.is_mech(style):
                for j in range(6):
                    a = math.pi / 6 + j * math.pi / 3
                    parts.append(P.gem(f'ReelRivet{i}_{j}', zf + (fh / 2 if i else -fh / 2) * 0.9, 0.02, col,
                                       M['accent'], segments=6, x=math.cos(a) * rf * 0.72, y=math.sin(a) * rf * 0.72))
            if B.is_spiky(style):
                for j in range(4):
                    a = math.pi / 4 + j * math.pi / 2
                    base = Vector((math.cos(a) * rf * 0.92, math.sin(a) * rf * 0.92, zf))
                    parts.append(P.spike(f'ReelSpike{i}_{j}', base, (math.cos(a), math.sin(a), 0.25 if i else -0.25),
                                         0.1, 0.026, col, M['secondary']))
    # wound chain coils (secondary = the runtime chain link colour) hugging the flanges
    wire = 0.024
    for i, zz in enumerate((z0 + fh + wire * 0.9, z1 - fh - wire * 0.9)):
        parts.append(P.ring_h(f'ReelCoil{i}', zz, rc_ + wire * 0.55, wire, col, M['secondary'], sides=5, samples=16))
    # motif2 badges seated on the drum front and back
    for side in (-1, 1):
        b = P.badge(f'ReelBadge{side + 1}', style, (z0 + z1) / 2, rc_ * 1.12, col, M['accent'],
                    size=min(0.13 * c, (z1 - z0 - 2 * fh - 4 * wire) * 1.05), key='motif2', side=side)
        if b is not None:
            parts.append(b)
    return parts


def handle(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    c = B.chunk(style)
    seg = 6 if s.get('faceted') else (8 if B.is_mech(style) else 10)
    body, glow = [], []
    grip_bot, grip_top = -0.6, 0.1
    body.append(B.strap_grip('Grip', grip_bot, grip_top, core.GRIP_R, style.get('grip_wraps', 6), col, M['grip'],
                             segments=10, rpw=12))
    body.append(core.collar('LowerCollar', grip_bot - 0.02, col, M['accent'], r=0.112, h=0.06))
    body += core.pommel('Pommel', style, grip_bot - 0.035, col, M['secondary'], scale=0.85)
    body.append(core.collar('UpperCollar', grip_top + 0.02, col, M['accent'], r=0.115, h=0.07))
    # race guard (flattened so tall disk / tsuba guards become a collar plate) + glow lens pair
    gz = grip_top + 0.12
    g = B.largest(core.guard_shape(style, 0.26 * c, 0.12))
    x0, z0, x1, z1 = g.bounds
    sc = min(0.56 * c / max(x1 - x0, 1e-6), 0.22 / max(z1 - z0, 1e-6), 1.6)
    g = affinity.scale(g, sc, sc, origin=(0, 0))
    x0, z0, x1, z1 = g.bounds
    g = affinity.translate(g, -(x0 + x1) / 2, gz - (z0 + z1) / 2)
    gt = 0.2
    body.append(core.plate('Guard', g, gt, col, M['secondary'], chamfer=0.035))
    lr = min(0.055, (g.bounds[3] - g.bounds[1]) * 0.32)
    for side in (-1, 1):
        ln = P.lens(f'GuardLens{side + 1}', lr, col, M['glow'], depth=0.035, segments=10, z=gz, y=side * (gt / 2 - 0.01))
        if side > 0:
            ln.rotation_euler = (math.radians(-90), 0, 0)
        glow.append(ln)
        bz = geo.ring(f'LensBezel{side + 1}', lr * 1.12, 0.014, sides=5, samples=16, col=col, material=M['accent'])
        bz.location = (0, side * (gt / 2), gz)
        body.append(bz)
    # chain reel
    r0 = gz + (z1 - z0) / 2 - 0.02
    r1 = r0 + 0.38
    # neck rod: grip top -> through the guard -> into the reel (guards with a central notch still connect)
    body.append(geo.lathe('Neck', [(0.0, grip_top - 0.02), (0.07, grip_top - 0.02), (0.075, r0 + 0.04),
                                   (0.0, r0 + 0.04)], segments=seg, col=col, material=M['primary']))
    body += reel(style, ctx, r0, r1, c, seg)
    # eyelet lug + end ring on top
    parts, end = eyelet('Top', style, ctx, 0.0, r1 + 0.2, up=True, R=0.1, hole=0.05, neck_len=0.22,
                        mat=M['primary'])
    body += parts
    grip = (0.0, 0.0, (grip_bot + grip_top) / 2)
    return body, glow, grip, end


# ------------------------------------------------------------------ heads (piece)
def head_dart(style, ctx, c):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    bl = style.get('blade', {})
    parts = []
    L = 0.92 * (1.06 if s.get('slender') else 1.0)
    W = 0.36 * min(bl.get('width', 1.0), 1.15) * c * (0.88 if s.get('slender') else 1.0)
    zr = 0.12
    shp = core.blade_outline(L, W, edge=bl.get('edge', 'straight'), tip=bl.get('tip', 'point'),
                             holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'),
                             single_edge=bl.get('single_edge', False))
    shp = B.taper(shp, L, 0.28)
    if B.is_spiky(style):
        barbs = unary_union([core.poly([(sx * W * 0.4, 0.06), (sx * W * 0.95, -0.08), (sx * W * 0.45, 0.2)])
                             for sx in (1, -1)])
        shp = shp.union(barbs).buffer(0)
    parts.append(core.blade('HeadBlade', core.place(shp, HX, zr), L, col, M['primary'], thickness=0.13))
    lw = W * 0.42 + 0.05
    lang = B.langet_shape(style, HX - lw, HX + lw, zr - 0.06, zr + 0.3)
    parts.append(core.plate('HeadLanget', lang, 0.17, col, M['secondary'], chamfer=0.03))
    m = core.motif_plate('HeadMotif', style, lw * 1.55, HX, zr + 0.12, 0.2, col, M['accent'])
    if m is not None:
        parts.append(m)
    g = B.largest(core.guard_shape(style, 0.2 * c, 0.1))
    x0, z0, x1, z1 = g.bounds
    sc = min(0.42 * c / max(x1 - x0, 1e-6), 0.14 / max(z1 - z0, 1e-6), 1.6)
    g = affinity.scale(g, sc, sc, origin=(0, 0))
    x0, z0, x1, z1 = g.bounds
    gz = zr - 0.115
    parts.append(core.plate('HeadGuard', affinity.translate(g, HX - (x0 + x1) / 2, gz - (z0 + z1) / 2), 0.21, col,
                            M['secondary'], chamfer=0.03))
    # ferrule down to the tail eyelet
    fz0, fz1 = gz - 0.3, gz - 0.02
    f = geo.lathe('HeadFerrule', [(0.0, fz0), (0.06, fz0), (0.075, fz1 - 0.08), (0.09, fz1), (0.0, fz1)],
                  segments=8, col=col, material=M['primary'])
    f.location = (HX, 0, 0)
    parts.append(f)
    bd = B.band('HeadBand', fz0 + 0.12, 0.085, col, M['accent'], h=0.05, segments=8)
    bd.location = (HX, 0, 0)
    parts.append(bd)
    ep, end = eyelet('Tail', style, ctx, HX, fz0 - 0.1, up=False, R=0.085, hole=0.042, neck_len=0.12)
    return parts + ep, end


def head_sickle(style, ctx, c):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    bl = style.get('blade', {})
    parts = []
    sx = HX - 0.28                       # haft axis (blade sweeps toward +X)
    h0, h1 = -0.15, 0.55
    hr = 0.07 * (0.9 + 0.1 * c)
    hf = geo.lathe('HeadHaft', [(0.0, h0), (hr * 0.9, h0), (hr, h0 + 0.2), (hr, h1), (0.0, h1)], segments=8, col=col,
                   material=M['haft'])
    hf.location = (sx, 0, 0)
    parts.append(hf)
    wraps = B.strap_grip('HeadWrap', h0 + 0.12, h1 - 0.2, hr * 1.04, 4, col, M['grip'], segments=8, rpw=10)
    wraps.location = (sx, 0, 0)
    parts.append(wraps)
    # socket block at the haft top (carries the motif)
    bw, bz0, bz1 = 0.12 * c, h1 - 0.1, h1 + 0.24
    block = B.langet_shape(style, sx - bw, sx + bw, bz0, bz1)
    parts.append(core.plate('HeadSocket', block, 0.2, col, M['secondary'], chamfer=0.03))
    m = core.motif_plate('HeadMotif', style, bw * 1.55, sx, (bz0 + bz1) / 2 + 0.01, 0.23, col, M['accent'])
    if m is not None:
        parts.append(m)
    # hooked blade off the socket toward +X, curving down (kama)
    L = 0.78
    W = 0.26 * min(bl.get('width', 1.0), 1.15) * c
    shp = core.blade_outline(L, W, edge=bl.get('edge', 'straight'), tip=bl.get('tip', 'hook'),
                             notch=bl.get('notch', 'none'), single_edge=True)
    shp = B.taper(shp, L, 0.35)
    shp = core.bend(shp, 1.0 + s.get('curve', 0.2) * 1.2)
    shp = affinity.rotate(shp, -90, origin=(0, 0))           # +Z -> +X; spine on top, edge curling under
    zb = bz1 - 0.1
    parts.append(core.blade('HeadBlade', core.place(shp, sx + bw * 0.4, zb), L, col, M['primary'], thickness=0.12))
    if B.is_spiky(style) or s.get('horns'):
        spur = core.poly([(sx - bw * 0.6, zb - 0.05), (sx - bw * 0.6, zb + 0.07), (sx - bw - 0.2, zb + 0.14)])
        if s.get('horns'):
            spur = core.poly(geo.bezier((sx - bw * 0.6, zb - 0.06), (sx - bw - 0.12, zb - 0.06),
                                        (sx - bw - 0.22, zb + 0.08), (sx - bw - 0.16, zb + 0.2), 10) +
                             geo.bezier((sx - bw - 0.16, zb + 0.2), (sx - bw - 0.14, zb + 0.1),
                                        (sx - bw - 0.06, zb + 0.06), (sx - bw * 0.6, zb + 0.08), 10)[1:])
        parts.append(core.plate('HeadSpur', spur, 0.1, col, M['primary'], chamfer=0.02))
    top = B.band('HeadCollar', h1 - 0.1, hr * 1.35, col, M['accent'], h=0.06, segments=8)
    top.location = (sx, 0, 0)
    parts.append(top)
    bot = B.band('HeadButt', h0 + 0.03, hr * 1.3, col, M['accent'], h=0.07, segments=8)
    bot.location = (sx, 0, 0)
    parts.append(bot)
    ep, end = eyelet('Tail', style, ctx, sx, h0 - 0.12, up=False, R=0.08, hole=0.04, neck_len=0.12)
    return parts + ep, end


def head_weight(style, ctx, c):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    parts = []
    size = 0.72 * (0.9 + 0.1 * c)
    zc = 0.2
    T = 0.32
    shp = None
    mshape = B.motif_shape(style, size)
    if mshape is not None:
        f = B.largest(P.filled(mshape))
        if f.area / f.convex_hull.area > 0.8 and f.area / (size * size) > 0.42:
            shp = B.fit(f, size)                        # the emblem itself becomes the weight
    emblem_body = shp is not None
    if shp is None:
        if s.get('faceted') or s.get('clockwork'):
            shp = core.poly([(size / 2 * math.cos(math.radians(90 + 60 * i)), size / 2 * math.sin(math.radians(90 + 60 * i)))
                             for i in range(6)])
        elif B.is_heavy(style):
            q = size * 0.46
            shp = core.poly([(-q, -q * 0.8), (q, -q * 0.8), (q * 1.08, 0), (q, q * 0.8), (-q, q * 0.8), (-q * 1.08, 0)])
        else:
            shp = Point(0, 0).buffer(size / 2, 24)
    if s.get('clockwork'):
        g = core.GUARDS['gear'](size * 0.95, size * 0.5)
        shp = unary_union([shp, B.fit(core.poly(list(B.largest(g).exterior.coords)), size * 1.16)]).buffer(0)
    shp = core.place(shp, HX, zc)
    parts.append(core.blade('HeadWeight', shp, size, col, M['primary'], thickness=T, edge_t=T * 0.5, bevel=0.06))
    # rim band (secondary) seated as a thicker ring just inside the outline
    rim = shp.difference(shp.buffer(-0.05)).buffer(0)
    if not rim.is_empty and not emblem_body:
        parts.append(core.plate('HeadRim', rim, T + 0.03, col, M['secondary'], chamfer=0.015))
    # focal: motif inlay (puck) or motif2 boss (emblem body)
    if emblem_body:
        b = core.motif_plate('HeadBoss', style, size * 0.32, HX, zc, T + 0.06, col, M['accent'], key='motif2')
        if b is not None:
            parts.append(b)
    else:
        m = core.motif_plate('HeadMotif', style, size * 0.66, HX, zc, T + 0.06, col, M['accent'])
        if m is not None:
            parts.append(m)
    if B.is_mech(style) and not s.get('clockwork'):
        for j in range(6):
            a = math.radians(30 + 60 * j)
            px, pz = HX + math.cos(a) * size * 0.4, zc + math.sin(a) * size * 0.4
            if shp.buffer(-0.04).contains(Point(px, pz)):
                parts.append(B.stud(f'HeadRivet{j}', px, pz, 0.03, T + 0.08, col, M['accent']))
    # eyelet lug on top
    top = shp.bounds[3]
    ep, end = eyelet('Top', style, ctx, HX, top + 0.1, up=True, R=0.09, hole=0.045, neck_len=0.16)
    return parts + ep, end


# ------------------------------------------------------------------ build
def build(style, ctx):
    c = B.chunk(style)
    body, glow, grip, end = handle(style, ctx)
    kind = head_kind(style)
    fn = {'dart': head_dart, 'sickle': head_sickle, 'weight': head_weight}[kind]
    head, hend = fn(style, ctx, c)
    return dict(body=body, glow=glow, grip=grip,
                pieces={'Head': head},
                piece_attachments={'Head': {'ChainEnd': hend}},
                chain=dict(link=style.get('chain_link', 'box')),
                attachments={'Grip': grip, 'ChainEnd': end, 'VFX_Guard': (0, 0, grip[2] + 0.47)})
