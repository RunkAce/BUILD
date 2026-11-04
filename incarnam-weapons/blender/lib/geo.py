"""Geometry builders for the Incarnam Iop weapon set.

All 2D outlines are lists of (x, z) points in the weapon's front plane
(x = across the blade, z = along the weapon). Thickness is along Y.
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon
from shapely.geometry import Point, Polygon


# ---------------------------------------------------------------- helpers
def link(obj, col=None):
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_object(name, bm, col=None, material=None):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    link(obj, col)
    if material is not None:
        me.materials.append(material)
    return obj


def shade_by_angle(obj, angle_deg=35):
    """Smooth faces but keep hard edges above angle_deg (stable across Blender 4.1+)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        e.smooth = True
        n = len(e.link_faces)
        # hard if the crease exceeds the angle, and ALWAYS hard on boundary / non-manifold edges
        # (left by merged parts or hidden-face removal) - otherwise normals wrap round corners onto flat faces
        if n != 2 or e.calc_face_angle(0) > math.radians(angle_deg):
            e.smooth = False
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()


def resample(pts, closed=True, step=None):
    """Optionally densify an outline so insets/bevels behave on long edges."""
    if step is None:
        return [tuple(p) for p in pts]
    out = []
    n = len(pts)
    rng = n if closed else n - 1
    for i in range(rng):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % n])
        k = max(1, int((b - a).length / step))
        for j in range(k):
            out.append(tuple(a.lerp(b, j / k)))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def orient(pts, ccw=True):
    pts = list(pts)
    if (signed_area(pts) > 0) != ccw:
        pts.reverse()
    return pts


# ---------------------------------------------------------------- slabs
def slab(name, outline=None, holes=(), core_t=0.12, edge_t=0.03, bevel_w=0.12, col=None, material=None,
         y_offset=0.0, smooth_angle=30, levels=None, shape=None, allow_multi=True):
    """Stylized blade slab.

    outline/holes: 2D (x, z) loops. Holes are REAL openings with inner walls.
    edge_t: thickness at every outline edge (cutting edge / inner slot edge).
    core_t: thickness of the raised flat face.
    bevel_w: width of the bevel band from edge to face, measured in the plane.
    levels: optional [(inset_distance, half_thickness), ...] for multi-step bevels; overrides the above.
    Narrow areas (tips, thin rails) simply stay at the thinner levels instead of self-overlapping.
    """
    levels = levels or [(0.0, edge_t / 2), (bevel_w, core_t / 2)]
    if shape is not None:
        base = shape.buffer(0)
    else:
        base = Polygon(orient(outline, True), [orient(h, False) for h in holes]).buffer(0)
    if base.geom_type == 'MultiPolygon':
        base = max(base.geoms, key=lambda g: g.area) if not allow_multi else base
    # drop micro-segments / duplicate points (they make notches and zero-area faces)
    base = base.simplify(0.0025, preserve_topology=True).buffer(0)
    if not base.is_valid or base.is_empty:
        raise ValueError(f'{name}: invalid outline')
    bands = [base] + [base.buffer(-d, join_style='mitre', mitre_limit=8.0) for d, _ in levels[1:]]
    boundary = base.boundary

    def height(x, z):
        d = boundary.distance(Point(x, z))
        for (d0, h0), (d1, h1) in zip(levels[:-1], levels[1:]):
            if d <= d1:
                t = 0 if d1 == d0 else (d - d0) / (d1 - d0)
                return h0 + (h1 - h0) * max(0.0, min(1.0, t))
        return levels[-1][1]

    regions = []
    for i in range(len(bands)):
        g = bands[i] if i == len(bands) - 1 else bands[i].difference(bands[i + 1])
        g = g.buffer(0)
        regions += [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area > 1e-9]

    bm = bmesh.new()
    cache = {}

    def vert(x, z, side):
        key = (round(x, 6), round(z, 6), side)
        v = cache.get(key)
        if v is None:
            h = height(x, z)
            v = cache[key] = bm.verts.new((x, y_offset + side * h, z))
        return v

    for poly in regions:
        loops = [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]
        flat = [p for loop in loops for p in loop]
        tris = tessellate_polygon([[Vector((x, z, 0)) for (x, z) in loop] for loop in loops])
        for t in tris:
            a, b, c = (flat[i] for i in t)
            for side in (-1, 1):
                vs = [vert(*a, side), vert(*b, side), vert(*c, side)]
                if len(set(vs)) == 3:
                    try:
                        bm.faces.new(vs)
                    except ValueError:
                        pass
    # side walls along every outer and hole boundary
    rings = [base.exterior] + list(base.interiors) if base.geom_type == 'Polygon' else \
        [r for p in base.geoms for r in [p.exterior] + list(p.interiors)]
    for r in rings:
        pts = list(r.coords)[:-1]
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            quad = [vert(*a, -1), vert(*b, -1), vert(*b, 1), vert(*a, 1)]
            if len(set(quad)) == 4:
                try:
                    bm.faces.new(quad)
                except ValueError:
                    pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    _fix_t_junctions(bm)
    clean_topology(bm)
    obj = mesh_object(name, bm, col, material)
    shade_by_angle(obj, smooth_angle)
    return obj


