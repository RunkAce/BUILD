"""Dagger: compact one-hand blade with a strong guard + pommel personality.

Structure (z up): tapered race blade (edge/tip/holes/notch/single_edge, curved for curving races) rising out
of a seated root langet (secondary) that carries the race motif inlay (focal), an oversized race guard with a
motif-cut boss, a short wrapped grip between faceted collars, and a heavy race pommel whose waist holds the
motif2 gem (the single glow accent). Reads: blade dict, guard, pommel, grip_wraps, motif, motif2,
silhouette (chunky, slender, heavy/tool, curve, spikes), mats roles."""
import math

from shapely.geometry import Point, box
from shapely.ops import transform, unary_union

import core
import geo


def _taper(shape, L, k):
    """Narrow a blade toward its tip (dagger read) while keeping the race edge styling."""
    return transform(lambda x, z: (x * (1.0 - k * min(max(z, 0.0), L) / L), z), shape.segmentize(0.02)).buffer(0)


def _pommel_band(style, scale, frac=0.85):
    """Widest radius of the race pommel profile and the z band (below the pommel top) where r >= frac * max."""
    prof = core.POMMELS.get(style.get('pommel', 'faceted')) or core.POMMELS['cap']
    rmax = max(p[0] for p in prof)
    thr = rmax * frac
    zs = []
    for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
        for k in range(11):
            t = k / 10
            if r0 + (r1 - r0) * t >= thr - 1e-9:
                zs.append(z0 + (z1 - z0) * t)
    return rmax * scale, max(zs) * scale, min(zs) * scale


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    sil = style.get('silhouette', {})
    chunky = sil.get('chunky', 1.0)
    slender = sil.get('slender', False)
    heavy = sil.get('heavy') or sil.get('tool') or chunky >= 1.2
    edge, tip = bl.get('edge', 'straight'), bl.get('tip', 'point')
    body, glow = [], []

    L = 1.3 + (0.12 if slender else 0.0) - (0.06 if heavy else 0.0)   # blade length
    W = 0.36 * min(bl.get('width', 1.0), 1.1) * min(chunky, 1.04) * (0.86 if slender else 1.0)
    root_z = 0.16                                                      # blade root (above guard)
    grip_top, grip_bot = -0.07, -0.55

    # --- blade
    shape = core.blade_outline(L, W, edge=edge, tip=tip, holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'),
                               single_edge=bl.get('single_edge', False))
    shape = _taper(shape, L, 0.42 if (tip == 'chisel' or edge == 'broad') else 0.34)
    curve = sil.get('curve', 0.0)
    if curve > 0.05:
        shape = core.bend(shape, curve * 0.55)
    # porthole / coin slot (inlaid race holes) just above the langet chevron
    shape, hole_parts = core.inlaid_hole(shape, bl.get('holes', 'none'), 0.37 + (0.04 if slender else 0.0))
    if sil.get('spikes') and edge not in ('serrated', 'jagged'):
        # saw-back spine teeth near the root on the -X edge
        teeth = unary_union([core.poly([(-W * 0.42, z), (-W * 0.62, z + 0.05), (-W * 0.4, z + 0.09)])
                             for z in (0.22, 0.34, 0.46)])
        shape = shape.union(teeth).buffer(0)
    body.append(core.blade('Blade', core.place(shape, 0, root_z - 0.06), L, col, M['primary'], thickness=0.12))
    body += core.inlay_parts('Blade', hole_parts, col, M, 0.12, place_fn=lambda g: core.place(g, 0, root_z - 0.06))

    # --- root langet: a slim seated chevron gripping the blade root, carries the race motif (focal emblem)
    lw = W * 0.5 + 0.06
    lang_top = root_z + 0.3 + (0.04 if slender else 0.0)
    if sil.get('round') or sil.get('organic'):
        lang = unary_union([box(-lw, root_z - 0.12, lw, lang_top - lw), Point(0, lang_top - lw).buffer(lw, 16)])
    else:
        lang = core.poly([(-lw, root_z - 0.12), (lw, root_z - 0.12), (lw, lang_top - 0.16), (0, lang_top),
                          (-lw, lang_top - 0.16)])
    body.append(core.plate('Langet', lang, 0.17, col, M['secondary'], chamfer=0.03))
    # --- oversized guard (race shape)
    gw = (0.44 if not slender else 0.4) * min(chunky, 1.2)
    g = core.guard_shape(style, gw, 0.24)
    msz = min(lw * 1.7, 0.34)
    mz, mt = root_z + 0.04, 0.21
    on_guard = g.buffer(-0.02).contains(Point(0, mz))
    if on_guard:
        # a disc / tsuba guard swallows the langet: the motif becomes the guard's front boss instead
        msz, mz, mt = min(0.3, g.bounds[3] * 1.1), g.bounds[3] * 0.3, 0.31
    m = core.motif_plate('RootMotif', style, msz, 0, mz, mt, col, M['accent'])
    if m is not None:
        body.append(m)
    body.append(core.plate('Guard', core.place(g, 0, 0.0), 0.26, col, M['secondary'], chamfer=0.04))
    if not on_guard:
        body.append(core.plate('GuardBand', box(-lw - 0.03, -0.045, lw + 0.03, 0.055), 0.3, col, M['accent'],
                               chamfer=0.03))

    # --- grip: short, chunky, between faceted collars
    body.append(core.collar('Collar', grip_top + 0.01, col, M['accent'], r=0.12, h=0.08))
    wraps = max(4, round(style.get('grip_wraps', 6) * 0.7))           # short grip: keep the sword's strap pitch
    body.append(geo.wrapped_grip('Grip', grip_bot, grip_top, 0.088, wraps=wraps, segments=12, col=col,
                                 material=M['grip'], style='strap'))
    body.append(core.collar('LowerCollar', grip_bot - 0.02, col, M['accent'], r=0.115, h=0.07))

    # --- heavy pommel with the motif2 gem through its widest waist (single emissive accent)
    long_pommel = style.get('pommel') in ('spike', 'fang')
    psc = (1.4 if not slender else 1.25) * (0.82 if long_pommel else 1.0)
    pz = grip_bot - 0.06
    body += core.pommel('Pommel', style, pz, col, M['secondary'], scale=psc)
    seg = 4 if style.get('pommel') in ('spike', 'fang') else 8
    rmax, zt, zl = _pommel_band(style, psc)
    frac = 0.85
    flat_lo, flat_hi = frac * rmax * math.cos(math.pi / seg), rmax * math.cos(math.pi / seg)
    gsz = min(0.18, (zt - zl) * 0.95, 2 * frac * rmax * math.sin(math.pi / seg) * 1.05)
    gt = flat_hi - flat_lo + 0.04                       # back buried in the narrowest flat, front proud of the widest
    for side in (-1, 1):                                # gem on the front and back flats of the pommel waist
        gem = core.motif_plate(f'PommelGem{side + 1}', style, gsz, 0, pz + (zt + zl) / 2, gt, col, M['glow'],
                               key='motif2')
        if gem is not None:
            gem.location.y = side * (flat_lo - 0.02 + gt / 2)
            glow.append(gem)

    tip_z = root_z - 0.06 + L
    return dict(body=body, glow=glow, grip=(0, 0, (grip_top + grip_bot) / 2),
                attachments={'Grip': (0, 0, (grip_top + grip_bot) / 2), 'VFX_Tip': (0, 0, tip_z),
                             'VFX_Guard': (0, 0, 0.0)})
