# MASTER PROMPT FOR CLAUDE — PIXELGATE: ALL 21 FACTORY WEAPONS

You are a senior Roblox FPS technical artist, hard-surface weapon modeler, first-person animator, Luau gameplay systems engineer and performance QA lead, working directly on **PIXELGATE**, my competitive Roblox portal shooter. Work on the actual project files and available modeling tools, not just a design essay. The game uses **Call of Duty-style custom loadouts**: players choose and customize primary/secondary weapons. Portals are an always-available traversal ability separate from the weapon slots; this game is **NOT** a Halo/Splitgate weapon-pickup-only game.

## NON-NEGOTIABLE GOAL
Create **one clean, premium, factory/default base weapon model for EACH OF THE 21 WEAPONS LISTED BELOW**, with genuinely movable pieces, mechanically plausible *game animations*, working virtual ammunition and reload logic, FPS/world-model integration, and a reusable structure for future cosmetics. **Do not add shotguns** in this pass; they were only suggested later and are not in the 21 original named weapons. **Do not create decorated fantasy skins now.**

The five screenshots in `REFERENCES/` are my visual art-style references. They show beautifully crafted fantasy weapons with a defined layered silhouette, crisp modeling and high-contrast materials. Treat these as a **QUALITY / STYLIZATION BENCHMARK**, not literal default weapon designs. Copy **no artwork, watermark, logo, shape or ornament** from them. No `Farlands`, no `GG/ATTERACT`, no stylized A logo in the final project. Source images may include third-party art, so use them as moodboards only and create original assets. Default guns need **recognizable real-gun-inspired factory silhouettes** with premium Roblox stylized construction. The Bow is a unique design, but still a plain factory baseline, not a recreation of the supplied ornate bow.

## BUILD THE REAL ASSET, NOT A PRETEND DEMO
1. First inspect the existing Roblox project and identify actual loadout, input, camera, portal, viewmodel, R6/R15 compatibility, weapon framework and asset import setup. **Do not delete or overwrite working systems.**
2. Determine which content-creation tools you truly have: Blender, Blender Python, Studio plugin, Roblox Studio bridge, FBX/GLB export, filesystem. Build usable assets with those tools. If blocked, state the exact tool barrier and produce executable generation/export scripts and transparent status, not a claim that professional meshes were created.
3. Make **M4A1** the first vertical slice: complete factory mesh and materials, model pivots, moving magazine/action controls, inspect/fire/reload animation, weapon configuration, ammo HUD hook, first-person plus third-person view, portal test and actual Studio verification. Do not propagate a broken template to the other 20.
4. Then build the other 20 using their individual briefs and finish with a full automated/manual QA pass.
5. Output editable project files, not just prose or screenshots. Continue through the roster without waiting for another prompt unless a truly blocking technical limitation arises.

## LOCKED LAUNCH ROSTER — 21 GUNS, 5 CLASSES
- **Assault Rifles (5):** AK-47, M4A1, SCAR, VSS, FAL.
- **SMGs (5):** P90, Vector, UMP45, MP5, Thompson.
- **Sniper & Marksman Rifles (5):** M700, Kar98k, M82, Bow, SVD.
- **LMGs (3):** RPK, Minigun, PKM.
- **Pistols / Sidearms (3):** Desert Eagle (Deagle), Glock (with Akimbo option), Magnum.

Keep the VSS in the user-specified AR menu category for now, but model its integrated suppressed precision profile; it may later be retagged as Marksman without remodeling. Minigun remains a selectable loadout weapon with serious handling constraints, **not** a mandatory arena pickup. The optional Glock Akimbo is a variant, **not** weapon #22. M700 uses a clearly declared detachable-box-mag game configuration; Kar98k has an internal feed; the Magnum is a revolver. The Bow must be a fully working virtual bow with actual string and arrow animations.

## CORE VISUAL DIRECTION
- Premium, highly polished **stylized 3D hard-surface** game weapons: between convincing contemporary shooter engineering and the bespoke shape craftsmanship of the five screenshots.
- Crisp bevels and highlights; precise material borders; tasteful baked/hand-authored texture gradients; readable silhouette at small UI scale; detailed close-up without photoreal grime/noise.
- Proportions bold enough to read within Roblox's stylization but never toy-like, huge blocky or low effort. Keep proper grip positions, believable silhouette, mag placement, barrels, optics and controls.
- Base colors: graphite, matte black, satin steel, factory tan/olive and wood where appropriate; functional tiny accent colors only. No magical emissions; no glowing scythes or gemstone gun bodies on factory models.
- Original weapon markings only, no unlicensed manufacturer logos unless project has permission. Keep future cosmetic material/mask slots isolated from the moving structure.
- Every weapon must look like its OWN type: M4 != SCAR != FAL; UMP != MP5; M82 != M700; PKM != RPK.

