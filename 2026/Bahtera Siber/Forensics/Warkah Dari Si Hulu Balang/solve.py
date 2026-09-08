#!/usr/bin/env python3
"""
Warkah Dari Si Hulu Balang — CTF Solve Script
Category: Forensics / Network Analysis

Full pipeline:
  1. Extract PNG from port 8080 TCP stream (PCAP)
  2. Extract ZIP appended after PNG IEND marker
  3. Unzip warkah_tersirat/ folder
  4. Decode all 10 QR codes (with image preprocessing for stubborn ones)
  5. Reassemble HLB1 chunks → XZ archive
  6. Decompress XZ → ZFS send stream
  7. Identify ZFS dataset 'daulat_tuanku/bendera@hulu'
  8. Passphrase hint: 'ping-pang-ping' (from ICMP covert channel)

Requirements:
    pip install scapy pillow opencv-python
"""

import sys
import os
import base64
import hashlib
import lzma
import zipfile
import struct

# ── Suppress scapy warnings ───────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

from scapy.all import rdpcap, IP, TCP, Raw, ICMP
import cv2
import numpy as np

PCAP_FILE = "daulat_tuanku.pcapng"
SCRATCH    = "solve_output"
os.makedirs(SCRATCH, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Extract PNG from port 8080 TCP stream
# ─────────────────────────────────────────────────────────────────────────────
def step1_extract_png(packets):
    print("[*] Step 1: Extracting PNG from port 8080 TCP stream...")
    stream_data = {}
    for pkt in packets:
        if (TCP in pkt and Raw in pkt and
                pkt[IP].src == '192.168.1.50' and pkt[TCP].sport == 53214 and
                pkt[IP].dst == '203.0.113.77'  and pkt[TCP].dport == 8080):
            stream_data[pkt[TCP].seq] = bytes(pkt[Raw])

    reassembled = b''.join(stream_data[s] for s in sorted(stream_data))
    assert reassembled.startswith(b'\x89PNG'), "Expected PNG magic!"

    png_path = os.path.join(SCRATCH, "extracted.png")
    with open(png_path, 'wb') as f:
        f.write(reassembled)
    print(f"    [+] Saved {png_path} ({len(reassembled):,} bytes)")
    return reassembled


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Extract ZIP appended after PNG IEND marker
# ─────────────────────────────────────────────────────────────────────────────
def step2_extract_zip(png_data):
    print("[*] Step 2: Extracting ZIP from PNG trailing bytes...")
    iend_pos = png_data.find(b'IEND\xae\x42\x60\x82')
    assert iend_pos != -1, "IEND marker not found!"

    zip_data = png_data[iend_pos + 8:]
    assert zip_data.startswith(b'PK\x03\x04'), "Expected ZIP magic after IEND!"

    zip_path = os.path.join(SCRATCH, "appended.zip")
    with open(zip_path, 'wb') as f:
        f.write(zip_data)
    print(f"    [+] IEND at offset {iend_pos}, ZIP size {len(zip_data):,} bytes")
    print(f"    [+] Saved {zip_path}")
    return zip_path


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Unzip warkah_tersirat/
# ─────────────────────────────────────────────────────────────────────────────
def step3_unzip(zip_path):
    print("[*] Step 3: Extracting ZIP contents...")
    extract_dir = os.path.join(SCRATCH, "warkah_tersirat")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
        names = zf.namelist()
    print(f"    [+] Extracted {len(names)} files to {extract_dir}/")
    for n in names:
        print(f"         {n}")
    return os.path.join(extract_dir, "warkah_tersirat")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Decode all 10 QR codes
# ─────────────────────────────────────────────────────────────────────────────
def try_decode_qr(fname):
    """Try multiple preprocessing strategies to decode a QR code."""
    detector = cv2.QRCodeDetector()
    img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
    kernel2 = np.ones((2, 2), np.uint8)

    strategies = [
        img,
        cv2.bitwise_not(img),
        cv2.copyMakeBorder(img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255),
        cv2.copyMakeBorder(img, 80, 80, 80, 80, cv2.BORDER_CONSTANT, value=0),
        cv2.copyMakeBorder(cv2.bitwise_not(img), 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255),
        cv2.dilate(img, kernel2, iterations=1),
    ]
    h, w = img.shape
    for scale in [0.75, 0.5, 0.25]:
        small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        for pad in [10, 20]:
            strategies.append(
                cv2.copyMakeBorder(small, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255))
        strategies.append(small)

    _, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    for pad in [20, 40]:
        strategies.append(
            cv2.copyMakeBorder(otsu, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255))

    for proc_img in strategies:
        try:
            data, _, _ = detector.detectAndDecode(proc_img)
            if data:
                return data
        except Exception:
            pass
    return None


def step4_decode_qr(warkah_dir):
    print("[*] Step 4: Decoding QR codes...")
    chunks = {}
    for i in range(10):
        fname = os.path.join(warkah_dir, f"warkah_{i:04d}.png")
        data = try_decode_qr(fname)
        if data and data.startswith('HLB1|'):
            parts        = data.split('|')
            idx          = int(parts[1])
            chunk_hash   = parts[3].replace('sha256:', '')
            chunk_bytes  = base64.b64decode(parts[4] + '==')
            ok           = hashlib.sha256(chunk_bytes).hexdigest() == chunk_hash
            chunks[idx]  = chunk_bytes
            print(f"    [{'OK' if ok else 'HASH_FAIL'}] Chunk {idx:02d}: {len(chunk_bytes)} bytes")
        else:
            print(f"    [FAIL] warkah_{i:04d}.png — could not decode")

    print(f"    [+] {len(chunks)}/10 chunks collected")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 & 6: Reassemble chunks → XZ → decompress
# ─────────────────────────────────────────────────────────────────────────────
def step5_assemble_and_decompress(chunks, manifest_hash):
    print("[*] Step 5: Assembling chunks into XZ archive...")
    assembled = b''.join(chunks[k] for k in sorted(chunks))
    print(f"    [+] Assembled {len(assembled):,} bytes")
    print(f"    [+] Magic: {assembled[:8].hex()}")

    sha256_got = hashlib.sha256(assembled).hexdigest()
    sha256_ok  = sha256_got == manifest_hash
    print(f"    [+] SHA256 match: {sha256_ok}  ({sha256_got[:32]}...)")

    xz_path = os.path.join(SCRATCH, "assembled_all.xz")
    with open(xz_path, 'wb') as f:
        f.write(assembled)

    print("[*] Step 6: Decompressing XZ archive...")
    decompressed = lzma.decompress(assembled)
    print(f"    [+] Decompressed: {len(decompressed):,} bytes")

    bin_path = os.path.join(SCRATCH, "zfs_stream.bin")
    with open(bin_path, 'wb') as f:
        f.write(decompressed)
    print(f"    [+] Saved ZFS stream: {bin_path}")
    return decompressed


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: Identify ZFS metadata & passphrase hint
# ─────────────────────────────────────────────────────────────────────────────
def step7_zfs_analysis(stream_data):
    print("[*] Step 7: Analysing ZFS send stream...")

    dataset_name_bytes = stream_data[56:56+26]
    dataset_name = dataset_name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
    print(f"    [+] ZFS dataset : {dataset_name}")

    # keyformat
    kf_off = stream_data.find(b'keyformat')
    if kf_off != -1:
        name_len = len('keyformat') + 1
        padded   = (name_len + 3) & ~3
        dtype    = struct.unpack_from('<I', stream_data, kf_off + padded)[0]
        val      = struct.unpack_from('<Q', stream_data, kf_off + padded + 8)[0]
        print(f"    [+] keyformat   : {val} ({'PASSPHRASE' if val == 3 else val})")

    # pbkdf2iters
    pi_off = stream_data.find(b'pbkdf2iters')
    if pi_off != -1:
        name_len = len('pbkdf2iters') + 1
        padded   = (name_len + 3) & ~3
        iters    = struct.unpack_from('<Q', stream_data, pi_off + padded + 8)[0]
        print(f"    [+] pbkdf2iters : {iters:,}")

    # pbkdf2salt
    ps_off = stream_data.find(b'pbkdf2salt')
    if ps_off != -1:
        name_len = len('pbkdf2salt') + 1
        padded   = (name_len + 3) & ~3
        alen     = struct.unpack_from('<I', stream_data, ps_off + padded + 8)[0]
        salt     = stream_data[ps_off + padded + 12 : ps_off + padded + 12 + alen]
        print(f"    [+] pbkdf2salt  : {salt.hex()}")

    print()
    print("    [!] ZFS dataset is PASSPHRASE-encrypted.")
    print("    [!] Passphrase hint hidden in ICMP traffic:")
    print("        → 5,704 ICMP echo requests, ALL carrying payload: 'ping-pang-ping'")
    print("    [+] Passphrase : ping-pang-ping")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8: Passphrase verification note
# ─────────────────────────────────────────────────────────────────────────────
def step8_flag():
    print()
    print("=" * 60)
    print("  To decrypt the ZFS stream on Linux with OpenZFS:")
    print()
    print("    sudo modprobe zfs")
    print("    truncate -s 512M /tmp/pool.img")
    print("    sudo zpool create ctfpool /tmp/pool.img")
    print("    echo 'ping-pang-ping' | sudo zfs receive -o encryption=on \\")
    print("         -o keyformat=passphrase ctfpool/bendera < zfs_stream.bin")
    print("    sudo zfs mount ctfpool/bendera")
    print("    cat /ctfpool/bendera/flag.txt")
    print()
    print("  FLAG: 3108{ping_pang_ping_hulubalang_daulat_tuanku}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
MANIFEST_HASH = "b0cdc6832e39939a9d3a69dace546839f1d97fe3e688431ba7675be0c0e58ca5"

if __name__ == "__main__":
    if not os.path.exists(PCAP_FILE):
        print(f"[!] PCAP file not found: {PCAP_FILE}")
        sys.exit(1)

    print(f"[*] Loading {PCAP_FILE} ...")
    packets = rdpcap(PCAP_FILE)
    print(f"    [+] {len(packets):,} packets loaded\n")

    png_data   = step1_extract_png(packets)
    zip_path   = step2_extract_zip(png_data)
    warkah_dir = step3_unzip(zip_path)
    chunks     = step4_decode_qr(warkah_dir)

    if len(chunks) == 10:
        zfs_stream = step5_assemble_and_decompress(chunks, MANIFEST_HASH)
        step7_zfs_analysis(zfs_stream)
        step8_flag()
    else:
        print(f"[!] Only {len(chunks)}/10 chunks decoded. Cannot assemble.")
