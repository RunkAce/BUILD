"""One-handed sword (reference template). Reads: style blade dict, guard, pommel, motif, mats roles."""
import core


def build(style, ctx):
    col, M = ctx['col'], ctx['mats']
    bl = style.get('blade', {})
    chunky = style.get('silhouette', {}).get('chunky', 1.0)
    L = 2.85                                   # blade length
    W = 0.46 * bl.get('width', 1.0) * chunky   # blade width
    grip_top, grip_bot = -0.06, -0.80
    body, glow = [], []
    shape = core.blade_outline(L, W, edge=bl.get('edge', 'straight'), tip=bl.get('tip', 'point'),
                               holes=bl.get('holes', 'none'), notch=bl.get('notch', 'none'))
    body.append(core.blade('Blade', core.place(shape, 0, 0.12), L, col, M['primary'], thickness=0.13))
    g = core.guard_shape(style, 0.62 * chunky, 0.26)
    body.append(core.plate('Guard', core.place(g, 0, 0.06), 0.26, col, M['secondary'], chamfer=0.04))
    # race motif: seated as an inlay at the blade root (through-slab slightly thicker than the blade)
    m = core.motif_plate('RootMotif', style, W * 0.62, 0, 0.12 + W * 0.45, 0.15, col, M['accent'])
    if m is not None:
        body.append(m)
    boss = core.motif_plate('GuardBoss', style, 0.22, 0, 0.06, 0.32, col, M['accent'], key='motif2')
    if boss is not None:
        body.append(boss)
    body.append(core.collar('Collar', grip_top + 0.02, col, M['accent'], r=0.115, h=0.07))
    body.append(core.grip('Grip', grip_bot, grip_top, style, col, M['grip']))
    body.append(core.collar('LowerCollar', grip_bot - 0.02, col, M['accent'], r=0.11, h=0.06))
    body += core.pommel('Pommel', style, grip_bot - 0.05, col, M['secondary'])
    return dict(body=body, glow=glow, grip=(0, 0, grip_top - 0.2),
                attachments={'Grip': (0, 0, grip_top - 0.2), 'VFX_Tip': (0, 0, 0.12 + L), 'VFX_Guard': (0, 0, 0.06)})
