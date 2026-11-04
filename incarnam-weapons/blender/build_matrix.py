"""Race x category weapon matrix builder.

  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_matrix.py --race cra --cat sword --preview
  ... --race cra --cat sword                 # full: optimise, UV, bake (512), export FBX + maps + stats
  ... --sheet-cat sword [--races a,b,c]      # preview contact sheet: one category across races
  ... --sheet-race cra                       # preview contact sheet: one race across all categories
  ... --check                                # build every combination (no render), report sizes/tris/errors

Outputs: export/pack/<Race>/<WeaponName>/  (FBX, textures/, stats.json), renders/pack/...
"""
import argparse
import importlib
import json
import math
import os
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
sys.path.insert(0, os.path.join(HERE, 'lib', 'kit'))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import geo  # noqa: E402
import optimize  # noqa: E402
import paint  # noqa: E402
import pipeline  # noqa: E402
import stage  # noqa: E402
import core  # noqa: E402

ROOT = os.path.dirname(HERE)
RACES_DIR = os.path.join(HERE, 'lib', 'kit', 'races')
CATS_DIR = os.path.join(HERE, 'lib', 'kit', 'categories')
TEX = 512


def available(dirname):
    return sorted(f[:-3] for f in os.listdir(dirname) if f.endswith('.py') and not f.startswith('_'))


def load_style(race):
    mod = importlib.import_module(f'races.{race}')
    importlib.reload(mod)
    return mod.STYLE


def load_cat(cat):
    mod = importlib.import_module(f'categories.{cat}')
    importlib.reload(mod)
    return mod


def weapon_name(style, cat):
    return style['names'].get(cat) or f"{style['race']}{cat.title().replace('_', '')}"


def build_one(race, cat, fresh=True):
    if fresh:
        stage.reset_scene()
        stage.neutral_stage()
    style = load_style(race)
    over = style.get('blade_by_cat', {}).get(cat)
    if over:                      # per-category blade tweaks (e.g. a shovel-spoon spear tip for one race)
        style = dict(style, blade={**style.get('blade', {}), **over})
    mod = load_cat(cat)
    name = weapon_name(style, cat)
    col = stage.collection(name)
    lo, hi = core.SIZES[cat]['length']
    mats = core.materials(style, height=hi, prefix=name)
    ctx = dict(col=col, mats=mats, name=name, cat=cat, race=race)
    b = mod.build(style, ctx)
    b.setdefault('glow', [])
    b.setdefault('pieces', {})
    b.setdefault('mirror_pieces', {})
    b.setdefault('piece_attachments', {})
    for objs in [b['body'], b['glow']] + list(b['pieces'].values()):
        core.apply(objs)
    b['body'] = [o for o in b['body'] if o is not None]
    b['glow'] = [o for o in b['glow'] if o is not None]
    return style, name, col, mats, b


def measure(b):
    objs = b['body'] + b['glow'] + [o for v in b['pieces'].values() for o in v]
    lo, hi = stage.bounds(objs)
    return {'length': round(hi.z - lo.z, 3), 'width': round(hi.x - lo.x, 3), 'depth': round(hi.y - lo.y, 3),
            'triangles': geo.tri_count(objs)}, objs


def preview(race, cat, out_dir, res=(360, 600), views=('front', 'three_quarter', 'side'), samples=16):
    style, name, col, mats, b = build_one(race, cat)
    m, objs = measure(b)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for v in views:
        r = res if v != 'side' else (int(res[0] * 0.6), res[1])
        stage.ortho_camera(objs, v, res=r)
        paths.append(stage.render(os.path.join(out_dir, f'{race}_{cat}_{v}.png'), samples=samples))
    return name, m, paths


