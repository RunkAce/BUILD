"""Cra: keen-eyed elven archers who strike from afar; precision, wind and the long sightline.
Colour story: moon-silver steel, deep forest-green enamel, warm brass, sage leather, pale ash wood,
chartreuse 'loosed-arrow' glow. Silhouettes are slender and leaf-bladed, with fletching guards and
arrow-nock pommels. Motif: an original notched fletching feather; small accent: a barbed arrowhead chevron."""

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

import geo


def _poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def feather(size):
    """Original fletching feather: tilted vane with two notches and a quill stub. Fits size x size."""
    s = size / 2
    right = geo.bezier((0, s), (s * 0.5, s * 0.55), (s * 0.55, -s * 0.2), (s * 0.08, -s * 0.62), 10)
    left = geo.bezier((s * 0.08, -s * 0.62), (-s * 0.25, -s * 0.5), (-s * 0.5, s * 0.1), (0, s), 10)
    vane = _poly(right + left[1:-1])
    # fletch notches (one per side, staggered) - reads as feather barbs
    vane = vane.difference(_poly([(s * 0.6, s * 0.18), (s * 0.12, -s * 0.02), (s * 0.6, -s * 0.12)]))
    vane = vane.difference(_poly([(-s * 0.6, -s * 0.05), (-s * 0.1, -s * 0.28), (-s * 0.6, -s * 0.42)]))
    quill = box(-s * 0.07, -s, s * 0.09, -s * 0.45)
    shp = unary_union([vane, quill])
    shp = affinity.rotate(shp, -18, origin=(0, 0))
    # keep inside the box
    minx, minz, maxx, maxz = shp.bounds
    k = min(1.0, size / max(maxx - minx, maxz - minz))
    shp = affinity.scale(shp, k, k, origin=(0, 0))
    cx, cz = (shp.bounds[0] + shp.bounds[2]) / 2, (shp.bounds[1] + shp.bounds[3]) / 2
    return affinity.translate(shp, -cx, -cz).buffer(0)


def arrowhead(size):
    """Barbed arrowhead chevron with a short tang."""
    s = size / 2
    head = _poly([(0, s), (s * 0.82, -s * 0.45), (s * 0.3, -s * 0.22), (s * 0.14, -s * 0.38),
                  (s * 0.14, -s), (-s * 0.14, -s), (-s * 0.14, -s * 0.38), (-s * 0.3, -s * 0.22),
                  (-s * 0.82, -s * 0.45)])
    return head


def fletch_guard(w, d):
    """Fletching guard: two swept vanes per side with a gap between them (negative space), on a round hub."""
    parts = [Point(0, 0).buffer(d * 0.55, 10)]
    for sx in (1, -1):
        upper = _poly([(sx * 0.04, d * 0.5), (sx * w * 0.6, d * 0.5), (sx * w * 1.04, d * 0.9),
                       (sx * w * 0.86, d * 0.0), (sx * 0.04, -d * 0.12)])
        lower = _poly([(sx * 0.04, -d * 0.34), (sx * w * 0.52, -d * 0.4), (sx * w * 0.82, -d * 1.3),
                       (sx * w * 0.3, -d * 0.95), (sx * 0.04, -d * 0.72)])
        parts += [upper, lower]
    return unary_union(parts).buffer(0)


def _metal(base, light, dark, rough, relief='hammered'):
    return dict(base=base, light=light, dark=dark, rough=rough, metal=1.0, relief=relief, paint_light=0.5)


STYLE = dict(
    id='cra', race='Cra',
    names=dict(fists='Quillknuckle Bracers', staff='Longsight Bowstaff', spear='Fletchpike', sword='Windthread',
               greatsword='Skyline Verdict', gun='Farshot Longbarrel', dagger='Nockpin', scythe='Gale Harvester',
               katana='Hawkline', dual_blades='Twin Quarrels', chain='Tetherbolt', blunt='Greenwood Maul'),
    mats=dict(
        primary=_metal('#C3CDCB', '#F2F7F4', '#6B7774', 0.36),                      # moon-silver steel
        secondary=dict(base='#2F6B4C', light='#5E9E72', dark='#163322', rough=0.4, metal=0.0,
                       relief='hammered', chip=0.5),                                # forest-green enamel
        accent=_metal('#B89A5A', '#EED79C', '#5C4826', 0.28, relief='filigree'),    # warm brass
        grip=dict(base='#5C6444', light='#8C9468', dark='#2A2E1D', rough=0.8, metal=0.0, relief='leather'),
        haft=dict(base='#B79E77', light='#DCC8A2', dark='#6E5A3E', rough=0.72, metal=0.0, relief='leather'),
        glow=dict(base='#B6F25C', light='#E4FFA8', dark='#5FA01E', rough=0.15, metal=0.0, relief='none',
                  emit=1.6),                                                        # loosed-arrow chartreuse
    ),
    blade=dict(edge='leaf', tip='point', width=0.92, holes='none', notch='none'),
    guard=fletch_guard, pommel='fang', grip_wraps=8, chain_link='oval',
    motif=feather, motif2=arrowhead,
    head=dict(staff='crescent', blunt='mace', gun='rifle'),
    silhouette=dict(curve=0.12, spikes=False, chunky=0.92, slender=True),
)
