"""Weapon kit core: shared building blocks for the race x category matrix.

A weapon = CATEGORY TEMPLATE (lib/kit/categories/<cat>.py)  x  RACE STYLE (lib/kit/races/<race>.py).

Coordinates: weapon points UP (+Z), front face toward -Y, 1 unit = 1 R6 stud. 2D outlines are (x, z).

RACE STYLE CONTRACT  (lib/kit/races/<race>.py must define STYLE = {...}):
  id            'cra'                         lowercase id
  race          'Cra'                         display name
  names         {category: 'OriginalName'}    one original weapon name per category (12)
  mats          {role: paint spec}            roles: primary (blade/head metal), secondary (guard/trim),
                                              accent (inlays), grip (wrap), haft (shafts/handles/wood),
                                              glow (emissive accent; spec with emit=...)
  blade         dict(edge=..., tip=..., width=1.0, holes=..., notch=...)   see blade_outline()
  guard         one of GUARDS keys                               (or a callable(width, depth) -> shape)
  pommel        one of POMMELS keys
  grip_wraps    int, 4..9
  chain_link    one of CHAIN_LINKS keys (box, oval, bone, ring, gear, bamboo)
  motif         callable(size) -> shapely Polygon/MultiPolygon centred at (0,0), fits in size x size.
                ORIGINAL emblem expressing the race (never an official class emblem).
  motif2        optional second motif (small accent: e.g. leaf, rivet, rune) callable(size)
  head          optional dict for staff/blunt/gun heads, e.g. dict(staff='orb'|'crescent'|'motif'|'cage',
                blunt='hammer'|'mace'|'club'|'motif', gun='pistol'|'blunderbuss'|'rifle')
  silhouette    dict of free-form tweaks templates may read (curve=0.0..1.0, spikes=bool, chunky=1.0 ...)

CATEGORY TEMPLATE CONTRACT (lib/kit/categories/<cat>.py must define build(style, ctx) -> Build):
  Build = dict(
    body=[objects],            static main mesh parts (joined + baked as <Name>_Body)
    glow=[objects],            emissive parts (joined as <Name>_Glow)        [optional]
    pieces={name: [objects]},  extra separately-exported pieces, e.g. 'L' (left copy for dual/fists),
                               'Head' (thrown chain head), each baked on its own   [optional]
    mirror_pieces={name: src}, piece to create by mirroring another piece in X (shares its texture)  [optional]
    chain=dict(link='<chain_link key>') if the weapon uses the runtime chain system           [optional]
    piece_attachments={piece: {name: (x,y,z)}}  attachments on separate pieces (e.g. {'Head': {'ChainEnd': ..}})
    grip=(x, y, z),            leading-hand grip point (becomes the origin)
    attachments={name: (x,y,z)} Roblox attachment points (Grip, GripSecondary, ChainEnd, VFX_*)
  )
"""
import math

import bpy
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

import geo
import paint

CATEGORIES = ['fists', 'staff', 'spear', 'sword', 'greatsword', 'gun', 'dagger', 'scythe', 'katana',
              'dual_blades', 'chain', 'blunt']

# R6 size targets: total length along +Z (studs) and grip radius
SIZES = {
    'fists':       dict(length=(1.0, 1.7), note='gauntlet/knuckle worn on the R6 arm end (1x1)'),
    'staff':       dict(length=(5.0, 6.8)),
    'spear':       dict(length=(5.5, 7.5)),
    'sword':       dict(length=(3.4, 4.6)),
    'greatsword':  dict(length=(5.0, 6.5)),
    'gun':         dict(length=(2.2, 3.6), note='length = muzzle to stock along +Z (barrel up)'),
    'dagger':      dict(length=(1.8, 2.6)),
    'scythe':      dict(length=(5.0, 6.8)),
    'katana':      dict(length=(4.2, 5.2)),
    'dual_blades': dict(length=(2.6, 3.6), note='per blade'),
    'chain':       dict(length=(1.6, 3.2), note='handle + head (head separate piece)'),
    'blunt':       dict(length=(3.4, 6.0)),
}
GRIP_R = 0.09


