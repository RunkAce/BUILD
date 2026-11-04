"""Iop: reckless, proud warriors of the war god; fire and strength. House style of the existing set:
ivory forged metal, vermilion enamel, aged gold, charcoal leather, amber heat. Motif: a flame tuft."""
import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import geo


def flame(size):
    """Original flame-tuft emblem (forelock flame), fits in size x size, centred."""
    s = size / 2
    outer = geo.bezier((0, s), (s * 0.35, s * 0.4), (s * 0.85, 0.1 * s), (s * 0.6, -s * 0.55), 10) + \
        geo.bezier((s * 0.6, -s * 0.55), (s * 0.3, -s), (-s * 0.3, -s), (-s * 0.6, -s * 0.55), 10)[1:] + \
        geo.bezier((-s * 0.6, -s * 0.55), (-s * 0.85, 0.0), (-s * 0.3, s * 0.2), (-s * 0.05, s * 0.55), 10)[1:]
    core_ = Point(0, -s * 0.35).buffer(s * 0.28, 10)
    return Polygon(geo.orient(outer)).buffer(0).difference(core_)


def spark(size):
    s = size / 2
    return Polygon(geo.orient([(0, s), (s * 0.25, s * 0.25), (s, 0), (s * 0.25, -s * 0.25), (0, -s),
                               (-s * 0.25, -s * 0.25), (-s, 0), (-s * 0.25, s * 0.25)]))


STYLE = dict(
    id='iop', race='Iop',
    names=dict(fists='Brawlbrand Knuckles', staff='Emberwatch Staff', spear='Flarecrest', sword='Sunbound',
               greatsword='Oathsplitter', gun='Warcry Hand-Cannon', dagger='Kindlefang', scythe='Ashreaper',
               katana='Duelflare', dual_blades='Twinpride Blades', chain='Warlink', blunt='Hearthbreaker'),
    bespoke=dict(sword='Sunbound', greatsword='Oathsplitter', spear='Flarecrest', chain='Warlink'),
    mats=dict(primary='ivory', secondary='vermilion', accent='gold_plain', grip='charcoal', haft='deepred',
              glow='amber'),
    blade=dict(edge='broad', tip='point', width=1.0, holes='slot', notch='scoop'),
    guard='crescent', pommel='spike', grip_wraps=7, chain_link='box',
    motif=flame, motif2=spark,
    head=dict(staff='motif', blunt='hammer', gun='blunderbuss'),
    silhouette=dict(curve=0.0, spikes=True, chunky=1.15),
)
