"""Two-handed spear. Long haft + socketed race head with a broad collar plate; the head FORM is race-driven.

Head forms (head_form(style), first match wins):
  partisan  heavy / tool        broad head + boar-spear lugs (crossbar) seated through the head root
  harpoon   steam / riveted     broad head + two pairs of back-swept barbs + a line eye lug with a rope tail
  leaf      organic             leaf head with a raised midrib + a vine binding wound up the socket
  minute    clockwork           clock minute-hand lance on a motif hub, diamond counterweight under the hub
  teardrop  round               teardrop head with a halo ring bridged onto its belly
  winged    spikes/horns/barbs/feral   tapered head + a pair of back-swept side lugs
  blade     everything else     tapered race blade (blade dict edge/tip/holes/notch)

Reads: blade dict (edge/tip/width/holes/notch/single_edge -> head outline), guard (collar plate under the head),
pommel (butt), motif (root inlay / hub), motif2 (socket badge / charm), grip_wraps, silhouette flags above plus
chunky, slender, curve (slight head sweep), faceted, segmented, theatrical...; mats roles (primary head, secondary
socket/collar/lugs, accent bands/inlays/halo, haft, grip, glow = socket gem).
"""
import math

from mathutils import Vector
from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.ops import transform, unary_union

import core
import geo
from categories import _polearm as P

SOCKET_Z = 4.0            # haft top / socket base (total ~6.0-6.4 studs with head + butt)
GRIP_A, GRIP_B = 1.05, 2.45
HEAD_W = 0.66             # head width factor (x blade width x chunk**0.5)
COLLAR_W = 0.5            # collar guard plate target width (studs, x chunk**0.5)


def head_form(style):
    s = P.sil(style)
    if s.get('heavy') or s.get('tool'):
        return 'partisan'
    if s.get('steam') or s.get('riveted'):
        return 'harpoon'
    if s.get('organic'):
        return 'leaf'
    if s.get('clockwork'):
        return 'minute'
    if s.get('round'):
        return 'teardrop'
    if s.get('spikes') or s.get('horns') or s.get('barbs') or s.get('feral'):
        return 'winged'
    return 'blade'


def fit_width(shape, target):
    x0, _, x1, _ = shape.bounds
    w = x1 - x0
    if w <= 1e-6:
        return shape
    return affinity.scale(shape, xfact=target / w, yfact=min(1.0, target / w) ** 0.5, origin=(0, 0))


def wing_shape(style, c, W, root_z):
    """Pair of short back-swept side blades rooted in the socket top (partisan-like lugs)."""
    bl = style.get('blade', {})
    s = P.sil(style)
    out = []
    wl = 0.52 * c
    ww = 0.17 * c
    w = core.blade_outline(wl, ww, edge='leaf' if bl.get('edge') in ('leaf', 'wavy') else 'straight',
                           tip='hook' if s.get('horns') else 'point')
    ang = 58 if not s.get('horns') else 40
    for sx in (1, -1):
        piece = core.place(w if sx > 0 else core.mirror(w), 0, 0, rot=-sx * ang)
        out.append(core.place(piece, sx * W * 0.12, root_z))
    return unary_union(out).buffer(0)


def taper(shape, L, shoulder=0.3, root=0.5, tip=0.42):
    """Turn a sword-like outline into a spearhead: narrow root, widest at the shoulder, long taper to the tip.
    Scales x by height, so edge treatments, holes and notches survive."""
    def f(x, z):
        t = max(0.0, min(1.0, z / L))
        k = root + (1 - root) * (t / shoulder) if t < shoulder else 1 - (1 - tip) * (t - shoulder) / (1 - shoulder)
        return x * k, z

    def fx(xs, zs):
        out = [f(x, z) for x, z in zip(xs, zs)]
        return [p[0] for p in out], [p[1] for p in out]
    return transform(fx, shape.segmentize(0.04)).buffer(0)


def barb_pair(c, z, x_edge, size=1.0):
    """Harpoon barbs: hooks pointing back down the haft, rooted inside the head edge."""
    out = []
    w = core.blade_outline(0.46 * c * size, 0.16 * c * size, edge='straight', tip='point')
    for sx in (1, -1):
        piece = core.place(w if sx > 0 else core.mirror(w), 0, 0, rot=-sx * 124)
        out.append(core.place(piece, sx * x_edge, z))
    return unary_union(out).buffer(0)


