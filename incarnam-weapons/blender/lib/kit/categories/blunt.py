"""Blunt weapon: hammer / mace / club / motif-head, picked by style['head']['blunt'].

Reads: head.blunt (kind), silhouette (chunky -> scale + length class; heavy/tool/riveted/steam -> long two-handed maul;
spikes/barbs/feral/thorns -> back pick, barbed flanges, spiked studs; playful/riveted/steam -> barrel head;
slender/portals/clockwork/swashbuckler/theatrical/faceted/round/organic/segmented -> flange, stud and head
variants), guard (head seat / club hilt guard), pommel (butt), motif (focal emblem: hammer strap, mace crest, club
plaque, the head itself), motif2 (striking-face badges, finials, charms), blade dict (flange edge read),
grip_wraps, mats roles (primary head, secondary sockets/rims/faces, accent bands/inlays, haft, grip, glow).
Long (> 4.5 studs) weapons are two-handed and carry GripSecondary.
Layout: butt at z=0, weapon points +Z, front face -Y.
"""
import math

from mathutils import Vector
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

import core
import geo
from categories import _polearm as P


def _flag(s, *keys):
    return any(s.get(k) for k in keys)


def _biggest(shape):
    if shape.geom_type == 'MultiPolygon':
        return max(shape.geoms, key=lambda g: g.area)
    return shape


def _slab(name, shape, t, col, mat, bw=0.05, y=0.0):
    """Thick part with a two-step faceted bevel (hammer blocks, emblem heads, rims)."""
    return geo.slab(name, shape=shape, core_t=t, edge_t=t * 0.55, bevel_w=bw,
                    levels=[(0.0, t * 0.28), (bw * 0.45, t * 0.42), (bw, t / 2)], col=col, material=mat,
                    smooth_angle=28, y_offset=y)


def _along_x(obj, x, z, sign=1):
    """Lathe built along +Z around z=0 -> lay it along +X (sign=1) or -X (sign=-1) at (x, 0, z)."""
    obj.rotation_euler = (0, math.radians(90 * sign), 0)
    obj.location = (x, 0, z)
    return obj


# Long two-handed variants scale their head with the haft so they read as mauls, not staves.
LONG_HEAD = dict(mace=1.4, motif=1.45, club_r=1.65, club_h=1.45)
LONG_TOP = dict(club=3.3, hammer=3.95, mace=3.6, motif=3.55)      # haft top (head socket) when long


def is_long(style):
    s = P.sil(style)
    return bool(_flag(s, 'heavy', 'tool', 'riveted', 'steam') or s.get('chunky', 1.0) >= 1.1)


def glow_fill(name, style, shp, t, col, M, y=0.0):
    """Glow seen through the emblem's openings (filled outline, shrunk), or None when it has none."""
    if P.hole_area(shp) <= 0.01 * shp.area:
        return None
    core_ = P.filled(shp).buffer(-0.012)
    if core_.is_empty:
        return None
    return core.plate(name, core_, t, col, M['glow'], chamfer=0.01, y=y)


