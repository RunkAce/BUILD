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


# ------------------------------------------------------------------ build
def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    s = B.sil(style)
    bl = style.get('blade', {})
    kind = kind_of(style)
    c = B.chunk(style)
    k = 0.8 + 0.2 * c                     # gentle chunk scale for cross-sections
    slender = bool(s.get('slender'))
    faceted = bool(s.get('faceted'))
    seg = 6 if faceted else (8 if B.is_mech(style) else 10)
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

    # ---------------- receiver + lock plates (motif focal)
    rec = receiver_shape(style, z0, z1, xb, xt)
    body.append(core.blade('Receiver', rec, z1 - z0, col, M['primary'], thickness=T, edge_t=T * 0.62, bevel=0.04))
    lh, lw = (z1 - z0) * 0.7, (xt - xb) * 0.7
    lxc, lzc = xb + (xt - xb) * 0.42, z0 + (z1 - z0) * 0.5
    lock = lock_plate_shape(style, lzc, lxc, lh, lw).intersection(rec.buffer(-0.025)).buffer(0)
    lock = B.largest(lock)
    body.append(core.plate('LockPlate', lock, T + 0.04, col, M['secondary'], chamfer=0.02))
    msz = min(lh, lw) * 0.86
    m = core.motif_plate('LockMotif', style, msz, lxc, lzc, T + 0.085, col, M['accent'])
    if m is not None:
        body.append(m)
    if B.is_mech(style) and not s.get('clockwork'):
        # rivets at the lock-plate ends (seated through the plate)
        lx0, lz0, lx1, lz1 = lock.bounds
        for i, (px, pz) in enumerate(((lxc, lz1 - 0.04), (lxc, lz0 + 0.04))):
            if lock.buffer(-0.02).contains(Point(px, pz)):
                body.append(B.stud(f'LockRivet{i}', px, pz, 0.028, T + 0.1, col, M['accent']))

    # ---------------- breech flange (race guard), seated across the barrel at the receiver front
    g = B.largest(core.guard_shape(style, 0.3, 0.12))
    gx0, gz0, gx1, gz1 = g.bounds
    gs = min(0.44 * k / max(gx1 - gx0, 1e-6), 0.16 / max(gz1 - gz0, 1e-6), 1.6)
    g = affinity.scale(g, gs, gs, origin=(0, 0))
    gx0, gz0, gx1, gz1 = g.bounds
    gzc = z1 + 0.01
    g = affinity.translate(g, -(gx0 + gx1) / 2, gzc - (gz0 + gz1) / 2)   # crossguard width spans gun up/down
    body.append(core.plate('BreechFlange', g, min(T * 0.78, 2 * r + 0.06), col, M['secondary'], chamfer=0.025))

    # ---------------- barrel
    if kind == 'pistol':
        prof = [(0.0, zb0), (r * 1.1, zb0), (r * 1.1, z1 + 0.12), (r * 1.0, z1 + 0.16), (r * 0.9, zm - 0.3),
                (r * 1.12, zm - 0.16), (r * 1.18, zm - 0.03), (r * 1.08, zm), (r * 0.6, zm), (r * 0.6, zm - 0.16),
                (0.0, zm - 0.16)]
    elif kind == 'blunderbuss':
        rb = 0.2 * k
        bell = geo.bezier((r * 0.92, z1 + 0.3), (r * 0.9, zm - 0.45), (rb * 0.6, zm - 0.2), (rb, zm), 8)
        prof = [(0.0, zb0), (r * 1.15, zb0), (r * 1.15, z1 + 0.14), (r * 1.0, z1 + 0.18)] + \
            [(x, z) for x, z in bell] + [(rb * 0.86, zm + 0.01), (rb * 0.7, zm - 0.03), (r * 0.7, zm - 0.3),
                                         (0.0, zm - 0.3)]
    else:
        prof = [(0.0, zb0), (r * 1.15, zb0), (r * 1.15, z1 + 0.18), (r * 1.0, z1 + 0.24), (r * 0.9, zm - 0.12),
                (r * 1.15, zm - 0.1), (r * 1.15, zm), (r * 0.55, zm), (r * 0.55, zm - 0.14), (0.0, zm - 0.14)]
    body.append(geo.lathe('Barrel', prof, segments=seg, col=col, material=M['primary'], smooth_angle=40))
    att['VFX_Muzzle'] = (0, 0, zm)

    def band(name, z, rr, mat, h=0.06):
        return B.band(name, z, rr, col, mat, h=h, segments=seg)

    # breech: faceted reinforce sleeve (pistol / rifle) + ring, then race barrel dressing
    if kind != 'blunderbuss':
        sl = 0.3 if kind == 'pistol' else 0.36
        body.append(geo.lathe('BreechSleeve', [(0.0, z1 - 0.04), (r * 1.22, z1 - 0.04), (r * 1.22, z1 + sl - 0.04),
                                               (r * 1.06, z1 + sl), (0.0, z1 + sl)], segments=6 if faceted else 8,
                              col=col, material=M['primary'], rot_offset=0.0 if faceted else None, smooth_angle=20))
    body.append(band('BreechRing', z1 + (0.06 if kind == 'blunderbuss' else sl - 0.01), r * 1.3, M['accent'], h=0.07))
    if s.get('segmented'):
        z = z1 + 0.32
        i = 0
        while z < zm - 0.3:
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
    elif kind == 'blunderbuss':
        body.append(band('BellRim', zm - 0.035, 0.2 * k * 1.04, M['secondary'], h=0.06))
    if s.get('organic'):
        za, zb = z1 + 0.2, zm - 0.35
        turns, n = 1.75, 40
        pts, radii = [], []
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t + 0.6
            rr = (r if kind != 'blunderbuss' else r * 0.95) * (0.8 if i in (0, n) else 1.06)
            pts.append(Vector((rr * math.cos(a), rr * math.sin(a), za + (zb - za) * t)))
            radii.append(0.022 * (0.55 + 0.45 * math.sin(math.pi * t)))
        body.append(geo.sweep('Vine', pts, 0.022, sides=5, col=col, material=M['accent'], radii=radii))
        for j, t in enumerate((0.3, 0.7)):
            a = 2 * math.pi * turns * t + 0.6
            p = Vector((r * 1.08 * math.cos(a), r * 1.08 * math.sin(a), za + (zb - za) * t))
            body.append(P.spike(f'Thorn{j}', p, (math.cos(a), math.sin(a), 0.5), 0.07, 0.018, col, M['accent']))

    # ---------------- front sight (motif2) seated on the barrel top near the muzzle
    fn2 = style.get('motif2')
    sight_z = zm - (0.24 if kind != 'blunderbuss' else 0.5)
    if fn2:
        f2 = fn2(0.14 * k)
        if f2 is not None and not f2.is_empty:
            f2 = B.largest(f2.buffer(0))
            rr = r * (0.9 if kind == 'pistol' else 1.0)
            if kind == 'blunderbuss':
                rr = r * 0.95
            fx = rr + 0.02 - f2.bounds[0]
            f2p = core.place(f2, fx, sight_z)
            post = box(rr * 0.55, f2p.bounds[1] + 0.01, rr + 0.045, f2p.bounds[3] - 0.01)
            post = post.intersection(f2p.buffer(0.04).union(box(rr * 0.5, -9, rr + 0.03, 9))).buffer(0)
            body.append(core.plate('FrontSight', B.largest(unary_union([f2p, post]).buffer(0)), 0.05, col, M['accent'],
                                   chamfer=0.01))

    # ---------------- hammer + pivot
    hz = z0
    hs = hammer_shape(style, xt, hz)
    body.append(core.plate('Hammer', hs, 0.09, col, M['secondary'], chamfer=0.018))
    body.append(B.stud('HammerPivot', xt - 0.005, hz + 0.12, 0.03, 0.13, col, M['accent']))

    # ---------------- glow charge (single emissive accent) on the receiver top
    va, vb = z0 + 0.28, z1 - 0.05
    if faceted:
        R = 0.085 * k
        zc = (va + vb) / 2 + 0.02
        glow.append(P.gem('Charge', zc, R, col, M['glow'], faceted=True, segments=6, x=xt + R * 0.5))
        for i, zz in enumerate((zc - R * 0.55, zc + R * 0.35)):
            body.append(B.band(f'ChargeSocket{i}', zz, R * (0.78 if i == 0 else 0.62), col, M['accent'], h=0.04,
                               segments=6))
            body[-1].location = (xt + R * 0.5, 0, 0)
    elif B.is_round(style):
        R = 0.075 * k
        zc = (va + vb) / 2
        glow.append(P.gem('Charge', zc, R, col, M['glow'], segments=10, x=xt + R * 0.45))
        cup = geo.lathe('ChargeCup', [(0.0, -R * 0.75), (R * 0.85, -R * 0.75), (R * 1.08, -R * 0.1),
                                      (R * 0.98, R * 0.05), (0.0, -R * 0.2)], segments=10, col=col,
                        material=M['accent'])
        cup.rotation_euler = (0, math.radians(90), 0)          # cup opens toward +X (gun top)
        cup.location = (xt + R * 0.45, 0, zc)
        body.append(cup)
    else:
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
    tg_front = (xb + 0.03, z1 - 0.2)
    trig = core.poly([(xb + 0.03, 0.36), (xb + 0.03, 0.3), (xb - 0.08, 0.25), (xb - 0.12, 0.27), (xb - 0.05, 0.31)])
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
        gshape = affinity.translate(affinity.rotate(gl, deg, origin=(0, 0)), ax, az)
        TG = T * 0.86
        body.append(core.blade('GripStock', gshape, Lg, col, M['haft'], thickness=TG, edge_t=TG * 0.6, bevel=0.035))
        panel = grip_local(style, Lg, wt).intersection(box(-1, -Lg + 0.24, 1, -0.06)).buffer(-0.028)
        if not panel.is_empty:
            panel = core.bend(B.largest(panel), curv)
            panel = affinity.translate(affinity.rotate(panel, deg, origin=(0, 0)), ax, az)
            body.append(core.plate('GripPanel', panel, TG + 0.035, col, M['grip'], chamfer=0.012))
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
        bez = geo.bezier(tg_front, (xb - 0.2, tg_front[1] + 0.02), (tg_end[0] - 0.06, tg_end[1] + 0.22), tg_end, 12)
        body.append(geo.sweep('TriggerGuard', [Vector((x, 0, z)) for x, z in bez], 0.024, sides=6, col=col,
                              material=M['accent'], smooth_angle=50))
        tail_pt = (bx, bz - 0.05)
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
        bez = geo.bezier(tg_front, (xb - 0.2, tg_front[1]), (xb - 0.12, z0 - 0.1), (-0.1, z0 - 0.16), 12)
        body.append(geo.sweep('TriggerGuard', [Vector((x, 0, z)) for x, z in bez], 0.024, sides=6, col=col,
                              material=M['accent'], smooth_angle=50))
        # forestock bedded under the barrel + oval barrel bands
        fz0, fz1 = z1 - 0.06, z1 + (zm - z1) * 0.4
        fd = 0.15 * k
        fore = core.poly([(0.0, fz0), (-fd, fz0), (-fd, fz1 - 0.3), (-fd * 0.55, fz1), (0.0, fz1)])
        fore = fore.buffer(-0.02).buffer(0.02)
        body.append(core.blade('Forestock', fore, fz1 - fz0, col, M['haft'], thickness=2 * r + 0.05,
                               edge_t=r * 1.2, bevel=0.03))
        for i, zz in enumerate((fz0 + 0.34, fz1 - 0.06)):
            b_ = geo.lathe(f'BarrelBand{i}', [(0.0, zz - 0.035), (0.13 * k, zz - 0.035), (0.14 * k, zz),
                                              (0.13 * k, zz + 0.035), (0.0, zz + 0.035)], segments=seg, col=col,
                           material=M['accent'], scale_xy=(0.88 if i else 1.0, 0.85 * (2 * r + 0.07) / (0.26 * k)))
            b_.location = (-0.05 * k if not i else -0.035 * k, 0, 0)
            body.append(b_)
        att['GripSecondary'] = (-0.08 * k, 0, (fz0 + fz1) / 2)
        tail_pt = (-0.18, zs - 0.02)

    # ---------------- bayonet (spiky races; read the race blade dict) / spiked bell
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
    elif B.is_spiky(style):
        rb = 0.2 * k
        for j in range(6):
            a = 2 * math.pi * j / 6 + math.pi / 6
            base = Vector((math.cos(a) * rb * 0.92, math.sin(a) * rb * 0.92, zm - 0.06))
            body.append(P.spike(f'BellSpike{j}', base, (math.cos(a), math.sin(a), 0.9), 0.14, 0.035, col,
                                M['secondary']))

    # ---------------- hanging tassel / charm (theatrical, swashbuckler, segmented)
    hang = P.hanging(style, ctx, 0.0, 0.0, name='Charm')
    if hang:
        xform(hang, Matrix.Translation((tail_pt[0], 0.0, tail_pt[1] + 0.02)))
        body += hang

    att['Grip'] = grip_pt
    return dict(body=body, glow=glow, grip=grip_pt, attachments=att)
