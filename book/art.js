// Simple flat-style SVG illustration kit for "يوسف والعملاق".
// Every scene is drawn in a 1000 x 760 viewBox.

const C = {
  skin: '#f1c39a', skinShade: '#e2a97c', hair: '#4a2c1a', thobe: '#ffffff', thobeLine: '#d9d4cc',
  giantSkin: '#d69a6a', giantShade: '#bf8255', giantTunic: '#3f8a7e', giantTunicDark: '#2f6c62', beard: '#6b3f22',
  abaya: '#2b2b33', ink: '#3a2a20', sand: '#f0cf8f', sandDark: '#e2b56e', mountain: '#c9875a', mountainDark: '#a96c45',
  palmTrunk: '#9a6a3c', palmLeaf: '#4f9a4a', palmLeafDry: '#b9a35a', water: '#5bb8e0', waterLight: '#a9e2f5',
  rock: '#8f7f72', rockDark: '#6f6157', house: '#e9c99b', houseDark: '#d3ab77', red: '#d4483b',
};

const g = (x, y, s, body, flip = false) =>
  `<g transform="translate(${x} ${y}) scale(${flip ? -s : s} ${s})">${body}</g>`;

// ---------- backgrounds ----------
function sky(kind = 'day') {
  const stops = {
    day: ['#8fd3f4', '#d8f1fb'], hot: ['#f7b267', '#fde4b5'], sunset: ['#f08a5d', '#ffd29d'],
    night: ['#1d2b53', '#3c4f8a'], dawn: ['#a6c8ff', '#ffe3c2'],
  }[kind];
  return `<defs><linearGradient id="sky-${kind}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${stops[0]}"/><stop offset="1" stop-color="${stops[1]}"/></linearGradient></defs>
    <rect width="1000" height="760" fill="url(#sky-${kind})"/>`;
}
const sun = (x, y, r = 60, col = '#ffd94a') =>
  `<circle cx="${x}" cy="${y}" r="${r * 1.5}" fill="${col}" opacity=".25"/><circle cx="${x}" cy="${y}" r="${r}" fill="${col}"/>`;
const moon = (x, y) =>
  `<circle cx="${x}" cy="${y}" r="55" fill="#fff6d5"/><circle cx="${x + 25}" cy="${y - 15}" r="50" fill="#1d2b53"/>`;
function stars(n = 30) {
  let s = '';
  for (let i = 0; i < n; i++) {
    const x = (i * 337) % 1000, y = (i * 191) % 380, r = 2 + (i % 3);
    s += `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" opacity="${0.5 + (i % 5) / 10}"/>`;
  }
  return s;
}
const cloud = (x, y, s = 1) => g(x, y, s,
  `<g fill="#fff" opacity=".9"><ellipse cx="0" cy="0" rx="70" ry="30"/><ellipse cx="-40" cy="5" rx="45" ry="25"/>
   <ellipse cx="45" cy="5" rx="50" ry="25"/><ellipse cx="5" cy="-20" rx="40" ry="30"/></g>`);

const ground = (y = 600, col = C.sand, col2 = C.sandDark) =>
  `<path d="M0 ${y} Q 250 ${y - 40} 500 ${y} T 1000 ${y} V 760 H 0 Z" fill="${col}"/>
   <path d="M0 ${y + 70} Q 300 ${y + 30} 600 ${y + 80} T 1000 ${y + 60} V 760 H 0 Z" fill="${col2}" opacity=".5"/>`;

const bigMountain = (x = 700, w = 700, h = 520, base = 620) =>
  `<path d="M${x - w / 2} ${base} L${x - w / 6} ${base - h * 0.75} L${x} ${base - h} L${x + w / 5} ${base - h * 0.7} L${x + w / 2} ${base} Z" fill="${C.mountain}"/>
   <path d="M${x} ${base - h} L${x + w / 5} ${base - h * 0.7} L${x + w / 2} ${base} L${x + w / 10} ${base} Z" fill="${C.mountainDark}" opacity=".6"/>`;
const farHills = (base = 600) =>
  `<path d="M0 ${base} L120 ${base - 120} L260 ${base - 40} L420 ${base - 170} L580 ${base - 60} L760 ${base - 150} L1000 ${base - 30} V${base + 40} H0 Z" fill="#dca877" opacity=".7"/>`;