# ------------------------------------------------------------------ heads
def head_hammer(style, ctx, zb, c, long):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    hw = (0.56 if long else 0.42) * c
    hh = (0.46 if long else 0.36) * c
    dep = (0.42 if long else 0.32) * c
    zc = zb + hh / 2 + 0.06
    barrel = bool(_flag(s, 'playful', 'riveted', 'steam'))
    back = 'flat'
    if s.get('tool'):
        back = 'pick'
    elif _flag(s, 'spikes', 'barbs', 'feral'):
        back = 'spike'
    if barrel:
        rr = hh / 2
        seg = 8 if _flag(s, 'riveted', 'steam') else 10
        prof = [(0.0, -hw), (rr * 1.12, -hw), (rr * 1.12, -hw + 0.08 * c), (rr * 0.96, -hw + 0.11 * c),
                (rr, -hw * 0.5), (rr * 1.06, 0.0), (rr, hw * 0.5), (rr * 0.96, hw - 0.11 * c),
                (rr * 1.12, hw - 0.08 * c), (rr * 1.12, hw), (0.0, hw)]
        parts.append(_along_x(geo.lathe('HeadBarrel', prof, segments=seg, col=col, material=M['primary'],
                                        smooth_angle=30), 0, zc))
        for k, xb in enumerate((-hw * 0.62, hw * 0.62)):
            parts.append(_along_x(core.collar(f'Hoop{k}', 0, col, M['accent'], r=rr * 1.04, h=0.07 * c, segments=seg),
                                  xb, zc))
        if _flag(s, 'riveted', 'steam'):
            for k, xb in enumerate((-hw * 0.62, hw * 0.62)):
                for j in range(4):
                    a = math.pi / 4 + j * math.pi / 2
                    parts.append(P.gem(f'Rivet{k}_{j}', zc + math.sin(a) * rr * 1.12, 0.026 * c, col, M['secondary'],
                                       segments=6, x=xb, y=math.cos(a) * rr * 1.12))
        face_r = rr * 1.12
        for k, sx in enumerate((1, -1)):
            parts.append(_along_x(geo.lathe(f'Face{k}', [(0.0, 0.0), (face_r * 0.96, 0.0), (face_r, 0.03),
                                                          (face_r * 0.9, 0.07), (0.0, 0.07)],
                                            segments=seg, col=col, material=M['secondary']), sx * (hw - 0.02), zc, sx))
        front_y = rr
        strap_t = None
    else:
        fl = 0.16 * c
        h2 = hh / 2
        ch = 0.05 * c
        right = [(hw - fl, h2 * 0.86), (hw - fl * 0.55, h2 * 1.1), (hw - ch, h2 * 1.1), (hw, h2 * 1.1 - ch),
                 (hw, -h2 * 1.1 + ch), (hw - ch, -h2 * 1.1), (hw - fl * 0.55, -h2 * 1.1), (hw - fl, -h2 * 0.86)]
        if back == 'flat':
            left = [(-x, z) for x, z in reversed(right)]
            # keep the outline order: right side top->bottom, then left side bottom->top
            pts = right + left
        elif back == 'spike':
            pts = right + [(-hw * 0.35, -h2 * 0.86), (-hw - 0.22 * c, -h2 * 0.05), (-hw - 0.26 * c, h2 * 0.12),
                           (-hw * 0.35, h2 * 0.86)]
        else:   # prospector's pick: long tapered beak curling down
            lo = geo.bezier((-hw * 0.3, -h2 * 0.86), (-hw * 0.8, -h2 * 0.9), (-hw * 1.25, -h2 * 1.3),
                            (-hw * 1.55, -h2 * 2.3), 8)
            up = geo.bezier((-hw * 1.55, -h2 * 2.3), (-hw * 1.3, -h2 * 0.9), (-hw * 0.9, h2 * 0.8),
                            (-hw * 0.3, h2 * 0.86), 8)
            pts = right + lo + up[1:]
        blk = core.place(core.poly(pts), 0, zc)
        parts.append(_slab('HeadBlock', blk, dep, col, M['primary'], bw=0.07 * c))
        faces = [1] if back != 'flat' else [1, -1]
        for k, sx in enumerate(faces):
            fp = core.poly(geo.mirror_x([(0, h2 * 1.16), (dep * 0.5, h2 * 1.16), (dep * 0.56, h2 * 1.1),
                                         (dep * 0.56, -h2 * 1.1), (dep * 0.5, -h2 * 1.16), (0, -h2 * 1.16)]))
            pl = core.plate(f'Face{k}', core.place(fp, 0, zc), 0.09, col, M['secondary'], chamfer=0.025)
            core.face_on(pl)
            pl.location = (sx * (hw - 0.02), 0, 0)
            parts.append(pl)
        front_y = dep / 2
        strap_t = dep + 0.04
    # striking-face badges (motif2) on the +X face (seen in the 3/4 view)
    fn2 = style.get('motif2')
    if fn2:
        shp = fn2(hh * 0.62)
        if shp is not None and not shp.is_empty:
            pl = core.plate('FaceBadge', core.place(shp, 0, zc), 0.05, col, M['accent'], chamfer=0.012)
            core.face_on(pl)
            pl.location = (hw + (0.06 if barrel else 0.075), 0, 0)
            parts.append(pl)
    # focal: race motif on a strap across the head, glow through its openings
    S = hh * (0.95 if barrel else 0.86)
    fn = style.get('motif')
    shp = core.place(fn(S), 0, zc) if fn else None
    if strap_t:
        sw = S * 0.5 + 0.035 * c
        parts.append(_slab('Strap', _chamfer_rect(-sw, zc - hh * 0.5, sw, zc + hh * 0.5, 0.03), strap_t, col,
                           M['secondary'], bw=0.03))
        if shp is not None:
            parts.append(core.plate('Emblem', shp, strap_t + 0.06, col, M['accent'], chamfer=0.02))
            g = glow_fill('Lumen', style, shp, strap_t + 0.03, col, M)
            if g is not None:
                glow.append(g)
            else:
                glow.append(P.lens('Lumen', 0.05 * c, col, M['glow'], depth=0.045, z=zc, y=-(strap_t + 0.06) / 2))
    elif shp is not None:
        # barrel: plaque seated into the curved front
        yc = -front_y * 0.9
        back_p = P.filled(shp).buffer(0.035)
        parts.append(core.plate('Plaque', back_p, front_y * 0.32, col, M['secondary'], chamfer=0.015, y=yc))
        parts.append(core.plate('Emblem', shp, 0.05, col, M['accent'], chamfer=0.012, y=yc - front_y * 0.16))
        g = glow_fill('Lumen', style, shp, 0.03, col, M, y=yc - front_y * 0.16)
        glow.append(g if g is not None else P.lens('Lumen', 0.05 * c, col, M['glow'], depth=0.045, z=zc,
                                                   y=yc - front_y * 0.16 - 0.025))
    top = zc + hh * 0.62
    if _flag(s, 'spikes', 'barbs'):
        parts.append(P.spike('TopSpike', (0, 0, zc + hh * 0.5), (0, 0, 1), 0.3 * c, 0.05 * c, col, M['primary']))
        top = zc + hh * 0.5 + 0.3 * c
    return parts, glow, zc, top, hw


