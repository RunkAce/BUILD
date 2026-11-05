"""AR_02 M4A1 - PIXELGATE factory v1 hero (vertical slice).

  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_m4a1.py [--preview] [--no-renders]

Original factory design inspired by the real carbine silhouette (no manufacturer markings).
Separate animated parts, each rigidly skinned to its own bone in ONE mesh:
  Root, Trigger, Magazine, ChargingHandle, BoltCarrier (visible through the ejection port), DustCover, Selector.
Weapon-side animation takes (FBX actions): Fire, DryFire, Reload_Tactical, Reload_Empty, Inspect, Idle.
Hand/arm motion (Equip, Walk, Sprint, ADS, Holster, PortalTransit) belongs to the game's viewmodel arm rig.
"""
import bpy  # noqa: F401  (first: makes bmesh importable)
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gunkit as G  # noqa: E402
import geo  # noqa: E402
import optimize  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

ID, NAME = 'AR_02', 'M4A1'
ROOT_DIR = os.path.join(os.path.dirname(HERE), 'Weapons', ID)
PREVIEW = '--preview' in sys.argv
FPS = 30

# ------------------------------------------------------------------ real-world layout (mm), stylised on top
# Reference: M4 carbine 838 mm overall (stock extended), 368 mm barrel (14.5 in), ~25 deg pistol-grip rake,
# lower receiver ~7.5-8.5 in, magwell ~1.25 in wide. x = mm from butt (0) to muzzle (838), z = mm from bore line.
S = 3.0 / 838.0              # studs per mm  (gun = 3.0 studs, sized for R6/R15 viewmodels)
W = 1.2 * S                  # stylisation: widths 20% chunkier than real
BORE = 0.0


def mm(pts):
    return G.P([(x * S, z * S) for x, z in pts])


def mmbox(x0, z0, x1, z1, r=0.0):
    return G.rbox(x0 * S, z0 * S, x1 * S, z1 * S, r * S)


GRIP = (300 * S, 0.0, -92 * S)    # centre of the right hand on the pistol grip -> Root/origin


