// Builds the KDP interior PDF, the front-cover PNG and the full-wrap cover PDF for "يوسف والعملاق".
// Usage: node build.js   (from the book/ directory)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const A = require('./art');
const { sky, sun, moon, stars, cloud, ground, bigMountain, farHills, palm, house, rock, stream, sheep, falcon,
  basket, dallah, finjan, yusuf, giant, mom, grandpa, villager, svg, g } = A;


// Real illustrations: drop images/scene-01.png ... scene-20.png and images/cover.png (png/jpg/webp).
// Any missing image falls back to the simple SVG drawing.
const IMG_DIR = path.resolve(__dirname, 'images');
function img(name) {
  for (const ext of ['png', 'jpg', 'jpeg', 'webp']) {
    const f = path.join(IMG_DIR, `${name}.${ext}`);
    if (fs.existsSync(f)) return `<img src="file://${f}" style="width:100%;height:100%;object-fit:cover;display:block">`;
  }
  return null;
}
const FONTS = path.resolve(__dirname, '../../video/fonts');
const OUT = path.resolve(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });

const TITLE = 'يوسف والعملاق';
const AUTHOR = 'تأليف: ________';   // اكتب اسم المؤلف هنا قبل النشر

// KDP paperback: 8.5" x 8.5" trim, with bleed -> 8.625" x 8.75"
const PW = 8.625, PH = 8.75;

const village = (dry = false) =>
  farHills(560) + house(170, 600, 0.9) + house(380, 610, 0.75) + palm(560, 620, 0.9, dry) + palm(90, 640, 0.8, dry);