def _chamfer_rect(x0, z0, x1, z1, ch):
    return core.poly([(x0 + ch, z0), (x1 - ch, z0), (x1, z0 + ch), (x1, z1 - ch), (x1 - ch, z1), (x0 + ch, z1),
                      (x0, z1 - ch), (x0, z0 + ch)])


def flange_shape(style, Rin, Rout, za, zb):
    """One radial flange in the (x>0, z) plane, base buried in the core at x=Rin."""
    s = P.sil(style)
    bl = style.get('blade', {})
    h = zb - za
    zm = (za + zb) / 2
    if _flag(s, 'barbs', 'spikes', 'feral') or bl.get('edge') in ('serrated', 'jagged'):
        # barbed hook: outer point sweeps down, teeth on the upper edge
        return core.poly([(Rin, zb), (Rout * 0.78, zb - h * 0.1), (Rout * 0.84, zb - h * 0.3),
                          (Rout * 0.95, zb - h * 0.32), (Rout, zb - h * 0.55), (Rout * 1.08, za - h * 0.08),
                          (Rout * 0.8, za + h * 0.2), (Rin, za)])
    if s.get('clockwork'):
        return core.poly([(Rin, zb), (Rout * 0.8, zb), (Rout * 0.8, zb - h * 0.18), (Rout, zb - h * 0.18),
                          (Rout, zb - h * 0.42), (Rout * 0.8, zb - h * 0.42), (Rout * 0.8, za + h * 0.42),
                          (Rout, za + h * 0.42), (Rout, za + h * 0.18), (Rout * 0.8, za + h * 0.18),
                          (Rout * 0.8, za), (Rin, za)])
    if s.get('slender'):
        # tall fletch / vane: leans out to a high point
        sh = core.poly([(Rin, zb - h * 0.05), (Rout * 1.06, zb + h * 0.1), (Rout * 0.78, zm + h * 0.05),
                        (Rout * 0.66, za + h * 0.12), (Rin, za)])
        if s.get('portals'):
            sh = sh.difference(Point((Rin + Rout) * 0.58, zm + h * 0.05).buffer((Rout - Rin) * 0.2, 12))
        return sh
    if s.get('round'):
        return Point(Rin, zm).buffer(Rout - Rin, 16).intersection(box(Rin, za, Rout + 1, zb)).union(
            box(Rin - 0.02, za, Rin + 0.02, zb))
    # default: chunky trapezoid with a notch
    return core.poly([(Rin, zb), (Rout * 0.72, zb - h * 0.04), (Rout * 1.04, zm + h * 0.06), (Rout * 1.04, zm - h * 0.06),
                      (Rout * 0.72, za + h * 0.04), (Rin, za)])


