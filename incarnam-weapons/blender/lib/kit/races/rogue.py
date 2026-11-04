"""Rogue: flamboyant bandits and gun-slinging bomb-makers; blackpowder, fuses, flintlocks and loot.
Colour story: blued gunmetal, dusty teal-grey bandana lacquer, heavy bandit brass, black leather, tarred oak,
and one burnt-orange lit-fuse spark as the only warm-red note (no red lacquer: that is Sacrier's). Silhouettes are swashbuckling and practical: single-edged clipped cutlass blades
with a saw-backed edge, a knuckle-bow guard that loops down over the hand, bomb-ball pommels, box links.
Motif: an original banded powder keg with a curling lit fuse; small accent: a round fused bomb."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _taper(path, w0, w1):
    n = len(path)
    left, right = [], []
    for i, (x, z) in enumerate(path):
        xa, za = path[max(i - 1, 0)]
        xb, zb = path[min(i + 1, n - 1)]
        tx, tz = xb - xa, zb - za
        ln = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / ln, tx / ln
        hw = w0 + (w1 - w0) * i / (n - 1)
        left.append((x + nx * hw, z + nz * hw))
        right.append((x - nx * hw, z - nz * hw))
    return Polygon(left + right[::-1]).buffer(0)


def powder_keg(size):
    """Barrel body with two cut hoop bands, a bung on top and a fuse curling up to a burst spark."""
    s = size / 2
    # tall bulging barrel (stave sides bow outward); hoops stand proud of the staves
    right = [(0, s * 0.42)] + geo.bezier((s * 0.5, s * 0.42), (s * 0.82, s * 0.2), (s * 0.82, -s * 0.76),
                                         (s * 0.5, -s * 0.98), 10) + [(0, -s * 0.98)]
    keg = _p(geo.mirror_x(right))
    hoops = [box(-s * 0.8, zc - s * 0.1, s * 0.8, zc + s * 0.1) for zc in (s * 0.2, -s * 0.74)]
    keg = unary_union([keg] + hoops)
    # dark stave seams between the hoops so it reads as wood, not a pot
    for x in (-s * 0.3, s * 0.3):
        keg = keg.difference(box(x - s * 0.05, -s * 0.5, x + s * 0.05, -s * 0.04))
    bung = box(-s * 0.14, s * 0.38, s * 0.14, s * 0.52)
    fuse = _taper(geo.bezier((0, s * 0.48), (s * 0.04, s * 0.76), (s * 0.3, s * 0.66), (s * 0.48, s * 0.72), 8),
                  s * 0.12, s * 0.1)
    spark = []
    cx, cz = s * 0.66, s * 0.74
    for i in range(10):
        a = math.radians(90 + 36 * i)
        r = s * 0.26 if i % 2 == 0 else s * 0.12
        spark.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return unary_union([keg, bung, fuse, _p(spark)]).buffer(0)


def bomb(size):
    """Round bomb with a fuse cap and a crescent glint cut."""
    s = size / 2
    ball = Point(0, -s * 0.14).buffer(s * 0.84, 16)
    cap = _p([(s * 0.18, s * 0.5), (s * 0.5, s * 0.82), (s * 0.72, s * 0.6), (s * 0.4, s * 0.28)])
    glint = Point(-s * 0.3, s * 0.12).buffer(s * 0.26, 10).difference(Point(-s * 0.18, 0.0).buffer(s * 0.28, 10))
    return unary_union([ball, cap]).difference(glint).buffer(0)


def knuckle_bow(w, d):
    """Cutlass guard: short shell bar, a knuckle-bow sweeping down over the hand on +X, a curled quillon on -X."""
    bar = _p([(-w * 0.72, -d * 0.28), (w * 0.78, -d * 0.36), (w * 0.82, d * 0.3), (-w * 0.66, d * 0.32)])
    bow = _taper(geo.bezier((w * 0.72, 0.0), (w * 1.05, -d * 0.9), (w * 0.72, -d * 2.2), (w * 0.3, -d * 2.75), 16),
                 d * 0.3, d * 0.17)
    knob = Point(w * 0.28, -d * 2.75).buffer(d * 0.24, 10)
    quill = _taper(geo.bezier((-w * 0.62, 0.0), (-w * 0.95, d * 0.05), (-w * 1.0, d * 0.6), (-w * 0.82, d * 0.9), 10),
                   d * 0.24, d * 0.12)
    qball = Point(-w * 0.82, d * 0.92).buffer(d * 0.2, 10)
    return unary_union([bar, bow, knob, quill, qball]).buffer(0)


STYLE = dict(
    id='rogue', race='Rogue',
    names=dict(fists='Powderkeg Knuckles', staff='Fuselight Staff', spear='Blackpowder Pike',
               sword='Cutpurse Cutlass', greatsword='Kegsplitter', gun='Smokejack Pistol', dagger='Pickpocket',
               scythe='Fusereaper', katana='Quickdraw Edge', dual_blades='Smash and Grab', chain='Flintlash',
               blunt='Kegknocker Mace'),
    mats=dict(
        primary=dict(base='#5F676C', light='#AEB7BC', dark='#202629', rough=0.38, metal=1.0, relief='hammered',
                     paint_light=0.55),                                             # blued gunmetal
        secondary=dict(base='#3E5A5E', light='#739498', dark='#16262A', rough=0.4, metal=0.0, relief='hammered',
                       chip=0.55),                                                  # dusty teal-grey bandana lacquer
        accent=dict(base='#CC9A3C', light='#F6D88E', dark='#624212', rough=0.26, metal=1.0, relief='hammered',
                    paint_light=0.5),                                               # heavy bandit brass
        grip=dict(base='#2C2422', light='#5A4A42', dark='#120E0D', rough=0.8, metal=0.0, relief='leather'),
        haft=dict(base='#5B3E2A', light='#8A6446', dark='#28190F', rough=0.7, metal=0.0, relief='leather'),
                                                                                    # tarred oak
        glow=dict(base='#FF7A1C', light='#FFC27C', dark='#B8460A', rough=0.12, metal=0.0, relief='none',
                  emit=1.8),                                                        # burnt-orange lit fuse
    ),
    blade=dict(edge='straight', tip='clip', width=1.05, holes='none', notch='teeth', single_edge=True),
    guard=knuckle_bow, pommel='orb', grip_wraps=6, chain_link='box',
    motif=powder_keg, motif2=bomb,
    head=dict(staff='cage', blunt='mace', gun='pistol'),
    silhouette=dict(curve=0.18, spikes=False, chunky=1.05, swashbuckler=True),
)
