"""SUNBOUND - solid broad sword, red spine, gold sun disk, short pommel streamer.

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_sunbound.py [--preview] [--no-turntable]

Invariants (brief section 5): one continuous solid blade (no fork, no slot), broad quiet
pearl-steel face, vermilion spine/inlay concentrated near the root (no red outer frame),
compact aged-gold sunburst disk with depth as the single focal ornament, usable grip,
short ivory streamer at a pommel attachment clear of the hand, with a stable root.
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
from shapely.affinity import rotate as srotate  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Sunbound'
ROOT = os.path.dirname(HERE)
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- dimensions (studs)
# From 02_Sunbound: blade width ~26% of blade length, grip ~16% of total, disk ~0.65x blade width.
GRIP_TOP, GRIP_BOT = -0.10, -1.00
BLADE_BASE = 0.12
HALF_W = 0.42
TIP = (0.07, 3.78)            # slightly offset point: decisive clip, not a symmetric spear
DISK_C = (0.0, 0.10)          # disk centre (sits on the guard/blade junction)
DISK_R = 0.27


def blade_shape():
    w = HALF_W
    right = [(0.0, BLADE_BASE - 0.05), (w + 0.10, BLADE_BASE), (w + 0.10, 0.34), (w + 0.02, 0.42),   # stepped root flare
             (w, 0.62), (w, 2.92), (w - 0.06, 3.22), TIP]
    left = [TIP, (-w + 0.02, 3.30), (-w, 3.02), (-w, 0.62), (-w - 0.02, 0.42), (-w - 0.10, 0.34),
            (-w - 0.10, BLADE_BASE)]
    return Polygon(geo.orient(right + left[1:]))


def spine_shape():
    # inset red strip: ~11% of blade width at the root, tapering to a point at ~35% of exposed blade
    hw = HALF_W * 0.14
    return Polygon(geo.orient([(0, 0.30 - 0.05), (hw, 0.34), (hw * 0.65, 1.0), (0.0, 1.45), (-hw * 0.65, 1.0),
                               (-hw, 0.34)]))


def fuller_prism(z0, z1, depth, width):
    """Triangular prism (V groove cutter) running along z on both faces."""
    bm = bmesh.new()
    for sign in (-1, 1):
        y_face = sign * 0.10
        a = [bm.verts.new((-width / 2, y_face + sign * 0.02, z)) for z in (z0, z1)]
        b = [bm.verts.new((width / 2, y_face + sign * 0.02, z)) for z in (z0, z1)]
        c = [bm.verts.new((0.0, y_face - sign * depth, z)) for z in (z0, z1)]
        for f in ([a[0], b[0], c[0]], [a[1], c[1], b[1]], [a[0], a[1], b[1], b[0]], [b[0], b[1], c[1], c[0]],
                  [c[0], c[1], a[1], a[0]]):
            bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return geo.mesh_object('FullerCutter', bm)


def rays_shape():
    """Shallow sun-ray relief on the blade root, radiating from the disk (blade side only)."""
    rays = []
    for i in range(11):
        a = math.radians(18 + i * 14.4)
        base = Point(DISK_C).buffer(DISK_R + 0.03)
        r1 = DISK_R + 0.36 + 0.08 * (i % 2)
        tri = Polygon([(DISK_C[0] + math.cos(a - 0.09) * (DISK_R + 0.02), DISK_C[1] + math.sin(a - 0.09) * (DISK_R + 0.02)),
                       (DISK_C[0] + math.cos(a) * r1, DISK_C[1] + math.sin(a) * r1),
                       (DISK_C[0] + math.cos(a + 0.09) * (DISK_R + 0.02), DISK_C[1] + math.sin(a + 0.09) * (DISK_R + 0.02))])
        rays.append(tri.difference(base))
    return unary_union(rays).intersection(blade_shape().buffer(-0.07)).intersection(box(-1, BLADE_BASE + 0.06, 1, 1))


def guard_shape():
    # red cross-guard: angled arms from the disk hub ending in two-point swallowtails
    def arm(sign):
        # hub -> lower swallowtail point -> V notch -> upper point -> back along the top edge
        pts = [(sign * 0.18, -0.16), (sign * 0.62, -0.10), (sign * 0.90, -0.06), (sign * 0.76, 0.12), (sign * 0.94, 0.40),
               (sign * 0.62, 0.28), (sign * 0.20, 0.34)]
        return Polygon(geo.orient(pts)).buffer(0)
    hub = Point(DISK_C).buffer(DISK_R + 0.07, 8)
    lower = Polygon(geo.orient([(-0.17, -0.06), (0.17, -0.06), (0.11, -0.22), (-0.11, -0.22)]))
    return unary_union([arm(1), arm(-1), hub, lower])


def arm_trim(sign):
    pts = [(sign * 0.36, -0.03), (sign * 0.74, 0.0), (sign * 0.70, 0.07), (sign * 0.36, 0.04)]
    return Polygon(geo.orient(pts)).buffer(0)


def star_shape(points=8, r_out=0.20, r_in=0.10):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi / 2 + i * math.pi / points
        pts.append((DISK_C[0] + r * math.cos(a), DISK_C[1] + r * math.sin(a)))
    return Polygon(geo.orient(pts))


def streamer(col, mat, root, length=0.95, width=0.2, segs=14, bones=5):
    """Short twisting flat strip skinned to a bone chain; root pinned at the pommel ring."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    rows = []
    for i in range(segs + 1):
        t = i / segs
        z = root[2] - 0.03 - t * length
        sway = 0.12 * math.sin(t * 2.2) * t           # rest pose: gentle S, hangs clear of the hand
        twist = math.radians(10 + 55 * t)
        w = width * (1 - 0.15 * t)
        hx, hy = math.cos(twist) * w / 2, math.sin(twist) * w / 2
        cx = root[0] + sway
        rows.append((bm.verts.new((cx - hx, root[1] - hy, z)), bm.verts.new((cx + hx, root[1] + hy, z)), t))
    for (a0, b0, t0), (a1, b1, t1) in zip(rows[:-1], rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1))
        for loop, uv in zip(f.loops, ((0, t0), (1, t0), (1, t1), (0, t1))):
            loop[uv_layer].uv = uv
    # angled end cut: one tail corner longer than the other (reads as a cut seal tab)
    rows[-1][0].co.z -= 0.07
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = geo.mesh_object(f'{NAME}_Streamer', bm, col, mat)
    # thickness so it never disappears edge-on, and both sides render
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.012
    sol.offset = 0
    # armature
    arm_data = bpy.data.armatures.new(f'{NAME}_StreamerRig')
    rig = bpy.data.objects.new(f'{NAME}_StreamerRig', arm_data)
    col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    # fixed root bone at the pommel ring: holds the attachment row so the cloth root can never drift
    rb = arm_data.edit_bones.new('ClothRoot')
    rb.head = (root[0], root[1], root[2] + 0.02)
    rb.tail = (root[0], root[1], root[2] - 0.03)
    prev = rb
    names = []
    for b in range(bones):
        t0, t1 = b / bones, (b + 1) / bones
        eb = arm_data.edit_bones.new(f'Cloth{b + 1}')
        eb.head = (root[0] + 0.12 * math.sin(t0 * 2.2) * t0, root[1], root[2] - 0.03 - t0 * length)
        eb.tail = (root[0] + 0.12 * math.sin(t1 * 2.2) * t1, root[1], root[2] - 0.03 - t1 * length)
        eb.parent = prev
        eb.use_connect = True
        prev = eb
        names.append(eb.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.vertex_groups.new(name='ClothRoot')
    for n in names:
        obj.vertex_groups.new(name=n)
    for v in obj.data.vertices:
        t = max(0.0, min(0.9999, (root[2] - 0.03 - v.co.z) / length))
        if t < 0.02:
            obj.vertex_groups['ClothRoot'].add([v.index], 1.0, 'REPLACE')
            continue
        f = t * bones
        i = int(f)
        frac = f - i
        obj.vertex_groups[names[i]].add([v.index], 1 - frac, 'REPLACE')
        if i + 1 < bones:
            obj.vertex_groups[names[i + 1]].add([v.index], frac, 'REPLACE')
    geo.finalize_weights(obj, names[-1])
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    obj.parent = rig
    return obj, rig, names


def cloth_material():
    """Ivory cloth: painted shading + UV-space vermilion edge stripe and chevron/diamond seal mark."""
    m = paint.painted(f'{NAME}_cloth', 'cloth', height=1.0, streak=0.4)
    nt = m.node_tree
    L = nt.links
    uv = nt.nodes.new('ShaderNodeUVMap')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(uv.outputs['UV'], sep.inputs[0])
    # edge stripe on one long edge (u < 0.12), first ~45% of length
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'LESS_THAN'; st.inputs[1].default_value = 0.12
    L.new(sep.outputs['X'], st.inputs[0])
    st2 = nt.nodes.new('ShaderNodeMath'); st2.operation = 'LESS_THAN'; st2.inputs[1].default_value = 0.45
    L.new(sep.outputs['Y'], st2.inputs[0])
    stripe = nt.nodes.new('ShaderNodeMath'); stripe.operation = 'MULTIPLY'
    L.new(st.outputs[0], stripe.inputs[0]); L.new(st2.outputs[0], stripe.inputs[1])
    # chevron: |u-0.5|*k + v band near v~0.62
    du = nt.nodes.new('ShaderNodeMath'); du.operation = 'SUBTRACT'; du.inputs[1].default_value = 0.5
    L.new(sep.outputs['X'], du.inputs[0])
    adu = nt.nodes.new('ShaderNodeMath'); adu.operation = 'ABSOLUTE'
    L.new(du.outputs[0], adu.inputs[0])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = 0.28
    L.new(adu.outputs[0], k.inputs[0])
    vv = nt.nodes.new('ShaderNodeMath'); vv.operation = 'ADD'
    L.new(sep.outputs['Y'], vv.inputs[0]); L.new(k.outputs[0], vv.inputs[1])
    band_lo = nt.nodes.new('ShaderNodeMath'); band_lo.operation = 'GREATER_THAN'; band_lo.inputs[1].default_value = 0.60
    L.new(vv.outputs[0], band_lo.inputs[0])
    band_hi = nt.nodes.new('ShaderNodeMath'); band_hi.operation = 'LESS_THAN'; band_hi.inputs[1].default_value = 0.66
    L.new(vv.outputs[0], band_hi.inputs[0])
    chev = nt.nodes.new('ShaderNodeMath'); chev.operation = 'MULTIPLY'
    L.new(band_lo.outputs[0], chev.inputs[0]); L.new(band_hi.outputs[0], chev.inputs[1])
    # diamond under the chevron
    dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'SUBTRACT'; dv.inputs[1].default_value = 0.76
    L.new(sep.outputs['Y'], dv.inputs[0])
    adv = nt.nodes.new('ShaderNodeMath'); adv.operation = 'ABSOLUTE'
    L.new(dv.outputs[0], adv.inputs[0])
    adv2 = nt.nodes.new('ShaderNodeMath'); adv2.operation = 'MULTIPLY'; adv2.inputs[1].default_value = 2.2
    L.new(adv.outputs[0], adv2.inputs[0])
    dsum = nt.nodes.new('ShaderNodeMath'); dsum.operation = 'ADD'
    L.new(adu.outputs[0], dsum.inputs[0]); L.new(adv2.outputs[0], dsum.inputs[1])
    dlo = nt.nodes.new('ShaderNodeMath'); dlo.operation = 'GREATER_THAN'; dlo.inputs[1].default_value = 0.10
    L.new(dsum.outputs[0], dlo.inputs[0])
    dhi = nt.nodes.new('ShaderNodeMath'); dhi.operation = 'LESS_THAN'; dhi.inputs[1].default_value = 0.17
    L.new(dsum.outputs[0], dhi.inputs[0])
    dia = nt.nodes.new('ShaderNodeMath'); dia.operation = 'MULTIPLY'
    L.new(dlo.outputs[0], dia.inputs[0]); L.new(dhi.outputs[0], dia.inputs[1])
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MAXIMUM'
    L.new(stripe.outputs[0], m1.inputs[0]); L.new(chev.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MAXIMUM'
    L.new(m1.outputs[0], m2.inputs[0]); L.new(dia.outputs[0], m2.inputs[1])
    paint_out = next(n for n in nt.nodes if n.label == 'PAINT_OUT')
    src = paint_out.inputs[0].links[0].from_socket
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['B'].default_value = paint._hex('#A8352A')
    L.new(src, mix.inputs['A']); L.new(m2.outputs[0], mix.inputs['Factor'])
    nt.links.remove(paint_out.inputs[0].links[0])
    L.new(mix.outputs['Result'], paint_out.inputs[0])
    return m


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    H = TIP[1] + 1.4
    mats = {k: paint.painted(f'{NAME}_{k}', k, height=H, seed=i * 2.3)
            for i, k in enumerate(['pearl', 'vermilion', 'gold_plain', 'gold', 'charcoal', 'deepred'])}
    # warm the pearl toward ivory at the root (QC: pearl dominant at tip and edges, warmth only near root)
    parts = []
    blade = geo.slab('Blade', shape=blade_shape(), core_t=0.20, edge_t=0.03, bevel_w=0.10,
                     levels=[(0.0, 0.015), (0.05, 0.07), (0.10, 0.10)], col=col, material=mats['pearl'])
    # empty fuller groove + red spine channel: boolean V-groove on both faces
    cutter = fuller_prism(0.30, 2.25, 0.035, 0.075)
    b = blade.modifiers.new('Fuller', 'BOOLEAN')
    b.object = cutter
    b.operation = 'DIFFERENCE'
    b.solver = 'EXACT'
    bpy.context.view_layer.objects.active = blade
    bpy.ops.object.modifier_apply(modifier='Fuller')
    bpy.data.objects.remove(cutter, do_unlink=True)
    geo.shade_by_angle(blade, 30)
    parts.append(blade)
    parts.append(geo.slab('Spine', shape=spine_shape(), core_t=0.215, edge_t=0.17, bevel_w=0.012,
                          col=col, material=mats['vermilion']))
    parts.append(geo.slab('SunRays', shape=rays_shape(), core_t=0.222, edge_t=0.20, bevel_w=0.012,
                          col=col, material=mats['pearl']))
    parts.append(geo.slab('Guard', shape=guard_shape(), core_t=0.32, edge_t=0.06, bevel_w=0.07,
                          levels=[(0.0, 0.03), (0.035, 0.12), (0.07, 0.16)], col=col, material=mats['vermilion']))
    for s in (1, -1):
        parts.append(geo.slab(f'ArmTrim{"R" if s > 0 else "L"}', shape=arm_trim(s).intersection(guard_shape().buffer(-0.035)),
                              core_t=0.335, edge_t=0.32, bevel_w=0.01, col=col, material=mats['gold_plain']))
    rim = Point(DISK_C).buffer(DISK_R, 32).difference(Point(DISK_C).buffer(DISK_R - 0.06, 32))
    parts.append(geo.slab('DiskRim', shape=rim, core_t=0.40, edge_t=0.30, bevel_w=0.02, col=col, material=mats['gold_plain']))
    parts.append(geo.slab('DiskPlate', shape=Point(DISK_C).buffer(DISK_R - 0.05, 32), core_t=0.34, edge_t=0.33,
                          bevel_w=0.005, col=col, material=mats['gold']))
    parts.append(geo.slab('DiskStar', shape=star_shape(), core_t=0.42, edge_t=0.36, bevel_w=0.025, col=col,
                          material=mats['gold_plain']))
    gem = geo.lathe('Gem', [(0.0, -0.25), (0.07, -0.235), (0.095, -0.20), (0.095, 0.20), (0.07, 0.235), (0.0, 0.25)],
                    segments=8, col=col, material=mats['deepred'], smooth_angle=10)
    gem.rotation_euler = (math.radians(90), 0, 0)
    gem.location = (DISK_C[0], 0, DISK_C[1])
    parts.append(gem)
    # collars, grip, pommel (red body + gold faceted cap, ring lug)
    parts.append(geo.lathe('UpperCollar', [(0.0, GRIP_TOP - 0.02), (0.11, GRIP_TOP - 0.02), (0.125, GRIP_TOP + 0.02),
                                           (0.125, GRIP_TOP + 0.10), (0.0, GRIP_TOP + 0.12)], segments=8, col=col,
                           material=mats['vermilion']))
    parts.append(geo.lathe('UpperRing', [(0.0, GRIP_TOP + 0.0), (0.132, GRIP_TOP + 0.0), (0.132, GRIP_TOP + 0.04),
                                         (0.0, GRIP_TOP + 0.04)], segments=8, col=col, material=mats['gold_plain']))
    parts.append(geo.wrapped_grip('Grip', GRIP_BOT, GRIP_TOP, 0.08, wraps=6, col=col, material=mats['charcoal'],
                                  style='strap'))
    parts.append(geo.lathe('LowerRing', [(0.0, GRIP_BOT - 0.04), (0.128, GRIP_BOT - 0.04), (0.128, GRIP_BOT),
                                         (0.0, GRIP_BOT)], segments=8, col=col, material=mats['gold_plain']))
    pz = GRIP_BOT - 0.04
    parts.append(geo.lathe('PommelBody', [(0.0, pz), (0.12, pz), (0.16, pz - 0.07), (0.16, pz - 0.18), (0.12, pz - 0.22),
                                          (0.0, pz - 0.22)], segments=8, col=col, material=mats['vermilion'], smooth_angle=20))
    parts.append(geo.lathe('PommelCap', [(0.0, pz - 0.20), (0.135, pz - 0.21), (0.17, pz - 0.27), (0.13, pz - 0.36),
                                         (0.0, pz - 0.40)], segments=8, col=col, material=mats['gold_plain'], smooth_angle=20))
    ring = geo.ring('PommelRing', 0.06, 0.016, sides=6, samples=16, col=col, material=mats['gold_plain'])
    ring.location = (0, 0, pz - 0.45)
    parts.append(ring)
    pipeline_apply(parts)
    return col, parts, mats, (0.0, 0.0, pz - 0.49)


def pipeline_apply(parts):
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def animate_streamer(rig, names, frames, amp=1.0):
    """Root nearly locked, amplitude and lag grow toward the free end; seamless loop (brief + 1.mp4 lessons)."""
    rig.animation_data_create()
    for f in range(1, frames + 2, 4):
        ph = 2 * math.pi * (f - 1) / frames
        for i, n in enumerate(names):
            pb = rig.pose.bones[n]
            pb.rotation_mode = 'XYZ'
            k = (i / (len(names) - 1)) ** 1.3
            lag = i * 0.7
            pb.rotation_euler = (amp * math.radians(4 + 14 * k) * math.sin(ph - lag),
                                 amp * math.radians(3 + 10 * k) * math.sin(2 * ph - lag * 1.3 + 1.0),
                                 amp * math.radians(2 + 8 * k) * math.sin(ph - lag + 2.0))
            pb.keyframe_insert('rotation_euler', frame=f)


if __name__ == '__main__':
    import pipeline  # noqa: E402
    col, parts, mats, ring_pt = build()
    cmat = cloth_material()
    cloth, rig, bone_names = streamer(col, cmat, ring_pt)
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'sunbound', 'blockout')
        os.makedirs(out, exist_ok=True)
        allp = parts + [cloth]
        print('tris', geo.tri_count(allp))
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(allp, v, res=(700, 900) if v != 'side' else (400, 900))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    grip_lead = (0.0, 0.0, GRIP_TOP - 0.22)
    # cloth: bake its own small texture set, then hand the rig + cloth to finish() as extra meshes
    bpy.context.view_layer.objects.active = cloth
    bpy.ops.object.modifier_apply(modifier='Solidify')
    cloth_maps = paint.bake_maps(cloth, os.path.join(ROOT, 'export', NAME, 'textures'), f'{NAME}_Streamer', size=512, samples=16)
    cloth.data.materials.clear()
    cloth.data.materials.append(paint.baked_material(f'{NAME}_StreamerBaked', cloth_maps))
    gem = next(p for p in parts if p.name == 'Gem')
    body_parts = [p for p in parts if p is not gem]
    # move rig with the weapon; cloth is parented to the rig
    rig.location = Vector(rig.location) - Vector(grip_lead)
    res = pipeline.finish(NAME, col, body_parts, ROOT, grip_lead, glow_parts=[gem], glow_spec='deepred', tex=2048,
                          extra_meshes=[], attachments={
                              'Grip': grip_lead,
                              'GripSecondary': (0.0, 0.0, GRIP_BOT + 0.2),
                              'ClothRoot': ring_pt,
                              'VFX_Disk': (DISK_C[0], 0.0, DISK_C[1]),
                              'VFX_SpineTip': (0.0, 0.0, 1.45),
                              'VFX_Tip': (TIP[0], 0.0, TIP[1]),
                          })
    res['stats']['streamer'] = {'triangles': geo.tri_count([cloth]), 'bones': bone_names, 'texture_size': 512,
                                'maps': {k: os.path.relpath(v, ROOT) for k, v in cloth_maps.items()}}
    with open(os.path.join(ROOT, 'export', NAME, f'{NAME}_stats.json'), 'w') as fh:
        json.dump(res['stats'], fh, indent=1)
    stage.export_fbx(os.path.join(ROOT, 'export', NAME, f'{NAME}_Streamer.fbx'), [rig, cloth])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'source', f'{NAME}.blend'))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    meshes = res['meshes'] + [cloth]
    rdir = os.path.join(ROOT, 'renders', 'sunbound')
    pipeline.acceptance_renders(NAME, meshes, res['glow'], rdir, samples=48)
    stage.set_mood('showcase')
    stage.ortho_camera(meshes, 'three_quarter', res=(1100, 1400))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)
    if '--no-turntable' not in sys.argv:
        animate_streamer(rig, bone_names, 96)
        pipeline.turntable(NAME, meshes + [rig], os.path.join(rdir, f'{NAME}_turntable.mp4'))
