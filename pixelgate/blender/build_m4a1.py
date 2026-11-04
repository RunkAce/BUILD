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

BORE = 0.125                 # bore line height (authoring z)
GRIP = (1.0, 0.0, -0.20)     # right-hand grip point -> Root/origin


def build():
    stage.reset_scene()
    stage.neutral_stage()
    col = stage.collection(NAME)
    M = G.mats(NAME, {
        'receiver': ('anodized', 'Body'), 'furniture': ('polymer', 'Furniture'), 'steel': ('blacksteel', 'MetalAccent'),
        'bright': ('steel', 'MetalAccent'), 'mag': ('anodized', 'Magazine')})
    B = {k: [] for k in ('Root', 'Trigger', 'Magazine', 'ChargingHandle', 'BoltCarrier', 'DustCover', 'Selector')}
    R = B['Root']

    # ---- upper receiver: flat-top with ejection port through-hole (bolt carrier shows through it)
    upper = G.P([(0.97, 0.05), (1.62, 0.05), (1.64, 0.08), (1.64, 0.205), (0.97, 0.205)])
    port = G.rbox(1.15, 0.085, 1.37, 0.165, 0.008)
    R.append(G.side('Upper', upper.difference(port), 0.13, col, M['receiver'], chamfer=0.02))
    R.append(G.side('PortCoverL', port.buffer(0.01), 0.012, col, M['receiver'], y=-0.059))      # left side closed
    # forward-assist housing (right side) + brass deflector
    R.append(G.tube('ForwardAssist', [(0.0, 0.0), (0.03, 0.0), (0.03, 0.09), (0.036, 0.1), (0.036, 0.13), (0.0, 0.13)],
                    col, M['receiver'], y=0.072, z=0.16, segments=10))
    R[-1].location = (0.98, 0.072, 0.16)
    R.append(G.side('Deflector', G.P([(1.08, 0.09), (1.15, 0.09), (1.15, 0.19), (1.1, 0.19)]), 0.03, col, M['receiver'],
                    y=0.075))
    # top rail with teeth (upper) + rear folding sight
    R.append(G.side('UpperRailBase', G.rbox(0.99, 0.2, 1.62, 0.235, 0.005), 0.085, col, M['receiver'], chamfer=0.008))
    R.append(G.side('UpperRailTeeth', G.teeth_along_x(1.0, 1.61, 0.042, 0.022, 0.03, 0.233), 0.085, col, M['receiver'],
                    chamfer=0.005))
    rs = G.P([(1.02, 0.262), (1.14, 0.262), (1.14, 0.3), (1.1, 0.36), (1.06, 0.36), (1.02, 0.3)]).difference(
        Point(1.08, 0.33, ).buffer(0.012, 8))
    R.append(G.side('RearSight', rs, 0.07, col, M['receiver'], chamfer=0.008))

    # ---- lower receiver with flared magwell, trigger guard, pistol grip
    lower = G.P([(0.95, 0.055), (1.5, 0.055), (1.5, -0.04), (1.44, -0.06), (1.43, -0.25), (1.19, -0.25), (1.17, -0.08),
                 (1.0, -0.09), (0.95, -0.03)])
    R.append(G.side('Lower', lower, 0.12, col, M['receiver'], chamfer=0.02))
    guard = G.P([(1.04, -0.09), (1.18, -0.09), (1.18, -0.2), (1.06, -0.2), (1.02, -0.16)]).difference(
        G.rbox(1.06, -0.18, 1.16, -0.1, 0.015))
    R.append(G.side('TriggerGuard', guard, 0.065, col, M['receiver'], chamfer=0.01))
    grip = G.P([(0.9, -0.07), (1.1, -0.08), (1.07, -0.17), (1.05, -0.24), (1.03, -0.27), (1.035, -0.32),
                (1.0, -0.46), (0.94, -0.49), (0.86, -0.47), (0.855, -0.43), (0.91, -0.3), (0.92, -0.2), (0.88, -0.12)])
    R.append(G.side('PistolGrip', grip, 0.115, col, M['furniture'], chamfer=0.022))
    # grip texture panels (shallow inlays)
    R.append(G.side('GripPanel', G.P([(0.93, -0.2), (1.02, -0.19), (0.98, -0.42), (0.92, -0.42)]), 0.125, col,
                    M['furniture'], chamfer=0.008))
    # mag release (right) + selector axle
    R.append(G.side('MagRelease', G.rbox(1.44, -0.02, 1.48, 0.02, 0.008), 0.15, col, M['steel'], chamfer=0.006))

    # ---- buffer tube + collapsible stock
    R.append(G.tube('BufferTube', [(0.0, 0.0), (0.055, 0.0), (0.055, 0.66), (0.06, 0.68), (0.06, 0.70), (0.0, 0.70)],
                    col, M['receiver'], segments=12))
    R[-1].location = (0.28, 0.0, BORE)
    stock = G.P([(0.0, -0.2), (0.05, -0.215), (0.12, -0.2), (0.36, -0.01), (0.62, 0.06), (0.62, 0.19), (0.3, 0.205),
                 (0.05, 0.21), (0.0, 0.2)]).difference(G.rbox(0.14, -0.08, 0.3, 0.04, 0.03))
    R.append(G.side('Stock', stock, 0.12, col, M['furniture'], chamfer=0.024))
    R.append(G.side('ButtPad', G.P([(-0.03, -0.215), (0.02, -0.225), (0.02, 0.215), (-0.03, 0.205)]), 0.13, col,
                    M['steel'], chamfer=0.012))
    R.append(G.side('StockLever', G.P([(0.4, -0.0), (0.56, 0.04), (0.56, 0.0), (0.42, -0.04)]), 0.05, col, M['steel'],
                    chamfer=0.006))

    # ---- handguard (slotted), rail, gas-block front sight, barrel, flash hider
    hg = G.rbox(1.64, 0.0, 2.27, 0.245, 0.04)
    slots = unary_union([G.rbox(1.72 + i * 0.1, 0.04, 1.78 + i * 0.1, 0.075, 0.016) for i in range(5)] +
                        [G.rbox(1.72 + i * 0.1, 0.16, 1.78 + i * 0.1, 0.195, 0.016) for i in range(5)])
    R.append(G.side('Handguard', hg.difference(slots), 0.16, col, M['receiver'], chamfer=0.018))
    R.append(G.side('HandguardRail', G.rbox(1.65, 0.24, 2.26, 0.265, 0.004), 0.085, col, M['receiver'], chamfer=0.006))
    R.append(G.side('HandguardTeeth', G.teeth_along_x(1.66, 2.25, 0.042, 0.022, 0.03, 0.263), 0.085, col,
                    M['receiver'], chamfer=0.005))
    R.append(G.side('DeltaRing', G.rbox(1.6, -0.01, 1.66, 0.255, 0.01), 0.175, col, M['steel'], chamfer=0.01))
    fs = G.P([(2.27, 0.06), (2.36, 0.06), (2.36, 0.18), (2.33, 0.42), (2.3, 0.42), (2.27, 0.18)]).difference(
        G.rbox(2.29, 0.25, 2.34, 0.36, 0.01))
    R.append(G.side('FrontSight', fs, 0.08, col, M['steel'], chamfer=0.01))
    R.append(G.side('SightPost', G.rbox(2.305, 0.25, 2.325, 0.37, 0.002), 0.018, col, M['bright'], chamfer=0.003))
    R.append(G.tube('Barrel', [(0.0, 0.0), (0.036, 0.0), (0.036, 0.36), (0.032, 0.38), (0.032, 0.55), (0.0, 0.55)],
                    col, M['steel'], segments=12))
    R[-1].location = (2.25, 0.0, BORE)
    fh = G.tube('FlashHider', [(0.0, 0.0), (0.045, 0.0), (0.05, 0.02), (0.05, 0.13), (0.044, 0.15), (0.0, 0.15)],
                col, M['steel'], segments=6)
    fh.location = (2.8, 0.0, BORE)
    R.append(fh)

    # ---- detail pass: pins, bolt catch, raised panels, seams, cheek riser, sling slot, end cap
    for nm, x, z in (('PivotPin', 1.47, 0.03), ('TakedownPin', 0.99, 0.03), ('TriggerPin', 1.125, -0.045),
                     ('HammerPin', 1.03, -0.045)):
        R.append(G.pin(nm, x, z, 0.014 if 'Pin' in nm[:6] else 0.011, 0.135, col, M['steel']))
    R.append(G.side('BoltCatch', G.P([(1.42, -0.02), (1.47, -0.02), (1.47, 0.03), (1.43, 0.04)]), 0.012, col, M['steel'],
                    y=-0.066, chamfer=0.003))
    R.append(G.side('MagwellPanel', G.P([(1.17, -0.06), (1.45, -0.06), (1.44, -0.24), (1.19, -0.24)]).difference(
        G.rbox(1.22, -0.2, 1.4, -0.1, 0.02)), 0.15, col, M['receiver'], chamfer=0.01))
    R.append(G.side('LowerPanel', G.rbox(1.0, -0.075, 1.17, 0.035, 0.012), 0.145, col, M['receiver'], chamfer=0.01))
    R.append(G.side('UpperSeam', G.rbox(0.97, 0.045, 1.62, 0.058, 0.003), 0.136, col, M['steel'], chamfer=0.003))
    R.append(G.side('CheekRiser', G.P([(0.06, 0.2), (0.5, 0.18), (0.5, 0.235), (0.08, 0.25)]), 0.105, col,
                    M['furniture'], chamfer=0.018))
    R.append(G.side('SlingSlot', G.rbox(0.03, -0.17, 0.09, -0.12, 0.01).difference(G.rbox(0.045, -0.16, 0.075, -0.13, 0.006)),
                    0.13, col, M['steel'], chamfer=0.005))
    R.append(G.side('ButtRibs', unary_union([G.rbox(-0.035, -0.18 + 0.07 * i, 0.0, -0.16 + 0.07 * i, 0.004)
                                              for i in range(6)]), 0.14, col, M['steel'], chamfer=0.004))
    R.append(G.side('EndCap', G.rbox(2.24, 0.005, 2.29, 0.24, 0.02), 0.17, col, M['steel'], chamfer=0.012))
    R.append(G.side('GasBlock', G.rbox(2.26, 0.075, 2.37, 0.175, 0.012), 0.09, col, M['steel'], chamfer=0.01))

    # ---- moving parts
    trig = G.P([(1.115, -0.085), (1.14, -0.085), (1.135, -0.13), (1.12, -0.175), (1.105, -0.17), (1.115, -0.12)])
    B['Trigger'].append(G.side('Trigger', trig, 0.025, col, M['bright'], chamfer=0.005))
    B['Selector'].append(G.side('Selector', G.P([(1.0, -0.035), (1.06, -0.015), (1.06, 0.005), (1.0, 0.0)]), 0.012,
                                col, M['steel'], y=-0.068, chamfer=0.003))
    ch = unary_union([G.rbox(0.9, 0.17, 1.0, 0.2, 0.006)])
    B['ChargingHandle'].append(G.side('ChargingHandle', ch, 0.05, col, M['steel'], chamfer=0.006))
    B['ChargingHandle'].append(G.side('ChargingLatch', G.rbox(0.88, 0.165, 0.92, 0.205, 0.008), 0.17, col, M['steel'],
                                      chamfer=0.008))
    B['BoltCarrier'].append(G.side('BoltCarrier', G.rbox(1.1, 0.09, 1.42, 0.16, 0.01), 0.1, col, M['bright'],
                                   chamfer=0.01))
    dc = G.rbox(1.15, 0.083, 1.37, 0.167, 0.006)
    B['DustCover'].append(G.side('DustCover', dc, 0.012, col, M['receiver'], y=0.069, chamfer=0.004))
    mag = G.P([(1.205, -0.06), (1.415, -0.06), (1.43, -0.32), (1.47, -0.62), (1.45, -0.68), (1.27, -0.68),
               (1.245, -0.62), (1.21, -0.32)])
    B['Magazine'].append(G.side('Magazine', mag, 0.09, col, M['mag'], chamfer=0.014))
    B['Magazine'].append(G.side('MagRibs', unary_union([G.rbox(1.24 + 0.006 * i, -0.2 - 0.12 * i, 1.42 + 0.01 * i,
                                                                -0.17 - 0.12 * i, 0.008) for i in range(4)]),
                                0.098, col, M['mag'], chamfer=0.005))
    B['Magazine'].append(G.side('MagBase', G.rbox(1.25, -0.72, 1.48, -0.66, 0.012), 0.11, col, M['furniture'],
                                chamfer=0.012))
    for k in B:
        G.apply(B[k])
    return col, M, B


