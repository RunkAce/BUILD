"""Fists: a PAIR of gauntlets worn on the R6 arm end (right built, left = X mirror of the Body).

Arm-local coordinates: the R6 arm is a 1 x 1 x 2 block standing on the hand point (0,0,0), i.e. it fills
x,y in [-0.5, 0.5], z in [0, 2]. The gauntlet hugs it with a 1.02 x 1.02 opening: a seated hand shell
(primary) + cuff (secondary) joined by accent bands, a wide race-shaped knuckle guard on the back of the
hand (front, -Y) that breaks past the shell outline, with the motif2 boss as the single glow accent, the race
motif inlaid in a pointed cuff plate, knuckle studs (style pommel profile; three big ones for heavy races)
or long curled talons (hooked / feral races) on the striking end (-Z), and an outer forearm fin (+X,
mirrored to the outside on the left) whose FORM follows the silhouette flags:
  spikes / feral -> 2-3 swept fins      round -> curled petals      organic -> curled leaf + midrib
  heavy / tool / riveted / warded -> squared pauldron plate (brim + rivets)    segmented -> stacked lames
  clockwork -> meshing gear pair        slender -> one long notched quill       else -> big race blade fin
Cuff profile by build: slender = long cuff with a pointed (V) front, heavy = short wide bell, else standard.
The fin group is fitted (tilted outward, then shrunk) so the whole gauntlet stays inside SIZES['fists'].
Runtime: weld to the arm at CFrame(0,-1,0) with NO rotation (mesh +Z = arm up); Grip = hand point.
Reads: mats roles, blade dict, guard, pommel, motif, motif2, silhouette flags."""
import math

import bmesh
from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

import core
import geo

HALF = 0.51          # half of the 1.02 x 1.02 arm opening


