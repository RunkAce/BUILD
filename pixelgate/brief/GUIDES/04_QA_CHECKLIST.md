# PIXELGATE — Acceptance tests (repeat for all 21 guns)

## Asset review
- [ ] Correct recognizable weapon silhouette, not a reskin of one generic gun.
- [ ] Factory variant only (no anime crystals, magic blades, rune engraving, third-party watermark).
- [ ] Correct separate animated body elements and correctly set pivots.
- [ ] No missing textures, pink models, flipped normals, clipped or disappearing meshes.
- [ ] Model and animation clearly usable in first-person and from an observer's view.
- [ ] Hand anchors and attachment points aligned; ADS centered when applicable.
- [ ] Camo/finish masking works independently of functional moving geometry.

## Functional tests
- [ ] Equip, unequip, aim and swap all work without remote spam or broken state.
- [ ] Fire animation triggers once per valid shot and stops on empty magazine.
- [ ] Visible parts **actually** move in the correct gun-specific sequence.
- [ ] Magazine top/bottom/internal/belt/cylinder/string animations match the weapon.
- [ ] Reload visually swaps/refills the correct virtual ammunition state.
- [ ] Tactical and empty reload take variants where applicable.
- [ ] Reload cancel/weapon swap/character reset leaves no floating mag or corrupt ammo state.
- [ ] Inspect does not change server-side ammo or damage.
- [ ] Bow draws/releases projectiles; does not eject brass.
- [ ] M700/Kar98k cycle manually; M82/SVD do not play manual-bolt shots.
- [ ] P90 top-mounted mag and PKM belt feed are unique.
- [ ] Glock Akimbo left/right variants coexist without aim/animation conflicts.
- [ ] Minigun barrels visibly spin with startup and shutdown, with strong mobility limits.
- [ ] Portal entry/exit, angle changes and trajectory transitions do not misalign muzzle effects or projectile traces.
- [ ] Other players see world model animation and hear corresponding sounds.
- [ ] Client cannot spoof unrestricted fire rate, reload state, ammo or damage.
- [ ] Mobile performance and memory budget measured in Studio (not guessed).
- [ ] Output errors clean; include a short repro log with pass/fail and what was actually run.

## Per-gun status row
`ID | Name | Mesh | UV/Materials | Rig | Idle | Fire | TacticalReload | EmptyReload | Inspect | Runtime | Portal QA | Mobile QA | Evidence | Notes`

No checkbox is premarked. Only mark a step when verified with a concrete test and artifact.
