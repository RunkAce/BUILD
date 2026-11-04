"""Foggernaut: steam-driven sea-voyagers in riveted diving armour who run on stasis; boilers, pipes, portholes.
Colour story: dark oxidised bronze, boiler-black navy enamel, brass rivets, tarred-canvas wraps, boiler iron
hafts, teal porthole glass, one cold stasis-blue glow. Silhouettes are heavy and industrial: straight riveted
plates with saw-teeth and clipped tips, ONE big bolted porthole (glass-filled) near the guard, a pipe-bar guard
with a bolted porthole hub, flat pipe-cap pommels, studded oval links, emblem staff heads and a long rifle.
Motif: an original lobed valve handwheel (five spokes, hex hub); accent: a hex bolt-nut."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _p(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def valve_wheel(size):
    """Steam valve handwheel: lobed rim, five spokes, a hex hub with a round bore (original emblem)."""
    s = size / 2
    rim = Point(0, 0).buffer(s * 0.86, 28).difference(Point(0, 0).buffer(s * 0.64, 28))
    lobes = [Point(s * 0.84 * math.cos(math.radians(90 + 72 * k)), s * 0.84 * math.sin(math.radians(90 + 72 * k)))
             .buffer(s * 0.16, 10) for k in range(5)]
    spokes = []
    for k in range(5):
        a = math.radians(90 + 36 + 72 * k)
        ca, sa = math.cos(a), math.sin(a)
        w = s * 0.085
        spokes.append(_p([(-sa * w, ca * w), (ca * s * 0.7 - sa * w, sa * s * 0.7 + ca * w),
                          (ca * s * 0.7 + sa * w, sa * s * 0.7 - ca * w), (sa * w, -ca * w)]))
    hub = _p([(s * 0.3 * math.cos(math.radians(60 * i)), s * 0.3 * math.sin(math.radians(60 * i))) for i in range(6)])
    bore = Point(0, 0).buffer(s * 0.11, 10)
    return unary_union([rim, hub] + lobes + spokes).difference(bore).buffer(0)


def hex_nut(size):
    s = size / 2
    pts = [(s * math.cos(math.radians(30 + 60 * i)), s * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    return _p(pts).difference(Point(0, 0).buffer(s * 0.36, 10)).buffer(0)


def porthole_guard(w, d):
    """Pipe bar with flange discs at the ends and a bolted porthole hub in the middle."""
    bar = box(-w * 0.86, -d * 0.24, w * 0.86, d * 0.24)
    flanges = [box(sx * w * 0.88 - d * 0.18, -d * 0.52, sx * w * 0.88 + d * 0.18, d * 0.52) for sx in (1, -1)]
    caps = [Point(sx * w * 1.0, 0).buffer(d * 0.3, 8) for sx in (1, -1)]
    # hub hangs below the bar so the blade-root inlay above it stays clear
    r = max(w * 0.27, d * 0.85)
    hz = -d * 0.35
    hub = Point(0, hz).buffer(r, 20).difference(Point(0, hz).buffer(r * 0.6, 16))
    bolts = [Point(r * math.cos(math.radians(a)), hz + r * math.sin(math.radians(a))).buffer(d * 0.16, 6)
             for a in range(0, 360, 45)]
    return unary_union([bar, hub] + flanges + caps + bolts).buffer(0)


STYLE = dict(
    id='foggernaut', race='Foggernaut',
    names=dict(fists='Rivetfist Gauntlets', staff='Boilerwake Staff', spear='Deepwater Harpoon',
               sword='Bulkhead Blade', greatsword='Keelbreaker', gun='Steamlung Cannon', dagger='Bilge Knife',
               scythe='Tidecutter', katana='Pressure Edge', dual_blades='Piston Pair', chain='Anchorline',
               blunt='Pistonmaul'),
    mats=dict(
        primary=dict(base='#6C4A34', light='#A7805F', dark='#2A180D', rough=0.44, metal=1.0, relief='hammered',
                     paint_light=0.45),                                             # dark oxidised bronze
        secondary=dict(base='#23303A', light='#4F6474', dark='#0D1318', rough=0.4, metal=0.0, relief='hammered',
                       chip=0.6),                                                   # boiler-black navy enamel
        accent=dict(base='#C8A04E', light='#F3D894', dark='#614419', rough=0.28, metal=1.0, relief='hammered',
                    paint_light=0.5),                                               # brass rivets
        grip=dict(base='#7D6A4E', light='#AE9874', dark='#3A2F20', rough=0.9, metal=0.0, relief='weave'),
                                                                                    # tarred canvas
        haft=dict(base='#4D5257', light='#8C949B', dark='#1D2023', rough=0.48, metal=1.0, relief='hammered',
                  paint_light=0.5),                                                 # boiler iron (metal)
        glass=dict(base='#2F7F80', light='#8FDCD2', dark='#0F3335', rough=0.1, metal=0.0, relief='none',
                   paint_light=0.8),                                                # teal porthole glass (not lit)
        glow=dict(base='#6EA8FF', light='#C4DCFF', dark='#2A4FC4', rough=0.12, metal=0.0, relief='none',
                  emit=1.6),                                                        # stasis blue
    ),
    blade=dict(edge='straight', tip='clip', width=1.15, holes='porthole', notch='teeth'),
    guard=porthole_guard, pommel='cap', grip_wraps=5, chain_link='oval',
    motif=valve_wheel, motif2=hex_nut,
    head=dict(staff='motif', blunt='hammer', gun='rifle'),
    silhouette=dict(curve=0.0, spikes=False, chunky=1.22, riveted=True, steam=True),
)
