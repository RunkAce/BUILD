# SIDE_01 — Desert Eagle (Deagle)

**PIXELGATE / Factory v1 / Pistols / Sidearms / Secondary**

## Visual goal
Large angular semi-auto pistol with broad slide, squared barrel/muzzle region and substantial grip.

**Factory materials:** Brushed graphite/gunmetal factory finish with restrained machined edges.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Slide`
- `Hammer_VisibleIfModeled`
- `Magazine`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable grip magazine and visible slide movement; use distinct slide-lock empty state.

**Distinct behavior:** Heavy pistol silhouette, distinctly NOT a revolver.

**Portal-combat considerations:** Slow, high-impact back-up sidearm for precise taps.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Desert Eagle (Deagle) at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
