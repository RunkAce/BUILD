"""Review renders for the van: review.py <blend> <out_dir> [views...] (studio lights scaled to the vehicle)."""
import bpy, math, os, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
blend, out = argv[0], argv[1]
views = argv[2:] or ['three_quarter', 'three_quarter_rear', 'side', 'front']
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
c = (lo + hi) / 2
size = (hi - lo).length
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.33, 0.35, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
def light(name, rot, e):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); l.data.energy = e; l.data.angle = 0.2
    l.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(l)
light('Key', (50, 0, -35), 3.2); light('Fill', (70, 0, 140), 0.9); light('Top', (5, 0, 0), 0.6)
# ground
bpy.ops.mesh.primitive_plane_add(size=size * 4, location=(c.x, c.y, lo.z - 0.001))
g = bpy.context.object; gm = bpy.data.materials.new('G'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1)
g.data.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
V = {'three_quarter': (1, -0.9, 0.45), 'three_quarter_rear': (-1, 0.9, 0.5), 'side': (0, -1, 0.08), 'front': (1, 0, 0.1),
     'rear': (-1, 0, 0.15), 'left': (0, 1, 0.1), 'top': (0.001, 0, 1), 'rear_open': (-1, 0.25, 0.18),
     'inside': None}
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', 24)); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 900
sc.view_settings.view_transform = 'Standard'
os.makedirs(out, exist_ok=True)
for v in views:
    if v.startswith('inside'):
        cam.data.type = 'PERSP'; cam.data.lens = 16; cam.data.clip_start = 0.05
        eye = Vector(eval(os.environ.get('EYE', '(c.x - 9.0, c.y, 6.0)'))); tgt = Vector(eval(os.environ.get('TGT', '(c.x + 2, c.y, 5.0)')))
        cam.location = eye; cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
        for o in sc.objects:
            if o.type == 'LIGHT': pass
        pl = bpy.data.objects.new('P', bpy.data.lights.new('P', 'POINT')); pl.data.energy = 900; pl.location = eye + Vector((3, 0, 1.5))
        sc.collection.objects.link(pl)
    else:
        cam.data.type = 'PERSP'; cam.data.lens = 50; cam.data.clip_start = 0.1; cam.data.clip_end = size * 20
        d = Vector(V[v]).normalized()
        cam.location = c + d * size * 1.75
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{v}.png')
    bpy.ops.render.render(write_still=True)
