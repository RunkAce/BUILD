# SIDE_02 — Glock

**PIXELGATE / Factory v1 / Pistols / Sidearms / Secondary**

## Visual goal
Simple rectangular slide and polymer frame. Exact same factory geometry supports a later Akimbo option.

**Factory materials:** Flat black polymer grip and dark nitride-like steel slide.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Slide`
- `Magazine`
- `CaseEjection_VFX`
- `Akimbo_LeftRig_Optional`
- `Akimbo_RightRig_Optional`


**Reload / ammunition display:** Detachable grip magazine and slide-locked empty state. For AKIMBO, make separate left/right viewmodel rigs, mirrored poses and coordinated reloads; do not merely duplicate the same transforms.

**Distinct behavior:** Intentionally minimal and professional, good baseline for pistol animations.

**Portal-combat considerations:** Fast-swap secondary; akimbo trades ADS precision for rapid close-range capability.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Glock at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
