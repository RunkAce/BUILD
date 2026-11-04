"""Shared polearm parts for the two-handed long categories (staff, spear).

Private helper (leading underscore: build_matrix.available() skips it). Everything here reads the race STYLE:
  silhouette flags -> haft dressing (segmented nodes, riveted bands, organic vine, clockwork double bands,
                      faceted low-poly haft, slender/heavy radius, theatrical/swashbuckler tassels, spikes)
  pommel           -> butt ferrule, grip_wraps -> wrap density, motif2 -> collar badges / hanging charm,
  mats roles       -> haft (shaft), grip (wraps), accent (bands), secondary (sockets), glow (gems).
Coordinates: butt end of the haft at z=0, weapon points +Z, front face -Y.
"""
import math

from mathutils import Vector
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import core
import geo


# ------------------------------------------------------------------ style readers
def sil(style):
    return style.get('silhouette', {})


def chunk(style):
    return max(0.88, min(1.25, sil(style).get('chunky', 1.0)))


def haft_r(style):
    s = sil(style)
    r = 0.074 * (0.7 + 0.3 * chunk(style))
    if s.get('slender'):
        r *= 0.92
    if s.get('heavy') or s.get('tool'):
        r *= 1.05
    return r


def haft_segments(style):
    s = sil(style)
    if s.get('faceted'):
        return 6
    if s.get('clockwork') or s.get('riveted') or s.get('heavy') or s.get('tool'):
        return 8
    return 10


def tassel_kind(style):
    """Hanging charm under the head: theatrical/swashbuckler -> ribbon tassel, segmented -> gourd-like charm."""
    s = sil(style)
    if s.get('theatrical') or s.get('swashbuckler'):
        return 'tassel'
    if s.get('segmented'):
        return 'charm'
    return None


# ------------------------------------------------------------------ primitives
def gem(name, zc, R, col, mat, faceted=False, segments=None, y=0.0, x=0.0):
    """Glow gem: faceted diamond (faceted races) or a low-poly rounded orb."""
    if faceted:
        prof = [(0.0, -R * 1.15), (R * 0.72, -R * 0.35), (R * 0.82, R * 0.1), (R * 0.5, R * 0.62), (0.0, R * 0.78)]
        seg = segments or 6
    else:
        n = 7
        prof = [(R * math.sin(math.pi * i / n), -R * math.cos(math.pi * i / n)) for i in range(n + 1)]
        prof[0], prof[-1] = (0.0, -R), (0.0, R)
        seg = segments or 12
    o = geo.lathe(name, [(r, zc + dz) for r, dz in prof], segments=seg, col=col, material=mat, smooth_angle=30)
    o.location = (x, y, 0)
    return o


def lens(name, R, col, mat, depth=0.06, segments=10, x=0.0, z=0.0, y=0.0):
    """Domed cabochon facing -Y (front): lathe built along Z then rotated so the dome points to the viewer."""
    prof = [(0.0, 0.0), (R, 0.0), (R * 0.92, depth * 0.45), (R * 0.55, depth * 0.9), (0.0, depth)]
    o = geo.lathe(name, prof, segments=segments, col=col, material=mat, smooth_angle=35)
    o.rotation_euler = (math.radians(90), 0, 0)    # +Z -> -Y
    o.location = (x, y, z)
    return o


def band(name, z, r, col, mat, h=0.07, segments=10):
    return core.collar(name, z, col, mat, r=r, h=h, segments=segments)


def spike(name, base, direction, length, r, col, mat, segments=4):
    """Small cone from base point along direction (thorns, horn nubs)."""
    d = Vector(direction).normalized()
    o = geo.lathe(name, [(0.0, 0.0), (r, 0.0), (r * 0.55, length * 0.5), (0.0, length)], segments=segments,
                  col=col, material=mat, rot_offset=math.pi / 4, smooth_angle=30)
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    o.location = base
    return o


def ring_h(name, z, R, wire, col, mat, sides=5, samples=20):
    """Horizontal ring (in XY) at height z."""
    pts = [Vector((R * math.cos(2 * math.pi * i / samples), R * math.sin(2 * math.pi * i / samples), z))
           for i in range(samples)]
    return geo.sweep(name, pts, wire, sides=sides, closed=True, col=col, material=mat)