// ---------- story: [illustration, text] ----------
const STORY = [
  [svg(sky('day') + sun(840, 120) + cloud(250, 120) + village() + ground(600) + palm(900, 680, 1.1) +
      yusuf(640, 690, 1.25, { arms: [-150, 160], mood: 'happy' })),
   'في قريةٍ صغيرةٍ بينَ النخيلِ والجبال، كانَ يعيشُ ولدٌ صغيرٌ اسمُه <b>يوسف</b>.<br>كانَ يوسفُ يحبُّ أن يلعبَ ويضحكَ، ويسألَ عن كلِّ شيء!'],

  [svg(sky('dawn') + bigMountain(620, 900, 560, 640) + g(640, 70, 1, '') + ground(640) +
      giant(640, 150, 0.22, { mood: 'angry' }) +
      '<text x="380" y="210" font-family="Cairo" font-weight="900" font-size="64" fill="#7a3d1e" transform="rotate(-8 380 210)">بُووم!</text>' +
      '<text x="800" y="260" font-family="Cairo" font-weight="900" font-size="54" fill="#7a3d1e" transform="rotate(8 800 260)">بُووم!</text>' +
      house(120, 700, 0.6) + villager(260, 720, 0.55, { mood: 'surprised', arms: [-160, 160] })),
   'وفي أعلى الجبلِ الكبير، كانَ يعيشُ <b>عملاقٌ ضخم</b>.<br>كانَ أهلُ القريةِ يسمعونَ صوتَه: بُووم... بُووم...<br>فيخافونَ ويُغلقونَ أبوابَهم.'],

  [svg(sky('hot') + sun(820, 130, 85, '#ffb703') + farHills(560) + house(200, 600, 0.8) + palm(470, 630, 0.9, true) + palm(880, 640, 0.95, true) +
      ground(600, '#ebc27c', '#d9a35c') +
      '<path d="M560 680 Q 640 650 720 680 Q 640 700 560 680 Z" fill="#c69a5a"/><path d="M590 676 l20 -8 M650 668 l10 12 M690 674 l-14 8" stroke="#9c7440" stroke-width="4"/>' +
      sheep(300, 700, 0.9, true) + sheep(150, 720, 0.7, true)),
   'وفي صيفٍ حارّ، <b>جفَّت عينُ الماء</b> التي يشربُ منها أهلُ القرية.<br>ذبلت النخلات، وعطشت الأغنام، وحزنَ الجميع.'],

  [svg(sky('hot') + sun(860, 110, 60, '#ffb703') + bigMountain(760, 600, 420, 600) + ground(600, '#ebc27c', '#d9a35c') +
      grandpa(330, 690, 1.15, { mood: 'worried', arms: [-15, 150] }) + villager(150, 700, 1, { col: '#efe6d6', mood: 'worried', flip: true }) +
      villager(520, 700, 0.9, { col: '#dfe8f0', mood: 'worried' })),
   'قالَ الجدُّ سالم وهو يُشيرُ إلى الجبل:<br>«الماءُ يأتي من الجبل... لكن مَن يجرؤُ أن يصعدَ إلى العملاق؟»'],

  [svg(sky('day') + farHills(560) + ground(600) + palm(900, 660, 1) +
      villager(200, 700, 1, { mood: 'happy' }) + villager(780, 700, 1, { col: '#efe6d6', mood: 'happy', flip: true }) +
      grandpa(640, 700, 0.95, { mood: 'surprised' }) + yusuf(440, 700, 1.15, { arms: [-20, 175], mood: 'brave' })),
   'رفعَ يوسفُ يدَه الصغيرةَ وقال: <b>«أنا أذهب!»</b><br>ضحكَ الناسُ وقالوا: «أنتَ صغيرٌ جدًّا يا يوسف!»'],

  [svg(sky('day') + house(820, 640, 1.3) + ground(620) + palm(110, 680, 1) +
      mom(520, 700, 1.2, { arms: [-20, -95], mood: 'smile' }) +
      yusuf(330, 710, 1.1, { arms: [-25, 75], mood: 'smile', holding: basket(95, -78, 0.9) })),
   'قالت أمُّه: «خُذ معكَ تمرًا وماءً، وتذكّر يا بُنيّ:<br><b>الكلمةُ الطيّبةُ تفتحُ القلوب</b>.»<br>قبّلَ يوسفُ رأسَ أمِّه وانطلق.'],

  [svg(sky('day') + cloud(200, 110) + falcon(640, 150, 0.9) +
      '<path d="M0 760 L 0 520 L 300 430 L 560 470 L 1000 260 L 1000 760 Z" fill="#c9875a"/>' +
      '<path d="M0 760 L 0 600 L 400 520 L 700 600 L 1000 420 L 1000 760 Z" fill="#a96c45" opacity=".5"/>' +
      rock(170, 560, 0.6) + rock(820, 420, 0.5) +
      yusuf(520, 545, 1.05, { arms: [-40, 150], mood: 'brave', holding: '' })),
   'صعدَ يوسفُ الجبلَ خطوةً خطوة.<br>مرَّ بصخورٍ كبيرة، ورأى صقرًا يُحلِّقُ فوقَه،<br>فقالَ بشجاعة: «لن أخاف!»'],

  [svg(sky('day') + '<path d="M0 760 V 610 Q 500 560 1000 610 V 760 Z" fill="#c9875a"/>' +
      giant(640, 720, 1.05, { mood: 'angry', arms: [-30, 30] }) +
      yusuf(190, 730, 0.75, { arms: [-60, 60], mood: 'surprised' }) +
      '<text x="330" y="200" font-family="Cairo" font-weight="900" font-size="80" fill="#7a3d1e" transform="rotate(-10 330 200)">بُووم!</text>'),
   'وفجأة... <b>بُووم! بُووم!</b><br>اهتزّت الأرض، وظهرَ العملاق!<br>كانَ طويلًا كالنخلة، وعيناهُ كبيرتانِ كالقمر.'],

  [svg(sky('day') + '<path d="M0 760 V 610 Q 500 560 1000 610 V 760 Z" fill="#c9875a"/>' +
      giant(720, 760, 1.05, { mood: 'angry' }) +
      yusuf(300, 720, 1.05, { arms: [-20, 165], mood: 'smile' })),
   'ارتجفت رُكبتا يوسف، لكنّه قالَ بصوتٍ واضح:<br><b>«السلامُ عليكم يا عمّي العملاق!»</b>'],

  [svg(sky('day') + '<path d="M0 760 V 610 Q 500 560 1000 610 V 760 Z" fill="#c9875a"/>' +
      giant(700, 760, 1.05, { mood: 'surprised', arms: [-20, -60] }) +
      yusuf(280, 720, 1.05, { arms: [-20, 20], mood: 'smile' })),
   'توقّفَ العملاقُ ونظرَ إليه مُستغربًا:<br>«وعليكمُ السلام... <b>لم يُسلِّم عليَّ أحدٌ منذُ سنين!</b><br>الجميعُ يهربُ منّي.»'],

  [svg(sky('day') + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      giant(560, 750, 1.0, { mood: 'sad', tear: true, thorn: true, arms: [-10, 10] }) +
      yusuf(200, 740, 1.0, { arms: [-20, 110], mood: 'worried' })),
   'رأى يوسفُ دمعةً كبيرةً في عينِ العملاق،<br>ورأى <b>شوكةً ضخمةً</b> في قدمِه.<br>فقالَ بلُطف: «هل قدمُكَ تؤلمُك؟»'],

  [svg(sky('day') + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      giant(600, 750, 1.0, { mood: 'sad', thorn: true, arms: [-60, 40] }) +
      yusuf(220, 740, 1.0, { arms: [-20, 20], mood: 'worried' }) +
      '<text x="800" y="470" font-family="Cairo" font-weight="900" font-size="56" fill="#7a3d1e" transform="rotate(8 800 470)">بُووم!</text>'),
   'قالَ العملاق: «نعم، ولهذا أضربُ الأرضَ بقدمي: بُووم بُووم...<br><b>ولم يُساعدني أحد.</b>»'],

  [svg(sky('day') + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      g(0, 0, 1, '') + giant(380, 760, 1.0, { mood: 'surprised', arms: [-30, 30] }) +
      yusuf(720, 740, 1.0, { arms: [-110, -70], mood: 'brave', flip: false }) +
      '<path d="M645 640 L 465 705" stroke="#5a4636" stroke-width="14" stroke-linecap="round"/>' +
      '<text x="760" y="300" font-family="Cairo" font-weight="900" font-size="60" fill="#7a3d1e">هِيييه!</text>'),
   'قالَ يوسف: «سأساعدُك!»<br>أمسكَ الشوكةَ بكلتا يديه، وشدَّ... وشدَّ... وشدَّ...<br><b>حتى خرجت!</b>'],

  [svg(sky('day') + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      giant(620, 760, 1.0, { mood: 'happy', arms: [-150, -100] }) +
      yusuf(250, 740, 1.0, { arms: [-20, 150], mood: 'happy' }) + basket(380, 740, 1.2) +
      '<text x="120" y="200" font-family="Cairo" font-weight="900" font-size="64" fill="#7a3d1e">هاهاها!</text>'),
   'ضحكَ العملاقُ ضحكةً عالية: <b>«هاهاها! شكرًا يا صديقي الصغير!»</b><br>وجلسا معًا يأكلانِ التمرَ الحُلو.'],

  [svg(sky('day') + farHills(600) + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      rock(760, 680, 1.2) + '<path d="M690 520 Q 700 480 720 470" stroke="#5bb8e0" stroke-width="12" fill="none" stroke-linecap="round"/>' +
      giant(360, 760, 0.95, { mood: 'surprised', arms: [-20, 80] }) +
      yusuf(120, 740, 0.85, { arms: [-20, 100], mood: 'worried' })),
   'قالَ يوسف: «قريتُنا عطشى، والماءُ لا يصلُ إلينا.»<br>نظرَ العملاقُ وقال: «آه! <b>صخرةٌ كبيرةٌ سدّت مجرى الماء</b><br>حينَ كنتُ أضربُ الأرضَ بقدمي!»'],

  [svg(sky('day') + farHills(600) + '<path d="M0 760 V 640 Q 500 600 1000 640 V 760 Z" fill="#c9875a"/>' +
      stream('M760 700 Q 700 720 600 730 T 300 760 T 0 760', 60) +
      giant(560, 750, 0.8, { mood: 'happy', arms: [170, 190], holding: rock(0, -650, 0.9) }) +
      yusuf(200, 720, 0.85, { arms: [-160, 160], mood: 'happy' })),
   'رفعَ العملاقُ الصخرةَ بيدَيه كأنّها حبّةُ تمر!<br><b>فانطلقَ الماءُ يجري ويلمعُ</b> نحوَ القرية.'],

  [svg(sky('sunset') + sun(150, 160, 70, '#ffcf5a') + village() + ground(620) +
      giant(720, 740, 0.95, { mood: 'happy', arms: [-20, 150], holding: yusuf(110, -430, 0.6, { arms: [-160, 170], mood: 'happy' }) }) +
      villager(330, 730, 0.75, { mood: 'surprised', arms: [-160, 160] })),
   'حملَ العملاقُ يوسفَ على كتفِه ونزلا معًا.<br>خافَ الناسُ أوّلًا...<br>ثمّ رأوا يوسفَ <b>يُلوِّحُ لهم ويضحك!</b>'],

  [svg(sky('day') + sun(850, 120) + farHills(560) + palm(120, 640, 1) + palm(880, 650, 1.05) + ground(600, '#d8e8a0', '#bcd682') +
      stream('M1000 650 Q 800 690 600 680 T 200 700 T 0 690', 70) +
      villager(260, 740, 1, { kid: true, mood: 'happy', col: '#ffd166', arms: [-160, 160] }) +
      villager(440, 750, 1, { kid: true, mood: 'happy', col: '#ef8fb0', arms: [-150, 150] }) +
      yusuf(620, 750, 0.95, { arms: [-160, 160], mood: 'happy' }) +
      grandpa(800, 740, 0.9, { mood: 'happy' }) + sheep(130, 760, 0.7)),
   'شربَ أهلُ القرية، واخضرّت النخيل، ورقصَ الأطفالُ حولَ الماء.<br>وقالَ الجدُّ سالم: <b>«الشجاعةُ لا تُقاسُ بالطول!»</b>'],

  [svg(sky('sunset') + farHills(560) + house(150, 620, 0.9) + palm(900, 640, 1) + ground(610) +
      giant(560, 760, 0.85, { mood: 'happy', arms: [-20, 120], holding: finjan(0, 0, 0) }) +
      finjan(760, 395, 2.2) + dallah(420, 740, 1.4) +
      yusuf(250, 740, 0.85, { arms: [-20, 110], mood: 'happy', holding: finjan(80, -110, 0.7) }) +
      grandpa(90, 760, 0.8, { mood: 'happy' })),
   'ومنذُ ذلكَ اليوم، صارَ العملاقُ صديقَ القرية،<br>يزورُهم كلَّ جمعة، ويشربُ معهم القهوة...<br><b>في فنجانٍ كبيرٍ جدًّا!</b>'],

  [svg(sky('night') + stars(40) + moon(800, 140) + farHills(580).replace('#dca877', '#2c3a68') +
      '<rect x="0" y="560" width="1000" height="200" fill="#26325a"/>' +
      '<rect x="280" y="380" width="440" height="240" rx="30" fill="#3d4a7a"/>' +
      '<rect x="300" y="470" width="400" height="120" rx="30" fill="#f4f1ea"/>' +
      '<rect x="300" y="440" width="120" height="70" rx="30" fill="#ffffff"/>' +
      g(370, 470, 1, `<circle cx="0" cy="0" r="54" fill="${A.C.skin}"/><path d="M-54 -8 Q -58 -62 0 -60 Q 58 -62 54 -8 Q 30 -30 0 -28 Q -30 -30 -54 -8 Z" fill="${A.C.hair}"/>`) +
      `<path d="M340 475 q12 10 24 0 M380 475 q12 10 24 0" stroke="#2b1a10" stroke-width="4" fill="none"/><path d="M360 500 q10 8 20 0" stroke="#3a2a20" stroke-width="4" fill="none"/>` +
      '<path d="M330 500 H 700 V 590 H 330 Z" fill="#5fa8d3"/>' +
      '<text x="460" y="420" font-family="Cairo" font-size="44" fill="#fff6d5">z z z</text>'),
   'وكانَ يوسفُ ينامُ كلَّ ليلةٍ وهو يبتسم،<br>لأنّه عرفَ أنَّ <b>الكلمةَ الطيّبةَ والقلبَ الشجاع</b><br>يصنعانِ العجائب.'],
];

