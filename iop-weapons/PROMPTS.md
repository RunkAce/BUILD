# Iop Arsenal: image generation prompts

Use these with the tool that made the original reference art (Midjourney, Stable Diffusion/Flux, DALL·E, Leonardo, etc.).

**Always attach the reference image as a style reference.** This is the biggest factor in getting a matching style:
- Midjourney: `--sref <reference image URL> --sw 300`, and add `--ar 1:1 --stylize 150`
- Stable Diffusion / Flux: use IP-Adapter (style) or img2img on the reference at a denoise of about 0.6–0.75
- Leonardo / DALL·E / others: upload the reference as a "style" or "image guidance" input

The `png/` silhouettes in this folder can also go into ControlNet (canny/lineart) or img2img as a shape guide.

---

## Shared style block (put at the start of every prompt)

```
stylized hand-painted fantasy game weapon icon, digital painting, soft painterly brush texture,
faceted two-tone shading split along a central ridge (warm lit plane and cool shadow plane),
no outlines, clean readable silhouette, small curved thorn spikes along the edges,
hooked crescent guard, long thin tapered spike pommel, open slot cut through the blade,
single weapon floating diagonally at 45 degrees, tip pointing top-right,
plain near-black background, soft warm highlights, game asset, centered, high detail
```

## Negative prompt (SD / Flux / Leonardo)

```
photo, realistic, 3d render, metallic chrome reflections, black outlines, cel shading, text,
watermark, hands, character, multiple weapons, busy background, blurry, low detail, cropped
```

---

## 01 · Oathbreaker: Sword (one-handed)
```
[STYLE] one-handed sword, straight steel-blue blade widening slightly toward the guard with
a long open slot down the middle, three thorn spikes on the edges, gold crescent guard with
upward hooked tips, short gold grip ending in a long gold spike pommel, small fiery orange
flame-shaped gem at the center of the guard
```

## 02 · Wrathbringer: Greatsword (two-handed)
```
[STYLE] massive two-handed greatsword, broad charcoal-black blade with a chiseled angular tip,
a glowing molten-orange crack channel running down the center of the blade, row of jagged saw
teeth along one edge, large molten-orange crescent guard with hooked tips, long dark grip with
an orange ring, spike pommel, embers drifting off the blade
```

## 03 · Quickfang: Dagger
```
[STYLE] short dagger, leaf-shaped jade-green blade with a narrow open slot, hooked thorn barbs
near the base, small bone-ivory crescent guard, short bone-ivory grip ending in a sharp spike
pommel, compact and fast-looking
```

## 04 · Skullsplitter's Grin: Axe (two-handed)
```
[STYLE] two-handed battle axe, large crimson-red crescent axe head with a curved cutting edge
and a slit cut through it, a long crimson back spike opposite the blade, long bone-ivory haft
with small red thorns along it, spike butt end
```

## 05 · Mountain's Knock: Hammer (two-handed)
```
[STYLE] two-handed war hammer, heavy beveled bronze block head with teal-capped striking faces,
teal spikes jutting out of both faces and a bronze spike on top, long teal haft with a bronze
collar, spike butt end, heavy and brutal
```

## 06 · Stubborn Pillar: Staff (two-handed)
```
[STYLE] two-handed battle staff, long silver shaft, top ends in a violet crescent fork whose two
prongs curve up into thorn points, a glowing violet orb held between the prongs, small silver
crescent collar below the head, spike butt end
```

## 07 · Spark of Bravado: Wand (one-handed)
```
[STYLE] short magic wand, ivory shaft, topped with a spiky rose-pink crystal shard surrounded by
four thorn points, ivory crescent cup holding the crystal, soft pink glow, spike pommel
```

## 08 · Hornsnap: Bow (two-handed)
```
[STYLE] recurve bow, amber-gold limbs shaped like a crescent horn with hooked recurved tips and
small thorns on the back, forest-green wrapped grip in the middle, thin taut bowstring, no arrow
```

## 09 · Trenchbreaker: Shovel (two-handed)
```
[STYLE] battle shovel used as a weapon, pointed rust-orange spade head with sharpened edges, an
open slot through the blade and thorn spikes on the shoulders, long ice-blue haft with a small
ice-blue crescent collar, T-shaped crossbar grip at the end
```

## 10 · Last Laugh: Scythe (two-handed)
```
[STYLE] war scythe, long sweeping plum-purple curved blade with small thorn barbs on the inner
edge, a back spike at the top of the haft, long dark ebony wood haft with purple thorns,
spike butt end
```

## 11 · Stonejaw: Pickaxe (two-handed)
```
[STYLE] two-handed war pickaxe, wide curved sandstone-yellow pick head with two long pointed
prongs, a short spike on top, blood-red haft with small thorns, spike butt end
```

## 12 · Unbowed Charge: Lance (two-handed)
```
[STYLE] cavalry lance, long white-gold leaf-shaped spear tip with downward-hooked barbs and a
narrow slot, long royal-blue shaft, royal-blue conical hand guard (vamplate) rimmed with
white-gold thorns, spike butt end
```

## 13 · Iop's Brow: Shield (off-hand)
```
[STYLE but replace "floating diagonally" with "front view, slightly tilted"] kite shield,
crimson-red face with a bone-ivory rim, thorn spikes all around the rim and a long spike at the
bottom point, ivory crescent across the top, a large fiery orange flame-tuft emblem in the center
```

---

### Tips
- Generate 4–8 variations of each weapon and keep the best one. Keep the same seed and `--sref` across the whole set so it looks consistent.
- If a color drifts, put it first and repeat it, for example `steel-blue blade, steel-blue`.
- For game icons, remove the background afterward with a background remover, or generate on a flat black background and key it out.