# ------------------------------------------------------------------ materials
def materials(style, height, prefix):
    """Instantiate the race's material roles for one weapon (unique names per weapon)."""
    out = {}
    for i, (role, spec) in enumerate(style['mats'].items()):
        out[role] = paint.painted(f'{prefix}_{role}', spec, height=height, seed=i * 2.7 + len(prefix))
    for role, fallback in (('haft', 'grip'), ('accent', 'secondary'), ('glow', 'accent')):
        out.setdefault(role, out.get(fallback))
    return out


# ------------------------------------------------------------------ 2D helpers
def poly(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def mirror(shape):
    return affinity.scale(shape, xfact=-1, yfact=1, origin=(0, 0))


def place(shape, x=0.0, z=0.0, scale=1.0, rot=0.0):
    s = affinity.scale(shape, scale, scale, origin=(0, 0)) if scale != 1 else shape
    if rot:
        s = affinity.rotate(s, rot, origin=(0, 0))
    return affinity.translate(s, x, z)


def bend(shape, curvature, z0=0.0):
    """Bend a shape along +Z into an arc toward +X (curvature = 1/radius). Used for katanas, scythes."""
    if abs(curvature) < 1e-6:
        return shape
    R = 1.0 / curvature

    def tf(x, z):
        t = (z - z0) / R
        return (R - (R - x) * math.cos(t), z0 + (R - x) * math.sin(t))

    def ring(coords):
        return [tf(x, z) for x, z in coords]

    def one(p):
        return Polygon(ring(p.exterior.coords), [ring(i.coords) for i in p.interiors]).buffer(0)
    dense = shape.segmentize(0.03)
    if dense.geom_type == 'MultiPolygon':
        return unary_union([one(p) for p in dense.geoms])
    return one(dense)


# ------------------------------------------------------------------ blades
def blade_outline(length, width, edge='straight', tip='point', holes='none', notch='none', single_edge=False,
                  seed=0):
    """Blade from z=0 (root) to z=length (tip), centred on x=0, half-width = width/2.
    edge : straight | leaf | serrated | wavy | crystal | jagged | broad
    tip  : point | clip | split | chisel | hook
    holes: none | slot | rings | motif (caller cuts motif separately)
    notch: none | scoop | teeth
    single_edge: spine on the -X side (katana/cleaver-like)."""
    hw = width / 2
    n = 28
    tip_len = {'point': 0.24, 'clip': 0.2, 'split': 0.22, 'chisel': 0.1, 'hook': 0.18}.get(tip, 0.22) * length
    body = length - tip_len
    right, left = [], []
    for i in range(n + 1):
        t = i / n
        z = t * body
        w = hw
        if edge == 'leaf':
            w = hw * (0.78 + 0.32 * math.sin(math.pi * min(1, t * 1.1)))
        elif edge == 'broad':
            w = hw * (0.92 + 0.12 * t)
        elif edge == 'wavy':
            w = hw * (0.88 + 0.14 * math.sin(t * math.pi * 6))
        elif edge == 'crystal':
            w = hw * (0.78 + 0.26 * (1 if i % 4 < 2 else 0))
        elif edge == 'jagged':
            w = hw * (0.82 + 0.2 * (((i * 7 + seed) % 5) / 4))
        wr = w
        if edge == 'serrated' and 0.15 < t < 0.85:
            wr = w * (1.0 if i % 2 == 0 else 0.86)
        if notch == 'scoop' and 0.55 < t < 0.68:
            wr = w * (0.72 + 1.6 * abs(t - 0.615))
        if notch == 'teeth' and 0.2 < t < 0.7 and i % 3 == 0:
            wr = w * 1.08
        right.append((wr, z))
        left.append((-(hw * 0.42 if single_edge else w), z))
    # tips
    if tip == 'point':
        tip_pts_r, tip_pts_l = [(0.0, length)], []
    elif tip == 'clip':
        tip_pts_r = [(hw * 0.3, body + tip_len * 0.55), (-hw * 0.15, length)]
        tip_pts_l = []
    elif tip == 'chisel':
        tip_pts_r = [(-hw * 0.5, length)]
        tip_pts_l = []
    elif tip == 'hook':
        tip_pts_r = [(hw * 1.05, body + tip_len * 0.7), (hw * 0.2, length)]
        tip_pts_l = []
    else:  # split
        tip_pts_r = [(hw * 0.55, length), (hw * 0.12, body + tip_len * 0.25), (-hw * 0.12, body + tip_len * 0.25),
                     (-hw * 0.55, length * 0.985)]
        tip_pts_l = []
    lft = left[::-1]
    outline = right + tip_pts_r + tip_pts_l + lft
    shape = poly(outline)
    if holes == 'slot':
        shape = shape.difference(poly([(-hw * 0.18, body * 0.12), (hw * 0.18, body * 0.12), (hw * 0.2, body * 0.78),
                                        (0, body * 0.86), (-hw * 0.2, body * 0.78)]))
    elif holes == 'rings':
        cx = -hw * 0.45 if single_edge else 0.0
        for k in range(3):
            shape = shape.difference(Point(cx, body * (0.25 + k * 0.18)).buffer(hw * 0.2, 12))
    return shape.buffer(0)


def blade(name, shape, length, col, mat, thickness=0.12, edge_t=0.02, bevel=None):
    """Chunky stylized blade slab with a two-step bevel (house style)."""
    bw = bevel or min(0.075, max(0.03, shape.bounds[2] * 0.22))
    return geo.slab(name, shape=shape, core_t=thickness, edge_t=edge_t, bevel_w=bw,
                    levels=[(0.0, edge_t / 2), (bw * 0.45, thickness * 0.33), (bw, thickness / 2)],
                    col=col, material=mat)


def plate(name, shape, thickness, col, mat, chamfer=0.02, y=0.0):
    """Flat chamfered part (guards, inlays, motif plates). Inlays: make it slightly thicker than the host."""
    return geo.slab(name, shape=shape, core_t=thickness, edge_t=max(thickness * 0.55, thickness - 2 * chamfer),
                    bevel_w=chamfer, col=col, material=mat, y_offset=y)


# ------------------------------------------------------------------ guards (2D shapes centred at z=0)
def _crescent(w, d):
    o = geo.bezier((0, -d * 0.5), (w * 0.6, -d * 0.5), (w * 0.95, 0.0), (w, d * 1.2), 12)
    i = geo.bezier((w, d * 1.2), (w * 0.8, d * 0.5), (w * 0.55, d * 0.35), (0, d * 0.4), 12)
    half = o + i[1:]
    return poly(half + [(-x, z) for x, z in reversed(half)][1:-1])


def _bar(w, d):
    return unary_union([box(-w, -d * 0.3, w, d * 0.3), Point(w, 0).buffer(d * 0.45, 8), Point(-w, 0).buffer(d * 0.45, 8)])


def _disk(w, d):
    return Point(0, 0).buffer(max(w * 0.55, d), 24)


def _wings(w, d):
    out = []
    for s in (1, -1):
        out.append(poly([(s * 0.05, -d * 0.4), (s * w, d * 0.1), (s * w * 1.05, d * 1.0), (s * w * 0.6, d * 0.35),
                         (s * 0.05, d * 0.4)]))
    return unary_union(out)


def _fang(w, d):
    out = [box(-w * 0.7, -d * 0.3, w * 0.7, d * 0.35)]
    for s in (1, -1):
        out.append(poly([(s * w * 0.55, -d * 0.3), (s * w, -d * 1.3), (s * w * 0.75, -d * 0.2)]))
    return unary_union(out)


def _gear(w, d):
    r = max(w * 0.6, d)
    pts = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        rr = r * (1.0 if (i // 2) % 2 == 0 else 0.8)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return poly(pts).difference(Point(0, 0).buffer(r * 0.28, 12))


def _leaf(w, d):
    out = []
    for s in (1, -1):
        a = geo.bezier((0, 0), (s * w * 0.3, d * 0.9), (s * w * 0.8, d * 0.8), (s * w, d * 0.2), 10)
        b = geo.bezier((s * w, d * 0.2), (s * w * 0.7, -d * 0.4), (s * w * 0.3, -d * 0.4), (0, 0), 10)
        out.append(poly(a + b[1:]))
    return unary_union(out + [Point(0, 0).buffer(d * 0.45, 10)])


def _swept(w, d):
    out = []
    for s in (1, -1):
        out.append(poly([(0, -d * 0.4), (s * w * 0.9, -d * 0.2), (s * w, -d * 0.9), (s * w * 1.1, d * 0.2),
                         (0, d * 0.45)]))
    return unary_union(out)


def _tsuba(w, d):
    r = max(w * 0.45, d * 0.9)
    return Point(0, 0).buffer(r, 6).buffer(r * 0.12, 4)


GUARDS = {'crescent': _crescent, 'bar': _bar, 'disk': _disk, 'wings': _wings, 'fang': _fang, 'gear': _gear,
          'leaf': _leaf, 'swept': _swept, 'tsuba': _tsuba}


def guard_shape(style, w, d):
    g = style.get('guard', 'bar')
    return (g if callable(g) else GUARDS.get(g, _bar))(w, d)


# ------------------------------------------------------------------ pommels (lathe profiles, z from 0 downward)
POMMELS = {
    'spike':   [(0.0, 0.0), (0.12, -0.02), (0.15, -0.10), (0.13, -0.18), (0.0, -0.46)],
    'orb':     [(0.0, 0.0), (0.09, -0.02), (0.15, -0.09), (0.16, -0.17), (0.12, -0.26), (0.0, -0.30)],
    'faceted': [(0.0, 0.0), (0.12, -0.01), (0.17, -0.08), (0.17, -0.18), (0.10, -0.26), (0.0, -0.28)],
    'cap':     [(0.0, 0.0), (0.13, 0.0), (0.14, -0.08), (0.11, -0.12), (0.0, -0.13)],
    'ring':    None,   # handled specially: cap + loop
    'fang':    [(0.0, 0.0), (0.12, -0.02), (0.14, -0.06), (0.06, -0.3), (0.0, -0.36)],
}


def pommel(name, style, z, col, mat, scale=1.0, segments=None):
    kind = style.get('pommel', 'faceted')
    parts = []
    prof = POMMELS.get(kind) or POMMELS['cap']
    seg = segments or (4 if kind in ('spike', 'fang') else 8)
    parts.append(geo.lathe(name, [(r * scale, z + dz * scale) for r, dz in prof], segments=seg,
                           rot_offset=math.pi / 4 if seg == 4 else None, col=col, material=mat, smooth_angle=25))
    if kind == 'ring':
        rg = geo.ring(f'{name}Ring', 0.07 * scale, 0.02 * scale, sides=6, samples=14, col=col, material=mat)
        rg.location = (0, 0, z - 0.2 * scale)
        parts.append(rg)
    return parts


def grip(name, z0, z1, style, col, mat, radius=GRIP_R):
    return geo.wrapped_grip(name, z0, z1, radius, wraps=style.get('grip_wraps', 6), col=col, material=mat,
                            style='strap')


def collar(name, z, col, mat, r=0.12, h=0.08, segments=8):
    return geo.lathe(name, [(0.0, z - h / 2), (r, z - h / 2), (r + 0.012, z), (r, z + h / 2), (0.0, z + h / 2)],
                     segments=segments, col=col, material=mat)


def shaft(name, z0, z1, col, mat, r=0.075, segments=10):
    return geo.lathe(name, [(0.0, z0), (r, z0), (r, z1), (0.0, z1)], segments=segments, col=col, material=mat)


def motif_plate(name, style, size, x, z, thickness, col, mat, key='motif'):
    fn = style.get(key)
    if not fn:
        return None
    shp = fn(size)
    if shp is None or shp.is_empty:
        return None
    return plate(name, place(shp, x, z), thickness, col, mat, chamfer=min(0.02, size * 0.06))


def face_on(obj, axis='Y'):
    """Rotate a slab (built in XZ) to face +X instead (for side plates on guns etc.)."""
    obj.rotation_euler = (0, 0, math.radians(90))
    return obj


# ------------------------------------------------------------------ chain links (one link mesh; runtime repeats it)
LINK = dict(length=0.27, width=0.10, bar=0.03)   # pitch = length - 2*bar = 0.21 (matches WarlinkChain default)


def chain_link(name, kind, col, mat):
    ln, w, bar = LINK['length'], LINK['width'], LINK['bar']
    if kind == 'oval':
        return geo.sweep(name, geo.stadium_path(ln - bar, w - bar, 24), bar / 2, sides=6, closed=True, col=col,
                         material=mat, flatten=0.8)
    if kind == 'ring':
        return geo.ring(name, ln / 2 - bar / 2, bar / 2, sides=6, samples=18, col=col, material=mat)
    if kind == 'bone':
        frame = box(-w / 2, -ln / 2, w / 2, ln / 2).difference(box(-w / 2 + bar, -ln / 2 + bar, w / 2 - bar, ln / 2 - bar))
        knobs = unary_union([Point(sx * w / 2, sz * ln / 2).buffer(bar * 0.9, 6) for sx in (1, -1) for sz in (1, -1)])
        return geo.slab(name, shape=frame.union(knobs), core_t=bar, edge_t=bar * 0.55, bevel_w=bar * 0.25, col=col,
                        material=mat, smooth_angle=20)
    if kind == 'gear':
        outer = Point(0, 0).buffer(ln / 2, 12)
        teeth = unary_union([place(box(-bar * 0.5, ln / 2 - bar * 0.2, bar * 0.5, ln / 2 + bar * 0.6), rot=a)
                             for a in range(0, 360, 45)])
        frame = outer.union(teeth).difference(Point(0, 0).buffer(ln / 2 - bar, 12))
        return geo.slab(name, shape=frame, core_t=bar, edge_t=bar * 0.55, bevel_w=bar * 0.25, col=col, material=mat,
                        smooth_angle=20)
    if kind == 'bamboo':
        seg = geo.lathe(name, [(0.0, -ln / 2), (w * 0.32, -ln / 2), (w * 0.38, -ln / 2 + bar), (w * 0.3, -ln * 0.1),
                               (w * 0.36, 0), (w * 0.3, ln * 0.1), (w * 0.38, ln / 2 - bar), (w * 0.32, ln / 2), (0.0, ln / 2)],
                        segments=8, col=col, material=mat)
        return seg
    # box (default, user's reference style)
    frame = box(-w / 2, -ln / 2, w / 2, ln / 2).difference(box(-w / 2 + bar, -ln / 2 + bar, w / 2 - bar, ln / 2 - bar))
    return geo.slab(name, shape=frame, core_t=bar, edge_t=bar * 0.55, bevel_w=bar * 0.22, col=col, material=mat,
                    smooth_angle=20)


CHAIN_LINKS = ['box', 'oval', 'ring', 'bone', 'gear', 'bamboo']


def apply(objs):
    for o in objs:
        if o is None:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return [o for o in objs if o is not None]
