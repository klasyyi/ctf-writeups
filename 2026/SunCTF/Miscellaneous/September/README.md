### September
+ CTF: SunCTF 2026
+ Category: Misc
+ Difficulty: Medium

---

### Challenge Description
> Something seems off with my MIDI...
File: September.mid

---

### Initial Reconnaissance & Analysis
The challenge provides a MIDI file and a hint emphasizing the word "off". This typically points to steganography hidden within MIDI Note Off events.
Initial analysis utilized the Python mido library to parse the file and check for common MIDI hiding techniques:
+ Explicit Note Off release velocities.
+ Orphaned Note Off events (turning off notes that were never turned on).
+ Least Significant Bit (LSB) manipulation in velocity bytes.
When these standard vectors came up empty, dumping the structural track list revealed 17 distinct tracks. The final track in the sequence was named 'TUBA'. Because the MIDI is a recreation of Earth, Wind & Fire's "September"—a funk song that does not use a tuba—this track was the definitive anomaly

Bash
+ import mido
mid = mido.MidiFile('September.mid')
print([track.name for track in mid.tracks])

---

### Exploitation & Solution
Examining the raw delta times (the number of ticks between events) of the TUBA track exposed a binary pattern. The TUBA track played a single note repetitively, varying only the physical duration of the notes and the gaps between them.
This timing structure perfectly mapped to Morse Code:
+ Short Note (~192 ticks): Dot (.)
+ Long Note (~384 ticks): Dash (-)
+ Massive Gap (1536 ticks): Word Space
Mapping the raw output translated the track into two distinct Morse code words. The first block of notes translated to -... .-. .- -.-. - ..-. ..--- -.... (SUNCTF26). After the 1536-tick word space, the second block translated to -... .- -.. . . -.-- .-. .-. (BADEEYAA)

---

### Flag
sunctf26{badeeyaa}

---

### Key Takeaways
This challenge demonstrated Delta Time Steganography within MIDI files. By manipulating the literal tick duration of notes and the silences between them, data can be encoded rhythmically. Because MIDI sequencers and synthesizers process these minute timing differences natively without throwing errors, this vector remains practically invisible to listeners and standard audio analysis tools.

### Read
+ https://ccrma.stanford.edu/~craig/14q/midifile/MidiFileFormat.html
+ https://img2sound.com/articles/audio-steganography-cheatsheet/
