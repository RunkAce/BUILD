"""Gun: stylised fantasy firearm. Barrel along +Z (muzzle up = forward in the R6 grip), gun profile in the XZ
plane (front view shows the side of the gun): the gun's TOP is +X (hammer, sights, charge vial) and its
UNDERSIDE is -X (trigger guard, pistol grip, rifle stock toe).

Kinds (style['head']['gun']):
  pistol      medium barrel with a muzzle swell, angled flintlock grip with the race pommel as butt cap
  blunderbuss short barrel flaring into a bell muzzle (spiked bell for spiky races), angled grip
  rifle       long slim barrel bedded in a wooden forestock with oval barrel bands, full shoulder stock
Reads: head.gun, receiver outline + lock (side) plate from silhouette flags (round / faceted / clockwork / heavy
/ tool / riveted / spikes / horns / organic / segmented / theatrical / swashbuckler / slender), race guard as
the breech flange, motif on the lock plates (focal, both sides), motif2 as the front sight (and the rifle cheek
inlay), blade dict as a bayonet for spiky races, pommel as the butt cap, mats roles (primary barrel/receiver,
secondary lock plate/hammer/flange, accent bands/inlays, haft wooden grip/stock, grip wrap panels, glow charge
vial = the single emissive accent).
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

KINDS = ('pistol', 'blunderbuss', 'rifle')


def kind_of(style):
    k = style.get('head', {}).get('gun', 'pistol')
    return k if k in KINDS else 'pistol'


def xform(objs, mtx):
    """Pre-multiply object transforms (parts are built at the origin, then posed)."""
    for o in objs:
        if o is not None:
            o.matrix_basis = mtx @ o.matrix_basis
    return objs


def rot2(x, z, th):
    """Rotate a 2D (x, z) vector CCW by th radians (shapely convention)."""
    c, s = math.cos(th), math.sin(th)
    return x * c - z * s, x * s + z * c


def bend_pt(x, z, curv):
    """Same mapping as core.bend (bends toward +X), for single points."""
    if abs(curv) < 1e-6:
        return x, z
    R = 1.0 / curv
    t = z / R
    return R - (R - x) * math.cos(t), (R - x) * math.sin(t)


# ------------------------------------------------------------------ 2D shapes
def receiver_shape(style, z0, z1, xb, xt):
    s = B.sil(style)
    w = xt - xb
    if B.is_round(style):
        r = w * 0.4
        shp = box(xb + r, z0 + r, xt - r, z1 - r).buffer(r, 8)
        shp = shp.union(box(xb + r * 0.5, z0, xt, z0 + r))          # flat rear for the hammer / tang
    elif s.get('faceted') or s.get('clockwork'):
        c = w * 0.3
        shp = core.poly([(xb + c, z0), (xt - c * 0.4, z0), (xt, z0 + c * 0.4), (xt, z1 - c * 0.4),
                         (xt - c * 0.4, z1), (xb + c * 0.6, z1), (xb, z1 - c * 1.2), (xb, z0 + c)])
    elif B.is_heavy(style):
        c = w * 0.12
        shp = core.poly([(xb + c, z0), (xt - c, z0), (xt, z0 + c), (xt, z1 - c), (xt - c, z1), (xb + c, z1),
                         (xb, z1 - c), (xb, z0 + c)])
    else:
        # flintlock lock body: long diagonal under the front, short chamfers at the rear
        shp = core.poly([(xb + 0.04, z0), (xt - 0.03, z0), (xt, z0 + 0.04), (xt, z1), (xb * 0.3, z1),
                         (xb, z1 - w * 0.62), (xb, z0 + 0.04)])
    return shp.buffer(0)


def lock_plate_shape(style, zc, xc, h, w):
    """Side (lock) plate outline centred at (xc, zc): h along Z, w along X."""
    s = B.sil(style)
    if s.get('clockwork'):
        g = core.GUARDS['gear'](w * 0.9, w * 0.5)
        g = core.poly(list(B.largest(g).exterior.coords))          # filled gear (motif covers the centre)
        return core.place(B.fit(g, min(h, w * 1.15)), xc, zc)
    if B.is_round(style):
        return affinity.translate(affinity.scale(Point(0, 0).buffer(0.5, 20), w, h, origin=(0, 0)), xc, zc)
    if s.get('faceted'):
        return core.poly([(xc, zc + h / 2), (xc + w / 2, zc + h * 0.22), (xc + w / 2, zc - h * 0.22), (xc, zc - h / 2),
                          (xc - w / 2, zc - h * 0.22), (xc - w / 2, zc + h * 0.22)])
    if B.is_heavy(style):
        return box(xc - w / 2, zc - h / 2, xc + w / 2, zc + h / 2)
    # flintlock lozenge: pointed front, rounded tail
    return unary_union([core.poly([(xc - w / 2, zc - h * 0.1), (xc + w / 2, zc - h * 0.1), (xc + w * 0.18, zc + h / 2),
                                   (xc - w * 0.3, zc + h * 0.34)]),
                        affinity.scale(Point(xc, zc - h * 0.1).buffer(w / 2, 14), 1.0, h * 0.8 / w,
                                       origin=(xc, zc - h * 0.1))]).buffer(0)


def hammer_shape(style, x0, z0):
    """Cock / hammer standing on the receiver top-rear (x0 = receiver top, z0 = receiver rear). Compact: the spur
    projects toward +X (gun top) and never drops below the receiver rear (no 'leg' in the silhouette)."""
    s = B.sil(style)
    if s.get('horns'):
        outer = geo.bezier((x0 - 0.05, z0 + 0.24), (x0 + 0.16, z0 + 0.3), (x0 + 0.26, z0 + 0.12), (x0 + 0.18, z0 + 0.04), 10)
        inner = geo.bezier((x0 + 0.18, z0 + 0.04), (x0 + 0.15, z0 + 0.12), (x0 + 0.08, z0 + 0.14), (x0 - 0.05, z0 + 0.08), 10)
        return core.poly(outer + inner[1:]).union(Point(x0 + 0.18, z0 + 0.06).buffer(0.035, 8)).buffer(0)
    if B.is_spiky(style):
        return core.poly([(x0 - 0.05, z0 + 0.24), (x0 - 0.05, z0 + 0.05), (x0 + 0.1, z0 + 0.04), (x0 + 0.26, z0 + 0.0),
                          (x0 + 0.14, z0 + 0.14), (x0 + 0.07, z0 + 0.24)])
    if B.is_round(style):
        return unary_union([core.poly([(x0 - 0.05, z0 + 0.22), (x0 - 0.05, z0 + 0.06), (x0 + 0.1, z0 + 0.06),
                                       (x0 + 0.12, z0 + 0.12), (x0 + 0.05, z0 + 0.22)]),
                            Point(x0 + 0.14, z0 + 0.1).buffer(0.055, 12)]).buffer(0)
    if B.is_heavy(style) or s.get('clockwork') or s.get('faceted'):
        return core.poly([(x0 - 0.05, z0 + 0.24), (x0 - 0.05, z0 + 0.05), (x0 + 0.17, z0 + 0.05), (x0 + 0.19, z0 + 0.13),
                          (x0 + 0.08, z0 + 0.15), (x0 + 0.05, z0 + 0.24)])
    return core.poly([(x0 - 0.05, z0 + 0.24), (x0 - 0.05, z0 + 0.05), (x0 + 0.1, z0 + 0.04), (x0 + 0.2, z0 + 0.06),
                      (x0 + 0.21, z0 + 0.12), (x0 + 0.1, z0 + 0.14), (x0 + 0.06, z0 + 0.24)])


def grip_local(style, Lg, wt):
    """Pistol grip outline in local coords: axis along -z', top at z'=+0.12 (seated), butt at z'=-Lg.
    +x' = backstrap, -x' = finger side."""
    s = B.sil(style)
    back = [(wt * 0.95, 0.12), (wt * 0.95, -0.05), (wt * 0.8, -Lg * 0.55), (wt * 0.9, -Lg + 0.08)]
    front = [(-wt * 0.8, -Lg + 0.1), (-wt * 0.85, -Lg * 0.5), (-wt, -0.1), (-wt, 0.12)]
    body = core.poly(back + front)
    if B.is_round(style):
        butt = Point(wt * 0.1, -Lg + 0.1).buffer(wt * 1.22, 14)
    elif s.get('faceted') or s.get('clockwork'):
        butt = Point(wt * 0.1, -Lg + 0.08).buffer(wt * 1.18, 3).buffer(0)
        butt = affinity.rotate(Point(0, 0).buffer(wt * 1.15, 6), 30, origin=(0, 0))
        butt = affinity.translate(butt, wt * 0.1, -Lg + 0.08)
    elif B.is_heavy(style):
        butt = box(-wt * 1.05, -Lg - 0.02, wt * 1.15, -Lg + 0.2)
    elif B.is_spiky(style):
        butt = core.poly([(-wt * 0.95, -Lg + 0.2), (wt * 0.9, -Lg + 0.2), (wt * 1.45, -Lg - 0.06), (wt * 0.2, -Lg - 0.0),
                          (-wt * 1.0, -Lg + 0.02)])
    else:
        butt = Point(wt * 0.12, -Lg + 0.08).buffer(wt * 1.12, 12)
    return unary_union([body, butt]).buffer(0.012).buffer(-0.012)


RECEIVERS = ('flintlock', 'drum', 'gear', 'boiler', 'carved', 'crystal')
BELLS = ('flare', 'crown', 'octagon', 'bamboo', 'trumpet')
VIALS = ('tube', 'shard', 'lozenge', 'orb', 'gem', 'ember', 'halo', 'hourglass', 'gauge', 'lantern', 'cell')


def _pick(style, key, options, default):
    v = style.get('head', {}).get(key)
    return v if v in options else default


def receiver_kind(style):
    """Receiver body form from silhouette flags (override: head.gun_receiver)."""
    s = B.sil(style)
    if s.get('clockwork'):
        d = 'gear'                                   # gear housing with spoke windows, dial hub
    elif s.get('steam') or s.get('riveted') or s.get('tool'):
        d = 'boiler'                                 # banded pressure tank coaxial with the barrel
    elif s.get('faceted'):
        d = 'crystal'                                # faceted lock body
    elif s.get('organic') or s.get('feral') or s.get('horns') or s.get('segmented'):
        d = 'carved'                                 # carved wooden stock-receiver with an inlaid lock plate
    elif s.get('round') or s.get('portals') or s.get('playful'):
        d = 'drum'                                   # fluted round drum (wheel) with a medallion hub
    elif s.get('slender'):
        d = 'carved'
    else:
        d = 'flintlock'                              # classic boxed flintlock lock
    return _pick(style, 'gun_receiver', RECEIVERS, d)


def bell_kind(style):
    """Blunderbuss bell variant (override: head.gun_bell)."""
    s = B.sil(style)
    if B.is_spiky(style):
        d = 'crown'
    elif s.get('segmented'):
        d = 'bamboo'
    elif B.is_heavy(style) or s.get('faceted') or s.get('clockwork') or s.get('riveted'):
        d = 'octagon'
    elif s.get('theatrical') or s.get('swashbuckler'):
        d = 'trumpet'
    else:
        d = 'flare'
    return _pick(style, 'gun_bell', BELLS, d)


def vial_kind(style, rk):
    """The single emissive accent: shape + position follow the receiver and race (override: head.gun_vial)."""
    s = B.sil(style)
    d = {'drum': 'halo', 'gear': 'hourglass', 'crystal': 'gem', 'carved': 'cell'}.get(rk)
    if rk == 'boiler':
        d = 'lantern' if s.get('tool') else 'gauge'
    if d is None:
        if s.get('swashbuckler'):
            d = 'ember'                              # lit slow-match held in the hammer jaws
        elif B.is_spiky(style):
            d = 'shard'
        elif s.get('theatrical'):
            d = 'lozenge'
        elif B.is_round(style):
            d = 'orb'
        else:
            d = 'tube'
    return _pick(style, 'gun_vial', VIALS, d)


def gear_outline(R, n=10, root=0.8):
    w = 2 * math.pi / n
    pts = []
    for i in range(n):
        a = w * i
        for da, rr in ((-0.3, root), (-0.17, 1.0), (0.17, 1.0), (0.3, root)):
            pts.append((R * rr * math.cos(a + da * w), R * rr * math.sin(a + da * w)))
    return core.poly(pts)


def carved_shape(z0, z1, xb, xt):
    """Carved wooden lock body: swelling underside, a rounded nose cupping the barrel, sloped back."""
    under = geo.bezier((xb + 0.03, z0 + 0.05), (xb - 0.04, z0 + 0.3), (xb + 0.0, z1 - 0.1), (-0.1, z1 - 0.01), 10)
    top = geo.bezier((0.1, z1 - 0.01), (xt + 0.03, z1 - 0.1), (xt + 0.04, z0 + 0.32), (xt, z0 + 0.1), 10)
    pts = [(xt - 0.03, z0), (xb + 0.08, z0)] + under + [(-0.06, z1 + 0.03), (0.06, z1 + 0.03)] + top
    return core.poly(pts).buffer(0.03, 6).buffer(-0.05, 6).buffer(0.02, 6)


def tang_shape(xb, xt, z0, h):
    c = 0.035
    return core.poly([(xb + 0.03 + c, z0), (xt - c, z0), (xt, z0 + c), (xt, z0 + h), (xb + 0.03, z0 + h),
                      (xb + 0.03, z0 + c)])


def y_disc(name, x, z, r, half, col, mat, segments=10, bev=0.025):
    """Two-step bevelled disc / boss whose axis runs along Y (through the gun, shows on both faces)."""
    o = geo.lathe(name, [(0.0, -half), (r - bev, -half), (r, -half + bev), (r, half - bev), (r - bev, half),
                         (0.0, half)], segments=segments, col=col, material=mat, smooth_angle=30)
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (x, 0, z)
    return o


def jag_tube(name, r_out, r_in, z_bot, tops, col, mat, rot=0.0):
    """Open tube (bamboo bell): per-vertex top heights `tops` give a slanted, cracked mouth."""
    import bmesh
    n = len(tops)
    bm = bmesh.new()
    ob, ot, it, ib = [], [], [], []
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        c, s_ = math.cos(a), math.sin(a)
        ob.append(bm.verts.new((r_out * c, r_out * s_, z_bot)))
        ot.append(bm.verts.new((r_out * c, r_out * s_, tops[i])))
        it.append(bm.verts.new((r_in * c, r_in * s_, tops[i] - 0.012)))
        ib.append(bm.verts.new((r_in * c, r_in * s_, z_bot + 0.03)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([ob[i], ob[j], ot[j], ot[i]])       # outer wall
        bm.faces.new([ot[i], ot[j], it[j], it[i]])       # lip
        bm.faces.new([it[i], it[j], ib[j], ib[i]])       # inner wall
    bm.faces.new(list(reversed(ob)))
    bm.faces.new(ib)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = geo.mesh_object(name, bm, col, mat)
    geo.shade_by_angle(obj, 35)
    return obj


def _interp(pts, z):
    """Piecewise-linear lookup of x at z in [(z, x), ...] sorted by descending z."""
    if z >= pts[0][0]:
        return pts[0][1]
    for (za, xa), (zb, xb_) in zip(pts[:-1], pts[1:]):
        if zb <= z <= za:
            t = (za - z) / max(za - zb, 1e-6)
            return xa + (xb_ - xa) * t
    return pts[-1][1]


def loop_pts(amap, zl, xlo, xhi, hy, tassel=None, n=18):
    """Closed cord loop pulled tight (convex hull) around a slab cross-section (x' in [xlo, xhi], y in +-hy) at
    local z' = zl, optionally also around a round tassel (xc, rt) lying against it. amap(x', z') -> world (x, z)."""
    sec = box(xlo, -hy, xhi, hy).buffer(-0.03).buffer(0.03)
    if tassel:
        sec = unary_union([sec, Point(tassel[0], 0.0).buffer(tassel[1], 12)])
    ring_ = sec.convex_hull.exterior
    L = ring_.length
    pts = []
    for i in range(n):
        q = ring_.interpolate(L * i / n)
        X, Z = amap(q.x, zl)
        pts.append(Vector((X, q.y, Z)))
    return pts


# ------------------------------------------------------------------ build
def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    bl = style.get('blade', {})
    kind = kind_of(style)
    rk = receiver_kind(style)
    vk = vial_kind(style, rk)
    bk = bell_kind(style) if kind == 'blunderbuss' else None
    c = B.chunk(style)
    k = 0.8 + 0.2 * c                     # gentle chunk scale for cross-sections
    slender = bool(s.get('slender'))
    faceted = bool(s.get('faceted'))
    seg = 6 if faceted else (8 if (B.is_mech(style) or bk == 'octagon') else 10)
    body, glow = [], []
    att = {}

    # ---------------- layout per kind
    z0 = 0.0
    z1 = 0.66 if kind == 'rifle' else 0.62
    xb, xt = -0.26 * k, 0.14 * k
    T = 0.26 * k                          # receiver thickness (Y)
    if kind == 'pistol':
        r = 0.085 * k * (0.92 if slender else 1.0)
        zm = 1.95
    elif kind == 'blunderbuss':
        r = 0.088 * k
        zm = 1.95
    else:
        r = 0.072 * k * (0.94 if slender else 1.0)
        zm = 2.18
    zb0 = z1 - 0.18                       # barrel breech (hidden in the receiver)
    xu = xb + 0.03                        # underside anchor (trigger + trigger guard front)
    info = {}

    # ---------------- receiver (form from silhouette flags) + lock plate / hub (motif focal)
    def lock_motif(lxc, lzc, msz, depth):
        m = core.motif_plate('LockMotif', style, msz, lxc, lzc, depth, col, M['accent'])
        if m is not None:
            body.append(m)

    if rk in ('flintlock', 'crystal', 'carved'):
        if rk == 'carved':
            rec = carved_shape(z0, z1, xb, xt)
            body.append(core.blade('Receiver', rec, z1 - z0, col, M['haft'], thickness=T * 0.96, edge_t=T * 0.6,
                                   bevel=0.05))
            # metal top strap seated along the wooden back edge (+X)
            strap = rec.difference(rec.buffer(-0.04)).intersection(box(xt - 0.05, z0 + 0.06, 1.0, z1 - 0.06))
            if not strap.is_empty:
                body.append(core.plate('TopStrap', B.largest(strap.buffer(0)), T * 0.96 + 0.02, col,
                                       M['secondary'], chamfer=0.012))
        else:
            rec = receiver_shape(style, z0, z1, xb, xt)
            body.append(core.blade('Receiver', rec, z1 - z0, col, M['primary'], thickness=T, edge_t=T * 0.62,
                                   bevel=0.04))
        lh, lw = (z1 - z0) * 0.7, (xt - xb) * 0.7
        lxc, lzc = xb + (xt - xb) * 0.42, z0 + (z1 - z0) * 0.5
        lock = lock_plate_shape(style, lzc, lxc, lh, lw).intersection(rec.buffer(-0.025)).buffer(0)
        lock = B.largest(lock)
        body.append(core.plate('LockPlate', lock, T + 0.04, col, M['secondary'], chamfer=0.02))
        lock_motif(lxc, lzc, min(lh, lw) * 0.86, T + 0.085)
        if B.is_mech(style) and not s.get('clockwork'):
            lx0, lz0, lx1, lz1 = lock.bounds
            for i, (px, pz) in enumerate(((lxc, lz1 - 0.04), (lxc, lz0 + 0.04))):
                if lock.buffer(-0.02).contains(Point(px, pz)):
                    body.append(B.stud(f'LockRivet{i}', px, pz, 0.028, T + 0.1, col, M['accent']))
    elif rk in ('drum', 'gear'):
        body.append(core.plate('Tang', tang_shape(xb, xt, z0, 0.24), T, col, M['primary'], chamfer=0.03))
        if rk == 'drum':
            R = 0.24 * k
            cx, cz = -0.05 * k, z0 + (z1 - z0) * 0.6
            sh = Point(cx, cz).buffer(R, 24)
            for j in range(8):                    # fluted rim (chamber flutes)
                a = 2 * math.pi * j / 8 + math.pi / 8
                sh = sh.difference(Point(cx + math.cos(a) * R * 1.05, cz + math.sin(a) * R * 1.05).buffer(R * 0.17, 8))
            TD = T + 0.08
            body.append(core.blade('Drum', sh.buffer(0), 2 * R, col, M['primary'], thickness=TD, edge_t=TD * 0.6,
                                   bevel=0.04))
            body.append(core.plate('DrumHub', Point(cx, cz).buffer(R * 0.52, 16), TD + 0.04, col, M['secondary'],
                                   chamfer=0.02))
            lock_motif(cx, cz, R * 0.92, TD + 0.08)
            info.update(cx=cx, cz=cz, R=R, TD=TD)
        else:
            R = 0.27 * k
            cx, cz = -0.05 * k, z0 + (z1 - z0) * 0.56
            g = affinity.translate(gear_outline(R, 10), cx, cz)
            ann = Point(cx, cz).buffer(R * 0.68, 24).difference(Point(cx, cz).buffer(R * 0.47, 24))
            spokes = unary_union([affinity.rotate(box(cx, cz - R * 0.075, cx + R, cz + R * 0.075),
                                                  72 * j + 18, origin=(cx, cz)) for j in range(5)])
            g = g.difference(ann.difference(spokes)).buffer(0)
            TG_ = T + 0.05
            body.append(core.blade('GearHousing', g, 2 * R, col, M['primary'], thickness=TG_, edge_t=TG_ * 0.6,
                                   bevel=0.035))
            body.append(core.plate('GearHub', Point(cx, cz).buffer(R * 0.5, 16), TG_ + 0.04, col, M['secondary'],
                                   chamfer=0.02))
            body.append(core.plate('GearRim', Point(cx, cz).buffer(R * 0.7, 24).difference(
                Point(cx, cz).buffer(R * 0.62, 24)), TG_ + 0.02, col, M['accent'], chamfer=0.008))
            lock_motif(cx, cz, R * 0.88, TG_ + 0.08)
            info.update(cx=cx, cz=cz, R=R)
    else:  # boiler
        body.append(core.plate('Tang', tang_shape(xb, xt, z0 - 0.02, 0.22), T, col, M['primary'], chamfer=0.03))
        Rt = 0.2 * k
        za, zt = z0 + 0.06, z1 + 0.06
        sy = 0.8
        body.append(geo.lathe('Boiler', [(0.0, za - 0.02), (Rt * 0.55, za), (Rt * 0.88, za + 0.05), (Rt, za + 0.12),
                                         (Rt, zt - 0.12), (Rt * 0.88, zt - 0.05), (Rt * 0.55, zt), (0.0, zt + 0.02)],
                              segments=10, col=col, material=M['primary'], scale_xy=(1, sy), smooth_angle=40))
        for i, zz in enumerate((za + 0.14, zt - 0.14)):
            body.append(B.band(f'BoilerBand{i}', zz, Rt, col, M['accent'], h=0.06, segments=10, scale_xy=(1, sy)))
            for j in range(4):
                a = math.pi / 4 + j * math.pi / 2
                body.append(P.gem(f'BoilerRivet{i}{j}', zz, 0.022, col, M['secondary'], segments=6,
                                  x=math.cos(a) * (Rt + 0.012), y=math.sin(a) * (Rt + 0.012) * sy))
        rg = 0.11 * k
        lxc, lzc = -0.02 * k, (za + zt) / 2
        half = Rt * sy + 0.035
        body.append(y_disc('GaugeBoss', lxc, lzc, rg, half, col, M['secondary'], segments=10))
        lock_motif(lxc, lzc, rg * 1.5, 2 * half + 0.03)
        if s.get('steam'):
            bez = geo.bezier((Rt * 0.62, zt - 0.05), (Rt * 1.05, zt + 0.06), (r * 1.7, z1 + 0.14), (r * 1.0, z1 + 0.27), 10)
            body.append(geo.sweep('SteamPipe', [Vector((x, 0, z)) for x, z in bez], 0.028, sides=6, col=col,
                                  material=M['secondary']))
        xu = -Rt + 0.03
        info.update(Rt=Rt, za=za, zt=zt, sy=sy)

    # ---------------- breech flange (race guard), seated across the barrel at the receiver front
    g = B.largest(core.guard_shape(style, 0.3, 0.12))
    gx0, gz0, gx1, gz1 = g.bounds
    gs = min(0.44 * k / max(gx1 - gx0, 1e-6), 0.16 / max(gz1 - gz0, 1e-6), 1.6)
    g = affinity.scale(g, gs, gs, origin=(0, 0))
    gx0, gz0, gx1, gz1 = g.bounds
    gzc = z1 + 0.01
    g = affinity.translate(g, -(gx0 + gx1) / 2, gzc - (gz0 + gz1) / 2)   # crossguard width spans gun up/down
    body.append(core.plate('BreechFlange', g, min(T * 0.78, 2 * r + 0.06), col, M['secondary'], chamfer=0.025))

    # ---------------- barrel (+ blunderbuss bell variant)
    rb = 0.2 * k
    zt0 = None                            # bamboo tube start
    if kind == 'pistol':
        prof = [(0.0, zb0), (r * 1.1, zb0), (r * 1.1, z1 + 0.12), (r * 1.0, z1 + 0.16), (r * 0.9, zm - 0.3),
                (r * 1.12, zm - 0.16), (r * 1.18, zm - 0.03), (r * 1.08, zm), (r * 0.6, zm), (r * 0.6, zm - 0.16),
                (0.0, zm - 0.16)]
    elif kind == 'blunderbuss':
        base = [(0.0, zb0), (r * 1.15, zb0), (r * 1.15, z1 + 0.14), (r * 1.0, z1 + 0.18)]
        if bk == 'trumpet':
            rb = 0.23 * k
            zf = z1 + 0.3
            bell = []
            for i in range(12):                 # exponential horn: slim throat, late wide flare
                t = i / 11
                bell.append((r * 0.82 + (rb - r * 0.82) * t ** 3.2, zf + (zm - zf) * (1 - (1 - t) ** 1.15)))
            prof = base + bell + [(rb * 0.9, zm + 0.008), (rb * 0.62, zm - 0.04), (r * 0.62, zm - 0.3),
                                  (0.0, zm - 0.3)]
        elif bk == 'octagon':
            rb = 0.21 * k
            prof = base + [(r * 0.95, zm - 0.6), (rb * 0.58, zm - 0.4), (rb * 0.64, zm - 0.33),
                           (rb * 0.94, zm - 0.07), (rb, zm), (rb * 0.84, zm + 0.01), (rb * 0.7, zm - 0.04),
                           (r * 0.7, zm - 0.3), (0.0, zm - 0.3)]
        elif bk == 'bamboo':
            rb = 0.155 * k
            zt0 = zm - 0.6
            prof = base + [(r * 0.98, zt0 - 0.05), (r * 1.0, zt0 + 0.04), (0.0, zt0 + 0.04)]
        else:   # flare / crown
            bell = geo.bezier((r * 0.92, z1 + 0.3), (r * 0.9, zm - 0.45), (rb * 0.6, zm - 0.2), (rb, zm), 8)
            prof = base + bell + [(rb * 0.86, zm + 0.01), (rb * 0.7, zm - 0.03), (r * 0.7, zm - 0.3),
                                  (0.0, zm - 0.3)]
    else:
        prof = [(0.0, zb0), (r * 1.15, zb0), (r * 1.15, z1 + 0.18), (r * 1.0, z1 + 0.24), (r * 0.9, zm - 0.12),
                (r * 1.15, zm - 0.1), (r * 1.15, zm), (r * 0.55, zm), (r * 0.55, zm - 0.14), (0.0, zm - 0.14)]
    body.append(geo.lathe('Barrel', prof, segments=seg, col=col, material=M['primary'], smooth_angle=40,
                          rot_offset=0.0 if bk == 'octagon' else None))
    att['VFX_Muzzle'] = (0, 0, zm)

    def band(name, z, rr, mat, h=0.06):
        return B.band(name, z, rr, col, mat, h=h, segments=seg)

    if bk == 'bamboo':
        # cracked bamboo bell: thick tube, slanted cut mouth with two split cracks, node rings
        n = 14
        tops = []
        for i in range(n):
            a = 2 * math.pi * i / n
            h = zm - 0.09 * (1 - math.cos(a)) / 2           # diagonal cut, high side toward the gun top (+X)
            if i in (4, 10):
                h -= 0.1                                    # split cracks
            elif i in (3, 5, 9, 11):
                h -= 0.025
            tops.append(h)
        body.append(jag_tube('BambooBell', rb, rb * 0.74, zt0, tops, col, M['haft']))
        body.append(band('BambooNode0', zt0 + 0.03, rb * 1.06, M['accent'], h=0.07))
        body.append(band('BambooNode1', zt0 + 0.3, rb * 1.03, M['haft'], h=0.045))
        body.append(geo.lathe('BambooBore', [(0.0, zm - 0.3), (rb * 0.75, zm - 0.3), (rb * 0.75, zm - 0.27),
                                             (0.0, zm - 0.27)], segments=10, col=col, material=M['primary']))

    # breech: faceted reinforce sleeve (pistol / rifle) + ring, then race barrel dressing
    sl = 0.3 if kind == 'pistol' else 0.36
    if kind != 'blunderbuss' and vk != 'cell':
        body.append(geo.lathe('BreechSleeve', [(0.0, z1 - 0.04), (r * 1.22, z1 - 0.04), (r * 1.22, z1 + sl - 0.04),
                                               (r * 1.06, z1 + sl), (0.0, z1 + sl)], segments=6 if faceted else 8,
                              col=col, material=M['primary'], rot_offset=0.0 if faceted else None, smooth_angle=20))
    ring_z = z1 + (0.06 if (kind == 'blunderbuss' or vk == 'cell') else sl - 0.01)
    body.append(band('BreechRing', ring_z, r * 1.3, M['accent'], h=0.07))
    dress_hi = (zt0 - 0.1) if zt0 else zm - 0.3
    if s.get('segmented'):
        z = z1 + 0.36
        i = 0
        while z < dress_hi:
            rr = r * (1.0 if kind != 'blunderbuss' else 0.95)
            body.append(geo.lathe(f'Node{i}', [(0.0, z - 0.03), (rr * 1.0, z - 0.03), (rr * 1.2, z), (rr * 1.0, z + 0.03),
                                               (0.0, z + 0.03)], segments=seg, col=col, material=M['primary']))
            z += 0.36
            i += 1
    elif B.is_mech(style) and not s.get('clockwork'):
        zz = z1 + (zm - z1) * 0.42
        rr = r * 0.95 if kind == 'blunderbuss' else r * 0.93
        body.append(band('MidBand', zz, rr * 1.38, M['accent'], h=0.11))
        for j in range(4):
            a = math.pi / 4 + j * math.pi / 2
            body.append(P.gem(f'MidRivet{j}', zz, 0.022, col, M['secondary'], segments=6,
                              x=math.cos(a) * rr * 1.42, y=math.sin(a) * rr * 1.42))
    elif s.get('clockwork'):
        zz = z1 + (zm - z1) * 0.45
        body.append(band('MidBandA', zz - 0.05, r * 1.24, M['accent'], h=0.045))
        body.append(band('MidBandB', zz + 0.05, r * 1.24, M['secondary'], h=0.045))
    elif kind != 'rifle':
        body.append(band('MidBand', z1 + (zm - z1) * 0.45, r * (1.22 if kind == 'pistol' else 1.18), M['accent']))
    if kind == 'pistol':
        body.append(band('MuzzleRing', zm - 0.1, r * 1.3, M['secondary'], h=0.07))
    elif bk == 'trumpet':
        body.append(geo.lathe('BellRim', [(rb * 0.9, zm - 0.03), (rb * 1.02, zm - 0.03), (rb * 1.07, zm - 0.005),
                                          (rb * 1.04, zm + 0.02), (rb * 0.9, zm + 0.022)], segments=seg, col=col,
                              material=M['secondary'], smooth_angle=50))
        body.append(band('ThroatRing', z1 + 0.32, r * 1.05, M['secondary'], h=0.05))
    elif bk == 'octagon':
        body.append(B.band('BellRim', zm - 0.03, rb * 1.03, col, M['secondary'], h=0.07, segments=8))
        body.append(B.band('BellStep', zm - 0.36, rb * 0.66, col, M['accent'], h=0.06, segments=8))
        body[-1].rotation_euler = (0, 0, math.pi / 8)
        body[-2].rotation_euler = (0, 0, math.pi / 8)
    elif bk in ('flare', 'crown'):
        body.append(band('BellRim', zm - 0.035, rb * 1.04, M['secondary'], h=0.06))
    if s.get('organic'):
        za_, zb_ = z1 + (0.36 if vk == 'cell' else 0.2), zm - 0.35
        turns, n = 1.5 if vk == 'cell' else 1.75, 40
        pts, radii = [], []
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t + 0.6
            rr = (r if kind != 'blunderbuss' else r * 0.95) * (0.8 if i in (0, n) else 1.06)
            pts.append(Vector((rr * math.cos(a), rr * math.sin(a), za_ + (zb_ - za_) * t)))
            radii.append(0.022 * (0.55 + 0.45 * math.sin(math.pi * t)))
        body.append(geo.sweep('Vine', pts, 0.022, sides=5, col=col, material=M['accent'], radii=radii))
        for j, t in enumerate((0.3, 0.7)):
            a = 2 * math.pi * turns * t + 0.6
            p = Vector((r * 1.08 * math.cos(a), r * 1.08 * math.sin(a), za_ + (zb_ - za_) * t))
            body.append(P.spike(f'Thorn{j}', p, (math.cos(a), math.sin(a), 0.5), 0.07, 0.018, col, M['accent']))

    # ---------------- front sight (motif2) seated on the barrel top near the muzzle
    fn2 = style.get('motif2')
    sight_z = zm - (0.24 if kind != 'blunderbuss' else 0.5)
    rr_s = r * (0.9 if kind == 'pistol' else (0.95 if kind == 'blunderbuss' else 1.0))
    if bk == 'bamboo':
        sight_z, rr_s = zm - 0.2, rb * 0.97
    elif bk == 'octagon':
        sight_z = zm - 0.7
    if fn2:
        f2 = fn2(0.14 * k)
        if f2 is not None and not f2.is_empty:
            f2 = B.largest(f2.buffer(0))
            fx = rr_s + 0.02 - f2.bounds[0]
            f2p = core.place(f2, fx, sight_z)
            post = box(rr_s * 0.55, f2p.bounds[1] + 0.01, rr_s + 0.045, f2p.bounds[3] - 0.01)
            post = post.intersection(f2p.buffer(0.04).union(box(rr_s * 0.5, -9, rr_s + 0.03, 9))).buffer(0)
            body.append(core.plate('FrontSight', B.largest(unary_union([f2p, post]).buffer(0)), 0.05, col, M['accent'],
                                   chamfer=0.01))

    # ---------------- hammer + pivot
    hz = z0
    hs = hammer_shape(style, xt, hz)
    body.append(core.plate('Hammer', hs, 0.09, col, M['secondary'], chamfer=0.018))
    body.append(B.stud('HammerPivot', xt - 0.005, hz + 0.12, 0.03, 0.13, col, M['accent']))

    # ---------------- glow charge: the single emissive accent (shape + position by race)
    va, vb = z0 + 0.28, z1 - 0.05
    ember_pt = None
    if vk == 'gem':
        R = 0.085 * k
        zc = (va + vb) / 2 + 0.02
        glow.append(P.gem('Charge', zc, R, col, M['glow'], faceted=True, segments=6, x=xt + R * 0.5))
        for i, zz in enumerate((zc - R * 0.55, zc + R * 0.35)):
            body.append(B.band(f'ChargeSocket{i}', zz, R * (0.78 if i == 0 else 0.62), col, M['accent'], h=0.04,
                               segments=6))
            body[-1].location = (xt + R * 0.5, 0, 0)
    elif vk == 'orb':
        R = 0.075 * k
        zc = (va + vb) / 2
        glow.append(P.gem('Charge', zc, R, col, M['glow'], segments=10, x=xt + R * 0.45))
        cup = geo.lathe('ChargeCup', [(0.0, -R * 0.75), (R * 0.85, -R * 0.75), (R * 1.08, -R * 0.1),
                                      (R * 0.98, R * 0.05), (0.0, -R * 0.2)], segments=10, col=col,
                        material=M['accent'])
        cup.rotation_euler = (0, math.radians(90), 0)          # cup opens toward +X (gun top)
        cup.location = (xt + R * 0.45, 0, zc)
        body.append(cup)
    elif vk == 'shard':
        # four-sided crystal shard standing in a single claw socket at the receiver top-rear
        rv = 0.055 * k
        xv = xt + rv * 0.5
        sa, sb = z0 + 0.22, z1 - 0.02
        o = geo.lathe('Charge', [(0.0, sa), (rv * 0.7, sa + 0.03), (rv, sa + (sb - sa) * 0.35), (rv * 0.8, sb - 0.1),
                                 (0.0, sb)], segments=4, col=col, material=M['glow'], rot_offset=math.pi / 4,
                      smooth_angle=20)
        o.location = (xv, 0, 0)
        glow.append(o)
        cl = B.band('ChargeClaw', sa + 0.05, rv * 1.25, col, M['accent'], h=0.08, segments=4)
        cl.location = (xv, 0, 0)
        cl.rotation_euler = (0, 0, math.pi / 4)
        body.append(cl)
        for j in range(2):
            body.append(P.spike(f'ChargeProng{j}', Vector((xv + (rv * 0.9 if j else -rv * 0.9) * 0.0,
                                                           (1 if j else -1) * rv * 1.1, sa + 0.08)),
                                (0, (1 if j else -1) * 0.25, 1), 0.12, 0.02, col, M['accent']))
    elif vk == 'lozenge':
        # flat harlequin diamond in a pointed bezel set into the receiver top edge (reads on both faces)
        R = 0.075 * k
        zc = (va + vb) / 2
        xv = xt + 0.02
        dia = core.poly([(xv, zc - R * 1.5), (xv + R, zc), (xv, zc + R * 1.5), (xv - R, zc)])
        body.append(core.plate('ChargeBezel', dia.buffer(0.022, join_style=2), 0.12, col, M['accent'], chamfer=0.015))
        glow.append(core.plate('Charge', dia, 0.16, col, M['glow'], chamfer=0.03))
    elif vk == 'ember':
        # lit slow-match tip clamped in the hammer jaws (a matchlock serpentine)
        ember_pt = (xt + 0.215, z0 + 0.1)
        glow.append(P.gem('Charge', ember_pt[1], 0.042, col, M['glow'], segments=6, x=ember_pt[0]))
        body.append(B.stud('MatchClamp', ember_pt[0] - 0.04, ember_pt[1], 0.03, 0.12, col, M['accent']))
    elif vk == 'halo':
        # glowing ring inlaid around the drum hub, both faces
        cx, cz, R, TD = info['cx'], info['cz'], info['R'], info['TD']
        for side in (-1, 1):
            o = geo.ring(f'ChargeHalo{side + 1}', R * 0.72, 0.022, sides=6, samples=28, col=col, material=M['glow'])
            o.location = (cx, side * (TD / 2 - 0.004), cz)
            glow.append(o)
    elif vk == 'hourglass':
        # caged hourglass standing on the barrel top just ahead of the gear housing
        rv = 0.055 * k
        xv = r * 1.22 + rv * 1.3 + 0.005
        ha, hb = z1 + 0.13, z1 + 0.43
        hm = (ha + hb) / 2
        o = geo.lathe('Charge', [(0.0, ha), (rv * 0.95, ha), (rv, ha + 0.04), (rv * 0.85, ha + 0.1), (rv * 0.22, hm),
                                 (rv * 0.85, hb - 0.1), (rv, hb - 0.04), (rv * 0.95, hb), (0.0, hb)], segments=8,
                      col=col, material=M['glow'], smooth_angle=50)
        o.location = (xv, 0, 0)
        glow.append(o)
        for i, zz in enumerate((ha - 0.01, hb + 0.01)):
            cap = B.band(f'HourCap{i}', zz, rv * 1.3, col, M['accent'], h=0.04, segments=8)
            cap.location = (xv, 0, 0)
            body.append(cap)
            br = box(0.0, zz - 0.025, xv, zz + 0.025)
            body.append(core.plate(f'HourBracket{i}', br, 0.06, col, M['secondary'], chamfer=0.01))
        for j in range(3):
            a = 2 * math.pi * j / 3 + math.pi / 3
            p = geo.lathe(f'HourPost{j}', [(0.0, ha - 0.01), (0.012, ha - 0.01), (0.012, hb + 0.01), (0.0, hb + 0.01)],
                          segments=4, col=col, material=M['secondary'])
            p.location = (xv + math.cos(a) * rv * 1.12, math.sin(a) * rv * 1.12, 0)
            body.append(p)
    elif vk == 'gauge':
        # glowing gauge glass on the boiler flank (gun top, +X), in a bolted bezel ring
        Rt = info['Rt']
        zc = (info['za'] + info['zt']) / 2 + 0.02
        lr = 0.07 * k
        o = P.lens('Charge', lr, col, M['glow'], depth=0.06, segments=10)
        o.rotation_euler = (0, math.radians(90), 0)          # dome faces +X
        o.location = (Rt - 0.012, 0, zc)
        glow.append(o)
        bz = geo.ring('ChargeBezel', lr + 0.012, 0.02, sides=6, samples=16, col=col, material=M['accent'], axis='X')
        bz.location = (Rt - 0.004, 0, zc)
        body.append(bz)
    elif vk == 'lantern':
        # miner's lantern: glowing globe in a cage, bracketed to the tank top
        Rt = info['Rt']
        R = 0.065 * k
        zc = (info['za'] + info['zt']) / 2 + 0.03
        xv = Rt + R * 0.85
        glow.append(P.gem('Charge', zc, R, col, M['glow'], segments=10, x=xv))
        for i, (zz, rr) in enumerate(((zc - R * 1.05, R * 0.8), (zc + R * 1.05, R * 0.62))):
            cap = B.band(f'LanternCap{i}', zz, rr, col, M['accent'], h=0.045, segments=8)
            cap.location = (xv, 0, 0)
            body.append(cap)
        for j in range(4):
            a = math.pi / 4 + j * math.pi / 2
            ca, sa_ = math.cos(a), math.sin(a)
            bars = geo.bezier((R * 0.7, zc - R * 1.05), (R * 1.25, zc - R * 0.5), (R * 1.25, zc + R * 0.5),
                              (R * 0.55, zc + R * 1.05), 8)
            body.append(geo.sweep(f'LanternBar{j}', [Vector((xv + ca * x, sa_ * x, z)) for x, z in bars], 0.012,
                                  sides=4, col=col, material=M['secondary']))
        body.append(core.plate('LanternBracket', box(Rt - 0.05, zc - R * 1.2, xv - R * 0.2, zc - R * 0.85), 0.07, col,
                               M['secondary'], chamfer=0.01))
        hook = geo.ring('LanternHook', 0.035, 0.012, sides=4, samples=10, col=col, material=M['secondary'])
        hook.location = (xv, 0, zc + R * 1.05 + 0.04)
        body.append(hook)
    elif vk == 'cell':
        # glowing charge cell set into the barrel just ahead of the breech, between two collars
        ca_, cb_ = z1 + 0.12, z1 + 0.3
        o = geo.lathe('Charge', [(0.0, ca_), (r * 1.12, ca_), (r * 1.2, ca_ + 0.03), (r * 1.2, cb_ - 0.03),
                                 (r * 1.12, cb_), (0.0, cb_)], segments=seg, col=col, material=M['glow'], smooth_angle=50)
        glow.append(o)
        for i, zz in enumerate((ca_, cb_)):
            body.append(band(f'CellCollar{i}', zz, r * 1.32, M['secondary'], h=0.045))
    else:   # tube
        rv = 0.05 * k * (1.15 if s.get('steam') else 1.0)
        xv = xt + rv * 0.55
        vial = geo.lathe('Charge', [(0.0, va), (rv * 0.6, va), (rv, va + 0.04), (rv, vb - 0.04), (rv * 0.6, vb),
                                    (0.0, vb)], segments=8, col=col, material=M['glow'], smooth_angle=50)
        vial.location = (xv, 0, 0)
        glow.append(vial)
        for i, zz in enumerate((va + 0.03, vb - 0.03)):
            cl = B.band(f'ChargeClamp{i}', zz, rv * 1.22, col, M['accent'], h=0.05, segments=8)
            cl.location = (xv, 0, 0)
            body.append(cl)

    # ---------------- trigger guard + trigger
    dxu = xu - (xb + 0.03)
    tg_front = (xu, z1 - 0.2)
    trig = core.poly([(xu, 0.36), (xu, 0.3), (xu - 0.11, 0.25), (xu - 0.15, 0.27), (xu - 0.08, 0.31)])
    body.append(core.plate('Trigger', trig, 0.05, col, M['accent'], chamfer=0.01))

    # ---------------- grip / stock
    if kind in ('pistol', 'blunderbuss'):
        th = math.radians(-60 if kind == 'pistol' else -56)
        Lg = 0.64 if kind == 'pistol' else 0.68
        wt = 0.13 * k
        ax, az = xb * 0.5, z0 + 0.12
        # banana sweep: the butt curls toward the backstrap (rounder races curl more, faceted / heavy less)
        curv = 0.75 if B.is_round(style) else (0.35 if (faceted or B.is_heavy(style)) else 0.55)
        gl = core.bend(grip_local(style, Lg, wt), curv)
        deg = math.degrees(th)

        def gpt(x, z):
            bx_, bz_ = bend_pt(x, z, curv)
            rx, rz = rot2(bx_, bz_, th)
            return ax + rx, az + rz

        def to_world(shape):
            return affinity.translate(affinity.rotate(core.bend(shape, curv), deg, origin=(0, 0)), ax, az)
        gshape = affinity.translate(affinity.rotate(gl, deg, origin=(0, 0)), ax, az)
        TG = T * 0.86
        body.append(core.blade('GripStock', gshape, Lg, col, M['haft'], thickness=TG, edge_t=TG * 0.6, bevel=0.035))
        panel = grip_local(style, Lg, wt).intersection(box(-1, -Lg + 0.24, 1, -0.06)).buffer(-0.028)
        if not panel.is_empty:
            body.append(core.plate('GripPanel', to_world(B.largest(panel)), TG + 0.035, col, M['grip'], chamfer=0.012))
        # butt cap: race pommel along the (bent) grip axis
        bx, bz = gpt(wt * 0.1, -Lg + 0.02)
        cap = core.pommel('ButtCap', style, 0.0, col, M['secondary'], scale=0.62 * k)
        beta = -(th + Lg * curv)
        xform(cap, Matrix.Translation((bx, 0, bz)) @ Matrix.Rotation(beta, 4, 'Y'))
        body += cap
        gx, gz = gpt(0.0, -Lg * 0.42)
        grip_pt = (gx, 0.0, gz)
        # trigger guard: receiver underside -> grip finger edge
        tg_end = gpt(-wt * 0.9, -0.2)
        bez = geo.bezier(tg_front, (xu - 0.23, tg_front[1] + 0.02), (tg_end[0] - 0.06, tg_end[1] + 0.22), tg_end, 12)
        body.append(geo.sweep('TriggerGuard', [Vector((x, 0, z)) for x, z in bez], 0.024, sides=6, col=col,
                              material=M['accent'], smooth_angle=50))
        # binding frame for cords / tassels: local x' across the grip, z' along it (0 = top, -Lg = butt)
        amap = gpt
        back_pts = [(0.12, wt * 0.95), (-0.05, wt * 0.95), (-Lg * 0.55, wt * 0.8), (-Lg + 0.08, wt * 0.9)]
        front_pts = [(0.12, -wt), (-0.1, -wt), (-Lg * 0.5, -wt * 0.85), (-Lg + 0.1, -wt * 0.8)]
        hy = TG / 2
        zbind = dict(tassel=(-0.1, -0.46), loops=(-0.15, -0.38), coil=(-0.14, -0.46), charm=-Lg + 0.17,
                     charm_loop=-Lg + 0.3, lead=0.0)
    else:
        zs = z0 - 1.18
        stock = core.poly([(xt - 0.02, z0 + 0.14), (xt - 0.02, z0 - 0.02), (0.03, z0 - 0.22), (0.05, z0 - 0.55),
                           (0.07, zs), (-0.42 * k, zs), (-0.24, z0 - 0.5), (-0.12, z0 - 0.2), (xb + 0.02, z0 + 0.0),
                           (xb + 0.02, z0 + 0.14)])
        stock = stock.buffer(0.03, 6).buffer(-0.06, 6).buffer(0.03, 6)
        TS = T * 0.84
        body.append(core.blade('Stock', stock, 1.3, col, M['haft'], thickness=TS, edge_t=TS * 0.6, bevel=0.04))
        wrist = stock.intersection(box(-1, z0 - 0.44, 1, z0 - 0.1)).buffer(-0.022)
        body.append(core.plate('WristWrap', B.largest(wrist), TS + 0.035, col, M['grip'], chamfer=0.012))
        bp = stock.intersection(box(-1, zs - 0.1, 1, zs + 0.07)).buffer(0.012)
        body.append(core.plate('ButtPlate', B.largest(bp), TS + 0.03, col, M['secondary'], chamfer=0.015))
        cheek = core.motif_plate('CheekInlay', style, 0.22 * k, -0.15, z0 - 0.78, TS + 0.05, col, M['accent'],
                                 key='motif2')
        if cheek is not None:
            body.append(cheek)
        grip_pt = (-0.05, 0.0, z0 - 0.27)
        bez = geo.bezier(tg_front, (xu - 0.23, tg_front[1]), (xb - 0.12, z0 - 0.1), (-0.1, z0 - 0.16), 12)
        body.append(geo.sweep('TriggerGuard', [Vector((x, 0, z)) for x, z in bez], 0.024, sides=6, col=col,
                              material=M['accent'], smooth_angle=50))
        # forestock bedded under the barrel + oval barrel bands
        fz0, fz1 = z1 - 0.06, z1 + (zm - z1) * 0.4
        fd = 0.15 * k
        fore = core.poly([(0.0, fz0), (-fd, fz0), (-fd, fz1 - 0.3), (-fd * 0.55, fz1), (0.0, fz1)])
        fore = fore.buffer(-0.02).buffer(0.02)
        body.append(core.blade('Forestock', fore, fz1 - fz0, col, M['haft'], thickness=2 * r + 0.05,
                               edge_t=r * 1.2, bevel=0.03))
        for i, zz in enumerate((fz0 + (0.42 if vk == 'cell' else 0.34), fz1 - 0.06)):
            b_ = geo.lathe(f'BarrelBand{i}', [(0.0, zz - 0.035), (0.13 * k, zz - 0.035), (0.14 * k, zz),
                                              (0.13 * k, zz + 0.035), (0.0, zz + 0.035)], segments=seg, col=col,
                           material=M['accent'], scale_xy=(0.88 if i else 1.0, 0.85 * (2 * r + 0.07) / (0.26 * k)))
            b_.location = (-0.05 * k if not i else -0.035 * k, 0, 0)
            body.append(b_)
        att['GripSecondary'] = (-0.08 * k, 0, (fz0 + fz1) / 2)

        # binding frame along the stock (world z; x' measured from the slice centre)
        def _slice(z):
            sl_ = stock.intersection(box(-5, z - 0.005, 5, z + 0.005))
            if sl_.is_empty:
                return 0.0, 0.1
            x0_, _, x1_, _ = sl_.bounds
            return (x0_ + x1_) / 2, (x1_ - x0_) / 2

        def amap(x, z):
            return x + _slice(z)[0], z
        zz_s = [z0 - 0.1 - 0.05 * i for i in range(12)]
        back_pts = [(z, _slice(z)[1]) for z in zz_s]
        front_pts = [(z, -_slice(z)[1]) for z in zz_s]
        hy = TS / 2
        zbind = dict(tassel=(z0 - 0.12, z0 - 0.48), loops=(z0 - 0.16, z0 - 0.4), coil=(z0 - 0.14, z0 - 0.42),
                     charm=z0 - 0.56, charm_loop=z0 - 0.46, lead=z0 - 0.1)

    def xback(z):
        return _interp(back_pts, z)

    def xfront(z):
        return _interp(front_pts, z)

    # ---------------- bayonet (spiky races; read the race blade dict) / spiked crown bell
    if B.is_spiky(style) and kind != 'blunderbuss':
        Lb, Wb = 0.6, 0.15 * min(bl.get('width', 1.0), 1.1)
        bshape = core.blade_outline(Lb, Wb, edge=bl.get('edge', 'straight'), tip=bl.get('tip', 'point'),
                                    single_edge=bl.get('single_edge', False))
        bxc = -(r + Wb * 0.5 + 0.03)
        broot = zm - 0.42
        body.append(core.blade('Bayonet', core.place(bshape, bxc, broot), Lb, col, M['primary'], thickness=0.07,
                               bevel=0.025))
        lug = core.poly([(0.0, broot - 0.12), (0.0, broot + 0.06), (bxc - Wb * 0.45, broot + 0.04),
                         (bxc - Wb * 0.5, broot - 0.08)])
        body.append(core.plate('BayonetLug', lug, 0.12, col, M['secondary'], chamfer=0.02))
        body.append(band('BayonetRing', broot - 0.03, r * 1.28, M['secondary'], h=0.08))
    elif bk == 'crown':
        for j in range(8):
            a = 2 * math.pi * j / 8 + math.pi / 8
            ln = 0.17 if j % 2 == 0 else 0.1
            base_ = Vector((math.cos(a) * rb * 0.98, math.sin(a) * rb * 0.98, zm - 0.05))
            body.append(P.spike(f'CrownPoint{j}', base_, (math.cos(a) * 0.3, math.sin(a) * 0.3, 1.0), ln, 0.038, col,
                                M['secondary']))

    # ---------------- cords / tassels / charms: bound flat along the grip or stock (never hanging free)
    tk = P.tassel_kind(style)
    if tk == 'tassel' and s.get('swashbuckler'):
        # slow-match fuse: lead from the hammer (ember) along the receiver underside, coiled round the grip
        za_c, zb_c = zbind['coil']
        turns, n = 2.5, 44
        pts = []
        if ember_pt is not None:
            lx, lz = amap(xback(zbind['lead']) + 0.02, zbind['lead'])
            lead = geo.bezier((ember_pt[0] - 0.01, ember_pt[1] - 0.04), (ember_pt[0] - 0.02, z0 - 0.06),
                              (xt - 0.05, z0 - 0.05), (lx, lz), 8)
            pts += [Vector((x, 0.0, z)) for x, z in lead[:-1]]
        for i in range(n + 1):
            t = i / n
            zl = za_c + (zb_c - za_c) * t
            a = 2 * math.pi * turns * t
            lo, hi = xfront(zl) - 0.012, xback(zl) + 0.012
            cxl, axl = (lo + hi) / 2, (hi - lo) / 2
            c_, s_ = math.cos(a), math.sin(a)
            xl = cxl + axl * math.copysign(abs(c_) ** 0.5, c_)
            X, Z = amap(xl, zl)
            pts.append(Vector((X, (hy + 0.012) * math.copysign(abs(s_) ** 0.5, s_), Z)))
        body.append(geo.sweep('FuseCord', pts, 0.016, sides=5, col=col, material=M['accent'], smooth_angle=60))
    elif tk == 'tassel':
        # ribbon tassel lying along the backstrap, tied on with two cord loops
        zt_a, zt_b = zbind['tassel']
        rt = 0.055
        pa = Vector((*amap(xback(zt_a) + rt * 0.7, zt_a),))
        pb = Vector((*amap(xback(zt_b) + rt * 0.7, zt_b),))
        pa3, pb3 = Vector((pa[0], 0, pa[1])), Vector((pb[0], 0, pb[1]))
        d = (pb3 - pa3)
        L = d.length
        d.normalize()
        rot = Vector((0, 0, -1)).rotation_difference(d).to_euler()
        cap = geo.lathe('TasselCap', [(0.0, 0.02), (0.034, 0.012), (0.042, -0.04), (0.0, -0.055)], segments=6,
                        col=col, material=M['primary'])
        tuft = geo.lathe('TasselTuft', [(0.0, -0.035), (0.04, -0.035), (rt * 0.95, -L * 0.45), (rt, -L * 0.85),
                                        (rt * 0.6, -L), (0.0, -L - 0.005)], segments=8, col=col, material=M['secondary'],
                         smooth_angle=60)
        for o in (cap, tuft):
            o.rotation_euler = rot
            o.location = pa3
            body.append(o)
        for i, zl in enumerate(zbind['loops']):
            xc = xback(zl) + rt * 0.7
            lp = loop_pts(amap, zl, xfront(zl) - 0.01, xback(zl) + 0.005, hy + 0.01, tassel=(xc, rt * 0.95))
            body.append(geo.sweep(f'TasselTie{i}', lp, 0.014, sides=4, closed=True, col=col, material=M['accent'],
                                  smooth_angle=60))
    elif tk == 'charm':
        # small motif2 charm inlaid on both grip faces, tied on by a cord loop and a knot stud
        zl = zbind['charm']
        f2 = B.motif_shape(style, 0.15 * k, key='motif2')
        if f2 is not None:
            shp = core.place(B.largest(f2), 0.0, zl)
            if kind in ('pistol', 'blunderbuss'):
                shp = to_world(shp)
            else:
                shp = affinity.translate(shp, _slice(zl)[0], 0)
            body.append(core.plate('CharmPlate', shp, 2 * hy + 0.06, col, M['accent'], chamfer=0.014))
        zl2 = zbind['charm_loop']
        lp = loop_pts(amap, zl2, xfront(zl2) - 0.01, xback(zl2) + 0.01, hy + 0.01)
        body.append(geo.sweep('CharmTie', lp, 0.014, sides=4, closed=True, col=col, material=M['accent'],
                              smooth_angle=60))
        kx, kz = amap(0.0, (zl + zl2) / 2 + 0.02)
        body.append(B.stud('CharmKnot', kx, kz, 0.026, 2 * hy + 0.07, col, M['accent']))

    att['Grip'] = grip_pt
    return dict(body=body, glow=glow, grip=grip_pt, attachments=att)
