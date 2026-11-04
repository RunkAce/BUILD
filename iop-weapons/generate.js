// Iop weapon set generator.
// Paints every weapon as layered, faceted SVG in the house style
// (two-tone light/shadow planes split on a center ridge, thorn spikes,
// hooked crescent guards, spike pommels, cut-through slots, painterly
// texture, near-black background), then renders PNGs with Playwright.
//
//   node generate.js        -> svg/*.svg, png/*.png, iop-weapons-sheet.png

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = __dirname;
const SIZE = 1024;

// ---------- palettes: H highlight, L light plane, M mid, D shadow ----------
const PAL = {
  steel:     { H: '#ffffff', L: '#dfe9f2', M: '#a3b7ca', D: '#4e6580' },
  gold:      { H: '#fff2b8', L: '#ffd25e', M: '#e09a22', D: '#7f4c0c' },
  char:      { H: '#a29bb0', L: '#6b6475', M: '#423d4a', D: '#1d1b22' },
  molten:    { H: '#fff0b0', L: '#ffb347', M: '#ff641a', D: '#9a2208' },
  jade:      { H: '#f2fff6', L: '#bfeccf', M: '#6cc08e', D: '#24603f' },
  bone:      { H: '#fffaf0', L: '#efe5cf', M: '#c9bb9b', D: '#6f6248' },
  crimson:   { H: '#ffd0c6', L: '#ff7f6a', M: '#d1352a', D: '#5e1210' },
  bronze:    { H: '#fff0cf', L: '#f2c787', M: '#bf8743', D: '#5f3a1a' },
  teal:      { H: '#d8fff8', L: '#8eeadb', M: '#26aa97', D: '#0f4f48' },
  violet:    { H: '#f6ecff', L: '#d9bdff', M: '#9563d6', D: '#3f1f6a' },
  silver:    { H: '#ffffff', L: '#eef1f6', M: '#b8bfcb', D: '#5e6573' },
  rose:      { H: '#fff0f5', L: '#ffc4d9', M: '#ec5f94', D: '#701a3e' },
  amber:     { H: '#fff6d6', L: '#ffdc8f', M: '#eda12c', D: '#7e4c0e' },
  forest:    { H: '#e6ffd8', L: '#b3e396', M: '#4a9636', D: '#1b4517' },
  rust:      { H: '#ffe0c8', L: '#f0ad80', M: '#bd6136', D: '#562512' },
  ice:       { H: '#f4feff', L: '#bdeefa', M: '#5ebcd8', D: '#1b5a70' },
  plum:      { H: '#f5e6ff', L: '#d6b2ef', M: '#8a49b5', D: '#361351' },
  ebony:     { H: '#c9b6a6', L: '#8c7a6e', M: '#5a4a40', D: '#2a201b' },
  sand:      { H: '#fffbe0', L: '#fbe7a6', M: '#d9ae45', D: '#735311' },
  blood:     { H: '#ffc9c0', L: '#f0796a', M: '#ad221b', D: '#4d0e0b' },
  royal:     { H: '#e3ecff', L: '#9fbcff', M: '#2c56c9', D: '#0d1f5f' },
  whitegold: { H: '#ffffff', L: '#fff6df', M: '#e6d29a', D: '#8f7944' },
  ember:     { H: '#fff3c4', L: '#ffb15c', M: '#f05a1c', D: '#7a1a06' }, // Iop flame emblem
};

// ---------- tiny SVG toolkit ----------
let defs, gid, holes;
function reset() { defs = []; gid = 0; holes = []; }
const f = (n) => n.toFixed(1);
const pts = (a) => a.map((p) => f(p[0]) + ',' + f(p[1])).join(' ');
const rad = (d) => (d * Math.PI) / 180;

