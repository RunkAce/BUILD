"""Sacrier: pain-hungry berserkers whose blood and tattoos are their power; fury grows as they bleed.
Colour story: blackened blood-iron, crimson lacquer, bone inlays, stained bandage wraps, blood-red glow.
Silhouette: serrated blades with forked tips and barb teeth, a thorned rib guard, faceted pommels,
lean and aggressive. Motif: a barbed heart with a stitched wound (original); accent: a thorn star."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def barbed_heart(size):
    """Original emblem: a heart with barbs on its shoulders and a vertical stitched wound cut through it."""
    s = size / 2
    heart = unary_union([Point(-s * 0.36, s * 0.22).buffer(s * 0.42, 14), Point(s * 0.36, s * 0.22).buffer(s * 0.42, 14),
                         _p([(-s * 0.76, s * 0.12), (s * 0.76, s * 0.12), (0, -s * 0.95)])])
    barbs = [_p([(sx * s * 0.62, s * 0.02), (sx * s * 0.99, -s * 0.4), (sx * s * 0.4, -s * 0.32)]) for sx in (1, -1)]
    barbs.append(_p([(-s * 0.1, s * 0.4), (0, s * 0.95), (s * 0.1, s * 0.4)]))
    wound = _p([(0, s * 0.42), (s * 0.08, -s * 0.05), (0, -s * 0.6), (-s * 0.08, -s * 0.05)])
    stitches = unary_union([box(-s * 0.26, z - s * 0.04, s * 0.26, z + s * 0.04) for z in (s * 0.18, -s * 0.12)])
    return unary_union([heart] + barbs).difference(wound.union(stitches)).buffer(0)


def thorn_star(size):
    """Small accent: four-point barbed thorn star with a pierced centre."""
    s = size / 2
    pts = []
    for i in range(8):
        a = math.pi / 2 + i * math.pi / 4 + (0.18 if i % 2 else 0)
        r = s * (0.98 if i % 2 == 0 else 0.3)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return _p(pts).difference(Point(0, 0).buffer(s * 0.12, 8)).buffer(0)


def rib_guard(w, d):
    """Custom guard: a ribcage-like bar with downward hooked thorns on each side."""
    out = [box(-w * 0.75, -d * 0.32, w * 0.75, d * 0.36)]
    for sx in (1, -1):
        out.append(_p([(sx * w * 0.6, d * 0.36), (sx * w * 1.05, d * 0.9), (sx * w * 0.98, d * 0.3),
                       (sx * w * 0.75, -d * 0.32)]))
        out.append(_p([(sx * w * 0.3, -d * 0.3), (sx * w * 0.5, -d * 1.0), (sx * w * 0.52, -d * 0.3)]))
    return unary_union(out).buffer(0)


STYLE = dict(
    id='sacrier', race='Sacrier',
    names=dict(fists='Scarknuckle Wraps', staff='Veinward Staff', spear='Lifethirst Pike', sword='Bloodpact',
               greatsword="Martyr's Cleave", gun='Heartdrum Pistol', dagger='Lancet of Vows', scythe='Pulsereaper',
               katana='Crimson Stitch', dual_blades='Twin Wounds', chain='Shacklewound', blunt='Painmonger Mace'),
    mats=dict(
        # blackened blood-iron (real metal), cool dark with bright worn edges
        primary=dict(base='#4A4447', light='#9A8F92', dark='#1A1617', rough=0.4, metal=1.0, relief='hammered',
                     paint_light=0.6),
        # crimson lacquer trim, chips to steel
        secondary=dict(base='#8E1626', light='#C8404E', dark='#3E070E', rough=0.34, metal=0.0, relief='hammered',
                       chip=0.5),
        # bone inlays
        accent=dict(base='#D8CBB0', light='#F4ECDA', dark='#8A7A5E', rough=0.55, metal=0.0, relief='hammered'),
        # blood-stained bandage wrap
        grip=dict(base='#BFAE94', light='#E6D9C2', dark='#6E3A30', rough=0.9, metal=0.0, relief='weave'),
        # dark oxblood leather hafts
        haft=dict(base='#3A1C1E', light='#6A383A', dark='#170A0B', rough=0.75, metal=0.0, relief='leather'),
        # living blood glow
        glow=dict(base='#FF2B3C', light='#FF8A90', dark='#8A0012', rough=0.12, metal=0.0, relief='none', emit=1.8),
    ),
    blade=dict(edge='serrated', tip='split', width=0.92, holes='none', notch='teeth'),
    guard=rib_guard, pommel='faceted', grip_wraps=8, chain_link='box',
    motif=barbed_heart, motif2=thorn_star,
    head=dict(staff='orb', blunt='mace', gun='pistol'),
    silhouette=dict(curve=0.1, spikes=True, chunky=0.95, barbs=True),
)