## REQUIRED COMPONENTS / VISUAL MOVING-PART AUDIT
| ID | Weapon | Virtual mechanism | Minimum separate moving/visual systems |
|---|---|---|---|
| AR_01 | AK-47 | Automatic rifle | Trigger, ChargingHandle, Bolt_Visible, Magazine |
| AR_02 | M4A1 | Automatic rifle | Trigger, Bolt_Visible, ChargingHandle, Magazine |
| AR_03 | SCAR | Automatic rifle | Trigger, ChargingHandle, Bolt_Visible, Magazine |
| AR_04 | VSS | Suppressed precision rifle | Trigger, Bolt_Visible, Magazine, SafetyControl_Visual |
| AR_05 | FAL | Precision-leaning battle rifle | Trigger, ChargingHandle, Bolt_Visible, Magazine |
| SMG_01 | P90 | Compact automatic SMG | Trigger, TopMagazine, Bolt_Visible_IfExposed, CaseEjection_DownwardVFX |
| SMG_02 | Vector | High-rate compact SMG | Trigger, Bolt_Visible, Magazine, ChargingControl_Visible |
| SMG_03 | UMP45 | Control-oriented SMG | Trigger, ChargingHandle, Bolt_Visible, Magazine |
| SMG_04 | MP5 | Classic precision SMG | Trigger, ChargingHandle, Bolt_Visible, Magazine |
| SMG_05 | Thompson | Vintage automatic SMG | Trigger, Bolt_Visible, Magazine, CaseEjection_VFX |
| PREC_01 | M700 | Bolt-action sniper rifle | Trigger, BoltHandle, Bolt, Magazine |
| PREC_02 | Kar98k | Bolt-action historical rifle | Trigger, BoltHandle, Bolt, InternalAmmoVisual_Optional |
| PREC_03 | M82 | Heavy semi-automatic precision rifle | Trigger, Bolt_Visible, Magazine, CaseEjection_VFX |
| PREC_04 | Bow | Projectile bow | BowString, BowLimbs_SubtleDeformOrPose, Arrow_Equipped, Arrow_ProjectileVFX |
| PREC_05 | SVD | Semi-automatic designated marksman rifle | Trigger, Bolt_Visible, Magazine, ChargingHandle_Visible |
| LMG_01 | RPK | Magazine-fed support rifle | Trigger, Bolt_Visible, Magazine, Bipod_OptionalCosmetic |
| LMG_02 | Minigun | Heavy rotary-barrel weapon (loadout) | RotatingBarrelAssembly, SpinUp_State, SpinDown_State, AmmoDrumOrModule |
| LMG_03 | PKM | Belt-fed general-purpose machine gun | Trigger, BeltSegment_ShortAnimated, FeedCover, AmmoBox |
| SIDE_01 | Desert Eagle (Deagle) | Heavy self-loading pistol | Trigger, Slide, Hammer_VisibleIfModeled, Magazine |
| SIDE_02 | Glock | Polymer semi-automatic pistol | Trigger, Slide, Magazine, CaseEjection_VFX |
| SIDE_03 | Magnum | Large-frame revolver | Trigger, Hammer, Cylinder_Rotation, Cylinder_SwingOut |

This table is an index: READ `WEAPON_BRIEFS/` and `GUIDES/02_MOVING_PARTS_AND_ANIMATION.md` for the full exception handling and real visual differentiators. **Only animate parts that actually belong to that gun.** 'Clips' is a casual player term: code/data/rigs must distinguish detachable magazines, internal feed, belt-fed boxes, cylinder chambers, and arrows.

## REQUIRED RIG / MODEL CONTRACT
For every weapon, deliver a first-person viewmodel and a simpler third-person/world model (can share authored source). Use stable IDs exactly from `DATA/weapon_manifest.json`. Use sensible mesh-part pivots and attachments: `Root`, `GripRight`, `GripLeft` if necessary, `Muzzle` (guns only), `ADS` (guns/scoped weapons), `Ejection` if applicable, `LeftHandIK`, `RightHandIK`, `MagazineSeat` if relevant, and a declared set of separate moving parts. A magazine must be individually movable during reload. Bolts, slides, cylinders, bowstrings, arrows, barrel clusters and feed covers have separate animation sources only where appropriate. Make the gun's reload physically *look* correct, without teaching real-world firearm building/assembly procedures.

