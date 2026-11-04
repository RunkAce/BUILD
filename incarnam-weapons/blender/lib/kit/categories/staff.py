"""Two-handed staff. Long haft + race head + one glow accent.

Reads: style['head']['staff'] (orb | crescent | motif | cage), guard (head seat), pommel (butt), motif (head
emblem / crest / inlay), motif2 (collar badges, finial, charm), blade dict (crescent edge treatment), grip_wraps,
silhouette (chunky, slender, spikes, curve, faceted, round, horns, portals, organic, segmented, riveted, clockwork,
theatrical...), mats roles (primary head metal, secondary sockets/frames, accent bands/inlays, haft, grip, glow).
"""
import math

from mathutils import Vector
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import core
import geo
from categories import _polearm as P

HAFT_TOP = 4.55
HEAD_SCALE = 1.22
GRIP_A, GRIP_B = 1.55, 2.95


# ------------------------------------------------------------------ neck (haft top -> head seat)
def neck(style, ctx, zb, top_r, h=0.3, name='Neck'):
    col, M = ctx['col'], ctx['mats']
    r = P.haft_r(style)
    seg = P.haft_segments(style)
    prof = [(0.0, zb - h), (r * 1.05, zb - h), (r * 1.35, zb - h * 0.55), (top_r * 0.8, zb - h * 0.15),
            (top_r, zb), (0.0, zb)]
    parts = [geo.lathe(name, prof, segments=seg, col=col, material=M['secondary'], smooth_angle=35)]
    parts.append(P.band(f'{name}Band', zb - h - 0.01, r * 1.32, col, M['accent'], h=0.06, segments=seg))
    return parts


