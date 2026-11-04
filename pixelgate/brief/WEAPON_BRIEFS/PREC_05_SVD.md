# PREC_05 — SVD

**PIXELGATE / Factory v1 / Sniper & Marksman Rifles / Primary**

## Visual goal
Long marksman rifle, distinctive thin stock/rear form and separate magazine, optic base appropriate to default profile.

**Factory materials:** Dark steel plus wood/tan polymer depending on the factory subvariant.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `ChargingHandle_Visible`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable box magazine and semi-automatic cycling—NOT a manual bolt action after each shot.

**Distinct behavior:** More nimble DMR identity than the massive M82.

**Portal-combat considerations:** Repeatable precision follow-ups rather than pure one-shot fantasy.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as SVD at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
