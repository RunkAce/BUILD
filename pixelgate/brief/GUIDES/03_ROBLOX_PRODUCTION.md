# PIXELGATE — Roblox Studio implementation contract

## Asset layout (suggested)
```text
ReplicatedStorage/
  PIXELGATE/
    WeaponConfigs/      -- 21 ModuleScripts / IDs stable across client and server
    Viewmodels/         -- 21 local-only viewmodel rigs with visible animated parts
    WorldModels/        -- 21 simplified third-person / dropped visual rigs
    Shared/             -- WeaponState, WeaponSignals, WeaponTypes, math helpers
    VFX/                -- reusable casing, muzzle, impact visuals
ServerScriptService/
  PIXELGATEWeapons/     -- authorization, damage, ammo, rate limits
StarterPlayerScripts/
  PIXELGATEWeapons/     -- input, ADS, inspect, prediction, render-level animation
```

Use actual production naming from the project if a preexisting system is present. Do not replace/delete functioning systems; inspect them and integrate non-destructively.

## Rig conventions
- `Root` is the nonrendered pivot driving the whole weapon viewmodel; `GripRight` and optional `GripLeft` are authoritative hand anchors.
- `Muzzle`, `ADS`, `Ejection`, `LeftHandIK`, `RightHandIK`, `MagazineSeat` are **Attachments**, not mystery unnamed parts.
- Specific mechanical parts are separate MeshParts or bones with meaningful pivot orientations; animate through one coherent animation system (Motor6D / bones / tracks), not per-frame permanently growing weld spaghetti.
- `Magazine` can temporarily transition between weapon-relative and hand-relative pose; use state-specific attachment/constraint approach and cosmetic cloned magazine drops if desired.
- `Slide`/`Bolt`/`BoltHandle`/`Cylinder`/`BowString`/`Arrow`/`FeedCover`/`BarrelRotor` only on the guns that need them.
- First-person viewmodel and third-person world model share weapon identity but may use distinct simplified LODs/animation sets.
- Avoid permanently welding a moving part to static geometry; verify the part actually animates in Studio.

## Expected project outputs
1. Blender-editable source (`.blend`) or equivalent editable mesh scene + export scripts where tool access allows.
2. `.fbx` / `.glb` exports and texture maps (.png) suitable for Roblox import, named by stable weapon ID.
3. Model hierarchy with attachments and pivot assignments plus animation clips or runnable scripts generating those clips.
4. 21 weapon configuration modules and server/client runtime integration to existing game framework.
5. Demo test scene with inventory/loadout selection, equip, target, ammo HUD, portal crossings, inspector and reload.
6. Per-weapon screenshots / short recordings / output logs showing functionality (NOT just assurances).
7. Explicit list of assets that are complete, blocked or intentionally deferred.

## Quality/performance targets (PROVISIONAL; measure in Studio)
- Prefer a clean game-ready hero viewmodel and a cheaper world model. Treat ~6k–15k triangles for a first-person weapon and ~1k–5k for a world model as early planning ranges, **not fixed Roblox limits**. Adjust for silhouette, phone performance and actual memory/profiler results.
- Limit unique materials and large textures; prototype 1K texture sheets for hero weapons and smaller world assets, escalating only where close-up value is demonstrable.
- Keep hidden internals modeled only where they appear during an animation; optimize cosmetic shells, ammo props and VFX; pool short-lived casing meshes.
- Avoid collision and physics simulation on first-person viewmodels. Keep world models safe from unnecessary physical collisions.
- Validate across PC, phone, different FOVs, widescreen and varied avatar body proportions. Don't assume a specific R6/R15 rig before auditing the project.

## Roblox-only modeling fallback
If Claude has Studio scripting but no mesh authoring tools: generate structured placeholder rigs only to PROVE the system, explicitly label them `BLOCKOUT_ONLY`, and deliver Blender/Python mesh-generation/export scripts or production modeling instructions rather than claiming hero quality. Prioritize clean mesh geometry over primitive block sculptures in final delivery.
