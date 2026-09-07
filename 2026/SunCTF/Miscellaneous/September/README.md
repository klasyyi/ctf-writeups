### September
+ Event: SunCTF 2026
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
import mido
mid = mido.MidiFile('September.mid')
print([track.name for track in mid.tracks])
