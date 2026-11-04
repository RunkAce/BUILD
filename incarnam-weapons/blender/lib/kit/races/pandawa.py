"""Pandawa: easy-going panda brewers and drunken-fist masters; bamboo, gourds, brew, balance.
Colour story: bright white steel, black lacquer (panda), jade inlays, bamboo hafts, white cloth wraps,
soft jade-mint spirit glow. Silhouette: broad single-edged dao blades with clipped tips, tsuba-like
guards, bamboo-node chains and segmented hafts. Motif: a cord-tied brewing gourd (original);
accent: a bamboo node."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def gourd(size):
    """Original emblem: a double-bulb calabash with a stopper and a cord band cut across its waist."""
    s = size / 2
    low = Point(0, -s * 0.42).buffer(s * 0.55, 18)
    high = Point(0, s * 0.3).buffer(s * 0.34, 16)
    waist = box(-s * 0.2, -s * 0.05, s * 0.2, s * 0.15)
    stopper = box(-s * 0.12, s * 0.6, s * 0.12, s * 0.97)
    body = unary_union([low, high, waist, stopper])
    cord = box(-s, s * 0.0, s, s * 0.07)
    shine = Point(-s * 0.2, -s * 0.38).buffer(s * 0.13, 8)
    return body.difference(cord).difference(shine).buffer(0)


def bamboo_node(size):
    """Small accent: a short bamboo segment with two swollen node rings and a single leaf."""
    s = size / 2
    stalk = box(-s * 0.3, -s * 0.95, s * 0.3, s * 0.95)
    nodes = unary_union([box(-s * 0.42, z - s * 0.09, s * 0.42, z + s * 0.09) for z in (-s * 0.35, s * 0.45)])
    groove = unary_union([box(-s * 0.5, z - s * 0.025, s * 0.5, z + s * 0.025) for z in (-s * 0.35, s * 0.45)])
    leaf = _p(geo.bezier((s * 0.3, s * 0.05), (s * 0.6, s * 0.3), (s * 0.85, s * 0.4), (s * 0.98, s * 0.75), 8) +
              geo.bezier((s * 0.98, s * 0.75), (s * 0.6, s * 0.65), (s * 0.4, s * 0.4), (s * 0.3, s * 0.2), 8)[1:])
    return unary_union([stalk, nodes, leaf]).difference(groove).buffer(0)


STYLE = dict(
    id='pandawa', race='Pandawa',
    names=dict(fists='Stillpaw Bracers', staff='Gourdsage Staff', spear='Reedwind Lance', sword='Brewguard Dao',
               greatsword='Mountainsleep', gun='Kegthunder Cannon', dagger='Cork Tooth', scythe='Paddyreaper',
               katana='Teahouse Calm', dual_blades='Tipsy Twins', chain='Swaying Gourd', blunt='Barrelhead Club'),
    mats=dict(
        # bright polished white steel (panda white)
        primary=dict(base='#C9CCC6', light='#F4F6F0', dark='#6E7470', rough=0.34, metal=1.0, relief='hammered',
                     paint_light=0.55),
        # black lacquer (panda black), chips to steel
        secondary=dict(base='#242123', light='#5A5458', dark='#0E0C0D', rough=0.3, metal=0.0, relief='hammered',
                       chip=0.4),
        # carved jade inlays (stone, dielectric)
        accent=dict(base='#4FA387', light='#9EDDC4', dark='#1C5240', rough=0.22, metal=0.0, relief='none'),
        # white cloth wrap
        grip=dict(base='#E6DFCD', light='#FBF8EE', dark='#9A917C', rough=0.9, metal=0.0, relief='weave'),
        # bamboo hafts
        haft=dict(base='#B9B263', light='#E2DC98', dark='#5E5A26', rough=0.5, metal=0.0, relief='leather'),
        # jade-mint spirit mist
        glow=dict(base='#7CF2C2', light='#C8FFE6', dark='#22A878', rough=0.12, metal=0.0, relief='none', emit=1.5),
    ),
    blade=dict(edge='broad', tip='clip', width=1.22, holes='none', notch='none', single_edge=True),
    guard='tsuba', pommel='orb', grip_wraps=6, chain_link='bamboo',
    motif=gourd, motif2=bamboo_node,
    head=dict(staff='orb', blunt='motif', gun='blunderbuss'),
    silhouette=dict(curve=0.08, spikes=False, chunky=1.1, segmented=True),
)
