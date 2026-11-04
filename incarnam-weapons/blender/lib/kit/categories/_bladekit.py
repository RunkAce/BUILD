"""Shared parts for the blade categories greatsword / katana / dual_blades (private: build_matrix skips '_' files).

Everything reads the race STYLE: silhouette flags, blade dict, pommel, motif/motif2, mats roles.
Coordinates: weapon points +Z, front face -Y, 2D outlines are (x, z).
"""
import math

import bmesh
from shapely.geometry import Point, box
from shapely.ops import transform, unary_union

import core
import geo


# ------------------------------------------------------------------ style readers
def sil(style):
    return style.get('silhouette', {})


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def chunk(style):
    return clamp(sil(style).get('chunky', 1.0), 0.88, 1.25)


def is_heavy(style):
    s = sil(style)
    return bool(s.get('heavy') or s.get('tool') or s.get('chunky', 1.0) >= 1.2)


def is_round(style):
    s = sil(style)
    return bool(s.get('round') or s.get('organic') or s.get('portals'))


def is_spiky(style):
    s = sil(style)
    return bool(s.get('spikes') or s.get('barbs') or s.get('thorns') or s.get('feral'))


def is_mech(style):
    s = sil(style)
    return bool(s.get('riveted') or s.get('clockwork') or s.get('heavy') or s.get('tool'))


# ------------------------------------------------------------------ 2D helpers
def taper(shape, L, k, z0=0.0):
    """Narrow toward the tip: x scaled by (1 - k * t), t = 0 at z0 .. 1 at z0 + L."""
    return transform(lambda x, z: (x * (1.0 - k * clamp((z - z0) / L, 0.0, 1.0)), z),
                     shape.segmentize(0.03)).buffer(0)


def largest(shape):
    if shape.geom_type == 'MultiPolygon':
        return max(shape.geoms, key=lambda g: g.area)
    return shape


def fit(shape, size):
    """Scale a shape so its larger bbox side == size, centred at the origin."""
    x0, z0, x1, z1 = shape.bounds
    s = size / max(x1 - x0, z1 - z0, 1e-6)
    return transform(lambda x, z: ((x - (x0 + x1) / 2) * s, (z - (z0 + z1) / 2) * s), shape)


def langet_shape(style, x0, x1, z0, z1):
    """Ricasso clasp outline (secondary) gripping a blade root: arch (round races), faceted shield, or chevron."""
    s = sil(style)
    w = x1 - x0
    cx = (x0 + x1) / 2
    if is_round(style):
        r = w / 2
        return unary_union([box(x0, z0, x1, z1 - r), Point(cx, z1 - r).buffer(r, 20)]).buffer(0)
    if s.get('faceted') or s.get('clockwork'):
        return core.poly([(x0, z0), (x1, z0), (x1, z1 - w * 0.42), (cx + w * 0.22, z1), (cx - w * 0.22, z1),
                          (x0, z1 - w * 0.42)])
    if is_heavy(style):
        c = w * 0.18
        return core.poly([(x0, z0), (x1, z0), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c)])
    return core.poly([(x0, z0), (x1, z0), (x1, z1 - w * 0.55), (cx, z1), (x0, z1 - w * 0.55)])


def motif_shape(style, size, key='motif'):
    fn = style.get(key)
    if not fn:
        return None
    shp = fn(size)
    if shp is None or shp.is_empty:
        return None
    return shp.buffer(0)


# ------------------------------------------------------------------ 3D primitives
def stud(name, x, z, r, depth, col, mat, segments=6, y=0.0):
    """Through-rivet: short chamfered cylinder along Y (seated through a plate of thickness < depth)."""
    h = depth / 2
    c = min(r * 0.35, h * 0.3)
    o = geo.lathe(name, [(0.0, -h), (r - c, -h), (r, -h + c), (r, h - c), (r - c, h), (0.0, h)], segments=segments,
                  col=col, material=mat, smooth_angle=30)
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (x, y, z)
    return o


def horizontal(obj, z, x=0.0, y=0.0):
    """Lay an XZ-built plate flat (shape +z -> -Y front, thickness along Z) at height z."""
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.location = (x, y, z)
    return obj


def strap_grip(name, z0, z1, radius, wraps, col, mat, segments=10, rpw=14, flatten=1.0, diamond=False):
    """Lower-poly helical strap wrap (same look as geo.wrapped_grip 'strap'). diamond=True crosses two
    opposite helices (katana ito-maki diamond read)."""
    length = z1 - z0
    bm = bmesh.new()
    rings = max(8, int(wraps * rpw))
    rows = []
    for r in range(rings + 1):
        t = r / rings
        z = z0 + t * length
        row = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            if diamond:
                p1 = (t * wraps - a / (2 * math.pi)) % 1.0
                p2 = (t * wraps + a / (2 * math.pi)) % 1.0
                bulge = 0.16 * radius * max(1 - abs(p1 - 0.5) * 2.4, 1 - abs(p2 - 0.5) * 2.4, 0.0)
            else:
                phase = (t * wraps - a / (2 * math.pi)) % 1.0
                bulge = 0.16 * radius * min(1.0, phase / 0.88) - (0.16 * radius if phase > 0.94 else 0.0)
                bulge = max(bulge, 0.0)
            rr = radius + bulge
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a) * flatten, z)))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = geo.mesh_object(name, bm, col, mat)
    geo.shade_by_angle(obj, 50)
    return obj


def band(name, z, r, col, mat, h=0.07, segments=8, scale_xy=(1, 1)):
    """Faceted collar (like core.collar) with optional oval cross-section."""
    return geo.lathe(name, [(0.0, z - h / 2), (r, z - h / 2), (r + 0.012, z), (r, z + h / 2), (0.0, z + h / 2)],
                     segments=segments, col=col, material=mat, scale_xy=scale_xy)


def pommel_seg(style):
    return 4 if style.get('pommel') in ('spike', 'fang') else 8


def pommel_widest(style, scale):
    prof = core.POMMELS.get(style.get('pommel', 'faceted')) or core.POMMELS['cap']
    r = max(p[0] for p in prof)
    zs = [p[1] for p in prof if p[0] >= r - 1e-6]
    return r * scale, sum(zs) / len(zs) * scale


def pommel_gems(style, pz, scale, col, mat, name='PommelGem', max_size=0.2):
    """motif2 gem seated on the front and back flats of the pommel's widest waist."""
    seg = pommel_seg(style)
    pr, pdz = pommel_widest(style, scale)
    flat, half = pr * math.cos(math.pi / seg), pr * math.sin(math.pi / seg)
    out = []
    for side in (-1, 1):
        g = core.motif_plate(f'{name}{side + 1}', style, min(max_size, half * 2.1), 0, pz + pdz, 0.07, col, mat,
                             key='motif2')
        if g is not None:
            g.location.y = side * (flat - 0.012)
            out.append(g)
    return out
