"""PIXELGATE gun kit: hard-surface helpers on top of the Incarnam pipeline (geo/paint/pipeline/stage).

Authoring convention (side view): X = along the barrel, MUZZLE TOWARD +X, Z = up, Y = gun width (left/right).
finish_orientation() rotates the finished gun so the muzzle points Blender -Y, which the FBX export maps to
Roblox -Z (LookVector / forward) with Roblox +Y up. Origin = Root = right-hand grip point.
"""
import math
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'incarnam-weapons', 'blender', 'lib')
sys.path.insert(0, os.path.abspath(LIB))

import bmesh  # noqa: E402  (bpy must be imported by the caller first)
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402

# Factory palette: PBR (metals metal=1, polymer/wood 0). 'mask' = camo/skin mask channel for future cosmetics.
FACTORY = {
    'anodized':  dict(base='#3B3F46', light='#79808B', dark='#16181B', rough=0.42, metal=1.0, relief='hammered', paint_light=0.45),
    'polymer':   dict(base='#4B4F56', light='#7C818A', dark='#1E2023', rough=0.62, metal=0.0, relief='leather', paint_light=0.6),
    'steel':     dict(base='#8C9097', light='#D3D6DB', dark='#3E4146', rough=0.32, metal=1.0, relief='hammered', paint_light=0.45),
    'blacksteel': dict(base='#2C2E32', light='#6A6E75', dark='#101113', rough=0.38, metal=1.0, relief='hammered', paint_light=0.45),
    'tan':       dict(base='#9C8A68', light='#C8B892', dark='#5A4C34', rough=0.6, metal=0.0, relief='leather', paint_light=0.6),
    'olive':     dict(base='#5D6247', light='#8A8F6C', dark='#2E3122', rough=0.6, metal=0.0, relief='leather', paint_light=0.6),
    'walnut':    dict(base='#6B4128', light='#A06C47', dark='#331C10', rough=0.55, metal=0.0, relief='weave', paint_light=0.6),
    'brass':     dict(base='#B48A3E', light='#E8C77E', dark='#5E4416', rough=0.3, metal=1.0, relief='none', paint_light=0.4),
}
# mask colours (R,G,B) per material role, baked to <ID>_Factory_MaskMap.png:
# R = Body, G = Furniture, B = MetalAccent, (R+G) yellow = Magazine. Wear/Emissive_FutureSkinOnly left black.
MASK = {'Body': (1, 0, 0), 'Furniture': (0, 1, 0), 'MetalAccent': (0, 0, 1), 'Magazine': (1, 1, 0)}


def mats(prefix, roles):
    """roles: {role_name: (factory_key, mask_slot)} -> {role_name: material}; stores mask slot on material."""
    out = {}
    for i, (role, (key, slot)) in enumerate(roles.items()):
        m = paint.painted(f'{prefix}_{role}', FACTORY[key], height=3.0, seed=i * 1.9, streak=0.35, bevel_radius=0.005, ao_dist=0.025, flat_light=True)
        m['mask_slot'] = slot
        out[role] = m
    return out


def P(pts):
    return Polygon(geo.orient(pts)).buffer(0)


def rbox(x0, z0, x1, z1, r=0.0):
    b = box(x0, z0, x1, z1)
    return b.buffer(-r).buffer(r, 6) if r > 0 else b


def side(name, shape, width, col, mat, chamfer=0.012, y=0.0):
    """Side-profile part: extrude a 2D (x,z) shape across the gun width with a crisp two-step chamfer."""
    c = min(chamfer, width * 0.3)
    o = geo.slab(name, shape=shape, core_t=width, edge_t=width - 2 * c, bevel_w=c,
                 levels=[(0.0, width / 2 - c), (c * 0.5, width / 2 - c * 0.3), (c, width / 2)],
                 col=col, material=mat, y_offset=y, smooth_angle=12)
    # machined side parts are all planar facets: flat shading is exact and can't bleed across triangles
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def top(name, shape, height, col, mat, z=0.0, chamfer=0.01):
    """Top-view part: 2D shape in (x, y) extruded along Z (e.g. rails seen from above)."""
    o = side(name, shape, height, col, mat, chamfer)
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (0, 0, z)
    return o


