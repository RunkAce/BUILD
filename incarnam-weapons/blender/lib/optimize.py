"""Topology optimisation and reporting for game export.

remove_hidden_faces(): deletes faces that can never be seen because they are buried inside other parts
  (blade root inside the guard, grip end caps inside collars, inlay backs inside the blade...). Each face
  is sampled at its centroid and corner-biased points; from each sample, rays are cast over the face's
  outward hemisphere. If EVERY ray from EVERY sample hits geometry, the face is enclosed -> removed.
  A single escaping ray keeps the face, so partially visible faces and open slots are never touched.
topology_report(): triangle count, n-gons, slivers (min angle < 6 deg), non-manifold edges, UV usage.
"""
import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _hemisphere(n=26):
    """Roughly uniform directions on the +Z hemisphere (Fibonacci), plus the pole."""
    dirs = [Vector((0, 0, 1))]
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n - 1):
        z = 1 - (i + 0.5) / (n - 1)          # 1..0
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * golden
        dirs.append(Vector((math.cos(a) * r, math.sin(a) * r, max(z, 0.04))).normalized())
    return dirs


def _frame(normal):
    n = normal.normalized()
    ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    t = n.cross(ref).normalized()
    b = n.cross(t)
    return t, b, n


def remove_hidden_faces(obj, occluders=(), rays=26, eps=1e-4, max_dist=1e4):
    """Delete fully enclosed faces of obj. occluders: other mesh objects that can hide obj's faces."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bms = []
    for o in [obj] + list(occluders):
        b = bmesh.new()
        b.from_object(o, depsgraph)
        b.transform(o.matrix_world)
        bms.append(b)
    merged = bmesh.new()
    for b in bms:
        tmp = bpy.data.meshes.new('_occ')
        b.to_mesh(tmp)
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        b.free()
    tree = BVHTree.FromBMesh(merged)
    merged.free()

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    hemi = _hemisphere(rays)
    hidden = []
    for f in bm.faces:
        n = (nmat @ f.normal).normalized()
        if n.length < 0.5:
            continue
        t, b, nn = _frame(n)
        cen = mw @ f.calc_center_median()
        verts = [mw @ v.co for v in f.verts]
        samples = [cen] + [cen.lerp(v, 0.7) for v in verts[:4]]
        visible = False
        for s in samples:
            origin = s + nn * eps
            for d in hemi:
                w = t * d.x + b * d.y + nn * d.z
                hit = tree.ray_cast(origin, w, max_dist)
                if hit[0] is None:
                    visible = True
                    break
            if visible:
                break
        if not visible:
            hidden.append(f)
    removed = len(hidden)
    bmesh.ops.delete(bm, geom=hidden, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return removed


def topology_report(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    slivers = 0
    tri_bm = bm.copy()
    bmesh.ops.triangulate(tri_bm, faces=tri_bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in tri_bm.faces:
        a, b, c = (v.co for v in f.verts)
        angs = []
        for p, q, r in ((a, b, c), (b, c, a), (c, a, b)):
            u, v = q - p, r - p
            if u.length < 1e-9 or v.length < 1e-9:
                angs.append(0.0)
            else:
                angs.append(u.angle(v))
        if min(angs) < math.radians(6):
            slivers += 1
    tri_bm.free()
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    # UV usage: fraction of the 0..1 square covered by UV triangles (approx, overlaps counted once per face)
    uv_area = 0.0
    uv = bm.loops.layers.uv.active
    if uv:
        for f in bm.faces:
            pts = [l[uv].uv for l in f.loops]
            a2 = 0.0
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                a2 += x1 * y2 - x2 * y1
            uv_area += abs(a2) / 2
    bm.free()
    return {'triangles': tris, 'quads': quads, 'ngons': ngons, 'faces': len(obj.data.polygons),
            'sliver_tris_lt6deg': slivers, 'non_manifold_edges': nonman, 'open_boundary_edges': boundary,
            'uv_coverage': round(uv_area, 3) if uv else None}
