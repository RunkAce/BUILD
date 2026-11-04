"""FLARECREST - original Iop spear with a spiral ribbon (user request; quality ref 1.mp4, design original).

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_spear.py [--preview] [--no-turntable]

Design: ivory leaf head with a real flame-shaped opening (family echo of Oathsplitter's slot), twin swept
vermilion crescent wings at the head base (family guard language), gold socket with amber gem, vermilion
lacquered shaft with gold bands, charcoal grip zone, gold butt spike. An ivory ribbon with vermilion edge
stripes spirals ~2.5 turns down the UPPER shaft from the socket and trails free; the coiled part is pinned,
only the tail moves. The grip zone stays clear of the ribbon (R6 hands).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from shapely import affinity as saffine  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Flarecrest'
ROOT = os.path.dirname(HERE)
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs), z up, origin set at grip
BUTT = -3.0
GRIP_TOP, GRIP_BOT = -0.55, -1.75
SOCKET_Z = 2.55
HEAD_BASE, HEAD_TIP_DESIGN = 2.95, 4.50
HEAD_STRETCH = 1.45                 # user: longer blade (head 1.55 -> 2.25 studs), width unchanged
HEAD_TIP = HEAD_BASE + (HEAD_TIP_DESIGN - HEAD_BASE) * HEAD_STRETCH
SHAFT_R = 0.075
WRAP_TOP, WRAP_BOT, WRAP_TURNS = 2.45, 0.55, 2.5


def head_shape():
    half = [(0.0, HEAD_TIP_DESIGN), (0.09, 4.24), (0.21, 3.86), (0.29, 3.50), (0.26, 3.22), (0.12, HEAD_BASE + 0.04),
            (0.06, HEAD_BASE - 0.02)]
    outline = geo.mirror_x([(x, z) for (x, z) in half])
    # flame-shaped opening: rounded belly, tip flicking to one side (reads as a flame tongue, not a loop)
    flame = geo.bezier((0.02, 3.92), (0.06, 3.76), (0.085, 3.56), (0.06, 3.42), 10) + \
        geo.bezier((0.06, 3.42), (0.04, 3.34), (-0.04, 3.34), (-0.06, 3.42), 8)[1:] + \
        geo.bezier((-0.06, 3.42), (-0.08, 3.56), (-0.03, 3.66), (-0.035, 3.76), 8)[1:-1]
    head = Polygon(geo.orient(outline), [geo.orient(flame, False)])
    return saffine.scale(head, xfact=1.0, yfact=HEAD_STRETCH, origin=(0.0, HEAD_BASE))


def wings_shape():
    parts = []
    for s in (1, -1):
        outer = geo.bezier((s * 0.08, 2.66), (s * 0.40, 2.62), (s * 0.56, 2.86), (s * 0.58, 3.26), 12)
        inner = geo.bezier((s * 0.58, 3.26), (s * 0.44, 3.02), (s * 0.30, 2.90), (s * 0.08, 2.92), 12)
        parts.append(Polygon(geo.orient(outer + inner[1:])).buffer(0))
    return unary_union(parts)


def wing_inlay(s):
    a = geo.bezier((s * 0.16, 2.72), (s * 0.38, 2.72), (s * 0.48, 2.86), (s * 0.52, 3.12), 10)
    b = geo.bezier((s * 0.49, 3.06), (s * 0.42, 2.90), (s * 0.32, 2.80), (s * 0.16, 2.79), 10)
    return Polygon(geo.orient(a + b)).buffer(0)


def helix_ribbon(col, mat, bones=8):
    """Ribbon: helix pinned around the upper shaft, then a free trailing tail; skinned to a bone chain."""
    width = 0.20
    wrap_r = SHAFT_R + 0.035
    samples_wrap, samples_tail = 70, 40
    centre, across, tparam = [], [], []
    total = samples_wrap + samples_tail
    for i in range(samples_wrap + 1):
        t = i / samples_wrap
        ang = t * WRAP_TURNS * 2 * math.pi
        z = WRAP_TOP - t * (WRAP_TOP - WRAP_BOT)
        radial = Vector((math.cos(ang), math.sin(ang), 0))
        c = Vector((0, 0, z)) + radial * wrap_r
        tangent = Vector((-math.sin(ang) * wrap_r * WRAP_TURNS * 2 * math.pi, math.cos(ang) * wrap_r * WRAP_TURNS * 2 * math.pi,
                          -(WRAP_TOP - WRAP_BOT))).normalized()
        w = radial.cross(tangent).normalized()          # width lies on the cylinder surface
        centre.append(c)
        across.append(w)
        tparam.append(i / total)
    # tail: leaves the shaft outward and down in a loose S, twisting from flat-on to edge-on and back
    last_c, last_w = centre[-1], across[-1]
    out_dir = Vector((last_c.x, last_c.y, 0)).normalized()
    for j in range(1, samples_tail + 1):
        u = j / samples_tail
        c = last_c + out_dir * (0.55 * u) + Vector((0, 0, -1.35 * u)) + \
            out_dir.cross(Vector((0, 0, 1))) * (0.25 * math.sin(u * math.pi * 1.3))
        twist = math.radians(80 * math.sin(u * math.pi))
        w = (last_w * math.cos(twist) + out_dir * math.sin(twist)).normalized()
        centre.append(c)
        across.append(w)
        tparam.append((samples_wrap + j) / total)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for c, w, tp in zip(centre, across, tparam):
        hw = width / 2 * (1 - 0.25 * max(0.0, (tp - 0.7) / 0.3))
        rows.append((bm.verts.new(c - w * hw), bm.verts.new(c + w * hw), tp))
    for (a0, b0, t0), (a1, b1, t1) in zip(rows[:-1], rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1))
        for loop, uv in zip(f.loops, ((0, t0), (1, t0), (1, t1), (0, t1))):
            loop[uvl].uv = uv
    rows[-1][0].co.z -= 0.08                             # angled cut end
    obj = geo.mesh_object(f'{NAME}_Ribbon', bm, col, mat)
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.012
    sol.offset = 0
    # bones: one root bone holds the whole wrap; the chain starts where the ribbon leaves the shaft
    arm_data = bpy.data.armatures.new(f'{NAME}_RibbonRig')
    rig = bpy.data.objects.new(f'{NAME}_RibbonRig', arm_data)
    col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    root = arm_data.edit_bones.new('RibbonRoot')
    root.head = (0, 0, WRAP_TOP)
    root.tail = (0, 0, WRAP_BOT)
    names = ['RibbonRoot']
    tail_pts = centre[samples_wrap - 10:]
    step = max(1, len(tail_pts) // bones)
    prev = root
    chain_pts = tail_pts[::step][:bones + 1]
    for k in range(len(chain_pts) - 1):
        eb = arm_data.edit_bones.new(f'Ribbon{k + 1}')
        eb.head = chain_pts[k]
        eb.tail = chain_pts[k + 1]
        eb.parent = prev
        prev = eb
        names.append(eb.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    for nm in names:
        obj.vertex_groups.new(name=nm)
    wrap_end_t = samples_wrap / total
    for v in obj.data.vertices:
        # nearest centreline index
        best, bi = 1e9, 0
        for i, c in enumerate(centre):
            d = (Vector(v.co) - c).length_squared
            if d < best:
                best, bi = d, i
        tp = tparam[bi]
        if tp <= wrap_end_t - 0.06:
            obj.vertex_groups['RibbonRoot'].add([v.index], 1.0, 'REPLACE')
            continue
        f = (bi - (samples_wrap - 10)) / step
        k = max(0, min(len(names) - 2, int(f)))
        frac = max(0.0, min(1.0, f - k))
        obj.vertex_groups[names[k + 1]].add([v.index], 1 - frac, 'REPLACE')
        if k + 2 < len(names):
            obj.vertex_groups[names[k + 2]].add([v.index], frac, 'REPLACE')
    geo.finalize_weights(obj, names[-1])
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    obj.parent = rig
    return obj, rig, names


def ribbon_material():
    m = paint.painted(f'{NAME}_ribbon', 'cloth', height=2.0, streak=0.4)
    nt, L = m.node_tree, m.node_tree.links
    uv = nt.nodes.new('ShaderNodeUVMap')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(uv.outputs['UV'], sep.inputs[0])
    du = nt.nodes.new('ShaderNodeMath'); du.operation = 'SUBTRACT'; du.inputs[1].default_value = 0.5
    L.new(sep.outputs['X'], du.inputs[0])
    adu = nt.nodes.new('ShaderNodeMath'); adu.operation = 'ABSOLUTE'
    L.new(du.outputs[0], adu.inputs[0])
    edge = nt.nodes.new('ShaderNodeMath'); edge.operation = 'GREATER_THAN'; edge.inputs[1].default_value = 0.36
    L.new(adu.outputs[0], edge.inputs[0])
    inner = nt.nodes.new('ShaderNodeMath'); inner.operation = 'LESS_THAN'; inner.inputs[1].default_value = 0.44
    L.new(adu.outputs[0], inner.inputs[0])
    stripe = nt.nodes.new('ShaderNodeMath'); stripe.operation = 'MULTIPLY'
    L.new(edge.outputs[0], stripe.inputs[0]); L.new(inner.outputs[0], stripe.inputs[1])
    po = next(n for n in nt.nodes if n.label == 'PAINT_OUT')
    src = po.inputs[0].links[0].from_socket
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['B'].default_value = paint._hex('#B23A2A')
    L.new(src, mix.inputs['A']); L.new(stripe.outputs[0], mix.inputs['Factor'])
    nt.links.remove(po.inputs[0].links[0])
    L.new(mix.outputs['Result'], po.inputs[0])
    return m


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    H = HEAD_TIP - BUTT
    mats = {k: paint.painted(f'{NAME}_{k}', k, height=H, seed=i * 2.9)
            for i, k in enumerate(['ivory', 'vermilion', 'gold', 'gold_plain', 'charcoal', 'amber'])}
    parts = []
    parts.append(geo.slab('Head', shape=head_shape(), core_t=0.13, edge_t=0.02, bevel_w=0.06,
                          levels=[(0.0, 0.01), (0.03, 0.045), (0.06, 0.065)], col=col, material=mats['ivory']))
    parts.append(geo.slab('Wings', shape=wings_shape(), core_t=0.16, edge_t=0.04, bevel_w=0.04,
                          levels=[(0.0, 0.02), (0.02, 0.06), (0.04, 0.08)], col=col, material=mats['vermilion']))
    for s in (1, -1):
        parts.append(geo.slab(f'WingInlay{"R" if s > 0 else "L"}', shape=wing_inlay(s).intersection(wings_shape().buffer(-0.02)),
                              core_t=0.175, edge_t=0.16, bevel_w=0.006, col=col, material=mats['gold_plain']))
    parts.append(geo.lathe('Socket', [(0.0, SOCKET_Z - 0.20), (0.10, SOCKET_Z - 0.20), (0.115, SOCKET_Z - 0.14),
                                      (0.10, SOCKET_Z - 0.10), (0.13, SOCKET_Z + 0.05), (0.13, SOCKET_Z + 0.22),
                                      (0.09, SOCKET_Z + 0.36), (0.0, SOCKET_Z + 0.40)], segments=8, col=col,
                           material=mats['gold']))
    gem = geo.lathe('Gem', [(0.0, -0.18), (0.055, -0.15), (0.075, 0.0), (0.055, 0.15), (0.0, 0.18)], segments=6,
                    col=col, material=mats['amber'], smooth_angle=10)
    gem.rotation_euler = (math.radians(90), 0, 0)
    gem.location = (0, 0, SOCKET_Z + 0.13)
    parts.append(gem)
    parts.append(geo.lathe('Shaft', [(0.0, BUTT + 0.30), (SHAFT_R, BUTT + 0.30), (SHAFT_R, SOCKET_Z - 0.15),
                                     (0.0, SOCKET_Z - 0.15)], segments=10, col=col, material=mats['vermilion']))
    for z in (WRAP_BOT - 0.12, GRIP_TOP + 0.04, GRIP_BOT - 0.04, BUTT + 0.55):
        parts.append(geo.lathe(f'Band{z:.2f}', [(0.0, z - 0.05), (SHAFT_R + 0.022, z - 0.05), (SHAFT_R + 0.03, z - 0.02),
                                               (SHAFT_R + 0.03, z + 0.02), (SHAFT_R + 0.022, z + 0.05), (0.0, z + 0.05)],
                               segments=10, col=col, material=mats['gold_plain']))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, SHAFT_R + 0.01, wraps=8, col=col,
                                  material=mats['charcoal'], style='strap'))
    parts.append(geo.lathe('ButtCap', [(0.0, BUTT + 0.36), (SHAFT_R + 0.03, BUTT + 0.34), (0.11, BUTT + 0.22),
                                       (0.10, BUTT + 0.14), (0.0, BUTT)], segments=6, col=col, material=mats['gold_plain'],
                           smooth_angle=20))
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return col, parts, mats


def animate_ribbon(rig, names, period, total=None):
    """Root locked; amplitude and lag grow toward the tip; seamless loop; 3-4 distinct tail poses (1.mp4)."""
    for f in range(1, (total or period) + 2, 3):
        ph = 2 * math.pi * (f - 1) / period
        for i, n in enumerate(names[1:], start=1):
            pb = rig.pose.bones[n]
            pb.rotation_mode = 'XYZ'
            k = (i / (len(names) - 1)) ** 1.4
            lag = i * 0.6
            pb.rotation_euler = (math.radians(3 + 16 * k) * math.sin(ph - lag),
                                 math.radians(2 + 10 * k) * math.sin(2 * ph - lag + 0.8),
                                 math.radians(2 + 14 * k) * math.sin(ph - lag * 1.2 + 2.1))
            pb.keyframe_insert('rotation_euler', frame=f)


if __name__ == '__main__':
    import pipeline  # noqa: E402
    col, parts, mats = build()
    rmat = ribbon_material()
    ribbon, rig, bone_names = helix_ribbon(col, rmat)
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'flarecrest', 'blockout')
        os.makedirs(out, exist_ok=True)
        allp = parts + [ribbon]
        print('tris', geo.tri_count(allp))
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(allp, v, res=(600, 1100) if v != 'side' else (400, 1100))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    grip_lead = (0.0, 0.0, GRIP_TOP - 0.25)
    bpy.context.view_layer.objects.active = ribbon
    bpy.ops.object.modifier_apply(modifier='Solidify')
    rmaps = paint.bake_maps(ribbon, os.path.join(ROOT, 'export', NAME, 'textures'), f'{NAME}_Ribbon', size=512, samples=12)
    ribbon.data.materials.clear()
    ribbon.data.materials.append(paint.baked_material(f'{NAME}_RibbonBaked', rmaps))
    gem = next(p for p in parts if p.name == 'Gem')
    body_parts = [p for p in parts if p is not gem]
    rig.location = Vector(rig.location) - Vector(grip_lead)
    res = pipeline.finish(NAME, col, body_parts, ROOT, grip_lead, glow_parts=[gem], tex=2048, attachments={
        'Grip': grip_lead,
        'GripSecondary': (0.0, 0.0, GRIP_BOT + 0.25),
        'RibbonRoot': (0.0, 0.0, WRAP_TOP),
        'VFX_Tip': (0.0, 0.0, HEAD_TIP),
        'VFX_Flame': (0.0, 0.0, HEAD_BASE + (3.6 - HEAD_BASE) * HEAD_STRETCH),
        'VFX_Gem': (0.0, 0.0, SOCKET_Z + 0.13),
    })
    import optimize  # noqa: E402
    res['stats']['ribbon'] = {'triangles': geo.tri_count([ribbon]), 'bones': bone_names, 'texture_size': 512,
                              'topology': optimize.topology_report(ribbon),
                              'maps': {k: os.path.relpath(v, ROOT) for k, v in rmaps.items()}}
    with open(os.path.join(ROOT, 'export', NAME, f'{NAME}_stats.json'), 'w') as fh:
        json.dump(res['stats'], fh, indent=1)
    stage.export_fbx(os.path.join(ROOT, 'export', NAME, f'{NAME}_Ribbon.fbx'), [rig, ribbon])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'source', f'{NAME}.blend'))
    meshes = res['meshes'] + [ribbon]
    rdir = os.path.join(ROOT, 'renders', 'flarecrest')
    pipeline.acceptance_renders(NAME, meshes, res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(meshes, 'three_quarter', res=(900, 1500))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
    if '--no-turntable' not in sys.argv:
        animate_ribbon(rig, bone_names, 72, total=144)   # 3 s seamless loop, twice per turn
        pipeline.turntable(NAME, meshes + [rig], os.path.join(rdir, f'{NAME}_turntable.mp4'), frames=144, res=(600, 1000))
