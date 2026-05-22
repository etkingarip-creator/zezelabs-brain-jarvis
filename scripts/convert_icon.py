import os
from PIL import Image

def main():
    png_path = r"C:\Users\Zezelabs2\.gemini\antigravity\brain\72ac3918-bee9-4134-aad2-e6f2c15d7d33\brain_icon_1779410183772.png"
    dest_dir = r"C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop"
    dest_path = os.path.join(dest_dir, "brain.ico")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    img = Image.open(png_path).convert("RGBA")
    
    # Make dark backgrounds transparent for high-fidelity rendering
    datas = img.getdata()
    new_data = []
    for item in datas:
        # If it is solid black or very close to black, make it transparent
        if item[0] < 20 and item[1] < 20 and item[2] < 20:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # Save as multi-resolution ICO
    img.save(dest_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Icon successfully generated at {dest_path}")

if __name__ == "__main__":
    main()
