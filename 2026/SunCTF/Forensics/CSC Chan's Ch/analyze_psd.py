import struct

def analyze_psd(filename):
    print(f"[*] Analyzing {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()

    # 1. Header Section
    magic = data[:4]
    if magic != b'8BPS':
        print("[-] Invalid PSD file")
        return
    print(f"[+] Magic bytes match: {magic.decode()}")
    
    offset = 26  # Skip header

    # 2. Color Mode Data Section
    color_mode_len = struct.unpack_from('>I', data, offset)[0]
    offset += 4 + color_mode_len

    # 3. Image Resources Section
    img_res_len = struct.unpack_from('>I', data, offset)[0]
    offset += 4 + img_res_len

    # 4. Layer and Mask Info Section
    layer_mask_len = struct.unpack_from('>I', data, offset)[0]
    layer_info_start = offset + 4
    
    layer_info_len = struct.unpack_from('>I', data, layer_info_start)[0]
    layer_count_raw = struct.unpack_from('>h', data, layer_info_start + 4)[0]
    layer_count = abs(layer_count_raw)
    
    print(f"[+] Found {layer_count} layers")

    # 5. Parse Layer Records
    pos = layer_info_start + 6
    for i in range(layer_count):
        top = struct.unpack_from('>i', data, pos)[0]
        left = struct.unpack_from('>i', data, pos+4)[0]
        bottom = struct.unpack_from('>i', data, pos+8)[0]
        right = struct.unpack_from('>i', data, pos+12)[0]
        channel_count = struct.unpack_from('>H', data, pos+16)[0]
        pos += 18
        
        # Skip channels
        for c in range(channel_count):
            pos += 6
            
        # Blend mode and flags
        flags = data[pos+10]
        pos += 12 
        
        extra_len = struct.unpack_from('>I', data, pos)[0]
        extra_start = pos + 4
        
        # Parse Layer Name
        mask_len = struct.unpack_from('>I', data, extra_start)[0]
        br_offset = extra_start + 4 + mask_len
        br_len = struct.unpack_from('>I', data, br_offset)[0]
        name_offset = br_offset + 4 + br_len
        name_len = data[name_offset]
        
        # Handle trailing null bytes which crash psd-tools
        layer_name = data[name_offset+1:name_offset+1+name_len].decode('latin-1', errors='replace').rstrip('\x00')
        
        visible = not (flags & 0x02)
        visibility_status = "VISIBLE" if visible else "HIDDEN"
        
        print(f"  -> Layer {i:02d}: '{layer_name}' | {visibility_status} | Size: {right-left}x{bottom-top}")
        
        pos = extra_start + extra_len

if __name__ == "__main__":
    analyze_psd('cici.psd')
