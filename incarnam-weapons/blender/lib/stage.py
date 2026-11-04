"""Shared scene, lighting, camera and render helpers for the Incarnam Iop weapon set.

Conventions (documented in incarnam-weapons/README.md):
  * Blender units are Roblox studs (1 BU = 1 stud). Export applies the stud->metre
    conversion so Roblox's importer lands at the intended size.
  * Each weapon is built pointing UP along Blender +Z, flat face toward -Y (front),
    cutting edges along +/-X. The origin sits at the primary grip point
    (where the leading hand closes), so equipping needs no per-weapon offsets.
"""
import math
import os

import bpy
from mathutils import Vector

STUD_IN_METRES = 0.28  # Roblox: 1 stud = 0.28 m (Roblox physics/units documentation)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'NONE'
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'  # honest colour for review; Roblox maps are judged in sRGB
    sc.view_settings.look = 'None'
    return sc


def collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if col.name not in par.children:
        par.children.link(col)
    return col


def _light(name, kind, energy, loc, rot, size=None, color=(1, 1, 1), col=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if size is not None and hasattr(data, 'size'):
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = [math.radians(a) for a in rot]
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def set_mood(mood):
    """Swap the lighting rig in place (neutral review <-> showcase)."""
    col = bpy.data.collections.get('_Stage')
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return neutral_stage(mood)


def _studio_env(world, mood):
    """Procedural studio environment: dark floor, soft horizon, brighter ceiling and two softbox bands.
    Metals (metalness 1) need this to show their PBR response; a flat grey world makes them look dead.
    The camera sees the background as a flat grey via the Light Path trick, so review shots stay clean."""
    nt = world.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    els = ramp.color_ramp.elements
    if mood == 'neutral':
        cols = [(0.0, (0.05, 0.05, 0.055, 1)), (0.45, (0.16, 0.16, 0.17, 1)), (0.52, (0.42, 0.42, 0.43, 1)),
                (0.7, (0.30, 0.30, 0.31, 1)), (0.86, (0.95, 0.95, 0.95, 1)), (0.92, (0.35, 0.35, 0.36, 1)),
                (1.0, (0.55, 0.55, 0.56, 1))]
        flat = (0.18, 0.18, 0.19, 1)
    else:
        cols = [(0.0, (0.01, 0.01, 0.012, 1)), (0.45, (0.05, 0.045, 0.05, 1)), (0.52, (0.30, 0.24, 0.20, 1)),
                (0.7, (0.10, 0.10, 0.12, 1)), (0.86, (1.0, 0.92, 0.82, 1)), (0.92, (0.12, 0.12, 0.14, 1)),
                (1.0, (0.25, 0.26, 0.30, 1))]
        flat = (0.018, 0.018, 0.022, 1)
    els[0].position, els[0].color = cols[0]
    els[1].position, els[1].color = cols[-1]
    for pos, c in cols[1:-1]:
        e = els.new(pos)
        e.color = c
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.inputs['Color2'].default_value = flat
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(mix.outputs['Color'], bg.inputs['Color'])


def neutral_stage(mood='neutral'):
    """Neutral review lighting: soft key, fill, rim, mid-grey world.
    mood='showcase' adds a warmer key and darker world for beauty shots,
    but every acceptance view is rendered in 'neutral'."""
    col = collection('_Stage')
    world = bpy.data.worlds.new('StageWorld')
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    _studio_env(world, mood)
    if mood == 'neutral':
        bg.inputs['Strength'].default_value = 0.8
        _light('Key', 'AREA', 900, (-4, -6, 6), (55, 0, -35), size=4, col=col)
        _light('Fill', 'AREA', 300, (6, -4, 2), (75, 0, 55), size=6, col=col)
        _light('Rim', 'AREA', 600, (2, 6, 5), (-55, 0, 160), size=3, col=col)
    else:
        bg.inputs['Strength'].default_value = 0.55
        _light('Key', 'AREA', 1100, (-4, -6, 6), (55, 0, -35), size=3, color=(1, 0.93, 0.85), col=col)
        _light('Fill', 'AREA', 150, (6, -4, 2), (75, 0, 55), size=6, color=(0.8, 0.88, 1), col=col)
        _light('Rim', 'AREA', 900, (2, 6, 5), (-55, 0, 160), size=2, col=col)
    return col


def bounds(objs):
    pts = []
    for o in objs:
        if o.type != 'MESH':
            continue
        deps = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        pts += [deps.matrix_world @ Vector(c) for c in deps.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


VIEWS = {
    'front': (0, -1, 0),
    'rear': (0, 1, 0),
    'side': (1, 0, 0),
    'three_quarter': (0.75, -0.85, 0.35),
    'three_quarter_rear': (-0.75, 0.85, 0.35),
}


def ortho_camera(objs, view, margin=1.12, res=(1024, 1024)):
    """Orthographic camera framing objs from a named view, fitted to the projected extents and image aspect."""
    sc = bpy.context.scene
    lo, hi = bounds(objs)
    centre = (lo + hi) / 2
    cam = sc.camera
    if cam is None:
        cam = bpy.data.objects.new('ReviewCam', bpy.data.cameras.new('ReviewCam'))
        sc.collection.objects.link(cam)
        sc.camera = cam
    cam.data.type = 'ORTHO'
    d = Vector(VIEWS[view]).normalized()
    rot = (-d).to_track_quat('-Z', 'Y')
    right = rot @ Vector((1, 0, 0))
    up = rot @ Vector((0, 1, 0))
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    w = max((c - centre).dot(right) for c in corners) * 2
    h = max((c - centre).dot(up) for c in corners) * 2
    rx, ry = res
    aspect = rx / ry
    scale = max(w, h * aspect) if rx >= ry else max(h, w / aspect)
    cam.data.ortho_scale = scale * margin
    size = max((hi - lo).length, 1e-3)
    cam.location = centre + d * size * 3
    cam.rotation_euler = rot.to_euler()
    cam.data.clip_end = size * 10
    sc.render.resolution_x, sc.render.resolution_y = res
    return cam


def render(path, engine='CYCLES', samples=48, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = engine
    if os.environ.get('SMOKE'):
        samples = 1
        sc.render.resolution_percentage = 20
    if engine == 'CYCLES':
        sc.cycles.samples = samples
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)
    return path


def wireframe_render(path):
    """Workbench render with wireframe overlay on flat shading, to expose topology."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_cavity = True
    mods = []
    for o in sc.objects:
        if o.type == 'MESH' and o.visible_get():
            m = o.modifiers.new('_wire', 'WIREFRAME')
            m.thickness = 0.004
            m.use_replace = False
            mods.append((o, m))
    render(path, engine='BLENDER_WORKBENCH')
    for o, m in mods:
        o.modifiers.remove(m)
    return path


def export_fbx(path, objs):
    """FBX for the Roblox 3D Importer: Y-up, -Z forward, studs -> metres."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.abspath(path), use_selection=True, object_types={'MESH', 'EMPTY', 'ARMATURE'},
        apply_unit_scale=True, global_scale=STUD_IN_METRES, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_tspace=True,
        add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    return path