function palm(x, y, s = 1, dry = false) {
  const leaf = dry ? C.palmLeafDry : C.palmLeaf;
  const droop = dry ? 40 : 0;
  let leaves = '';
  [[-1, -10], [-1, 30], [1, -10], [1, 30], [0, -60]].forEach(([d, a]) => {
    leaves += `<path d="M0 -300 Q ${d * 90} ${-360 + a + droop} ${d * 170 || 10} ${-300 + a + droop * 2} Q ${d * 90} ${-320 + a + droop} 0 -300 Z" fill="${leaf}"/>`;
  });
  return g(x, y, s, `<path d="M-14 0 Q -4 -150 -8 -300 L 8 -300 Q 6 -150 14 0 Z" fill="${C.palmTrunk}"/>
    ${[...Array(8)].map((_, i) => `<path d="M-12 ${-30 - i * 34} l24 -8" stroke="#7c5230" stroke-width="4"/>`).join('')}
    ${leaves}${dry ? '' : '<circle cx="-10" cy="-290" r="10" fill="#b5651d"/><circle cx="8" cy="-286" r="10" fill="#b5651d"/>'}`);
}

function house(x, y, s = 1) {
  let cren = '';
  for (let i = 0; i < 6; i++) cren += `<path d="M${-90 + i * 32} -160 l12 -20 l12 20 Z" fill="${C.houseDark}"/>`;
  return g(x, y, s, `<rect x="-95" y="-160" width="190" height="160" fill="${C.house}"/>
    <rect x="-95" y="-160" width="190" height="14" fill="${C.houseDark}"/>${cren}
    <path d="M-25 0 V-70 Q 0 -95 25 -70 V0 Z" fill="#8a5a33"/>
    <path d="M-70 -120 l14 -14 l14 14 v20 h-28 Z" fill="#6d4a2e"/><path d="M42 -120 l14 -14 l14 14 v20 h-28 Z" fill="#6d4a2e"/>`);
}

const rock = (x, y, s = 1) => g(x, y, s,
  `<path d="M-120 0 Q -140 -90 -60 -130 Q 20 -170 90 -110 Q 150 -60 120 0 Z" fill="${C.rock}"/>
   <path d="M20 -150 Q 100 -120 120 0 L 60 0 Q 80 -90 20 -150 Z" fill="${C.rockDark}" opacity=".6"/>`);

const stream = (pts, w = 40) =>
  `<path d="${pts}" fill="none" stroke="${C.water}" stroke-width="${w}" stroke-linecap="round"/>
   <path d="${pts}" fill="none" stroke="${C.waterLight}" stroke-width="${w / 4}" stroke-dasharray="20 30" stroke-linecap="round"/>`;

const sheep = (x, y, s = 1, sad = false) => g(x, y, s,
  `<ellipse cx="0" cy="-45" rx="55" ry="35" fill="#f7f3ea"/>
   <circle cx="-30" cy="-60" r="22" fill="#f7f3ea"/><circle cx="25" cy="-65" r="22" fill="#f7f3ea"/>
   <rect x="-35" y="-20" width="9" height="20" fill="#555"/><rect x="25" y="-20" width="9" height="20" fill="#555"/>
   <ellipse cx="62" cy="-50" rx="20" ry="16" fill="#555"/><circle cx="68" cy="-54" r="3" fill="#fff"/>
   ${sad ? '<path d="M60 -40 q8 -5 14 0" stroke="#fff" stroke-width="2" fill="none"/>' : ''}`);

const falcon = (x, y, s = 1) => g(x, y, s,
  `<path d="M0 0 Q -60 -40 -120 -10 Q -60 -15 -20 10 Z M0 0 Q 60 -40 120 -10 Q 60 -15 20 10 Z" fill="#6b4a2f"/>
   <ellipse cx="0" cy="5" rx="16" ry="26" fill="#8a6440"/><circle cx="0" cy="-18" r="12" fill="#8a6440"/>
   <path d="M-4 -12 l4 10 l4 -10 Z" fill="#f2b53a"/>`);

const basket = (x, y, s = 1) => g(x, y, s,
  `${[...Array(7)].map((_, i) => `<ellipse cx="${-30 + i * 10}" cy="${-30 - (i % 2) * 8}" rx="9" ry="12" fill="#7b3f16"/>`).join('')}
   <path d="M-45 -28 H45 L35 0 H-35 Z" fill="#c8954f"/><path d="M-40 -18 H40 M-37 -9 H37" stroke="#a4743a" stroke-width="3"/>`);

const dallah = (x, y, s = 1) => g(x, y, s,
  `<path d="M-30 0 Q -40 -60 -20 -80 L20 -80 Q 40 -60 30 0 Z" fill="#d9a441"/>
   <path d="M-20 -80 Q 0 -120 20 -80" fill="#c08c2e"/><path d="M28 -55 Q 70 -70 75 -105" stroke="#d9a441" stroke-width="9" fill="none"/>
   <path d="M-28 -60 Q -60 -40 -30 -15" stroke="#c08c2e" stroke-width="7" fill="none"/>`);
