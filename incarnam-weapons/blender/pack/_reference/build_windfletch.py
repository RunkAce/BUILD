"""WINDFLETCH - original Cra recurve bow for the Incarnam Wakfu pack.

Run:  cd blender && EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python pack/build_windfletch.py [--preview] [--no-renders]

Class fantasy (Cra): proud elf-like long-range archers, precision and keen sight, magic arrows (light,
fire, air) loosed from a bow with no quiver. Design (original, no official item or emblem shapes):
a deep-recurve bow whose limbs carry swept forest-green fletching vanes on their backs, so the
whole bow reads as an arrow's flight feathers spread like wings. Ivory-ash laminated limbs with a
green inlay stripe, aged-gold riser fittings and nock caps, a real sight window through the riser,
brown leather grip. One emissive accent: a pale sky-cyan 'far-light' lens seated under the sight window.

Axes: bow plane = XZ (front view shows the full recurve profile), target side -X, archer/string side +X,
width of limbs along Y. Origin = centre of the grip where the bow hand closes.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Windfletch'
ID = 'windfletch'
ROOT = os.path.dirname(os.path.dirname(HERE))
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
TIP_Z = 2.38                 # bow is 4.76 studs tall (R6 bow 4-5.5)
RISER_TOP = 0.86
GRIP_TOP, GRIP_BOT = 0.24, -0.30
WINDOW = (0.40, 0.74)        # sight window z range
LENS_Z = 0.33
# limb centreline (upper limb; lower limb mirrored in z)
LIMB = [(-0.02, 0.66), (0.00, 0.95), (0.07, 1.35), (0.21, 1.75), (0.38, 2.04), (0.50, 2.20), (0.52, 2.31),
        (0.45, 2.40), (0.32, 2.43), (0.20, 2.40)]
LIMB_W = [0.24, 0.21, 0.18, 0.16, 0.14, 0.12, 0.10, 0.085, 0.07, 0.05]
NOCK = (0.515, 2.27)          # string contact on the recurve


# ---------------------------------------------------------------- outline helpers
def band(pts, half_w):
    """Closed outline around a polyline with per-point half widths (pointed caps optional via 0 width)."""
    P = [Vector(p) for p in pts]
    left, right = [], []
    for i, p in enumerate(P):
        a = P[max(0, i - 1)]
        b = P[min(len(P) - 1, i + 1)]
        t = (b - a).normalized()
        n = Vector((-t.y, t.x))
        left.append(tuple(p + n * half_w[i]))
        right.append(tuple(p - n * half_w[i]))
    return Polygon(geo.orient(left + list(reversed(right)))).buffer(0)


def smooth_path(pts, n=6):
    """Catmull-Rom densify so limbs bend smoothly instead of kinking."""
    P = [Vector(p) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                                    (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    out.append(tuple(P[-1]))
    return out


def interp_w(n_out, ws):
    out = []
    for i in range(n_out):
        f = i / (n_out - 1) * (len(ws) - 1)
        k = min(int(f), len(ws) - 2)
        out.append(ws[k] + (ws[k + 1] - ws[k]) * (f - k))
    return out


def flip(shape):
    from shapely.affinity import scale
    return scale(shape, xfact=1.0, yfact=-1.0, origin=(0, 0))


def limb_shape():
    path = smooth_path(LIMB)
    return band(path, [w / 2 for w in interp_w(len(path), LIMB_W)]), path


def limb_inlay():
    path = smooth_path(LIMB[1:6])
    ws = interp_w(len(path), [0.05, 0.045, 0.04, 0.03, 0.0])
    return band(path, [w / 2 for w in ws])


def vane_shapes():
    """Swept fletching vanes on the limb back (target side, -x): two per limb, raking toward the tip."""
    vanes = []
    # big vane near the limb root, small vane mid-limb
    specs = [((-0.04, 0.98), (0.02, 1.42), 0.40, 0.62), ((0.10, 1.50), (0.20, 1.80), 0.26, 0.40)]
    for (a, b, reach, rise) in specs:
        ax, az = a
        bx, bz = b
        tipx, tipz = ax - reach, az + rise
        outer = geo.bezier((ax + 0.02, az), (ax - reach * 0.45, az + rise * 0.05), (tipx + 0.02, tipz - rise * 0.45),
                           (tipx, tipz), 10)
        inner = geo.bezier((tipx, tipz), (tipx + reach * 0.35, tipz - rise * 0.25), (bx - 0.10, bz - 0.02),
                           (bx + 0.02, bz), 10)
        # feather barb notches along the outer edge
        poly = Polygon(geo.orient(outer + inner[1:])).buffer(0)
        notches = []
        for k in (0.35, 0.62):
            px, pz = outer[int(k * (len(outer) - 1))]
            notches.append(Polygon([(px - 0.12, pz - 0.02), (px + 0.05, pz + 0.035), (px - 0.12, pz + 0.07)]))
        vanes.append(poly.difference(unary_union(notches)).buffer(0))
    return unary_union(vanes)


def riser_shape():
    # deflex riser: forward-bulging handle belly, arrow shelf, sight window (real opening)
    front = [(-0.06, -RISER_TOP), (-0.16, -0.66), (-0.13, -0.34), (-0.10, -0.12), (-0.11, 0.20), (-0.17, 0.36),
             (-0.20, 0.56), (-0.16, 0.78), (-0.06, RISER_TOP)]
    back = [(0.07, RISER_TOP), (0.12, 0.74), (0.13, 0.42), (0.06, 0.34), (0.05, 0.27), (0.10, 0.22),
            (0.10, -0.20), (0.13, -0.40), (0.12, -0.70), (0.07, -RISER_TOP)]
    outline = front + back
    win = geo.bezier((-0.02, WINDOW[0]), (-0.12, WINDOW[0] + 0.04), (-0.12, WINDOW[1] - 0.06), (-0.04, WINDOW[1]), 8) + \
        geo.bezier((-0.04, WINDOW[1]), (0.05, WINDOW[1] - 0.06), (0.06, WINDOW[0] + 0.08), (-0.02, WINDOW[0]), 8)[1:-1]
    return Polygon(geo.orient(outline), [geo.orient(win, False)]).buffer(0)


def lens_setting():
    return Point(-0.045, LENS_Z).buffer(0.10, 6)


def collar_shape(path, i, length=0.12, extra=0.03):
    """Gold band wrapping a limb at path index i."""
    p = Vector(path[i])
    t = (Vector(path[min(i + 1, len(path) - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
    n = Vector((-t.y, t.x))
    w = LIMB_W[0] / 2 + extra
    c = [p - t * length / 2 + n * w, p + t * length / 2 + n * w * 0.9, p + t * length / 2 - n * w * 0.9, p - t * length / 2 - n * w]
    return Polygon(geo.orient([tuple(v) for v in c])).buffer(0)


def nock_cap():
    path = smooth_path(LIMB)
    tail = path[-16:]
    ws = interp_w(len(tail), [0.15, 0.135, 0.12, 0.10, 0.075, 0.0])
    cap = band(tail, [w / 2 for w in ws]).buffer(0.01)
    # small barb on the outer curl: the tip reads as an arrowhead hook
    ex, ez = tail[-1]
    barb = Polygon(geo.orient([(ex + 0.04, ez - 0.03), (ex - 0.13, ez - 0.10), (ex + 0.01, ez + 0.04)]))
    return unary_union([cap, barb]).buffer(0)


def mats_for(H):
    specs = {
        'ash': dict(base='#E2D4B2', light='#FAF2DC', dark='#8F7A58', rough=0.55, metal=0.0, relief='none', chip=0.0,
                    paint_light=0.6),
        'fletch': dict(base='#3F7F57', light='#7DBB86', dark='#1C3A29', rough=0.45, metal=0.0, relief='hammered',
                       chip=0.45),
        'gold': 'gold_plain',
        'goldf': 'gold',
        'leather': dict(base='#5A3B27', light='#8A5E3E', dark='#26170E', rough=0.8, metal=0.0, relief='leather'),
        'string': dict(base='#E9E1C8', light='#FFFFFF', dark='#9A917A', rough=0.85, metal=0.0, relief='none'),
        'lens': dict(base='#8FE6F2', light='#E8FCFF', dark='#2E8CA6', rough=0.1, metal=0.0, relief='none', emit=2.2),
    }
    return {k: paint.painted(f'{NAME}_{k}', v, height=H, seed=i * 2.7) for i, (k, v) in enumerate(specs.items())}


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    mats = mats_for(2 * TIP_Z)
    parts = []
    limb, path = limb_shape()
    inlay = limb_inlay()
    vanes = vane_shapes()
    for side, f in (('U', lambda s: s), ('L', flip)):
        parts.append(geo.slab(f'Limb{side}', shape=f(limb), levels=[(0.0, 0.035), (0.03, 0.075), (0.06, 0.085)],
                              col=col, material=mats['ash']))
        parts.append(geo.slab(f'LimbInlay{side}', shape=f(inlay), core_t=0.186, edge_t=0.165, bevel_w=0.01,
                              col=col, material=mats['fletch']))
        parts.append(geo.slab(f'Vanes{side}', shape=f(vanes.difference(limb.buffer(-0.03))),
                              levels=[(0.0, 0.012), (0.03, 0.045), (0.07, 0.055)], col=col, material=mats['fletch']))
        parts.append(geo.slab(f'Collar{side}', shape=f(collar_shape(path, 4)), levels=[(0.0, 0.08), (0.02, 0.105)],
                              col=col, material=mats['gold']))
        parts.append(geo.slab(f'NockCap{side}', shape=f(nock_cap()), levels=[(0.0, 0.05), (0.02, 0.07)],
                              col=col, material=mats['gold']))
    for o in parts:
        if o.name.startswith(('Limb', 'Vanes')):
            for v in o.data.vertices:
                t = max(0.0, min(1.0, (abs(v.co.z) - 0.9) / (TIP_Z - 0.9)))
                v.co.y *= 1.0 - 0.42 * t
    riser = riser_shape()
    parts.append(geo.slab('Riser', shape=riser, levels=[(0.0, 0.04), (0.035, 0.085), (0.06, 0.095)],
                          col=col, material=mats['fletch']))
    # gold window frame inlay on both faces (seated into the riser face)
    win_hole = Polygon(riser.interiors[0])
    frame = win_hole.buffer(0.045, join_style='mitre').difference(win_hole).intersection(riser.buffer(-0.02))
    parts.append(geo.slab('WindowFrame', shape=frame, core_t=0.215, edge_t=0.19, bevel_w=0.012, col=col,
                          material=mats['goldf']))
    point = Polygon(geo.orient([(-0.02, -0.40), (0.05, -0.50), (0.0, -0.78), (-0.08, -0.52)]))
    parts.append(geo.slab('RiserInlay', shape=point.intersection(riser.buffer(-0.03)), core_t=0.215, edge_t=0.19,
                          bevel_w=0.012, col=col, material=mats['goldf']))
    parts.append(geo.slab('LensSetting', shape=lens_setting(), levels=[(0.0, 0.08), (0.025, 0.12)], col=col,
                          material=mats['gold']))
    lens = geo.lathe('Lens', [(0.0, -0.17), (0.045, -0.155), (0.068, -0.115), (0.068, 0.115), (0.045, 0.155), (0.0, 0.17)],
                     segments=6, col=col, material=mats['lens'], smooth_angle=10)
    lens.rotation_euler = (math.radians(90), 0, 0)
    lens.location = (-0.045, 0, LENS_Z)
    parts.append(lens)
    # grip: leather wrap around the narrow handle section, gold bands either end
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, 0.105, wraps=5, col=col, material=mats['leather'],
                                  style='strap', flatten=1.0))
    for nm, z in (('GripBandTop', GRIP_TOP), ('GripBandBot', GRIP_BOT)):
        parts.append(geo.lathe(nm, [(0.0, z - 0.035), (0.13, z - 0.035), (0.14, z), (0.13, z + 0.035), (0.0, z + 0.035)],
                               segments=8, col=col, material=mats['gold']))
    # string: nock to nock along the recurve bellies
    top = Vector((NOCK[0], 0, NOCK[1]))
    bot = Vector((NOCK[0], 0, -NOCK[1]))
    pts = [top.lerp(bot, i / 6) for i in range(7)]
    parts.append(geo.sweep('String', pts, 0.014, sides=6, col=col, material=mats['string']))
    serving = geo.lathe('Serving', [(0.0, -0.22), (0.022, -0.22), (0.022, 0.22), (0.0, 0.22)], segments=6, col=col,
                        material=mats['leather'])
    serving.location = (NOCK[0], 0, 0.02)
    parts.append(serving)
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
    lens = next(p for p in parts if p.name == 'Lens')
    body_parts = [p for p in parts if p is not lens]
    grip_lead = (0.0, 0.0, 0.0)
    res = pipeline.finish(NAME, col, body_parts, ROOT, grip_lead, glow_parts=[lens], glow_spec=dict(
        base='#8FE6F2', light='#E8FCFF', dark='#2E8CA6', rough=0.1, metal=0.0, relief='none', emit=2.2), tex=1024,
        attachments={
            'Grip': grip_lead,
            'StringTop': (NOCK[0], 0.0, NOCK[1]),
            'StringBottom': (NOCK[0], 0.0, -NOCK[1]),
            'ArrowNock': (NOCK[0], 0.0, 0.27),       # nocking point on the string, level with the arrow shelf
            'ArrowRest': (0.05, 0.0, 0.27),
            'VFX_Lens': (-0.045, 0.0, LENS_Z),
            'VFX_TipTop': (0.30, 0.0, TIP_Z),
            'VFX_TipBottom': (0.30, 0.0, -TIP_Z),
        })
    print(json.dumps(res['stats'], indent=1))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    rdir = os.path.join(ROOT, 'renders', 'pack', ID)
    pipeline.acceptance_renders(NAME, res['meshes'], res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(res['meshes'], 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
