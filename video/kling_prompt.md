# Oncoal — Kling video brief (single file)

Vertical 9:16 · 1080x1920 · total ~44 s · cinematic, warm, golden-hour Yemeni mood
Song: "هذا أونكول" — festive Yemeni (Sanaani wedding style) male chorus, oud + mirwas drum + hand claps, ~92 BPM

---

## 1) MASTER PROMPT (paste this first / use as the global style)

Cinematic vertical commercial for "Oncoal", a Yemeni restaurant specializing in mandi cooked over coal. Warm golden-hour color grade, rich amber and deep brown tones, soft film grain, shallow depth of field, slow elegant camera moves (dolly-in, gentle orbit, slow push), floating embers and rising steam, festive and welcoming mood. The film travels across Yemen — the tower houses of Old Sana'a, the mud-brick skyscrapers of Shibam in Hadramout, and the mountains and sea of Aden — then arrives at the restaurant: glowing coals, mandi rice platters, tender lamb, roasted chicken, families sharing food together. Photorealistic, 4K, high detail, appetizing food cinematography.

**Negative prompt:** text, letters, subtitles, watermark, logo distortion, deformed hands, extra fingers, blurry food, cartoon, anime, oversaturated, low quality, cold blue tones

> ⚠️ Do not ask Kling to write Arabic text or the logo — it garbles it. Add captions, prices and the logo afterwards in CapCut / the editor.

---

## 2) SHOT LIST (generate each shot separately, 5 s each, then join)

Use **Image-to-Video** with the dish images in `video/assets/hd/` where noted.

| # | Time | Lyric (sung) | Kling prompt (English) | Reference image |
|---|---|---|---|---|
| 1 | 0:00–0:05 | (intro — oud + drum) | Slow aerial drone shot over Old Sana'a at sunrise, traditional brown tower houses with white gypsum window decorations, golden morning light, birds flying, camera glides forward. Then an ornate carved wooden Yemeni door slowly opens with warm light pouring through. | `assets/city/sanaa1.jpg` |
| 2 | 0:05–0:08 | بعدوو بعدوو | Epic aerial shot of Shibam, Hadramout — ancient mud-brick skyscrapers rising from the desert valley, palm trees in the foreground, golden sunset light, camera pushes forward slowly. | `assets/city/shibam.jpg` |
| 3 | 0:08–0:11 | بعدوو من طريقنا | Aden, Yemen: white minarets in Crater district against dramatic volcanic mountains, then a quick pan to the Arabian Sea with waves crashing on rocks at sunset, Sira fortress on the hill. | `assets/city/aden.jpg` |
| 4 | 0:11–0:14 | هذا أونكول هذا أونكول | Close-up of glowing red coals in a traditional underground mandi oven (taboon), sparks and embers flying upward in slow motion, smoke swirling, dark warm background (space left in center for the logo). | — |
| 5 | 0:14–0:16 | أحلى مندي عندنا | Whole roasted chicken mandi on a large round platter of fragrant yellow rice, steam rising, camera slowly orbits the plate, warm restaurant lighting. | `assets/hd/full_mandi.png` |
| 6 | 0:16–0:21 | أفضل لحوم لحومنا ×2 | Tender slow-cooked lamb mandi on spiced rice, a hand pulls the meat apart and it falls off the bone, juicy, steam rising, macro food shot, slow push-in. | `assets/hd/lamb.png`, `assets/hd/mazbi.png` |
| 7 | 0:21–0:26 | ما حد ينافس طبخنا ×2 | Chef lowers meat into the coal oven, smoke rises; then a mixed platter of chicken and lamb on rice is placed on the table, followed by crispy golden fried chicken (broasted) with fries. | `assets/hd/mix.png`, `assets/hd/broasted.png` |
| 8 | 0:26–0:31 | وكل الزباين أهلنا ×2 | A happy Yemeni family sitting together around a large shared platter in a warm restaurant, laughing and eating, then a whole roasted fish with lemon on rice. | `assets/hd/fish.png` |
| 9 | 0:31–0:36 | مرحبا بكم لعندنا ×2 | Adeni milk tea poured from high into a small glass, steam; then massoub (banana bread with honey) and mutabaq on the table; a Yemeni dallah coffee pot and dates — hospitality. | `assets/hd/massoub.png`, `assets/hd/mutabaq.png` |
| 10 | 0:36–0:39 | هذا أونكول هذا أونكول | Fast top-down montage of many dishes on a dark wooden table, one plate slides in on each beat, steam and embers. | all `assets/hd/*.png` |
| 11 | 0:39–0:44 | بعدوو عن طريقنا | Restaurant entrance at night with warm golden light, door opens welcomingly, embers float in the air, camera slowly pulls back (space for logo + "ORDER NOW"). | — |

---

## 3) LYRICS (for the song / lip-sync / captions)

```
بعدوو بعدوو
بعدوو من طريقنا
هذا اونكول هذا اونكول
احلى مندي عندنا
افضل لحوم لحومنا
افضل لحوم لحومنا
ماحد ينافس طبخنا
ماحد ينافس طبخنا
وكل الزباين اهلنا
وكل الزباين اهلنا
مرحبا بكم لعندنا
مرحبا بكم لعندنا
هذا اونكول هذا اونكول
بعدوو عن طريقنا
```

**Music prompt (if generating the song):** Yemeni traditional folk song, festive Sanaani wedding style, male lead singer with group chorus answering (call and response), Arabic Yemeni dialect, oud, mirwas hand drum, darbuka, hand claps, 92 BPM, joyful and celebratory, ends with a final drum hit and zaghrouta.
*(A finished track with these exact lyrics is already in the repo: `video/assets/song/oncoal_song.mp3` — upload it as the audio.)*

---

## 4) ON-SCREEN TEXT (add in the editor after Kling)

| Shot | Text |
|---|---|
| 1 | صنعاء · من اليمن… إلى سفرتك |
| 2 | حضرموت · شبام |
| 3 | عدن |
| 4 | ONCOAL أونكول · Yemeni Kitchen · Cooked over Coal |
| 5 | Full Chicken Mandi $39.99 |
| 6 | Lamb Mandi $24.99 · 100% Zabihah Halal |
| 7 | Mix $22.99 · Broasted 4 pcs $16.99 |
| 8 | Fish $44.99 · أونكول… بيتك الثاني |
| 9 | حياكم الله · Massoub $12.99 |
| 11 | ONCOAL · A taste of Yemen · ORDER NOW اطلب الآن · Daily 12 PM – Close |

Lyric captions: bottom of the screen, gold Arabic font, each word lights up as it is sung.

**Photo credits (city photos, Wikimedia Commons):** Sana'a — Rod Waddington (CC BY-SA 2.0), Ayah Alakwaa (CC BY-SA 4.0); Shibam — Ala Askool (CC BY-SA 4.0); Aden — Jialiang Gao (CC BY-SA 3.0).
