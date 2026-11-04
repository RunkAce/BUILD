"""Eliotrope: serene wanderers of the stars who fold space, opening paired portals to strike from anywhere.
Colour story: pale moonsilver, deep celestial-teal enamel, white-gold trim, sky-blue cloth wraps, pale birch
hafts, one mint-turquoise portal glow. Silhouettes are light and elegant: slender straight blades pierced by
round 'portal' holes, a halo-ring guard the blade emerges through with swept fins, orb pommels, round links.
Motif: an original portal gate (thick ring with an off-centre opening and a traveller spark inside);
small accent: two interlinked portal rings."""
import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def portal_gate(size):
    """Thick ring with an off-centre opening (reads as a gate in perspective) and a 4-point spark inside."""
    s = size / 2
    outer = Point(0, 0).buffer(s * 0.98, 24)
    hole = Point(s * 0.12, s * 0.06).buffer(s * 0.6, 20)
    ring = outer.difference(hole)
    # one clean swirl gap through the thick (lower-left) side of the ring
    ring = ring.difference(_p([(-s * 0.2, -s * 0.3), (-s * 0.62, -s * 1.0), (-s * 0.9, -s * 0.72)]))
    cx, cz, k = s * 0.12, s * 0.06, s * 0.36
    spark = _p([(cx, cz + k), (cx + k * 0.26, cz + k * 0.26), (cx + k, cz), (cx + k * 0.26, cz - k * 0.26),
                (cx, cz - k), (cx - k * 0.26, cz - k * 0.26), (cx - k, cz), (cx - k * 0.26, cz + k * 0.26)])
    return unary_union([ring, spark]).buffer(0)


def twin_rings(size):
    s = size / 2
    out = []
    for cx in (-s * 0.36, s * 0.36):
        out.append(Point(cx, 0).buffer(s * 0.62, 14).difference(Point(cx, 0).buffer(s * 0.36, 12)))
    return unary_union(out).buffer(0)


def halo_guard(w, d):
    """Halo ring raised around the blade root, sitting on a thin bar with swept fins at each end."""
    r_out = max(w * 0.6, d * 1.25)
    r_in = r_out * 0.72
    halo = Point(0, d * 0.55).buffer(r_out, 24).difference(Point(0, d * 0.55).buffer(r_in, 24))
    bar = box_(-w * 0.75, -d * 0.22, w * 0.75, d * 0.22)
    fins = []
    for sx in (1, -1):
        # lens-shaped fin swept slightly back-down, like a gliding wingtip
        a = geo.bezier((sx * w * 0.55, d * 0.28), (sx * w * 0.8, d * 0.4), (sx * w * 1.0, d * 0.1),
                       (sx * w * 1.18, -d * 0.45), 10)
        b = geo.bezier((sx * w * 1.18, -d * 0.45), (sx * w * 0.95, -d * 0.3), (sx * w * 0.8, -d * 0.3),
                       (sx * w * 0.55, -d * 0.28), 10)
        fins.append(_p(a + b[1:]))
    return unary_union([halo, bar] + fins).buffer(0)


def box_(x0, z0, x1, z1):
    return _p([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])


STYLE = dict(
    id='eliotrope', race='Eliotrope',
    names=dict(fists='Blinkstep Knuckles', staff='Gatewarden Staff', spear='Farreach', sword='Threshold',
               greatsword='Skyrift', gun='Gatebolt Rifle', dagger='Blinkfang', scythe='Riftreaper',
               katana='Driftcut', dual_blades='Twin Gates', chain='Loopline Tether', blunt='Rimfall Mace'),
    mats=dict(
        primary=dict(base='#C9D5DC', light='#F3F9FC', dark='#5E6E78', rough=0.3, metal=1.0, relief='hammered',
                     paint_light=0.55),                                             # pale moonsilver
        secondary=dict(base='#1F6474', light='#4FA3B3', dark='#0A2C35', rough=0.34, metal=0.0, relief='hammered',
                       chip=0.45),                                                  # celestial teal enamel
        accent=dict(base='#E2D29C', light='#FFF5D2', dark='#86733F', rough=0.26, metal=1.0, relief='hammered',
                    paint_light=0.5),                                               # white gold
        grip=dict(base='#7DB4D2', light='#BFE0F0', dark='#2F5F7A', rough=0.88, metal=0.0, relief='weave'),
                                                                                    # sky-blue cloth
        haft=dict(base='#CDBB9A', light='#EDE0C6', dark='#7E6C4E', rough=0.66, metal=0.0, relief='leather'),
                                                                                    # pale birch
        glow=dict(base='#3DFFD2', light='#B8FFF0', dark='#0FA98A', rough=0.12, metal=0.0, relief='none',
                  emit=1.8),                                                        # portal turquoise
    ),
    blade=dict(edge='straight', tip='point', width=0.84, holes='rings', notch='none'),
    guard=halo_guard, pommel='orb', grip_wraps=5, chain_link='ring',
    motif=portal_gate, motif2=twin_rings,
    head=dict(staff='motif', blunt='mace', gun='rifle'),
    silhouette=dict(curve=0.0, spikes=False, chunky=0.9, slender=True, portals=True),
)
