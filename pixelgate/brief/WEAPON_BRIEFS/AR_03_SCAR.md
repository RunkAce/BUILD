# AR_03 — SCAR

**PIXELGATE / Factory v1 / Assault Rifles / Primary**

## Visual goal
Thick, sturdy premium rifle, squared receiver, visible upper rail, distinctive stock and magazines.

**Factory materials:** Factory dark earth and graphite polymer with satin gunmetal.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `ChargingHandle`
- `Bolt_Visible`
- `Magazine`
- `Stock_Optional`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detached box magazine; reserve a separate charging control on the rig for reload and inspection animation.

**Distinct behavior:** Chunkier receiver and high-contrast slab shapes distinguish it from the M4.

**Portal-combat considerations:** Steady ranged rifle with heavier movement feel, without excessive viewmodel obstruction.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as SCAR at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
