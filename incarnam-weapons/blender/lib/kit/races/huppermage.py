"""Huppermage: scholar-battlemages who chain elemental runes (fire, water, earth, air and light) into spells.
Colour story: radiant white-gold metal, ivory-cream enamel, sapphire rune crystal, deep-blue silk wraps,
dark rosewood hafts, one pale quadramental gold-white glow. Silhouettes are arcane and faceted: stepped
crystal-edged blades with a rune channel, a guard of rune beads strung on a lozenge bar, faceted pommels.
Motif: an original four-quarter rune (diamond split into four elemental facets around a core);
small accent: a lidded triangle glyph."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _rhomb(cx, cz, rx, rz):
    return _p([(cx, cz + rz), (cx + rx, cz), (cx, cz - rz), (cx - rx, cz)])


def quarter_rune(size):
    """Diamond cut into four facets by a cross gap, with a round core and four corner ticks."""
    s = size / 2
    d = _rhomb(0, 0, s * 0.82, s * 0.98)
    g = s * 0.075
    d = d.difference(box(-g, -s, g, s)).difference(box(-s, -g, s, g))
    d = d.difference(Point(0, 0).buffer(s * 0.36, 14))
    core = _rhomb(0, 0, s * 0.2, s * 0.24)
    return unary_union([d, core]).buffer(0)


def lidded_glyph(size):
    """Triangle glyph with an open centre, a lid bar above and a dot inside."""
    s = size / 2
    tri = _p([(0, s * 0.62), (s * 0.92, -s * 0.92), (-s * 0.92, -s * 0.92)])
    tri = tri.difference(_p([(0, s * 0.18), (s * 0.5, -s * 0.66), (-s * 0.5, -s * 0.66)]))
    lid = box(-s * 0.6, s * 0.78, s * 0.6, s * 0.96)
    dot = Point(0, -s * 0.36).buffer(s * 0.14, 8)
    return unary_union([tri, lid, dot]).buffer(0)


def rune_bead_guard(w, d):
    """Lozenge bar tapering to points, strung with a tall centre rhomb and two side rune beads."""
    bar = _p([(-w * 1.08, 0.0), (-w * 0.5, -d * 0.42), (w * 0.5, -d * 0.42), (w * 1.08, 0.0), (w * 0.5, d * 0.42),
              (-w * 0.5, d * 0.42)])
    centre = _rhomb(0, d * 0.05, w * 0.4, d * 0.78)
    beads = [_rhomb(sx * w * 0.7, 0.0, d * 0.62, d * 0.85) for sx in (1, -1)]
    return unary_union([bar, centre] + beads).buffer(0)


STYLE = dict(
    id='huppermage', race='Huppermage',
    names=dict(fists='Runeknuckle Wraps', staff='Fourfold Staff', spear='Glyphlance', sword='Runebrand',
               greatsword='Sigilcleaver', gun='Runeflint Pistol', dagger='Quillspike', scythe='Equinox Reaper',
               katana='Glyphdraw', dual_blades='Sunglyph and Moonglyph', chain='Runelink Flail',
               blunt='Codex Hammer'),
    mats=dict(
        primary=dict(base='#D6BE7E', light='#FCEBB8', dark='#7A6230', rough=0.26, metal=1.0, relief='hammered',
                     paint_light=0.5),                                              # radiant white-gold
        secondary=dict(base='#E7DFCB', light='#FFFBF0', dark='#9B8F72', rough=0.38, metal=0.0, relief='hammered',
                       chip=0.4),                                                   # ivory-cream enamel
        accent=dict(base='#2C5FC2', light='#7FA8F2', dark='#102A66', rough=0.14, metal=0.0, relief='none'),
                                                                                    # sapphire rune crystal
        grip=dict(base='#24336E', light='#4E64AA', dark='#0D1430', rough=0.84, metal=0.0, relief='weave'),
                                                                                    # deep-blue silk
        haft=dict(base='#5A2E2A', light='#8A4D45', dark='#26110F', rough=0.6, metal=0.0, relief='leather'),
                                                                                    # dark rosewood
        glow=dict(base='#FFEE96', light='#FFFBE0', dark='#D9A93A', rough=0.12, metal=0.0, relief='none',
                  emit=1.6),                                                        # quadramental light
    ),
    blade=dict(edge='crystal', tip='point', width=0.96, holes='slot', notch='none'),
    guard=rune_bead_guard, pommel='faceted', grip_wraps=6, chain_link='oval',
    motif=quarter_rune, motif2=lidded_glyph,
    head=dict(staff='orb', blunt='motif', gun='pistol'),
    silhouette=dict(curve=0.0, spikes=False, chunky=1.0, faceted=True, runes=True),
)
