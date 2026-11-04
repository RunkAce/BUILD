"""NIGHTLATCH - original Sram-inspired assassin's dagger (Wakfu pack).

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python pack/build_nightlatch.py [--preview] [--no-renders]

Design: a hooked, talon-curved single-edge dagger. A real KEYHOLE opening punched through the blade root
(the thief / trap-setter read) is lined with a thin violet glow (the single emissive accent). Midnight-indigo
enamel guard with two rib-like quillons swept back toward the hand, bone collar seated over the blade root,
a back-spine "latch tooth" for the rear strike, plum leather grip and a faceted bone knuckle pommel.
Colour story: cold pale steel + midnight indigo + bone, one violet glow.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))
ROOT = os.path.dirname(os.path.dirname(HERE))

import bpy  # noqa: E402
from shapely.affinity import translate
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Nightlatch'
ID = 'nightlatch'
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
GRIP_TOP, GRIP_BOT = -0.06, -0.66
BLADE_BASE = 0.10
TIP = (-0.16, 1.62)
KEY_C = (0.0, 0.50)        # keyhole round centre
KEY_R = 0.062

SPECS = {
    'steel': dict(base='#AEB2C0', light='#ECEEF5', dark='#454658', rough=0.34, metal=1.0, relief='hammered', paint_light=0.5),
    'indigo': dict(base='#3B2F6E', light='#6E5DB0', dark='#160F2E', rough=0.38, metal=0.0, relief='hammered', chip=0.45),
    'bone': dict(base='#D6CBAE', light='#F5EEDA', dark='#7A6E58', rough=0.62, metal=0.0, relief='none'),
    'leather': dict(base='#3A2738', light='#6A4A63', dark='#170F17', rough=0.78, metal=0.0, relief='leather'),
    'blued': dict(base='#3E4060', light='#7C80A8', dark='#15162A', rough=0.30, metal=1.0, relief='hammered', paint_light=0.5),
    'silver': dict(base='#9C9AA6', light='#E2E0EA', dark='#3E3C48', rough=0.30, metal=1.0, relief='hammered', paint_light=0.5),
    'glow': dict(base='#A86BFF', light='#E0C6FF', dark='#5A22B0', rough=0.15, metal=0.0, relief='none', emit=2.2),
}


def keyhole():
    c = Point(KEY_C).buffer(KEY_R, 24)
    stem = Polygon(geo.orient([(-0.028, KEY_C[1] - 0.02), (0.028, KEY_C[1] - 0.02), (0.05, 0.33), (-0.05, 0.33)]))
    return unary_union([c, stem]).buffer(0.004).buffer(-0.004)


def blade_shape():
    # cutting edge (+x) bellies out then sweeps hard into a hooked tip that leans to the spine side
    edge = geo.bezier((0.17, BLADE_BASE), (0.25, 0.62), (0.22, 1.12), TIP, 16)
    # spine (-x): straight, then a latch tooth (notch + hook), then a concave clip up to the tip
    spine = [TIP, (-0.15, 1.42), (-0.115, 1.24), (-0.13, 1.17), (-0.26, 1.21), (-0.17, 1.02), (-0.15, 0.62),
             (-0.165, BLADE_BASE)]
    outline = edge + spine[1:]
    return Polygon(geo.orient(outline), [geo.orient(list(keyhole().exterior.coords)[:-1], False)]).buffer(0)


def guard_shape():
    # rib-like quillons swept DOWN toward the hand; a pointed centre plate the blade seats into
    parts = []
    for s in (1, -1):
        top = geo.bezier((s * 0.14, 0.16), (s * 0.34, 0.15), (s * 0.48, 0.06), (s * 0.54, -0.18), 10)
        bot = geo.bezier((s * 0.54, -0.18), (s * 0.40, -0.06), (s * 0.28, -0.02), (s * 0.12, -0.04), 10)
        parts.append(Polygon(geo.orient(top + bot[1:])).buffer(0))
    plate = Polygon(geo.orient([(0, -0.14), (0.20, -0.04), (0.21, 0.16), (0.0, 0.26), (-0.21, 0.16), (-0.20, -0.04)]))
    return unary_union(parts + [plate]).buffer(0.006).buffer(-0.006)


def rib_inlay(s):
    a = geo.bezier((s * 0.22, 0.10), (s * 0.36, 0.09), (s * 0.44, 0.03), (s * 0.49, -0.11), 10)
    b = geo.bezier((s * 0.47, -0.08), (s * 0.40, 0.0), (s * 0.32, 0.05), (s * 0.22, 0.06), 10)
    return Polygon(geo.orient(a + b)).buffer(0)


def collar_shape():
    # bone collar wrapping the blade root, top edge a shallow V that points up the blade
    return Polygon(geo.orient([(-0.20, 0.08), (0.20, 0.08), (0.21, 0.20), (0.0, 0.29), (-0.21, 0.20)]))


def spine_band():
    # blued-steel band following the spine from the collar up to the latch tooth (two-tone blade read)
    b = blade_shape()
    inner = b.buffer(-0.022, join_style='mitre')
    band = inner.difference(translate(b, xoff=0.10))
    return band.intersection(box(-1, 0.30, -0.02, 1.13)).difference(escutcheon().buffer(0.02)).buffer(0)


def escutcheon():
    # lock plate around the keyhole: rounded top, pointed foot, seated on the blade face
    top = Point(KEY_C).buffer(KEY_R + 0.05, 24)
    foot = Polygon(geo.orient([(-0.10, KEY_C[1] - 0.02), (0.10, KEY_C[1] - 0.02), (0.085, 0.28), (0.0, 0.235), (-0.085, 0.28)]))
    return unary_union([top, foot]).buffer(0.01).buffer(-0.01).difference(keyhole())


def key_glow():
    k = keyhole()
    return k.difference(k.buffer(-0.016, join_style='mitre'))


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
    H = TIP[1] - (GRIP_BOT - 0.3)
    mats = {k: paint.painted(f'{NAME}_{k}', v, height=H, seed=i * 1.7) for i, (k, v) in enumerate(SPECS.items())}
    parts = []
    parts.append(geo.slab('Blade', shape=blade_shape(), levels=[(0.0, 0.010), (0.035, 0.034), (0.07, 0.048)],
                          col=col, material=mats['steel']))
    # collar sits OVER the blade root with the keyhole cut through it too (keyhole stays a real opening)
    col_shape = collar_shape().difference(keyhole().buffer(0.025))
    parts.append(geo.slab('Collar', shape=col_shape, levels=[(0.0, 0.05), (0.02, 0.075), (0.035, 0.082)],
                          col=col, material=mats['bone']))
    parts.append(geo.slab('SpineBand', shape=spine_band(), levels=[(0.0, 0.046), (0.012, 0.054)],
                          col=col, material=mats['blued']))
    parts.append(geo.slab('Escutcheon', shape=escutcheon(), levels=[(0.0, 0.05), (0.018, 0.068), (0.03, 0.072)],
                          col=col, material=mats['indigo']))
    parts.append(geo.slab('Guard', shape=guard_shape(), levels=[(0.0, 0.03), (0.03, 0.095), (0.06, 0.115)],
                          col=col, material=mats['indigo']))
    core = guard_shape().buffer(-0.035, join_style='mitre')
    for s in (1, -1):
        parts.append(geo.slab(f'Rib{"R" if s > 0 else "L"}', shape=rib_inlay(s).intersection(core),
                              levels=[(0.0, 0.112), (0.01, 0.122)], col=col, material=mats['bone']))
    # silver cabochon setting on the guard plate (no glow; the glow lives in the keyhole)
    stud = geo.lathe('GuardStud', [(0.0, -0.14), (0.05, -0.135), (0.065, -0.10), (0.065, 0.10), (0.05, 0.135), (0.0, 0.14)],
                     segments=6, col=col, material=mats['silver'], smooth_angle=10)
    stud.rotation_euler = (math.radians(90), 0, 0)
    stud.location = (0, 0, 0.02)
    parts.append(stud)
    # collars, grip, pommel
    parts.append(geo.lathe('UpperCollar', [(0.0, GRIP_TOP - 0.03), (0.10, GRIP_TOP - 0.03), (0.112, GRIP_TOP),
                                           (0.112, GRIP_TOP + 0.06), (0.0, GRIP_TOP + 0.08)], segments=6,
                           col=col, material=mats['indigo'], smooth_angle=20))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, 0.078, wraps=5, col=col, material=mats['leather'],
                                  style='strap'))
    parts.append(geo.lathe('LowerRing', [(0.0, GRIP_BOT - 0.04), (0.108, GRIP_BOT - 0.04), (0.108, GRIP_BOT + 0.01),
                                         (0.0, GRIP_BOT + 0.01)], segments=6, col=col, material=mats['silver']))
    pz = GRIP_BOT - 0.04
    parts.append(geo.lathe('Pommel', [(0.0, pz + 0.005), (0.10, pz), (0.155, pz - 0.07), (0.14, pz - 0.16),
                                      (0.07, pz - 0.23), (0.0, pz - 0.25)], segments=5, rot_offset=math.pi / 2,
                           col=col, material=mats['bone'], smooth_angle=20))
    parts.append(geo.lathe('PommelBand', [(0.0, pz - 0.05), (0.158, pz - 0.06), (0.158, pz - 0.10), (0.0, pz - 0.11)],
                           segments=5, rot_offset=math.pi / 2, col=col, material=mats['indigo'], smooth_angle=20))
    glow = geo.slab('KeyGlow', shape=key_glow(), levels=[(0.0, 0.030), (0.006, 0.034)], col=col, material=mats['glow'])
    apply(parts + [glow])
    return col, parts, mats, [glow]


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
            stage.ortho_camera(allp, v, res=(560, 720) if v != 'side' else (320, 720))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    grip_lead = (0.0, 0.0, (GRIP_TOP + GRIP_BOT) / 2 + 0.05)
    res = pipeline.finish(NAME, col, parts, ROOT, grip_lead, glow_parts=fx, glow_spec=SPECS['glow'], tex=1024,
                          attachments={
                              'Grip': grip_lead,
                              'VFX_Keyhole': (KEY_C[0], 0.0, KEY_C[1]),
                              'VFX_Tip': (TIP[0], 0.0, TIP[1]),
                              'VFX_LatchTooth': (-0.26, 0.0, 1.21),
                              'VFX_Pommel': (0.0, 0.0, GRIP_BOT - 0.29),
                          })
    print(json.dumps(res['stats'], indent=1))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    rdir = os.path.join(ROOT, 'renders', 'pack', ID)
    pipeline.acceptance_renders(NAME, res['meshes'], res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(res['meshes'], 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