# ------------------------------------------------------------------ heads
def head_orb(style, ctx, zb, c):
    """Glow orb held by claw prongs rising from a cup, seated on the race guard."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    faceted = bool(s.get('faceted'))
    R = 0.2 * c
    cup_r = R * 0.78
    parts, glow = [], []
    parts += neck(style, ctx, zb, cup_r * 0.85)
    # guard seat under the cup
    parts.append(P.guard_plate('HeadSeat', style, 0.3 * c, 0.13 * c, zb + 0.02, 0.13, col, M['secondary']))
    cup = [(0.0, zb - 0.02), (cup_r * 0.8, zb - 0.02), (cup_r, zb + 0.06), (cup_r * 1.08, zb + 0.13),
           (cup_r * 0.9, zb + 0.15), (0.0, zb + 0.15)]
    parts.append(geo.lathe('Cup', cup, segments=8 if faceted else 10, col=col, material=M['primary'],
                           smooth_angle=35))
    zc = zb + 0.13 + R * 0.92
    glow.append(P.gem('Orb', zc, R, col, M['glow'], faceted=faceted, segments=6 if faceted else 12))
    # prongs
    n = 3 if (s.get('slender') or s.get('round')) else 4
    off = math.pi / 2 if n == 3 else math.pi / 4
    spiky = bool(s.get('spikes'))
    for k in range(n):
        a = off + 2 * math.pi * k / n
        ca, sa = math.cos(a), math.sin(a)
        if spiky:
            rho_z = geo.bezier((cup_r * 0.85, zb + 0.1), (R * 1.25, zc - R * 0.5), (R * 1.25, zc + R * 0.3),
                               (R * 0.95, zc + R * 1.35), 10)
        else:
            rho_z = geo.bezier((cup_r * 0.85, zb + 0.1), (R * 1.25, zc - R * 0.55), (R * 1.15, zc + R * 0.45),
                               (R * 0.36, zc + R * 0.95), 10)
        pts = [Vector((rho * ca, rho * sa, z)) for rho, z in rho_z]
        radii = [0.034 * c * (1 - 0.6 * i / 10) for i in range(11)]
        parts.append(geo.sweep(f'Prong{k}', pts, 0.03, sides=5, col=col, material=M['primary'], radii=radii,
                               smooth_angle=40))
    # crown: round races get a closed top bead; others a motif2 finial seated on the prong tips
    if not spiky:
        parts.append(P.gem('Crown', zc + R * 1.02, 0.045 * c, col, M['accent'], segments=8))
        fn2 = style.get('motif2')
        if fn2 and not s.get('round'):
            f2 = fn2(0.2 * c)
            if f2 is not None and not f2.is_empty:
                # seat the finial's lowest point into the crown bead
                fz = zc + R * 1.02 + 0.02 - f2.bounds[1]
                parts.append(core.plate('Finial', core.place(f2, 0, fz), 0.06, col, M['accent'], chamfer=0.012))
                parts.append(geo.lathe('FinialPin', [(0.0, zc + R * 0.9), (0.018, zc + R * 0.9),
                                                     (0.018, fz + f2.bounds[1] + 0.04), (0.0, fz + f2.bounds[1] + 0.04)],
                                       segments=6, col=col, material=M['accent']))
    # race emblem inlaid on the cup front
    m = P.badge('CupMotif', style, zb + 0.07, cup_r, col, M['accent'], size=0.15 * c, key='motif')
    if m is not None:
        parts.append(m)
    return parts, glow, zc, zc + R * 1.4


def head_crescent(style, ctx, zb, c):
    """Bladed crescent (moon / horns / jaw) cradling a glow gem on a stem."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    bl = style.get('blade', {})
    parts, glow = [], []
    Ro = 0.5 * c * (1.06 if s.get('horns') else 1.0)
    curve = s.get('curve', 0.0)
    zc = zb + Ro - 0.02
    outer = Point(0, zc).buffer(Ro, 40)
    off = 0.36 if not s.get('horns') else 0.46
    Ri = Ro * (0.8 if not s.get('slender') else 0.86)
    inner = Point(curve * Ro * 0.35, zc + Ro * off).buffer(Ri, 40)
    cres = outer.difference(inner)
    if s.get('horns'):
        # horns: flare the tips outward by scaling the upper half wider
        cres = affinity.scale(cres, xfact=1.12, yfact=1.0, origin=(0, zc))
    if s.get('spikes') or bl.get('edge') in ('jagged', 'serrated'):
        teeth = []
        for ang in (-35, -60, -120, -145):
            a = math.radians(ang)
            bx, bz = math.cos(a) * Ro * 0.96, zc + math.sin(a) * Ro * 0.96
            tx, tz = math.cos(a) * Ro * 1.2, zc + math.sin(a) * Ro * 1.2
            px, pz = -math.sin(a) * 0.06, math.cos(a) * 0.06
            teeth.append(core.poly([(bx + px, bz + pz), (tx, tz), (bx - px, bz - pz)]))
        cres = unary_union([cres] + teeth)
    cres = cres.buffer(0)
    if cres.geom_type == 'MultiPolygon':
        cres = max(cres.geoms, key=lambda g: g.area)
    parts.append(core.blade('Crescent', cres, 2 * Ro, col, M['primary'], thickness=0.13, bevel=0.06))
    # socket + race guard seat at the crescent base
    parts += neck(style, ctx, zb + 0.04, 0.12 * c)
    parts.append(P.guard_plate('HeadSeat', style, 0.26 * c, 0.12 * c, zb + 0.05, 0.17, col, M['secondary']))
    # motif inlay through the bottom of the crescent (focal), proud of the blade faces
    bot_in = zc + Ro * off - Ri               # inner edge z at centre
    band_mid = (zc - Ro + bot_in) / 2 + 0.03
    msz = min(0.3 * c, (bot_in - (zc - Ro)) * 1.15)
    m = core.motif_plate('CrescentMotif', style, msz, 0, band_mid + 0.02, 0.17, col, M['accent'])
    if m is not None:
        parts.append(m)
    # glow: gem on a stem in the bowl; slender (bow-like) races also string the horns with light
    stem_top = bot_in + 0.16 * c
    parts.append(geo.lathe('Stem', [(0.0, bot_in - 0.05), (0.035, bot_in - 0.05), (0.03, stem_top - 0.03),
                                    (0.05, stem_top), (0.0, stem_top + 0.01)], segments=6, col=col,
                           material=M['secondary']))
    gR = 0.085 * c
    glow.append(P.gem('Gem', stem_top + gR * 0.95, gR, col, M['glow'], faceted=True,
                      segments=6 if s.get('faceted') else 8))
    if s.get('slender'):
        tips = _horn_tips(cres, zc)
        if tips:
            (xl, zl), (xr, zr) = tips
            gz = stem_top + gR * 0.95
            pts = [Vector((xl, 0, zl)), Vector((0, 0, gz)), Vector((xr, 0, zr))]
            glow.append(geo.sweep('String', pts, 0.012, sides=4, col=col, material=M['glow']))
    return parts, glow, zc, cres.bounds[3]


