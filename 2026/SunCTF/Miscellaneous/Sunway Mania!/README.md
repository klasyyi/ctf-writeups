# Sunway Mania! 
+ Event: Sunway CTF 2026
+ Category: Misc
+ Difficulty: Medium

---

### Challenge Description
> Sunway OSU! Mania Championship is coming soon! Do you have what it takes to qualify? Note: this is a Misc challenge, you do not need to pentest my website.

A website at https://sunwaymania.site simulates an osu! Mania championship qualifier portal. Players must submit a valid .osr (osu! replay) file and a matching username to "qualify" and unlock the competitors page where the flag is stored.

---

### Initial Reconnaissance & Analysis
First Look at the Site
The site has:
+ A submission form at POST /qualify accepting username + .osr file
+ A download link at /download/qualifier-beatmap for the official .osz beatmap
+ A /competitors page locked behind qualification

Validation rules visible in the HTML:
+ Game mode must be osu!mania
+ Beatmap must match the official qualifier
+ Username must match the replay owner and exist in osu! records
+ Top 50 leaderboard identities are protected
+ Replay must achieve 100.00% accuracy
+ Auto mod is not accepted

it's about understanding the osu! replay (.osr) binary format and crafting a valid fake replay
The .osz beatmap file is a ZIP archive containing .osu difficulty files. The .osr format identifies a beatmap by the MD5 hash of the .osu file, and score data is stored in plain binary fields

Bash
+ cp Sunway-Mania-2026-Qualifier.osz Sunway-Mania-2026-Qualifier.zip
+ certutil -hashfile "t+pazolite - Electric Sister Bitch (Verniy_Chan) [ADVANCED Lv.12].osu" MD5
+ (Get-Content file.osu | Select-String "^[0-9]").Count
+ curl -X POST https://sunwaymania.site/qualify ...

Files found in the .osz
osz_extracted/
├── BG.jpg
├── Greget.wav
├── SB/
│   ├── 75cd961f68b36757006a483128c93383.jpg
│   ├── jitter.jpg
│   └── whait.jpg  (+ others)
├── t+pazolite - Electric Sister Bitch (Verniy_Chan) [ADVANCED Lv.12].osu  ← QUALIFIER
├── t+pazolite - Electric Sister Bitch (Verniy_Chan) [BASIC Lv.6].osu
├── t+pazolite - Electric Sister Bitch (Verniy_Chan) [NOVICE Lv.8].osu
├── t+pazolite - Electric Sister Bitch (Verniy_Chan) [Rido's INFINITE Lv.16].osu
├── t+pazolite - Electric Sister Bitch (Verniy_Chan) [Rinzler's EXHAUST Lv.14].osu
├── t+pazolite - Electric Sister Bitch (Verniy_Chan).osb
└── t+pazolite - Electric Sister Bitch.mp3

Key values extracted from [ADVANCED Lv.12].osu:
BeatmapID:     694150
BeatmapSetID:  310607
Mode:          3  (osu!mania)
CircleSize:    4  (4K)
Hit objects:   888
MD5 hash:      956400d129308e59d887f6b631a78510

### Exploitation & Solution