const finjan = (x, y, s = 1) => g(x, y, s,
  `<path d="M-30 -45 H30 L20 0 H-20 Z" fill="#fff"/><path d="M-30 -45 H30" stroke="#d9a441" stroke-width="6"/><path d="M-25 -40 H25 L23 -32 H-23 Z" fill="#8a5a2a"/>`);

// ---------- characters ----------
function arm(sx, sy, ang, len, col, w, hand) {
  const r = (ang * Math.PI) / 180, ex = sx + Math.sin(r) * len, ey = sy + Math.cos(r) * len;
  return `<path d="M${sx} ${sy} L${ex.toFixed(1)} ${ey.toFixed(1)}" stroke="${col}" stroke-width="${w}" stroke-linecap="round"/>
    <circle cx="${ex.toFixed(1)}" cy="${ey.toFixed(1)}" r="${w * 0.55}" fill="${hand}"/>`;
}

function face(cx, cy, r, mood, eyeCol = '#2b1a10') {
  const ex = r * 0.38, ey = cy - r * 0.05, er = r * 0.11;
  let eyes = `<circle cx="${cx - ex}" cy="${ey}" r="${er}" fill="${eyeCol}"/><circle cx="${cx + ex}" cy="${ey}" r="${er}" fill="${eyeCol}"/>
    <circle cx="${cx - ex + er * .35}" cy="${ey - er * .35}" r="${er * .35}" fill="#fff"/><circle cx="${cx + ex + er * .35}" cy="${ey - er * .35}" r="${er * .35}" fill="#fff"/>`;
  if (mood === 'happy' || mood === 'sleep') {
    eyes = `<path d="M${cx - ex - er} ${ey} q${er} ${mood === 'sleep' ? er : -er} ${er * 2} 0 M${cx + ex - er} ${ey} q${er} ${mood === 'sleep' ? er : -er} ${er * 2} 0" stroke="${eyeCol}" stroke-width="${r * 0.07}" fill="none" stroke-linecap="round"/>`;
  }
  const my = cy + r * 0.42, mw = r * 0.32;
  const mouth = {
    smile: `<path d="M${cx - mw} ${my - 4} Q ${cx} ${my + mw * 0.8} ${cx + mw} ${my - 4}" stroke="${C.ink}" stroke-width="${r * 0.07}" fill="none" stroke-linecap="round"/>`,
    happy: `<path d="M${cx - mw} ${my - 6} Q ${cx} ${my + mw * 1.3} ${cx + mw} ${my - 6} Z" fill="#9b3b33"/>`,
    open: `<ellipse cx="${cx}" cy="${my}" rx="${mw * 0.45}" ry="${mw * 0.6}" fill="#9b3b33"/>`,
    worried: `<path d="M${cx - mw * .7} ${my + 4} Q ${cx} ${my - mw * 0.5} ${cx + mw * .7} ${my + 4}" stroke="${C.ink}" stroke-width="${r * 0.07}" fill="none" stroke-linecap="round"/>`,
    brave: `<path d="M${cx - mw * .7} ${my} H ${cx + mw * .7}" stroke="${C.ink}" stroke-width="${r * 0.07}" stroke-linecap="round"/>`,
    sleep: `<path d="M${cx - mw * .4} ${my} Q ${cx} ${my + mw * .4} ${cx + mw * .4} ${my}" stroke="${C.ink}" stroke-width="${r * 0.06}" fill="none" stroke-linecap="round"/>`,
  }[mood === 'surprised' ? 'open' : mood] || '';
  const cheeks = `<circle cx="${cx - r * 0.6}" cy="${cy + r * 0.25}" r="${r * 0.14}" fill="#f29c8f" opacity=".6"/><circle cx="${cx + r * 0.6}" cy="${cy + r * 0.25}" r="${r * 0.14}" fill="#f29c8f" opacity=".6"/>`;
  return eyes + mouth + cheeks;
}