def contact_sheet(items, out_png, cols):
    """items: list of (label, png). Tiles with labels via ffmpeg."""
    if not items:
        return
    inputs, filters = [], []
    for i, (label, png) in enumerate(items):
        inputs += ['-i', png]
        safe = label.replace(':', ' ').replace("'", '')
        filters.append(f"[{i}]scale=300:500:force_original_aspect_ratio=decrease,pad=300:520:(ow-iw)/2:0:color=0x2e2e30,"
                       f"drawtext=text='{safe}':x=8:y=h-20:fontsize=15:fontcolor=white[v{i}]")
    rows = math.ceil(len(items) / cols)
    layout = '|'.join(f'{(i % cols) * 300}_{(i // cols) * 520}' for i in range(len(items)))
    stack = ''.join(f'[v{i}]' for i in range(len(items)))
    if len(items) == 1:
        fc = ';'.join(filters) + ';[v0]null[out]'
    else:
        fc = ';'.join(filters) + f';{stack}xstack=inputs={len(items)}:layout={layout}:fill=0x2e2e30[out]'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', fc, '-map', '[out]', out_png],
                   check=True)


def finish(race, cat):
    style, name, col, mats, b = build_one(race, cat)
    if cat in style.get('bespoke', {}):
        print('SKIP bespoke', style['bespoke'][cat])
        return style['bespoke'][cat], {}
    m, _ = measure(b)
    exp = os.path.join(ROOT, 'export', 'pack', style['race'], name)
    src = os.path.join(ROOT, 'source', 'pack', style['race'])
    os.makedirs(exp, exist_ok=True)
    gx, gy, gz = b['grip']
    off = Vector((-gx, -gy, -gz))
    # move separate pieces with the weapon (finish() shifts body + glow)
    piece_objs = [o for v in b['pieces'].values() for o in v]
    res = pipeline.finish(name, col, b['body'], ROOT, b['grip'], b.get('attachments', {'Grip': b['grip']}),
                          glow_parts=b['glow'], extra_meshes=piece_objs, tex=TEX, bake_samples=8,
                          export_dir=exp, source_dir=src, glow_mat=mats.get('glow'))
    stats = res['stats']
    stats.update(race=style['race'], category=cat, r6_target_length=core.SIZES[cat]['length'], measured=m)
    tex_dir = os.path.join(exp, 'textures')
    # separately baked pieces (e.g. thrown chain head, second gauntlet when not a mirror)
    for pname, objs in b['pieces'].items():
        objs = [o for o in objs if o is not None]
        if not objs:
            continue
        obj = paint.join(objs, f'{name}_{pname}')
        optimize.remove_hidden_faces(obj)
        paint.unwrap(obj)
        maps = paint.bake_maps(obj, tex_dir, f'{name}_{pname}', size=TEX, samples=8)
        obj.data.materials.clear()
        obj.data.materials.append(paint.baked_material(f'{name}_{pname}_Baked', maps))
        # piece attachments (e.g. the thrown head's ChainEnd), given in build coords, exported as empties
        empties = []
        patt = {}
        for an, loc in b.get('piece_attachments', {}).get(pname, {}).items():
            p = Vector(loc) + off
            e = pipeline.attachment(an, p, col)
            e.parent = obj
            empties.append(e)
            patt[an] = [round(c, 4) for c in p]
        stage.export_fbx(os.path.join(exp, f'{name}_{pname}.fbx'), [obj] + empties)
        stats.setdefault('pieces', {})[pname] = {'triangles': geo.tri_count([obj]), 'maps': sorted(maps),
                                                 'attachments': patt}
    # mirrored pieces share the source texture
    for pname, srcname in b['mirror_pieces'].items():
        srcobj = res['body'] if srcname == 'Body' else bpy.data.objects.get(f'{name}_{srcname}')
        if srcobj is None:
            continue
        c = srcobj.copy()
        c.data = srcobj.data.copy()
        c.name = c.data.name = f'{name}_{pname}'
        bpy.context.scene.collection.objects.link(c)
        c.parent = None
        c.matrix_world = srcobj.matrix_world.copy()
        c.scale = (-1, 1, 1)
        core.apply([c])
        if not geo.mesh_health(c)['normals_outward']:
            c.data.flip_normals()
        stage.export_fbx(os.path.join(exp, f'{name}_{pname}.fbx'), [c])
        stats.setdefault('pieces', {})[pname] = {'triangles': geo.tri_count([c]), 'mirror_of': srcname}
    # chain link for chain weapons (runtime system repeats it)
    if b.get('chain'):
        kind = b['chain'].get('link', style.get('chain_link', 'box'))
        mat = mats.get('secondary') or mats.get('primary')
        link = core.chain_link(f'{name}_ChainLink', kind, col, mat)
        paint.unwrap(link)
        lmaps = paint.bake_maps(link, tex_dir, f'{name}_ChainLink', size=256, samples=8)
        link.data.materials.clear()
        link.data.materials.append(paint.baked_material(f'{name}_ChainLink_Baked', lmaps))
        stage.export_fbx(os.path.join(exp, f'{name}_ChainLink.fbx'), [link])
        stats['chain'] = {'link_kind': kind, 'pitch': core.LINK['length'] - 2 * core.LINK['bar'],
                          'link_triangles': geo.tri_count([link])}
    with open(os.path.join(exp, f'{name}_stats.json'), 'w') as fh:
        json.dump(stats, fh, indent=1)
    return name, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--race')
    ap.add_argument('--cat')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--sheet-cat')
    ap.add_argument('--sheet-race')
    ap.add_argument('--races')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out')
    args = ap.parse_args([a for a in sys.argv[1:] if a != '--'])
    rdir = os.path.join(ROOT, 'renders', 'pack')
    if args.check:
        report = []
        races = args.races.split(',') if args.races else available(RACES_DIR)
        cats = [args.cat] if args.cat else available(CATS_DIR)
        for r in races:
            for c in cats:
                try:
                    style, name, col, mats, b = build_one(r, c)
                    m, _ = measure(b)
                    lo, hi = core.SIZES[c]['length']
                    ok = lo - 0.15 <= m['length'] <= hi + 0.15 and m['triangles'] <= 8000
                    report.append(dict(race=r, cat=c, name=name, ok=ok, **m))
                except Exception as e:  # noqa: BLE001
                    report.append(dict(race=r, cat=c, ok=False, error=f'{type(e).__name__}: {e}',
                                       trace=traceback.format_exc()[-800:]))
        out = args.out or os.path.join(rdir, 'check.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(report, open(out, 'w'), indent=1)
        bad = [x for x in report if not x['ok']]
        print(f'CHECK {len(report) - len(bad)}/{len(report)} ok -> {out}')
        for x in bad:
            print('  BAD', x.get('race'), x.get('cat'), x.get('error') or x)
        return
    if args.sheet_cat:
        cat = args.sheet_cat
        races = args.races.split(',') if args.races else available(RACES_DIR)
        items = []
        for r in races:
            try:
                name, m, paths = preview(r, cat, os.path.join(rdir, '_tiles'), views=('three_quarter',))
                items.append((f'{r} {name} {m["length"]}st {m["triangles"]}t', paths[0]))
            except Exception as e:  # noqa: BLE001
                print('FAIL', r, cat, e)
                traceback.print_exc()
        out = args.out or os.path.join(rdir, f'sheet_cat_{cat}.png')
        contact_sheet(items, out, cols=6)
        print('SHEET', out)
        return
    if args.sheet_race:
        race = args.sheet_race
        items = []
        for c in available(CATS_DIR):
            try:
                name, m, paths = preview(race, c, os.path.join(rdir, '_tiles'), views=('three_quarter',))
                items.append((f'{c} {name} {m["length"]}st', paths[0]))
            except Exception as e:  # noqa: BLE001
                print('FAIL', race, c, e)
                traceback.print_exc()
        out = args.out or os.path.join(rdir, f'sheet_race_{race}.png')
        contact_sheet(items, out, cols=6)
        print('SHEET', out)
        return
    if args.preview:
        name, m, paths = preview(args.race, args.cat, os.path.join(rdir, args.race, args.cat))
        print('PREVIEW', name, json.dumps(m), paths)
        return
    name, stats = finish(args.race, args.cat)
    print('DONE', name, stats.get('triangles_total'), stats.get('measured'))


if __name__ == '__main__':
    main()
