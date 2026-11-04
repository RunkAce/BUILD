"""Finishing pipeline shared by every weapon: join -> UV -> bake -> attachments -> save -> export -> renders.

Roblox-facing layout per weapon (see README):
  <Name>_Body   one MeshPart, one 2K SurfaceAppearance (Color/Normal/Roughness/Metalness)
  <Name>_Glow   optional MeshPart for amber energy (gems, heat channels) -> Neon / effects toggle
  <Name>_*      other moving parts (cloth, chain links, second blade) as their own meshes
  Attachments   Empties named like Roblox Attachments, parented to the body:
                Grip (leading hand, = origin), GripSecondary, VFX_*, ClothRoot, ChainA/ChainB ...
"""
import json
import math
import os
import subprocess

import bpy
from mathutils import Vector

import geo
import optimize
import paint
import stage


def apply_all(objs):
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def shift(objs, offset):
    for o in objs:
        o.location = o.location + Vector(offset)
    apply_all([o for o in objs if o.type == 'MESH'])


def attachment(name, loc, col, parent=None, axis_up=(0, 0, 1)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = 0.15
    e.location = loc
    col.objects.link(e)
    if parent is not None:
        e.parent = parent
    return e


def finish(name, col, body_parts, out_root, grip_point, attachments, glow_parts=(), extra_meshes=(),
           tex=2048, bake_samples=16, glow_spec='amber'):
    """Returns dict with objects and stats. grip_point is moved to the origin."""
    off = (-grip_point[0], -grip_point[1], -grip_point[2])
    everything = list(body_parts) + list(glow_parts) + list(extra_meshes)
    shift(everything, off)

    body = paint.join(list(body_parts), f'{name}_Body')
    topo_before = optimize.topology_report(body)
    hidden_removed = optimize.remove_hidden_faces(body, occluders=list(glow_parts) + list(extra_meshes))
    paint.unwrap(body)
    maps_dir = os.path.join(out_root, 'export', name, 'textures')
    maps = paint.bake_maps(body, maps_dir, name, size=tex, samples=bake_samples)
    body.data.materials.clear()
    body.data.materials.append(paint.baked_material(f'{name}_Baked', maps))
    geo.shade_by_angle(body, 30)

    glow = None
    if glow_parts:
        glow = paint.join(list(glow_parts), f'{name}_Glow')
        hidden_removed += optimize.remove_hidden_faces(glow, occluders=[body])
        paint.unwrap(glow)
        glow.data.materials.clear()
        gm = paint.painted(f'{name}_GlowMat', glow_spec, height=1.0)
        glow.data.materials.append(gm)

    att_objs = {}
    for aname, loc in attachments.items():
        p = Vector(loc) + Vector(off)
        att_objs[aname] = attachment(aname, p, col, parent=None)
    for e in att_objs.values():
        e.parent = body

    meshes = [body] + ([glow] if glow else []) + list(extra_meshes)
    stats = {
        'name': name,
        'triangles': {o.name: geo.tri_count([o]) for o in meshes},
        'triangles_total': geo.tri_count(meshes),
        'texture_size': tex,
        'maps': {k: os.path.relpath(v, out_root) for k, v in maps.items()},
        'health': {o.name: geo.mesh_health(o) for o in meshes},
        'topology': {'before_optimise': topo_before, 'hidden_faces_removed': hidden_removed,
                     'after': {o.name: optimize.topology_report(o) for o in meshes}},
        'attachments': {k: [round(c, 4) for c in (Vector(v) + Vector(off))] for k, v in attachments.items()},
        'bounds_studs': None,
    }
    lo, hi = stage.bounds(meshes)
    stats['bounds_studs'] = {'min': [round(c, 3) for c in lo], 'max': [round(c, 3) for c in hi],
                             'length': round(hi.z - lo.z, 3)}

    src = os.path.join(out_root, 'source')
    os.makedirs(src, exist_ok=True)
    exp = os.path.join(out_root, 'export', name)
    os.makedirs(exp, exist_ok=True)
    stage.export_fbx(os.path.join(exp, f'{name}.fbx'), meshes + list(att_objs.values()))
    with open(os.path.join(exp, f'{name}_stats.json'), 'w') as fh:
        json.dump(stats, fh, indent=1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(src, f'{name}.blend')))
    return {'body': body, 'glow': glow, 'meshes': meshes, 'attachments': att_objs, 'stats': stats}