// Yusuf: feet at (0,0), ~230 units tall at s=1. Arms: [left, right] angles (0 = down, 90 = toward +x, 180 = up)
function yusuf(x, y, s = 1, { arms = [-20, 20], mood = 'smile', flip = false, holding = '' } = {}) {
  const body = `
    <ellipse cx="0" cy="2" rx="55" ry="9" fill="#000" opacity=".12"/>
    <rect x="-24" y="-48" width="16" height="44" rx="7" fill="${C.skin}"/><rect x="8" y="-48" width="16" height="44" rx="7" fill="${C.skin}"/>
    <ellipse cx="-17" cy="-3" rx="16" ry="7" fill="#8a5a33"/><ellipse cx="17" cy="-3" rx="16" ry="7" fill="#8a5a33"/>
    ${arm(-26, -118, arms[0], 58, C.thobe, 20, C.skin)}
    <path d="M-30 -130 Q 0 -138 30 -130 L 46 -38 Q 0 -30 -46 -38 Z" fill="${C.thobe}" stroke="${C.thobeLine}" stroke-width="3"/>
    <path d="M0 -130 V -95" stroke="${C.thobeLine}" stroke-width="3"/>
    ${arm(26, -118, arms[1], 58, C.thobe, 20, C.skin)}
    ${holding}
    <circle cx="0" cy="-178" r="54" fill="${C.skin}"/>
    <circle cx="-54" cy="-174" r="11" fill="${C.skinShade}"/><circle cx="54" cy="-174" r="11" fill="${C.skinShade}"/>
    <path d="M-54 -186 Q -58 -240 0 -238 Q 58 -240 54 -186 Q 40 -206 18 -204 Q 30 -222 6 -214 Q -20 -228 -24 -208 Q -44 -210 -54 -186 Z" fill="${C.hair}"/>
    ${face(0, -172, 54, mood)}`;
  return g(x, y, s, body, flip);
}

// Giant: feet at (0,0), ~640 units tall at s=1.
function giant(x, y, s = 1, { arms = [-15, 15], mood = 'smile', thorn = false, flip = false, tear = false, holding = '' } = {}) {
  const brows = {
    angry: `<path d="M-62 -548 L-18 -532 M62 -548 L18 -532" stroke="${C.beard}" stroke-width="14" stroke-linecap="round"/>`,
    sad: `<path d="M-62 -532 L-18 -550 M62 -532 L18 -550" stroke="${C.beard}" stroke-width="14" stroke-linecap="round"/>`,
    surprised: `<path d="M-62 -560 Q -40 -575 -18 -560 M62 -560 Q 40 -575 18 -560" stroke="${C.beard}" stroke-width="14" fill="none" stroke-linecap="round"/>`,
  }[mood] || `<path d="M-62 -552 Q -40 -562 -18 -552 M62 -552 Q 40 -562 18 -552" stroke="${C.beard}" stroke-width="14" fill="none" stroke-linecap="round"/>`;
  const fm = mood === 'angry' ? 'brave' : mood === 'sad' ? 'worried' : mood;
  const body = `
    <ellipse cx="0" cy="4" rx="190" ry="22" fill="#000" opacity=".15"/>
    <rect x="-95" y="-190" width="70" height="185" rx="30" fill="${C.giantSkin}"/><rect x="25" y="-190" width="70" height="185" rx="30" fill="${C.giantSkin}"/>
    <ellipse cx="-62" cy="-8" rx="62" ry="24" fill="#7a4a2a"/><ellipse cx="62" cy="-8" rx="62" ry="24" fill="#7a4a2a"/>
    ${thorn ? `<path d="M40 -20 L95 -120 L80 -14 Z" fill="#5a4636"/><path d="M48 -24 L88 -100" stroke="#7d6450" stroke-width="5"/>` : ''}
    ${arm(-115, -400, arms[0], 210, C.giantSkin, 60, C.giantShade)}
    <path d="M-120 -430 Q 0 -460 120 -430 L 150 -170 Q 0 -150 -150 -170 Z" fill="${C.giantTunic}"/>
    <rect x="-140" y="-250" width="280" height="30" fill="${C.giantTunicDark}"/><rect x="-22" y="-256" width="44" height="42" rx="6" fill="#e1b84b"/>
    ${arm(115, -400, arms[1], 210, C.giantSkin, 60, C.giantShade)}
    ${holding}
    <circle cx="0" cy="-520" r="100" fill="${C.giantSkin}"/>
    <ellipse cx="-100" cy="-515" rx="20" ry="28" fill="${C.giantShade}"/><ellipse cx="100" cy="-515" rx="20" ry="28" fill="${C.giantShade}"/>
    <path d="M-92 -500 Q -100 -380 0 -370 Q 100 -380 92 -500 Q 60 -450 0 -455 Q -60 -450 -92 -500 Z" fill="${C.beard}"/>
    <path d="M-95 -560 Q -90 -630 0 -628 Q 90 -630 95 -560 Q 50 -600 0 -598 Q -50 -600 -95 -560 Z" fill="${C.beard}"/>
    <ellipse cx="0" cy="-510" rx="18" ry="22" fill="${C.giantShade}"/>
    ${face(0, -520, 100, fm)}${brows}
    ${tear ? '<path d="M-40 -500 q-10 25 0 35 q10 -10 0 -35 Z" fill="#7fd0f2"/>' : ''}`;
  return g(x, y, s, body, flip);
}

