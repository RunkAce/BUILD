"""STILLHAND - original Xelor-inspired clock-hand war needle (Wakfu pack).

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python pack/build_stillhand.py [--preview] [--no-renders]

Design: a staff-length NEEDLE built as an oversized clock hand. A polished brass pointer blade with a real
open "moon" ring and a spade point rises out of a dial hub: navy enamel face, brass bezel, twelve raised hour
ticks, a short brass minute hand frozen near ten, and a cyan time-crystal at the arbor (the single emissive
accent). Navy enamel octagonal shaft with brass bands, a two-hand grip of cream mummy bandage, and a clock-hand
counterweight tail (open ring) as the butt. Colour story: deep navy + warm brass + bandage cream, one cyan glow.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))
ROOT = os.path.dirname(os.path.dirname(HERE))

import bpy  # noqa: E402
from shapely.affinity import rotate as srotate  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Stillhand'
ID = 'stillhand'
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
GRIP_TOP, GRIP_BOT = 0.0, -1.0
HUB = 2.20                 # dial centre
DIAL_R = 0.42
RING_Z, RING_RO, RING_RI = 3.52, 0.20, 0.11    # open moon ring on the pointer
TIP_Z = 4.42
SHAFT_R = 0.072
TAIL_RING_Z = -1.42

SPECS = {
    'brass': dict(base='#C29A52', light='#F2D79A', dark='#5C4120', rough=0.28, metal=1.0, relief='hammered', paint_light=0.5),
    'brass_fil': dict(base='#B88F4A', light='#EBCF90', dark='#56391C', rough=0.30, metal=1.0, relief='filigree', paint_light=0.5),
    'navy': dict(base='#1F3368', light='#4466A8', dark='#0B1430', rough=0.36, metal=0.0, relief='hammered', chip=0.4),
    'bandage': dict(base='#E2D7BC', light='#FAF4E4', dark='#8F8467', rough=0.9, metal=0.0, relief='weave'),
    'glow': dict(base='#46D8F0', light='#B8F6FF', dark='#127A9C', rough=0.12, metal=0.0, relief='none', emit=2.0),
}


def pointer_lower():
    return Polygon(geo.orient(geo.mirror_x([(0.0, RING_Z - RING_RO + 0.05), (0.06, RING_Z - RING_RO + 0.05),
                                            (0.07, RING_Z - RING_RO - 0.06), (0.17, HUB + 0.66), (0.155, HUB + 0.42),
                                            (0.10, HUB), (0.0, HUB)])))


def pointer_shape():
    """Clock-hand blade from the arbor to the spade point, with a real open moon ring."""
    half = [(0.0, TIP_Z), (0.13, TIP_Z - 0.30), (0.27, TIP_Z - 0.46), (0.085, TIP_Z - 0.58),   # spade
            (0.06, RING_Z + RING_RO - 0.05)]
    stem_top = Polygon(geo.orient(geo.mirror_x(half + [(0.0, RING_Z + RING_RO - 0.05)])))
    ring_out = Point(0, RING_Z).buffer(RING_RO, 32)
    body = unary_union([stem_top, ring_out, pointer_lower()]).buffer(0.012).buffer(-0.012)
    return body.difference(Point(0, RING_Z).buffer(RING_RI, 24))


def pointer_inlay():
    """Navy enamel channel down the lower stem (two-tone clock hand)."""
    from shapely.geometry import box
    return pointer_lower().buffer(-0.05, join_style='mitre').intersection(box(-1, HUB + DIAL_R + 0.05, 1, RING_Z - RING_RO - 0.06))


def tail_shape():
    """Counterweight tail at the butt: short taper into an open ring."""
    taper = Polygon(geo.orient(geo.mirror_x([(0.0, GRIP_BOT - 0.08), (0.075, GRIP_BOT - 0.08), (0.06, TAIL_RING_Z + 0.10),
                                             (0.0, TAIL_RING_Z)])))
    ring = Point(0, TAIL_RING_Z).buffer(0.16, 28)
    return unary_union([taper, ring]).buffer(0.01).buffer(-0.01).difference(Point(0, TAIL_RING_Z).buffer(0.075, 20))


def tick_shapes():
    out = []
    for i in range(12):
        a = math.radians(90 - i * 30)
        major = i % 3 == 0
        r0, r1 = (0.21, 0.32) if major else (0.255, 0.32)
        w = 0.035 if major else 0.02
        t = Polygon(geo.orient([(-w, r0), (w, r0), (w * 1.3, r1), (-w * 1.3, r1)]))
        out.append(srotate(t, -i * 30, origin=(0, 0)))
    from shapely.affinity import translate
    return translate(unary_union(out), 0, HUB)


def minute_hand():
    h = Polygon(geo.orient([(0.0, -0.06), (0.045, 0.0), (0.026, 0.19), (0.0, 0.24), (-0.026, 0.19), (-0.045, 0.0)]))
    from shapely.affinity import translate
    return translate(srotate(h, 62, origin=(0, 0)), 0, HUB)


def apply(parts):
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    H = TIP_Z - TAIL_RING_Z + 0.2
    mats = {k: paint.painted(f'{NAME}_{k}', v, height=H, seed=i * 2.1) for i, (k, v) in enumerate(SPECS.items())}
    parts = []
    # pointer blade (brass), base hidden inside the dial
    parts.append(geo.slab('Pointer', shape=pointer_shape(), levels=[(0.0, 0.014), (0.03, 0.045), (0.06, 0.058)],
                          col=col, material=mats['brass']))
    parts.append(geo.slab('PointerInlay', shape=pointer_inlay(), levels=[(0.0, 0.054), (0.012, 0.062)],
                          col=col, material=mats['navy']))
    # dial: navy face, brass bezel, raised ticks, minute hand, arbor boss
    parts.append(geo.slab('DialFace', shape=Point(0, HUB).buffer(DIAL_R - 0.06, 40),
                          levels=[(0.0, 0.066), (0.02, 0.075)], col=col, material=mats['navy']))
    bezel = Point(0, HUB).buffer(DIAL_R, 40).difference(Point(0, HUB).buffer(DIAL_R - 0.075, 40))
    parts.append(geo.slab('Bezel', shape=bezel, levels=[(0.0, 0.06), (0.025, 0.105), (0.04, 0.115)],
                          col=col, material=mats['brass']))
    parts.append(geo.slab('Ticks', shape=tick_shapes(), levels=[(0.0, 0.080), (0.008, 0.088)], col=col,
                          material=mats['brass']))
    parts.append(geo.slab('MinuteHand', shape=minute_hand(), levels=[(0.0, 0.086), (0.012, 0.096)], col=col,
                          material=mats['brass']))
    boss = geo.lathe('ArborBoss', [(0.0, -0.11), (0.085, -0.11), (0.10, -0.085), (0.10, 0.085), (0.085, 0.11), (0.0, 0.11)],
                     segments=10, col=col, material=mats['brass'], smooth_angle=20)
    boss.rotation_euler = (math.radians(90), 0, 0)
    boss.location = (0, 0, HUB)
    parts.append(boss)
    # socket where the shaft clasps the bezel
    sz = HUB - DIAL_R
    parts.append(geo.lathe('Socket', [(0.0, sz - 0.22), (0.085, sz - 0.22), (0.11, sz - 0.16), (0.11, sz + 0.01),
                                      (0.09, sz + 0.05), (0.0, sz + 0.05)], segments=8, col=col,
                           material=mats['brass_fil'], smooth_angle=25))
    # navy octagonal shaft with brass bands
    parts.append(geo.lathe('Shaft', [(0.0, GRIP_TOP), (SHAFT_R, GRIP_TOP), (SHAFT_R * 0.92, sz - 0.18), (0.0, sz - 0.18)],
                           segments=8, col=col, material=mats['navy'], smooth_angle=30))
    for i, z in enumerate((0.75, 1.40)):
        parts.append(geo.lathe(f'Band{i}', [(0.0, z - 0.05), (0.088, z - 0.05), (0.095, z - 0.03), (0.095, z + 0.03),
                                            (0.088, z + 0.05), (0.0, z + 0.05)], segments=8, col=col,
                               material=mats['brass'], smooth_angle=25))
    # grip collars and bandage grip
    parts.append(geo.lathe('UpperCollar', [(0.0, GRIP_TOP - 0.03), (0.098, GRIP_TOP - 0.03), (0.11, GRIP_TOP + 0.01),
                                           (0.11, GRIP_TOP + 0.08), (0.085, GRIP_TOP + 0.12), (0.0, GRIP_TOP + 0.12)],
                           segments=8, col=col, material=mats['brass'], smooth_angle=25))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, 0.082, wraps=9, col=col, material=mats['bandage'],
                                  style='round'))
    parts.append(geo.lathe('LowerCollar', [(0.0, GRIP_BOT - 0.10), (0.085, GRIP_BOT - 0.10), (0.11, GRIP_BOT - 0.06),
                                           (0.11, GRIP_BOT + 0.02), (0.098, GRIP_BOT + 0.04), (0.0, GRIP_BOT + 0.04)],
                           segments=8, col=col, material=mats['brass'], smooth_angle=25))
    parts.append(geo.slab('Tail', shape=tail_shape(), levels=[(0.0, 0.02), (0.03, 0.055), (0.05, 0.065)],
                          col=col, material=mats['brass']))
    gem = geo.lathe('TimeCrystal', [(0.0, -0.165), (0.045, -0.13), (0.062, -0.06), (0.062, 0.06), (0.045, 0.13), (0.0, 0.165)],
                    segments=6, col=col, material=mats['glow'], smooth_angle=10)
    gem.rotation_euler = (math.radians(90), 0, 0)
    gem.location = (0, 0, HUB)
    apply(parts + [gem])
    return col, parts, mats, [gem]


if __name__ == '__main__':
    import pipeline  # noqa: E402
    col, parts, mats, fx = build()
    allp = parts + fx
    print('tris', geo.tri_count(allp))
    for o in allp:
        h = geo.mesh_health(o)
        if h['non_manifold_edges'] or not h['normals_outward']:
            print('HEALTH', o.name, h)
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'pack', ID, 'blockout')
        os.makedirs(out, exist_ok=True)
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(allp, v, res=(560, 900) if v != 'side' else (300, 900))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    grip_lead = (0.0, 0.0, GRIP_TOP - 0.22)
    res = pipeline.finish(NAME, col, parts, ROOT, grip_lead, glow_parts=fx, glow_spec=SPECS['glow'], tex=1024,
                          attachments={
                              'Grip': grip_lead,
                              'GripSecondary': (0.0, 0.0, GRIP_BOT + 0.22),
                              'VFX_Dial': (0.0, 0.0, HUB),
                              'VFX_MoonRing': (0.0, 0.0, RING_Z),
                              'VFX_Tip': (0.0, 0.0, TIP_Z),
                              'VFX_Tail': (0.0, 0.0, TAIL_RING_Z),
                          })
    print(json.dumps(res['stats'], indent=1))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    rdir = os.path.join(ROOT, 'renders', 'pack', ID)
    pipeline.acceptance_renders(NAME, res['meshes'], res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(res['meshes'], 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
