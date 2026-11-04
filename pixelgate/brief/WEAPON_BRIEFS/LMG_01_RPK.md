# LMG_01 — RPK

**PIXELGATE / Factory v1 / Light Machine Guns / Primary**

## Visual goal
Heavy AK-family support gun with long barrel, beefy furniture and elongated curved magazine; optional bipod is VISUAL only.

**Factory materials:** Industrial dark steel and muted wood/polymer.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `Bipod_OptionalCosmetic`
- `CaseEjection_VFX`


**Reload / ammunition display:** Long curved detachable magazine, not a belt-fed sequence.

**Distinct behavior:** Rifle-derived support weapon and sturdier shape distinguish it from PKM.

**Portal-combat considerations:** Suppressive loadout with handling and weight trade-offs.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as RPK at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