function mom(x, y, s = 1, { arms = [-15, 15], mood = 'smile', flip = false } = {}) {
  return g(x, y, s, `<ellipse cx="0" cy="2" rx="60" ry="9" fill="#000" opacity=".12"/>
    ${arm(-30, -230, arms[0], 85, C.abaya, 24, C.skin)}
    <path d="M-38 -250 Q 0 -262 38 -250 L 64 0 H -64 Z" fill="${C.abaya}"/>
    ${arm(30, -230, arms[1], 85, C.abaya, 24, C.skin)}
    <circle cx="0" cy="-300" r="54" fill="${C.abaya}"/><ellipse cx="0" cy="-292" rx="38" ry="42" fill="${C.skin}"/>
    ${face(0, -292, 40, mood)}`, flip);
}

function grandpa(x, y, s = 1, { mood = 'smile', flip = false, arms = [-15, 30] } = {}) {
  return g(x, y, s, `<ellipse cx="0" cy="2" rx="60" ry="9" fill="#000" opacity=".12"/>
    <path d="M66 0 L 70 -170" stroke="#7b5230" stroke-width="9" stroke-linecap="round"/>
    ${arm(-32, -235, arms[0], 85, C.thobe, 24, C.skin)}
    <path d="M-40 -255 Q 0 -265 40 -255 L 60 0 H -60 Z" fill="${C.thobe}" stroke="${C.thobeLine}" stroke-width="3"/>
    ${arm(32, -235, arms[1], 85, C.thobe, 24, C.skin)}
    <circle cx="0" cy="-300" r="46" fill="${C.skin}"/>
    <path d="M-40 -285 Q -40 -220 0 -215 Q 40 -220 40 -285 Q 20 -265 0 -268 Q -20 -265 -40 -285 Z" fill="#e8e8e8"/>
    <path d="M-62 -310 Q 0 -390 62 -310 L 72 -220 L 40 -290 Q 0 -300 -40 -290 L -72 -220 Z" fill="#fff"/>
    <path d="M-62 -310 Q 0 -390 62 -310 L 72 -220 L 40 -290 Q 0 -300 -40 -290 L -72 -220 Z" fill="none" stroke="${C.red}" stroke-width="5" stroke-dasharray="10 8"/>
    <ellipse cx="0" cy="-338" rx="56" ry="10" fill="#222"/>
    ${face(0, -298, 42, mood)}`, flip);
}

function villager(x, y, s = 1, { col = '#ffffff', mood = 'smile', flip = false, kid = false, arms = [-15, 15] } = {}) {
  if (kid) return g(x, y, s, `<rect x="-14" y="-40" width="12" height="38" rx="5" fill="${C.skin}"/><rect x="2" y="-40" width="12" height="38" rx="5" fill="${C.skin}"/>
    ${arm(-20, -100, arms[0], 45, col, 16, C.skin)}<path d="M-24 -110 L 24 -110 L 36 -34 H -36 Z" fill="${col}"/>${arm(20, -100, arms[1], 45, col, 16, C.skin)}
    <circle cx="0" cy="-145" r="42" fill="${C.skin}"/><path d="M-42 -150 Q -40 -195 0 -192 Q 40 -195 42 -150 Q 0 -170 -42 -150 Z" fill="#2d1b10"/>
    ${face(0, -140, 42, mood)}`, flip);
  return g(x, y, s, `${arm(-32, -235, arms[0], 85, col, 24, C.skin)}
    <path d="M-40 -255 Q 0 -265 40 -255 L 60 0 H -60 Z" fill="${col}" stroke="${C.thobeLine}" stroke-width="3"/>
    ${arm(32, -235, arms[1], 85, col, 24, C.skin)}
    <circle cx="0" cy="-300" r="46" fill="${C.skin}"/>
    <path d="M-62 -310 Q 0 -390 62 -310 L 66 -230 L 40 -290 Q 0 -300 -40 -290 L -66 -230 Z" fill="#fff"/>
    <ellipse cx="0" cy="-338" rx="56" ry="10" fill="#222"/>${face(0, -298, 42, mood)}`, flip);
}

const svg = (inner) => `<svg viewBox="0 0 1000 760" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMax slice">${inner}</svg>`;

module.exports = { C, g, sky, sun, moon, stars, cloud, ground, bigMountain, farHills, palm, house, rock, stream, sheep, falcon,
  basket, dallah, finjan, yusuf, giant, mom, grandpa, villager, svg };
