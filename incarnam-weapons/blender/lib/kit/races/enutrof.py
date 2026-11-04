"""Enutrof: crusty old treasure-hunters and prospectors; wealth, digging, earth, patience.
Colour story: rich treasure gold, verdigris patina trim, weathered dark iron, brown leather, gold-glint glow.
Silhouette: broad spade-like blades with chisel tips and ONE lipped coin slot, coin-disk guards, squat cap
pommels, tight wraps, extra-chunky miner's-tool mass: a pick beak behind the hammer head and the scythe heel, a
shovel-spoon spear head. Enutrof owns the only true saturated-gold blades in the matrix.
Motif: a milled coin with a keyhole (original); accent: a faceted nugget."""
import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def keycoin(size):
    """Original emblem: thick coin with a milled (notched) rim and a keyhole pierced through the centre."""
    s = size / 2
    pts = []
    n = 24
    for i in range(n):
        a = 2 * math.pi * i / n
        r = s * (0.98 if i % 2 == 0 else 0.88)
        pts.append((r * math.cos(a), r * math.sin(a)))
    coin = _p(pts)
    ring_cut = Point(0, 0).buffer(s * 0.64, 5).difference(Point(0, 0).buffer(s * 0.55, 5))
    key = unary_union([Point(0, s * 0.14).buffer(s * 0.2, 4),
                       _p([(-s * 0.1, s * 0.1), (s * 0.1, s * 0.1), (s * 0.19, -s * 0.42), (-s * 0.19, -s * 0.42)])])
    return coin.difference(ring_cut).difference(key).buffer(0)


def nugget(size):
    """Small accent: faceted gold nugget (irregular octagon with a facet notch)."""
    s = size / 2
    pts = [(-s * 0.35, s * 0.9), (s * 0.4, s * 0.8), (s * 0.95, s * 0.2), (s * 0.75, -s * 0.6), (s * 0.1, -s * 0.95),
           (-s * 0.6, -s * 0.7), (-s * 0.95, -s * 0.05), (-s * 0.8, s * 0.55)]
    facet = _p([(-s * 0.1, s * 0.35), (s * 0.35, s * 0.05), (-s * 0.05, -s * 0.3), (-s * 0.4, 0.0)])
    return _p(pts).difference(facet).buffer(0)


STYLE = dict(
    id='enutrof', race='Enutrof',
    names=dict(fists='Nuggetfist Knuckles', staff='Lodelight Staff', spear='Veinprobe', sword='Tithe-Cutter',
               greatsword='Motherlode', gun='Claimjumper Blunderbuss', dagger='Pursepick', scythe='Rustharvest',
               katana='Gilded Patience', dual_blades='Penny and Pound', chain='Coffer Flail',
               blunt='Seamcracker Hammer'),
    mats=dict(
        # saturated treasure gold (real metal)
        primary=dict(base='#D8A41F', light='#FFE577', dark='#6C4806', rough=0.3, metal=1.0, relief='hammered',
                     paint_light=0.5),
        # verdigris patina over copper trim (patina is a dielectric crust)
        secondary=dict(base='#4F8F79', light='#8CC6AE', dark='#1F4236', rough=0.7, metal=0.0, relief='hammered',
                       chip=0.5),
        # weathered dark iron rivets/bands
        accent=dict(base='#56504A', light='#A39A8E', dark='#201C19', rough=0.5, metal=1.0, relief='hammered',
                    paint_light=0.5),
        # worn brown leather
        grip=dict(base='#6E4A2C', light='#A27650', dark='#311E10', rough=0.78, metal=0.0, relief='leather'),
        # old oak tool hafts
        haft=dict(base='#7C5C3A', light='#AE8A60', dark='#3A2814', rough=0.8, metal=0.0, relief='leather'),
        # coin glint
        glow=dict(base='#FFDD6A', light='#FFF4BE', dark='#C0901C', rough=0.12, metal=0.0, relief='none', emit=1.5),
    ),
    blade=dict(edge='broad', tip='chisel', width=1.15, holes='coinslot', notch='none'),
    blade_by_cat=dict(spear=dict(tip='spade', width=1.3)),                               # shovel-spoon spear head
    guard='disk', pommel='cap', grip_wraps=7, chain_link='gear',
    motif=keycoin, motif2=nugget,
    head=dict(staff='cage', blunt='hammer', gun='blunderbuss'),
    silhouette=dict(curve=0.0, spikes=False, chunky=1.25, tool=True),
)
