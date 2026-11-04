# PIXELGATE — Moving-parts and ammunition animation specification

**Only for virtual game models.** This is animation/gameplay logic, not a real-world firearm construction or operational reference.

## Universal state machine
`Unheld -> Equip -> Idle / Move / Sprint / ADS -> Fire -> Recovery -> Idle`, with validated transitions into `Reload_Tactical`, `Reload_Empty`, `Inspect`, `DryFire`, `Holster`, `Interrupted`, `PortalTransit`. A given gun may specialize or omit states where physically irrelevant.

The trigger, bolt, slide, charging piece, magazine, cylinder, feed box, ammunition props, bowstring, arrow and rotating barrel cluster must be separate moveable/renderable pieces WHEN RELEVANT TO THE WEAPON. **Do not attach every gun to the same fake generic animation.** The viewmodel needs correct local pivots, sensible motion arcs and useful visual feedback.

## Animation requirements
- Equip/switch: correct first-person hand grip, hide/show sync, no weapon teleport through camera.
- Fire: one deliberate impulse, muzzle flash at real `Muzzle` attachment (except bow), virtual spent case at `Ejection` attachment where appropriate, gun movement smooth on recovery. Firing animation can include brief visible bolt/slide travel.
- ADS: sight line aligns with center ray; reticle and weapon mesh agree; scopes are not filled by arbitrary mesh intersections.
- Empty/dry: trigger cue + empty sound; cannot spawn projectile or spend ammo below zero.
- Reload: visible ammunition source leaves gun and is replaced/refilled, with the gun's exact feed architecture; only adjust ammo counts when agreed animation event fires; if canceled, ammo state remains coherent.
- Tactical vs empty reload: distinguish when meaningful. Empty reload may include a visible receiver/slide step. Revolvers and bows use different semantic tracks.
- Inspect: looks deliberately hand-animated, highlights mechanical pieces, never causes weapon to fire.
- Dual Glock: actual left and right rig variants, opposing offsets, alternating/paired recoil presentation, independent ammunition states if designed; don't mirror only the final image.
- PortalTransit: brief transition pose without ruining visibility, ability usage must not desync the gun's state.

## Gun-specific visible systems
**Detachable magazine**: AK-47, M4A1, SCAR, VSS, FAL, Vector, UMP45, MP5, Thompson, M700 (selected game variant), M82, SVD, RPK, Deagle, Glock. P90 is also detachable but its mag is TOP-mounted.

**Internal ammunition**: Kar98k, show bolt + internal-round / clip-like reload. **No modern detachable external magazine**.

**Belt feed**: PKM, show feed cover, ammo box and short decorative belt segment coordinated with virtual ammo state. **No rifle mag**.

**Rotary action**: Minigun, animate barrel spin with startup and shutdown plus a large ammo module. **No handgun slide**.

**Revolver**: Magnum, animate hammer, cylinder rotation/swing and visual rounds/speed-loader. **No pistol slide**.

**Projectile string**: Bow, animate bowstring, arrow nock and draw/release. **No brass ejection/magazine**.

**Manual bolt cycle**: M700 and Kar98k. **No self-loading loop**.

**Self-loading precision**: M82 and SVD; brief visual receiver movement and eject cue as necessary, no manual bolt animation after each shot.

## Virtual ammunition design
Ammo figures are **gameplay constants to be tuned**, not assertions about real hardware. Set per-weapon `MagazineSize`, `ReserveAmmo`, `FireMode`, `ReloadDuration`, `RateOfFire`, `SpreadProfile`, `RecoilProfile` in authoritative Luau configuration. For bow use `ArrowCount`/`DrawTime`; for revolver use `CylinderCapacity`; for belt-fed use `BeltCapacity` and ammo box visuals. Never infer ammo counts from modeled cartridges or let rendered props dictate server authoritative counts.

## Visual/remote replication principles
- Server owns validated fire requests, ammo decrement, damage, cooldown, reload acceptance, player equip permissions and portal trajectory validation.
- Client owns responsive viewmodel posing, ADS, cosmetic muzzle/tracer/casing effects and smoothing.
- Nearby clients see world model + concise state replication instead of expensive per-frame part-CFrame remotes.
- Hitscan/projectile decisions are game design choices. Determine portal traversal support and exploit-resistant validation before claiming complete.
- All animations can be interrupted or resumed safely; never create infinite remote loops or permanently orphan dropped magazines.
