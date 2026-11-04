"""Xelor: bandaged time-mages who bend the hours; clockwork, dials, sand and the turning of the hands.
Colour story: polished clock-brass, midnight-indigo enamel, pale steel 'hand' trim, linen bandage wraps,
dark walnut, cyan 'chronal' glow. Silhouettes are precise and mechanical: stepped tick-mark edges, split
clock-hand tips, gear guards, flat caps, gear links. Motif: an original clock dial (ticks + hands at ten
past ten); small accent: an hourglass."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def _hand(angle_deg, length, width):
    a = math.radians(angle_deg)
    ux, uz = math.cos(a), math.sin(a)
    px, pz = -uz, ux
    return _poly([(px * width, pz * width), (ux * length * 0.8 + px * width, uz * length * 0.8 + pz * width),
                  (ux * length, uz * length),
                  (ux * length * 0.8 - px * width, uz * length * 0.8 - pz * width), (-px * width, -pz * width)])


def dial(size):
    """Clock dial: rim with four tick bars, hour + minute hands, centre hub. Fits size x size."""
    s = size / 2
    rim = Point(0, 0).buffer(s, 20).difference(Point(0, 0).buffer(s * 0.74, 20))
    ticks = [box(-s * 0.08, s * 0.5, s * 0.08, s * 0.8)]
    ticks.append(box(-s * 0.08, -s * 0.8, s * 0.08, -s * 0.5))
    ticks.append(box(s * 0.5, -s * 0.08, s * 0.8, s * 0.08))
    ticks.append(box(-s * 0.8, -s * 0.08, -s * 0.5, s * 0.08))
    hands = [_hand(150, s * 0.5, s * 0.1), _hand(40, s * 0.66, s * 0.08)]
    hub = Point(0, 0).buffer(s * 0.16, 10)
    return unary_union([rim] + ticks + hands + [hub]).buffer(0)


def hourglass(size):
    """Hourglass with capped ends."""
    s = size / 2
    return _poly([(-s * 0.72, s), (s * 0.72, s), (s * 0.72, s * 0.8), (s * 0.5, s * 0.8), (s * 0.12, 0),
                  (s * 0.5, -s * 0.8), (s * 0.72, -s * 0.8), (s * 0.72, -s), (-s * 0.72, -s), (-s * 0.72, -s * 0.8),
                  (-s * 0.5, -s * 0.8), (-s * 0.12, 0), (-s * 0.5, s * 0.8), (-s * 0.72, s * 0.8)])


def _cog(r, teeth=8, cx=0.0, cz=0.0, hole=0.35):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if (i // 2) % 2 == 0 else r * 0.78
        pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return _poly(pts).difference(Point(cx, cz).buffer(r * hole, 10))


def escapement_guard(w, d):
    """Squared escapement bar with a toothed cog at each end and a notched centre block (keeps blade root clear)."""
    bar = box(-w * 0.78, -d * 0.3, w * 0.78, d * 0.3)
    block = box(-w * 0.3, -d * 0.55, w * 0.3, d * 0.42)
    cogs = [_cog(d * 0.82, 8, sx * w * 0.84, 0.0) for sx in (1, -1)]
    return unary_union([bar, block] + cogs).buffer(0)


STYLE = dict(
    id='xelor', race='Xelor',
    names=dict(fists='Clockwork Knuckles', staff='Meridian Staff', spear='Minute Hand', sword='Tickblade',
               greatsword='Hour Hand', gun='Chronoflint Pistol', dagger='Tocklet', scythe='Twilight Pendulum',
               katana='Stopped Moment', dual_blades='Tick and Tock', chain='Pendulum Tether',
               blunt='Gearwright Maul'),
    mats=dict(
        primary=dict(base='#C7A45A', light='#F3DC9C', dark='#5E4520', rough=0.3, metal=1.0, relief='hammered',
                     paint_light=0.5),                                              # clock brass
        secondary=dict(base='#2C2F6E', light='#5459A8', dark='#13143A', rough=0.36, metal=0.0, relief='hammered',
                       chip=0.5),                                                   # midnight indigo enamel
        accent=dict(base='#BFC5CC', light='#EEF2F5', dark='#5C636B', rough=0.3, metal=1.0, relief='hammered',
                    paint_light=0.5),                                               # pale steel (clock hands)
        grip=dict(base='#D6CBB0', light='#F2EBD8', dark='#8A7C5E', rough=0.9, metal=0.0, relief='weave'),
                                                                                    # linen bandage
        haft=dict(base='#4A3426', light='#73543E', dark='#22160F', rough=0.68, metal=0.0, relief='leather'),
        glow=dict(base='#43DCFF', light='#B0F2FF', dark='#127FB8', rough=0.12, metal=0.0, relief='none',
                  emit=1.7),                                                        # chronal cyan
    ),
    blade=dict(edge='straight', tip='point', width=1.0, holes='none', notch='teeth'),
    guard=escapement_guard, pommel='cap', grip_wraps=7, chain_link='gear',
    motif=dial, motif2=hourglass,
    head=dict(staff='motif', blunt='mace', gun='pistol'),
    silhouette=dict(curve=0.0, spikes=False, chunky=1.0, clockwork=True),
)
