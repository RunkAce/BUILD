"""Masqueraider: carnival performers who fight behind interchangeable masks, switching moods mid-dance.
Colour story: bright silvered steel, deep plum lacquer, porcelain-white trim (the signature), raspberry ribbon
wraps, plum-black lacquered ebony, one hot-magenta glow (black-and-white belongs to Pandawa). Silhouettes are theatrical and flowing: leaf blades with a
swallow-tail split tip, a jester-collar guard whose drooping points end in bells, ring pommels for ribbons.
Motif: an original harlequin lozenge mask (diamond face, almond eyes, forehead diamond); accent: a jester bell."""
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


def harlequin_mask(size):
    """Lozenge face with two upswept almond eye cuts, a forehead diamond cut and a small chin point."""
    s = size / 2
    face = _p([(0, s), (s * 0.92, s * 0.08), (s * 0.62, -s * 0.5), (0, -s), (-s * 0.62, -s * 0.5),
               (-s * 0.92, s * 0.08)])
    eyes = []
    for sx in (1, -1):
        eyes.append(_p([(sx * s * 0.1, s * 0.02), (sx * s * 0.3, s * 0.2), (sx * s * 0.62, s * 0.18),
                        (sx * s * 0.42, -s * 0.06), (sx * s * 0.18, -s * 0.08)]))
    brow = _p([(0, s * 0.68), (s * 0.12, s * 0.48), (0, s * 0.3), (-s * 0.12, s * 0.48)])
    mouth = _p([(-s * 0.26, -s * 0.38), (0, -s * 0.5), (s * 0.26, -s * 0.38), (0, -s * 0.6)])
    return face.difference(unary_union(eyes + [brow, mouth])).buffer(0)


def bell(size):
    """Jester bell: round body with a slot mouth and a hanging loop."""
    s = size / 2
    body = Point(0, -s * 0.18).buffer(s * 0.78, 14)
    slot = box(-s * 0.62, -s * 0.36, s * 0.62, -s * 0.2)
    hole = Point(0, -s * 0.6).buffer(s * 0.12, 8)
    loop = Point(0, s * 0.72).buffer(s * 0.28, 10).difference(Point(0, s * 0.72).buffer(s * 0.13, 8))
    return unary_union([body.difference(slot).difference(hole), loop]).buffer(0)


def jester_guard(w, d):
    """Jester collar: a central lozenge and two drooping points per side, each finished with a bell ball."""
    out = [_p([(0, d * 0.75), (w * 0.4, 0.0), (0, -d * 0.6), (-w * 0.4, 0.0)])]
    for sx in (1, -1):
        long_ = geo.bezier((sx * w * 0.2, d * 0.1), (sx * w * 0.6, d * 0.55), (sx * w * 1.0, d * 0.2),
                           (sx * w * 1.02, -d * 0.75), 9)
        out.append(_taper(long_, d * 0.36, d * 0.08))
        out.append(Point(sx * w * 1.02, -d * 0.85).buffer(d * 0.24, 6))
        short = geo.bezier((sx * w * 0.2, -d * 0.05), (sx * w * 0.45, -d * 0.1), (sx * w * 0.6, -d * 0.5),
                           (sx * w * 0.55, -d * 1.05), 6)
        out.append(_taper(short, d * 0.26, d * 0.07))
        out.append(Point(sx * w * 0.55, -d * 1.12).buffer(d * 0.18, 5))
    return unary_union(out).buffer(0)


STYLE = dict(
    id='masqueraider', race='Masqueraider',
    names=dict(fists='Encore Knuckles', staff='Facechanger Marotte', spear='Curtaincall Lance', sword='Bravura',
               greatsword='Grand Finale', gun='Confetti Cannon', dagger='Stage Whisper', scythe='Final Act',
               katana='Pirouette', dual_blades='Smile and Sorrow', chain='Ribbonlash', blunt='Slapstick Maul'),
    mats=dict(
        primary=dict(base='#C4C7CF', light='#F4F6FA', dark='#565A63', rough=0.3, metal=1.0, relief='hammered',
                     paint_light=0.55),                                             # bright silvered steel
        secondary=dict(base='#5B1E4E', light='#9A4C86', dark='#260A20', rough=0.32, metal=0.0, relief='hammered',
                       chip=0.45),                                                  # deep plum lacquer
        accent=dict(base='#E6E0D6', light='#FFFFFF', dark='#9A9286', rough=0.34, metal=0.0, relief='none'),
                                                                                    # porcelain (mask) trim
        grip=dict(base='#A82356', light='#DA5687', dark='#4E0C25', rough=0.86, metal=0.0, relief='weave'),
                                                                                    # raspberry ribbon
        haft=dict(base='#3A2035', light='#6A4762', dark='#170A14', rough=0.5, metal=0.0, relief='leather'),
                                                                                    # lacquered ebony
        glow=dict(base='#FF4FB2', light='#FFB6DE', dark='#B0126A', rough=0.12, metal=0.0, relief='none',
                  emit=1.7),                                                        # carnival magenta
    ),
    blade=dict(edge='leaf', tip='hook', width=1.1, holes='none', notch='none'),
    guard=jester_guard, pommel='ring', grip_wraps=7, chain_link='ring',
    motif=harlequin_mask, motif2=bell,
    head=dict(staff='motif', blunt='club', gun='blunderbuss'),
    silhouette=dict(curve=0.15, spikes=False, chunky=0.95, theatrical=True),
)
