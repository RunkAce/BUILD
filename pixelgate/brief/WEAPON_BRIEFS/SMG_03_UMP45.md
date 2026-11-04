# SMG_03 — UMP45

**PIXELGATE / Factory v1 / Submachine Guns / Primary**

## Visual goal
Squared polymer receiver, thicker straight magazine and practical utilitarian geometry.

**Factory materials:** Charcoal/black polymer with subtle steel highlights.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `ChargingHandle`
- `Bolt_Visible`
- `Magazine`
- `Stock_Optional`
- `CaseEjection_VFX`


**Reload / ammunition display:** Large detachable stick magazine with distinct empty and partial reload takes.

**Distinct behavior:** Angular chunky control feel versus the smoother MP5.

**Portal-combat considerations:** Well-rounded for close- and short-midrange engagements.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as UMP45 at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