Avoid: a static gun model with a fake arm waving; all guns sharing identical magazine animation; welded magazines that never visibly move; wrong reload architectures; nonfunctional viewmodel actions; fake animations unsupported by actual Studio rigs; copied fantasy skins as defaults; simple cubes falsely claimed as polished finished guns.

## ANIMATION CONTRACT
Each gun: `Equip`, `Idle`, `Walk`, `Sprint`, `ADS` if applicable, `Fire` or `Release`, `DryFire`/empty reaction if relevant, `Reload_Tactical` if relevant, `Reload_Empty` if relevant, `Inspect`, `Holster`, `PortalTransit_Recovery`. Specialist states: `BoltCycle` (M700/Kar98k), `BowNock/Draw/Hold/Loose`, `CylinderOpen/Refill/Close` (Magnum), `RotorSpinUp/SpinLoop/SpinDown` (Minigun), `FeedCover/BeltBoxSwap` (PKM), `AkimboAlternateLeftRight` (Glock option). Animation notifies must drive visible ammo swaps, weapon state changes, sounds and VFX at the right moment. Poses must not clip into the camera or HUD while portaling, sprinting or aiming.

Ammunition is GAME data (not real-world ballistics): config each weapon's virtual capacity, reserve ammo, fire behavior, reload gates, recoil and hit validation. Choose sensible provisional FPS values and clearly tag them for balancing. **No physical real-world weapons or functional engineering instructions are being requested; only virtual meshes and simulated game logic.**

## IMPLEMENTATION / NETWORK / PORTALS
Build clean Luau modules integrated with current game rather than inventing a second incompatible gun framework. Server must authorize equip, ammo decrement, shot cadence and damage; client may predict the responsive presentation. Avoid exploitable remotes and untrusted client damage. Visual casings and dropped magazines should be pooled/local cosmetic effects. Validate shot-origin vs displayed muzzle, latency and portal transforms, so bullets or bow projectiles continue along correct paths when crossing or firing through portals. The permanent portal ability must not accidentally wipe equip/reload/ADS state. Respect custom loadouts, perk and attachment hooks but **do not add a full attachment content pack or cosmetics to this baseline**.

Do not start by creating 21 visual blockouts and calling it finished. Produce **one fully usable vertical slice**, validate it, then replicate with unique source geometry and unique mechanics.

## FILENAME / FOLDER CONTRACT
Use `DATA/weapon_roster.csv`, `DATA/weapon_manifest.json`, 21 files in `WEAPON_BRIEFS/` and the GUIDES as your authoritative asset-production packet. Within the project, group source mesh, exported mesh, textures, animations and Luau config by stable weapon ID. Do not use final names like `Gun1` or `MeshPart27`. Use labeled attachment positions and consistent naming.

Suggested export structure:
```
PIXELGATE/Weapons/{WeaponID}/Source/{WeaponID}.blend
PIXELGATE/Weapons/{WeaponID}/Exports/{WeaponID}_Viewmodel.fbx
PIXELGATE/Weapons/{WeaponID}/Exports/{WeaponID}_World.fbx
PIXELGATE/Weapons/{WeaponID}/Textures/{WeaponID}_Factory_*.png
PIXELGATE/Weapons/{WeaponID}/Animations/*
PIXELGATE/Weapons/{WeaponID}/WeaponConfig.luau
PIXELGATE/Weapons/{WeaponID}/QA.md
```

## REQUIRED QA AND EVIDENCE
For EACH of 21 weapons demonstrate: screenshot of default model (side + first-person), real separated moving parts, actual animation test (fire, reload, inspect, specialist moves), ammo consistency across reload/swap, world-model observer test, aiming sanity, portal test, no spurious Output errors, and reasonable desktop/mobile performance. Use `GUIDES/04_QA_CHECKLIST.md` and mark items only when truly tested. If any functionality is unfinished, label it explicitly. Verify 21 unique weapon configs and 21 models; no duplicate gun ID; no extra shotguns; no weapon #22 for Akimbo Glock.

## HOW TO REPORT
After work: (A) concise completion table `21/21` with each gun's mesh/rig/animations/runtime/portal QA statuses; (B) exact artifact locations; (C) screenshot/video proof paths; (D) issues and precise repro steps; (E) next best improvements. Never claim completion just because you generated text descriptions or a few script stubs. Actually implement and test as far as your tools permit.

**START NOW:** inspect the current PIXELGATE project/tooling, build M4A1 as the hero standard, then carry the same level of quality through all 21 original factory weapons. Read the supplemental guides and each per-weapon brief before implementing its distinctive moving systems.