def fletched_vanes(style, ctx, Rm, z0, z1, Hm, c, k):
    """Archer's mace: three tall fletching vanes (notched feather barbs, a slight helical twist like an arrow's
    fletch) over a lower tier of three short vanes in the secondary enamel, offset 60 degrees."""
    col, M = ctx['col'], ctx['mats']
    Rin = Rm * 0.55

    def vane(Rout, h):
        za, zb = -h / 2, h / 2                    # built around z=0 so the twist pivots on the vane's centre
        A, B = Vector((Rout * 0.6, za + h * 0.1)), Vector((Rout * 1.1, zb))
        sh = core.poly([(Rin, za), (A.x, A.y), (B.x, B.y), (Rout * 0.78, zb - h * 0.02), (Rin, zb - h * 0.14)])
        e = (B - A).normalized()
        out, inn = Vector((e.y, -e.x)), Vector((-e.y, e.x))
        dep = (Rout - Rin) * 0.32
        for t in (0.36, 0.66):                    # feather barbs: slits running down-in from the outer edge
            p = A + (B - A) * t
            tri = [p + out * 0.04, p - e * 0.075 + out * 0.04, p - e * 0.12 + inn * dep]
            sh = sh.difference(core.poly([(q.x, q.y) for q in tri]))
        return _biggest(sh.buffer(0))

    parts = []
    big = vane(Rm + 0.27 * c * k, Hm * 0.9)
    small = vane(Rm + 0.15 * c * k, Hm * 0.42)
    zm_big = z0 + Hm * 0.5
    zm_small = z0 + Hm * 0.25
    for j in range(3):
        a = math.radians(90 + 120 * j)            # front (-Y, 270 deg) sits between two tall vanes
        f = core.blade(f'Vane{j}', big, Hm, col, M['primary'], thickness=0.07, bevel=0.028)
        f.rotation_euler = (math.radians(9), 0, a)
        f.location = (0, 0, zm_big)
        parts.append(f)
        a2 = a + math.pi / 3
        f2 = core.blade(f'VaneLow{j}', small, Hm * 0.5, col, M['secondary'], thickness=0.06, bevel=0.024)
        f2.rotation_euler = (math.radians(9), 0, a2)
        f2.location = (0, 0, zm_small)
        parts.append(f2)
    return parts


def halo_crown(style, ctx, Rm, z0, z1, Hm, c, k):
    """Portal mace: four gate-shaped flanges, each pierced by a round portal, rise past the cap as posts that
    carry a horizontal halo ring. Returns (parts, crest_z)."""
    col, M = ctx['col'], ctx['mats']
    Rin = Rm * 0.55
    Rout = Rm + 0.22 * c * k
    Rh = Rout * 1.08                              # the halo flares out past the flanges: a crown, not a cage
    za = z0 + Hm * 0.1
    h = z1 - za
    zr = z1 + Hm * 0.26
    pw = 0.042 * c * k
    outer = geo.bezier((Rin, za), (Rout * 1.12, za + h * 0.04), (Rout * 1.06, z1 - h * 0.12), (Rh + pw, zr + 0.02), 14)
    inner = geo.bezier((Rh - pw, zr + 0.02), (Rout * 0.8, z1 + Hm * 0.02), (Rout * 0.6, z1 - h * 0.03),
                       (Rin, z1 - h * 0.08), 10)
    sh = core.poly(outer + inner).buffer(0)
    hx = (Rm * 1.05 + Rout) / 2
    sh = sh.difference(Point(hx, za + h * 0.48).buffer((Rout - Rm * 1.05) * 0.3, 14)).buffer(0)
    parts = []
    for j in range(4):
        f = core.blade(f'Flange{j}', _biggest(sh), Hm, col, M['primary'], thickness=0.075, bevel=0.03)
        f.rotation_euler = (0, 0, math.radians(45 + 90 * j))
        parts.append(f)
    parts.append(P.ring_h('Halo', zr, Rh, 0.034 * c * k, col, M['accent'], sides=6, samples=28))
    return parts, z1 + 0.03