function lg(stops, x1 = 0, y1 = 0, x2 = 0, y2 = 1) {
  const id = 'g' + gid++;
  defs.push(`<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">` +
    stops.map(([o, c, a = 1]) => `<stop offset="${o}" stop-color="${c}" stop-opacity="${a}"/>`).join('') +
    `</linearGradient>`);
  return `url(#${id})`;
}
function rg(stops, cx = 0.4, cy = 0.35) {
  const id = 'g' + gid++;
  defs.push(`<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="0.7">` +
    stops.map(([o, c, a = 1]) => `<stop offset="${o}" stop-color="${c}" stop-opacity="${a}"/>`).join('') +
    `</radialGradient>`);
  return `url(#${id})`;
}
const lightFill = (p) => lg([[0, p.M], [0.3, p.H], [0.55, p.L], [0.8, p.L], [1, p.M]], 0, 0, 0.25, 1);
const darkFill = (p) => lg([[0, p.D], [0.45, p.M], [1, p.D]], 0, 0, 0.25, 1);
const poly = (a, fill, extra = '') => `<polygon points="${pts(a)}" fill="${fill}" ${extra}/>`;

// Symmetric vertical piece. profile: [[y, halfWidth], ...] top -> bottom.
function sym(profile, p, cx = 0) {
  const ridge = profile.slice().reverse().map(([y]) => [cx, y]);
  const left = profile.map(([y, w]) => [cx - w, y]).concat(ridge);
  const right = profile.map(([y, w]) => [cx + w, y]).concat(ridge);
  const streak = profile.map(([y, w]) => [cx - w * 0.6, y])
    .concat(profile.slice().reverse().map(([y, w]) => [cx - w * 0.18, y]));
  const rim = profile.map(([y, w]) => [cx - w, y]);
  return poly(left, lightFill(p)) + poly(right, darkFill(p)) +
    poly(streak, p.H, 'opacity="0.28"') +
    `<polyline points="${pts(rim)}" fill="none" stroke="${p.H}" stroke-width="1.6" opacity="0.55"/>`;
}
// Symmetric horizontal piece. profile: [[x, halfHeight], ...] left -> right.
function hsym(profile, p, cy = 0) {
  const ridge = profile.slice().reverse().map(([x]) => [x, cy]);
  const top = profile.map(([x, h]) => [x, cy - h]).concat(ridge);
  const bot = profile.map(([x, h]) => [x, cy + h]).concat(ridge);
  const streak = profile.map(([x, h]) => [x, cy - h * 0.6])
    .concat(profile.slice().reverse().map(([x, h]) => [x, cy - h * 0.2]));
  return poly(top, lg([[0, p.M], [0.35, p.H], [0.7, p.L], [1, p.M]], 0, 0, 1, 0.3)) +
    poly(bot, lg([[0, p.D], [0.5, p.M], [1, p.D]], 0, 0, 1, 0.3)) +
    poly(streak, p.H, 'opacity="0.25"');
}
// Thorn spike. ang: 0 = up, 90 = right. bend curls the tip sideways.
function spike(x, y, ang, len, w, p, bend = 0.18) {
  const d = [Math.sin(rad(ang)), -Math.cos(rad(ang))];
  const n = [Math.cos(rad(ang)), Math.sin(rad(ang))];
  const tip = [x + d[0] * len + n[0] * len * bend, y + d[1] * len + n[1] * len * bend];
  const mid = [x + d[0] * len * 0.45, y + d[1] * len * 0.45];
  const b1 = [x + n[0] * w, y + n[1] * w];
  const b2 = [x - n[0] * w, y - n[1] * w];
  return poly([b1, mid, tip, [x, y]], p.L) + poly([[x, y], tip, mid, b2], p.D) +
    poly([[x, y], tip, b2], p.M, 'opacity="0.55"');
}
// Crescent band along an arc. taper: 'both' | 'start' (thick at a0) | 'end'.
function crescent(cx, cy, r, th, a0, a1, p, taper = 'both') {
  const N = 48, outer = [], mid = [], inner = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, a = rad(a0 + (a1 - a0) * t);
    const k = taper === 'both' ? Math.pow(Math.sin(Math.PI * t), 0.75)
      : taper === 'start' ? Math.pow(1 - t, 0.8) : Math.pow(t, 0.8);
    const u = [Math.cos(a), Math.sin(a)], h = (th * k) / 2;
    outer.push([cx + u[0] * (r + h), cy + u[1] * (r + h)]);
    mid.push([cx + u[0] * r, cy + u[1] * r]);
    inner.push([cx + u[0] * (r - h), cy + u[1] * (r - h)]);
  }
  return poly(outer.concat(mid.slice().reverse()), lg([[0, p.L], [0.5, p.H], [1, p.L]], 0, 0, 1, 1)) +
    poly(mid.concat(inner.slice().reverse()), lg([[0, p.D], [0.5, p.M], [1, p.D]], 0, 0, 1, 1)) +
    `<polyline points="${pts(outer)}" fill="none" stroke="${p.H}" stroke-width="1.5" opacity="0.5"/>`;
}
// Iop flame-tuft emblem (unit height ~125, base at y).
function flame(x, y, s, p = PAL.ember) {
  const d = 'M0,-100 C18,-70 40,-50 38,-20 C36,10 18,25 0,25 C-18,25 -36,10 -38,-20 ' +
    'C-40,-45 -22,-58 -14,-80 C-10,-60 0,-55 4,-60 C6,-75 2,-88 0,-100 Z';
  const core = 'M0,-55 C10,-38 20,-25 17,-8 C14,8 6,14 0,14 C-8,14 -16,6 -16,-8 C-16,-25 -6,-35 0,-55 Z';
  return `<g transform="translate(${x},${y}) scale(${s})">` +
    `<path d="${d}" fill="${lg([[0, p.L], [0.5, p.M], [1, p.D]], 0, 0, 1, 0.4)}"/>` +
    `<path d="${core}" fill="${p.H}" opacity="0.85"/></g>`;
}
function orb(x, y, r, p) {
  return `<circle cx="${x}" cy="${y}" r="${r * 1.7}" fill="${p.M}" opacity="0.25" filter="url(#glow)"/>` +
    `<circle cx="${x}" cy="${y}" r="${r}" fill="${rg([[0, p.H], [0.35, p.L], [0.8, p.M], [1, p.D]])}"/>` +
    `<ellipse cx="${x - r * 0.35}" cy="${y - r * 0.4}" rx="${r * 0.25}" ry="${r * 0.14}" fill="#fff" opacity="0.7" transform="rotate(-30 ${x - r * 0.35} ${y - r * 0.4})"/>`;
}
const glowPoly = (a, p) => poly(a, p.M, 'opacity="0.55" filter="url(#glow)"');
// Cut-through slot (masked out, like the reference's split blades).
function hole(a) { holes.push(a); return ''; }
const lens = (cx, y0, y1, w) => [[cx, y0], [cx + w * 0.8, y0 + (y1 - y0) * 0.15], [cx + w, y0 + (y1 - y0) * 0.7], [cx, y1], [cx - w, y0 + (y1 - y0) * 0.7], [cx - w * 0.8, y0 + (y1 - y0) * 0.15]];

