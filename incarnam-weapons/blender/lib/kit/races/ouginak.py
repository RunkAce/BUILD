"""Ouginak: hound-blooded trackers who hunt their prey relentlessly and turn feral in a rage.
Colour story: warm gunmetal iron, tawny hide trim, fang-bone inlays, oxblood leather wraps,
pale hunting-moon glow. Silhouette: jagged bitten edges with hooked canine tips, fang guards
and fang pommels, bone chain links, heavy and brutish. Motif: a pair of bared fangs under a bite arch
(original); accent: a paw print."""
import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def bared_fangs(size):
    """Original emblem: a gum arch with two long curved canines and a small incisor row between them."""
    s = size / 2
    arch = Point(0, s * 0.2).buffer(s * 0.95, 24).difference(Point(0, s * 0.05).buffer(s * 0.7, 24))
    arch = arch.intersection(_p([(-s, s * 0.05), (s, s * 0.05), (s, s), (-s, s)]))
    fangs = []
    for sx in (1, -1):
        fangs.append(_p(geo.bezier((sx * s * 0.82, s * 0.15), (sx * s * 0.78, -s * 0.35), (sx * s * 0.6, -s * 0.75),
                                   (sx * s * 0.3, -s * 0.95), 10) +
                        geo.bezier((sx * s * 0.3, -s * 0.95), (sx * s * 0.42, -s * 0.5), (sx * s * 0.45, -s * 0.15),
                                   (sx * s * 0.42, s * 0.15), 10)[1:]))
    teeth = [_p([(x - s * 0.1, s * 0.12), (x + s * 0.1, s * 0.12), (x, -s * 0.2)]) for x in (-s * 0.16, s * 0.16)]
    return unary_union([arch] + fangs + teeth).buffer(0)


def paw(size):
    """Small accent: a paw print (heel pad + four toe pads)."""
    s = size / 2
    heel = unary_union([Point(x, z).buffer(s * 0.3, 12) for x, z in
                        ((-s * 0.26, -s * 0.5), (s * 0.26, -s * 0.5), (0, -s * 0.3))])
    toes = [Point(x, z).buffer(s * 0.19, 10) for x, z in
            ((-s * 0.68, s * 0.12), (-s * 0.25, s * 0.62), (s * 0.25, s * 0.62), (s * 0.68, s * 0.12))]
    return unary_union([heel] + toes).intersection(Point(0, 0).buffer(s * 0.99, 24)).buffer(0)


def jaw_guard(w, d):
    """Custom guard: a heavy jaw bar whose ends rise into fangs that bite up around the blade root."""
    out = [_p([(-w * 0.8, -d * 0.45), (w * 0.8, -d * 0.45), (w * 0.9, d * 0.3), (-w * 0.9, d * 0.3)])]
    for sx in (1, -1):
        out.append(_p(geo.bezier((sx * w * 0.95, d * 0.2), (sx * w * 1.0, d * 0.9), (sx * w * 0.8, d * 1.4),
                                 (sx * w * 0.5, d * 1.7), 8) +
                      geo.bezier((sx * w * 0.5, d * 1.7), (sx * w * 0.62, d * 1.2), (sx * w * 0.6, d * 0.7),
                                 (sx * w * 0.45, d * 0.25), 8)[1:]))
        out.append(_p([(sx * w * 0.25, -d * 0.4), (sx * w * 0.42, -d * 1.05), (sx * w * 0.55, -d * 0.4)]))
    return unary_union(out).buffer(0)


STYLE = dict(
    id='ouginak', race='Ouginak',
    names=dict(fists='Mauler Grips', staff='Moonhowl Staff', spear='Packfang Pike', sword='Scentseeker',
               greatsword="Alpha's Jaw", gun='Houndbark Rifle', dagger='Dewclaw', scythe='Gnawmoon',
               katana='Lone Fang', dual_blades='Twin Canines', chain='Leashbreaker', blunt='Marrowcrack Club'),
    mats=dict(
        # warm rough-forged gunmetal iron
        primary=dict(base='#6E665D', light='#B7AE9F', dark='#27231F', rough=0.46, metal=1.0, relief='hammered',
                     paint_light=0.55),
        # tawny hide trim
        secondary=dict(base='#A06C3A', light='#D29E66', dark='#4C2E14', rough=0.8, metal=0.0, relief='leather'),
        # fang-bone inlays
        accent=dict(base='#E3D7B8', light='#FBF4E2', dark='#8E8064', rough=0.5, metal=0.0, relief='hammered'),
        # oxblood leather wrap
        grip=dict(base='#5C2A22', light='#8E4A3C', dark='#26100C', rough=0.78, metal=0.0, relief='leather'),
        # dark smoked wood
        haft=dict(base='#3F2F25', light='#6E5644', dark='#19110C', rough=0.8, metal=0.0, relief='leather'),
        # pale hunting-moon glow
        glow=dict(base='#A6D6FF', light='#E2F2FF', dark='#3A7EC8', rough=0.12, metal=0.0, relief='none', emit=1.6),
    ),
    blade=dict(edge='jagged', tip='hook', width=1.05, holes='none', notch='scoop'),
    guard=jaw_guard, pommel='fang', grip_wraps=7, chain_link='bone',
    motif=bared_fangs, motif2=paw,
    head=dict(staff='crescent', blunt='club', gun='rifle'),
    silhouette=dict(curve=0.12, spikes=True, chunky=1.18, feral=True),
)
