"""Resize/compress images in assets/images to a reasonable web size in place."""
import os
from PIL import Image, ImageOps

MAX_DIM = 1600
JPEG_QUALITY = 82
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "images")

def optimize(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    if max(w, h) > MAX_DIM:
        scale = MAX_DIM / max(w, h)
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    elif ext == ".png":
        im.save(path, "PNG", optimize=True)
    print(f"{os.path.basename(path)}: {w}x{h} -> {im.size[0]}x{im.size[1]}, {os.path.getsize(path)//1024}KB")

if __name__ == "__main__":
    for name in sorted(os.listdir(IMG_DIR)):
        if name.lower().endswith((".jpg", ".jpeg", ".png")):
            optimize(os.path.join(IMG_DIR, name))