def build():
    stage.reset_scene()
    stage.neutral_stage()
    col = stage.collection(NAME)
    M = G.mats(NAME, {
        'receiver': ('anodized', 'Body'), 'furniture': ('polymer', 'Furniture'), 'steel': ('blacksteel', 'MetalAccent'),
        'bright': ('steel', 'MetalAccent'), 'mag': ('anodized', 'Magazine'),
        'round': ('polymer', 'Furniture', False), 'roundsteel': ('blacksteel', 'MetalAccent', False)})
    B = {k: [] for k in ('Root', 'Trigger', 'Magazine', 'ChargingHandle', 'BoltCarrier', 'DustCover', 'Selector')}
    R = B['Root']

    def side(name, shape, width_mm, mat, chamfer_mm=3.5, y_mm=0.0, bone='Root'):
        B[bone].append(G.side(name, shape, width_mm * W, col, mat, chamfer=chamfer_mm * W, y=y_mm * W))

    def front(name, shape_yz, x0_mm, x1_mm, mat, chamfer_mm=2.0, bone='Root'):
        """Rear-view part: 2D (y, z) shape extruded along x (sight towers, ears) - openings run along the bore."""
        o = G.side(name, shape_yz, (x1_mm - x0_mm) * S, col, mat, chamfer=chamfer_mm * S)
        o.rotation_euler = (0, 0, math.radians(90))      # shape u -> y, thickness -> x
        o.location = ((x0_mm + x1_mm) / 2 * S, 0, 0)
        B[bone].append(o)

    def round_x(name, x0, prof, z_mm=0.0, y_mm=0.0, mat=None, seg=12, bone='Root'):
        o = G.tube(name, [(r * W, dx * S) for r, dx in prof], col, mat, segments=seg)
        o.location = (x0 * S, y_mm * W, z_mm * S)
        B[bone].append(o)

    # ---- upper receiver (flat-top), ejection port as a real opening, port backing on the left
    port = mmbox(375, -10, 440, 12, 3)
    side('Upper', mm([(292, -18), (475, -18), (476, 22), (296, 22), (290, 14)]).difference(port), 36, M['receiver'], 4)
    side('PortBacking', port.buffer(2 * S), 4, M['receiver'], 1, y_mm=-16)
    side('UpperRail', mmbox(294, 21, 472, 30, 1), 26, M['receiver'], 2)
    side('RailTeeth', G.teeth_along_x(296 * S, 470 * S, 10 * S, 5 * S, 6 * S, 29 * S), 26, M['receiver'], 1.2)
    # brass deflector + forward assist: RIGHT side, just behind the port (not inline with the stock)
    side('Deflector', mm([(362, -2), (374, -2), (374, 16), (366, 18)]), 10, M['receiver'], 2, y_mm=19)
    round_x('ForwardAssist', 330, [(0, 0), (8.5, 0), (9.5, 4), (9.5, 26), (8, 30), (0, 30)], z_mm=9, y_mm=19,
            mat=M['receiver'], seg=10)
    round_x('FAButton', 324, [(0, 0), (6.5, 0), (7, 2), (7, 7), (0, 7)], z_mm=9, y_mm=19, mat=M['steel'], seg=10)
    # rear sight: base on the rail (side profile) + aperture tower built in REAR view, so the peep hole runs
    # ALONG the sight line (x), between two protective ears; centre z 53 = front post tip -> clear sight picture
    side('RearSightBase', mm([(300, 30), (336, 30), (336, 38), (330, 42), (306, 42), (300, 38)]), 26, M['receiver'], 2.5)
    front('RearSightTower', G.rbox(-13 * W, 38 * S, 13 * W, 64 * S, 1.5 * S).difference(
        G.rbox(-6 * W, 59 * S, 6 * W, 70 * S, 1 * S)).difference(Point(0, 53 * S).buffer(3.8 * S, 12)),
        312, 326, M['receiver'], 2)

    # ---- lower receiver: magwell (with flare), trigger area, grip seat behind the trigger guard
    side('Lower', mm([(285, -17), (482, -17), (482, -34), (472, -36), (475, -88), (390, -88), (393, -56), (340, -56),
                      (334, -46), (290, -46), (285, -36)]), 38, M['receiver'], 4)
    side('MagwellFrame', mm([(390, -56), (476, -56), (478, -90), (388, -90)]).difference(mmbox(400, -82, 466, -62, 4)),
         42, M['receiver'], 2.5)
    side('TriggerGuard', mm([(393, -56), (393, -80), (346, -80), (334, -64), (334, -56)]).difference(
        mm([(387, -59), (387, -74), (349, -74), (341, -62), (341, -59)])), 12, M['receiver'], 2)
    for nm, x, z in (('TakedownPin', 296, -26), ('PivotPin', 474, -26), ('TriggerPin', 365, -32), ('HammerPin', 340, -32)):
        o = G.pin(nm, x * S, z * S, 3.6 * S, 44 * W, col, M['steel'])
        R.append(o)
    side('BoltCatch', mm([(396, -22), (412, -20), (412, -12), (398, -14)]), 3, M['steel'], 1, y_mm=-20)
    round_x('MagRelease', 395, [(0, 0), (5, 0), (5, 1), (0, 1)], z_mm=-25, mat=M['steel'], seg=8)
    B['Root'][-1].rotation_euler = (0, 0, math.radians(90))
    B['Root'][-1].location = (395 * S, 21 * W, -25 * S)

    # ---- pistol grip: ~25 deg rake, finger groove, beavertail tucked under the lower (seated, not floating)
    side('PistolGrip', mm([(284, -42), (335, -42), (332, -57), (326, -69), (327, -79), (318, -100), (301, -138),
                           (297, -150), (257, -153), (253, -146), (268, -108), (281, -70), (285, -55), (281, -48)]),
         32, M['furniture'], 6)
    side('GripTexture', mm([(286, -72), (318, -74), (300, -126), (270, -130)]), 34, M['furniture'], 2)

    # ---- buffer tube (coaxial with the bore) + castle nut + collapsible stock
    round_x('BufferTube', 110, [(0, 0), (15, 0), (15, 172), (0, 172)], z_mm=2, mat=M['roundsteel'])
    round_x('CastleNut', 274, [(0, 0), (18, 0), (19, 3), (19, 10), (18, 12), (0, 12)], z_mm=2, mat=M['steel'], seg=8)
    side('Stock', mm([(0, -88), (10, -93), (55, -63), (100, -37), (176, -21), (176, 21), (60, 29), (8, 33),
                      (0, 29)]).difference(mmbox(58, -38, 102, -22, 7)), 44, M['furniture'], 7)
    side('StockShell', mm([(62, -15), (178, -15), (178, 25), (66, 28)]), 50, M['furniture'], 5)   # tube housing layer
    side('ButtPad', mm([(-7, -89), (3, -95), (3, 34), (-7, 30)]), 48, M['steel'], 3)
    side('StockLever', mm([(120, -34), (170, -24), (170, -18), (124, -27)]), 14, M['steel'], 2)

    # ---- round ribbed handguard (carbine length), delta ring, front sight base / A-frame, barrel, birdcage
    ribs = [(0, 0), (29, 0)]
    for i in range(14):
        x = 6 + i * 12
        ribs += [(29, x), (27, x + 3), (27, x + 9), (29, x + 12)]
    ribs += [(29, 175), (0, 175)]
    round_x('Handguard', 482, ribs, z_mm=-3, mat=M['round'], seg=14)
    round_x('DeltaRing', 470, [(0, 0), (33, 0), (34, 3), (34, 12), (31, 15), (0, 15)], z_mm=-3, mat=M['steel'], seg=16)
    round_x('HandguardCap', 652, [(0, 0), (30, 0), (30, 7), (0, 7)], z_mm=-3, mat=M['steel'], seg=14)
    # front sight: A-frame body (side) stays below the sight line; ears + post built in rear view with an open
    # channel along x, post tip at z 53 (aperture centre) so it sits in the middle of the peep hole
    side('FrontSightBase', mm([(657, -14), (690, -14), (690, 14), (684, 14), (680, 38), (666, 38), (662, 14),
                               (657, 14)]).difference(mm([(668, 18), (678, 18), (676, 31), (670, 31)])), 26,
         M['steel'], 3)
    front('FrontSightEars', G.rbox(-12 * W, 36 * S, 12 * W, 62 * S, 1.5 * S).difference(
        G.rbox(-6.5 * W, 41 * S, 6.5 * W, 70 * S, 1.5 * S)), 666, 680, M['steel'], 2)
    front('SightPost', G.rbox(-1.8 * W, 38 * S, 1.8 * W, 53 * S, 0.4 * S), 670, 676, M['bright'], 0.6)
    round_x('Barrel', 470, [(0, 0), (9, 0), (9, 220), (8.2, 224), (8.2, 313), (0, 313)], mat=M['roundsteel'], seg=12)
    hider = [(0, 0), (11, 0)]
    for i in range(3):
        x = 6 + i * 15
        hider += [(11, x), (9, x + 2), (9, x + 11), (11, x + 13)]
    hider += [(11, 52), (10, 55), (0, 55)]
    round_x('FlashHider', 783, hider, mat=M['roundsteel'], seg=8)

    # ---- moving parts
    side('Trigger', mm([(361, -38), (369, -38), (369, -50), (365, -62), (358, -71), (354, -69), (360, -58), (362, -48)]),
         7, M['bright'], 1.2, bone='Trigger')
    side('Selector', mm([(312, -32), (330, -28), (330, -23), (312, -26)]), 3, M['steel'], 0.8, y_mm=-21,
         bone='Selector')
    side('ChargingHandle', mmbox(276, 17, 300, 27, 2), 14, M['steel'], 2, bone='ChargingHandle')
    side('ChargingLatch', mmbox(276, 16, 287, 28, 3), 50, M['steel'], 2.5, bone='ChargingHandle')
    side('BoltCarrier', mmbox(360, -9, 455, 11, 3), 26, M['bright'], 2.5, bone='BoltCarrier')
    side('DustCover', mmbox(372, -12, 443, 14, 2), 4, M['receiver'], 1, y_mm=19, bone='DustCover')
    mag = mm([(398, -50), (468, -50), (470, -110), (480, -170), (496, -226), (434, -238), (424, -226), (412, -170),
              (402, -110)])
    side('Magazine', mag, 28, M['mag'], 4, bone='Magazine')
    ribs = unary_union([mm([(395, -120 - i * 22), (505, -120 - i * 22), (505, -112 - i * 22), (395, -112 - i * 22)])
                        for i in range(4)]).intersection(mag.buffer(-4 * S))
    side('MagRibs', ribs, 30, M['mag'], 1.5, bone='Magazine')
    side('MagBase', mm([(430, -250), (502, -238), (500, -226), (428, -236)]), 32, M['furniture'], 3, bone='Magazine')
    for k in B:
        G.apply(B[k])
    return col, M, B


