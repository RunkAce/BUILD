# AR_04 — VSS

**PIXELGATE / Factory v1 / Assault Rifles / Primary**

## Visual goal
Compact stock and receiver paired with the long, visually dominant integral suppressor. In this launch roster it remains in the assault-rifle UI class as supplied, but plays as a precision/suppressed hybrid.

**Factory materials:** Muted metal, aged dark wood or polymer, almost no flashy color.

**Art direction:** premium stylized 3D hard-surface, refined shapes, high-contrast material separation, deliberate hand-authored texture treatment, readable while fast-moving; no ornate fantasy skins, no crystals, no copied ornamentation or logos.

## Working in-game components
- `Trigger`
- `Bolt_Visible`
- `Magazine`
- `SafetyControl_Visual`
- `CaseEjection_VFX`


**Reload / ammunition display:** Small detachable box magazine with restrained tactical/empty reload motions.

**Distinct behavior:** Integrated suppressed front profile—not a generic rifle plus an add-on suppressor.

**Portal-combat considerations:** Stealth-inspired low-signature gun VFX and readable short firing impulse.

## Required animation coverage
Equip, idle, walk, sprint, aim-down-sights if relevant, fire, dry fire, tactical reload if applicable, empty reload if applicable, inspect, holster/swap, portal-entry/exit camera and weapon pose recovery. Add action-specific animations only where appropriate (bolt cycle, string draw, barrel spin, revolver cylinder, belt feed).

## Deliverable acceptance
- Recognizable as VSS at thumbnail size and in first person.
- Functional moveable components modeled as separate meshes and correctly pivoted (where visible); no fake moving geometry from unanimated texture scrolls.
- Verified factory material pass, mesh topology, normals, UVs, collision-free viewmodel, world/third-person LOD.
- Real working weapon data and animation hookups in Studio; user can equip, shoot/release, inspect, reload/refill and switch weapons without errors.
- Client VFX and server-authoritative virtual ammo/damage are kept in sync.
- No self-claimed 'done' without test evidence in Output and a brief per-weapon verification record.
