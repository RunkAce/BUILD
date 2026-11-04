"""Sadida: nature-bound doll-makers of the great tree; plants, thorns, brambles, living wood.
Colour story: leaf-green lacquered heartwood, dark bark, blossom-pink enamel, vine-fibre wraps,
chartreuse sap glow. Silhouette: leaf-swelled blades with thorn teeth, leaf guards, seed-pod pommels,
gently organic curvature. Motif: a seedling - seed, root tail, two unequal upswept leaves (original); accent: a four-petal bud."""
import math

from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _leaf(base, tip, width, n=10):
    """Narrow lens leaf from base to tip, bellied `width` (fraction of its length) to each side."""
    (bx, bz), (tx, tz) = base, tip
    dx, dz = tx - bx, tz - bz
    ln = math.hypot(dx, dz) or 1.0
    nx, nz = -dz / ln * width * ln, dx / ln * width * ln
    a = geo.bezier(base, (bx + dx * 0.3 + nx, bz + dz * 0.3 + nz), (bx + dx * 0.75 + nx * 0.7, bz + dz * 0.75 + nz * 0.7),
                   tip, n)
    b = geo.bezier(tip, (bx + dx * 0.75 - nx * 0.45, bz + dz * 0.75 - nz * 0.45), (bx + dx * 0.3 - nx * 0.6,
                   bz + dz * 0.3 - nz * 0.6), base, n)
    return _p(a + b[1:-1])


def sprout(size):
    """Original emblem: a seedling. A solid teardrop seed with a short curling root tail below, a stem rising from
    its tip and two asymmetric, narrow, upswept leaves (one large, one small)."""
    s = size / 2
    seed = _p(geo.bezier((0, s * 0.02), (s * 0.44, -s * 0.1), (s * 0.44, -s * 0.66), (0, -s * 0.66), 10) +
              geo.bezier((0, -s * 0.66), (-s * 0.44, -s * 0.66), (-s * 0.44, -s * 0.1), (0, s * 0.02), 10)[1:-1])
    # root tail: tapers from the seed base and curls off to one side
    rp = geo.bezier((0, -s * 0.6), (s * 0.02, -s * 0.82), (-s * 0.1, -s * 0.92), (-s * 0.3, -s * 0.98), 8)
    left, right = [], []
    for i, (x, z) in enumerate(rp):
        xa, za = rp[max(i - 1, 0)]
        xb, zb = rp[min(i + 1, len(rp) - 1)]
        tx, tz = xb - xa, zb - za
        ln = math.hypot(tx, tz) or 1.0
        hw = s * (0.09 - 0.07 * i / (len(rp) - 1))
        left.append((x - tz / ln * hw, z + tx / ln * hw))
        right.append((x + tz / ln * hw, z - tx / ln * hw))
    root = Polygon(left + right[::-1]).buffer(0)
    stem = _p([(-s * 0.13, -s * 0.05), (s * 0.13, -s * 0.05), (s * 0.11, s * 0.4), (-s * 0.1, s * 0.4)])
    big = _leaf((s * 0.0, s * 0.24), (s * 0.66, s * 0.98), 0.4)
    small = _leaf((s * 0.0, s * 0.14), (-s * 0.54, s * 0.62), 0.46)
    g = unary_union([seed, root, stem, big, small]).buffer(0)
    x0, _, x1, _ = g.bounds
    return affinity.translate(g, -(x0 + x1) / 2, 0.0)       # centre the asymmetric silhouette


def bud(size):
    """Small accent: four-petal blossom bud with a pierced heart."""
    s = size / 2
    petals = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        c = Point(math.cos(a) * s * 0.45, math.sin(a) * s * 0.45).buffer(s * 0.5, 10)
        petals.append(c)
    return unary_union(petals).intersection(Point(0, 0).buffer(s * 0.98, 20)).difference(
        Point(0, 0).buffer(s * 0.2, 8)).buffer(0)


STYLE = dict(
    id='sadida', race='Sadida',
    names=dict(fists='Bramblegrasp Knuckles', staff='Rootcradle Staff', spear='Thornspire', sword='Greenvow',
               greatsword='Elderbough', gun='Seedspitter', dagger='Briarnip', scythe='Harvest Hush',
               katana='Willowdraw', dual_blades='Twin Sprigs', chain='Creeperlash', blunt='Burlknot Cudgel'),
    mats=dict(
        # lacquered living heartwood (dielectric): bright leaf green, reads as the hero colour
        primary=dict(base='#7FA548', light='#C6DE82', dark='#34511F', rough=0.48, metal=0.0, relief='leather',
                     paint_light=0.7),
        # dark bark trim
        secondary=dict(base='#5C3F2B', light='#8E6A4A', dark='#2A1B12', rough=0.82, metal=0.0, relief='leather'),
        # blossom-pink enamel inlays
        accent=dict(base='#D9789A', light='#F4AFC6', dark='#7E3350', rough=0.36, metal=0.0, relief='hammered',
                    chip=0.3),
        # woven vine fibre wrap
        grip=dict(base='#8E7C4E', light='#C2B07A', dark='#463B22', rough=0.9, metal=0.0, relief='weave'),
        # bark-clad hafts
        haft=dict(base='#6B4A30', light='#9C7650', dark='#30200F', rough=0.85, metal=0.0, relief='leather'),
        # chartreuse sap
        glow=dict(base='#B6EE48', light='#E6FF9A', dark='#5E9A12', rough=0.15, metal=0.0, relief='none', emit=1.6),
    ),
    blade=dict(edge='leaf', tip='point', width=1.08, holes='none', notch='teeth'),
    guard='leaf', pommel='orb', grip_wraps=5, chain_link='oval',
    motif=sprout, motif2=bud,
    head=dict(staff='motif', blunt='club', gun='rifle'),
    silhouette=dict(curve=0.25, spikes=True, chunky=1.0, organic=True, thorns=True),
)
