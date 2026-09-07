# CSC Chan's Chall

- **CTF:** SunCTF 2026
- **Category:** Forensics
- **Difficulty:** Medium
---

### Description
> I managed to find CSC Chan's design files! I wonder what easter eggs are hidden in it...
> File provided: cici.psd

---

### Initial Reconnaissance & Analysis
When approaching this challenge, the first step was to understand the provided file. It's a standard Adobe Photoshop Document (.psd). 
My initial thought process was:
+ PSD files are essentially archives of image layers, metadata, and resources.
+ Flags are often hidden in invisible layers, in the file metadata (EXIF/XMP), or appended to the end of the file

First, I checked the basic file headers. String extraction (strings cici.psd) yielded no obvious flags. I then attempted to use the Python psd-tools library to extract the layers. However, the tool crashed due to corrupted or malformed layer names containing embedded null characters (\x00)
To bypass this anti-forensics trick, I wrote a custom parser script, analyze_psd.py, to safely read the binary structure of the file and list out the layers without crashing
Running python analyze_psd.py identified 11 layers in total, noting that 7 of them were marked with a hidden visibility flag

---

### Exploitation & Solution
Since standard extraction tools failed, I wrote a second script, decode_layers.py, to manually parse the PackBits (RLE) compressed layer data from the binary and reconstruct each layer into a .png file
After running python decode_layers.py, I reviewed the extracted layers. Paint Layer 8 (layer_01_Paint_Layer_8.png) stood out. It appeared completely blank (white), but a pixel analysis revealed something suspicious:
+ RGB values were entirely 255, 255, 255 (pure white)
+ The Alpha channel, however, had varying values ranging from 25 to 201
This is a classic "white-on-white" steganography trick. The author drew with a semi-transparent white brush on a white canvas. It is completely invisible to the naked eye
To reveal the text, I wrote a final script, reveal_flag.py, which composites the extracted white-on-white layer onto a solid black background using the Python Imaging Library (PIL)
Viewing the resulting flag_revealed.png image revealed the handwritten flag

---

### Flag
sunctf26{how_cici_was_born}

---

### Key Takeaways
+ White-on-White Steganography: Data can be hidden in plain sight by using colors that match the background but differ in their alpha (transparency) channels
+ Tool Evasion: The author cleverly broke standard PSD parsing tools by introducing null bytes into the layer names, forcing the solver to understand the underlying file format and parse it manually
+ Forensics Methodology: Always check hidden layers and verify the alpha channels of seemingly blank images during forensics analysis. Custom scripting is often required when standard tools fail

---

### Read
+ 