def _horn_tips(shape, zc):
    xs = list(shape.exterior.coords)
    left = [p for p in xs if p[0] < 0 and p[1] > zc]
    right = [p for p in xs if p[0] > 0 and p[1] > zc]
    if not left or not right:
        return None
    lt = max(left, key=lambda p: p[1])
    rt = max(right, key=lambda p: p[1])
    # pull the anchor slightly inside the horn so the string is seated in the blade
    return (lt[0] * 0.94, lt[1] - 0.04), (rt[0] * 0.94, rt[1] - 0.04)


def head_motif(style, ctx, zb, c):
    """Big race emblem framed by a secondary rim, light showing through its openings."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    S = 0.8 * c
    zc = zb + 0.16 + S / 2
    fn = style.get('motif')
    shp = fn(S) if fn else Point(0, 0).buffer(S / 2, 20)
    shp = core.place(shp.buffer(0), 0, zc)
    if shp.geom_type == 'MultiPolygon':
        shp = unary_union(list(shp.geoms)).buffer(0)
    full = P.filled(shp)
    # rim hugging the emblem silhouette (two-tone frame), joined to the seat below
    rim = full.buffer(0.045, join_style='mitre', mitre_limit=3).difference(full.buffer(-0.002))
    parts.append(core.plate('Rim', rim.buffer(0), 0.13, col, M['secondary'], chamfer=0.022))
    parts.append(core.plate('Emblem', shp, 0.17, col, M['primary'], chamfer=0.03))
    # glow through the openings, or a seated cabochon when the emblem has none
    if P.hole_area(shp) > 0.012 * S * S:
        core_ = full.buffer(-0.01)
        glow.append(core.plate('Lumen', core_, 0.09, col, M['glow'], chamfer=0.012))
    else:
        h = shp.centroid
        glow.append(P.lens('Lumen', 0.08 * c, col, M['glow'], depth=0.07, x=h.x, z=h.y, y=-0.075))
    # seat: race guard cradling the emblem, socketed onto the neck
    seat_z = full.bounds[1] + 0.02
    parts += neck(style, ctx, seat_z - 0.04, 0.12 * c)
    parts.append(P.guard_plate('HeadSeat', style, 0.3 * c, 0.13 * c, seat_z, 0.2, col, M['secondary']))
    # portal races: a thin halo ring around the emblem, pinned at the seat
    if s.get('portals'):
        rr = S * 0.66
        halo = Point(0, zc).buffer(rr, 32).difference(Point(0, zc).buffer(rr - 0.05, 32))
        # spokes bridge the halo into the rim (never floating)
        spokes = []
        for ang in (0, 60, 120, 180):
            a = math.radians(ang)
            r_in = 0.0
            for k in range(40):     # walk out from the centre until we leave the framed emblem
                rp = k * rr / 40
                if not full.buffer(0.045).contains(Point(rp * math.cos(a), zc + rp * math.sin(a))):
                    break
                r_in = rp
            r_in = max(r_in - 0.03, 0.0)
            p0 = (r_in * math.cos(a), zc + r_in * math.sin(a))
            p1 = ((rr - 0.02) * math.cos(a), zc + (rr - 0.02) * math.sin(a))
            spokes.append(LineStringBuffer(p0, p1, 0.022))
        halo = unary_union([halo] + spokes).buffer(0)
        parts.append(core.plate('Halo', halo, 0.08, col, M['accent'], chamfer=0.015))
    top = max(full.bounds[3] + 0.045, (zc + S * 0.66) if s.get('portals') else 0)
    # spiky races: twin horn spikes rising from the seat
    if s.get('spikes'):
        for sx in (1, -1):
            b = Vector((sx * 0.22 * c, 0, seat_z + 0.02))
            parts.append(P.spike(f'SeatSpike{sx}', b, (sx * 0.55, 0, 1), 0.26 * c, 0.04, col, M['primary']))
    return parts, glow, zc, top


def head_cage(style, ctx, zb, c):
    """Lantern cage: bowed bars between a base cup and a cap, glow core inside, race crest on top."""
    col, M = ctx['col'], ctx['mats']
    s = P.sil(style)
    parts, glow = [], []
    Hc = 0.62 * c
    Rb = 0.24 * c
    rb = 0.15 * c
    z0, z1 = zb + 0.08, zb + 0.08 + Hc
    parts += neck(style, ctx, zb, rb * 0.9)
    parts.append(P.guard_plate('HeadSeat', style, 0.28 * c, 0.12 * c, zb + 0.02, 0.12, col, M['secondary']))
    seg = 8
    base = [(0.0, zb - 0.02), (rb * 0.85, zb - 0.02), (rb * 1.1, z0 - 0.02), (rb * 1.12, z0 + 0.04),
            (rb * 0.9, z0 + 0.06), (0.0, z0 + 0.06)]
    parts.append(geo.lathe('CageBase', base, segments=seg, col=col, material=M['secondary']))
    cap = [(0.0, z1 - 0.06), (rb * 0.9, z1 - 0.06), (rb * 1.12, z1 - 0.03), (rb * 1.1, z1 + 0.04),
           (rb * 0.6, z1 + 0.1), (0.0, z1 + 0.12)]
    parts.append(geo.lathe('CageCap', cap, segments=seg, col=col, material=M['secondary']))
    nb = 6 if (s.get('riveted') or s.get('heavy') or s.get('tool')) else 4
    for k in range(nb):
        a = math.pi / nb + 2 * math.pi * k / nb
        ca, sa = math.cos(a), math.sin(a)
        rz = geo.bezier((rb * 0.95, z0 + 0.02), (Rb * 1.3, z0 + Hc * 0.25), (Rb * 1.3, z1 - Hc * 0.25),
                        (rb * 0.95, z1 - 0.02), 10)
        pts = [Vector((r * ca, r * sa, z)) for r, z in rz]
        parts.append(geo.sweep(f'Bar{k}', pts, 0.034 * c, sides=4, col=col, material=M['primary'],
                               smooth_angle=40))
    zm = (z0 + z1) / 2
    parts.append(P.ring_h('Belt', zm, Rb * 1.07, 0.024 * c, col, M['accent'], sides=4, samples=nb * 4))
    # glow core on a pedestal
    gR = 0.15 * c
    parts.append(geo.lathe('Pedestal', [(0.0, z0 + 0.04), (0.05, z0 + 0.04), (0.035, zm - gR * 0.7),
                                        (0.0, zm - gR * 0.6)], segments=6, col=col, material=M['secondary']))
    glow.append(P.gem('Core', zm + 0.01, gR, col, M['glow'], faceted=bool(s.get('faceted') or s.get('tool')),
                      segments=8))
    # crest: race motif standing on the cap
    S = 0.36 * c
    fn = style.get('motif')
    top = z1 + 0.12
    if fn:
        shp = fn(S)
        if shp is not None and not shp.is_empty:
            bz = shp.bounds[1]
            cz = z1 + 0.08 - bz
            parts.append(core.plate('Crest', core.place(shp, 0, cz), 0.1, col, M['accent'], chamfer=0.018))
            top = cz + shp.bounds[3]
    return parts, glow, zm, top


def LineStringBuffer(p0, p1, half_w):
    return LineString([p0, p1]).buffer(half_w, cap_style=2)


HEADS = dict(orb=head_orb, crescent=head_crescent, motif=head_motif, cage=head_cage)


# ------------------------------------------------------------------ build
def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    c = P.chunk(style)
    kind = style.get('head', {}).get('staff', 'orb')
    head_fn = HEADS.get(kind, head_orb)
    zb = HAFT_TOP
    body, glow = [], []
    body += P.haft(style, ctx, 0.0, zb - 0.2, keep_clear=[(GRIP_A, GRIP_B)])
    body += P.grip_zone(style, ctx, GRIP_A, GRIP_B)
    body += P.butt(style, ctx, 0.0)
    hp, hg, zc, top = head_fn(style, ctx, zb, c * HEAD_SCALE)
    body += hp
    glow += hg
    r = P.haft_r(style)
    # race badge on the neck band + hanging charm for theatrical / segmented races
    b = P.badge('NeckBadge', style, zb - 0.62, r * 1.3, col, M['accent'], size=0.14)
    if b is not None:
        body.append(P.band('NeckBadgeBand', zb - 0.62, r * 1.3, col, M['secondary'], h=0.12,
                           segments=P.haft_segments(style)))
        body.append(b)
    body += P.hanging(style, ctx, zb - 0.34, r * 1.3)
    grip_hi = GRIP_B - 0.32
    grip_lo = GRIP_A + 0.32
    return dict(body=body, glow=glow, grip=(0, 0, grip_hi),
                attachments={'Grip': (0, 0, grip_hi), 'GripSecondary': (0, 0, grip_lo), 'VFX_Head': (0, 0, zc),
                             'VFX_Tip': (0, 0, top), 'VFX_Butt': (0, 0, -0.2)})
