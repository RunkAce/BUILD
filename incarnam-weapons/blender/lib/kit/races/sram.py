"""Sram: skeletal shadow-assassins who strike from behind and hide traps; stealth, cruelty, the unseen.
Colour story: blackened gunmetal, aged bone, tarnished silver, plum-black leather, ebony, a single
toxic-violet glow. Silhouettes are cruel and hooked: jagged edges with teeth, hooked tips, downward
fang guards, ring pommels, bone links. Motif: an original hooded domino-mask with slanted eye cuts;
small accent: a three-point caltrop (trap)."""
import math

from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _ellipse(cx, cz, rx, rz, rot=0.0, res=10):
    e = affinity.scale(Point(0, 0).buffer(1.0, res), rx, rz, origin=(0, 0))
    if rot:
        e = affinity.rotate(e, rot, origin=(0, 0))
    return affinity.translate(e, cx, cz)


def hood_mask(size):
    """Hooded cowl: pointed-arch hood over flared shoulders, a dark face-opening and two slanted eye slits
    glinting inside it. Fits size x size."""
    s = size / 2
    right = geo.bezier((0, s), (s * 0.42, s * 0.72), (s * 0.66, s * 0.2), (s * 0.62, -s * 0.38), 10) + \
        [(s * 0.98, -s * 0.98), (0, -s * 0.78)]
    hood = _poly(geo.mirror_x(right))
    face = geo.bezier((0, s * 0.5), (s * 0.3, s * 0.36), (s * 0.42, -s * 0.05), (s * 0.3, -s * 0.42), 8) + \
        [(0, -s * 0.5)]
    hood = hood.difference(_poly(geo.mirror_x(face)))
    # two bold slanted eye shards glinting inside the dark opening
    eyes = [_poly([(sx * s * 0.05, -s * 0.12), (sx * s * 0.36, s * 0.16), (sx * s * 0.3, -s * 0.26)]) for sx in (1, -1)]
    return unary_union([hood] + eyes).buffer(0)


def caltrop(size):
    """Three-point caltrop / trap rune with a socket."""
    s = size / 2
    pts = []
    for i in range(6):
        a = math.radians(90 + 60 * i)
        r = s if i % 2 == 0 else s * 0.3
        pts.append((r * math.cos(a), r * math.sin(a)))
    return _poly(pts).difference(Point(0, 0).buffer(s * 0.13, 8)).buffer(0)


STYLE = dict(
    id='sram', race='Sram',
    names=dict(fists='Gravegrip Claws', staff='Hushbone Staff', spear='Nightneedle', sword='Shadecut',
               greatsword='Ossuary', gun='Snaretrap Pistol', dagger='Whisperfang', scythe='Marrowscythe',
               katana='Veilcut', dual_blades='Twin Shivs', chain='Snarechain', blunt='Knucklebone Cudgel'),
    mats=dict(
        primary=dict(base='#4A4850', light='#9B98A6', dark='#1A191E', rough=0.38, metal=1.0, relief='hammered',
                     paint_light=0.5),                                              # blackened gunmetal
        secondary=dict(base='#D6CAB0', light='#F4ECD8', dark='#857A62', rough=0.62, metal=0.0, relief='leather'),
                                                                                    # aged bone
        accent=dict(base='#A3A1A8', light='#DCDAE0', dark='#4C4A52', rough=0.32, metal=1.0, relief='filigree',
                    paint_light=0.5),                                               # tarnished silver
        grip=dict(base='#3A2840', light='#614569', dark='#180F1C', rough=0.8, metal=0.0, relief='leather'),
        haft=dict(base='#2E2629', light='#54474C', dark='#120E10', rough=0.66, metal=0.0, relief='leather'),
        glow=dict(base='#B068FF', light='#DDB8FF', dark='#5E22B0', rough=0.15, metal=0.0, relief='none',
                  emit=1.7),                                                        # toxic violet
    ),
    blade=dict(edge='jagged', tip='hook', width=0.85, holes='none', notch='none'),
    guard='fang', pommel='ring', grip_wraps=7, chain_link='bone',
    motif=hood_mask, motif2=caltrop,
    head=dict(staff='motif', blunt='club', gun='pistol'),
    silhouette=dict(curve=0.25, spikes=True, chunky=0.9),
)
