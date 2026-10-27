#!/usr/bin/env python3
"""Placeholder exploded-component sequences on #050505.
Swap these out for Veo→Ezgif frames later; the canvas mechanic is identical."""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 720
BG = (5, 5, 5)
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "sequences")

def font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/segoeui.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

F = font(15)

def ease(t):  # easeInOutCubic
    return 4*t*t*t if t < 0.5 else 1 - (-2*t+2)**3/2

def rrect(draw, box, r, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def frame(parts, t):
    img = Image.new("RGB", (W, H), BG)
    # subtle radial backdrop
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W*0.12, H*0.10, W*0.88, H*0.78], fill=55)
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    img = Image.composite(Image.new("RGB", (W, H), (10, 13, 26)), img, glow)

    e = ease(t)
    cx, cy = W/2, H/2 - 10

    # ---- glow halos (accent) ----
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for (name, tx, ty, col) in parts:
        x, y = cx + tx*e, cy + ty*e
        w, h = 112, 74
        hd.rounded_rectangle([x-w/2, y-h/2, x+w/2, y+h/2], radius=14, fill=col + (150,))
    halo = halo.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB")

    d = ImageDraw.Draw(img, "RGBA")
    # connector lines from hub
    for (name, tx, ty, col) in parts:
        x, y = cx + tx*e, cy + ty*e
        d.line([cx, cy, x, y], fill=col + (70,), width=2)
    # central hub core
    d.ellipse([cx-16, cy-16, cx+16, cy+16], fill=(0, 214, 255, 230))
    # boxes
    for (name, tx, ty, col) in parts:
        x, y = cx + tx*e, cy + ty*e
        w, h = 112, 74
        d.rounded_rectangle([x-w/2, y-h/2, x+w/2, y+h/2], radius=14,
                            fill=(34, 38, 48, 255), outline=col + (255,), width=3)
        # inner highlight bar
        d.rounded_rectangle([x-w/2+8, y-h/2+8, x+w/2-8, y-h/2+16], radius=4, fill=col + (90,))
        tb = d.textbbox((0, 0), name, font=F); tw = tb[2]-tb[0]
        a = int(max(60, min(255, (e-0.2)/0.4*255)))
        d.text((x - tw/2, y + 42), name, font=F, fill=(235, 233, 226, a))

    # no baked-in caption: the page's text beats carry the copy
    return img

def ring(parts_names, colors):
    out = []
    n = len(parts_names)
    for i, nm in enumerate(parts_names):
        ang = (i/n)*2*math.pi - math.pi/2
        R = 210
        out.append((nm, math.cos(ang)*R, math.sin(ang)*R*0.82, colors[i % len(colors)]))
    return out

CYAN, BLUE, AMBER = (0, 214, 255), (0, 80, 255), (240, 168, 54)

CHARGER = ring(["Connector", "Power PCB", "Contactor", "Cooling", "Controller",
                "HMI", "RFID", "Cabinet"], [CYAN, BLUE, CYAN, BLUE])
MICRO = ring(["Transformer", "BESS", "Inverter", "Breaker", "Busbar", "Meter", "Feeder"],
             [AMBER, CYAN, BLUE, CYAN, AMBER, BLUE, CYAN])

def render(name, parts, count=48):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    for i in range(count):
        t = i/(count-1)
        img = frame(parts, t)
        img.save(os.path.join(d, f"frame_{i:03d}.jpg"), quality=82)
    print(f"{name}: {count} frames")

render("charger-explode", CHARGER)
render("microgrid-explode", MICRO)
