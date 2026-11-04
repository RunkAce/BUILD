"""Eniripsa: gentle fairy-folk healers whose spoken words mend wounds; care, blossoms and soft light.
Colour story: pearl-white steel, blush-rose enamel, champagne gold filigree, cream cloth wraps, birch
hafts, rose-pink 'healing word' glow. Silhouettes are soft and rounded: wavy petal edges, a four-petal
blossom guard, orb pommels, ring chains. Motif: an original dewdrop with a sprouting-leaf cut;
small accent: a five-petal blossom."""
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _ellipse(cx, cz, rx, rz, rot=0.0, res=12):
    e = affinity.scale(Point(0, 0).buffer(1.0, res), rx, rz, origin=(0, 0))
    if rot:
        e = affinity.rotate(e, rot, origin=(0, 0))
    return affinity.translate(e, cx, cz)


def dewdrop(size):
    """Original dewdrop with a leaf-shaped cut sprouting inside it. Fits size x size."""
    s = size / 2
    bulb = Point(0, -s * 0.34).buffer(s * 0.66, 16)
    drop = unary_union([bulb, _poly([(0, s), (s * 0.5, -s * 0.05), (-s * 0.5, -s * 0.05)])]).convex_hull
    leaf = Point(-s * 0.15, 0).buffer(s * 0.3, 10).intersection(Point(s * 0.15, 0).buffer(s * 0.3, 10))
    leaf = affinity.scale(leaf, 1.0, 1.55, origin=(0, 0))
    leaf = affinity.rotate(leaf, -32, origin=(0, 0))
    leaf = affinity.translate(leaf, s * 0.08, -s * 0.3)
    return drop.difference(leaf).buffer(0)


def blossom(size):
    """Five-petal blossom with an open heart (centre hole)."""
    import math
    s = size / 2
    petals = [Point(s * 0.52 * math.cos(math.radians(90 + 72 * i)), s * 0.52 * math.sin(math.radians(90 + 72 * i)))
              .buffer(s * 0.42, 10) for i in range(5)]
    flower = unary_union(petals + [Point(0, 0).buffer(s * 0.5, 12)])
    return flower.difference(Point(0, 0).buffer(s * 0.2, 10)).buffer(0)


def petal_guard(w, d):
    """Four-petal guard: two broad upper petals swept outward, two small lower petals, round hub."""
    parts = [Point(0, 0).buffer(d * 0.6, 14)]
    for sx in (1, -1):
        parts.append(_ellipse(sx * w * 0.52, d * 0.28, w * 0.48, d * 0.62, rot=sx * -28))
        parts.append(_ellipse(sx * w * 0.36, -d * 0.48, w * 0.28, d * 0.42, rot=sx * 35))
    return unary_union(parts).buffer(0)


STYLE = dict(
    id='eniripsa', race='Eniripsa',
    names=dict(fists='Mendgrip Gauntlets', staff='Lullaby Staff', spear='Dewspire', sword='Petalvow',
               greatsword='Rosewarden', gun='Balmcaster', dagger='Thornkiss', scythe='Bloomsickle',
               katana='Blushsong', dual_blades='Twin Remedies', chain='Tendril Tether', blunt='Kindheart Mallet'),
    mats=dict(
        primary=dict(base='#E8DAD5', light='#FFF8F5', dark='#9A8480', rough=0.4, metal=1.0, relief='hammered',
                     paint_light=0.55),                                             # pearl-white steel
        secondary=dict(base='#D47A93', light='#F2A9BD', dark='#7A3448', rough=0.36, metal=0.0, relief='hammered',
                       chip=0.45),                                                  # blush-rose enamel
        accent=dict(base='#CDB487', light='#F6E6C2', dark='#6E5634', rough=0.26, metal=1.0, relief='filigree',
                    paint_light=0.5),                                               # champagne gold
        grip=dict(base='#EDE1CF', light='#FCF8F0', dark='#A69780', rough=0.88, metal=0.0, relief='weave'),
        haft=dict(base='#E2D6C0', light='#F7F0E2', dark='#9A8A6E', rough=0.66, metal=0.0, relief='leather'),
        glow=dict(base='#FF92C9', light='#FFD0E8', dark='#C2427F', rough=0.15, metal=0.0, relief='none',
                  emit=1.5),                                                        # healing-word rose
    ),
    blade=dict(edge='wavy', tip='point', width=0.95, holes='none', notch='none'),
    guard=petal_guard, pommel='orb', grip_wraps=5, chain_link='ring',
    motif=dewdrop, motif2=blossom,
    head=dict(staff='orb', blunt='motif', gun='pistol'),
    silhouette=dict(curve=0.0, spikes=False, chunky=0.95, round=True),
)
