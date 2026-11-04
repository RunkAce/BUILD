# Incarnam: Iop weapon set

Four original Iop weapons built as real 3D game assets for a **Roblox R6** game:

| Weapon | What it is | Moving parts |
|---|---|---|
| **Oathsplitter** | Two-handed split greatsword with a real slot opening and twin points | none (amber heat is a separate mesh) |
| **Sunbound** | Solid broad sword, red spine, gold sun disk | short pommel streamer (skinned, 6 bones) |
| **Warlink** | Paired cleavers joined by a chain | chain built at runtime from one link mesh |
| **Flarecrest** | Spear with a flame-cut leaf blade (added at your request) | spiral ribbon (skinned, 9 bones) |

Completion status, measured numbers and known issues are in [Completion report](#completion-report) below. The concept QC is in [`docs/QC_REPORT.md`](docs/QC_REPORT.md).

---

## Folder layout

```
incarnam-weapons/
  export/<Weapon>/          FBX files for Roblox + textures/ (Color, Normal, Roughness, Metalness PNGs) + <Weapon>_stats.json
  source/<Weapon>.blend     Blender source scenes (textures packed)
  renders/<weapon>/         acceptance views (front/rear/side/3q/3q-rear, wireframe, effects off), showcase, turntable MP4
  renders/r6_scale/         every weapon next to and held by an exact-size R6 proxy
  blender/                  build scripts: one per weapon, plus lib/ (geometry, PBR paint + bake, optimiser, export)
  roblox/src/               Luau: chain system, cloth driver, R6 left-hand weld
  roblox/tools/             MeasureHandSpan (sizes the Warlink chain to your animations)
  roblox/tests/             solver tests, run in the real Luau VM
  docs/                     concept QC report + raw review data
```

## Conventions

- **Units:** 1 Blender unit = 1 stud. The FBX export converts to the 0.28 m stud, so check the size after your first import (see step 1 below).
- **Axes:** weapons are modeled pointing up (Blender +Z, which becomes Roblox +Y), with the front face toward Blender −Y. FBX is exported with `axis_up=Y`, `axis_forward=-Z`.
- **Origin:** the origin is the leading-hand grip point, so a Tool's `Grip` can start at identity.
- **Attachments** are exported as FBX empties with Roblox-style names:
  - `Grip` and `GripSecondary` for the hands.
  - `VFX_*` for effect origins: slot base, bridge, tips, gem, disk, spine tip, flame.
  - `ClothRoot` and `RibbonRoot` for cloth roots.
  - `ChainEnd` on each Warlink cleaver's eyelet.

  If your importer doesn't turn the empties into Attachments, the exact positions are listed in each `<Weapon>_stats.json` under `attachments`.
- **Materials:** one SurfaceAppearance per MeshPart (Roblox allows one per part):
  - `ColorMap` is sRGB.
  - `NormalMap` is tangent-space, OpenGL / Y+.
  - `RoughnessMap` and `MetalnessMap` are linear.

  Metals have metalness 1 and painted parts (enamel, leather, cloth) have metalness 0. Worn edges of the red enamel show bare steel.
- **Glow parts:** `<Weapon>_Glow` meshes (gems, Oathsplitter's slot heat) are separate. Set them to `Neon` material, or drive them from your VFX, and hide them for the effects-off state.

## Setting up in Roblox Studio

1. **Import one weapon first and check scale and orientation.** In Avatar or 3D Importer, import `export/Oathsplitter/Oathsplitter.fbx`. It should be about **5.9 studs** long, about 1.2× an R6's height. If it comes in wrong, fix the importer scale once and use the same setting for every weapon.
2. **Add the maps.** For each MeshPart, add a `SurfaceAppearance` and upload the four PNGs from `export/<Weapon>/textures/` to its `ColorMap`, `NormalMap`, `RoughnessMap` and `MetalnessMap`.
3. **Make the Tool.** The MeshPart named `Handle` is the one the right hand holds. On R6, Roblox's `RightGrip` holds it at `Right Arm * CFrame.new(0,-1,0) * Angles(-90°,0,0)`, so the blade points forward. Tune `Tool.Grip` if your animations expect a different hold.

### Warlink chain (custom system)

The chain is **one link mesh repeated at runtime**, not a fixed-length model. Its length is a setting, so it can match your R6 animations.

1. Put `ChainSolver`, `WarlinkChain` and `ClothSway` (from `roblox/src`) as ModuleScripts in `ReplicatedStorage.WarlinkModules`.
2. Import `Warlink_ChainLink.fbx` and `Warlink_ChainEndLink.fbx`. Give them the chain maps (`Warlink_Chain_*.png`) and put them in `ReplicatedStorage.WarlinkAssets` named `ChainLink` and `ChainEndLink`.
3. Build the Tool: `Handle` (the right cleaver, `Warlink_CleaverR`) and `CleaverL`, each with an Attachment named `ChainEnd` at the eyelet. Place `CleaverL` next to the Handle in the pose it should keep when holstered. Tag the Tool `Warlink`. Put `WarlinkTool.server.luau` inside it as a Script. On equip it welds `CleaverL` to the R6 `Left Arm`, because R6 has no left grip. When unequipped or dropped, a stow weld keeps `CleaverL` with the Handle, so it never falls out of the world. If your animations already drive the weapons with their own Motor6Ds, skip that script; the chain only needs the two `ChainEnd` attachments.
4. Put `WarlinkChainController.client.luau` in `StarterPlayerScripts`. It shows the chain for every player holding a Warlink and removes it on unequip, respawn or tool removal.
5. **Size the chain to your animations.** Put `roblox/tools/MeasureHandSpan.client.luau` in `StarterPlayerScripts`, paste your animation IDs at the top, and press Play. It plays each animation, records the widest eyelet-to-eyelet distance, and prints a `LinkCount`. Set that as a number attribute `LinkCount` on the Tool, then delete the script.
6. Optional Tool attributes:
   - `ChainMode`: `"Coil"` (the default) runs eyelet A → coil → free span → eyelet B. The spare links wind up the left forearm, following the square R6 arm at a fixed clearance and one link pitch apart, and pay out as the hands separate. `"Hang"` lets the whole chain sag, kept above the floor by a raycast.
   - `Pitch`: default 0.21, which matches the exported link.

How it behaves:
- Links never stretch while the hands are closer than the chain length.
- If an animation goes wider, the chain goes straight, every link shares the extra length evenly so no gap opens, and the console prints the `LinkCount` you need.
- It is purely visual: no collisions and no damage. Your server combat stays in charge.
- All links move in one `BulkMoveTo` per frame, and chains far from the camera update less often.

### Cloth (Sunbound streamer, Flarecrest ribbon)

1. Import `Sunbound_Streamer.fbx` and `Flarecrest_Ribbon.fbx` as **skinned** MeshParts, with bones included. Weld each one to its weapon at `ClothRoot` or `RibbonRoot`. Both rigs pass `blender/validate_rigs.py` on the re-imported FBX:
   - every vertex is weighted, with at most 4 influences, normalised;
   - there is one root bone;
   - the pinned area doesn't move when the tail is bent.
2. Put `ClothSwayController.client.luau` in `StarterPlayerScripts`. Tag the weapon Tool `ClothSway` and give it two string attributes:
   - **Sunbound:** `ClothPart` = the streamer part's name, `ClothBones` = `Cloth1,Cloth2,Cloth3,Cloth4,Cloth5`
   - **Flarecrest:** `ClothPart` = the ribbon part's name, `ClothBones` = `Ribbon1,Ribbon2,Ribbon3,Ribbon4,Ribbon5,Ribbon6,Ribbon7,Ribbon8`

How it moves:
- The root bones (`ClothRoot` and `RibbonRoot`) are never driven, so the attachment point stays pinned. On Flarecrest the whole spiral wrap is pinned and only the free tail moves.
- Sway and lag increase toward the tip, and the cloth trails behind the weapon's motion on springs, then settles. `IdleAmplitude` and `MaxLean` are totals at the tip, spread along the chain.
- Don't key these cloth bones in animations as well. The script sets `Bone.Transform` every frame.

## Rebuilding / changing the weapons

```bash
bash tools/setup_blender.sh
```

```bash
cd incarnam-weapons/blender && ./finish_all.sh oathsplitter sunbound warlink spear
```

Each weapon is defined in `build_<weapon>.py` as 2D outlines plus dimensions in studs. Edit a number and re-run to get new meshes, maps, renders and stats. `--preview` renders a fast blockout. `SMOKE=1` runs the whole pipeline with tiny bakes to check for errors.

Tests for the Luau solver:

```bash
npm install --prefix /opt/luau @luau-rs/luau@0.739.0
```

```bash
node incarnam-weapons/roblox/tests/run.mjs
```

```bash
node incarnam-weapons/roblox/tests/compile_all.mjs
```

## Completion report

All numbers are measured from the exported files (`export/<Weapon>/<Weapon>_stats.json`). **Nothing has been imported into Roblox or tested in Studio yet.** Scale, orientation, grip feel, effects and performance in your game still need one Studio check (step 1 above).

| | Oathsplitter | Sunbound | Warlink | Flarecrest |
|---|---|---|---|---|
| Length (studs) | 5.9 | 5.35 | 2.66 per cleaver | 8.2 |
| Triangles, main mesh | 6,752 | 5,385 | 4,312 per cleaver | 7,363 |
| Triangles, glow mesh | 208 | 48 | n/a | 36 |
| Triangles, cloth or chain | n/a | streamer 116 | link 64, end link 64 | ribbon 884 |
| Buried faces removed | 450 (from 7,600 tris) | 791 (from 6,802 tris) | 146 per cleaver (from 4,604 tris) | 230 (from 7,812 tris) |
| Texture set | 2K × 4 maps | 2K × 4 + streamer 512 × 4 | cleavers 1K × 4, shared by both · chain 512 × 4 | 2K × 4 + ribbon 512 × 4 |
| UV coverage | 58% | 65% | 65% | 39% |
| Rig | none | ClothRoot + Cloth1–5 ✅ | none (runtime chain) | RibbonRoot + Ribbon1–8 ✅ |

✅ means it passed `validate_rigs.py` on the re-imported FBX:
- every vertex is weighted, with at most 4 influences, normalised;
- there is a single root bone;
- the pinned root area moves 0.0 studs when the tail is bent, while the tail moves 0.23 studs on Sunbound and 0.35 studs on Flarecrest.

**Per weapon:**
- **Oathsplitter.**
  - Geometry: the slot is a real opening with inner bevels from both sides, with twin points, a bridge, a crescent guard, a gold frame and the gem.
  - Effects: the amber heat in the slot is a separate `Oathsplitter_Glow` mesh.
  - Renders: it's the only weapon with renders (acceptance views, showcase and turntable), because you asked to skip them for the others.
- **Sunbound.**
  - Geometry: a solid blade with an empty fuller groove, an inset red spine, a sun disk in three layers (rim, star, 8-sided gem), and swallowtail guard arms.
  - Streamer: rigged and driven at runtime by `ClothSway`.
- **Warlink.**
  - Geometry: mirrored cleavers that share one texture set, box-frame links in your reference style, and squared eyelets.
  - Chain: built at runtime, with its length a single setting (`LinkCount`). The solver passes 634 checks in real Luau.
  - Equip: the R6 left-hand weld plus a stow weld for when it's unequipped.
- **Flarecrest.**
  - Geometry: the longer leaf blade with the flame-shaped opening, crescent wings and the gold socket.
  - Ribbon: the spiral wrap is pinned to `RibbonRoot`, and only the tail moves.

**Known remaining issues:**
- **Roblox import is unverified.** Scale (0.28 m per stud), orientation, and whether the FBX empties come in as Attachments all need one Studio import to confirm.
- **Chain length is a placeholder.** It defaults to 32 links (an R6 estimate) until you run `MeasureHandSpan` with your animations.
- **Oathsplitter's grip is 1.1 studs.** R6 hands are 1 stud wide each, so a two-handed animation will overlap the arm blocks. Easy to lengthen if your animations need it.
- **Flarecrest is 8.2 studs** (about 1.6× an R6). That's from the longer blade you asked for. Its UVs are only 39% used because the long shaft islands pack inefficiently; it still bakes cleanly at 2K, but a tighter pack would give more texture detail.
- **Leftover sliver triangles** (2–4% of each mesh) are in the narrow flat bevel strips. They're planar, so they don't affect shading. A few 8-sided n-gons remain on the pommel and lathe caps; Roblox triangulates them on import.
- **Glow meshes have no emissive map.** Roblox SurfaceAppearance doesn't take one, so set the `_Glow` parts to Neon or drive them from your VFX.
- **The Roblox scripts are compile-checked and reviewed, but not run in Roblox.** The solver math is tested in real Luau; the parts that need the engine (welds, BulkMoveTo, bones) have only had an independent adversarial review, with 21 findings fixed.
