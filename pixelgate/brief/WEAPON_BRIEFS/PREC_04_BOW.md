# PREC_04 — Bow

**PIXELGATE / Factory v1 / Sniper & Marksman Rifles / Primary**

## Visual goal
Purpose-built premium stylized modern recurve or hybrid bow; taut string, riser, limbs, arrow rest. Factory model is functional and restrained, NOT a copy of the supplied ornate bow reference.

**Factory materials:** Deep graphite limbs, brushed metal riser, muted leather grip and a tiny neutral accent.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `BowString`
- `BowLimbs_SubtleDeformOrPose`
- `Arrow_Equipped`
- `Arrow_ProjectileVFX`


**Reload / ammunition display:** No magazine. Nock an arrow, draw string, hold, release; respawn/nock next virtual arrow. Visible ammo is arrow count/quiver rather than clips.

**Distinct behavior:** Use unique silhouette and animation grammar; no fake brass ejection or gun magazine.

**Portal-combat considerations:** Projectile traversal through portals must be clear and fair, with no hitscan-only assumptions.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as Bow at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
