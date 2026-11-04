# SMG_04 — MP5

**PIXELGATE / Factory v1 / Submachine Guns / Primary**

## Visual goal
Compact classic rounded/pressed-metal upper, tubular handguard and narrow stick magazine.

**Factory materials:** Black blued steel, matte textured handguard.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `ChargingHandle`
- `Bolt_Visible`
- `Magazine`
- `Stock_Optional`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable stick magazine; dedicated visible charging-handle animation can be used for the empty-reload visual beat.

**Distinct behavior:** Keep familiar classic receiver and slim silhouette, unlike UMP45.

**Portal-combat considerations:** Easy-to-read control for entry-level fast portal fights.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as MP5 at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
