"""OATHSPLITTER - two-handed split greatsword (collection benchmark).

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_oathsplitter.py [--preview]

Invariants (brief section 4): long REAL opening through the blade with inner bevels,
two substantial points, thick rails, substantial bridge below the fork, vermilion
crescent guard with a few large swept points, charcoal two-hand grip, pointed pommel.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))

import bpy  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Oathsplitter'
ROOT = os.path.dirname(HERE)
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
# Proportions measured off 01_Oathsplitter concept: blade ~62% of length, guard span ~33%,
# tips ~21% of length beyond the bridge, grip+pommel ~26%.
GRIP_TOP, GRIP_BOT = -0.02, -1.12
BLADE_BASE = 0.36
SLOT_BOT, SLOT_TOP = 0.64, 2.76
BRIDGE_TOP = 3.08                  # fork crotch; bridge SLOT_TOP..BRIDGE_TOP = 0.32 >= one rail width (QC)
TIP_L, TIP_R = 4.16, 3.92          # staggered twin points, as in the concept
HALF_W = 0.36
SLOT_HW = 0.085
RAIL_C = (HALF_W + SLOT_HW) / 2    # rail centre line x


def scoop(side, z0, depth, length=0.30, barb=0.035):
    """Concave scoop cut into an outer edge ending in an outward barb (side=+1 right, -1 left)."""
    w = HALF_W
    pts = [(w, z0), (w - depth * 0.7, z0 + length * 0.25), (w - depth, z0 + length * 0.55),
           (w - depth * 0.55, z0 + length * 0.85), (w + barb, z0 + length)]
    return [(side * x, z) for (x, z) in pts]


def blade_shape():
    w = HALF_W
    right = ([(0.0, BLADE_BASE - 0.04), (w + 0.07, BLADE_BASE - 0.02), (w + 0.02, BLADE_BASE + 0.22), (w, 1.6)]
             + scoop(1, 2.30, 0.085)
             + [(w - 0.005, 2.75)] + scoop(1, 3.00, 0.06, 0.24, 0.02)
             + [(w - 0.02, 3.30), (RAIL_C + 0.02, TIP_R), (RAIL_C - 0.085, 3.30), (0.05, BRIDGE_TOP)])
    left_up = ([(-w, 1.6), (-w + 0.0, 2.45)] + [(x, z) for (x, z) in scoop(-1, 2.50, 0.085)]
               + [(-w + 0.005, 2.95)] + scoop(-1, 3.20, 0.06, 0.24, 0.02)
               + [(-w + 0.02, 3.52), (-RAIL_C - 0.02, TIP_L), (-RAIL_C + 0.085, 3.52), (-0.05, BRIDGE_TOP)])
    left = list(reversed(left_up)) + [(-w - 0.02, BLADE_BASE + 0.22), (-w - 0.07, BLADE_BASE - 0.02)]
    outline = right + left
    bottom = geo.arc(0, SLOT_BOT + SLOT_HW, SLOT_HW, 0, -180, 10)
    slot = [(SLOT_HW + 0.006, SLOT_TOP - 0.10), (0.0, SLOT_TOP), (-SLOT_HW - 0.006, SLOT_TOP - 0.10)] + \
           [(x, z) for (x, z) in reversed(bottom)]
    slot = [(-SLOT_HW - 0.006, SLOT_TOP - 0.10)] + [(-SLOT_HW, SLOT_BOT + SLOT_HW)] + \
           geo.arc(0, SLOT_BOT + SLOT_HW, SLOT_HW, 180, 360, 10)[1:-1] + \
           [(SLOT_HW, SLOT_BOT + SLOT_HW), (SLOT_HW + 0.006, SLOT_TOP - 0.10), (0.0, SLOT_TOP)]
    return Polygon(geo.orient(outline), [geo.orient(slot, False)]), slot


def guard_shape():
    # thick crescent opening toward the blade; two large swept horns rising well above the blade root,
    # a raised centre boss the blade seats into, and two lower claws
    outer_r = geo.bezier((0.0, -0.14), (0.62, -0.14), (0.98, 0.20), (1.04, 0.98), 16)
    inner_r = geo.bezier((1.04, 0.98), (0.84, 0.56), (0.62, 0.36), (0.30, 0.34), 16)
    right = outer_r + inner_r[1:] + [(0.0, 0.40)]
    left = [(-x, z) for (x, z) in reversed(right)]
    body = Polygon(geo.orient(right[:-1] + left[1:]))
    claws = []
    for s in (1, -1):
        claws.append(Polygon(geo.orient([(s * 0.26, -0.08), (s * 0.50, -0.34), (s * 0.46, -0.04)])))
    return unary_union([body] + claws).buffer(0.004).buffer(-0.004)


def horn_inlay(sign):
    a = geo.bezier((0.30, -0.02), (0.66, 0.0), (0.86, 0.26), (0.94, 0.80), 14)
    b = geo.bezier((0.90, 0.70), (0.80, 0.34), (0.62, 0.12), (0.32, 0.07), 14)
    return Polygon(geo.orient([(sign * x, z) for (x, z) in a + b]))


def root_inlay(slot):
    # bold gold frame: U band around the slot bottom flaring into pointed wings at the blade corners
    # and two spikes running up the slot sides (concept: gold 4-point frame at the blade root)
    slot_poly = Polygon(geo.orient(slot, False))
    ring = slot_poly.buffer(0.10, join_style='mitre').difference(slot_poly.buffer(0.035, join_style='mitre'))
    ring = ring.intersection(box(-1, BLADE_BASE, 1, 1.05))
    parts = [ring]
    for s in (1, -1):
        parts.append(Polygon(geo.orient([(s * 0.12, 0.86), (s * 0.34, BLADE_BASE + 0.02), (s * 0.27, BLADE_BASE + 0.02),
                                         (s * 0.13, 0.62)])))
        parts.append(Polygon(geo.orient([(s * 0.115, 0.98), (s * 0.16, 1.36), (s * 0.085, 1.08), (s * 0.085, 0.98)])))
    return unary_union(parts)


def slot_heat(slot):
    """Amber heat sliver lining the lower inner wall of the slot (separate mesh: effects on/off)."""
    slot_poly = Polygon(geo.orient(slot, False))
    band = slot_poly.buffer(0.0).difference(slot_poly.buffer(-0.022, join_style='mitre'))
    return band.intersection(box(-1, 0, 1, 1.25))


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    H = TIP_L - (-1.6)
    mats = {k: paint.painted(f'{NAME}_{k}', k, height=H, seed=i * 3.1)
            for i, k in enumerate(['ivory', 'vermilion', 'gold', 'charcoal', 'amber', 'deepred'])}

    parts = []
    shape, slot = blade_shape()
    parts.append(geo.slab('Blade', shape=shape, core_t=0.19, edge_t=0.03, bevel_w=0.075,
                          levels=[(0.0, 0.016), (0.03, 0.062), (0.075, 0.095)],
                          col=col, material=mats['ivory']))
    parts.append(geo.slab('RootInlay', shape=root_inlay(slot), core_t=0.215, edge_t=0.19, bevel_w=0.012,
                          col=col, material=mats['gold']))
    # guard: thick vermilion crescent with gold horn inlays, gold diamond setting, amber gem
    parts.append(geo.slab('Guard', shape=guard_shape(), core_t=0.32, edge_t=0.05, bevel_w=0.07,
                          levels=[(0.0, 0.025), (0.035, 0.115), (0.075, 0.16)],
                          col=col, material=mats['vermilion']))
    guard_core = guard_shape().buffer(-0.045, join_style='mitre')
    boss = Polygon(geo.orient([(0, -0.16), (0.30, 0.02), (0.24, 0.30), (0, 0.40), (-0.24, 0.30), (-0.30, 0.02)]))
    parts.append(geo.slab('GuardBoss', shape=boss, core_t=0.36, edge_t=0.26, bevel_w=0.045,
                          col=col, material=mats['vermilion']))
    for s in (1, -1):
        parts.append(geo.slab(f'HornInlay{"R" if s > 0 else "L"}', shape=horn_inlay(s).intersection(guard_core), core_t=0.345, edge_t=0.32,
                              bevel_w=0.01, col=col, material=mats['gold']))
    diamond = Polygon(geo.orient([(0, -0.10), (0.19, 0.12), (0, 0.36), (-0.19, 0.12)]))
    parts.append(geo.slab('GemSetting', shape=diamond, core_t=0.38, edge_t=0.25, bevel_w=0.04,
                          col=col, material=mats['gold']))
    # amber gem: faceted, protruding from BOTH faces of the setting
    gem = geo.lathe('Gem', [(0.0, -0.25), (0.06, -0.20), (0.115, 0.0), (0.06, 0.20), (0.0, 0.25)], segments=4,
                    rot_offset=0, col=col, material=mats['amber'], smooth_angle=10)
    gem.rotation_euler = (1.5708, 0, 0)
    gem.scale = (1.0, 1.35, 1.0)
    gem.location = (0, 0, 0.13)
    parts.append(gem)
    heat = geo.slab('SlotHeat', shape=slot_heat(slot), core_t=0.12, edge_t=0.11, bevel_w=0.005,
                    col=col, material=mats['amber'])
    # collars, grip, pommel
    parts.append(geo.lathe('UpperCollar', [(0.0, -0.10), (0.115, -0.10), (0.125, -0.07), (0.125, 0.02),
                                           (0.10, 0.05), (0.0, 0.05)], segments=10, col=col, material=mats['vermilion']))
    parts.append(geo.lathe('UpperBand', [(0.0, -0.06), (0.131, -0.06), (0.131, -0.02), (0.0, -0.02)],
                           segments=10, col=col, material=mats['gold']))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP - 0.08, 0.085, wraps=7, col=col,
                                  material=mats['charcoal'], style='strap'))
    parts.append(geo.lathe('LowerCollar', [(0.0, GRIP_BOT - 0.10), (0.11, GRIP_BOT - 0.10), (0.122, GRIP_BOT - 0.07),
                                           (0.122, GRIP_BOT + 0.01), (0.10, GRIP_BOT + 0.03), (0.0, GRIP_BOT + 0.03)],
                           segments=10, col=col, material=mats['vermilion']))
    pz = GRIP_BOT - 0.10
    parts.append(geo.lathe('Pommel', [(0.0, pz), (0.15, pz - 0.02), (0.20, pz - 0.12), (0.19, pz - 0.22),
                                      (0.0, pz - 0.52)], segments=4, rot_offset=0.7854,
                           col=col, material=mats['vermilion'], smooth_angle=20))
    parts.append(geo.lathe('PommelBand', [(0.0, pz - 0.05), (0.212, pz - 0.07), (0.212, pz - 0.15), (0.0, pz - 0.17)],
                           segments=4, rot_offset=0.7854, col=col, material=mats['gold'], smooth_angle=20))

    # apply transforms of rotated/scaled parts so joins are clean
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return col, parts, mats, [heat]


if __name__ == '__main__':
    import pipeline  # noqa: E402
    col, parts, mats, fx = build()
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'oathsplitter', 'blockout')
        os.makedirs(out, exist_ok=True)
        allp = parts + fx
        print('tris', geo.tri_count(allp))
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(allp, v, res=(700, 900) if v != 'side' else (400, 900))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    gem = next(p for p in parts if p.name == 'Gem')
    body_parts = [p for p in parts if p is not gem]
    grip_lead = (0.0, 0.0, GRIP_TOP - 0.22)           # leading hand just under the upper collar
    res = pipeline.finish(NAME, col, body_parts, ROOT, grip_lead, glow_parts=[gem] + fx, tex=2048, attachments={
        'Grip': grip_lead,
        'GripSecondary': (0.0, 0.0, GRIP_BOT + 0.22),   # trailing hand above the lower collar
        'VFX_SlotBase': (0.0, 0.0, SLOT_BOT + 0.1),
        'VFX_Bridge': (0.0, 0.0, (SLOT_TOP + BRIDGE_TOP) / 2),
        'VFX_TipL': (-RAIL_C - 0.02, 0.0, TIP_L),
        'VFX_TipR': (RAIL_C + 0.02, 0.0, TIP_R),
        'VFX_Gem': (0.0, 0.0, 0.13),
    })
    print(json.dumps(res['stats'], indent=1))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    rdir = os.path.join(ROOT, 'renders', 'oathsplitter')
    pipeline.acceptance_renders(NAME, res['meshes'], res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(res['meshes'], 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
    if '--no-turntable' not in sys.argv:
        pipeline.turntable(NAME, res['meshes'], os.path.join(rdir, f'{NAME}_turntable.mp4'))
