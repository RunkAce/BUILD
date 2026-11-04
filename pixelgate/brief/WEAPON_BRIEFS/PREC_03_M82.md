# PREC_03 — M82

**PIXELGATE / Factory v1 / Sniper & Marksman Rifles / Primary**

## Visual goal
Extremely long, substantial receiver, oversized muzzle area and detached large box magazine; dramatic weight without massive ornament.

**Factory materials:** Dark industrial steel and muted tactical composite.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `CaseEjection_VFX`
- `RecoilSlideVisual_Optional`


**Reload / ammunition display:** Detachable box-magazine reload; self-loading animation after each virtual shot—NOT a bolt-action sequence.

**Distinct behavior:** Heavy semi-auto precision rifle. Make it dramatic through scale and recoil response, not implausible moving fins.

**Portal-combat considerations:** High handling cost and long sight recovery; keep it balanced for custom loadouts.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as M82 at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
