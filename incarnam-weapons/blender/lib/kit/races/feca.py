"""Feca: steadfast protectors who raise shields and lay protective glyphs; endurance, armour, the shell.
Colour story: blued bastion steel, deep cobalt enamel, burnished bronze, navy leather, dark oak,
azure 'glyph' glow. Silhouettes are protective and rounded: swelling leaf blades with a true point, arched
langets and round medallions, a crossguard ending in two hanging shield plates (the Feca signature), shell-orb
pommels, an orb-headed ward staff, a flanged mace and a short warding pistol, box links. Motif: an original
hexagonal shell scute with Y-spokes (turtle-shell ward); small accent: a hex rivet."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _hex(r, rot=90.0, cx=0.0, cz=0.0):
    return _poly([(cx + r * math.cos(math.radians(rot + 60 * i)), cz + r * math.sin(math.radians(rot + 60 * i)))
                  for i in range(6)])


def scute(size):
    """Hex shell-scute ward: hex rim, central hex boss and three spokes to alternate corners."""
    s = size / 2
    rim = _hex(s).difference(_hex(s * 0.66))
    boss = _hex(s * 0.3)
    spokes = []
    for i in range(3):
        a = math.radians(90 + 120 * i)
        spokes.append(_poly([(math.cos(a) * s * 0.8 - math.sin(a) * s * 0.09, math.sin(a) * s * 0.8 + math.cos(a) * s * 0.09),
                             (math.cos(a) * s * 0.8 + math.sin(a) * s * 0.09, math.sin(a) * s * 0.8 - math.cos(a) * s * 0.09),
                             (math.sin(a) * s * 0.09, -math.cos(a) * s * 0.09),
                             (-math.sin(a) * s * 0.09, math.cos(a) * s * 0.09)]))
    return unary_union([rim, boss] + spokes).buffer(0)


def rivet(size):
    """Hex rivet with a round socket."""
    s = size / 2
    return _hex(s * 0.95, rot=0).difference(Point(0, 0).buffer(s * 0.32, 10)).buffer(0)


def shield_guard(w, d):
    """Squared crossbar ending in two heater-shield plates that hang slightly below the bar."""
    parts = [box(-w * 0.72, -d * 0.36, w * 0.72, d * 0.4)]
    for sx in (1, -1):
        cx = sx * w * 0.78
        hw = w * 0.26
        sh = _poly([(cx - hw, d * 0.62), (cx + hw, d * 0.62), (cx + hw, -d * 0.2),
                    (cx + hw * 0.55, -d * 0.85), (cx, -d * 1.2), (cx - hw * 0.55, -d * 0.85), (cx - hw, -d * 0.2)])
        parts.append(sh)
    return unary_union(parts).buffer(0)


STYLE = dict(
    id='feca', race='Feca',
    names=dict(fists='Shellguard Knuckles', staff='Glyphkeeper Staff', spear='Rampart Lance', sword='Wardsteel',
               greatsword='Bastion Wall', gun='Barrier Mortar', dagger='Vigil Knife', scythe='Tidewall Crescent',
               katana='Stillwater Edge', dual_blades='Twin Ramparts', chain='Anchorward', blunt='Keepstone Hammer'),
    mats=dict(
        primary=dict(base='#A4B0BA', light='#E1E9EF', dark='#4B5560', rough=0.4, metal=1.0, relief='hammered',
                     paint_light=0.5),                                              # blued bastion steel
        secondary=dict(base='#2A4C8E', light='#5079C2', dark='#122347', rough=0.38, metal=0.0, relief='hammered',
                       chip=0.55),                                                  # cobalt enamel
        accent=dict(base='#A77C45', light='#E3BE84', dark='#4E3418', rough=0.3, metal=1.0, relief='filigree',
                    paint_light=0.5),                                               # burnished bronze
        grip=dict(base='#273149', light='#4A5778', dark='#121724', rough=0.8, metal=0.0, relief='leather'),
        haft=dict(base='#5C4433', light='#86664C', dark='#2C1F16', rough=0.7, metal=0.0, relief='leather'),
        glow=dict(base='#5AADFF', light='#B5DCFF', dark='#1F5FC4', rough=0.15, metal=0.0, relief='none',
                  emit=1.5),                                                        # azure glyph light
    ),
    blade=dict(edge='leaf', tip='point', width=1.05, holes='none', notch='none'),
    guard=shield_guard, pommel='orb', grip_wraps=6, chain_link='box',
    motif=scute, motif2=rivet,
    head=dict(staff='orb', blunt='mace', gun='pistol'),
    silhouette=dict(curve=0.0, spikes=False, chunky=1.12, round=True, warded=True),
)