def clean_topology(bm):
    """Remove degenerate faces, merge coplanar slivers, re-triangulate with BEAUTY (no long thin tris)."""
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges,
                             delimit={'NORMAL'})
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.join_triangles(bm, faces=bm.faces, angle_face_threshold=math.radians(1),
                             angle_shape_threshold=math.radians(40))
    for f in [f for f in bm.faces if f.calc_area() < 1e-9]:
        bm.faces.remove(f)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def _fix_t_junctions(bm, eps=1e-6):
    """Split boundary edges that have a vertex lying on them (from polygon-difference seams)."""
    for _ in range(4):
        bnd = [e for e in bm.edges if len(e.link_faces) == 1]
        if not bnd:
            return
        bverts = {v for e in bnd for v in e.verts}
        changed = False
        for e in bnd:
            if not e.is_valid:
                continue
            a, b = e.verts[0].co, e.verts[1].co
            ab = b - a
            L2 = ab.length_squared
            if L2 < eps:
                continue
            for v in list(bverts):
                if v in e.verts or not v.is_valid:
                    continue
                t = (v.co - a).dot(ab) / L2
                if 1e-4 < t < 1 - 1e-4 and ((a + ab * t) - v.co).length < 1e-5:
                    res = bmesh.ops.subdivide_edges(bm, edges=[e], cuts=1)
                    nv = [g for g in res['geom_inner'] if isinstance(g, bmesh.types.BMVert)][0]
                    nv.co = v.co.copy()
                    bmesh.ops.pointmerge(bm, verts=[nv, v], merge_co=v.co.copy())
                    changed = True
                    break
        if not changed:
            return


def extrude_outline(name, outline, holes=(), thickness=0.1, chamfer=0.02, col=None, material=None, y_offset=0.0,
                    smooth_angle=30):
    """Flat extruded piece (guards, inlays, plates) with a chamfered rim."""
    return slab(name, outline, holes, core_t=thickness, edge_t=max(thickness - 2 * chamfer, thickness * 0.35),
                bevel_w=chamfer, col=col, material=material, y_offset=y_offset, smooth_angle=smooth_angle)


# ---------------------------------------------------------------- revolved parts
def lathe(name, profile, segments=8, col=None, material=None, rot_offset=None, smooth_angle=40, scale_xy=(1, 1)):
    """Revolve a (radius, z) profile around Z. Low segment counts give faceted stylized pommels."""
    bm = bmesh.new()
    off = math.pi / segments if rot_offset is None else rot_offset
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segments):
            a = off + 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a) * scale_xy[0], r * math.sin(a) * scale_xy[1], z)))
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            quad = [a[i], a[j], b[j], b[i]]
            if len(set(quad)) == 4:
                bm.faces.new(quad)
    if profile[0][0] > 1e-6:
        bm.faces.new(list(reversed(rings[0])))
    if profile[-1][0] > 1e-6:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object(name, bm, col, material)
    shade_by_angle(obj, smooth_angle)
    return obj