# ------------------------------------------------------------------ rounded-square lofts (arm wrappers)
def _rrect(hx, hy, r, steps):
    r = max(0.006, min(r, hx - 0.002, hy - 0.002))
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0), (-hx + r, hy - r, 90), (-hx + r, -hy + r, 180), (hx - r, -hy + r, 270)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def loft(name, prof, col, mat, r0=0.07, steps=2, closed=True, cap0=False, cap1=False, hx=HALF, hy=HALF,
         smooth=34, shear=None):
    """Revolve-like loft of a (d, z) profile around the arm: each profile point becomes a rounded square ring
    offset d outside the hx x hy opening (corner radius grows with d so offsets stay parallel)."""
    bm = bmesh.new()
    rings = []
    for d, z in prof:
        rings.append([bm.verts.new((x, y, shear(x, y, z) if shear else z)) for x, y in _rrect(hx + d, hy + d, r0 + d, steps)])
    n = len(rings[0])
    pairs = list(zip(rings[:-1], rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([a[i], a[j], b[j], b[i]])
    if cap0:
        bm.faces.new(list(reversed(rings[0])))
    if cap1:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = geo.mesh_object(name, bm, col, mat)
    geo.shade_by_angle(obj, smooth)
    return obj


def band(name, z, h, d_in, d_out, col, mat, r0, steps, shear=None):
    """Accent band seated into the shell: buried inner face, two-step faceted outer edge."""
    c = h * 0.28
    return loft(name, [(d_in, z - h / 2), (d_out - c, z - h / 2), (d_out, z - h / 2 + c), (d_out, z + h / 2 - c),
                       (d_out - c, z + h / 2), (d_in, z + h / 2)], col, mat, r0=r0, steps=steps, shear=shear)


def _clip(shape, x0, z0, x1, z1):
    return shape.intersection(box(x0, z0, x1, z1)).buffer(0)


def _talon(L, w, hook, serrated=False):
    """Hooked talon hanging from z=0 to z=-L, tapering all the way, tip hooking toward +X by `hook`."""
    outer = geo.bezier((-w / 2, 0.0), (-w / 2, -L * 0.5), (hook * 0.4 - w * 0.12, -L * 0.88), (hook, -L), 10)
    inner = geo.bezier((hook, -L), (hook * 0.55 + w * 0.12, -L * 0.72), (w / 2, -L * 0.42), (w / 2, 0.0), 10)
    if serrated:
        inner = [(x + (0.025 if 2 < k < 9 and k % 2 else 0.0), z) for k, (x, z) in enumerate(inner)]
    return core.poly(outer + inner[1:-1] + [(w / 2, 0.06), (-w / 2, 0.06)])


def _crest(tip, kind, pw, z0, z1):
    """Cuff plate outline whose top echoes the race blade tip (arch for round / organic races)."""
    sh = z1 - 0.15                                        # shoulder height
    base = [(-pw * 0.8, z0), (pw * 0.8, z0), (pw, z0 + 0.08)]
    if kind == 'arch':
        top = [(pw, sh)] + [(x, sh + (z - sh) * 0.45) for x, z in geo.arc(0, sh, pw, 0, 180, 10)[1:-1]] + [(-pw, sh)]
    elif tip == 'chisel':
        top = [(pw, sh + 0.06), (pw * 0.55, z1 - 0.02), (-pw * 0.55, z1 - 0.02), (-pw, sh + 0.06)]
    elif tip == 'clip':
        top = [(pw, z1 + 0.02), (pw * 0.2, z1 - 0.04), (-pw, sh)]
    elif tip == 'split':
        top = [(pw, sh), (pw * 0.55, z1 + 0.03), (0, sh + 0.04), (-pw * 0.55, z1 + 0.03), (-pw, sh)]
    elif tip == 'hook':
        top = [(pw, sh)] + geo.bezier((pw * 0.7, sh + 0.08), (pw * 0.6, z1 + 0.1), (-pw * 0.2, z1 + 0.12),
                                      (-pw * 0.5, z1 - 0.04), 8) + [(-pw, sh)]
    else:                                                  # point
        top = [(pw, sh), (0, z1 + 0.03), (-pw, sh)]
    return core.poly(base + top + [(-pw, z0 + 0.08)])


def _rot_z(obj, deg):
    obj.rotation_euler = (0, 0, math.radians(deg))
    return obj


# ------------------------------------------------------------------ outer forearm fins: 2D parts in the XZ plane
# Every fin form is a list of flat parts (outline + role + thickness) so the whole group can be fitted to the
# R6 length budget (rotated further outward / scaled about its root) before any mesh is made.
def _part(name, shape, role, t, kind='plate', chamfer=0.03):
    return dict(name=name, shape=shape.buffer(0), role=role, t=t, kind=kind, chamfer=chamfer)


def _curl(shape, k):
    """Bend a +Z shape so its tip curls toward -X: after the outward (clockwise) tilt it sweeps back up."""
    return core.mirror(core.bend(core.mirror(shape), k)) if k > 0.02 else shape


def _sym(right):
    """Closed outline from a right-hand half running (0, 0) -> (0, L)."""
    return core.poly(right + [(-x, z) for x, z in reversed(right)][1:-1])


def _gear2d(r, teeth, hole, windows=4):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if i % 4 in (1, 2) else r * 0.8
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    g = core.poly(pts).difference(Point(0, 0).buffer(hole, 12))
    for j in range(windows):                      # spoke windows = negative space
        a = 2 * math.pi * (j + 0.5) / windows
        g = g.difference(Point(r * 0.52 * math.cos(a), r * 0.52 * math.sin(a)).buffer(r * 0.15, 8))
    return g


def _fin_form(sil, heavy, slender):
    if sil.get('clockwork'):
        return 'gear'
    if sil.get('warded'):
        return 'pauldron'
    if sil.get('round'):
        return 'petal'
    if sil.get('organic'):
        return 'leaf'
    if sil.get('spikes') or sil.get('feral'):
        return 'swept'
    if sil.get('segmented'):
        return 'lames'
    if heavy:
        return 'pauldron'
    if slender:
        return 'quill'
    return 'blade'


def _fin_parts(form, style, px, pz, cuff_top, hs_top):
    """Fin parts placed around the root pivot (px, pz) on the outer (+X) cuff wall."""
    bl, sil = style.get('blade', {}), style.get('silhouette', {})
    bw = bl.get('width', 1.0)
    edge, tip = bl.get('edge', 'straight'), bl.get('tip', 'point')
    holes = bl.get('holes', 'none')
    P = []

    def put(shape, x=0.0, z=0.0, rot=0.0):
        return core.place(shape, px + x, pz + z, rot=rot)

    if form == 'blade':                           # one big blade-outline fin (race edge / tip / holes)
        L, W = 1.1, min(0.78, 0.7 * bw)
        fs = core.blade_outline(L, W, edge=edge, tip=tip if tip != 'split' else 'point',
                                holes=holes if holes in ('slot', 'rings') else 'none', notch='none',
                                single_edge=bl.get('single_edge', False))
        fs = _curl(fs, 0.25 + sil.get('curve', 0.0) * 1.2)
        P.append(_part('Fin', put(fs, rot=-46), 'primary', 0.12, 'blade'))
    elif form == 'quill':                         # one long feather quill: notched vane + raised rachis
        L, W = 1.15, 0.36 * bw
        vane = _sym(geo.bezier((0.0, 0.0), (W * 0.62, L * 0.2), (W * 0.55, L * 0.78), (0.0, L), 14))
        vane = vane.difference(box(-W, -0.1, -0.0001, L + 0.1)).union(core.poly(
            geo.bezier((0.0, L), (-W * 0.3, L * 0.72), (-W * 0.42, L * 0.3), (-0.03, 0.0), 12) + [(0.03, 0.0)]))
        for zf in (0.44, 0.64):                   # feather splits
            vane = vane.difference(core.poly([(W * 0.8, L * zf + 0.08), (W * 0.1, L * zf - 0.05), (W * 0.8, L * zf)]))
        if holes == 'rings':                      # portal ring punched through the vane
            vane = vane.difference(Point(-W * 0.05, L * 0.28).buffer(W * 0.17, 14))
        rach = core.poly([(-0.045, -0.06), (0.045, -0.06), (0.014, L * 0.9), (-0.014, L * 0.9)])
        vane, rach = _curl(vane, 0.35), _curl(rach, 0.35)
        P += [_part('Quill', put(vane, rot=-38), 'primary', 0.1, 'blade'),
              _part('Rachis', put(rach, rot=-38), 'accent', 0.15, chamfer=0.02)]
    elif form == 'swept':                         # 2-3 swept back fins fanning from the cuff wall
        n = 3 if (sil.get('feral') or sil.get('barbs')) else 2
        for k in range(n):
            L, W = 1.05 * (1 - 0.22 * k), 0.42 * bw * (1 - 0.12 * k)
            fs = core.blade_outline(L, W, edge=edge, tip='hook' if tip == 'hook' else 'point', single_edge=True)
            fs = _curl(fs, 0.4)
            P.append(_part(f'Fin{k}', put(fs, 0.0, -0.13 * k, rot=-38 - 22 * k), 'primary',
                           (0.12, 0.15, 0.12)[k], 'blade'))
    elif form == 'petal':                         # two curled petals + a raised vein
        big = _sym(geo.bezier((0.0, 0.0), (0.72 * bw * 0.7, 0.1), (0.72 * bw * 0.62, 0.74), (0.0, 0.95), 14))
        small = core.place(big, scale=0.7)
        vein = core.poly([(-0.035, -0.04), (0.035, -0.04), (0.012, 0.72), (-0.012, 0.72)])
        P += [_part('Petal', put(_curl(big, 0.5), rot=-40), 'primary', 0.11, 'blade'),
              _part('PetalVein', put(_curl(vein, 0.5), rot=-40), 'accent', 0.15, chamfer=0.02),
              _part('Petal2', put(_curl(small, 0.6), 0.0, -0.12, rot=-84), 'secondary', 0.14, 'blade')]
    elif form == 'leaf':                          # big curled leaf with midrib (+ thorns), small under-leaf
        L, W = 1.1, 0.62 * bw
        right = geo.bezier((0.0, 0.0), (W * 0.6, L * 0.18), (W * 0.5, L * 0.7), (0.0, L), 16)
        left = geo.bezier((0.0, L), (-W * 0.45, L * 0.66), (-W * 0.55, L * 0.2), (0.0, 0.0), 16)
        leaf = core.poly(right + left[1:-1])
        if sil.get('thorns'):
            for i in (5, 9):
                x, z = right[i]
                leaf = leaf.union(core.poly([(x - 0.06, z - 0.05), (x + 0.1, z + 0.06), (x - 0.04, z + 0.07)]))
        rib = core.poly([(-0.04, -0.05), (0.04, -0.05), (0.012, L * 0.86), (-0.012, L * 0.86)])
        P += [_part('Leaf', put(_curl(leaf, 0.7), rot=-40), 'primary', 0.11, 'blade'),
              _part('Midrib', put(_curl(rib, 0.7), rot=-40), 'accent', 0.15, chamfer=0.02),
              _part('Leaf2', put(_curl(core.place(leaf, scale=0.55), 0.9), 0.0, -0.12, rot=-86), 'secondary', 0.14,
                    'blade')]
    elif form == 'pauldron':                      # squared plate standing off the outer wrist + brim + rivets
        out = 0.54 + 0.06 * (style['silhouette'].get('chunky', 1.0) > 1.2)
        pl = core.poly([(-0.1, -0.06), (out - 0.2, -0.13), (out - 0.04, 0.02), (out, 0.66), (out - 0.18, 0.86),
                        (-0.1, 0.8)])
        pl = pl.difference(Point(0.12, 0.95).buffer(0.15, 10))     # crenel notch on the top edge
        brim = pl.intersection(box(-1, 0.6, 1, 2)).buffer(0.025, join_style='mitre')
        n_riv = 5 if sil.get('riveted') else 3
        riv = unary_union([Point(out - 0.15, 0.05 + 0.5 * i / max(1, n_riv - 1)).buffer(0.045, 8)
                           for i in range(n_riv)])
        P += [_part('Pauldron', put(pl, rot=-14), 'primary', 0.22, chamfer=0.035),
              _part('PauldronBrim', put(brim, rot=-14), 'secondary', 0.27, chamfer=0.03),
              _part('PauldronRivets', put(riv, rot=-14), 'accent', 0.31, chamfer=0.02)]
    elif form == 'lames':                         # three overlapping squared lames stepping out and up
        for k in range(3):
            z0, o = -0.04 + 0.27 * k, 0.36 + 0.06 * k
            lame = core.poly([(-0.1, z0), (o, z0 - 0.06), (o + 0.06, z0 + 0.28), (o - 0.04, z0 + 0.34), (-0.1, z0 + 0.34)])
            P.append(_part(f'Lame{k}', put(lame, rot=-8 - 5 * k), ('primary', 'secondary', 'primary')[k],
                           (0.2, 0.25, 0.2)[k], chamfer=0.035))
            P.append(_part(f'LamePeg{k}', put(Point(o - 0.08, z0 + 0.15).buffer(0.045, 8), rot=-8 - 5 * k), 'accent',
                           0.3, chamfer=0.02))
    elif form == 'gear':                          # meshing gear pair on the outer wrist, accent hubs
        r1, r2 = 0.38, 0.22
        c1 = (0.26, 0.12)
        a = math.radians(62)
        c2 = (c1[0] + (r1 + r2) * 0.88 * math.cos(a), c1[1] + (r1 + r2) * 0.88 * math.sin(a))
        g1 = core.place(_gear2d(r1, 10, r1 * 0.2), *c1, rot=9)
        g2 = core.place(_gear2d(r2, 7, r2 * 0.24, windows=3), *c2)
        hub1 = core.place(Point(0, 0).buffer(r1 * 0.34, 16).difference(Point(0, 0).buffer(r1 * 0.2, 12)), *c1)
        hub2 = core.place(Point(0, 0).buffer(r2 * 0.38, 12).difference(Point(0, 0).buffer(r2 * 0.24, 10)), *c2)
        P += [_part('Gear', put(g1), 'primary', 0.14, chamfer=0.025),
              _part('GearSmall', put(g2), 'secondary', 0.18, chamfer=0.025),
              _part('GearHub', put(hub1), 'accent', 0.2, chamfer=0.02),
              _part('GearHubSmall', put(hub2), 'accent', 0.24, chamfer=0.02)]
    return P


def _fit(parts, pivot, zmax):
    """Keep the fin group under zmax (R6 length budget): tilt it a little further outward, then shrink it a
    little, then tilt more, and only then shrink hard (fins stay big without turning into a flat comb)."""
    def top(ps):
        return max(p['shape'].bounds[3] for p in ps)

    def tilt(ps, limit, extra):
        while top(ps) > zmax and extra < limit:
            extra += 4
            ps = [dict(p, shape=affinity.rotate(p['shape'], -4, origin=pivot)) for p in ps]
        return ps, extra

    def shrink(ps, floor):
        if top(ps) <= zmax:
            return ps, 1.0
        k = max(floor, (zmax - pivot[1]) / (top(ps) - pivot[1]))
        return [dict(p, shape=affinity.scale(p['shape'], k, k, origin=pivot)) for p in ps], k
    parts, extra = tilt(parts, 24, 0)
    parts, s = shrink(parts, 0.78)
    parts, extra = tilt(parts, 40, extra)
    parts, _ = shrink(parts, 0.6)
    return parts


# ------------------------------------------------------------------ template
def build(style, ctx):
    import bpy
    import stage
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    sil = style.get('silhouette', {})
    chunky = sil.get('chunky', 1.0)
    heavy = bool(sil.get('heavy') or sil.get('tool') or sil.get('riveted') or chunky >= 1.18)
    slender = sil.get('slender', False)
    edge, tip = bl.get('edge', 'straight'), bl.get('tip', 'point')
    claws = tip == 'hook' or sil.get('feral', False)
    # cross-section flavour
    r0 = 0.16 if sil.get('round') else (0.035 if (sil.get('faceted') or sil.get('clockwork')) else 0.075)
    steps = 1 if (sil.get('faceted') or sil.get('clockwork') or edge == 'crystal') else 2
    wall = 0.10 * (1.25 if heavy else (0.82 if slender else 1.0))
    # cuff profile by build: long pointed (slender) | short heavy bell (heavy) | standard flare
    cuff = 'long' if slender else ('bell' if heavy else 'std')
    hs_top = 0.44                               # hand shell / cuff joint (wrist)
    zb = -0.2                                   # fist floor (striking end)
    kb = wall * 1.5                             # knuckle bulge
    wr = wall * 0.5                             # wrist
    if cuff == 'long':
        cuff_top, fl, rake, point, rim_roll = 1.0, wall + 0.06, 0.14, 0.3, 0.02
    elif cuff == 'bell':
        cuff_top, fl, rake, point, rim_roll = 0.86 - (0.04 if claws else 0.0), wall + 0.16 * chunky, 0.1, 0.0, 0.045
    else:
        cuff_top, fl, rake, point, rim_roll = 1.0 - (0.08 if claws else 0.0), wall + 0.11 * chunky, 0.2, 0.0, 0.025
    body, glow = [], []

    # Outer surface offset d(z) of the whole gauntlet (knuckle bulge -> narrow wrist -> cuff).
    # Every plate is seated on (and tilted with) this surface so nothing floats.
    mid = [(wr + (fl - wr) * 0.3, hs_top + (cuff_top - 0.08 - hs_top) * 0.55)] if cuff == 'bell' else []
    surf = [(kb, zb + 0.08), (kb, 0.1), (wr, hs_top)] + mid + [(fl, cuff_top - 0.08)]

    def sd(z):
        for (d0, z0), (d1, z1) in zip(surf[:-1], surf[1:]):
            if z <= z1:
                return d0 + (d1 - d0) * max(0.0, z - z0) / max(z1 - z0, 1e-6)
        return surf[-1][0]

    def slope(z):                               # tilt (rad) of the surface at z, + = leaning outward going up
        return math.atan2(sd(z + 0.02) - sd(z - 0.02), 0.04)

    def seat(obj, zc, dz=0.0):
        """obj built centred on z=0 in the XZ plane -> stand it on the front surface at height zc."""
        obj.rotation_euler = (slope(zc), 0, 0)
        obj.location = (0, -(HALF + sd(zc)) - dz, zc)
        return obj

    def seat_chord(obj, z0, z1, zc):
        """Stand a tall plate on the chord of the surface between z0 and z1 (touches both ends) so a concave
        bell flare cannot swallow its upper half."""
        a = math.atan2(sd(z1) - sd(z0), z1 - z0)
        obj.rotation_euler = (a, 0, 0)
        obj.location = (0, -(HALF + sd(z0) + (sd(z1) - sd(z0)) * (zc - z0) / (z1 - z0)), zc)
        return obj

    # cuff rim is cut on a slant: the front (-Y, outer forearm) rides higher than the back, like a real
    # gauntlet cuff; slender races also get a pointed (V) front, rising to a tip over the forearm
    zs = hs_top + 0.06

    def shear(x, y, z):
        w = max(0.0, min(1.0, (z - zs) / (cuff_top - zs)))
        v = point * max(0.0, -y) / 0.6 * max(0.0, 1.0 - abs(x) / 0.62) if point else 0.0
        return z + w * (rake * (-y) + v)

    # --- hand shell (primary): closed outer floor at the fist end, inner floor under the arm's bottom face
    body.append(loft('HandShell', [(0.03, zb), (kb * 0.7, zb + 0.015), (kb, zb + 0.08), (kb, 0.1), (wr, hs_top - 0.02),
                                   (wr, hs_top + 0.02), (0.0, hs_top + 0.02), (0.0, 0.0)],
                     col, M['primary'], r0=r0, steps=steps, closed=False, cap0=True, cap1=True))
    # --- cuff (secondary): profile follows the surface, rolled faceted rim, leather lining roll on top
    body.append(loft('Cuff', [(0.0, hs_top - 0.02), (wr * 0.8, hs_top - 0.02), (wr, hs_top + 0.01)] + mid +
                     [(fl, cuff_top - 0.08), (fl + rim_roll, cuff_top - 0.045), (fl - 0.01, cuff_top),
                      (wall * 0.6, cuff_top)],
                     col, M['secondary'], r0=r0, steps=steps, shear=shear))
    body.append(loft('Lining', [(0.0, cuff_top - 0.06), (wall * 0.75, cuff_top - 0.06), (wall * 0.7, cuff_top + 0.025),
                                (wall * 0.35, cuff_top + 0.045), (0.0, cuff_top + 0.02)],
                     col, M['grip'], r0=r0, steps=steps, smooth=60, shear=shear))
    # --- seated accent bands: knuckle bar, wrist joint, rim; segmented / riveted / clockwork / heavy get more
    body.append(band('KnuckleBar', zb + 0.12, 0.11, kb * 0.5, kb + 0.045, col, M['accent'], r0, steps))
    body.append(band('WristBand', hs_top, 0.1, wr * 0.4, wr + 0.06, col, M['accent'], r0, steps))
    body.append(band('RimBand', cuff_top - 0.09, 0.08 if cuff == 'bell' else 0.06, wall * 0.6,
                     fl + (0.065 if cuff == 'bell' else 0.05), col, M['accent'], r0, steps, shear=shear))
    if sil.get('segmented') or sil.get('riveted') or sil.get('clockwork') or sil.get('heavy'):
        zm = hs_top + (cuff_top - hs_top) * 0.42
        body.append(band('MidBand', zm, 0.05, wr * 0.5, sd(zm) + 0.04, col, M['accent'], r0, steps, shear=shear))

    # --- knuckle guard on the back of the hand: the race guard silhouette, wide (0.65-0.75 half-span) and
    # allowed past the shell sides and up over the wrist, so the race outline breaks the box silhouette
    gz = 0.2
    gw = 0.65 + 0.1 * max(0.0, min(1.0, (chunky - 0.9) / 0.35))
    g = _clip(core.guard_shape(style, gw, 0.24), -HALF - kb - 0.26, zb + 0.1 - gz, HALF + kb + 0.26, hs_top + 0.1 - gz)
    if not g.is_empty:
        body.append(seat(core.plate('KnuckleGuard', g, 0.2, col, M['secondary'], chamfer=0.035), gz))
    boss = core.motif_plate('KnuckleBoss', style, 0.2, 0, 0, 0.26, col, M['glow'], key='motif2')
    if boss is not None:
        glow.append(seat(boss, gz))
        body.append(seat(core.plate('BossSeat', Point(0, 0).buffer(0.14, 16).difference(Point(0, 0).buffer(0.105, 16)),
                                    0.25, col, M['accent'], chamfer=0.02), gz))

    # --- cuff plate on the forearm front: pointed shield carrying the race motif inlay (focal emblem)
    cz0 = hs_top + 0.08
    cz1 = cuff_top + (0.02 if cuff == 'long' else (0.06 if claws or cuff == 'bell' else 0.1))
    czc = (cz0 + cz1) / 2 - 0.04
    pw = 0.4 if not slender else 0.34
    cp = _crest(tip, 'arch' if sil.get('round') or sil.get('organic') else None, pw, cz0, cz1)
    ch0, ch1 = cz0 + 0.04, min(cz1, cuff_top - 0.06)
    body.append(seat_chord(core.plate('CuffPlate', core.place(cp, 0, -czc), 0.12, col, M['primary'], chamfer=0.03),
                           ch0, ch1, czc))
    lift = shear(0.0, -(HALF + sd(czc)), czc) - czc
    mot = core.motif_plate('CuffMotif', style, pw * 1.6, 0, 0.0, 0.17, col, M['accent'])
    if mot is not None:
        body.append(seat_chord(mot, ch0, ch1, czc))
    for o in body[-2:]:
        if o.name.startswith(('CuffPlate', 'CuffMotif')):
            o.location.z += lift

    # --- striking end: fanned talons (hooked / feral races, long) or raked knuckle studs from the race pommel
    # profile (heavy races: three big studs, others four)
    if claws:
        cl_len = 0.55
        cw = 0.2 * bl.get('width', 1.0) * (1.12 if heavy else 1.0)
        for i, (x, fan, hook) in enumerate(((-0.34, -14, 0.12), (0.0, 0, 0.07), (0.34, 14, -0.12))):
            sh = _talon(cl_len * (1.05 if x == 0 else 1.0), cw, hook)
            sh = core.place(sh, 0, 0, rot=fan)
            c = core.blade(f'Claw{i}', sh, cl_len, col, M['primary'], thickness=0.1, bevel=0.035)
            c.rotation_euler = (math.radians(-40), 0, 0)             # rake forward
            c.location = (x, -0.14, zb + 0.07)
            body.append(c)
    else:
        sc, xs = (1.4, (-0.36, 0.0, 0.36)) if heavy else (0.8, (-0.4, -0.135, 0.135, 0.4))
        a = math.radians(-38)
        for i, x in enumerate(xs):
            parts = core.pommel(f'Stud{i}', style, 0.0, col, M['accent'] if heavy else M['primary'], scale=sc)
            for p in parts:      # raked forward over the front-bottom edge so they read from the front
                lz = p.location.z
                p.rotation_euler = (a, 0, 0)
                p.location = (x, -HALF + 0.1 + lz * math.sin(a), zb + 0.05 + lz * math.cos(a))
            body += parts

    # --- outer forearm fin (+X, mirrored to the outside on the left): form picked by silhouette flags,
    # rooted on a seated accent block in the cuff wall and fitted to the R6 length budget
    form = _fin_form(sil, heavy, slender)
    if form in ('pauldron', 'lames'):
        fz = hs_top - 0.02
    elif form == 'gear':
        fz = hs_top + 0.06
    elif form == 'swept':
        fz = hs_top + 0.18
    elif form == 'quill':
        fz = hs_top
    else:                                       # blade, petal, leaf
        fz = hs_top + 0.04
    fx = HALF + sd(fz)
    bpy.context.view_layer.update()
    lo, _hi = stage.bounds(body + glow)
    fins = _fit(_fin_parts(form, style, fx - 0.05, fz, cuff_top, hs_top), (fx - 0.05, fz), lo.z + 1.68)
    keep = box(HALF + 0.015, -5, 5, 5)          # never cut into the arm itself
    for p in fins:
        shp = p['shape'].intersection(keep).buffer(0)
        if shp.is_empty or shp.area < 1e-4:
            continue
        if p['kind'] == 'blade':
            body.append(core.blade(p['name'], shp, 1.0, col, M[p['role']], thickness=p['t']))
        else:
            body.append(core.plate(p['name'], shp, p['t'], col, M[p['role']], chamfer=p['chamfer']))
    zr0 = fz - 0.3 if form == 'swept' else fz - 0.12
    body.append(core.plate('FinRoot', core.poly([(fx - 0.07, zr0 - 0.05), (fx + 0.07, zr0), (fx + 0.1, fz + 0.1),
                                                 (fx - 0.04, fz + 0.18)]), 0.26, col, M['accent'], chamfer=0.03))
    hand = (0.0, 0.0, 0.0)
    # left gauntlet = X mirror of the right one; the glow boss is mirrored too (the pipeline strips Body faces
    # hidden behind glow parts, so a Body-only mirror would leave a hole under the boss)
    mirrors = {'L': 'Body'}
    if glow:
        mirrors['L_Glow'] = 'Glow'
    return dict(body=body, glow=glow, grip=hand, mirror_pieces=mirrors,
                attachments={'Grip': hand, 'VFX_Knuckle': (0, -HALF + 0.05, zb - 0.12),
                             'VFX_Cuff': (0, -(HALF + sd(czc)) - 0.08, czc + lift)})
