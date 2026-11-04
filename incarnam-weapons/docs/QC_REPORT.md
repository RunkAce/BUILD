# Incarnam Iop concepts: quality-control report

**What was reviewed:** the three concept images (Oathsplitter, Sunbound, Warlink), the master brief, the concept briefs, the reference index and manifests, 4 of the 5 videos (frame-sampled), and the 5 reference images that were pasted into the chat.

**How it was reviewed:** each concept had one art-director QC pass, then an independent checker who re-examined the image and tried to refute every finding. There were also three motion reviews built from timestamped contact sheets of the videos, and one brief audit. The raw structured results are in `review_raw.json`.

## Verdicts

| Concept | Verdict | Independent check | Checker tally |
|---|---|---|---|
| Oathsplitter | **Pass with fixes** | Agrees | 27 confirmed, 2 overstated |
| Sunbound | **Pass with fixes** | Agrees | 16 confirmed, 6 overstated, 1 understated |
| Warlink | **Pass with fixes** | Agrees | 15 confirmed, 8 overstated, 2 refuted, 1 understated |

None of the three concepts breaks a design invariant. All three read clearly at a 96 px icon size and are clearly different from each other in silhouette.

## Oathsplitter

**What works:**
- The slot is truly open: its pixels match the background, not black paint.
- Both rails are wider than the slot.
- The bridge and the two separate points are there.
- The blade faces are quiet, and the detail sits at the guard, the blade root and the pommel.

**What to fix:**
- **The guard is not mirrored.** The upper horn barely sweeps forward, while the lower horn sweeps strongly. Build it symmetric, using the lower horn's sweep for both. *Done in the model.*
- **The bridge is short and sunken.** It's shorter along the blade than one rail is wide, and it sits below the rail faces. Make it flush and at least one rail width long. *Done: 0.32 studs against a 0.275-stud rail.*
- **The guard-to-grip stack is lumpy.** Make it four clean parts: guard, boss, collar and grip. *Done.*
- **The grip blends into the background.** It's warm brown-black (#231D1A) against a #252225 background. Use cool charcoal #2E2F33 with lighter strap edges. *Done.*
- **The surfaces don't read as the right materials.** The blade has marble-like mottling and the guard has crack lines, so it reads as stone or lava rather than forged metal and enamel. *Done:* the blade uses broad directional value, the red is enamel with edge chips that show steel underneath, and there are no cracks.
- **The glow spills into the slot.** The amber bloom fills the slot itself. Keep the heat only on the inner-wall channel. *Done:* the heat is a separate thin `SlotHeat` mesh lining the lower slot wall.

## Sunbound

**What works:**
- A solid, continuous broad blade, clearly different from Oathsplitter.
- A real layered gold sun disk (rim, star and faceted gem).
- A short cloth with a clean root that stays clear of the grip.

**What to fix:**
- **The blade face is warm peach-ivory, not pearl steel** (#C9CDD0). Blend it toward pearl at the tip and edges, and keep the warmth near the root.
- **The red spine is a hairline,** about 3–4% of blade width. Model it as a separate inset strip about 10–12% of the width at the root, tapering out at about 35% of the blade length.
- **There's a painted highlight baked onto the face.** It only works from this one camera angle, which the brief forbids. Don't paint it into the albedo.
- **The gold reads too saturated and orange.** Pull it toward aged gold #9D7950. Keep the pommel as drawn: a red body with a gold end cap.
- **Missed by the first pass:** an empty fuller groove continues past the red inlay to about 55–60% of the blade, the cloth has a thin vermilion edge stripe, and the gem has 8 sides with a flat top.

## Warlink

**What works:**
- Two compact hooked cleavers and a U-shaped chain read immediately.
- The 9 links alternate orientation, have open centres and are consistent in size.
- The eyelets sit beyond the grip, so links never cross the hands.

**What to fix:**
- **The eyelet-to-pommel join is under-designed.** The checker found a hex steel lug that is drawn but not developed. Build a two-tier red ferrule, then a hex steel lug, then a rigid eyelet. Add a gold collar, so the eyelets (the brief's focal detail) stand out from the chain links.
- **The cutting bevel is ambiguous.** Model it as a flat-ground primary bevel on both faces, each 15–18% of the blade width.
- **The chain is too close to the background value.** Make the chain steel cooler and a little lighter (#4C5056, chamfer highlights #A9AFB5) so it doesn't merge with the charcoal grips.
- **One link mesh for all 9 links,** with a flattened octagonal cross-section and a 90° alternation.
- **Corrections to the first QC pass:**
  - In the tip notch, the inner prong is the taller one, and the notch is about 0.11 of the cleaver length deep with a rounded root.
  - The chain dimensions were overstated by 15–20%. Use an arc of about 0.83 L, a resting span of about 0.67 L and a sag of about 0.19 L, where L is one cleaver's length.
  - A diamond-shaped boss around the gold rivet was missing from the build spec.

## Lessons from the videos

These come from sampled frames, not continuous playback. Timing, simulation method and collision can't be known from stills.

- **Ribbon (1.mp4).**
  - The root is pinned hard, and the ribbon's freedom grows toward the tip.
  - The spear stays completely still while the ribbon moves.
  - It's a twisting flat strip, not a tube.
  - The free end goes through 3–4 distinct poses.
  - It's a seamless loop of about 3 seconds.
  - *For Sunbound, take the root behaviour only; its streamer stays short (per the brief). The full spiral ribbon goes on the new spear, at your request.*
- **Auras (2.mp4).**
  - The equip reveal is one big burst, then a small glow that stays close to the weapon.
  - Each weapon keeps one dominant energy hue.
  - Full-length bloom (the red weapon around 10–12 s) hides the structure. That's the counterexample for Oathsplitter.
- **Chain (FULL / Chain Weapon.mp4).** There are four readable chain states: gathered, snap-apart with an upward bow, taut at full separation (this is the length check), and recovery.
  - The chain should be taut exactly at maximum hand separation.
  - The chain ends are anchored at the wrists in the reference. For Warlink they move to the pommel eyelets.
  - The third-person whip segment (4.8–7.8 s) is long and loopy. Don't copy it; the brief calls for a compact tether.
- **Rig in the clips:** the creator's blocky R6-style test dummy with first-person viewmodel hands. That's not your project's rig, so it doesn't tell us which rig your game uses.

## Blocked here: what's needed from you

| Item | What unblocks it |
|---|---|
| Rig, scale and attachment conventions | Your Roblox project (.rbxl or a Rojo repo), or at least the rig type, avatar height and your existing Tool/attachment names |
| Checking import scale and orientation | Import one exported FBX in Studio and send a screenshot |
| Equip on your avatar, VFX, first- and third-person checks, performance | A Studio playtest on your side (this container can't run Roblox) |
| Hash-checking the concepts | The original concept PNGs (only compressed webp copies arrived), plus `iop_blade_i.png`, `001025`, `000732` and `3.mp4` |
