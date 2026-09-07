# CSC Chan's Chall

- **CTF:** SunCTF 2026
- **Category:** Forensics
- **Difficulty:** Medium
---

### Description
> I managed to find CSC Chan's design files! I wonder what easter eggs are hidden in it...
> File provided: cici.psd

---

### Solution
When approaching this challenge, the first step was to understand the provided file. It's a standard Adobe Photoshop Document (.psd). My initial thought process was:
+ PSD files are essentially archives of image layers, metadata, and resources.
+ Flags are often hidden in invisible layers, in the file metadata (EXIF/XMP), or appended to the end of the file

First, I wrote a quick Python script to parse the file header and extract strings:
+ python -c "
with open('cici.psd', 'rb') as f:
    data = f.read(26)
    print(data[:4]) # Magic bytes: 8BPS
"
strings cici.psd | grep -i "sunctf"

String extraction yielded no obvious flags. I then attempted to use the Python psd-tools library to extract the layers. However, the tool crashed due to corrupted or malformed layer names containing embedded null characters (\x00). This indicated that standard tools might fail and I needed to analyze the layers more directly.

---

### Exploitation


---

### Flag


---

### Key Takeaways
+ 

---

### Read
+ 

