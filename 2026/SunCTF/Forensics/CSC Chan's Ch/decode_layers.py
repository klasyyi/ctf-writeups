import struct
import os
from PIL import Image

def decode_packbits(data, out_len):
    """Decodes PackBits RLE compression commonly used in PSD files."""
    out = bytearray()
    i = 0
    while i < len(data) and len(out) < out_len:
        header = data[i]
        i += 1
        if header == 128:
            continue
        elif header <= 127:
            # Literal run
            count = header + 1
            out.extend(data[i:i+count])
            i += count
        else:
            # Repeat run
            count = 257 - header
            out.extend([data[i]] * count)
            i += 1
    return bytes(out[:out_len])

def extract_layers(filename):
    print(f"[*] Extracting layers from {filename}...")
    with open(filename, 'rb') as f:
        raw = f.read()

    offset = 26
    color_mode_len = struct.unpack_from('>I', raw, offset)[0]
    offset += 4 + color_mode_len
    img_res_len = struct.unpack_from('>I', raw, offset)[0]
    offset += 4 + img_res_len

    offset += 4 # Skip layer mask len
    offset += 4 # Skip layer info len

    layer_count = abs(struct.unpack_from('>h', raw, offset)[0])
    offset += 2

    layers = []
    pos = offset
    for i in range(layer_count):
        top, left, bottom, right = struct.unpack_from('>iiii', raw, pos)
        ch_count = struct.unpack_from('>H', raw, pos+16)[0]
        pos += 18

        channels = []
        for c in range(ch_count):
            ch_id, ch_len = struct.unpack_from('>hI', raw, pos)
            channels.append({'id': ch_id, 'len': ch_len})
            pos += 6

        flags = raw[pos+10]
        pos += 12

        extra_len = struct.unpack_from('>I', raw, pos)[0]
        extra_start = pos + 4

        mask_len = struct.unpack_from('>I', raw, extra_start)[0]
        br_offset = extra_start + 4 + mask_len
        br_len = struct.unpack_from('>I', raw, br_offset)[0]
        name_off = br_offset + 4 + br_len
        name_len_b = raw[name_off]
        layer_name = raw[name_off+1:name_off+1+name_len_b].decode('latin-1').rstrip('\x00')

        layers.append({
            'name': layer_name,
            'width': right - left, 'height': bottom - top,
            'channels': channels
        })
        pos = extra_start + extra_len

    os.makedirs('extracted_layers', exist_ok=True)
    
    # Extract channel image data
    channel_data_start = pos
    pos = channel_data_start
    
    for i, layer in enumerate(layers):
        w, h = layer['width'], layer['height']
        ch_pixels = {}
        
        for ch in layer['channels']:
            ch_id = ch['id']
            ch_data_len = ch['len']
            ch_data = raw[pos:pos+ch_data_len]
            pos += ch_data_len

            if w == 0 or h == 0:
                continue

            compression = struct.unpack_from('>H', ch_data, 0)[0]

            if compression == 1: # PackBits RLE
                row_counts = []
                rc_offset = 2
                for r in range(h):
                    row_counts.append(struct.unpack_from('>H', ch_data, rc_offset)[0])
                    rc_offset += 2
                    
                pixels = bytearray()
                rd_pos = rc_offset
                for r in range(h):
                    row_compressed = ch_data[rd_pos:rd_pos+row_counts[r]]
                    pixels.extend(decode_packbits(row_compressed, w))
                    rd_pos += row_counts[r]
                ch_pixels[ch_id] = bytes(pixels)
            else:
                ch_pixels[ch_id] = b'\x00' * (w*h)

        if w > 0 and h > 0:
            r_data = ch_pixels.get(0, b'\x00'*(w*h))
            g_data = ch_pixels.get(1, b'\x00'*(w*h))
            b_data = ch_pixels.get(2, b'\x00'*(w*h))
            a_data = ch_pixels.get(-1, b'\xff'*(w*h))

            rgba = bytearray(w * h * 4)
            for px in range(w * h):
                rgba[px*4]   = r_data[px]
                rgba[px*4+1] = g_data[px]
                rgba[px*4+2] = b_data[px]
                rgba[px*4+3] = a_data[px]
                
            img = Image.frombytes('RGBA', (w, h), bytes(rgba))
            safe_name = layer["name"].replace(" ", "_")
            out_name = f'extracted_layers/layer_{i:02d}_{safe_name}.png'
            img.save(out_name)
            print(f"[+] Saved {out_name}")

if __name__ == "__main__":
    extract_layers('cici.psd')