def badge(name, style, z, host_r, col, mat, size=0.15, key='motif2', side=-1):
    """Small motif plate seated into the FRONT (side=-1) or back face of a collar of radius host_r."""
    t = 0.07
    yc = side * (host_r * 0.78)
    fn = style.get(key)
    if not fn:
        return None
    shp = fn(size)
    if shp is None or shp.is_empty:
        return None
    return core.plate(name, core.place(shp, 0, z), t, col, mat, chamfer=min(0.016, size * 0.08), y=yc)


# ------------------------------------------------------------------ haft
def haft(style, ctx, z0, z1, keep_clear=(), name='Haft'):
    """Shaft from z0 to z1 plus race dressing. keep_clear: [(za, zb)] spans with no dressing (grip zones)."""
    col, M = ctx['col'], ctx['mats']
    s = sil(style)
    r = haft_r(style)
    seg = haft_segments(style)
    L = z1 - z0
    parts = [geo.lathe(name, [(0.0, z0), (r * 0.9, z0), (r, z0 + L * 0.35), (r, z0 + L * 0.8), (r * 0.94, z1),
                              (0.0, z1)], segments=seg, col=col, material=M['haft'], smooth_angle=40)]

    def clear(z, pad=0.08):
        return all(not (a - pad <= z <= b + pad) for a, b in keep_clear)

    if s.get('segmented'):
        # bamboo nodes: raised ridges of the haft material every ~0.5 stud
        z = z0 + 0.32
        k = 0
        while z < z1 - 0.15:
            if clear(z):
                parts.append(geo.lathe(f'{name}Node{k}', [(0.0, z - 0.035), (r * 1.02, z - 0.035), (r * 1.17, z),
                                                          (r * 1.02, z + 0.035), (0.0, z + 0.035)],
                                       segments=seg, col=col, material=M['haft'], smooth_angle=40))
            z += 0.52
            k += 1
    elif s.get('riveted') or s.get('heavy'):
        for k, z in enumerate((z0 + 0.4, z0 + L * 0.5, z1 - 0.35)):
            if not clear(z):
                continue
            parts.append(band(f'{name}Band{k}', z, r * 1.3, col, M['accent'], h=0.12, segments=seg))
            for j in range(4):
                a = math.pi / 4 + j * math.pi / 2
                parts.append(gem(f'{name}Rivet{k}_{j}', z, 0.022, col, M['secondary'], segments=6,
                                 x=math.cos(a) * r * 1.33, y=math.sin(a) * r * 1.33))
    elif s.get('clockwork'):
        for k, z in enumerate((z0 + 0.45, z1 - 0.4)):
            if clear(z):
                parts.append(band(f'{name}BandA{k}', z - 0.05, r * 1.22, col, M['accent'], h=0.045, segments=seg))
                parts.append(band(f'{name}BandB{k}', z + 0.05, r * 1.22, col, M['secondary'], h=0.045, segments=seg))
    else:
        for k, z in enumerate((z0 + 0.38, z1 - 0.38)):
            if clear(z):
                parts.append(band(f'{name}Band{k}', z, r * 1.24, col, M['accent'], h=0.06, segments=seg))
    if s.get('organic'):
        # living vine spiralling the upper haft, ends tucked into the wood
        za, zb = (max(z0, *(b for a, b in keep_clear)) + 0.18) if keep_clear else z0 + 0.5, z1 - 0.05
        turns = 2.25
        n = 54
        pts, radii = [], []
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t
            rr = r * (0.75 if i in (0, n) else 1.08)
            pts.append(Vector((rr * math.cos(a), rr * math.sin(a), za + (zb - za) * t)))
            radii.append(0.024 * (0.55 + 0.45 * math.sin(math.pi * t)))
        parts.append(geo.sweep(f'{name}Vine', pts, 0.024, sides=5, col=col, material=M['primary'], radii=radii))
        if s.get('thorns') or s.get('spikes'):
            for j, t in enumerate((0.22, 0.48, 0.74)):
                a = 2 * math.pi * turns * t
                p = Vector((r * 1.12 * math.cos(a), r * 1.12 * math.sin(a), za + (zb - za) * t))
                parts.append(spike(f'{name}Thorn{j}', p, (math.cos(a), math.sin(a), 0.6), 0.08, 0.02, col,
                                   M['primary']))
    return parts


