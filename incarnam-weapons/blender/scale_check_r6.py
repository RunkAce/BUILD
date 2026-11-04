"""R6 scale check: every weapon next to and held by an exact-size R6 proxy.

Run: EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python scale_check_r6.py
Writes renders/r6_scale/lineup.png, held.png and r6_measurements.json.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'lib'))
sys.argv = [sys.argv[0], '--preview']

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import geo  # noqa: E402
import r6  # noqa: E402
import stage  # noqa: E402

import build_oathsplitter as OS  # noqa: E402
import build_sunbound as SB  # noqa: E402
import build_warlink as WL  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'renders', 'r6_scale')
os.makedirs(OUT, exist_ok=True)


def group(name, objs, matrix):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    for o in objs:
        o.parent = e
    e.matrix_world = matrix
    return e


def dup(objs):
    out = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy() if o.data else None
        bpy.context.scene.collection.objects.link(c)
        out.append(c)
    return out


stage.reset_scene()
stage.neutral_stage()
col = stage.collection('R6Check')

os_col, os_parts, _, os_fx = OS.build(fresh=False)
os_parts += os_fx
sb_col, sb_parts, _, sb_ring = SB.build(fresh=False)
wl_col, wl_mats, wl_r, wl_l, wl_chain = WL.build(fresh=False)

grips = {
    'Oathsplitter': Vector((0, 0, OS.GRIP_TOP - 0.22)),
    'Sunbound': Vector((0, 0, SB.GRIP_TOP - 0.22)),
    'Warlink': Vector((0, 0, WL.GRIP_TOP - 0.18)),
}
meas = {}
for nm, parts in (('Oathsplitter', os_parts), ('Sunbound', sb_parts), ('Warlink_cleaver', wl_r)):
    lo, hi = stage.bounds(parts)
    meas[nm] = {'length_studs': round(hi.z - lo.z, 2), 'width_studs': round(hi.x - lo.x, 2)}

# ---------------------------------------------------------------- lineup: upright next to an R6 (front view)
r6.build(col, x_offset=0.0)
x = 2.6
lineup = []
for nm, parts in (('Oathsplitter', os_parts), ('Sunbound', sb_parts)):
    lo, hi = stage.bounds(parts)
    group(f'Line_{nm}', parts, Matrix.Translation((x - (lo.x + hi.x) / 2, 0, -lo.z)))
    lineup += parts
    x += (hi.x - lo.x) + 0.7
lo, hi = stage.bounds(wl_r)
group('Line_WarlinkR', wl_r, Matrix.Translation((x + 0.5, 0, -lo.z)))
group('Line_WarlinkL', wl_l, Matrix.Translation((x + 1.7, 0, -lo.z)))
for c in wl_chain:
    c.hide_render = True
bpy.context.view_layer.update()
allvis = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
stage.ortho_camera(allvis, 'front', res=(1800, 900), margin=1.05)
# ground line
bpy.ops.mesh.primitive_plane_add(size=60, location=(4, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new('floor')
fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.09, 0.1, 1)
floor.data.materials.append(fm)
stage.render(os.path.join(OUT, 'lineup.png'), samples=24)

# ---------------------------------------------------------------- held: default R6 tool grip (blade forward)
for o in list(bpy.context.scene.objects):
    if o.name.startswith(('R6_', 'Line_')) or o.type == 'MESH':
        if o is not floor:
            o.hide_render = True
held = []
spacing = 5.5
for i, (nm, parts) in enumerate((('Oathsplitter', os_parts), ('Sunbound', sb_parts))):
    pr, hands = r6.build(col, x_offset=i * spacing, arm_pitch_r=35, arm_pitch_l=0)
    cp = dup(parts)
    for o in cp:
        o.hide_render = False
    group(f'Held_{nm}', cp, hands['Right'] @ Matrix.Translation(-grips[nm]))
    held += cp + list(pr.values())
# Warlink: one cleaver in each hand, arms raised forward, chain between the eyelets
pr, hands = r6.build(col, x_offset=2 * spacing, arm_pitch_r=55, arm_pitch_l=55)
cr, cl = dup(wl_r), dup(wl_l)
for o in cr + cl:
    o.hide_render = False
group('Held_WarlinkR', cr, hands['Right'] @ Matrix.Translation(-grips['Warlink']))
group('Held_WarlinkL', cl, hands['Left'] @ Matrix.Translation(-grips['Warlink']))
bpy.context.view_layer.update()
eyeR = WL.eyelet_world(cr)
eyeL = WL.eyelet_world(cl)
meas['R6'] = {
    'grip_gap_hands_hanging': 3.0,
    'warlink_eyelet_gap_this_pose': round((eyeR - eyeL).length, 2),
    'oathsplitter_grip_diameter': 0.17, 'r6_hand_width': 1.0,
}
held += cr + cl + list(pr.values())
for o in held:
    o.hide_render = False
bpy.context.view_layer.update()
stage.ortho_camera(held, 'three_quarter', res=(1800, 1000), margin=1.05)
stage.render(os.path.join(OUT, 'held.png'), samples=24)
with open(os.path.join(OUT, 'r6_measurements.json'), 'w') as fh:
    json.dump(meas, fh, indent=1)
print(json.dumps(meas, indent=1))
