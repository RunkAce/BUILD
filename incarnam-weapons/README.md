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
3. Build the Tool: `Handle` (the right cleaver, `Warlink_CleaverR`) and `CleaverL`, each with an Attachment named `ChainEnd` at the eyelet. Tag the Tool `Warlink`. Put `WarlinkTool.server.luau` inside it as a Script. It welds `CleaverL` to the R6 `Left Arm`, because R6 has no left grip. If your animations already drive the weapons with their own Motor6Ds, skip that script; the chain only needs the two `ChainEnd` attachments.
4. Put `WarlinkChainController.client.luau` in `StarterPlayerScripts`. It shows the chain for every player holding a Warlink and removes it on unequip, respawn or tool removal.
5. **Size the chain to your animations.** Put `roblox/tools/MeasureHandSpan.client.luau` in `StarterPlayerScripts`, paste your animation IDs at the top, and press Play. It plays each animation, records the widest eyelet-to-eyelet distance, and prints a `LinkCount`. Set that as a number attribute `LinkCount` on the Tool, then delete the script.
6. Optional Tool attributes:
   - `ChainMode`: `"Coil"` (the default) winds spare links around the left forearm and pays them out as the hands separate. `"Hang"` lets the whole chain sag, kept above the floor by a raycast.
   - `Pitch`: default 0.21, which matches the exported link.

How it behaves:
- Links never stretch while the hands are closer than the chain length.
- If an animation goes wider, the chain goes straight, every link shares the extra length evenly so no gap opens, and the console prints the `LinkCount` you need.
- It is purely visual: no collisions and no damage. Your server combat stays in charge.
- All links move in one `BulkMoveTo` per frame, and chains far from the camera update less often.

### Cloth (Sunbound streamer, Flarecrest ribbon)

Import `Sunbound_Streamer.fbx` and `Flarecrest_Ribbon.fbx` as skinned MeshParts (bones included). Weld each one to its weapon at `ClothRoot` or `RibbonRoot`. Then, from a LocalScript:

```lua
local ClothSway = require(ReplicatedStorage.WarlinkModules.ClothSway)
ClothSway.new(streamerMeshPart, { "Cloth1", "Cloth2", "Cloth3", "Cloth4", "Cloth5" })   -- ClothRoot stays fixed
ClothSway.new(ribbonMeshPart, { "Ribbon1", "Ribbon2", "Ribbon3", "Ribbon4", "Ribbon5", "Ribbon6", "Ribbon7", "Ribbon8" })
```

The root stays locked, and sway and lag increase toward the tip. When the weapon moves, the cloth trails behind on springs and then settles.

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

_Filled in from the measured stats after the production run (see below)._