def grip_zone(style, ctx, za, zb, name='Grip'):
    """Two-hand wrap zone with seated collars at both ends. Lower poly than the sword grip (long polearms)."""
    col, M = ctx['col'], ctx['mats']
    r = haft_r(style)
    wraps = max(6, min(11, int(round(style.get('grip_wraps', 6) * 1.35))))
    parts = [geo.wrapped_grip(name, za, zb, r * 1.08, wraps=wraps, segments=8, col=col, material=M['grip'],
                              style='strap')]
    seg = haft_segments(style)
    parts.append(band(f'{name}CollarTop', zb + 0.02, r * 1.4, col, M['accent'], h=0.07, segments=seg))
    parts.append(band(f'{name}CollarBot', za - 0.02, r * 1.4, col, M['accent'], h=0.07, segments=seg))
    return parts


def butt(style, ctx, z0, name='Butt'):
    """Butt ferrule: accent collar + the race pommel hanging below z0."""
    col, M = ctx['col'], ctx['mats']
    r = haft_r(style)
    parts = [band(f'{name}Ferrule', z0 + 0.03, r * 1.32, col, M['accent'], h=0.1, segments=haft_segments(style))]
    parts += core.pommel(name, style, z0 - 0.01, col, M['secondary'], scale=0.75 * (r / 0.074))
    return parts


def hanging(style, ctx, z_top, x_side, name='Charm'):
    """Tassel or charm hanging from a collar at z_top on the +X side (theatrical / segmented races)."""
    kind = tassel_kind(style)
    if not kind:
        return []
    col, M = ctx['col'], ctx['mats']
    drop = 0.42
    pts = [Vector((x_side * 0.85, 0, z_top)), Vector((x_side * 1.15, 0, z_top - 0.08)),
           Vector((x_side * 1.35, -0.01, z_top - drop * 0.6)), Vector((x_side * 1.4, -0.01, z_top - drop))]
    parts = [geo.sweep(f'{name}Cord', pts, 0.014, sides=4, col=col, material=M['accent'])]
    xe, ze = x_side * 1.4, z_top - drop
    if kind == 'tassel':
        cap = geo.lathe(f'{name}Cap', [(0.0, ze + 0.02), (0.035, ze + 0.01), (0.04, ze - 0.04), (0.0, ze - 0.05)],
                        segments=6, col=col, material=M['accent'])
        tuft = geo.lathe(f'{name}Tuft', [(0.0, ze - 0.03), (0.04, ze - 0.03), (0.06, ze - 0.16), (0.07, ze - 0.26),
                                         (0.0, ze - 0.27)], segments=8, col=col, material=M['grip'], smooth_angle=60)
        for o in (cap, tuft):
            o.location = (xe, -0.01, 0)
        parts += [cap, tuft]
    else:
        m = badge(f'{name}Plate', style, ze - 0.09, 0.0, col, M['accent'], size=0.2, key='motif2')
        if m is not None:
            m.location = (xe, -0.01, 0)
            parts.append(m)
        knot = gem(f'{name}Knot', ze + 0.005, 0.025, col, M['accent'], segments=6, x=xe, y=-0.01)
        parts.append(knot)
    return parts


def guard_plate(name, style, w, d, z, t, col, mat, chamfer=0.03, max_h=None):
    g = core.guard_shape(style, w, d)
    if max_h:
        x0, z0, x1, z1 = g.bounds
        if z1 - z0 > max_h:      # flatten tall guards (disk / tsuba / gear) into a collar
            g = affinity.scale(g, xfact=1.0, yfact=max_h / (z1 - z0), origin=(0, 0))
    return core.plate(name, core.place(g, 0, z), t, col, mat, chamfer=chamfer)


def filled(shape):
    """Shape with its holes filled (exteriors only)."""
    geoms = getattr(shape, 'geoms', [shape])
    return unary_union([Polygon(p.exterior.coords) for p in geoms if p.geom_type == 'Polygon']).buffer(0)


def hole_area(shape):
    return filled(shape).area - shape.area


def biggest_hole_centre(shape):
    geoms = getattr(shape, 'geoms', [shape])
    best = None
    for p in geoms:
        for ring in p.interiors:
            h = Polygon(ring.coords)
            if best is None or h.area > best.area:
                best = h
    return best


def disk(r, x=0.0, z=0.0, res=16):
    return Point(x, z).buffer(r, res)