// ---------- the weapons (local frame: tip points up, y- is up) ----------
const W = [];

W.push({ id: '01-sword', name: 'Oathbreaker Sword', type: 'Sword (one-handed)', colors: 'Steel blue + gold',
  rot: 35, scale: 1.05, cy: -90, draw() {
  const s = PAL.steel, g = PAL.gold;
  return sym([[0, 12], [140, 10], [150, 15], [168, 10], [270, 0]], g) +
    sym([[-440, 0], [-400, 14], [-330, 26], [-200, 30], [-120, 36], [-60, 46], [-20, 42], [0, 40]], s) +
    hole(lens(0, -330, -110, 8)) +
    spike(-29, -250, -62, 28, 6, s) + spike(33, -150, 62, 26, 6, s) + spike(-44, -70, -70, 32, 7, s) +
    crescent(0, -70, 84, 24, 8, 172, g) +
    spike(-83, -58, -20, 34, 7, g) + spike(83, -58, 20, 34, 7, g) +
    flame(0, 14, 0.42);
}});

W.push({ id: '02-greatsword', name: 'Wrathbringer', type: 'Greatsword (two-handed)', colors: 'Charcoal + molten orange',
  rot: 35, scale: 0.92, cy: -20, draw() {
  const c = PAL.char, m = PAL.molten;
  const channel = [[0, -400], [8, -370], [10, -110], [0, -70], [-10, -110], [-8, -370]];
  let teeth = '';
  [-350, -290, -230, -170].forEach((y) => { teeth += spike(56, y, 72, 26, 9, c, 0.25); });
  return sym([[0, 15], [140, 14], [150, 20], [170, 20], [180, 14], [320, 12], [332, 19], [348, 12], [450, 0]], c) +
    sym([[140, 18], [150, 22], [170, 22], [180, 18]], m) +
    sym([[-480, 0], [-440, 28], [-390, 64], [-300, 58], [-200, 54], [-100, 52], [-30, 60], [0, 52]], c) +
    teeth + spike(-60, -60, -75, 40, 10, c) +
    glowPoly(channel, m) + sym([[-400, 0], [-370, 7], [-110, 10], [-70, 0]], m) +
    crescent(0, -100, 122, 30, 12, 168, m) +
    spike(-119, -75, -15, 48, 9, m) + spike(119, -75, 15, 48, 9, m) +
    flame(0, 20, 0.5);
}});