def head_mace(style, ctx, zb, c, long):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    k = LONG_HEAD['mace'] if long else 1.0
    Rm = 0.2 * c * k
    Hm = 0.74 * c * k
    z0, z1 = zb, zb + Hm
    zc = (z0 + z1) / 2
    faceted = bool(s.get('faceted'))
    seg = 8
    if s.get('swashbuckler'):
        # powder-keg head: staved barrel with iron hoops, studs, and a lit fuse
        Rk = Rm * 1.45
        prof = [(0.0, z0), (Rk * 0.78, z0), (Rk * 0.92, z0 + 0.04), (Rk, zc), (Rk * 0.92, z1 - 0.04),
                (Rk * 0.78, z1), (0.0, z1)]
        parts.append(geo.lathe('Keg', prof, segments=10, col=col, material=M['haft'], smooth_angle=30))
        for j, zz in enumerate((z0 + 0.07, zc, z1 - 0.07)):
            rr = Rk * (0.9 if j != 1 else 1.0) + 0.012
            parts.append(core.collar(f'Hoop{j}', zz, col, M['primary'], r=rr, h=0.06, segments=10))
        for j in range(5):
            for zz, off in ((zc - Hm * 0.22, 0.0), (zc + Hm * 0.22, math.pi / 5)):
                a = off + 2 * math.pi * j / 5 + math.pi / 2
                d = (math.cos(a), math.sin(a), 0)
                parts.append(P.spike(f'Stud{j}_{zz:.2f}', (d[0] * Rk * 0.9, d[1] * Rk * 0.9, zz), d, 0.14 * c,
                                     0.04 * c, col, M['primary']))
        parts.append(geo.lathe('Bung', [(0.0, z1 - 0.02), (0.07, z1 - 0.02), (0.07, z1 + 0.06), (0.0, z1 + 0.06)],
                               segments=6, col=col, material=M['accent']))
        pts = [Vector((0, 0, z1 + 0.05)), Vector((0.03, 0, z1 + 0.14)), Vector((-0.02, -0.01, z1 + 0.22)),
               Vector((0.02, -0.01, z1 + 0.29))]
        parts.append(geo.sweep('Fuse', pts, 0.016, sides=5, col=col, material=M['grip']))
        glow.append(P.gem('Spark', z1 + 0.32, 0.05 * c, col, M['glow'], faceted=True, segments=6, x=0.02, y=-0.01))
        # race emblem on the keg front
        fn = style.get('motif')
        if fn:
            S = Hm * 0.42
            shp = core.place(fn(S), 0, zc)
            parts.append(core.plate('KegEmblem', P.filled(shp).buffer(0.03), Rk * 0.3, col, M['secondary'],
                                    chamfer=0.015, y=-Rk * 0.88))
            parts.append(core.plate('KegEmblemInlay', shp, 0.05, col, M['accent'], chamfer=0.012,
                                    y=-Rk * 0.88 - Rk * 0.15))
        return parts, glow, zc, z1 + 0.37, Rk + 0.14 * c
    # core body
    prof = [(0.0, z0 - 0.04), (Rm * 0.7, z0 - 0.04), (Rm * 0.95, z0 + Hm * 0.12), (Rm * 1.05, zc),
            (Rm * 0.95, z1 - Hm * 0.12), (Rm * 0.7, z1 + 0.02), (0.0, z1 + 0.05)]
    parts.append(geo.lathe('Core', prof, segments=seg, col=col, material=M['secondary'], smooth_angle=30,
                           rot_offset=0.0))
    parts.append(core.collar('CoreBandLo', z0 + 0.01, col, M['accent'], r=Rm * 0.82, h=0.07, segments=seg))
    parts.append(core.collar('CoreBandHi', z1 - 0.01, col, M['accent'], r=Rm * 0.82, h=0.07, segments=seg))
    # flanges (race driven: fletched vanes, halo crown, gear teeth, barbs, round lobes, trapezoids)
    gem_dz = 0.0
    crest_z = z1 + 0.03
    if s.get('portals'):
        fp, crest_z = halo_crown(style, ctx, Rm, z0, z1, Hm, c, k)
        parts += fp
    elif s.get('slender'):
        parts += fletched_vanes(style, ctx, Rm, z0, z1, Hm, c, k)
        gem_dz = Hm * 0.14                       # the lower vane tier points at the viewer: lift the gem clear
    else:
        n = 8 if s.get('clockwork') else 6
        Rout = Rm + 0.25 * c * k
        fs = flange_shape(style, Rm * 0.55, Rout, z0 + Hm * 0.08, z1 - Hm * 0.08)
        for j in range(n):
            a = 2 * math.pi * j / n + (math.pi / n if n == 8 else 0.0)   # keep the front (-Y) between two flanges
            f = core.blade(f'Flange{j}', fs, Hm, col, M['primary'], thickness=0.075 if n == 8 else 0.085, bevel=0.03)
            f.rotation_euler = (0, 0, a)
            parts.append(f)
    # glow: cabochon on the core front, between two flanges (front is at -90 deg = between 240 and 300)
    gR = 0.07 * c
    glow.append(P.lens('Gem', gR, col, M['glow'], depth=0.06, segments=6 if faceted else 10, z=zc + gem_dz,
                       y=-Rm * (0.98 if not gem_dz else 0.9)))
    # crest: race motif standing on the top, seated into the cap
    top = z1 + 0.05
    fn = style.get('motif')
    if fn:
        S = 0.38 * c * k
        shp = fn(S)
        if shp is not None and not shp.is_empty:
            cz = crest_z - shp.bounds[1] - 0.03
            parts.append(core.plate('Crest', core.place(shp, 0, cz), 0.1, col, M['accent'], chamfer=0.018))
            top = cz + shp.bounds[3]
    if _flag(s, 'spikes', 'barbs') and not fn:
        parts.append(P.spike('TopSpike', (0, 0, z1), (0, 0, 1), 0.28 * c, 0.05 * c, col, M['primary']))
    return parts, glow, zc, top, Rm + 0.25 * c * k


