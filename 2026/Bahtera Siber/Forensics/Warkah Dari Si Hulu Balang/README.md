# Warkah Dari Si Hulu Balang

- **Event:** Bahtera Siber 2026
- **Category:** Forensics
- **Difficulty:** Hard

---

## 1. Challenge Description

> Tersingkap riak di lautan bayang yang sarat berkocak, tatkala hamba menitipkan telinga menelusuri bisikan si Hulubalang; di celah serakan debu yang berterbangan, tersembunyi cebisan warkah yang dicantas dan peti berazimat yang menanti demi menzahirkan panji keramat yang sekian lama berhijab.

*(Translation: Ripples surface in the shadow-laden sea, as the servant lends an ear to follow the Hulubalang's whisper; among the scattered dust, hidden are fragments of a torn letter and an enchanted chest awaiting to reveal the sacred banner long veiled.)*

The challenge provides a single packet capture file: `daulat_tuanku.pcapng`. The Malay riddle hints at:
- **"cebisan warkah yang dicantas"** → *torn/fragmented letter* (data split across packets)
- **"peti berazimat"** → *enchanted chest* (encrypted/hidden archive)
- **"panji keramat"** → *sacred banner* = the flag

---

## 2. Initial Reconnaissance & Analysis

Loading the PCAP and running a quick overview reveals 120,004 packets with a rich mix of protocols.

**Key hosts identified:**

| IP | Role |
|----|------|
| `192.168.1.50` | Internal victim/exfiltration host |
| `203.0.113.77` | Attacker's external server |
| `192.168.1.1` → `192.168.1.19` | Various LAN hosts (noise) |

**Protocol distribution:**

| Protocol | Packets |
|----------|---------|
| TCP / HTTP (port 80) | 88,812 / 85,290 |
| UDP / DNS | 18,624 / 12,664 |
| ARP | 6,864 |
| ICMP | 5,704 |
| NTP / DHCP | 1,983 / 1,744 |
| HTTP (port 8080) | 3,522 |

**Anomalies immediately spotted:**

1. **ICMP (5,704 pkts)** — all echo requests carry the identical payload `ping-pang-ping`
2. **Port 8080 (3,522 pkts)** — a single TCP stream between `192.168.1.50:53214` → `203.0.113.77:8080`
3. **HTTP port 80 (85,290 pkts)** — all requests are `GET / HTTP/1.1` to common hosts (noise)

---

## 3. Exploitation & Solution

### Step 1 — Extract the PNG from Port 8080 Stream

Reassembling the TCP stream on port 8080 (sorted by sequence number) yields **2,460,116 bytes** starting with `\x89PNG` — a valid PNG header. We extract it directly:

```python
# From extract.py
stream_data = {}
for pkt in packets:
    if (TCP in pkt and Raw in pkt and
        pkt[IP].src == '192.168.1.50' and pkt[TCP].sport == 53214 and
        pkt[IP].dst == '203.0.113.77' and pkt[TCP].dport == 8080):
        stream_data[pkt[TCP].seq] = bytes(pkt[Raw])

reassembled = b''.join(stream_data[s] for s in sorted(stream_data))
# → saves extracted.png (2,460,116 bytes)
```

### Step 2 — PNG Polyglot: ZIP Appended After IEND

Scanning the extracted PNG for the IEND chunk (`\x49\x45\x4e\x44\xae\x42\x60\x82`) reveals **41,727 bytes of data after the image ends**, starting with `PK\x03\x04` — a ZIP archive!

```
PNG IEND at offset 2,418,381
Appended ZIP at offset 2,418,389  →  41,727 bytes
ZIP magic: 504b0304...
```

This is the **"peti berazimat"** (enchanted chest) — a ZIP archive hidden inside the PNG's trailing bytes.

```python
# From inspect_zip_png.py
iend_pos = png_data.find(b'IEND\xae\x42\x60\x82')
appended = png_data[iend_pos + 8:]  # Everything after IEND
# → appended starts with PK\x03\x04 ✓
```

### Step 3 — Extract ZIP Contents

Opening the ZIP reveals 10 PNG files and a manifest inside the folder `warkah_tersirat/` (*"hidden letter"*):

```
warkah_tersirat/
├── manifest.txt          (149 bytes)
├── warkah_0000.png       (4,141 bytes)
├── warkah_0001.png       (4,147 bytes)
├── ...
└── warkah_0009.png       (4,111 bytes)
```

`manifest.txt` reveals the encoding scheme:

```
sha256=b0cdc6832e39939a9d3a69dace546839f1d97fe3e688431ba7675be0c0e58ca5
chunks=10
chunk_size=986
format=HLB1|index|total|sha256(chunk)|base64(chunk)
```

Each PNG is a **QR code** encoding one chunk of the original data in the format `HLB1|index|total|sha256|base64data`.

### Step 4 — Decode All 10 QR Codes

The QR codes are 1064×1064 pixels (1-bit grayscale). Standard decoders fail on several because they **lack a quiet zone** (white border). We apply image preprocessing strategies (padding, scaling, dilation) to recover all 10:

| Image | Issue | Fix |
|-------|-------|-----|
| `warkah_0000.png` | No quiet zone | Add 20px white border |
| `warkah_0001.png` | Too large | Scale to 75% + 10px pad |
| `warkah_0002.png` | Different margin | Add 80px black border |
| `warkah_0003–0005.png` | — | Decoded directly |
| `warkah_0006.png` | Too large | Scale to 75% + 10px pad |
| `warkah_0007.png` | — | Decoded directly |
| `warkah_0008.png` | Too large | Scale to 75% + 10px pad |
| `warkah_0009.png` | Noisy | Morphological dilation |

Each decoded QR string follows the format:
```
HLB1|0003|0010|sha256:f43f4e8b...|+J8e42PZxTVlZ5lWHXUCJHQdkt5qxjwh+...
```

See `solve.py` for the full decoding pipeline using OpenCV's `QRCodeDetector`.

### Step 5 — Reassemble Chunks → XZ Archive

Base64-decoding and concatenating all 10 chunks (each 986 bytes, last 978 bytes) in index order yields **9,852 bytes** starting with the XZ magic bytes `\xfd\x37\x7a\x58\x5a\x00`:

```python
assembled = b''.join(chunks[k] for k in sorted(chunks))
# First 8 bytes: fd377a585a000004  →  XZ format ✓

# SHA256 verification:
hashlib.sha256(assembled).hexdigest()
# → b0cdc6832e39939a9d3a69dace546839f1d97fe3e688431ba7675be0c0e58ca5  ✓  (matches manifest)
```

Decompressing the XZ archive yields **19,132 bytes**.

### Step 6 — ZFS Encrypted Send Stream

Running `file` on the decompressed binary confirms the final layer:

```
decompressed_final.bin: ZFS snapshot (little-endian machine), version 218628113,
type: ZFS, name: 'daulat_tuanku/bendera@hulu'
```

The dataset name `daulat_tuanku/bendera@hulu` is critical:
- `bendera` = **"flag"** in Malay ← this is the flag file!
- `@hulu` = ZFS snapshot name

Parsing the embedded nvlist metadata reveals the encryption parameters:

```
keyformat  : 3  (PASSPHRASE)
pbkdf2iters: 350,000
DSL_CRYPTO_MASTER_KEY_1 : <wrapped key bytes>
DSL_CRYPTO_IV / DSL_CRYPTO_MAC : <auth data>
```

### Step 7 — Passphrase from ICMP Covert Channel

Revisiting the ICMP anomaly: **5,704 packets all carrying the payload `ping-pang-ping`**. This repeated, unusual string — embedded in every single ICMP echo request across the capture — is the passphrase hint left by the challenge author.

Passphrase: **`ping-pang-ping`**

Using ZFS receive on Linux with the passphrase decrypts the stream and yields the flag from the `bendera` dataset.

---

## 4. Flag

```
3108{ping_pang_ping_hulubalang_daulat_tuanku}
```

---

## 5. Files Included

| File | Description |
|------|-------------|
| `README.md` | This writeup |
| `solve.py` | Full end-to-end solve script |
| `manifest.txt` | Extracted manifest from ZIP |

> **Note:** `daulat_tuanku.pcapng` (14.5 MB) is not included in this repo due to file size. Obtain it from the challenge platform.

---

## 6. Attack Chain Summary

```
daulat_tuanku.pcapng
 └─ TCP stream port 8080
     └─ extracted.png  (2.46 MB PNG)
         └─ [After IEND] appended.zip  (41 KB)
             └─ warkah_tersirat/
                 ├─ manifest.txt       ← chunk format & SHA256
                 └─ warkah_0000–0009.png  ← 10× QR codes
                     └─ HLB1 chunks (base64)
                         └─ assembled_all.xz  (9,852 bytes)
                             └─ decompressed_final.bin  (ZFS send stream)
                                 └─ daulat_tuanku/bendera@hulu
                                     └─ passphrase: ping-pang-ping (from ICMP)
                                         └─ FLAG 🏴
```

---

## 7. Key Takeaways

- **PNG Polyglot / Appended Data:** ZIP archives can be hidden after a PNG's `IEND` marker and remain invisible to image viewers while still being a valid ZIP. Always run `binwalk` or manually check for trailing data past the `IEND` chunk.
- **QR Codes as Data Carriers:** The challenge split a binary payload into 10 QR codes using a custom chunking scheme (`HLB1` format). When standard QR decoders fail, preprocessing (scaling, padding quiet zones, morphological operations) recovers the data.
- **ZFS as a Steganographic Container:** Using a ZFS encrypted send stream as the final layer is highly unconventional. The `file` command is essential — it identifies the format from the binary structure and NVList metadata.
- **ICMP Covert Channel Identification:** The repeated `ping-pang-ping` payload across 5,704 ICMP packets is not just noise — it is the passphrase key for the final decryption stage.
- **Multi-Layer Forensics:** Never stop at the first artifact. Each layer peels back to reveal the next: PCAP → PNG → ZIP → QR codes → XZ → ZFS → flag.
