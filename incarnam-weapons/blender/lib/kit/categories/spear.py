"""Two-handed spear. Long haft + socketed race blade head (blade_outline) with collar, optional side wings.

Reads: blade dict (edge/tip/width/holes/notch/single_edge -> head outline), guard (collar plate under the head),
pommel (butt), motif (root inlay), motif2 (socket badge / charm), grip_wraps, silhouette (chunky, slender,
curve -> slight head sweep, spikes/horns/barbs/feral/thorns -> side wings, faceted, segmented, riveted, organic,
clockwork, theatrical...), mats roles (primary head, secondary socket/guard, accent bands/inlays, haft, grip,
glow = socket gem).
"""
import math

from shapely.geometry import box
from shapely.ops import transform, unary_union

import core
import geo
from categories import _polearm as P

SOCKET_Z = 4.5            # haft top / socket base
GRIP_A, GRIP_B = 1.2, 2.6


def wings_wanted(style):
    s = P.sil(style)
    return bool(s.get('spikes') or s.get('horns') or s.get('barbs') or s.get('feral'))


def wing_shape(style, c, root_z):
    """Pair of short back-swept side blades rooted in the socket top (partisan-like lugs)."""
    bl = style.get('blade', {})
    s = P.sil(style)
    out = []
    wl = 0.42 * c
    ww = 0.13 * c
    w = core.blade_outline(wl, ww, edge='leaf' if bl.get('edge') in ('leaf', 'wavy') else 'straight',
                           tip='hook' if s.get('horns') else 'point')
    ang = 58 if not s.get('horns') else 40
    for sx in (1, -1):
        piece = core.place(w if sx > 0 else core.mirror(w), 0, 0, rot=-sx * ang)
        out.append(core.place(piece, sx * 0.03, root_z))
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


def barb_shape(style, c, z, x_edge):
    """Harpoon barbs: short hooks pointing back down the haft (riveted / steam races)."""
    out = []
    w = core.blade_outline(0.3 * c, 0.11 * c, edge='straight', tip='point')
    for sx in (1, -1):
        piece = core.place(w if sx > 0 else core.mirror(w), 0, 0, rot=-sx * 128)
        out.append(core.place(piece, sx * x_edge * 0.8, z))
    return unary_union(out).buffer(0)


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    bl = style.get('blade', {})
    c = P.chunk(style)
    r = P.haft_r(style)
    seg = P.haft_segments(style)
    body, glow = [], []

    # ---------------------------------------------------------------- haft, grip, butt
    body += P.haft(style, ctx, 0.0, SOCKET_Z + 0.05, keep_clear=[(GRIP_A, GRIP_B)])
    body += P.grip_zone(style, ctx, GRIP_A, GRIP_B)
    body += P.butt(style, ctx, 0.0)

    # ---------------------------------------------------------------- socket (tapered ferrule) + collar
    sz0, sz1 = SOCKET_Z - 0.32, SOCKET_Z + 0.28
    sr = r * 1.45 * (1.08 if s.get('heavy') or s.get('tool') else 1.0)
    prof = [(0.0, sz0), (r * 1.12, sz0), (sr * 0.95, sz0 + 0.16), (sr, sz0 + 0.3), (sr * 0.82, sz1 - 0.06),
            (sr * 0.62, sz1), (0.0, sz1)]
    body.append(geo.lathe('Socket', prof, segments=6 if s.get('faceted') else 8, col=col, material=M['secondary'],
                          smooth_angle=35))
    body.append(P.band('SocketBand', sz0 + 0.02, r * 1.35, col, M['accent'], h=0.07, segments=seg))
    body.append(P.band('SocketRing', sz0 + 0.3, sr * 1.08, col, M['accent'], h=0.06, segments=8))
    # langets: strips running down the haft from the socket, through the haft (front + back)
    lang = box(-0.028, sz0 - 0.34, 0.028, sz0 + 0.06)
    body.append(core.plate('Langets', lang, 2 * r + 0.03, col, M['accent'], chamfer=0.012))
    # glow gem seated in the socket front, motif2 badge on the back face
    gem_z = sz0 + 0.17
    glow.append(P.lens('SocketGem', 0.05 * c, col, M['glow'], depth=0.045, z=gem_z, y=-sr * 0.86))
    b = P.badge('SocketBadge', style, gem_z, sr * 0.98, col, M['accent'], size=0.13, side=1)
    if b is not None:
        body.append(b)

    # ---------------------------------------------------------------- head
    root = sz1 - 0.04
    L = 1.75 * (1.06 if s.get('slender') else 1.0) * (0.96 if s.get('heavy') else 1.0)
    W = 0.44 * bl.get('width', 1.0) * c ** 0.5
    shape = core.blade_outline(L, W, edge=bl.get('edge', 'leaf'), tip=bl.get('tip', 'point'),
                               holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'),
                               single_edge=bl.get('single_edge', False))
    # tang neck: narrow the blade root so it seats into the socket mouth
    shape = taper(shape, L)
    neck = core.poly([(-W * 0.18, -0.12), (W * 0.18, -0.12), (W * 0.26, 0.1), (-W * 0.26, 0.1)])
    shape = unary_union([shape, neck]).buffer(0)
    curve = s.get('curve', 0.0)
    if curve > 0.05:
        shape = core.bend(shape, curve * 0.3, z0=0.15)
    head = core.place(shape, 0, root + 0.12)
    if wings_wanted(style):
        head = unary_union([head, wing_shape(style, c, root + 0.06)]).buffer(0)
    elif s.get('riveted') or s.get('steam'):
        head = unary_union([head, barb_shape(style, c, root + 0.12 + L * 0.12, W * 0.5 * 0.8)]).buffer(0)
    body.append(core.blade('Head', head, L, col, M['primary'], thickness=0.12))
    # race guard as the collar plate at the head root
    body.append(P.guard_plate('Collar', style, 0.3 * c, 0.11 * c, root + 0.04, 0.15, col, M['secondary'],
                              chamfer=0.035, max_h=0.24))
    # race motif inlaid in the blade root (proud of both faces)
    mx = W * 0.145 if bl.get('single_edge') else 0.0     # centre of the blade face (spine side is narrow)
    m = core.motif_plate('RootMotif', style, W * 0.55, mx, root + 0.12 + L * 0.3, 0.15, col, M['accent'])
    if m is not None:
        body.append(m)
    body += P.hanging(style, ctx, sz0 + 0.02, r * 1.35)

    tip_z = root + 0.12 + L
    grip_hi = GRIP_B - 0.3
    grip_lo = GRIP_A + 0.3
    return dict(body=body, glow=glow, grip=(0, 0, grip_hi),
                attachments={'Grip': (0, 0, grip_hi), 'GripSecondary': (0, 0, grip_lo), 'VFX_Tip': (0, 0, tip_z),
                             'VFX_Socket': (0, 0, gem_z), 'VFX_Butt': (0, 0, -0.2)})