def head_club(style, ctx, zb, c, long):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    r = P.haft_r(style)
    kh = LONG_HEAD['club_h'] if long else 1.0
    kr = LONG_HEAD['club_r'] if long else 1.0
    k = (kh + kr) / 2                         # studs / spikes / reach follow the head's mass
    Hc = 1.2 * c * kh
    Rc = 0.25 * c * kr
    z0 = zb - 0.35
    mat = M['primary'] if s.get('organic') else M['haft']
    seg = 7 if _flag(s, 'feral', 'spikes') else 8

    def rad(t):  # profile radius along the club, t in 0..1
        if t < 0.72:
            u = t / 0.72
            return r * 1.02 + (Rc - r * 1.02) * (u ** 1.6)
        u = (t - 0.72) / 0.28
        return Rc * math.sqrt(max(0.0, 1 - (u * 0.92) ** 2))
    prof = [(0.0, z0)] + [(rad(i / 14), z0 + Hc * i / 14) for i in range(14)] + [(Rc * 0.36, z0 + Hc * 0.995),
                                                                                  (0.0, z0 + Hc)]
    parts.append(geo.lathe('Club', prof, segments=seg, col=col, material=mat, smooth_angle=34))
    # bands hugging the swell
    for j, t in enumerate((0.42, 0.86)):
        z = z0 + Hc * t
        parts.append(core.collar(f'ClubBand{j}', z, col, M['accent'], r=rad(t) * 1.02 + 0.012, h=0.07 * c, segments=seg))
    # studs: spikes / thorns / diamond studs / rivets
    spiky = bool(_flag(s, 'spikes', 'feral', 'thorns', 'barbs'))
    for ring, t in enumerate((0.58, 0.74)):
        z = z0 + Hc * t
        rr = rad(t)
        nn = 5
        for j in range(nn):
            a = 2 * math.pi * j / nn + (math.pi / nn if ring else 0) + math.pi / 2 + math.pi / nn
            d = Vector((math.cos(a), math.sin(a), 0.25 if ring else 0.0)).normalized()
            base = Vector((math.cos(a) * rr * 0.88, math.sin(a) * rr * 0.88, z))
            if spiky:
                parts.append(P.spike(f'Stud{ring}_{j}', base, d, 0.17 * c * k, 0.045 * c * k, col, M['primary']))
            elif s.get('theatrical'):
                g = P.gem(f'Stud{ring}_{j}', 0, 0.05 * c, col, M['secondary'], faceted=True, segments=4)
                g.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
                g.location = base + d * 0.03
                parts.append(g)
            else:
                parts.append(P.gem(f'Stud{ring}_{j}', z, 0.04 * c, col, M['primary'], segments=6,
                                   x=base.x * 1.08, y=base.y * 1.08))
    # focal: race emblem plaque seated into the front of the swell, glow through its openings
    tz = 0.66
    zp = z0 + Hc * tz
    Rp = rad(tz)
    S = Rp * 1.25
    fn = style.get('motif')
    if fn:
        shp = core.place(fn(S), 0, zp)
        yc = -Rp * 0.9
        parts.append(core.plate('Plaque', P.filled(shp).buffer(0.035), Rp * 0.34, col, M['secondary'], chamfer=0.015,
                                y=yc))
        parts.append(core.plate('Emblem', shp, 0.05, col, M['accent'], chamfer=0.012, y=yc - Rp * 0.17))
        g = glow_fill('Lumen', style, shp, 0.03, col, M, y=yc - Rp * 0.17)
        glow.append(g if g is not None else P.lens('Lumen', 0.05 * c, col, M['glow'], depth=0.045, z=zp,
                                                   y=yc - Rp * 0.17 - 0.025))
    top = z0 + Hc
    if spiky:
        parts.append(P.spike('TopSpike', (0, 0, top - 0.03), (0, 0, 1), 0.22 * c * k, 0.06 * c * k, col, M['primary']))
        top += 0.2 * c * k
    else:
        parts.append(P.gem('TopBead', top + 0.02, 0.06 * c, col, M['accent'], segments=8))
        top += 0.08 * c
    return parts, glow, zp, top, Rc + 0.17 * c * k


def _revolve_profile(full, n=16):
    """Right-half silhouette of a (roughly symmetric) emblem as a lathe profile [(r, z)]."""
    x0, z0, x1, z1 = full.bounds
    prof = [(0.0, z0)]
    for i in range(1, n):
        z = z0 + (z1 - z0) * i / n
        cut = full.intersection(box(0, z - 0.002, 5, z + 0.002))
        w = cut.bounds[2] if not cut.is_empty else 0.0
        prof.append((max(0.02, w), z))
    prof.append((0.0, z1))
    return prof