W.push({ id: '03-dagger', name: 'Quickfang', type: 'Dagger', colors: 'Jade green + bone',
  rot: 35, scale: 1.45, cy: -60, draw() {
  const j = PAL.jade, b = PAL.bone;
  return sym([[0, 9], [100, 8], [110, 12], [122, 8], [190, 0]], b) +
    sym([[-310, 0], [-260, 15], [-170, 30], [-90, 34], [-30, 26], [0, 24]], j) +
    hole(lens(0, -210, -80, 6)) +
    spike(-33, -110, -55, 34, 7, j) + spike(30, -180, 58, 26, 6, j) + spike(-24, -40, -80, 20, 5, j) +
    crescent(0, -40, 58, 18, 15, 165, b) +
    spike(-56, -25, -25, 26, 6, b) + spike(56, -25, 25, 26, 6, b) +
    flame(0, 12, 0.3);
}});

W.push({ id: '04-axe', name: 'Skullsplitter\'s Grin', type: 'Axe (two-handed)', colors: 'Crimson + bone',
  rot: 35, scale: 0.92, cy: 0, draw() {
  const r = PAL.crimson, b = PAL.bone;
  const cx = 20, cy = -275, R = 180, up = [], lo = [];
  for (let i = 0; i <= 24; i++) {
    const a1 = rad(-70 + 70 * i / 24), a2 = rad(70 * i / 24);
    up.push([cx + R * Math.cos(a1), cy + R * Math.sin(a1)]);
    lo.push([cx + R * Math.cos(a2), cy + R * Math.sin(a2)]);
  }
  const edge = up.concat(lo.slice(1)).map(([x, y]) => [cx + (x - cx) * 0.93, cy + (y - cy) * 0.93]);
  return sym([[-440, 0], [-400, 12], [400, 12], [415, 17], [430, 12], [490, 0]], b) +
    poly([[12, -350]].concat(up, [[12, -275]]), lg([[0, r.M], [0.4, r.H], [0.7, r.L], [1, r.M]], 0, 0, 1, 1)) +
    poly([[12, -275]].concat(lo, [[12, -200]]), lg([[0, r.D], [0.5, r.M], [1, r.D]], 0, 0, 1, 1)) +
    `<polyline points="${pts(edge)}" fill="none" stroke="${r.H}" stroke-width="5" opacity="0.45"/>` +
    hole([[118, -345], [132, -300], [134, -250], [118, -205], [106, -275]]) +
    spike(-12, -275, -90, 110, 28, r, 0.1) + spike(-12, -330, -60, 40, 9, r) + spike(-12, -220, -120, 40, 9, r) +
    spike(-12, -40, -70, 26, 6, r) + spike(12, 60, 70, 26, 6, r) + spike(-12, 160, -70, 26, 6, r) +
    flame(60, -255, 0.42);
}});

W.push({ id: '05-hammer', name: 'Mountain\'s Knock', type: 'Hammer (two-handed)', colors: 'Bronze + teal',
  rot: 35, scale: 0.9, cy: 0, draw() {
  const z = PAL.bronze, t = PAL.teal;
  return sym([[-300, 13], [380, 13], [392, 19], [408, 13], [480, 0]], t) +
    sym([[-300, 24], [-260, 24], [-250, 18]], z) +
    spike(0, -440, 0, 70, 18, z, 0.05) +
    hsym([[-175, 44], [-155, 72], [-115, 82], [115, 82], [155, 72], [175, 44]], z, -360) +
    hsym([[-182, 30], [-160, 52], [-150, 52], [-145, 30]], t, -360) +
    hsym([[145, 30], [150, 52], [160, 52], [182, 30]], t, -360) +
    spike(-182, -360, -90, 60, 18, t, 0.05) + spike(182, -360, 90, 60, 18, t, 0.05) +
    spike(-100, -282, -160, 30, 8, z) + spike(100, -282, 160, 30, 8, z) +
    flame(0, -335, 0.5);
}});