BONES = {   # bone: (head, tail, parent) in authoring coords; tails point +Z (see gunkit.rig axes note)
    'Root': ((GRIP[0], 0, GRIP[2]), (GRIP[0], 0, GRIP[2] + 0.2), None),
    'Trigger': ((365 * S, 0, -36 * S), (365 * S, 0, -36 * S + 0.1), 'Root'),
    'Magazine': ((433 * S, 0, -50 * S), (433 * S, 0, -50 * S + 0.1), 'Root'),
    'ChargingHandle': ((288 * S, 0, 22 * S), (288 * S, 0, 22 * S + 0.1), 'Root'),
    'BoltCarrier': ((406 * S, 0, 0.0), (406 * S, 0, 0.1), 'Root'),
    'DustCover': ((408 * S, 19 * W, -12 * S), (408 * S, 19 * W, -12 * S + 0.1), 'Root'),
    'Selector': ((314 * S, -21 * W, -29 * S), (314 * S, -21 * W, -29 * S + 0.1), 'Root'),
}
# pose axes for a +Z-pointing bone (roll 0): loc (dx, dz, -dy) world; rot about world Y -> (0,0,-a), world X -> (a,0,0)


def animate(arm):
    acts = {}
    acts['Idle'] = G.new_action(arm, 'Idle')
    for b in BONES:                                       # every part keyed at rest (no pose bleeding between takes)
        for f in (1, 30):
            G.key(arm, b, f, loc=(0, 0, 0), rot=(0, 0, 0))

    acts['Fire'] = G.new_action(arm, 'Fire')                     # 1 shot @ ~800 rpm: 2.25 frames ~ use 4-frame cycle
    for f, tr, bolt, dc in ((1, 0, 0, 0), (2, -14, -0.13, -100), (3, -14, -0.215, -100), (4, -6, -0.05, -100), (5, 0, 0, -100)):
        G.key(arm, 'Trigger', f, rot=(0, 0, -tr))
        G.key(arm, 'BoltCarrier', f, loc=(bolt, 0, 0))
        G.key(arm, 'DustCover', f, rot=(dc, 0, 0))

    acts['DryFire'] = G.new_action(arm, 'DryFire')
    for f, tr in ((1, 0), (3, -14), (8, 0)):
        G.key(arm, 'Trigger', f, rot=(0, 0, -tr))

    def mag_out_in(start, out_end, in_start, end):
        G.key(arm, 'Magazine', start, loc=(0, 0, 0), rot=(0, 0, 0))
        G.key(arm, 'Magazine', start + 3, loc=(0, -0.04, 0), rot=(0, 0, 0))                    # unseat
        G.key(arm, 'Magazine', out_end, loc=(-0.15, -0.9, 0.05), rot=(0, 0, 18))               # out & away (hand takes it)
        G.key(arm, 'Magazine', in_start, loc=(-0.12, -0.75, 0.05), rot=(0, 0, 12))             # fresh mag comes in
        G.key(arm, 'Magazine', end - 4, loc=(0, -0.05, 0), rot=(0, 0, 0))
        G.key(arm, 'Magazine', end - 2, loc=(0, 0.01, 0), rot=(0, 0, 0))                       # seat with a tap
        G.key(arm, 'Magazine', end, loc=(0, 0, 0), rot=(0, 0, 0))

    acts['Reload_Tactical'] = G.new_action(arm, 'Reload_Tactical')     # 2.0 s
    mag_out_in(6, 22, 32, 52)
    G.key(arm, 'Root', 1, loc=(0, 0, 0))
    G.key(arm, 'Root', 60, loc=(0, 0, 0))

    acts['Reload_Empty'] = G.new_action(arm, 'Reload_Empty')           # 2.6 s: bolt locked back, then released
    for f in (1, 60):
        G.key(arm, 'BoltCarrier', f, loc=(-0.2, 0, 0))
    G.key(arm, 'DustCover', 1, rot=(-100, 0, 0))
    mag_out_in(6, 22, 32, 52)
    G.key(arm, 'ChargingHandle', 56, loc=(0, 0, 0))
    G.key(arm, 'ChargingHandle', 62, loc=(-0.2, 0, 0))
    G.key(arm, 'BoltCarrier', 62, loc=(-0.2, 0, 0))
    G.key(arm, 'ChargingHandle', 66, loc=(-0.2, 0, 0))
    G.key(arm, 'ChargingHandle', 69, loc=(0, 0, 0))
    G.key(arm, 'BoltCarrier', 66, loc=(-0.2, 0, 0))
    G.key(arm, 'BoltCarrier', 68, loc=(0, 0, 0))
    G.key(arm, 'DustCover', 78, rot=(-100, 0, 0))

    acts['Inspect'] = G.new_action(arm, 'Inspect')                     # 3.0 s, never fires
    for f, sel in ((1, 0), (20, 0), (26, -60), (40, -60), (46, 0), (90, 0)):
        G.key(arm, 'Selector', f, rot=(0, 0, sel))
    for f, chv in ((1, 0), (52, 0), (58, -0.12), (66, -0.12), (70, 0), (90, 0)):
        G.key(arm, 'ChargingHandle', f, loc=(chv, 0, 0))
    for f, bv in ((1, 0), (56, 0), (59, -0.1), (66, -0.1), (69, 0), (90, 0)):
        G.key(arm, 'BoltCarrier', f, loc=(bv, 0, 0))
    for f, d in ((1, 0), (56, 0), (58, -100), (90, -100)):
        G.key(arm, 'DustCover', f, rot=(d, 0, 0))
    for a in acts.values():
        for fc in _fcurves(a):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
    return acts


