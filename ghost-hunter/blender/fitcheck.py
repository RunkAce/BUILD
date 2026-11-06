"""Avatar fit test for the GhostVan: are the doorways, aisle, cab and steps sized for Roblox characters?

  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python fitcheck.py <GhostVan.blend> <out.json> [render.png]

Avatar collision boxes (studs), standing on the surface below them:
  R6         2 wide x 5   tall x 1 deep   (Torso/Head/legs envelope; the arms do not collide)
  R15        2 wide x 5.3 tall x 1 deep   (default Blocky R15 at scale 1)
  R6 arms    4 wide x 5   tall x 1 deep   (visual only: do the arms clip through walls/shelves?)
  Tall       2 wide x 6.6 tall x 1 deep   (a tall R15 / Rthro-ish avatar)
Doors are treated as OPEN (excluded). Everything else, Glass included, blocks.
Coordinates are Roblox model space (front = -Z, right = +X, up = +Y, origin = ground between axles).
"""
import bpy
import bmesh
import json
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
dg = bpy.context.evaluated_depsgraph_get()
DOORS = {'FrontDoorL', 'FrontDoorR', 'SlidingDoor', 'RearDoorL', 'RearDoorR', 'FrontDoorLGlass', 'FrontDoorRGlass',
         'RearDoorLGlass', 'RearDoorRGlass'}
bm = bmesh.new()
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name not in DOORS:
        t = bmesh.new()
        t.from_object(o, dg)
        t.transform(o.matrix_world)
        me = bpy.data.meshes.new('_t')
        t.to_mesh(me)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        t.free()
VAN = BVHTree.FromBMesh(bm)


def B(rx, ry, rz):            # Roblox model space -> Blender (export) space
    return Vector((rx, -rz, ry))


def box_tree(c, size):
    """Axis-aligned box: c = Roblox (x, feet y, z) centre on the floor, size = Roblox (sx, sy, sz)."""
    b = bmesh.new()
    lo = B(c[0] - size[0] / 2, c[1] + 0.15, c[2] + size[2] / 2)   # humanoids step over lips < 0.15
    hi = B(c[0] + size[0] / 2, c[1] + size[1], c[2] - size[2] / 2)
    mn = Vector((min(lo.x, hi.x), min(lo.y, hi.y), min(lo.z, hi.z)))
    mx = Vector((max(lo.x, hi.x), max(lo.y, hi.y), max(lo.z, hi.z)))
    bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts:
        v.co = Vector((mn.x if v.co.x < 0 else mx.x, mn.y if v.co.y < 0 else mx.y, mn.z if v.co.z < 0 else mx.z))
    t = BVHTree.FromBMesh(b)
    b.free()
    return t


def floor_at(rx, rz, top=12.0):
    hit = VAN.ray_cast(B(rx, top, rz), Vector((0, 0, -1)), 20)
    return round(hit[0].z, 3) if hit[0] is not None else 0.0


def ceiling_at(rx, ry, rz):
    hit = VAN.ray_cast(B(rx, ry, rz), Vector((0, 0, 1)), 20)
    return round(hit[0].z, 3) if hit[0] is not None else None


AV = {'R6': (2, 5.0, 1), 'R15': (2, 5.3, 1), 'R6_arms': (4, 5.0, 1), 'Tall': (2, 6.6, 1)}
# (name, roblox x, z, walking along: 'z' = along the van, 'x' = across)
SPOTS = [('rear_doorway', 0.0, 10.6, 'z'), ('cargo_rear', 0.95, 8.6, 'z'), ('cargo_mid', 0.95, 4.8, 'z'),
         ('beside_stool', 0.95, 3.5, 'z'), ('cargo_front', 0.95, 0.8, 'z'), ('bulkhead_pass', 0.0, -3.85, 'z'),
         ('cab_aisle', 0.0, -4.8, 'z'), ('side_doorway', 3.9, -1.6, 'x'), ('side_inside', 2.4, -1.6, 'x'),
         ('aisle_centre', 0.125, 6.5, 'z'), ('aisle_centre_front', 0.125, 1.5, 'z')]
res = {'spots': {}, 'steps': {}, 'seated': {}}
for name, rx, rz, along in SPOTS:
    fy = floor_at(rx, rz, top=8.0)
    r = {'floor': fy, 'ceiling_clear': None}
    c = ceiling_at(rx, fy + 0.1, rz)
    r['headroom'] = round(c - fy, 2) if c else None
    for av, (w, h, d) in AV.items():
        size = (d, h, w) if along == 'x' else (w, h, d)
        hits = box_tree((rx, fy, rz), size).overlap(VAN)
        r[av] = 'fits' if not hits else f'blocked ({len(hits)} tris)'
    res['spots'][name] = r
# step rises on both entries (walking in from the ground)
for name, path in (('rear', [(0.0, z) for z in (14.2, 13.4, 12.6, 12.0, 11.2, 10.6, 9.5)]),
                   ('side', [(x, -1.6) for x in (6.3, 5.0, 4.4, 3.95, 3.3)])):
    hs = [floor_at(x, z, top=8.0) for x, z in path]
    seq = [0.0]
    for h in hs:
        if abs(h - seq[-1]) > 0.05:
            seq.append(h)
    rises = [round(b - a, 2) for a, b in zip(seq[:-1], seq[1:])]
    res['steps'][name] = {'levels': seq, 'rises': rises, 'max_rise': max(rises) if rises else 0}
# seated head clearance (R6: head top ~3.1 above the cushion)
for name, (rx, rz) in {'driver': (-2.15, -5.2), 'passenger': (2.15, -5.2), 'desk_stool': (-1.3, 3.5)}.items():
    cushion = floor_at(rx, rz, top=6.0)
    c = ceiling_at(rx, cushion + 0.1, rz)
    res['seated'][name] = {'cushion': cushion, 'clear_above': round(c - cushion, 2) if c else None,
                           'R6_head_fits': (c - cushion) > 3.2 if c else True}
json.dump(res, open(argv[1], 'w'), indent=1)
print(json.dumps(res, indent=1))

if len(argv) > 2:      # scale render: blocky stand-in figures (R6 proportions) at the entries and inside
    mat = bpy.data.materials.new('Fig')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.55, 0.15, 1)

    def figure(rx, ry, rz):
        for (sx, sy, sz, oy) in ((1, 2, 1, 1), (2, 2, 1, 3), (1.2, 1, 1.2, 4.5)):
            for ox in ((-0.5, 0.5) if sy == 2 and sx == 1 else (0,)):
                bpy.ops.mesh.primitive_cube_add(size=1, location=B(rx + ox, ry + oy, rz))
                o = bpy.context.object
                o.scale = (sx, sz, sy)
                o.data.materials.append(mat)
        for ox in (-1.5, 1.5):
            bpy.ops.mesh.primitive_cube_add(size=1, location=B(rx + ox, ry + 3, rz))
            o = bpy.context.object
            o.scale = (1, 1, 2)
            o.data.materials.append(mat)
    figure(0, res['steps']['rear']['levels'][1], 13.4)      # on the rear step
    figure(0.95, res['spots']['cargo_mid']['floor'], 4.8)       # standing in the HQ
    figure(6.6, 0, -1.6)                                     # waiting at the side door
    for d in DOORS:
        o = bpy.data.objects.get(d)
        if o:
            o.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=argv[2].replace('.png', '.blend'))
