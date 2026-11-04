"""WARLINK - paired short broad cleavers joined through pommel eyelets by a compact chain.

Run:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_warlink.py [--preview] [--no-turntable]

Invariants (brief section 6): two matching short broad cleavers; robust pommel eyelets beyond the grip
with visible interior thickness; thick dark-steel chain of rigid interlocking links, consistent size,
alternating orientation, open centres; compact tether matching the concept length (never stretched);
taut at full separation, controlled slack when closer, stable endpoints.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))

import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import geo  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402

NAME = 'Warlink'
ROOT = os.path.dirname(HERE)
PREVIEW = '--preview' in sys.argv

# ---------------------------------------------------------------- one cleaver (local, spine toward +x)
L = 2.3                       # cleaver length, tip to eyelet bottom (studs)
GRIP_TOP, GRIP_BOT = 0.18, -0.55
EYE_Z = -0.92                 # eyelet centre
EYE_R, EYE_WIRE = 0.10, 0.038
LINKS = 7
# Rectangular box-frame links (user style ref: FULL Chain Weapon.mp4 ~0:09-0:13): square-section bars,
# outer length ~2.7x width, bar ~0.3x width, alternating 90 deg. 9 pieces x pitch ~= 0.83 L tether.
LINK_LEN, LINK_W, LINK_WIRE = 0.27, 0.10, 0.03
PITCH = LINK_LEN - 2 * LINK_WIRE           # centre-to-centre spacing of interlocked links (bars overlap)


def blade_shape():
    out = [(0.22, 0.30), (0.22, 1.40),            # spine side (covered by the housing)
           (-0.10, 1.60),                          # inner prong (taller, broader)
           (-0.17, 1.40), (-0.21, 1.34), (-0.25, 1.36),   # rounded notch root (~0.11 L deep from the outer tip)
           (-0.40, 1.53),                          # outer prong (thin, shorter)
           (-0.43, 1.30), (-0.44, 0.90), (-0.41, 0.48), (-0.36, 0.34), (-0.30, 0.30)]
    return Polygon(geo.orient(out))


def housing_shape():
    strip = Polygon(geo.orient([(0.14, 0.24), (0.31, 0.24), (0.31, 1.40), (0.235, 1.53), (0.14, 1.44)]))
    boss = Polygon(geo.orient([(0.225, 1.06), (0.35, 1.19), (0.225, 1.32), (0.10, 1.19)]))
    return unary_union([strip, boss])


def accent_shape():
    # gold Y accent riding along the housing (concept: curved trident-like line near the spine)
    stem = geo.bezier((0.07, 0.36), (0.04, 0.55), (0.03, 0.72), (0.06, 0.96), 10)
    stem_b = geo.bezier((0.12, 0.92), (0.11, 0.72), (0.12, 0.55), (0.14, 0.36), 10)
    arm = geo.bezier((0.05, 0.50), (-0.03, 0.56), (-0.09, 0.64), (-0.13, 0.78), 8)
    arm_b = geo.bezier((-0.09, 0.78), (-0.04, 0.64), (0.02, 0.58), (0.08, 0.56), 8)
    return unary_union([Polygon(geo.orient(stem + stem_b)).buffer(0), Polygon(geo.orient(arm + arm_b)).buffer(0)])


def guard_shape():
    band = Polygon(geo.orient([(-0.46, 0.20), (0.33, 0.20), (0.35, 0.32), (-0.46, 0.32)]))
    hook = Polygon(geo.orient(geo.bezier((0.30, 0.20), (0.48, 0.20), (0.56, 0.28), (0.56, 0.44), 8)
                              + geo.bezier((0.52, 0.38), (0.48, 0.32), (0.42, 0.31), (0.30, 0.32), 8))).buffer(0)
    return unary_union([band, hook])


def cleaver(col, mats, side):
    """side=+1 right cleaver, -1 left. Built with the spine toward +x; the RIGHT one is mirrored so both
    spines and quillons face the chain centre at rest (concept 03_Warlink)."""
    tag = 'R' if side > 0 else 'L'
    parts = []
    parts.append(geo.slab(f'Blade{tag}', shape=blade_shape(), core_t=0.13, edge_t=0.02, bevel_w=0.08,
                          levels=[(0.0, 0.01), (0.08, 0.065)], col=col, material=mats['ivory']))
    parts.append(geo.slab(f'Housing{tag}', shape=housing_shape(), core_t=0.19, edge_t=0.10, bevel_w=0.035,
                          col=col, material=mats['vermilion']))
    parts.append(geo.slab(f'Accent{tag}', shape=accent_shape(), core_t=0.145, edge_t=0.13, bevel_w=0.008,
                          col=col, material=mats['gold_plain']))
    rivet = geo.lathe(f'Rivet{tag}', [(0.0, -0.115), (0.05, -0.11), (0.055, -0.09), (0.055, 0.09), (0.05, 0.11),
                                      (0.0, 0.115)], segments=10, col=col, material=mats['gold_plain'])
    rivet.rotation_euler = (math.radians(90), 0, 0)
    rivet.location = (0.225, 0, 1.19)
    parts.append(rivet)
    parts.append(geo.slab(f'Guard{tag}', shape=guard_shape(), core_t=0.22, edge_t=0.08, bevel_w=0.04,
                          col=col, material=mats['vermilion']))
    parts.append(geo.lathe(f'TopFerrule{tag}', [(0.0, GRIP_TOP - 0.02), (0.11, GRIP_TOP - 0.02), (0.125, GRIP_TOP + 0.01),
                                               (0.125, GRIP_TOP + 0.04), (0.0, GRIP_TOP + 0.04)], segments=8,
                           col=col, material=mats['vermilion']))
    parts.append(geo.wrapped_grip(f'Grip{tag}', GRIP_BOT, GRIP_TOP - 0.02, 0.078, wraps=5, col=col,
                                  material=mats['charcoal'], style='strap'))
    # two-tier stepped ferrule + gold collar band (QC: give the eyelet join emphasis)
    z = GRIP_BOT
    parts.append(geo.lathe(f'Ferrule{tag}', [(0.0, z), (0.11, z), (0.115, z - 0.06), (0.135, z - 0.07),
                                            (0.135, z - 0.17), (0.11, z - 0.19), (0.0, z - 0.19)], segments=8,
                           col=col, material=mats['vermilion']))
    parts.append(geo.lathe(f'Collar{tag}', [(0.0, z - 0.095), (0.141, z - 0.095), (0.141, z - 0.135), (0.0, z - 0.135)],
                           segments=8, col=col, material=mats['gold_plain']))
    # hex steel lug, pierced by the eyelet
    lug = geo.lathe(f'Lug{tag}', [(0.0, z - 0.19), (0.07, z - 0.19), (0.075, z - 0.24), (0.05, z - 0.30),
                                  (0.0, z - 0.31)], segments=6, col=col, material=mats['darksteel'], smooth_angle=15)
    lug.scale = (1.0, 0.55, 1.0)
    parts.append(lug)
    eo = EYE_R + EYE_WIRE
    eframe = box(-eo, EYE_Z - eo, eo, EYE_Z + eo).difference(box(-EYE_R + 0.01, EYE_Z - EYE_R + 0.01, EYE_R - 0.01, EYE_Z + EYE_R - 0.01))
    eye = geo.slab(f'Eyelet{tag}', shape=eframe, core_t=EYE_WIRE * 1.6, edge_t=EYE_WIRE * 0.9, bevel_w=0.012,
                   col=col, material=mats['darksteel'], smooth_angle=20)
    parts.append(eye)
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if side > 0:
        for o in parts:
            o.scale = (-1, 1, 1)
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.transform_apply(scale=True)
            if not geo.mesh_health(o)['normals_outward']:
                o.data.flip_normals()
    return parts


# ---------------------------------------------------------------- chain
def link_mesh(name, col, mat, brass=False):
    """Box-frame link: rectangle of four square-section bars with a small chamfer, long axis on Z,
    frame in the XZ plane, open centre. Brass end links use the same frame, slightly heavier."""
    w, ln, bar = LINK_W, LINK_LEN, LINK_WIRE
    if brass:
        w, bar = w * 1.1, bar * 1.15
    frame = box(-w / 2, -ln / 2, w / 2, ln / 2).difference(box(-w / 2 + bar, -ln / 2 + bar, w / 2 - bar, ln / 2 - bar))
    return geo.slab(name, shape=frame, core_t=bar, edge_t=bar * 0.55, bevel_w=bar * 0.22,
                    col=col, material=mat, smooth_angle=20)


def solve_chain(a, b, n, pitch, prev=None, iters=60, gravity=(0, 0, -0.012), damping=0.92, prev2=None):
    """Fixed-length chain between endpoints a,b: Verlet + distance constraints. Never stretches links:
    if |b-a| exceeds the chain length the far endpoint constraint wins and the chain goes straight (taut)."""
    a, b = Vector(a), Vector(b)
    if prev is None:
        pts = [a.lerp(b, i / (n - 1)) + Vector((0, 0, -0.35 * math.sin(math.pi * i / (n - 1)))) for i in range(n)]
        return pts
    pts = [p.copy() for p in prev]
    old = [p.copy() for p in (prev2 or prev)]
    for i in range(1, n - 1):
        v = (pts[i] - old[i]) * damping
        pts[i] = pts[i] + v + Vector(gravity)
    pts[0], pts[-1] = a.copy(), b.copy()
    for _ in range(iters):
        for i in range(n - 1):
            d = pts[i + 1] - pts[i]
            ln = d.length or 1e-6
            diff = (ln - pitch) / ln
            if i == 0:
                pts[i + 1] -= d * diff
            elif i + 1 == n - 1:
                pts[i] += d * diff
            else:
                pts[i] += d * 0.5 * diff
                pts[i + 1] -= d * 0.5 * diff
        pts[0], pts[-1] = a.copy(), b.copy()
    return pts


def place_links(objs, pts, cam_side=Vector((0, -1, 0))):
    """Orient each link along its segment; alternate 90 deg roll; links overlap neighbours by design."""
    for i, o in enumerate(objs):
        p0, p1 = pts[i], pts[i + 1]
        mid = (p0 + p1) / 2
        t = (p1 - p0).normalized()
        q = Vector((0, 0, 1)).rotation_difference(t)
        roll = Quaternion(t, math.radians(90 if i % 2 else 0))
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = roll @ q
        o.location = mid


def build(fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    col = stage.collection(NAME)
    mats = {k: paint.painted(f'{NAME}_{k}', k, height=L, seed=i * 1.7)
            for i, k in enumerate(['ivory', 'vermilion', 'gold', 'gold_plain', 'charcoal', 'darksteel'])}
    right = cleaver(col, mats, +1)
    left = cleaver(col, mats, -1)
    # chain: brass ring, 9 steel links, brass ring = 11 segments between the eyelets
    chain = [link_mesh('ChainRingA', col, mats['gold_plain'], brass=True)]
    chain += [link_mesh(f'Link{i + 1:02d}', col, mats['darksteel']) for i in range(LINKS)]
    chain += [link_mesh('ChainRingB', col, mats['gold_plain'], brass=True)]
    return col, mats, right, left, chain


def rest_pose(right, left, angle=24, span=2.3):
    """Concept rest pose: blades up, splayed outward, eyelets span ~0.67 L, chain sags in a U."""
    for parts, s in ((right, 1), (left, -1)):
        piv = bpy.data.objects.new(f'Pivot{"R" if s > 0 else "L"}', None)
        bpy.context.scene.collection.objects.link(piv)
        for o in parts:
            o.parent = piv
        piv.location = (s * span / 2, 0, -EYE_Z)
        piv.rotation_euler = (0, math.radians(s * angle), 0)   # tips splay outward
    bpy.context.view_layer.update()


def eyelet_world(parts):
    eye = next(o for o in parts if o.name.startswith('Eyelet'))
    return eye.matrix_world @ Vector((0, 0, EYE_Z - EYE_R * 0.55))


if __name__ == '__main__':
    import pipeline  # noqa: E402
    col, mats, right, left, chain = build()
    rest_pose(right, left)
    a, b = eyelet_world(left), eyelet_world(right)
    n = len(chain) + 1
    pts = solve_chain(a, b, n, PITCH)
    prev = None
    for _ in range(200):                                     # settle to a plausible rest
        pts, prev = solve_chain(a, b, n, PITCH, prev=pts, prev2=prev), pts
    place_links(chain, pts)
    allm = right + left + chain
    if PREVIEW:
        out = os.path.join(ROOT, 'renders', 'warlink', 'blockout')
        os.makedirs(out, exist_ok=True)
        print('tris', geo.tri_count(allm))
        bad = {o.name: geo.mesh_health(o) for o in allm if not geo.mesh_health(o)['normals_outward'] or geo.mesh_health(o)['non_manifold_edges']}
        print('health issues', bad)
        for v in ('front', 'three_quarter', 'side'):
            stage.ortho_camera(allm, v, res=(1000, 800) if v != 'side' else (500, 800))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)

    # ------------------------------------------------------------ finishing (non-preview)
    import pipeline  # noqa: E402,F811
    exp = os.path.join(ROOT, 'export', NAME)
    tex_dir = os.path.join(exp, 'textures')
    os.makedirs(tex_dir, exist_ok=True)
    rdir = os.path.join(ROOT, 'renders', 'warlink')
    os.makedirs(rdir, exist_ok=True)

    # 1) the posed scene is for renders; rebuild clean, unposed pieces for baking/export
    for o in list(bpy.data.objects):
        if o.type in ('MESH', 'EMPTY') and not o.name.startswith('_'):
            bpy.data.objects.remove(o, do_unlink=True)
    col = stage.collection(NAME)
    left_parts = cleaver(col, mats, -1)
    grip_pt = (0.0, 0.0, GRIP_TOP - 0.18)
    pipeline.shift(left_parts, (0, 0, -grip_pt[2]))
    body = paint.join(left_parts, f'{NAME}_CleaverL')
    paint.unwrap(body)
    maps = paint.bake_maps(body, tex_dir, f'{NAME}_Cleaver', size=1024, samples=12)
    body.data.materials.clear()
    body.data.materials.append(paint.baked_material(f'{NAME}_CleaverBaked', maps))
    geo.shade_by_angle(body, 30)
    right_body = body.copy()
    right_body.data = body.data.copy()
    right_body.name = right_body.data.name = f'{NAME}_CleaverR'
    col.objects.link(right_body)
    right_body.scale = (-1, 1, 1)
    bpy.ops.object.select_all(action='DESELECT')
    right_body.select_set(True)
    bpy.context.view_layer.objects.active = right_body
    bpy.ops.object.transform_apply(scale=True)
    if not geo.mesh_health(right_body)['normals_outward']:
        right_body.data.flip_normals()
    eye_local = Vector((0, 0, EYE_Z - EYE_R * 0.55 - grip_pt[2]))
    atts = {}
    for cb, tag in ((body, 'L'), (right_body, 'R')):
        for an, loc in (('Grip', (0, 0, 0)), ('ChainEnd', tuple(eye_local)), ('VFX_Rivet', (0.225 * (1 if tag == 'L' else -1), 0, 1.19 - grip_pt[2])),
                        ('VFX_Edge', (-0.43 * (1 if tag == 'L' else -1), 0, 0.9 - grip_pt[2]))):
            e = pipeline.attachment(an, loc, col)
            e.name = f'{an}'  # Roblox Attachment names must match per part; Blender suffixes duplicates
            e.parent = cb
            atts.setdefault(tag, []).append(e)

    # 2) chain kit: one link + one brass ring baked together, then 11 rigid pieces skinned to 11 bones
    link_src = link_mesh('KitLink', col, mats['darksteel'])
    ring_src = link_mesh('KitRing', col, mats['gold_plain'], brass=True)
    ring_src.location = (0.4, 0, 0)
    pipeline.apply_all([ring_src])
    kit = paint.join([link_src, ring_src], f'{NAME}_ChainKit')
    paint.unwrap(kit)
    kit_maps = paint.bake_maps(kit, tex_dir, f'{NAME}_Chain', size=512, samples=12)
    kit.data.materials.clear()
    kit.data.materials.append(paint.baked_material(f'{NAME}_ChainBaked', kit_maps))
    bpy.ops.object.select_all(action='DESELECT')
    kit.select_set(True)
    bpy.context.view_layer.objects.active = kit
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    pieces = sorted([o for o in bpy.context.selected_objects], key=lambda o: o.matrix_world.translation.x)
    link_piece, ring_piece = pieces[0], pieces[-1]
    for pc in pieces:
        bpy.ops.object.select_all(action='DESELECT')
        pc.select_set(True)
        bpy.context.view_layer.objects.active = pc
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        pc.location = (0, 0, 0)
    # the runtime chain system (roblox/src/WarlinkChain.luau) clones these two meshes N times:
    # one steel link and one gold end link, origin at the centre, long axis +Z (Roblox +Y), frame in XZ (Roblox XY)
    link_piece.name = link_piece.data.name = f'{NAME}_ChainLink'
    ring_piece.name = ring_piece.data.name = f'{NAME}_ChainEndLink'
    order = [ring_piece] + [link_piece] * LINKS + [ring_piece]   # concept-length layout for the renders only

    # 3) export (unposed, origins at grips; chain straight in bind pose) + stats
    stage.export_fbx(os.path.join(exp, f'{NAME}_CleaverL.fbx'), [body] + atts['L'])
    stage.export_fbx(os.path.join(exp, f'{NAME}_CleaverR.fbx'), [right_body] + atts['R'])
    stage.export_fbx(os.path.join(exp, f'{NAME}_ChainLink.fbx'), [link_piece])
    stage.export_fbx(os.path.join(exp, f'{NAME}_ChainEndLink.fbx'), [ring_piece])
    import optimize  # noqa: E402
    stats = {
        'name': NAME,
        'triangles': {o.name: geo.tri_count([o]) for o in (body, right_body, link_piece, ring_piece)},
        'triangles_example_r6_chain_32_links': geo.tri_count([body, right_body]) + 30 * geo.tri_count([link_piece])
                                               + 2 * geo.tri_count([ring_piece]),
        'texture_size': {'cleavers_shared': 1024, 'chain': 512},
        'maps': {k: os.path.relpath(v, ROOT) for k, v in list(maps.items()) + [('Chain_' + k, v) for k, v in kit_maps.items()]},
        'health': {o.name: geo.mesh_health(o) for o in (body, right_body, link_piece, ring_piece)},
        'topology': {o.name: optimize.topology_report(o) for o in (body, right_body, link_piece, ring_piece)},
        'chain': {'system': 'runtime: roblox/src/WarlinkChain.luau clones ChainLink/ChainEndLink LinkCount times',
                  'pitch_studs': round(PITCH, 4), 'link_outer': [LINK_W, LINK_LEN, LINK_WIRE],
                  'concept_length_render_pieces': len(order), 'concept_length_studs': round(len(order) * PITCH, 3),
                  'r6_note': 'set Tool attribute LinkCount from tools/MeasureHandSpan (R6 estimate ~30-35)'},
        'attachments': {'cleaver': {'Grip': [0, 0, 0], 'ChainEnd': [round(c, 4) for c in eye_local]}},
    }
    with open(os.path.join(exp, f'{NAME}_stats.json'), 'w') as fh:
        json.dump(stats, fh, indent=1)
    src_dir = os.path.join(ROOT, 'source')
    os.makedirs(src_dir, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(src_dir, f'{NAME}.blend'))
    print(json.dumps(stats, indent=1))

    # 4) presentation scene: concept pose with baked materials, separate posed link objects
    link_piece.hide_render = ring_piece.hide_render = True
    piv = {}
    for cb, s in ((body, -1), (right_body, 1)):
        p_ = bpy.data.objects.new(f'Pose{cb.name}', None)
        bpy.context.scene.collection.objects.link(p_)
        cb.parent = p_
        piv[s] = p_

    def pose(span, angle, lift=0.0):
        for s, p_ in piv.items():
            p_.location = (s * span / 2, 0, -eye_local.z + lift)
            p_.rotation_euler = (0, math.radians(s * angle), 0)
        bpy.context.view_layer.update()

    show_links = []
    for i, src in enumerate(order):
        c = src.copy()
        c.data = src.data
        c.hide_render = False
        bpy.context.scene.collection.objects.link(c)
        show_links.append(c)

    def ends():
        return (body.matrix_world @ eye_local, right_body.matrix_world @ eye_local)

    def place(pts):
        for i, o in enumerate(show_links):
            p0, p1 = pts[i], pts[i + 1]
            t = (p1 - p0).normalized()
            q = Vector((0, 0, 1)).rotation_difference(t)
            # kit pieces were authored with long axis on Z (link) / ring in XZ plane
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = Quaternion(t, math.radians(90 if i % 2 else 0)) @ q
            o.location = (p0 + p1) / 2

    pose(2.3, 24)
    a_, b_ = ends()
    pts = solve_chain(a_, b_, len(order) + 1, PITCH)
    prev = None
    for _ in range(240):
        pts, prev = solve_chain(a_, b_, len(order) + 1, PITCH, prev=pts, prev2=prev), pts
    place(pts)
    meshes = [body, right_body] + show_links
    pipeline.acceptance_renders(NAME, meshes, None, rdir, samples=40)
    stage.set_mood('showcase')
    stage.ortho_camera(meshes, 'three_quarter', res=(1400, 1100))
    stage.render(os.path.join(rdir, f'{NAME}_showcase.png'), samples=96)

    if '--no-turntable' not in sys.argv:
        # motion demo: rest -> hands apart until TAUT (length check) -> gather (controlled slack) -> rest
        frames = 4 if os.environ.get('SMOKE') else 120
        chain_len = len(order) * PITCH
        sc = bpy.context.scene
        sc.frame_start, sc.frame_end = 1, frames
        prev = None
        for f in range(1, frames + 1):
            t = (f - 1) / frames
            w = 0.5 - 0.5 * math.cos(2 * math.pi * t)               # 0 -> 1 -> 0
            span = 1.2 + w * 2.3                                    # wider than the chain at the peak
            ang = 24 - 30 * w
            lift = 0.25 * math.sin(2 * math.pi * t)
            pose(span, ang, lift)
            for p_ in piv.values():
                p_.keyframe_insert('location', frame=f)
                p_.keyframe_insert('rotation_euler', frame=f)
            a_, b_ = ends()
            gap = (b_ - a_).length
            if gap > chain_len:                                      # never stretch: hands clamp at taut
                mid = (a_ + b_) / 2
                dirv = (b_ - a_).normalized()
                a_, b_ = mid - dirv * chain_len / 2, mid + dirv * chain_len / 2
            pts, prev = (solve_chain(a_, b_, len(order) + 1, PITCH, prev=pts, prev2=prev, iters=40), pts)
            place(pts)
            for o in show_links:
                o.keyframe_insert('location', frame=f)
                o.keyframe_insert('rotation_quaternion', frame=f)
        cam = sc.camera
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = 5.2
        cam.location = (2.4, -7.0, 1.6)
        cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = 12
        sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = 1100, 800
        frame_dir = os.path.join(rdir, f'{NAME}_motion_frames')
        os.makedirs(frame_dir, exist_ok=True)
        sc.render.filepath = os.path.join(frame_dir, 'f_')
        bpy.ops.render.render(animation=True)
        import subprocess
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', os.path.join(frame_dir, 'f_%04d.png'),
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', os.path.join(rdir, f'{NAME}_motion.mp4')], check=True)
        import shutil
        shutil.rmtree(frame_dir, ignore_errors=True)