def _fcurves(act):
    if hasattr(act, 'fcurves') and act.fcurves:
        return list(act.fcurves)
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', []):
                out += list(bag.fcurves)
    return out


# animation notify events (seconds) for the game framework: ammo changes ONLY at these events
EVENTS = {
    'Fire': {'Muzzle': 0.0, 'Eject': 0.05},
    'Reload_Tactical': {'MagOut': 0.3, 'MagIn': 1.65, 'AmmoCommit': 1.7, 'End': 2.0},
    'Reload_Empty': {'MagOut': 0.3, 'MagIn': 1.65, 'BoltRelease': 2.2, 'AmmoCommit': 2.25, 'End': 2.6},
    'Inspect': {'End': 3.0},
}

def sight_check(mesh, rv):
    """Sight picture from the ADS attachment down the bore + ray test: the post must be the first thing the
    centre line meets, and lines just above/beside the post must escape (nothing blocking the sight line)."""
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    ads = bpy.data.objects['ADS'].matrix_world.translation.copy()
    fwd = (bpy.data.objects['Muzzle'].matrix_world.translation - ads)
    fwd.z = 0
    fwd.normalize()
    up = Vector((0, 0, 1))
    right = fwd.cross(up).normalized()
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(mesh, dg)
    post_d = (673 - 312) * S
    res = {}
    for tag, dz, dy, want_hit in (('centre_below_tip', -1.5, 0, True), ('above_tip', 2.5, 0, False),
                                  ('left_of_post', 0, -3.5, False), ('right_of_post', 0, 3.5, False)):
        # aim at a point beside / above the post tip at the post's distance
        tgt = ads + fwd * post_d + up * (dz * S) + right * (dy * W)
        d = (tgt - ads).normalized()
        hit = tree.ray_cast(ads + d * 1e-4, d, 10.0)
        dist = None if hit[0] is None else round((hit[0] - ads).length / S, 1)
        ok = (dist is not None and abs(dist - (post_d / S)) < 8) if want_hit else (dist is None)
        res[tag] = {'hit_mm': dist, 'ok': ok}
    print('SIGHT_CHECK', json.dumps(res))
    sc = bpy.context.scene
    cam = sc.camera
    cam.data.type = 'PERSP'
    cam.data.lens = 60
    cam.data.clip_start = 0.002
    cam.location = ads - fwd * 0.12
    cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    stage.render(os.path.join(rv, f'{ID}_sight_picture.png'), samples=32)
    return res

