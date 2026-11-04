"""Ecaflip: feline gamblers who live by luck, dice and cards; swagger, chance, nine lives.
Colour story: warm copper, black card-lacquer enamel, gold coin filigree, cream leather wraps,
black-lacquered wood, lucky-emerald glow (the green of the gaming table). Silhouettes are cocky and
playful: clipped claw tips, three dice-pip holes, a cat-ear crossguard, faceted die pommels.
Motif: an original lucky coin with a slit cat-eye cut; small accent: a card-diamond pip."""
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def lucky_coin(size):
    """Coin with a vertical slit-pupil (cat-eye) cut and a notched rim. Fits size x size."""
    s = size / 2
    coin = Point(0, 0).buffer(s, 20)
    pupil = Point(-s * 0.42, 0).buffer(s * 0.62, 14).intersection(Point(s * 0.42, 0).buffer(s * 0.62, 14))
    pupil = affinity.scale(pupil, 1.0, 1.0, origin=(0, 0))
    coin = coin.difference(pupil)
    for a in (45, 135, 225, 315):   # four rim notches -> reads as a minted coin, not a plain disc
        coin = coin.difference(affinity.rotate(box(-s * 0.09, s * 0.82, s * 0.09, s * 1.05), a, origin=(0, 0)))
    return coin.buffer(0)


def card_pip(size):
    """Card-diamond pip with a round centre (die pip)."""
    s = size / 2
    d = _poly([(0, s), (s * 0.68, 0), (0, -s), (-s * 0.68, 0)])
    return d.difference(Point(0, 0).buffer(s * 0.2, 10)).buffer(0)


def ear_guard(w, d):
    """Crossbar with two upturned cat ears flanking the blade and a small chin point below."""
    bar = unary_union([box(-w * 0.86, -d * 0.34, w * 0.86, d * 0.34),
                       Point(w * 0.86, 0).buffer(d * 0.34, 8), Point(-w * 0.86, 0).buffer(d * 0.34, 8)])
    parts = [bar, _poly([(-w * 0.2, -d * 0.3), (0, -d * 0.95), (w * 0.2, -d * 0.3)])]
    for sx in (1, -1):
        ear = geo.bezier((sx * w * 0.4, d * 0.2), (sx * w * 0.46, d * 0.9), (sx * w * 0.66, d * 1.5),
                         (sx * w * 0.84, d * 1.7), 8) + \
            geo.bezier((sx * w * 0.84, d * 1.7), (sx * w * 0.9, d * 1.1), (sx * w * 0.94, d * 0.6),
                       (sx * w * 0.98, d * 0.2), 8)[1:]
        parts.append(_poly(ear))
    return unary_union(parts).buffer(0)


STYLE = dict(
    id='ecaflip', race='Ecaflip',
    names=dict(fists='Pawprint Knuckles', staff='Wildcard Staff', spear='Long Odds', sword='Lucky Streak',
               greatsword='High Roller', gun='Double Down', dagger='Sleeve Ace', scythe='Ninth Life',
               katana='Whisker Cut', dual_blades='Double Six', chain='Yarnspinner', blunt='Jackpot Mallet'),
    mats=dict(
        primary=dict(base='#C47E4E', light='#F2BE90', dark='#62311A', rough=0.32, metal=1.0, relief='hammered',
                     paint_light=0.5),                                              # warm copper
        secondary=dict(base='#262221', light='#4E4744', dark='#0F0D0C', rough=0.3, metal=0.0, relief='hammered',
                       chip=0.4),                                                   # black card lacquer
        accent=dict(base='#D4AE4E', light='#FBE39A', dark='#6A4E18', rough=0.24, metal=1.0, relief='filigree',
                    paint_light=0.5),                                               # coin gold
        grip=dict(base='#E2D0AC', light='#F8EDD5', dark='#8E7C5A', rough=0.78, metal=0.0, relief='leather'),
        haft=dict(base='#33292A', light='#5B4A4A', dark='#140F10', rough=0.5, metal=0.0, relief='leather'),
        glow=dict(base='#3FEFA2', light='#A8FFD6', dark='#119460', rough=0.15, metal=0.0, relief='none',
                  emit=1.6),                                                        # lucky emerald
    ),
    blade=dict(edge='straight', tip='clip', width=1.0, holes='rings', notch='none'),
    guard=ear_guard, pommel='faceted', grip_wraps=6, chain_link='oval',
    motif=lucky_coin, motif2=card_pip,
    head=dict(staff='motif', blunt='hammer', gun='blunderbuss'),
    silhouette=dict(curve=0.1, spikes=False, chunky=1.0, playful=True),
)