def wrapped_grip(name, z0, z1, radius, wraps=7, band_w=None, segments=10, col=None, material=None, flatten=1.0,
                 style='round'):
    """Grip core plus helical overlapping wrap bands (real relief, not painted)."""
    length = z1 - z0
    band_w = band_w or length / wraps * 1.05
    bm = bmesh.new()
    # game budget: ~8 rows per wrap is enough for the strap silhouette; leather grain lives in the normal map
    rings = max(8, int(wraps * 8))
    if os.environ.get('LEGACY_GRIP'):          # reproduce the grip used by the delivered packs (audits only)
        rings, segments = int(wraps * (24 if style == 'strap' else 10)), 16
    # Each wrap band: a ring whose centre line slants; build as a twisted tube surface offset from core.
    verts_rows = []
    for r in range(rings + 1):
        t = r / rings
        z = z0 + t * length
        row = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            # helical bulge: bands overlap, each band is thicker at its leading edge
            phase = (t * wraps - a / (2 * math.pi)) % 1.0
            if style == 'strap':
                # flat leather straps: each strap rises linearly then drops off a sharp lip onto the next
                bulge = 0.16 * radius * min(1.0, phase / 0.88) - (0.16 * radius if phase > 0.94 else 0.0)
                bulge = max(bulge, 0.0)
            else:
                bulge = 0.18 * radius * (phase ** 0.6) * (1 - phase) * 3.2
            rr = radius + bulge
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a) * flatten, z)))
        verts_rows.append(row)
    for a, b in zip(verts_rows[:-1], verts_rows[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(list(reversed(verts_rows[0])))
    bm.faces.new(verts_rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object(name, bm, col, material)
    shade_by_angle(obj, 50)
    return obj


# ---------------------------------------------------------------- swept tubes / links
def sweep(name, path, radius, sides=8, closed=False, col=None, material=None, flatten=1.0, smooth_angle=50,
          radii=None):
    """Sweep a polygonal cross-section along a 3D path (list of Vectors)."""
    bm = bmesh.new()
    n = len(path)
    rows = []
    up = Vector((0, 0, 1))
    for i, p in enumerate(path):
        a = path[(i - 1) % n] if (closed or i > 0) else path[i]
        b = path[(i + 1) % n] if (closed or i < n - 1) else path[i]
        tan = (b - a).normalized()
        ref = up if abs(tan.dot(up)) < 0.9 else Vector((1, 0, 0))
        nrm = tan.cross(ref).normalized()
        bin_ = tan.cross(nrm).normalized()
        r = radii[i] if radii else radius
        row = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides + math.pi / sides
            off = nrm * math.cos(ang) * r + bin_ * math.sin(ang) * r * flatten
            row.append(bm.verts.new(p + off))
        rows.append(row)
    pairs = list(zip(rows[:-1], rows[1:])) + ([(rows[-1], rows[0])] if closed else [])
    for ra, rb in pairs:
        for s in range(sides):
            t = (s + 1) % sides
            bm.faces.new([ra[s], ra[t], rb[t], rb[s]])
    if not closed:
        bm.faces.new(list(reversed(rows[0])))
        bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object(name, bm, col, material)
    shade_by_angle(obj, smooth_angle)
    return obj


def stadium_path(length, width, samples=28):
    """Closed rounded-rectangle loop in the XZ plane (chain link centre line)."""
    r = width / 2
    straight = max(0.0, length - width)
    pts = []
    for i in range(samples):
        t = i / samples
        a = 2 * math.pi * t
        x = r * math.cos(a)
        z = r * math.sin(a)
        z += straight / 2 if z >= 0 else -straight / 2
        pts.append(Vector((x, 0, z)))
    return pts


def chain_link(name, length=0.36, width=0.22, wire=0.045, sides=6, col=None, material=None):
    """Rigid stadium link with an open centre; faceted wire for stylized read."""
    return sweep(name, stadium_path(length, width), wire, sides=sides, closed=True, col=col, material=material,
                 smooth_angle=55)


def ring(name, radius, wire, sides=8, samples=24, col=None, material=None, axis='Y'):
    pts = [Vector((radius * math.cos(2 * math.pi * i / samples), 0, radius * math.sin(2 * math.pi * i / samples)))
           for i in range(samples)]
    obj = sweep(name, pts, wire, sides=sides, closed=True, col=col, material=material)
    if axis == 'X':
        obj.rotation_euler = (0, 0, math.radians(90))
    return obj


# ---------------------------------------------------------------- outline utilities
def mirror_x(half):
    """half: points from top centre down the +x side to bottom centre. Returns full closed outline."""
    right = [tuple(p) for p in half]
    left = [(-x, z) for (x, z) in reversed(half) if abs(x) > 1e-9]
    full = right + left
    # drop duplicated centre points
    out = []
    for p in full:
        if not out or (abs(out[-1][0] - p[0]) > 1e-9 or abs(out[-1][1] - p[1]) > 1e-9):
            out.append(p)
    return out


def arc(cx, cz, r, a0, a1, n=12):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def bezier(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def tri_count(objs):
    total = 0
    for o in objs:
        if o.type == 'MESH':
            deps = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = deps.to_mesh()
            total += sum(len(p.vertices) - 2 for p in me.polygons)
            deps.to_mesh_clear()
    return total


def mesh_health(obj):
    """Return a dict of mesh problems: non-manifold edges, loose verts, zero-area faces, inverted normals."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nonman = [e for e in bm.edges if not e.is_manifold]
    loose = [v for v in bm.verts if not v.link_edges]
    zero = [f for f in bm.faces if f.calc_area() < 1e-9]
    # inverted check: signed volume should be positive for outward normals
    vol = bm.calc_volume(signed=True)
    if any(e.is_boundary for e in bm.edges):
        # open shell (hidden faces removed): volume sign is meaningless -> area-weighted vote of face normals
        # against the direction from the mesh centre
        c = sum((v.co for v in bm.verts), Vector()) / max(len(bm.verts), 1)
        score = sum(f.normal.dot((f.calc_center_median() - c)) * f.calc_area() for f in bm.faces)
        outward = score > 0
    else:
        outward = vol > 0
    bm.free()
    return {'non_manifold_edges': len(nonman), 'loose_verts': len(loose), 'zero_area_faces': len(zero),
            'signed_volume': round(vol, 6), 'normals_outward': outward}


def finalize_weights(obj, fallback_group, limit=4):
    """Make skin weights game-safe: every vertex weighted (fallback_group if none), at most `limit`
    influences (Roblox skinned meshes allow 4), and weights normalised to sum exactly 1."""
    names = {g.index: g.name for g in obj.vertex_groups}
    fixes = {'unweighted_fixed': 0, 'trimmed': 0}
    per_vertex = []
    for v in obj.data.vertices:
        ws = [(names[g.group], g.weight) for g in v.groups if g.weight > 1e-4]
        if not ws:
            ws = [(fallback_group, 1.0)]
            fixes['unweighted_fixed'] += 1
        ws.sort(key=lambda t: -t[1])
        if len(ws) > limit:
            ws = ws[:limit]
            fixes['trimmed'] += 1
        tot = sum(w for _, w in ws)
        per_vertex.append((v.index, [(n, w / tot) for n, w in ws]))
    for g in obj.vertex_groups:
        g.remove([v.index for v in obj.data.vertices])
    for idx, ws in per_vertex:
        for n, w in ws:
            obj.vertex_groups[n].add([idx], w, 'REPLACE')
    return fixes