def teardrop(L, W):
    """Round belly low on the head, drawn up into a point."""
    R = W * 0.5
    zc = R * 1.05
    right = geo.bezier((R, zc), (R, zc + R * 0.9), (R * 0.42, L * 0.7), (0.0, L), 12)
    belly = geo.arc(0, zc, R, 0, -180, 16)       # right side round the bottom to the left
    left_up = [(-x, z) for x, z in right][:-1]   # (-R, zc) up to just below the tip
    shape = core.poly(list(reversed(right)) + belly[1:-1] + left_up)
    neck = core.poly([(-W * 0.16, -0.12), (W * 0.16, -0.12), (W * 0.24, zc * 0.3), (-W * 0.24, zc * 0.3)])
    return unary_union([shape, neck]).buffer(0), zc, R


def minute_hand(L, W, c):
    """Clock minute-hand lance: tapered stem, a broad arrow-diamond near the tip; built from z=0 at the hub."""
    hw = W * 0.5
    stem = 0.3 * hw + 0.03
    pts = [(stem, 0.0), (stem * 0.62, L * 0.58), (hw * 0.95, L * 0.72), (0.0, L), (-hw * 0.95, L * 0.72),
           (-stem * 0.62, L * 0.58), (-stem, 0.0)]
    lance = core.poly(pts)
    # small lozenge window in the arrow (clock-hand cut-out)
    win = core.poly([(0, L * 0.67), (hw * 0.24, L * 0.73), (0, L * 0.81), (-hw * 0.24, L * 0.73)])
    return lance.difference(win).buffer(0)


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    bl = style.get('blade', {})
    c = P.chunk(style)
    r = P.haft_r(style)
    seg = P.haft_segments(style)
    form = head_form(style)
    body, glow = [], []

    # ---------------------------------------------------------------- haft, grip, butt
    body += P.haft(style, ctx, 0.0, SOCKET_Z + 0.05, keep_clear=[(GRIP_A, GRIP_B)])
    body += P.grip_zone(style, ctx, GRIP_A, GRIP_B)
    body += P.butt(style, ctx, 0.0)

    # ---------------------------------------------------------------- socket (tapered ferrule) + collar
    sz0, sz1 = SOCKET_Z - 0.36, SOCKET_Z + 0.3
    sr = r * 1.85 * (1.08 if form in ('partisan', 'harpoon') else 1.0)
    prof = [(0.0, sz0), (r * 1.12, sz0), (sr * 0.92, sz0 + 0.17), (sr, sz0 + 0.32), (sr * 0.84, sz1 - 0.07),
            (sr * 0.62, sz1), (0.0, sz1)]
    body.append(geo.lathe('Socket', prof, segments=6 if s.get('faceted') else 8, col=col, material=M['secondary'],
                          smooth_angle=35))
    body.append(P.band('SocketBand', sz0 + 0.02, r * 1.4, col, M['accent'], h=0.08, segments=seg))
    body.append(P.band('SocketRing', sz0 + 0.32, sr * 1.08, col, M['accent'], h=0.07, segments=8))
    # langets: strips running down the haft from the socket, through the haft (front + back)
    lang = box(-0.032, sz0 - 0.38, 0.032, sz0 + 0.06)
    body.append(core.plate('Langets', lang, 2 * r + 0.03, col, M['accent'], chamfer=0.012))
    # glow gem seated in the socket front, motif2 badge on the back face
    gem_z = sz0 + 0.19
    glow.append(P.lens('SocketGem', 0.06 * c, col, M['glow'], depth=0.05, z=gem_z, y=-sr * 0.86))
    b = P.badge('SocketBadge', style, gem_z, sr * 0.98, col, M['accent'], size=0.15, side=1)
    if b is not None:
        body.append(b)

    # ---------------------------------------------------------------- head
    root = sz1 - 0.04
    hz = root + 0.12                     # head outline z=0
    L = 1.55 * (1.06 if s.get('slender') else 1.0)
    W = HEAD_W * bl.get('width', 1.0) * c ** 0.5
    extra = []                           # (name, shape, role, thickness)
    inlays = []                          # inlaid_hole() parts (head-local 2D)
    motif_at = (0.0, hz + L * 0.3, W * 0.5)
    if form == 'teardrop':
        shape, zc, R = teardrop(L, W * 1.05)
        motif_at = (0.0, hz + zc, R * 1.1)
        # halo ring round the belly, bridged onto the head at both sides (never floating)
        rr = R * 1.42
        halo = Point(0, zc).buffer(rr, 32).difference(Point(0, zc).buffer(rr - 0.055 * c, 32))
        bridges = [LineString([(sx * R * 0.85, zc), (sx * (rr - 0.02), zc)]).buffer(0.03 * c, cap_style=2)
                   for sx in (1, -1)]
        extra.append(('Halo', core.place(unary_union([halo] + bridges).buffer(0), 0, hz), 'accent', 0.09))
    elif form == 'minute':
        hub_r = W * 0.42
        hc = hub_r * 0.95                # hub centre above the head root (clear of the collar)
        shape = minute_hand(L - hc, W, c)
        shape = core.place(shape, 0, hc)
        hub = Point(0, 0).buffer(hub_r, 24)
        # counterweight: a diamond under the hub, wider than the socket mouth
        cw = core.poly([(0, -hub_r * 1.55), (hub_r * 0.62, -hub_r * 0.55), (0, -hub_r * 0.1),
                        (-hub_r * 0.62, -hub_r * 0.55)])
        shape = unary_union([shape, core.place(hub, 0, hc)]).buffer(0)
        extra.append(('Counterweight', core.place(cw, 0, hz + hc), 'secondary', 0.15))
        extra.append(('HubRim', core.place(Point(0, 0).buffer(hub_r * 1.08, 24).difference(
            Point(0, 0).buffer(hub_r * 0.84, 24)), 0, hz + hc), 'accent', 0.15))
        motif_at = (0.0, hz + hc, hub_r * 1.45)
    elif form == 'leaf':
        shape = core.blade_outline(L, W * 1.08, edge='leaf', tip='point', notch=bl.get('notch', 'none'))
        shape = taper(shape, L, shoulder=0.38, root=0.45, tip=0.35)
        rib = core.poly([(-0.025, L * 0.05), (0.025, L * 0.05), (0.012, L * 0.86), (-0.012, L * 0.86)])
        extra.append(('Midrib', core.place(rib, 0, hz), 'accent', 0.15))
        motif_at = (0.0, hz + L * 0.22, W * 0.42)
    else:
        edge = bl.get('edge', 'leaf')
        tip = bl.get('tip', 'point')
        if form == 'partisan' and tip not in ('spade', 'chisel'):
            edge = 'broad'
        if form == 'harpoon':
            tip = 'point'                # harpoons need a clean piercing point; the barbs carry the width
        wk = {'partisan': 1.08, 'harpoon': 0.72}.get(form, 1.0)
        shape = core.blade_outline(L, W * wk, edge=edge, tip=tip,
                                   holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'),
                                   single_edge=bl.get('single_edge', False))
        shape = taper(shape, L, root=0.55 if form in ('partisan', 'harpoon') else 0.5, tip=0.42)
        # porthole / coin slot: one seated hole just above the root motif zone
        shape, inl = core.inlaid_hole(shape, bl.get('holes', 'none'), L * 0.42, size=0.9)
        inlays = inl
    # tang neck: narrow the blade root so it seats into the socket mouth
    neck = core.poly([(-W * 0.16, -0.12), (W * 0.16, -0.12), (W * 0.24, 0.1), (-W * 0.24, 0.1)])
    shape = unary_union([shape, neck]).buffer(0)
    if form == 'blade' or form == 'winged':
        curve = s.get('curve', 0.0)
        if curve > 0.05:
            shape = core.bend(shape, curve * 0.3, z0=0.15)
    head = core.place(shape, 0, hz)
    if form == 'winged':
        head = unary_union([head, wing_shape(style, c, W, root + 0.06)]).buffer(0)
    elif form == 'harpoon':
        barbs = []
        for t, size in ((0.12, 1.0), (0.46, 0.85)):
            wa = core._width_at(head, hz + L * t)
            hwl = wa[1] if wa else W * 0.3
            barbs.append(barb_pair(c, hz + L * t, hwl * 0.5, size))
        head = unary_union([head] + barbs).buffer(0)
    if head.geom_type == 'MultiPolygon':
        head = max(head.geoms, key=lambda g: g.area)
    body.append(core.blade('Head', head, L, col, M['primary'], thickness=0.13))
    body += core.inlay_parts('Head', inlays, col, M, 0.13, place_fn=lambda g: core.place(g, 0, hz))
    for nm, shp, role, t in extra:
        body.append(core.plate(nm, shp, t, col, M[role], chamfer=0.022))

    # race guard as the collar plate at the head root (~0.5 stud wide so the junction reads at distance)
    g = core.guard_shape(style, 0.3 * c, 0.11 * c)
    x0, z0, x1, z1 = g.bounds
    if z1 - z0 > 0.26:
        g = affinity.scale(g, xfact=1.0, yfact=0.26 / (z1 - z0), origin=(0, 0))
    g = fit_width(g, COLLAR_W * c ** 0.5)
    body.append(core.plate('Collar', core.place(g, 0, root + 0.04), 0.17, col, M['secondary'], chamfer=0.035))

    # form-specific dressing
    if form == 'partisan':
        # boar-spear lugs: a crossbar through the head root, ends flared into blunt lug tips
        lw = W * 0.4 + 0.08
        lug = unary_union([box(-lw, -0.045, lw, 0.045)] +
                          [core.poly([(sx * lw * 0.7, -0.05), (sx * (lw + 0.1), -0.09), (sx * (lw + 0.06), 0.03),
                                      (sx * lw * 0.7, 0.06)]) for sx in (1, -1)]).buffer(0)
        lz = sz0 + 0.3
        body.append(core.plate('Lugs', core.place(lug, 0, lz), 0.15, col, M['secondary'], chamfer=0.03))
        for sx in (1, -1):
            body.append(P.gem(f'LugRivet{sx}', lz, 0.03, col, M['accent'], segments=6,
                              x=sx * lw * 0.72, y=-0.07))
    elif form == 'harpoon':
        # line eye: a bolted lug on the socket's +X side with a ring and a short rope tail
        ez = sz0 + 0.32
        lug = unary_union([box(sr * 0.6, ez - 0.07, sr + 0.12, ez + 0.07),
                           Point(sr + 0.14, ez).buffer(0.09, 16)]).difference(Point(sr + 0.14, ez).buffer(0.045, 12))
        body.append(core.plate('LineEye', lug.buffer(0), 0.07, col, M['accent'], chamfer=0.015))
        ex = sr + 0.14
        pts = [Vector((ex, 0, ez - 0.045)), Vector((ex + 0.04, -0.01, ez - 0.16)),
               Vector((ex + 0.02, -0.02, ez - 0.32)), Vector((ex - 0.05, -0.01, ez - 0.46)),
               Vector((ex - 0.08, 0.0, ez - 0.6))]
        body.append(geo.sweep('Line', pts, 0.022, sides=5, col=col, material=M['grip'], smooth_angle=60))
        body.append(geo.lathe('LineKnot', [(0.0, ez - 0.66), (0.035, ez - 0.64), (0.04, ez - 0.58),
                                           (0.0, ez - 0.55)], segments=6, col=col, material=M['grip']))
    elif form == 'leaf':
        # vine binding: wound up the socket and onto the head root, ends tucked in
        za, zb = sz0 + 0.05, root + 0.2
        n, turns = 40, 2.6
        pts, radii = [], []
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t
            z = za + (zb - za) * t
            rr = sr * (0.95 + 0.2 * t) if z < sz1 else W * 0.22
            rr *= 0.8 if i in (0, n) else 1.0
            pts.append(Vector((rr * math.cos(a), rr * math.sin(a), z)))
            radii.append(0.026 * (0.55 + 0.45 * math.sin(math.pi * t)))
        body.append(geo.sweep('Vine', pts, 0.026, sides=5, col=col, material=M['haft'], radii=radii))
        for j, (t, sx) in enumerate(((0.3, 1), (0.62, -1))):
            z = za + (zb - za) * t
            leaf = core.blade_outline(0.24, 0.1, edge='leaf', tip='point')
            leaf = core.place(leaf, 0, 0, rot=-sx * 62)
            body.append(core.plate(f'VineLeaf{j}', core.place(leaf, sx * sr * 0.8, z), 0.04, col, M['primary'],
                                   chamfer=0.01, y=-0.02))
    elif form == 'minute':
        # tick ring round the socket mouth
        for k in range(8):
            a = 2 * math.pi * k / 8
            body.append(P.gem(f'Tick{k}', sz1 - 0.08, 0.022, col, M['accent'], segments=4,
                              x=math.cos(a) * sr * 0.92, y=math.sin(a) * sr * 0.92))

    # race motif inlaid in the head (proud of both faces)
    mx, mz, msz = motif_at
    if form in ('blade', 'winged', 'partisan', 'harpoon') and bl.get('single_edge'):
        mx = W * 0.145                   # centre of the blade face (spine side is narrow)
    m = core.motif_plate('RootMotif', style, msz, mx, mz, 0.17, col, M['accent'])
    if m is not None:
        body.append(m)
    body += P.hanging(style, ctx, sz0 + 0.02, r * 1.4)

    tip_z = head.bounds[3]
    grip_hi = GRIP_B - 0.3
    grip_lo = GRIP_A + 0.3
    return dict(body=body, glow=glow, grip=(0, 0, grip_hi),
                attachments={'Grip': (0, 0, grip_hi), 'GripSecondary': (0, 0, grip_lo), 'VFX_Tip': (0, 0, tip_z),
                             'VFX_Socket': (0, 0, gem_z), 'VFX_Butt': (0, 0, -0.2)})
