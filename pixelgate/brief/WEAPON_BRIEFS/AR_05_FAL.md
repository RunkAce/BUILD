# AR_05 — FAL

**PIXELGATE / Factory v1 / Assault Rifles / Primary**

## Visual goal
Long, solid and authoritative rifle proportions, full-length receiver and heavier visual weight.

**Factory materials:** Blackened steel with muted wood or polymer stock and handguard.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `ChargingHandle`
- `Bolt_Visible`
- `Magazine`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable box magazine and confident, weightier reload animations.

**Distinct behavior:** Differentiate from AK and SCAR with long top line and classic battle-rifle proportions.

**Portal-combat considerations:** High-reward controlled fire, not the fastest run-and-gun choice.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as FAL at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
