"""Osamodas: horned beast-tamers and summoners who bind creatures and call them to fight.
Colour story: azure blued steel, dark keratin horn, violet enamel, rawhide wraps, violet summoning glow.
Silhouette: wavy horn-ringed blades with hooked claw tips, swept-back horn guards, leash-ring pommels,
strong sweep/curvature. Motif: a horn crown cradling a summoning gem (original); accent: a raking claw."""
import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def horn_crown(size):
    """Original emblem: two ram-curl horns sweeping up and out from a diamond gem."""
    s = size / 2
    parts = []
    for sx in (1, -1):
        outer = geo.bezier((sx * s * 0.1, -s * 0.6), (sx * s * 1.1, -s * 0.75), (sx * s * 1.12, s * 0.6),
                           (sx * s * 0.6, s * 0.98), 12)
        inner = geo.bezier((sx * s * 0.6, s * 0.98), (sx * s * 0.62, s * 0.35), (sx * s * 0.5, -s * 0.05),
                           (sx * s * 0.1, -s * 0.05), 12)
        parts.append(_p(outer + inner[1:]))
    gem = _p([(0, s * 0.3), (s * 0.3, -s * 0.3), (0, -s * 0.95), (-s * 0.3, -s * 0.3)])
    eye = _p([(0, -s * 0.05), (s * 0.11, -s * 0.33), (0, -s * 0.62), (-s * 0.11, -s * 0.33)])
    return unary_union(parts + [gem]).difference(eye).buffer(0)


def claw(size):
    """Small accent: three curved raking claw marks fused at the base."""
    s = size / 2
    out = []
    for k, dx in enumerate((-0.5, 0.0, 0.5)):
        x0, x1 = (dx - 0.32) * s, (dx + 0.32) * s
        lo, hi = -s * (0.95 if k == 1 else 0.75), s * (0.95 if k == 1 else 0.75)
        # tapered crescent slash, fat in the middle, sharp at both ends
        a = geo.bezier((x0, lo), (x0 + s * 0.02, lo * 0.2), (x1 - s * 0.2, hi * 0.6), (x1, hi), 8)
        b = geo.bezier((x1, hi), (x1 - s * 0.02, hi * 0.1), (x0 + s * 0.32, lo * 0.5), (x0, lo), 8)
        out.append(_p(a + b[1:]))
    return unary_union(out).buffer(0)


def _taper(path, w0, w1):
    """Polygon around a polyline path whose half-width tapers from w0 to w1."""
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


def horn_guard(w, d):
    """Custom guard: a horn boss with two horns that sweep out and rake back down toward the hand."""
    out = [Point(0, 0).buffer(d * 0.62, 10)]
    for sx in (1, -1):
        path = geo.bezier((sx * d * 0.1, d * 0.1), (sx * w * 0.6, d * 0.1), (sx * w * 1.0, -d * 0.3),
                          (sx * w * 0.92, -d * 1.7), 14)
        out.append(_taper(path, d * 0.5, d * 0.06))
    return unary_union(out).buffer(0)


STYLE = dict(
    id='osamodas', race='Osamodas',
    names=dict(fists='Clawcaller Grips', staff='Hornwake Crook', spear='Wyrmgoad', sword='Packbinder',
               greatsword='Behemoth Tusk', gun='Roarpipe Pistol', dagger='Talonquill', scythe='Moultreaper',
               katana='Featherdraw', dual_blades='Twin Talons', chain='Leashwyrm', blunt='Herdbreaker Maul'),
    mats=dict(
        # blued tamer's steel
        primary=dict(base='#7E9CC4', light='#C9DAF0', dark='#2E3F5E', rough=0.36, metal=1.0, relief='hammered',
                     paint_light=0.55),
        # dark polished horn/keratin
        secondary=dict(base='#3E2C28', light='#7A5A4A', dark='#1A1110', rough=0.4, metal=0.0, relief='none'),
        # violet enamel inlays
        accent=dict(base='#6E4AA6', light='#A684DA', dark='#2E1B4E', rough=0.34, metal=0.0, relief='hammered',
                    chip=0.45),
        # rawhide leash wrap
        grip=dict(base='#A87B50', light='#D6AE80', dark='#553A22', rough=0.8, metal=0.0, relief='leather'),
        # horn-banded hafts
        haft=dict(base='#4A3530', light='#7C5E52', dark='#1E1412', rough=0.6, metal=0.0, relief='leather'),
        # summoning-portal violet
        glow=dict(base='#C27CFF', light='#E8C8FF', dark='#6A2AB8', rough=0.12, metal=0.0, relief='none', emit=1.7),
    ),
    blade=dict(edge='wavy', tip='hook', width=0.95, holes='none', notch='scoop'),
    guard=horn_guard, pommel='ring', grip_wraps=6, chain_link='ring',
    motif=horn_crown, motif2=claw,
    head=dict(staff='crescent', blunt='motif', gun='pistol'),
    silhouette=dict(curve=0.4, spikes=False, chunky=1.0, horns=True),
)