// ---------- page templates ----------
const css = `
@font-face { font-family: Cairo; src: url('file://${FONTS}/Cairo.ttf'); font-weight: 200 1000; }
@font-face { font-family: Ruqaa; src: url('file://${FONTS}/Ruqaa.ttf'); }
@page { size: ${PW}in ${PH}in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; }
body { font-family: Cairo, sans-serif; direction: rtl; color: #3a2a20; }
.page { width: ${PW}in; height: ${PH}in; position: relative; overflow: hidden; page-break-after: always; background: #fff8ec; }
.art { position: absolute; inset: 0 0 auto 0; height: 6.05in; }
.art svg { width: 100%; height: 100%; display: block; }
.text { position: absolute; left: 0; right: 0; bottom: 0; height: 2.7in; padding: 0.38in 0.75in 0.75in; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; font-size: 19.5pt; line-height: 1.7; font-weight: 600;
  background: #fff8ec; border-top: 6px solid #f0b24a; }
.text b { color: #b5501e; font-weight: 800; }
.num { position: absolute; bottom: 0.42in; font-size: 11pt; color: #b89a78; font-weight: 700; }
.even .num { left: 0.62in; } .odd .num { right: 0.62in; }
.center { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 0.9in; }
.t-title { font-family: Ruqaa; font-size: 66pt; color: #b5501e; line-height: 1.2; }
.t-sub { font-size: 18pt; margin-top: 0.15in; color: #6b4a2e; }
.small { font-size: 11pt; line-height: 1.9; color: #6b5a4a; font-weight: 500; }
.q { font-size: 17pt; line-height: 2.1; text-align: right; font-weight: 600; }
`;

