"""Stylized painted materials and texture baking for Roblox SurfaceAppearance.

Each material is a procedural 'paint' shader that computes, per surface point:
  * PAINT  - hand-painted base colour: cavity/AO darkening, worn bright edges,
             warm->cool length gradient, broad brush variation and streaks.
  * ROUGH  - roughness (edges polished slightly smoother than faces).
  * METAL  - metalness.
  * NRM    - shading normal: rounded micro-bevel on every hard edge + material relief
             (hammered metal, leather wrap grain, cloth weave, engraved filigree).
bake_maps() bakes those into real UV textures:
  ColorMap (sRGB), NormalMap (tangent space, OpenGL/Y+), RoughnessMap, MetalnessMap,
which are exactly the four channels Roblox SurfaceAppearance accepts.
"""
import os

import bpy


def _hex(h):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


# Palette from the brief, with PBR-correct metalness: metals are 1.0 (base colour = reflectance tint),
# dielectrics are 0.0. Enamel ('chip') wears through at edges to bare forged steel underneath.
# rough = face roughness; edges polish toward rough-0.2, cavities get rougher, smudge noise varies faces.
PALETTE = {
    'ivory':     dict(base='#DCD2B8', light='#F7F1E2', dark='#8E8068', rough=0.42, metal=1.0, relief='hammered', paint_light=0.55),
    'pearl':     dict(base='#D5D2CA', light='#F6F5F0', dark='#7F8689', rough=0.46, metal=1.0, relief='hammered', paint_light=0.55),
    'vermilion': dict(base='#B93C2B', light='#E06A52', dark='#5A1F1A', rough=0.38, metal=0.0, relief='hammered', chip=0.55),
    'deepred':   dict(base='#702D27', light='#A8483B', dark='#36130F', rough=0.42, metal=0.0, relief='hammered', chip=0.5),
    'charcoal':  dict(base='#2E2F33', light='#57534F', dark='#17181B', rough=0.78, metal=0.0, relief='leather'),
    'gold':      dict(base='#B9925A', light='#F0D298', dark='#5A3F22', rough=0.28, metal=1.0, relief='filigree', paint_light=0.5),
    'gold_plain': dict(base='#B9925A', light='#F0D298', dark='#5A3F22', rough=0.26, metal=1.0, relief='hammered', paint_light=0.5),
    'darksteel': dict(base='#5A5E64', light='#A9AFB5', dark='#202225', rough=0.42, metal=1.0, relief='hammered', paint_light=0.5),
    'cloth':     dict(base='#E8DFC9', light='#FBF7EC', dark='#9C917A', rough=0.9, metal=0.0, relief='weave'),
    'amber':     dict(base='#F09A2E', light='#FFC870', dark='#A8420C', rough=0.12, metal=0.0, relief='none', emit=1.6),
}
CHIP_STEEL = '#B8B6B0'   # bare forged steel revealed by enamel chips


def _n(nt, kind, loc, **inputs):
    node = nt.nodes.new(kind)
    node.location = loc
    for k, v in inputs.items():
        node.inputs[k].default_value = v
    return node