def tube(name, profile, col, mat, y=0.0, z=0.0, segments=12, smooth=40):
    """Round part along X: profile [(radius, x), ...]."""
    o = geo.lathe(name, [(r, x) for r, x in profile], segments=segments, col=col, material=mat, smooth_angle=smooth)
    o.rotation_euler = (0, math.radians(90), 0)   # lathe Z axis -> +X
    bpy.context.view_layer.update()
    # lathe along Z then rotated: z' -> x, so place
    o.location = (0, y, z)
    return o


def apply(objs):
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objs


def teeth_along_x(x0, x1, pitch, w, h, z):
    """Picatinny-like rail teeth as one 2D side shape (repeated small blocks)."""
    parts = []
    x = x0
    while x + w <= x1:
        parts.append(box(x, z, x + w, z + h))
        x += pitch
    return unary_union(parts)


# ------------------------------------------------------------------ rig: one skinned mesh, rigid bone per part
def rig(name, col, parts_by_bone, bone_heads, root='Root'):
    """parts_by_bone: {bone: [objects]}; bone_heads: {bone: ((x,y,z) head, (x,y,z) tail, parent)}.
    Joins everything into ONE mesh, each vertex rigidly weighted (1.0) to its part's bone.
    Returns (mesh_obj, armature_obj)."""
    arm_data = bpy.data.armatures.new(f'{name}_Rig')
    arm = bpy.data.objects.new(f'{name}_Rig', arm_data)
    col.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = {}
    for b, (h, t, parent) in bone_heads.items():
        eb = arm_data.edit_bones.new(b)
        eb.head, eb.tail = h, t
        ebs[b] = eb
    for b, (h, t, parent) in bone_heads.items():
        if parent:
            ebs[b].parent = ebs[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    objs = []
    for b, plist in parts_by_bone.items():
        for o in plist:
            vg = o.vertex_groups.new(name=b)
            vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
            objs.append(o)
    mesh = paint.join(objs, f'{name}_Mesh')
    mod = mesh.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm
    mesh.parent = arm
    return mesh, arm


def key(arm, bone, frame, loc=None, rot=None):
    pb = arm.pose.bones[bone]
    pb.rotation_mode = 'XYZ'
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert('location', frame=frame)
    if rot is not None:
        pb.rotation_euler = [math.radians(a) for a in rot]
        pb.keyframe_insert('rotation_euler', frame=frame)


def new_action(arm, name):
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    return act


def bake_mask(obj, out_path, size=1024):
    """Bake the camo/skin mask: each material emits its MASK slot colour."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    img = bpy.data.images.new(os.path.basename(out_path), size, size, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    saved = []
    for slot in obj.material_slots:
        m = slot.material
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        prev = out.inputs['Surface'].links[0].from_socket if out.inputs['Surface'].links else None
        em = nt.nodes.new('ShaderNodeEmission')
        em.name = '_mask_emit'
        c = MASK.get(m.get('mask_slot', 'Body'), (0, 0, 0))
        em.inputs['Color'].default_value = (*c, 1)
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        tn = nt.nodes.new('ShaderNodeTexImage')
        tn.name = '_mask_target'
        tn.image = img
        nt.nodes.active = tn
        saved.append((nt, out, prev, em, tn))
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    sc.render.bake.margin = 8
    bpy.ops.object.bake(type='EMIT')
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    for nt, out, prev, em, tn in saved:
        if prev is not None:
            nt.links.new(prev, out.inputs['Surface'])
        nt.nodes.remove(em)
        nt.nodes.remove(tn)
    return out_path


def pin(name, x, z, r, length, col, mat, segments=10):
    """Cross pin / button along Y (through the receiver), centred at y=0."""
    o = geo.lathe(name, [(0.0, -length / 2), (r * 0.85, -length / 2), (r, -length / 2 + r * 0.3), (r, length / 2 - r * 0.3),
                         (r * 0.85, length / 2), (0.0, length / 2)], segments=segments, col=col, material=mat)
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (x, 0, z)
    return o


def weighted_normals(obj):
    """Hard-surface normals: big flat faces stay flat, chamfers carry the curvature (face-area weighting)."""
    import bpy
    for p in obj.data.polygons:
        p.use_smooth = True
    m = obj.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL')
    m.mode = 'FACE_AREA'
    m.weight = 100
    m.keep_sharp = True
    m.thresh = 0.01
    bpy.context.view_layer.objects.active = obj
    # keep it as the first modifier (before Armature) and apply it
    while obj.modifiers[0].name != m.name:
        bpy.ops.object.modifier_move_up(modifier=m.name)
    bpy.ops.object.modifier_apply(modifier=m.name)