W.push({ id: '06-staff', name: 'Stubborn Pillar', type: 'Staff (two-handed)', colors: 'Violet + silver',
  rot: 35, scale: 0.9, cy: 0, draw() {
  const v = PAL.violet, s = PAL.silver;
  return sym([[-330, 10], [100, 10], [110, 15], [125, 10], [440, 10], [500, 0]], s) +
    crescent(0, -400, 88, 30, 0, 180, v) +
    spike(-88, -400, -12, 80, 13, v) + spike(88, -400, 12, 80, 13, v) +
    spike(-100, -360, -110, 30, 7, v) + spike(100, -360, 110, 30, 7, v) +
    orb(0, -410, 44, v) +
    crescent(0, -300, 34, 14, 20, 160, s) +
    flame(0, -295, 0.28);
}});

W.push({ id: '07-wand', name: 'Spark of Bravado', type: 'Wand (one-handed)', colors: 'Rose pink + ivory',
  rot: 35, scale: 1.5, cy: -30, draw() {
  const r = PAL.rose, b = PAL.bone;
  return sym([[-130, 9], [180, 7], [190, 11], [202, 7], [260, 0]], b) +
    crescent(0, -175, 52, 18, 8, 172, b) +
    sym([[-340, 0], [-290, 22], [-220, 36], [-160, 24], [-120, 0]], r) +
    spike(-34, -225, -80, 46, 8, r) + spike(34, -225, 80, 46, 8, r) +
    spike(-20, -290, -35, 30, 5, r) + spike(20, -290, 35, 30, 5, r) +
    `<circle cx="0" cy="-230" r="70" fill="${r.L}" opacity="0.18" filter="url(#glow)"/>` +
    flame(0, -40, 0.32);
}});

W.push({ id: '08-bow', name: 'Hornsnap', type: 'Bow (two-handed)', colors: 'Amber + forest green',
  rot: 35, scale: 0.98, cy: 0, draw() {
  const a = PAL.amber, g = PAL.forest, b = PAL.bone;
  const cx = -260, R = 360;
  const tipT = [cx + R * Math.cos(rad(-60)), R * Math.sin(rad(-60))];
  const tipB = [cx + R * Math.cos(rad(60)), R * Math.sin(rad(60))];
  return `<line x1="${f(tipT[0])}" y1="${f(tipT[1])}" x2="${f(tipB[0])}" y2="${f(tipB[1])}" stroke="${b.L}" stroke-width="3" opacity="0.8"/>` +
    crescent(cx, 0, R, 40, -62, 62, a) +
    spike(tipT[0], tipT[1], -40, 70, 9, a, 0.3) + spike(tipB[0], tipB[1], 220, 70, 9, a, -0.3) +
    spike(cx + 380 * Math.cos(rad(-30)), 380 * Math.sin(rad(-30)), 65, 30, 7, a) +
    spike(cx + 380 * Math.cos(rad(30)), 380 * Math.sin(rad(30)), 115, 30, 7, a) +
    sym([[-70, 22], [-58, 28], [58, 28], [70, 22]], g, 100) +
    spike(124, -60, 80, 26, 7, g) + spike(124, 60, 100, 26, 7, g) +
    flame(100, 18, 0.32);
}});

W.push({ id: '09-shovel', name: 'Trenchbreaker', type: 'Shovel (two-handed)', colors: 'Rust orange + ice blue',
  rot: 35, scale: 0.9, cy: 0, draw() {
  const r = PAL.rust, i = PAL.ice;
  return sym([[-220, 11], [430, 11], [445, 0]], i) +
    hsym([[-62, 0], [-48, 12], [48, 12], [62, 0]], i, 445) +
    spike(-60, 445, -100, 30, 8, i) + spike(60, 445, 100, 30, 8, i) +
    sym([[-490, 0], [-440, 40], [-390, 72], [-310, 84], [-240, 76], [-220, 34], [-205, 16]], r) +
    hole(lens(0, -420, -280, 14)) +
    spike(-74, -238, -135, 34, 9, r) + spike(74, -238, 135, 34, 9, r) +
    spike(-60, -400, -60, 30, 7, r) + spike(60, -400, 60, 30, 7, r) +
    crescent(0, -235, 30, 12, 15, 165, i) +
    flame(0, -250, 0.34);
}});