def acceptance_renders(name, meshes, glow, out_dir, samples=48, res=900):
    """Neutral-light front/rear/side/3q/3q-rear, wireframe, and effects off vs on."""
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for v in ('front', 'rear', 'side', 'three_quarter', 'three_quarter_rear'):
        stage.ortho_camera(meshes, v, res=(res, int(res * 1.25)) if v != 'side' else (int(res * 0.5), int(res * 1.25)))
        paths[v] = stage.render(os.path.join(out_dir, f'{name}_{v}.png'), samples=samples)
    stage.ortho_camera(meshes, 'three_quarter', res=(res, int(res * 1.25)))
    paths['wireframe'] = stage.wireframe_render(os.path.join(out_dir, f'{name}_wireframe.png'))
    if glow is not None:
        glow.hide_render = True
        paths['effects_off'] = stage.render(os.path.join(out_dir, f'{name}_effects_off.png'), samples=samples)
        glow.hide_render = False
    return paths


def turntable(name, meshes, out_path, frames=96, res=(720, 900), engine='CYCLES', samples=12, fps=24,
              mood='showcase', tilt=12):
    """Rotate the weapon 360 deg about its long axis under a fixed camera, encode H.264 MP4.
    Cycles + denoise: on a CPU-only box this is far faster than software-GL EEVEE."""
    if os.environ.get('SMOKE'):
        frames = 4
    sc = bpy.context.scene
    sc.cycles.use_denoising = True
    pivot = bpy.data.objects.new(f'{name}_TurntablePivot', None)
    sc.collection.objects.link(pivot)
    roots = [m for m in meshes if m.parent is None]
    for m in roots:
        m.parent = pivot
    lo, hi = stage.bounds(meshes)
    centre = (lo + hi) / 2
    pivot.location = (0, 0, 0)
    cam = sc.camera or bpy.data.objects.new('ReviewCam', bpy.data.cameras.new('ReviewCam'))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'PERSP'
    cam.data.lens = 70
    length = (hi - lo).length
    d = Vector((0, -math.cos(math.radians(tilt)), math.sin(math.radians(tilt))))
    cam.location = centre + d * length * 1.9
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.frame_start, sc.frame_end = 1, frames
    pivot.rotation_mode = 'XYZ'
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert('rotation_euler', frame=1)
    pivot.rotation_euler = (0, 0, math.radians(360))
    pivot.keyframe_insert('rotation_euler', frame=frames + 1)
    _linearize(pivot)
    sc.render.engine = engine
    if engine == 'CYCLES':
        sc.cycles.samples = samples
    else:
        sc.eevee.taa_render_samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = 'PNG'
    frame_dir = out_path + '_frames'
    os.makedirs(frame_dir, exist_ok=True)
    sc.render.filepath = os.path.join(frame_dir, 'f_')
    bpy.ops.render.render(animation=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(frame_dir, 'f_%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out_path], check=True)
    import shutil
    shutil.rmtree(frame_dir, ignore_errors=True)
    for m in roots:
        m.parent = None
    return out_path


def _linearize(obj):
    """Linear interpolation on all keys (Blender 4.4+ layered actions and legacy fcurves)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    curves = []
    if hasattr(act, 'fcurves') and act.fcurves:
        curves = list(act.fcurves)
    else:
        for layer in getattr(act, 'layers', []):
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', []):
                    curves += list(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
