"""Crea miniaturas .webp (700 px) en stock/fotos/sm/ para las fotos que no tengan una."""
import os
from PIL import Image
SRC, DST = "stock/fotos", "stock/fotos/sm"
os.makedirs(DST, exist_ok=True)
n = 0
for f in sorted(os.listdir(SRC)):
    base, ext = os.path.splitext(f)
    if ext.lower() not in (".jpg", ".jpeg", ".png"):
        continue
    out = os.path.join(DST, base + ".webp")
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(os.path.join(SRC, f)):
        continue
    im = Image.open(os.path.join(SRC, f))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3]); im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((700, 700))
    im.save(out, "WEBP", quality=80, method=6)
    n += 1
print("miniaturas nuevas:", n)
