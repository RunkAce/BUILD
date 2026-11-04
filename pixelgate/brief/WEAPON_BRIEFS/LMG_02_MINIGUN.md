# LMG_02 — Minigun

**PIXELGATE / Factory v1 / Light Machine Guns / Primary**

## Visual goal
Visually bold fictional game-ready six-barrel rotary gun and large visible ammo module, robust handles and spinning barrel shroud.

**Factory materials:** Black industrial metal, tungsten-like silver accents, matte polymer.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `RotatingBarrelAssembly`
- `SpinUp_State`
- `SpinDown_State`
- `AmmoDrumOrModule`
- `Trigger`
- `HeatShimmer_VFX`


**Reload / ammunition display:** Swap the large detachable ammo module/drum in a choreographed game animation; NO normal rifle magazine or reciprocating handgun slide.

**Distinct behavior:** VERY heavy loadout weapon with spin-up and spin-down; not an arena pickup unless designers change the game later.

**Portal-combat considerations:** Cannot invalidate custom loadout balance: movement, start-up, visibility and portal interactions need strong constraints.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Minigun at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
