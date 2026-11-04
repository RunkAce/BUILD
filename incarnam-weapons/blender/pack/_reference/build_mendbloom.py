"""MENDBLOOM - original Eniripsa healing wand for the Incarnam Wakfu pack.

Run:  cd blender && EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python pack/build_mendbloom.py [--preview] [--no-renders]

Class fantasy (Eniripsa): winged, fairy-like healers whose power is spoken words that mend; water-element
heals, marks and support. Design (original, no official item or emblem shapes): a one-handed wand whose head
is a pair of feathered wings rising from a gold collar and curling in toward each other, framing a real open
space that cradles a mint-green dew-drop (the single emissive accent). Pearl-steel wing feathers with rose
enamel inlays, rose-lacquer shaft with gold bands, plum leather strap grip, gold pommel with a small rose drop.

Axes: wand points +Z, broad face of the wings faces -Y. Origin = centre of the grip where the hand closes.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Mendbloom'
ID = 'mendbloom'
ROOT = os.path.dirname(os.path.dirname(HERE))
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
GRIP_TOP, GRIP_BOT = 0.40, -0.40
POMMEL_Z = GRIP_BOT - 0.05
SHAFT_TOP = 1.86
COLLAR_Z = (1.80, 2.02)
WING_ROOT = (0.12, 2.0)
GEM_Z = (2.12, 2.74)
GEM_R = 0.125
# feathers: (angle from vertical, deg, + = outward), length, max width, curl (deg, - = toward the centre/up)
# the long inner feather bows out and curls back in, framing an open space around the dew-drop;
# the outer feathers spread sideways and sweep upward, giving the scalloped wing edge.
FEATHERS = [(40, 1.00, 0.20, -82), (62, 0.84, 0.22, -58), (84, 0.66, 0.21, -42), (104, 0.48, 0.18, -30)]


def band(pts, half_w):
    P = [Vector(p) for p in pts]
    left, right = [], []
    for i, p in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        t = (b - a).normalized()
        n = Vector((-t.y, t.x))
        left.append(tuple(p + n * half_w[i]))
        right.append(tuple(p - n * half_w[i]))
    return Polygon(geo.orient(left + list(reversed(right)))).buffer(0)


def feather(root, ang, length, width, curl, n=20, start=0.0, end=1.0, wscale=1.0):
    """Curved pointed feather: centreline bends by `curl` degrees over its length."""
    pts, ws = [], []
    x, z = root
    a = math.radians(ang)
    step = length / n
    for i in range(n + 1):
        t = i / n
        if start <= t <= end:
            pts.append((x, z))
            # width: narrow quill at root, full at ~45 %, sharp point at tip
            prof = (0.45 + 0.55 * math.sin(min(t / 0.45, 1.0) * math.pi / 2)) if t < 0.45 else \
                max(0.004, (1 - t) / 0.55) ** 0.8
            ws.append(width / 2 * prof * wscale)
        x += math.sin(a) * step
        z += math.cos(a) * step
        a += math.radians(curl) / n
    return band(pts, ws)


def wing(sign):
    fs = [feather(WING_ROOT, *f) for f in FEATHERS]
    # covert body: hull of the feather roots so the wing reads as one solid shape with free feather tips
    roots = unary_union([feather(WING_ROOT, *f, end=0.42) for f in FEATHERS]).convex_hull
    w = unary_union(fs + [roots]).buffer(0.01).buffer(-0.01)
    if sign < 0:
        from shapely.affinity import scale
        w = scale(w, xfact=-1, yfact=1, origin=(0, 0))
    return w


def wing_inlay(sign):
    fs = [feather(WING_ROOT, *f, start=0.3, end=0.85, wscale=0.40) for f in FEATHERS]
    w = unary_union(fs)
    if sign < 0:
        from shapely.affinity import scale
        w = scale(w, xfact=-1, yfact=1, origin=(0, 0))
    return w.intersection(wing(sign).buffer(-0.03))


def mats_for(H):
    specs = {
        'pearl': 'pearl',
        'rose': dict(base='#C9637E', light='#F09AAF', dark='#6A2338', rough=0.36, metal=0.0, relief='hammered', chip=0.45),
        'gold': 'gold_plain',
        'goldf': 'gold',
        'ivory': dict(base='#E9E0D2', light='#FBF6EE', dark='#9C8C7A', rough=0.45, metal=0.0, relief='none'),
        'plum': dict(base='#4B2A38', light='#7A4A5C', dark='#1F1017', rough=0.8, metal=0.0, relief='leather'),
        'dew': dict(base='#7CEBB8', light='#DFFFF0', dark='#1F8A62', rough=0.1, metal=0.0, relief='none', emit=2.0),
    }
    return {k: paint.painted(f'{NAME}_{k}', v, height=H, seed=i * 1.9) for i, (k, v) in enumerate(specs.items())}


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    mats = mats_for(3.6)
    parts = []
    for s, nm in ((1, 'R'), (-1, 'L')):
        parts.append(geo.slab(f'Wing{nm}', shape=wing(s), levels=[(0.0, 0.014), (0.03, 0.05), (0.06, 0.062)],
                              col=col, material=mats['pearl']))
        parts.append(geo.slab(f'WingInlay{nm}', shape=wing_inlay(s), core_t=0.136, edge_t=0.118, bevel_w=0.01,
                              col=col, material=mats['rose']))
    # dew-drop gem (teardrop, pointed top) seated in a gold cradle
    gz0, gz1 = GEM_Z
    gem = geo.lathe('Dew', [(0.0, gz0), (GEM_R * 0.7, gz0 + 0.03), (GEM_R, gz0 + 0.12), (GEM_R * 0.85, gz0 + 0.25),
                            (GEM_R * 0.45, gz0 + 0.42), (0.0, gz1)], segments=8, col=col, material=mats['dew'],
                    smooth_angle=12)
    parts.append(gem)
    parts.append(geo.lathe('Cradle', [(0.0, COLLAR_Z[1] - 0.02), (0.10, COLLAR_Z[1] - 0.02), (0.135, gz0 + 0.07),
                                      (0.118, gz0 + 0.10), (0.085, gz0 + 0.04), (0.0, gz0 + 0.02)], segments=8, col=col,
                           material=mats['goldf'], smooth_angle=25))
    parts.append(geo.lathe('Collar', [(0.0, COLLAR_Z[0]), (0.085, COLLAR_Z[0]), (0.13, COLLAR_Z[0] + 0.05),
                                      (0.17, COLLAR_Z[1] - 0.05), (0.15, COLLAR_Z[1]), (0.0, COLLAR_Z[1])],
                           segments=8, col=col, material=mats['gold']))
    # shaft: rose lacquer tapering toward the head, gold bands
    parts.append(geo.lathe('Shaft', [(0.0, GRIP_TOP - 0.05), (0.072, GRIP_TOP - 0.05), (0.06, 1.2), (0.052, SHAFT_TOP),
                                     (0.0, SHAFT_TOP)], segments=10, col=col, material=mats['ivory']))
    # rose 'spoken word' ribbon inlay spiralling up the shaft, half sunk into it
    hz0, hz1, turns = 0.52, 1.74, 2.0
    helix = []
    for i in range(65):
        t = i / 64
        z = hz0 + t * (hz1 - hz0)
        r = 0.072 - 0.020 * (z - 0.35) / 1.51 + 0.002
        a = t * turns * 2 * math.pi
        helix.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    parts.append(geo.sweep('WordRibbon', helix, 0.026, sides=6, col=col, material=mats['rose'], flatten=0.45))
    for nm, z, r in (('BandA', 1.42, 0.075), ('BandB', 0.86, 0.082)):
        parts.append(geo.lathe(nm, [(0.0, z - 0.04), (r - 0.01, z - 0.04), (r, z - 0.015), (r, z + 0.015),
                                    (r - 0.01, z + 0.04), (0.0, z + 0.04)], segments=10, col=col, material=mats['gold']))
    parts.append(geo.lathe('UpperFerrule', [(0.0, GRIP_TOP - 0.03), (0.098, GRIP_TOP - 0.03), (0.105, GRIP_TOP + 0.02),
                                            (0.09, GRIP_TOP + 0.10), (0.0, GRIP_TOP + 0.10)], segments=8, col=col,
                           material=mats['gold']))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, 0.085, wraps=6, col=col, material=mats['plum'],
                                  style='strap'))
    pz = POMMEL_Z
    parts.append(geo.lathe('Pommel', [(0.0, pz + 0.08), (0.098, pz + 0.08), (0.12, pz), (0.13, pz - 0.10),
                                      (0.09, pz - 0.18), (0.0, pz - 0.20)], segments=8, col=col, material=mats['gold'],
                           smooth_angle=25))
    parts.append(geo.lathe('PommelDrop', [(0.0, pz - 0.17), (0.07, pz - 0.19), (0.075, pz - 0.25), (0.04, pz - 0.33),
                                          (0.0, pz - 0.38)], segments=6, col=col, material=mats['rose'], smooth_angle=20))
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return col, parts, mats


if __name__ == '__main__':
    col, parts, mats = build()
    for p in parts:
        h = geo.mesh_health(p)
        if h['non_manifold_edges'] or not h['normals_outward']:
            print('HEALTH', p.name, h)
    print('tris', geo.tri_count(parts))
    lo, hi = stage.bounds(parts)
    print('bounds', [round(c, 3) for c in lo], [round(c, 3) for c in hi])
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'pack', ID, 'blockout')
        os.makedirs(out, exist_ok=True)
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(parts, v, res=(560, 900) if v != 'side' else (320, 900))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    import json  # noqa: E402
    import pipeline  # noqa: E402
    gem = next(p for p in parts if p.name == 'Dew')
    body_parts = [p for p in parts if p is not gem]
    grip_lead = (0.0, 0.0, 0.0)
    res = pipeline.finish(NAME, col, body_parts, ROOT, grip_lead, glow_parts=[gem], glow_spec=dict(
        base='#7CEBB8', light='#DFFFF0', dark='#1F8A62', rough=0.1, metal=0.0, relief='none', emit=2.0), tex=1024,
        attachments={
            'Grip': grip_lead,
            'VFX_Dew': (0.0, 0.0, (GEM_Z[0] + GEM_Z[1]) / 2),
            'VFX_Tip': (0.0, 0.0, GEM_Z[1] + 0.25),
            'VFX_Pommel': (0.0, 0.0, POMMEL_Z - 0.38),
        })
    print(json.dumps(res['stats'], indent=1))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    rdir = os.path.join(ROOT, 'renders', 'pack', ID)
    pipeline.acceptance_renders(NAME, res['meshes'], res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(res['meshes'], 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