def head_motif(style, ctx, zb, c, long):
    """The race emblem IS the head. Round / segmented races revolve its silhouette into a solid 3D head with
    the emblem inlaid on the front; the rest get a thick two-tone emblem slab. Both carry flank strike bosses."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    k = LONG_HEAD['motif'] if long else 1.0
    S = 0.84 * c * k
    zc = zb + 0.1 + S / 2
    fn = style.get('motif')
    shp = fn(S) if fn else Point(0, 0).buffer(S / 2, 20)
    shp = core.place(shp.buffer(0), 0, zc)
    full = P.filled(shp)
    sym = full.intersection(core.mirror(full)).area / max(full.area, 1e-6)
    revolve = bool(_flag(s, 'round', 'segmented')) and sym > 0.85
    if revolve:
        closed = full.buffer(0.045, join_style='mitre').buffer(-0.045, join_style='mitre')
        prof = _revolve_profile(_biggest(closed.buffer(0)) if closed.geom_type == 'MultiPolygon' and
                                closed.buffer(0.01).geom_type == 'MultiPolygon' else closed, n=18)
        wmax = max(r for r, _ in prof)
        want = 0.34 * c * k                       # a blunt head must carry mass: scale slim silhouettes up
        f = min(1.5, max(1.0, want / wmax))
        pz0 = prof[0][1]
        prof = [(r * f, zb - 0.03 + (z - pz0) * f ** 0.6) for r, z in prof]
        parts.append(geo.lathe('HeadBody', prof, segments=10, col=col, material=M['primary'], smooth_angle=40))
        wmax = max(r for r, _ in prof)
        zrow = max(prof, key=lambda p: p[0])[1]
        full = core.poly([(r, z) for r, z in prof] + [(-r, z) for r, z in reversed(prof)])
        zc = zrow
        # seam band at the widest row with the emblem plaque seated over it on the front
        parts.append(core.collar('HeadSeam', zrow, col, M['accent'], r=wmax * 1.02 + 0.01, h=0.07 * c, segments=10))
        inner = fn(wmax * 0.95) if fn else None
        if inner is not None and not inner.is_empty:
            em = core.place(inner, 0, zrow)
            yc = -wmax * 0.9
            parts.append(core.plate('Plaque', P.filled(em).buffer(0.03), wmax * 0.34, col, M['secondary'],
                                    chamfer=0.015, y=yc))
            parts.append(core.plate('EmblemInlay', em, 0.05, col, M['accent'], chamfer=0.012, y=yc - wmax * 0.17))
            g = glow_fill('Lumen', style, em, 0.03, col, M, y=yc - wmax * 0.17)
            glow.append(g if g is not None else P.lens('Lumen', 0.05 * c, col, M['glow'], depth=0.045, z=zrow,
                                                       y=yc - wmax * 0.17 - 0.025))
        bx, bzc, T = wmax, zrow, wmax * 2
    else:
        T = 0.4 * c * k
        rim = full.buffer(0.055, join_style='mitre', mitre_limit=3).difference(full.buffer(-0.002)).buffer(0)
        parts.append(_slab('Rim', rim, T * 0.8, col, M['secondary'], bw=0.035))
        parts.append(_slab('Emblem', shp, T, col, M['primary'], bw=0.06))
        g = glow_fill('Lumen', style, shp, T * 0.66, col, M)
        if g is not None:
            glow.append(g)
        else:
            ce = shp.representative_point() if not shp.centroid.within(shp) else shp.centroid
            glow.append(P.lens('Lumen', 0.08 * c, col, M['glow'], depth=0.06, x=ce.x, z=ce.y, y=-T / 2 + 0.01))
        row = full.buffer(0.055).intersection(box(-5, zc - 0.01, 5, zc + 0.01))
        bx = (row.bounds[2] if not row.is_empty else full.bounds[2] + 0.05)
        bzc = zc
    fx0, fz0, fx1, fz1 = full.bounds
    # striking bosses on both flanks, seated into the head at its widest row
    bR = 0.13 * c * k
    spiky = bool(_flag(s, 'spikes', 'barbs', 'horns'))
    for j, sx in enumerate((1, -1)):
        x = sx * (bx - 0.04)
        if spiky:
            parts.append(P.spike(f'Boss{j}', (x, 0, bzc), (sx, 0, 0.2), 0.26 * c * k, bR, col, M['accent']))
        else:
            prof = [(0.0, 0.0), (bR, 0.0), (bR * 1.05, bR * 0.35), (bR * 0.72, bR * 0.85), (0.0, bR * 1.0)]
            parts.append(_along_x(geo.lathe(f'Boss{j}', prof, segments=6 if s.get('faceted') else 8, col=col,
                                            material=M['accent']), x, bzc, sx))
    # motif2 finial on the crown of the head: sunk into the crown and pinned through its centre
    colm = full.buffer(0.0 if revolve else 0.055).intersection(box(-0.025, -50, 0.025, 50))
    crown = colm.bounds[3] if not colm.is_empty else fz1
    top = crown
    fn2 = style.get('motif2')
    if fn2:
        f2 = fn2(0.24 * c)
        if f2 is not None and not f2.is_empty:
            fz = crown - 0.07 - f2.bounds[1]
            parts.append(core.plate('Finial', core.place(f2, 0, fz), 0.1, col, M['accent'], chamfer=0.015))
            pin_top = fz + f2.bounds[3] - 0.02
            parts.append(geo.lathe('FinialPin', [(0.0, crown - 0.12), (0.03, crown - 0.12), (0.03, pin_top),
                                                 (0.0, pin_top)], segments=6, col=col, material=M['accent']))
            top = max(fz1, fz + f2.bounds[3])
    return parts, glow, zc, top, bx + bR


HEADS = dict(hammer=head_hammer, mace=head_mace, club=head_club, motif=head_motif)


# ------------------------------------------------------------------ build
def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    c = P.chunk(style)
    r = P.haft_r(style)
    seg = P.haft_segments(style)
    kind = style.get('head', {}).get('blunt', 'hammer')
    head_fn = HEADS.get(kind, head_hammer)
    long = is_long(style)
    body, glow = [], []
    if long:
        zt = LONG_TOP.get(kind, 3.95)
        ga, gb = 0.42, 2.05
        body += P.haft(style, ctx, 0.0, zt, keep_clear=[(ga, gb)])
        body += P.grip_zone(style, ctx, ga, gb)
        body += P.butt(style, ctx, 0.0)
        grip = (0, 0, gb - 0.28)
        grip2 = (0, 0, ga + 0.3)
    else:
        zt = {'club': 2.3, 'hammer': 2.75}.get(kind, 2.45)
        ga, gb = 0.0, 0.86
        body += P.haft(style, ctx, gb, zt, keep_clear=[(0, gb + 0.1)])
        wraps = max(4, style.get('grip_wraps', 6))
        body.append(geo.wrapped_grip('Grip', ga, gb, r * 1.14, wraps=wraps, segments=10, col=col,
                                     material=M['grip'], style='strap'))
        body.append(P.band('GripCollarTop', gb + 0.02, r * 1.45, col, M['accent'], h=0.07, segments=seg))
        body.append(P.band('GripCollarBot', ga - 0.02, r * 1.4, col, M['accent'], h=0.07, segments=seg))
        body += core.pommel('Pommel', style, ga - 0.05, col, M['secondary'], scale=0.85)
        grip = (0, 0, gb - 0.28)
        grip2 = None
    # head socket: neck flare + race guard seat (club: the guard becomes a small hilt guard above the grip)
    if kind != 'club':
        prof = [(0.0, zt - 0.36), (r * 1.02, zt - 0.36), (r * 1.3, zt - 0.16), (r * 1.7, zt - 0.02),
                (r * 1.75, zt + 0.08), (0.0, zt + 0.08)]
        body.append(geo.lathe('Neck', prof, segments=seg, col=col, material=M['accent'], smooth_angle=35))
        body.append(P.band('NeckBand', zt - 0.37, r * 1.3, col, M['accent'], h=0.06, segments=seg))
        body.append(P.guard_plate('Seat', style, 0.26 * c, 0.11 * c, zt + 0.02, 0.2 * c, col, M['secondary'],
                                  chamfer=0.03, max_h=0.2 * c))
        # langets: straps running down the haft from the head, seated into its faces
        for j, sy in enumerate((-1, 1)):
            body.append(core.plate(f'Langet{j}', box(-0.032, zt - 0.62, 0.032, zt - 0.3), 0.035, col, M['accent'],
                                   chamfer=0.01, y=sy * r * 0.97))
            body.append(P.gem(f'LangetRivet{j}', zt - 0.55, 0.018, col, M['secondary'], segments=6,
                              y=sy * (r * 0.97 + 0.02)))
        zb = zt + 0.06
    else:
        g = None if long else P.guard_plate('HiltGuard', style, 0.2 * c, 0.1 * c, gb + 0.09, 0.16, col, M['secondary'], chamfer=0.03,
                          max_h=0.16)
        body.append(g)
        zb = zt
    hp, hg, zc, top, reach = head_fn(style, ctx, zb, c, long)
    body += hp
    glow += hg
    # theatrical / segmented / swashbuckler charm hanging under the head
    if kind != 'mace' or not s.get('swashbuckler'):
        body += P.hanging(style, ctx, zt - 0.2, -r * 1.3)
    att = {'Grip': grip, 'VFX_Head': (0, 0, zc), 'VFX_Tip': (0, 0, top), 'VFX_Impact': (reach, 0, zc)}
    if grip2 is not None:
        att['GripSecondary'] = grip2
    return dict(body=body, glow=glow, grip=grip, attachments=att)
