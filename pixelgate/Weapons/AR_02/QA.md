# AR_02 M4A1 — QA record (factory_v1)

Marked only where actually verified. **Studio, portal and in-game tests are blocked**: this environment has no Roblox Studio, no PIXELGATE project and no viewmodel arm rig.

| Check | Status | Evidence |
|---|---|---|
| Recognisable M4A1 silhouette, original (no logos/third-party art) | ✅ verified (render) | `Review/AR_02_side.png`, `Review/AR_02_three_quarter.png` |
| Separate moving parts with pivots | ✅ verified (Blender) | 7 bones: Root, Trigger, Magazine, ChargingHandle, BoltCarrier, DustCover, Selector; each part rigidly skinned (1 bone per vertex) |
| Weapon-side takes: Idle, Fire, DryFire, Reload_Tactical, Reload_Empty, Inspect | ✅ authored, frames rendered | `Review/AR_02_Reload_Empty_f*.png`, `Review/AR_02_Inspect_f*.png` |
| Magazine visibly leaves and re-seats; bolt locks back on empty; charging handle releases bolt | ✅ verified (frames) | Reload_Empty f22 / f63 / f68 |
| Mesh: no holes, no flipped faces, no shading artefacts | ✅ verified | plain-metal and textured renders after the optimiser fix |
| Viewmodel triangles | 5381 | brief planning range 6k–15k |
| World model triangles | 2421 | brief planning range 1k–5k |
| Textures | 1024 PBR (Color/Normal/Roughness/Metalness) + MaskMap | `Textures/` |
| Attachments (GripRight, GripLeft, RightHandIK, LeftHandIK, Muzzle, ADS, Ejection, MagazineSeat) | ✅ placed, exported as empties on Root | positions in `AR_02_stats.json` |
| FBX imports into Studio with bones + animations | ⛔ not tested (no Studio) | — |
| Arms: Equip / Walk / Sprint / ADS / Holster / PortalTransit | ⛔ blocked: needs the project's viewmodel arms | — |
| Iron sights unobstructed (peep hole runs along the bore, front post centred between open ears) | ✅ verified (Blender ray test + render) | ray from ADS hits the post first at 358 mm; rays above / left / right of the post escape; `Review/AR_02_sight_picture.png` |
| ADS camera alignment with the arms rig | ⛔ not tested (no viewmodel arms) | ADS attachment at the rear face of the aperture |
| Server-authoritative ammo, fire rate, damage; HUD; portal crossing | ⛔ blocked: needs the existing PIXELGATE weapon framework | config + event map ready in `WeaponConfig.luau` |
| Mobile performance | ⛔ not measured | — |
