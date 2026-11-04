# LMG_03 — PKM

**PIXELGATE / Factory v1 / Light Machine Guns / Primary**

## Visual goal
Long chunky support rifle with receiver cover, feed-belt silhouette, removable ammo box and optional folded bipod.

**Factory materials:** Satin dark steel and dark wood or durable polymer.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `BeltSegment_ShortAnimated`
- `FeedCover`
- `AmmoBox`
- `Bolt_VisualIfVisible`
- `Bipod_OptionalCosmetic`
- `CaseEjection_VFX`


**Reload / ammunition display:** BELT-FED: animate the feed cover and ammo box/belt visual elements. Do not substitute an assault-rifle magazine reload.

**Distinct behavior:** Belt and cover distinguish this model mechanically and graphically.

**Portal-combat considerations:** Sustained cover fire; dedicated weight and ADS handling.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as PKM at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