W.push({ id: '10-scythe', name: 'Last Laugh', type: 'Scythe (two-handed)', colors: 'Plum + ebony',
  rot: 35, scale: 0.82, cy: -90, draw() {
  const p = PAL.plum, e = PAL.ebony;
  return sym([[-440, 12], [440, 12], [455, 18], [470, 12], [500, 0]], e) +
    crescent(-150, -250, 227, 74, -48.6, -178, p, 'start') +
    spike(-183, -439, 170, 32, 7, p) + spike(-290, -393, 135, 26, 6, p) +
    spike(0, -420, 30, 70, 12, p) +
    crescent(0, -380, 26, 12, 10, 170, e) +
    spike(-12, -300, -80, 24, 6, p) + spike(12, -200, 80, 24, 6, p) +
    flame(18, -392, 0.32);
}});

W.push({ id: '11-pickaxe', name: 'Stonejaw', type: 'Pickaxe (two-handed)', colors: 'Sandstone + blood red',
  rot: 35, scale: 0.9, cy: -10, draw() {
  const s = PAL.sand, b = PAL.blood;
  return sym([[-420, 13], [440, 13], [452, 19], [466, 13], [500, 0]], b) +
    crescent(0, -120, 300, 50, -152, -28, s) +
    sym([[-460, 0], [-440, 30], [-385, 30], [-370, 16]], s) +
    spike(0, -460, 0, 46, 12, s, 0.05) +
    spike(-140, -380, -20, 34, 8, s) + spike(140, -380, 20, 34, 8, s) +
    spike(-12, -280, -70, 24, 6, b) + spike(12, -200, 70, 24, 6, b) +
    flame(0, -392, 0.3);
}});

W.push({ id: '12-lance', name: 'Unbowed Charge', type: 'Lance (two-handed)', colors: 'White gold + royal blue',
  rot: 35, scale: 0.88, cy: 0, draw() {
  const w = PAL.whitegold, r = PAL.royal;
  return sym([[-250, 10], [470, 10], [500, 0]], r) +
    sym([[-500, 0], [-450, 14], [-370, 30], [-300, 24], [-255, 12], [-240, 12]], w) +
    hole(lens(0, -420, -310, 6)) +
    spike(-26, -320, -150, 46, 10, w) + spike(26, -320, 150, 46, 10, w) +
    sym([[-245, 16], [-230, 16]], w) +
    sym([[-40, 12], [70, 92], [88, 92], [96, 14]], r) +
    spike(-92, 90, -125, 34, 8, w) + spike(92, 90, 125, 34, 8, w) +
    spike(-60, 50, -100, 22, 6, w) + spike(60, 50, 100, 22, 6, w) +
    flame(0, 60, 0.38);
}});

W.push({ id: '13-shield', name: 'Iop\'s Brow', type: 'Shield (off-hand)', colors: 'Crimson + bone',
  rot: -8, scale: 1.2, sx: 1, cy: 0, draw() {
  const c = PAL.crimson, b = PAL.bone;
  const prof = [[-270, 150], [-250, 192], [-110, 204], [40, 184], [160, 122], [260, 42], [315, 0]];
  const rim = prof.map(([y, w], i) => [i === 0 ? y - 18 : y + (i === prof.length - 1 ? 22 : 0), w + 20]);
  return spike(-205, -248, -55, 62, 14, b) + spike(205, -248, 55, 62, 14, b) +
    spike(-212, -40, -95, 40, 10, b) + spike(212, -40, 95, 40, 10, b) +
    spike(-150, 160, -125, 34, 9, b) + spike(150, 160, 125, 34, 9, b) +
    spike(0, 330, 180, 60, 12, b, 0) +
    sym(rim, b) + sym(prof, c) +
    crescent(0, -290, 100, 22, 30, 150, b) +
    flame(0, 40, 2.2, PAL.ember) +
    spike(0, -288, 0, 60, 12, b, 0);
}});

