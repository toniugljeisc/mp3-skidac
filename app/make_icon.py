"""Napravi app/icon.ico (pokreće se pri buildu)."""
import os
from PIL import Image, ImageDraw

S = 1024
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle([40, 40, S - 40, S - 40], radius=220, fill=(245, 165, 36, 255))
c, w = (26, 19, 0, 255), 70
d.line([(400, 720), (400, 280)], fill=c, width=w)
d.line([(740, 660), (740, 220)], fill=c, width=w)
d.polygon([(365, 250), (775, 180), (775, 320), (365, 390)], fill=c)
d.ellipse([250, 630, 435, 790], fill=c)
d.ellipse([590, 570, 775, 730], fill=c)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
im.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon:", out)