const pageNum = (n) => `<div class="num">${n.toLocaleString('ar-EG')}</div>`;
const pages = [];

// 1: title page
pages.push(`<div class="page center">
  <div style="width:3.6in;height:2.9in">${svg(sky('day') + sun(820, 130) + bigMountain(650, 800, 420, 640) + ground(640) +
    giant(700, 740, 0.85, { mood: 'happy', arms: [-20, 150] }) + yusuf(300, 740, 1.1, { arms: [-20, 165], mood: 'happy' }))}</div>
  <div class="t-title" style="margin-top:.35in">${TITLE}</div>
  <div class="t-sub">${AUTHOR}</div></div>`);
// 2: copyright / dedication
pages.push(`<div class="page center"><div style="font-size:22pt;font-weight:800;color:#b5501e;margin-bottom:.3in">إهداء</div>
  <div style="font-size:17pt;line-height:1.9">إلى يوسف...<br>صغيرٌ في طولِه، كبيرٌ في قلبِه.</div>
  <div class="small" style="position:absolute;bottom:.9in;left:.9in;right:.9in">${TITLE}<br>${AUTHOR}<br>
  جميع الحقوق محفوظة © ${new Date().getFullYear()}<br>لا يجوز نسخ أو إعادة نشر أي جزء من هذا الكتاب دون إذن خطي من المؤلف.</div></div>`);