def painted(name, spec, height=1.0, bevel_radius=0.012, ao_dist=0.12, streak=1.0, seed=0.0, paint_light=1.0):
    """Create the procedural paint material. height = weapon length (for the gradient)."""
    spec = dict(PALETTE[spec]) if isinstance(spec, str) else dict(spec)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = _n(nt, 'ShaderNodeOutputMaterial', (1400, 0))
    tc = _n(nt, 'ShaderNodeTexCoord', (-1400, 0))
    geom = _n(nt, 'ShaderNodeNewGeometry', (-1400, -300))

    # --- edge mask from bevel vs true normal
    bev = _n(nt, 'ShaderNodeBevel', (-1200, -300))
    bev.samples = 8
    bev.inputs['Radius'].default_value = bevel_radius
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.location = (-1000, -300)
    L.new(bev.outputs['Normal'], dot.inputs[0]); L.new(geom.outputs['Normal'], dot.inputs[1])
    edge = nt.nodes.new('ShaderNodeMapRange'); edge.location = (-820, -300)
    edge.inputs['From Min'].default_value = 0.998; edge.inputs['From Max'].default_value = 0.92
    L.new(dot.outputs['Value'], edge.inputs['Value'])

    # --- cavity from AO
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', (-1200, 200))
    ao.samples = 16
    ao.inputs['Distance'].default_value = ao_dist
    cav = nt.nodes.new('ShaderNodeMapRange'); cav.location = (-1000, 200)
    cav.inputs['From Min'].default_value = 0.35; cav.inputs['From Max'].default_value = 1.0
    L.new(ao.outputs['AO'], cav.inputs['Value'])

    # --- broad brush variation + stretched streaks (object space)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1200, 500)
    L.new(tc.outputs['Object'], sep.inputs[0])
    big = nt.nodes.new('ShaderNodeTexNoise'); big.location = (-1000, 520)
    big.noise_dimensions = '4D'
    for k, v in (('Scale', 1.6 / max(height, 0.1)), ('Detail', 2.0), ('Roughness', 0.5), ('W', seed)):
        big.inputs[k].default_value = v
    L.new(tc.outputs['Object'], big.inputs['Vector'])
    st_map = nt.nodes.new('ShaderNodeMapping'); st_map.location = (-1200, 750)
    st_map.inputs['Scale'].default_value = (9.0, 9.0, 1.2)
    L.new(tc.outputs['Object'], st_map.inputs['Vector'])
    streaks = _n(nt, 'ShaderNodeTexNoise', (-1000, 760), Scale=3.0, Detail=4.0, Roughness=0.6)
    L.new(st_map.outputs['Vector'], streaks.inputs['Vector'])

    # length gradient (base of weapon slightly warmer/darker, tip lighter/cooler)
    grad = nt.nodes.new('ShaderNodeMapRange'); grad.location = (-1000, 950)
    grad.inputs['From Min'].default_value = -0.35 * height; grad.inputs['From Max'].default_value = 0.85 * height
    L.new(sep.outputs['Z'], grad.inputs['Value'])

    # --- colour stack
    base = _hex(spec['base']); light = _hex(spec['light']); dark = _hex(spec['dark'])
    c0 = _n(nt, 'ShaderNodeMix', (-600, 400)); c0.data_type = 'RGBA'
    c0.inputs['A'].default_value = dark; c0.inputs['B'].default_value = base
    L.new(cav.outputs['Result'], c0.inputs['Factor'])
    # broad variation: lerp toward light/dark by noise
    var = nt.nodes.new('ShaderNodeMapRange'); var.location = (-800, 520)
    var.inputs['From Min'].default_value = 0.35; var.inputs['From Max'].default_value = 0.65
    var.inputs['To Min'].default_value = -0.22; var.inputs['To Max'].default_value = 0.22
    L.new(big.outputs['Fac'], var.inputs['Value'])
    strk = nt.nodes.new('ShaderNodeMapRange'); strk.location = (-800, 760)
    strk.inputs['From Min'].default_value = 0.4; strk.inputs['From Max'].default_value = 0.6
    strk.inputs['To Min'].default_value = -0.12 * streak; strk.inputs['To Max'].default_value = 0.12 * streak
    L.new(streaks.outputs['Fac'], strk.inputs['Value'])
    gr = nt.nodes.new('ShaderNodeMapRange'); gr.location = (-800, 950)
    gr.inputs['To Min'].default_value = -0.06; gr.inputs['To Max'].default_value = 0.08
    L.new(grad.outputs['Result'], gr.inputs['Value'])
    s1 = nt.nodes.new('ShaderNodeMath'); s1.operation = 'ADD'; s1.location = (-600, 700)
    L.new(var.outputs['Result'], s1.inputs[0]); L.new(strk.outputs['Result'], s1.inputs[1])
    s2 = nt.nodes.new('ShaderNodeMath'); s2.operation = 'ADD'; s2.location = (-450, 700)
    L.new(s1.outputs[0], s2.inputs[0]); L.new(gr.outputs['Result'], s2.inputs[1])
    up = nt.nodes.new('ShaderNodeMath'); up.operation = 'MAXIMUM'; up.location = (-300, 760); up.inputs[1].default_value = 0
    L.new(s2.outputs[0], up.inputs[0])
    dn = nt.nodes.new('ShaderNodeMath'); dn.operation = 'MINIMUM'; dn.location = (-300, 640); dn.inputs[1].default_value = 0
    L.new(s2.outputs[0], dn.inputs[0])
    dn_abs = nt.nodes.new('ShaderNodeMath'); dn_abs.operation = 'ABSOLUTE'; dn_abs.location = (-150, 640)
    L.new(dn.outputs[0], dn_abs.inputs[0])
    c1 = _n(nt, 'ShaderNodeMix', (-150, 400)); c1.data_type = 'RGBA'; c1.inputs['B'].default_value = light
    L.new(c0.outputs['Result'], c1.inputs['A']); L.new(up.outputs[0], c1.inputs['Factor'])
    c2 = _n(nt, 'ShaderNodeMix', (0, 400)); c2.data_type = 'RGBA'; c2.inputs['B'].default_value = dark
    L.new(c1.outputs['Result'], c2.inputs['A']); L.new(dn_abs.outputs[0], c2.inputs['Factor'])
    # painted key light, fixed in OBJECT space (hand-painted look that survives any game lighting).
    # |n.y| makes front and rear faces read identically; left/top bevels catch light, right/bottom fall to shadow.
    nsep = nt.nodes.new('ShaderNodeSeparateXYZ'); nsep.location = (-1200, -700)
    L.new(tc.outputs['Normal'], nsep.inputs[0])
    ny = nt.nodes.new('ShaderNodeMath'); ny.operation = 'ABSOLUTE'; ny.location = (-1050, -700)
    L.new(nsep.outputs['Y'], ny.inputs[0])
    ncomb = nt.nodes.new('ShaderNodeCombineXYZ'); ncomb.location = (-900, -700)
    L.new(nsep.outputs['X'], ncomb.inputs['X']); L.new(ny.outputs[0], ncomb.inputs['Y']); L.new(nsep.outputs['Z'], ncomb.inputs['Z'])
    ldot = nt.nodes.new('ShaderNodeVectorMath'); ldot.operation = 'DOT_PRODUCT'; ldot.location = (-750, -700)
    ldot.inputs[1].default_value = (-0.52, 0.56, 0.64)
    L.new(ncomb.outputs[0], ldot.inputs[0])
    lit = nt.nodes.new('ShaderNodeMapRange'); lit.location = (-600, -620)
    lit.inputs['From Min'].default_value = 0.56; lit.inputs['From Max'].default_value = 1.0
    paint_light = spec.get('paint_light', paint_light)
    lit.inputs['To Max'].default_value = 0.55 * paint_light
    L.new(ldot.outputs['Value'], lit.inputs['Value'])
    shd = nt.nodes.new('ShaderNodeMapRange'); shd.location = (-600, -820)
    shd.inputs['From Min'].default_value = 0.5; shd.inputs['From Max'].default_value = -0.4
    shd.inputs['To Max'].default_value = 0.6 * paint_light
    L.new(ldot.outputs['Value'], shd.inputs['Value'])
    c2a = _n(nt, 'ShaderNodeMix', (60, 250)); c2a.data_type = 'RGBA'; c2a.inputs['B'].default_value = light
    L.new(c2.outputs['Result'], c2a.inputs['A']); L.new(lit.outputs['Result'], c2a.inputs['Factor'])
    c2b = _n(nt, 'ShaderNodeMix', (120, 250)); c2b.data_type = 'RGBA'; c2b.inputs['B'].default_value = dark
    L.new(c2a.outputs['Result'], c2b.inputs['A']); L.new(shd.outputs['Result'], c2b.inputs['Factor'])
    c2 = c2b
    # worn bright edges, broken up by noise so highlights are painted, not uniform
    edge_brk = nt.nodes.new('ShaderNodeMath'); edge_brk.operation = 'MULTIPLY'; edge_brk.location = (-450, 150)
    L.new(edge.outputs['Result'], edge_brk.inputs[0])
    eb = nt.nodes.new('ShaderNodeMapRange'); eb.location = (-650, 150)
    eb.inputs['From Min'].default_value = 0.3; eb.inputs['From Max'].default_value = 0.6
    eb.inputs['To Min'].default_value = 0.45; eb.inputs['To Max'].default_value = 1.0
    L.new(streaks.outputs['Fac'], eb.inputs['Value']); L.new(eb.outputs['Result'], edge_brk.inputs[1])
    c3 = _n(nt, 'ShaderNodeMix', (200, 300)); c3.data_type = 'RGBA'; c3.inputs['B'].default_value = light
    L.new(c2.outputs['Result'], c3.inputs['A']); L.new(edge_brk.outputs[0], c3.inputs['Factor'])
    paint = c3
    paint.label = 'PAINT'

    # --- PBR roughness / metalness
    # smudge: broad noise so faces are not uniformly glossy
    smudge = _n(nt, 'ShaderNodeTexNoise', (-200, -60), Scale=4.0 / max(height, 0.3), Detail=3.0, Roughness=0.55)
    L.new(tc.outputs['Object'], smudge.inputs['Vector'])
    sm = nt.nodes.new('ShaderNodeMapRange'); sm.location = (0, -60)
    sm.inputs['From Min'].default_value = 0.35; sm.inputs['From Max'].default_value = 0.65
    sm.inputs['To Min'].default_value = -0.07; sm.inputs['To Max'].default_value = 0.09
    L.new(smudge.outputs['Fac'], sm.inputs['Value'])
    epol = nt.nodes.new('ShaderNodeMath'); epol.operation = 'MULTIPLY'; epol.location = (0, -160)
    epol.inputs[1].default_value = -0.2
    L.new(edge.outputs['Result'], epol.inputs[0])
    cavr = nt.nodes.new('ShaderNodeMapRange'); cavr.location = (0, -260)
    cavr.inputs['To Min'].default_value = 0.16; cavr.inputs['To Max'].default_value = 0.0
    L.new(cav.outputs['Result'], cavr.inputs['Value'])
    r1 = nt.nodes.new('ShaderNodeMath'); r1.operation = 'ADD'; r1.location = (150, -100)
    r1.inputs[0].default_value = spec['rough']
    L.new(sm.outputs['Result'], r1.inputs[1])
    r2 = nt.nodes.new('ShaderNodeMath'); r2.operation = 'ADD'; r2.location = (250, -140)
    L.new(r1.outputs[0], r2.inputs[0]); L.new(epol.outputs[0], r2.inputs[1])
    r3 = nt.nodes.new('ShaderNodeMath'); r3.operation = 'ADD'; r3.location = (350, -180); r3.use_clamp = True
    L.new(r2.outputs[0], r3.inputs[0]); L.new(cavr.outputs['Result'], r3.inputs[1])
    rough_out = r3.outputs[0]
    metal_val = nt.nodes.new('ShaderNodeValue'); metal_val.location = (150, -300)
    metal_val.outputs[0].default_value = spec['metal']
    metal_out = metal_val.outputs[0]
    color_out = paint.outputs['Result']

    chip_amt = spec.get('chip', 0.0)
    if chip_amt:
        # enamel chips: only on worn edges, broken up by fine noise -> bare steel (metal 1, glossier)
        cn = _n(nt, 'ShaderNodeTexNoise', (-200, -420), Scale=18.0, Detail=6.0, Roughness=0.7)
        L.new(tc.outputs['Object'], cn.inputs['Vector'])
        cm = nt.nodes.new('ShaderNodeMath'); cm.operation = 'MULTIPLY'; cm.location = (0, -420)
        L.new(edge.outputs['Result'], cm.inputs[0]); L.new(cn.outputs['Fac'], cm.inputs[1])
        chip = nt.nodes.new('ShaderNodeMapRange'); chip.location = (150, -420); chip.label = 'CHIP'
        chip.inputs['From Min'].default_value = 0.42 * (1.2 - chip_amt)
        chip.inputs['From Max'].default_value = 0.42 * (1.2 - chip_amt) + 0.04
        L.new(cm.outputs[0], chip.inputs['Value'])
        cc = _n(nt, 'ShaderNodeMix', (350, 300)); cc.data_type = 'RGBA'; cc.inputs['B'].default_value = _hex(CHIP_STEEL)
        L.new(paint.outputs['Result'], cc.inputs['A']); L.new(chip.outputs['Result'], cc.inputs['Factor'])
        color_out = cc.outputs['Result']
        mm = nt.nodes.new('ShaderNodeMix'); mm.location = (350, -320); mm.data_type = 'FLOAT'
        mm.inputs['B'].default_value = 1.0
        L.new(metal_out, mm.inputs['A']); L.new(chip.outputs['Result'], mm.inputs['Factor'])
        metal_out = mm.outputs['Result']
        rm = nt.nodes.new('ShaderNodeMix'); rm.location = (450, -200); rm.data_type = 'FLOAT'
        rm.inputs['B'].default_value = 0.3
        L.new(rough_out, rm.inputs['A']); L.new(chip.outputs['Result'], rm.inputs['Factor'])
        rough_out = rm.outputs['Result']
    # tag outputs for the baker
    for out_sock, lab in ((color_out, 'PAINT_OUT'), (rough_out, 'ROUGH'), (metal_out, 'METAL')):
        r = nt.nodes.new('NodeReroute'); r.label = lab; r.location = (600, {'PAINT_OUT': 200, 'ROUGH': -100, 'METAL': -300}[lab])
        L.new(out_sock, r.inputs[0])

    # --- normal: micro-bevel + material relief
    relief = spec.get('relief', 'none')
    bump = _n(nt, 'ShaderNodeBump', (600, -450), Strength=0.0, Distance=0.004)
    if relief != 'none':
        if relief == 'hammered':
            tex = _n(nt, 'ShaderNodeTexVoronoi', (300, -500), Scale=38.0 / max(height, 0.5) * 4)
            src = tex.outputs['Distance']; bump.inputs['Strength'].default_value = 0.07
        elif relief == 'leather':
            mp = nt.nodes.new('ShaderNodeMapping'); mp.location = (100, -650)
            mp.inputs['Scale'].default_value = (60.0, 60.0, 60.0)
            L.new(tc.outputs['Object'], mp.inputs['Vector'])
            tex = _n(nt, 'ShaderNodeTexNoise', (300, -500), Scale=1.0, Detail=8.0, Roughness=0.7)
            L.new(mp.outputs['Vector'], tex.inputs['Vector'])
            src = tex.outputs['Fac']; bump.inputs['Strength'].default_value = 0.35
        elif relief == 'weave':
            tex = _n(nt, 'ShaderNodeTexWave', (300, -500), Scale=120.0, Distortion=0.5)
            tex.wave_type = 'BANDS'
            src = tex.outputs['Fac']; bump.inputs['Strength'].default_value = 0.12
        else:  # filigree: interlocking engraved swirl lines, read as engraving at game distance
            tex = _n(nt, 'ShaderNodeTexWave', (300, -500), Scale=14.0, Distortion=9.0, Detail=3.0)
            tex.wave_type = 'RINGS'; tex.wave_profile = 'SIN'
            src = tex.outputs['Fac']; bump.inputs['Strength'].default_value = 0.55
        if relief in ('hammered', 'weave', 'filigree'):
            L.new(tc.outputs['Object'], tex.inputs['Vector'])
        L.new(src, bump.inputs['Height'])
    L.new(bev.outputs['Normal'], bump.inputs['Normal'])
    bump.label = 'NRM'

    # --- preview shader (also the NORMAL bake source)
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled', (900, 0))
    _lab = lambda lab: next(n for n in nt.nodes if n.label == lab).outputs[0]
    L.new(_lab('PAINT_OUT'), bsdf.inputs['Base Color'])
    L.new(_lab('ROUGH'), bsdf.inputs['Roughness'])
    L.new(_lab('METAL'), bsdf.inputs['Metallic'])
    L.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    if spec.get('emit'):
        L.new(paint.outputs['Result'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = spec['emit']
    L.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    emit = _n(nt, 'ShaderNodeEmission', (900, -300), Strength=1.0)
    emit.name = '_bake_emit'
    m['spec'] = {k: v for k, v in spec.items() if k != 'emit'}
    return m


def _route(mat, which):
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    emit = nt.nodes['_bake_emit']
    for l in list(out.inputs['Surface'].links):
        nt.links.remove(l)
    for l in list(emit.inputs['Color'].links):
        nt.links.remove(l)
    if which == 'normal':
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        return
    src = next(n for n in nt.nodes if n.label == {'color': 'PAINT_OUT', 'rough': 'ROUGH', 'metal': 'METAL'}[which]).outputs[0]
    nt.links.new(src, emit.inputs['Color'])
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])


