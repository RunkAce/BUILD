# SMG_05 — Thompson

**PIXELGATE / Factory v1 / Submachine Guns / Primary**

## Visual goal
Distinctive early-era rounded receiver and substantial wood furniture. Launch default uses a stick magazine; drum is a future variant, not required.

**Factory materials:** Warm walnut and dark blued steel, brushed wear only at edges.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `CaseEjection_VFX`


**Reload / ammunition display:** Detachable straight stick magazine in the base model; no forced drum-mag reload.

**Distinct behavior:** Preserve the recognizable historic silhouette, stylized rather than museum photoreal.

**Portal-combat considerations:** A characterful gun for players who prefer older designs.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Thompson at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