STORY.forEach(([svgArt, text], i) => {
  const art = img(`scene-${String(i + 1).padStart(2, '0')}`) || svgArt;
  const n = pages.length + 1;
  pages.push(`<div class="page ${n % 2 ? 'odd' : 'even'}"><div class="art">${art}</div><div class="text"><p>${text}</p></div>${pageNum(n)}</div>`);
});

// the end
pages.push(`<div class="page center">${''}<div style="width:3.4in;height:2.6in">${svg(sky('sunset') + sun(500, 420, 110, '#ffcf5a') + farHills(560) + ground(600) +
  giant(650, 740, 0.85, { mood: 'happy', arms: [-20, 150] }) + yusuf(330, 740, 1.05, { arms: [-20, 160], mood: 'happy' }))}</div>
  <div class="t-title" style="font-size:58pt;margin-top:.3in">النهاية</div></div>`);
// questions page
pages.push(`<div class="page center"><div style="font-size:24pt;font-weight:800;color:#b5501e;margin-bottom:.35in">لنتحدّث عن القصة</div>
  <div class="q">١. لماذا كانَ العملاقُ يضربُ الأرضَ بقدمِه؟<br>٢. ماذا أعطت الأمُّ يوسفَ قبلَ أن يذهب؟<br>٣. ماذا قالَ يوسفُ أوّلَ ما رأى العملاق؟<br>
  ٤. كيفَ رجعَ الماءُ إلى القرية؟<br>٥. ماذا تعلّمتَ من يوسف؟</div></div>`);
// pad to an even count (KDP needs >= 24 pages, even)
while (pages.length < 24 || pages.length % 2) pages.push('<div class="page"></div>');

const interiorHtml = `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>${css}</style></head><body>${pages.join('\n')}</body></html>`;
fs.writeFileSync(path.join(OUT, 'interior.html'), interiorHtml);

// ---------- cover ----------
const PAGES = pages.length;
const SPINE = +(PAGES * 0.002347).toFixed(4);   // premium color paper, inches per page
const CW = 0.125 + 8.5 + SPINE + 8.5 + 0.125, CH = 8.75;
const frontArt = img('cover') || svg(sky('day') + sun(830, 120, 70) + cloud(220, 110) + bigMountain(640, 900, 560, 640) + palm(90, 700, 1.1) + ground(640) +
  giant(660, 760, 0.85, { mood: 'happy', arms: [-20, 160] }) + yusuf(330, 750, 1.15, { arms: [-20, 170], mood: 'happy' }));