ATTACH = {   # authoring coords (real-world placements)
    'GripRight': GRIP, 'RightHandIK': GRIP, 'LeftHandIK': (590 * S, 0.0, -32 * S), 'GripLeft': (590 * S, 0.0, -32 * S),
    'Muzzle': (838 * S, 0.0, 0.0), 'ADS': (312 * S, 0.0, 53 * S), 'Ejection': (408 * S, 20 * W, 0.0),
    'MagazineSeat': (433 * S, 0.0, -50 * S),
}


def to_game(v):
    """authoring (x muzzle+, y right, z up) -> exported Blender coords (muzzle -Y, right +X, up +Z), origin at grip."""
    x, y, z = v[0] - GRIP[0], v[1] - GRIP[1], v[2] - GRIP[2]
    return (y, -x, z)


def orient(objs):
    """Move grip to origin and rotate so the muzzle points -Y (Roblox -Z forward)."""
    m = Matrix.Rotation(math.radians(-90), 4, 'Z') @ Matrix.Translation(Vector(GRIP) * -1)
    for o in objs:
        o.matrix_world = m @ o.matrix_world
    G.apply(objs)


if __name__ == '__main__':
    col, M, B = build()
    allp = [o for v in B.values() for o in v]
    if PREVIEW:
        out = os.path.join(ROOT_DIR, 'Review', 'blockout')
        os.makedirs(out, exist_ok=True)
        print('tris', geo.tri_count(allp))
        for v in ('front', 'three_quarter'):
            stage.ortho_camera(allp, v, res=(1100, 560))
            stage.render(os.path.join(out, f'{v}.png'), samples=24)
        sys.exit(0)
    # optimise each static group before joining (moving parts stay whole)
    removed = 0
    orient(allp)
    for k, v in B.items():
        if len(v) > 1:
            j = paint.join(v, f'_{k}')
            removed += optimize.remove_hidden_faces(j)
            B[k] = [j]
    bone_heads = {b: (to_game(h), to_game(t), p) for b, (h, t, p) in BONES.items()}
    mesh, arm = G.rig(ID, col, B, bone_heads)
    paint.unwrap(mesh)
    tex = os.path.join(ROOT_DIR, 'Textures')
    maps = paint.bake_maps(mesh, tex, f'{ID}_Factory', size=1024, samples=32)
    G.bake_mask(mesh, os.path.join(tex, f'{ID}_Factory_MaskMap.png'))
    mesh.data.materials.clear()
    mesh.data.materials.append(paint.baked_material(f'{ID}_Baked', maps))
    acts = animate(arm)
    # attachments as empties parented to Root bone
    att_objs = []
    for an, p in ATTACH.items():
        e = bpy.data.objects.new(an, None)
        e.empty_display_size = 0.05
        col.objects.link(e)
        e.location = to_game(p)
        e.parent = arm
        e.parent_type = 'BONE'
        e.parent_bone = 'Root'
        e.matrix_world = Matrix.Translation(to_game(p))
        att_objs.append(e)
    exp = os.path.join(ROOT_DIR, 'Exports')
    os.makedirs(exp, exist_ok=True)
    arm.animation_data.action = acts['Idle']
    bpy.ops.object.select_all(action='DESELECT')
    for o in [mesh, arm] + att_objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(exp, f'{ID}_Viewmodel.fbx'), use_selection=True,
                             object_types={'MESH', 'ARMATURE', 'EMPTY'}, apply_unit_scale=True,
                             global_scale=stage.STUD_IN_METRES, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', add_leaf_bones=False, bake_anim=True,
                             bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
                             bake_anim_force_startend_keying=True, path_mode='STRIP')
    # world model: static, lighter (decimated copy, same UVs/textures)
    wm = mesh.copy()
    wm.data = mesh.data.copy()
    wm.name = wm.data.name = f'{ID}_World'
    col.objects.link(wm)
    wm.parent = None
    wm.modifiers.clear()
    wm.matrix_world = mesh.matrix_world.copy()
    dec = wm.modifiers.new('Dec', 'DECIMATE')
    dec.ratio = 0.45
    dec.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = wm
    bpy.ops.object.modifier_apply(modifier='Dec')
    for vg in list(wm.vertex_groups):
        wm.vertex_groups.remove(vg)
    stage.export_fbx(os.path.join(exp, f'{ID}_World.fbx'), [wm])
    stats = {
        'id': ID, 'name': NAME,
        'viewmodel_triangles': geo.tri_count([mesh]), 'world_triangles': geo.tri_count([wm]),
        'hidden_faces_removed': removed, 'texture': '1024 PBR + MaskMap',
        'bones': list(BONES), 'animations': list(acts), 'events_seconds': EVENTS,
        'attachments': {k: [round(c, 4) for c in to_game(v)] for k, v in ATTACH.items()},
        'topology': optimize.topology_report(mesh),
        'length_studs': round(stage.bounds([mesh])[1].y - stage.bounds([mesh])[0].y, 3),
    }
    with open(os.path.join(ROOT_DIR, f'{ID}_stats.json'), 'w') as fh_:
        json.dump(stats, fh_, indent=1)
    src = os.path.join(ROOT_DIR, 'Source')
    os.makedirs(src, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(src, f'{ID}.blend'))
    print(json.dumps({k: stats[k] for k in ('viewmodel_triangles', 'world_triangles', 'length_studs')}))
    if '--no-renders' in sys.argv:
        sys.exit(0)
    # review shots: side beauty, 3/4, and a reload/inspect strip
    rv = os.path.join(ROOT_DIR, 'Review')
    os.makedirs(rv, exist_ok=True)
    arm.animation_data.action = acts['Idle']
    bpy.context.scene.frame_set(1)
    for v, res in (('side', (1400, 700)), ('three_quarter', (1400, 800))):
        view = 'side' if v == 'side' else 'three_quarter'
        stage.ortho_camera([mesh], view, res=res)
        stage.render(os.path.join(rv, f'{ID}_{v}.png'), samples=48)
    sight_check(mesh, rv)
    for actn, frames in (('Reload_Empty', (1, 14, 22, 40, 52, 63, 68)), ('Inspect', (1, 30, 58, 66))):
        arm.animation_data.action = acts[actn]
        for f in frames:
            bpy.context.scene.frame_set(f)
            stage.ortho_camera([mesh], 'side', res=(700, 400), margin=1.25)
            stage.render(os.path.join(rv, f'{ID}_{actn}_f{f:02d}.png'), samples=12)
