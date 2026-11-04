# SIDE_03 — Magnum

**PIXELGATE / Factory v1 / Pistols / Sidearms / Secondary**

## Visual goal
Robust classic six-shot-style revolver silhouette, long-ish barrel, exposed hammer silhouette and prominent cylinder.

**Factory materials:** Dark brushed alloy, neutral textured grip and crisp rim highlights.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Hammer`
- `Cylinder_Rotation`
- `Cylinder_SwingOut`
- `IndividualRoundsVisual_Optional`
- `SpentCasingVisual_Optional`


**Reload / ammunition display:** Revolver cylinder opens/closes and individual ammo/speed-loader visuals animate; NO removable pistol magazine and NO reciprocating auto-pistol slide.

**Distinct behavior:** This is a revolver in the factory spec, separate from Deagle.

**Portal-combat considerations:** Measured precision sidearm, pronounced kick and slower refilling.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Magnum at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