const frontInner = `<div style="position:absolute;inset:0">${frontArt}</div>
  <div style="position:absolute;top:.55in;left:0;right:0;text-align:center">
    <div style="font-family:Ruqaa;font-size:82pt;color:#fff;line-height:1.15;text-shadow:0 4px 0 #b5501e,0 8px 18px rgba(0,0,0,.35)">${TITLE}</div></div>
  <div style="position:absolute;bottom:.5in;left:0;right:0;text-align:center;font-size:18pt;font-weight:700;color:#fff;text-shadow:0 2px 6px rgba(0,0,0,.5)">${AUTHOR}</div>`;
const coverCss = `@font-face { font-family: Cairo; src: url('file://${FONTS}/Cairo.ttf'); font-weight: 200 1000; }
@font-face { font-family: Ruqaa; src: url('file://${FONTS}/Ruqaa.ttf'); }
svg { width:100%; height:100%; display:block } * { margin:0; padding:0; box-sizing:border-box; } body { font-family: Cairo; direction: rtl; }`;
const frontHtml = `<!doctype html><html><head><meta charset="utf-8"><style>${coverCss}
  @page { size: 8.5in 8.5in; margin:0 } .f{width:8.5in;height:8.5in;position:relative;overflow:hidden}</style></head>
  <body><div class="f">${frontInner}</div></body></html>`;
// Arabic books open right-to-left, so on the flat wrap the FRONT is on the LEFT: [front | spine | back].
const backInner = `<div style="position:absolute;inset:0;background:linear-gradient(#8fd3f4,#fff8ec)"></div>
  <div style="position:absolute;top:1.1in;left:.8in;right:.8in;text-align:center;font-size:17pt;line-height:1.9;font-weight:600;color:#3a2a20">
  <div style="font-size:24pt;font-weight:800;color:#b5501e;margin-bottom:.2in">عملاقٌ يُخيفُ القرية... وولدٌ صغيرٌ شجاع!</div>
  حينَ جفَّ الماءُ في القرية، لم يجرؤ أحدٌ على صعودِ الجبلِ إلى العملاق.<br>
  إلا يوسف! بقلبٍ شجاعٍ وكلمةٍ طيّبة، يكتشفُ يوسفُ سرَّ العملاق،<br>ويُعيدُ الماءَ إلى قريتِه.<br>
  <span style="color:#b5501e">قصةٌ عن الشجاعة، واللُّطف، ومساعدةِ الآخرين.</span></div>
  <div style="position:absolute;bottom:.25in;right:.25in;width:2.2in;height:1.4in;background:#fff;border-radius:6px"></div>`;
const coverHtml = `<!doctype html><html><head><meta charset="utf-8"><style>${coverCss}
  @page { size: ${CW}in ${CH}in; margin:0 } .w{width:${CW}in;height:${CH}in;position:relative;overflow:hidden;display:flex;direction:ltr}
  .side{width:${8.5 + 0.125}in;height:100%;position:relative;overflow:hidden;direction:rtl} .spine{width:${SPINE}in;background:#f0b24a}</style></head>
  <body><div class="w"><div class="side" style="padding:0">${frontInner.replace('top:.55in', 'top:.68in').replace('bottom:.5in', 'bottom:.62in')}</div>
  <div class="spine"></div><div class="side">${backInner.replace('right:.25in;width', 'left:.4in;width')}</div></div></body></html>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(interiorHtml, { waitUntil: 'load' }); await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(OUT, 'yusuf-interior.pdf'), width: `${PW}in`, height: `${PH}in`, printBackground: true, preferCSSPageSize: true });

  await page.setContent(coverHtml, { waitUntil: 'load' }); await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(OUT, 'yusuf-cover-wrap.pdf'), width: `${CW}in`, height: `${CH}in`, printBackground: true, preferCSSPageSize: true });

  const shot = await browser.newPage({ viewport: { width: 816, height: 816 }, deviceScaleFactor: 3.125 }); // 2550 px = 8.5in @ 300dpi
  await shot.setContent(frontHtml, { waitUntil: 'load' }); await shot.evaluate(() => document.fonts.ready);
  await shot.screenshot({ path: path.join(OUT, 'yusuf-front-cover.png') });

  // preview contact sheet of all pages
  const prev = await browser.newPage({ viewport: { width: 828, height: 840 } });
  await prev.setContent(interiorHtml, { waitUntil: 'load' }); await prev.evaluate(() => document.fonts.ready);
  const els = await prev.$$('.page');
  for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: path.join(OUT, `p${String(i + 1).padStart(2, '0')}.png`) });
  await browser.close();
  console.log('pages:', PAGES, 'spine(in):', SPINE, 'cover:', CW.toFixed(3), 'x', CH);
})();