BONES = {   # bone: (head, tail, parent) in authoring coords; tails point +Z (see gunkit.rig axes note)
    'Root': ((GRIP[0], 0, GRIP[2]), (GRIP[0], 0, GRIP[2] + 0.2), None),
    'Trigger': ((1.125, 0, -0.088), (1.125, 0, 0.012), 'Root'),
    'Magazine': ((1.31, 0, -0.06), (1.31, 0, 0.04), 'Root'),
    'ChargingHandle': ((0.95, 0, 0.185), (0.95, 0, 0.285), 'Root'),
    'BoltCarrier': ((1.26, 0, 0.125), (1.26, 0, 0.225), 'Root'),
    'DustCover': ((1.26, 0.069, 0.083), (1.26, 0.069, 0.183), 'Root'),
    'Selector': ((1.02, -0.068, -0.012), (1.02, -0.068, 0.088), 'Root'),
}
# pose axes for a +Z-pointing bone (roll 0): loc (dx, dz, -dy) world; rot about world Y -> (0,0,-a), world X -> (a,0,0)


def animate(arm):
    acts = {}
    acts['Idle'] = G.new_action(arm, 'Idle')
    for b in BONES:                                       # every part keyed at rest (no pose bleeding between takes)
        for f in (1, 30):
            G.key(arm, b, f, loc=(0, 0, 0), rot=(0, 0, 0))

    acts['Fire'] = G.new_action(arm, 'Fire')                     # 1 shot @ ~800 rpm: 2.25 frames ~ use 4-frame cycle
    for f, tr, bolt, dc in ((1, 0, 0, 0), (2, -14, -0.12, -100), (3, -14, -0.2, -100), (4, -6, -0.05, -100), (5, 0, 0, -100)):
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
ATTACH = {   # authoring coords
    'GripRight': GRIP, 'RightHandIK': GRIP, 'LeftHandIK': (1.95, 0.0, 0.0), 'GripLeft': (1.95, 0.0, 0.0),
    'Muzzle': (2.95, 0.0, BORE), 'ADS': (1.08, 0.0, 0.33), 'Ejection': (1.26, 0.075, 0.125),
    'MagazineSeat': (1.31, 0.0, -0.06),
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
    for actn, frames in (('Reload_Empty', (1, 14, 22, 40, 52, 63, 68)), ('Inspect', (1, 30, 58, 66))):
        arm.animation_data.action = acts[actn]
        for f in frames:
            bpy.context.scene.frame_set(f)
            stage.ortho_camera([mesh], 'side', res=(700, 400), margin=1.25)
            stage.render(os.path.join(rv, f'{ID}_{actn}_f{f:02d}.png'), samples=12)
