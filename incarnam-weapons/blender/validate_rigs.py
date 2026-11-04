"""Validate the skinned cloth rigs (Sunbound streamer, Flarecrest ribbon, Warlink chain).

Run: EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python validate_rigs.py
Checks on the SOURCE rig and on the RE-IMPORTED exported FBX (what Roblox receives):
  * every vertex weighted, weights normalised (sum = 1), <= 4 influences per vertex (Roblox limit)
  * bones form one connected hierarchy under a single root
  * deformation: rotating the free-end bones moves the tail but leaves the pinned root region still
Writes export/rig_validation.json and exits non-zero on failure.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = os.path.dirname(HERE)
RIGS = [
    # name, fbx, pinned bone (must not move), bones to bend for the deformation test
    ('Sunbound streamer', 'export/Sunbound/Sunbound_Streamer.fbx', 'ClothRoot', ['Cloth3', 'Cloth4', 'Cloth5']),
    ('Flarecrest ribbon', 'export/Flarecrest/Flarecrest_Ribbon.fbx', 'RibbonRoot', ['Ribbon4', 'Ribbon6', 'Ribbon8']),
]


def evaluated_coords(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = [obj.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return co


def check(label, fbx, pinned, bend):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = os.path.join(ROOT, fbx)
    if not os.path.exists(path):
        return {'rig': label, 'ok': False, 'error': f'missing {fbx}'}
    bpy.ops.import_scene.fbx(filepath=path)
    arm = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
    mesh = next((o for o in bpy.context.scene.objects if o.type == 'MESH'), None)
    res = {'rig': label, 'fbx': fbx}
    if not (arm and mesh):
        res.update(ok=False, error='armature or mesh missing after FBX re-import')
        return res
    mod = next((m for m in mesh.modifiers if m.type == 'ARMATURE'), None)
    bones = [b.name for b in arm.data.bones]
    roots = [b.name for b in arm.data.bones if b.parent is None]
    groups = {g.index: g.name for g in mesh.vertex_groups}
    unweighted, over4, bad_sum, unknown = 0, 0, 0, set()
    for v in mesh.data.vertices:
        ws = [(groups[g.group], g.weight) for g in v.groups if g.weight > 1e-4]
        if not ws:
            unweighted += 1
            continue
        if len(ws) > 4:
            over4 += 1
        if abs(sum(w for _, w in ws) - 1.0) > 0.02:
            bad_sum += 1
        for n, _ in ws:
            if n not in bones:
                unknown.add(n)
    res.update(bones=len(bones), bone_names=bones, roots=roots, vertices=len(mesh.data.vertices),
               has_armature_modifier=bool(mod and mod.object == arm), unweighted_vertices=unweighted,
               over_4_influences=over4, unnormalised=bad_sum, groups_without_bone=sorted(unknown))

    # deformation test in pose mode
    rest = evaluated_coords(mesh)
    pinned_idx = []
    if pinned and pinned in mesh.vertex_groups:
        gi = mesh.vertex_groups[pinned].index
        pinned_idx = [v.index for v in mesh.data.vertices
                      if any(g.group == gi and g.weight > 0.999 for g in v.groups)]
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for bn in bend:
        pb = arm.pose.bones.get(bn)
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (math.radians(35), 0, math.radians(20))
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    posed = evaluated_coords(mesh)
    moved = [(posed[i] - rest[i]).length for i in range(len(rest))]
    pin_move = max((moved[i] for i in pinned_idx), default=0.0)
    res.update(pinned_vertices=len(pinned_idx), pinned_max_move=round(pin_move, 6),
               tail_max_move=round(max(moved), 4))
    res['ok'] = (res['has_armature_modifier'] and unweighted == 0 and over4 == 0 and bad_sum == 0
                 and not unknown and len(roots) == 1 and pin_move < 1e-4 and max(moved) > 0.02)
    return res


results = [check(*r) for r in RIGS]
out = os.path.join(ROOT, 'export', 'rig_validation.json')
with open(out, 'w') as fh:
    json.dump(results, fh, indent=1)
for r in results:
    print(('PASS ' if r.get('ok') else 'FAIL ') + json.dumps({k: v for k, v in r.items() if k != 'bone_names'}))
sys.exit(0 if all(r.get('ok') for r in results) else 1)
