# SMG_02 — Vector

**PIXELGATE / Factory v1 / Submachine Guns / Primary**

## Visual goal
Sharp modern lower receiver, forward-biased angular styling, magazine in the pistol-grip region.

**Factory materials:** Black anodized aluminum and grippy charcoal polymer.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `ChargingControl_Visible`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable grip-region stick magazine, snappy and compact visual sequence.

**Distinct behavior:** Pronounced angular silhouette rather than a generic rectangular SMG.

**Portal-combat considerations:** Close-range specialist: manageable first-person shake at high virtual fire cadence.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Vector at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