// ---------- build ----------
const FILTERS = `
<filter id="paint" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="4" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.006 0.035" numOctaves="4" seed="11" result="n2"/>
  <feColorMatrix in="n2" type="saturate" values="0" result="g"/>
  <feComposite in="g" in2="d" operator="in" result="gi"/>
  <feBlend in="gi" in2="d" mode="soft-light" result="b"/>
  <feComposite in="b" in2="d" operator="in"/>
</filter>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="14"/></filter>
<radialGradient id="bg" cx="0.5" cy="0.5" r="0.75"><stop offset="0" stop-color="#1a1918"/><stop offset="1" stop-color="#0a0a0a"/></radialGradient>
<filter id="shade" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000" flood-opacity="0.6"/></filter>`;

function buildSVG(w, bg = true) {
  reset();
  const body = w.draw();
  const mask = holes.length
    ? `<mask id="m" maskUnits="userSpaceOnUse" x="-2000" y="-2000" width="4000" height="4000"><rect x="-2000" y="-2000" width="4000" height="4000" fill="#fff"/>${holes.map((h) => poly(h, '#000')).join('')}</mask>`
    : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${SIZE}" height="${SIZE}" viewBox="0 0 ${SIZE} ${SIZE}">
<defs>${FILTERS}${defs.join('')}</defs>
${bg ? `<rect width="${SIZE}" height="${SIZE}" fill="url(#bg)"/>` : ''}
<g transform="translate(${SIZE / 2},${SIZE / 2}) rotate(${w.rot}) scale(${w.scale * 1.0 * (w.sx ?? 1.22)},${w.scale * 1.0}) translate(0,${-w.cy})">
  <defs>${mask}</defs>
  <g filter="url(#shade)"><g filter="url(#paint)"><g ${holes.length ? 'mask="url(#m)"' : ''}>${body}</g></g></g>
</g></svg>`;
}

(async () => {
  for (const d of ['svg', 'png', 'png-transparent']) fs.mkdirSync(path.join(OUT, d), { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: SIZE, height: SIZE } });
  for (const w of W) {
    const svg = buildSVG(w);
    fs.writeFileSync(path.join(OUT, 'svg', w.id + '.svg'), svg);
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.locator('svg').screenshot({ path: path.join(OUT, 'png', w.id + '.png') });
    await page.setContent(`<html><body style="margin:0;background:transparent">${buildSVG(w, false)}</body></html>`);
    await page.locator('svg').screenshot({ path: path.join(OUT, 'png-transparent', w.id + '.png'), omitBackground: true });
    console.log('rendered', w.id);
  }
  // contact sheet
  const cards = W.map((w) => `<figure><img src="data:image/png;base64,${fs.readFileSync(path.join(OUT, 'png', w.id + '.png')).toString('base64')}"><figcaption><b>${w.name}</b><span>${w.type}</span><i>${w.colors}</i></figcaption></figure>`).join('');
  const html = `<html><head><style>
    body{margin:0;background:#0b0b0b;color:#efe5cf;font-family:Georgia,serif;padding:40px}
    h1{margin:0 0 6px;font-size:44px;letter-spacing:2px;color:#ffb15c}
    p.sub{margin:0 0 30px;color:#a89f8c;font-size:18px}
    .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
    figure{margin:0;background:#141312;border:1px solid #2a2622;border-radius:12px;overflow:hidden}
    img{width:100%;display:block}
    figcaption{padding:12px 16px 16px;display:flex;flex-direction:column;gap:3px}
    b{font-size:22px} span{font-size:15px;color:#c9bb9b} i{font-size:14px;color:#8a8173}
  </style></head><body><h1>IOP ARSENAL</h1><p class="sub">One weapon per type, in the house style</p><div class="grid">${cards}</div></body></html>`;
  const sheet = await browser.newPage({ viewport: { width: 1800, height: 1000 } });
  await sheet.setContent(html, { waitUntil: 'load' });
  await sheet.screenshot({ path: path.join(OUT, 'iop-weapons-sheet.png'), fullPage: true });
  await browser.close();
})();
