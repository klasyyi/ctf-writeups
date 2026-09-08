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

---

### Exploitation & Solution
Username Constraint
The server checks the username against the osu! API:
+ Must be a real osu! account
+ Must NOT be a top-50 ranked mania player (shown on leaderboard: zeroxdd, Kuroya, Lunaris)
Solution: use Verniy_Chan — the beatmap creator. They have a real osu! account and are not top-50 in mania.

Attempting zeroxdd (rank 1) returns:
+ Submission rejected — Impersonation is strictly prohibited. 
+ Top 50 leaderboard usernames cannot be used.

Exploit Script - forge_replay.ps1

Bash
+ curl -c cookies.txt https://sunwaymania.site/ -o page.html
+ CSRF=$(grep -oP 'name="csrf_token" value="\K[^"]+' page.html)
+ curl -X POST https://sunwaymania.site/qualify \
  -b cookies.txt -c cookies.txt \
  -F "csrf_token=$CSRF" \
  -F "username=Verniy_Chan" \
  -F "replay=@qualifier_replay.osr;type=application/octet-stream" \
  -H "Referer: https://sunwaymania.site/" \
  -H "Origin: https://sunwaymania.site"
+ curl -b cookies.txt https://sunwaymania.site/competitors

---

### Flag
sunctf26{y0u_4r3_4n_0SU_pl4y3r!}

---

### Key takeaaways
+ The .osr format is not cryptographically signed. Any client can craft a valid-looking replay without actually playing the game
+ .osz files are just renamed ZIPs. Always try to inspect "opaque" file formats by renaming/extracting
+ osu! trusts the MD5 of the .osu file for beatmap matching — knowing this is key to forging a replay for a specific map
+ The server only checks if the username exists in the osu! API and isn't top-50. it doesn't verify actual ownership
