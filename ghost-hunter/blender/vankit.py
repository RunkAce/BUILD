"""Small hard-surface helpers for vehicle props (ghost-hunter van), on top of the Incarnam lib (geo/paint/stage).

Authoring convention: X = along the van, FRONT toward +X, Z = up, Y = width (+Y = driver/left side).
Units: studs. The finished model is rotated so the front faces Blender -Y = Roblox -Z (LookVector).
"""
import math
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'incarnam-weapons', 'blender', 'lib')
sys.path.insert(0, os.path.abspath(LIB))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402

import geo  # noqa: E402


def P(pts, r=0.0):
    p = Polygon(geo.orient(pts)).buffer(0)
    return p.buffer(-r, join_style='round').buffer(r, 8) if r > 0 else p


def rbox(x0, z0, x1, z1, r=0.0):
    b = box(x0, z0, x1, z1)
    return b.buffer(-r).buffer(r, 6) if r > 0 else b


def side(name, shape, width, col, mat, chamfer=0.06, y=0.0, smooth=False):
    """2D (x, z) shape extruded across Y with a two-step chamfer."""
    c = min(chamfer, width * 0.3)
    o = geo.slab(name, shape=shape, core_t=width, edge_t=width - 2 * c, bevel_w=c,
                 levels=[(0.0, width / 2 - c), (c * 0.5, width / 2 - c * 0.3), (c, width / 2)],
                 col=col, material=mat, y_offset=y, smooth_angle=30)
    if not smooth:
        for p in o.data.polygons:
            p.use_smooth = False
    return o


def front(name, shape_yz, x0, x1, col, mat, chamfer=0.05):
    """2D (y, z) shape extruded along X (rear doors, grille, dash)."""
    o = side(name, shape_yz, x1 - x0, col, mat, chamfer)
    o.rotation_euler = (0, 0, math.radians(90))
    o.location = ((x0 + x1) / 2, 0, 0)
    return o


def top(name, shape_xy, z0, z1, col, mat, chamfer=0.05):
    """2D (x, y) shape extruded along Z (desk tops, roof panels)."""
    o = side(name, shape_xy, z1 - z0, col, mat, chamfer)
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (0, 0, (z0 + z1) / 2)
    return o


def block(name, x0, y0, z0, x1, y1, z1, col, mat, chamfer=0.04):
    return side(name, rbox(x0, z0, x1, z1), y1 - y0, col, mat, chamfer, y=(y0 + y1) / 2)


def lathe_y(name, profile, col, mat, loc, segments=16, smooth=40):
    """Round part with its axis along Y. profile [(radius, y)]."""
    o = geo.lathe(name, profile, segments=segments, col=col, material=mat, smooth_angle=smooth)
    o.rotation_euler = (math.radians(-90), 0, 0)   # lathe +Z -> +Y
    o.location = loc
    return o


def lathe_z(name, profile, col, mat, loc, segments=12, smooth=40):
    o = geo.lathe(name, profile, segments=segments, col=col, material=mat, smooth_angle=smooth)
    o.location = loc
    return o


def lathe_x(name, profile, col, mat, loc, segments=12, smooth=40):
    o = geo.lathe(name, profile, segments=segments, col=col, material=mat, smooth_angle=smooth)
    o.rotation_euler = (0, math.radians(90), 0)
    o.location = loc
    return o


def rod(name, a, b, r, col, mat, segments=8):
    """Cylinder from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = geo.lathe(name, [(0, 0), (r, 0), (r, d.length), (0, d.length)], segments=segments, col=col, material=mat,
                  smooth_angle=50)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.normalized().to_track_quat('Z', 'Y')
    o.location = a
    return o


def apply(objs):
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objs


def boolean(target, cutters, op='DIFFERENCE'):
    """Exact boolean of target with each cutter (cutters are deleted)."""
    apply([target] + list(cutters))
    bpy.context.view_layer.objects.active = target
    for c in cutters:
        m = target.modifiers.new('B', 'BOOLEAN')
        m.operation = op
        m.solver = 'EXACT'
        m.object = c
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(True)
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(c, do_unlink=True)
    return target


def prism(name, shape_xz, y0, y1, col):
    """Plain (unchamfered) cutter prism."""
    w = y1 - y0
    return geo.slab(name, shape=shape_xz, levels=[(0.0, w / 2)], col=col, y_offset=(y0 + y1) / 2)


def quad_panel(name, corners, thickness, col, mat):
    """Thin box from 4 coplanar corners (e.g. a sloped windshield)."""
    c = [Vector(v) for v in corners]
    n = (c[1] - c[0]).cross(c[3] - c[0]).normalized() * (thickness / 2)
    bm = bmesh.new()
    a = [bm.verts.new(v - n) for v in c]
    b = [bm.verts.new(v + n) for v in c]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return geo.mesh_object(name, bm, col, mat)


def split_at_z(obj, zs):
    """Bisect the mesh at the given heights so faces can carry two-tone paint / stripes."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for z in zs:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def assign(obj, mat, test):
    """Assign mat to faces whose (centre, normal) satisfy test."""
    me = obj.data
    names = [m.name if m else '' for m in me.materials]
    if mat.name not in names:
        me.materials.append(mat)
        names.append(mat.name)
    idx = names.index(mat.name)
    mw = obj.matrix_world
    for p in me.polygons:
        if test(mw @ p.center, (mw.to_3x3() @ p.normal).normalized()):
            p.material_index = idx
