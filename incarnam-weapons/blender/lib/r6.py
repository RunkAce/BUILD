"""Exact-size R6 proxy (Roblox classic rig) for scale and grip checks. Blender Z = Roblox Y (up),
Blender -Y = Roblox -Z (character front). 1 BU = 1 stud.

R6 parts: Head 2x1x1 part (visible head mesh ~1.25 wide), Torso 2x2x1, each Arm/Leg 1x2x1.
Torso centre at height 3. Shoulders: Torso CFrame(+-1, 0.5, 0); arm centres at x = +-1.5.
RightGrip (tool weld) C0 on the arm = CFrame(0,-1,0) * Angles(-90 deg, 0, 0): the grip point is the
bottom-centre of the arm, and the tool's +Y (our blade direction) points FORWARD (Roblox -Z).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import geo
import paint


def _box(name, size, centre, col, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.04, segments=2, affect='EDGES')
    o = geo.mesh_object(name, bm, col, mat)
    geo.shade_by_angle(o, 40)
    return o


def build(col, x_offset=0.0, arm_pitch_r=0.0, arm_pitch_l=0.0):
    """Returns dict of parts + hand frames. arm_pitch_* rotates arms forward (deg) about the shoulder."""
    skin = bpy.data.materials.get('R6_skin') or paint.painted('R6_skin', dict(
        base='#C9C2B6', light='#E6E1D8', dark='#7E786E', rough=0.7, metal=0.0, relief='none'), height=5)
    shirt = bpy.data.materials.get('R6_shirt') or paint.painted('R6_shirt', dict(
        base='#5E6B7A', light='#8A97A6', dark='#2E3640', rough=0.8, metal=0.0, relief='none'), height=5)
    parts = {}
    ox = x_offset
    parts['Torso'] = _box('R6_Torso', (2, 1, 2), (ox, 0, 3), col, shirt)
    parts['Head'] = _box('R6_Head', (1.25, 1.2, 1.2), (ox, 0, 4.6), col, skin)
    parts['LeftLeg'] = _box('R6_LeftLeg', (1, 1, 2), (ox - 0.5, 0, 1), col, shirt)
    parts['RightLeg'] = _box('R6_RightLeg', (1, 1, 2), (ox + 0.5, 0, 1), col, shirt)
    hands = {}
    for side, pitch in (('Right', arm_pitch_r), ('Left', arm_pitch_l)):
        s = 1 if side == 'Right' else -1
        arm = _box(f'R6_{side}Arm', (1, 1, 2), (0, 0, 0), col, skin)
        # arm local: centre at origin; shoulder pivot at (-s*0.5, 0, 0.5) in arm space (Motor6D C1)
        pivot_world = Vector((ox + s * 1.0, 0, 3.5))
        rot = Matrix.Rotation(math.radians(-pitch), 4, 'X')  # +pitch raises the arm forward (toward -Y)
        arm.matrix_world = Matrix.Translation(pivot_world) @ rot @ Matrix.Translation((s * 0.5, 0, -0.5))
        parts[f'{side}Arm'] = arm
        # RightGrip-equivalent: arm * CFrame(0,-1,0) * Angles(-90,0,0) -> tool +Z(Blender up) points forward
        grip = arm.matrix_world @ Matrix.Translation((0, 0, -1)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        hands[side] = grip
    return parts, hands
