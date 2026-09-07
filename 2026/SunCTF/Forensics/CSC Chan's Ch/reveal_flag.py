from PIL import Image
import os

def reveal_flag(layer_path, output_path):
    print(f"[*] Processing {layer_path}...")
    
    if not os.path.exists(layer_path):
        print("[-] Target layer file not found.")
        return

    # Open the layer containing the white-on-white text
    img = Image.open(layer_path).convert('RGBA')

    # Create a solid black background matching the layer's size
    bg = Image.new('RGBA', img.size, (0, 0, 0, 255))
    
    # Paste the transparent layer onto the black background
    # The mask ensures that the alpha channel dictates visibility
    bg.paste(img, mask=img.split()[3])
    
    # Save the revealed image
    bg.convert('RGB').save(output_path)
    print(f"[+] Flag revealed and saved to {output_path}")

if __name__ == "__main__":
    # Adjust this path based on where decode_layers.py saved the output
    hidden_layer = 'extracted_layers/layer_01_Paint_Layer_8.png'
    output_image = 'flag_revealed.png'
    
    reveal_flag(hidden_layer, output_image)