def bake_maps(obj, out_dir, prefix, size=2048, margin=12, samples=32):
    """Bake ColorMap / NormalMap / RoughnessMap / MetalnessMap for obj (all its materials)."""
    os.makedirs(out_dir, exist_ok=True)
    # smoke-test override (tiny bakes): SMOKE=1
    if os.environ.get('SMOKE'):
        size, samples = 64, 1
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.render.bake.margin = margin
    sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mats = [s.material for s in obj.material_slots if s.material]
    results = {}
    for which, cs, btype in (('color', 'sRGB', 'EMIT'), ('rough', 'Non-Color', 'EMIT'),
                             ('metal', 'Non-Color', 'EMIT'), ('normal', 'Non-Color', 'NORMAL')):
        img = bpy.data.images.new(f'{prefix}_{which}', size, size, alpha=False, float_buffer=False)
        img.colorspace_settings.name = cs
        for m in mats:
            _route(m, which)
            node = m.node_tree.nodes.get('_bake_target') or m.node_tree.nodes.new('ShaderNodeTexImage')
            node.name = '_bake_target'
            node.image = img
            node.location = (1100, -600)
            m.node_tree.nodes.active = node
        if btype == 'NORMAL':
            sc.render.bake.normal_space = 'TANGENT'
            sc.render.bake.normal_r, sc.render.bake.normal_g, sc.render.bake.normal_b = 'POS_X', 'POS_Y', 'POS_Z'
            bpy.ops.object.bake(type='NORMAL')
        else:
            bpy.ops.object.bake(type='EMIT')
        name = {'color': 'ColorMap', 'rough': 'RoughnessMap', 'metal': 'MetalnessMap', 'normal': 'NormalMap'}[which]
        path = os.path.abspath(os.path.join(out_dir, f'{prefix}_{name}.png'))
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        results[name] = path
    for m in mats:
        _route(m, 'normal')
    return results


def baked_material(name, maps, emit_mask=None):
    """Material that uses ONLY the baked maps: what Roblox SurfaceAppearance will show."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']

    def tex(path, cs, loc):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = cs
        n.location = loc
        return n
    c = tex(maps['ColorMap'], 'sRGB', (-600, 300))
    r = tex(maps['RoughnessMap'], 'Non-Color', (-600, 0))
    mt = tex(maps['MetalnessMap'], 'Non-Color', (-600, -300))
    nm = tex(maps['NormalMap'], 'Non-Color', (-600, -600))
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.location = (-300, -600)
    nt.links.new(c.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
    nt.links.new(mt.outputs['Color'], bsdf.inputs['Metallic'])
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def unwrap(obj, margin=0.004, angle=60):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=__import__('math').radians(angle), island_margin=margin,
                             area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    o.data.name = name
    return o
