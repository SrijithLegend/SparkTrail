#!/usr/bin/env python3
"""Act 1 frames: EV charger internals revealed part-by-part + where SparkTrail sits,
then the microgrid. Large, bright, diagrammatic, TVA palette on the site's #0A0A0F.
Swap for Veo→Ezgif frames later (same frame_NNN.jpg naming, update counts in app/page.tsx)."""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 900
BG = (10, 10, 15)  # #0A0A0F, the site --bg: frame edges must be invisible
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "sequences")
# TVA palette: orange signature, amber secondary, cyan = SparkTrail (defense)
ORANGE, AMBER, CYAN = (255, 107, 0), (240, 168, 54), (0, 214, 255)
CARD, TEXT = (30, 25, 24), (240, 236, 228)

def font(sz, bold=False):
    for p in [f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
              "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
F = font(17, True); FS = font(14)  # Segoe UI runs wider than DejaVu

def ease(t): t = max(0, min(1, t)); return 4*t*t*t if t < 0.5 else 1-(-2*t+2)**3/2
def lerp(a, b, t): return a+(b-a)*t
def clamp(x, a=0, b=1): return max(a, min(b, x))

def backdrop():
    img = Image.new("RGB", (W, H), BG)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([W*0.05, H*0.05, W*0.95, H*0.9], fill=60)
    g = g.filter(ImageFilter.GaussianBlur(140))
    return Image.composite(Image.new("RGB", (W, H), (26, 14, 6)), img, g).convert("RGBA")

def glow(base, box, col, rad, a, blur):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(l).rounded_rectangle(box, radius=rad, fill=col+(a,))
    return Image.alpha_composite(base, l.filter(ImageFilter.GaussianBlur(blur)))

# ---------- charger internals ----------
MODULES = [("Connector / CCS", 275, ORANGE), ("Power module", 360, AMBER),
           ("Contactor", 445, ORANGE), ("Charger controller", 530, AMBER),
           ("Comms / OCPP", 615, ORANGE)]
PED = [90, 235, 250, 690]; COL_X = 480; SPARK = (630, 450); PACK = [720, 395, 855, 545]
BW, BH = 180, 68

def charger_frame(p):
    img = backdrop()
    for i, (nm, y, col) in enumerate(MODULES):
        f = ease(clamp((p-(0.08+i*0.1))/0.3)); x = lerp(170, COL_X, f)
        img = glow(img, [x-BW/2, y-BH/2, x+BW/2, y+BH/2], col, 16, int(150*f), 22)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle(PED, radius=22, fill=(22, 18, 16, 255), outline=(120, 80, 45, 255), width=2)
    d.text((PED[0]+16, PED[1]+14), "EV CHARGER", font=FS, fill=(205, 170, 135, 255))
    pa = clamp((p-0.45)/0.2)
    if pa > 0:
        a = int(255*pa)
        d.rounded_rectangle(PACK, radius=14, fill=(34, 24, 14, a), outline=AMBER+(a,), width=4)
        for cx in range(PACK[0]+16, PACK[2]-12, 20):
            d.line([cx, PACK[1]+16, cx, PACK[3]-16], fill=AMBER+(int(120*pa),), width=4)
        d.text((PACK[0]+6, PACK[3]+10), "Battery pack", font=FS, fill=TEXT+(a,))
    for i, (nm, y, col) in enumerate(MODULES):
        f = ease(clamp((p-(0.08+i*0.1))/0.3)); x = lerp(170, COL_X, f)
        d.line([PED[2], y, x-BW/2, y], fill=col+(int(110*f),), width=2)
        d.rounded_rectangle([x-BW/2, y-BH/2, x+BW/2, y+BH/2], radius=14,
                            fill=CARD+(255,), outline=col+(255,), width=4)
        d.rounded_rectangle([x-BW/2+10, y-BH/2+10, x+BW/2-10, y-BH/2+18], radius=4, fill=col+(110,))
        tb = d.textbbox((0, 0), nm, font=F); d.text((x-(tb[2]-tb[0])/2, y-11), nm, font=F, fill=TEXT+(255,))
    sa = clamp((p-0.6)/0.22)
    if sa > 0:  # SparkTrail on the control link between command and cell
        a = int(255*sa)
        d.line([COL_X+BW/2, 530, SPARK[0], SPARK[1]], fill=CYAN+(int(170*sa),), width=4)
        d.line([SPARK[0], SPARK[1], PACK[0], (PACK[1]+PACK[3])//2], fill=CYAN+(int(170*sa),), width=4)
        img = glow(img, [SPARK[0]-40, SPARK[1]-40, SPARK[0]+40, SPARK[1]+40], CYAN, 40, int(210*sa), 22)
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([SPARK[0]-22, SPARK[1]-22, SPARK[0]+22, SPARK[1]+22], fill=CYAN+(a,))
        for txt, fnt, dy, col in [("SPARKTRAIL", F, 32, CYAN+(a,)), ("physics-aware monitor", FS, 56, (200, 235, 245, a))]:
            tb = d.textbbox((0, 0), txt, font=fnt)
            d.text((SPARK[0]+18-(tb[2]-tb[0])/2, SPARK[1]+dy), txt, font=fnt, fill=col)
    return img.convert("RGB")

# ---------- microgrid ----------
def ring(names, cols):
    out = []; n = len(names)
    for i, nm in enumerate(names):
        a = (i/n)*2*math.pi - math.pi/2
        out.append((nm, math.cos(a)*270, math.sin(a)*215, cols[i % len(cols)]))
    return out
MICRO = ring(["Transformer", "BESS", "Inverter", "Breaker", "Busbar", "Smart meter", "Feeder"],
             [ORANGE, AMBER, ORANGE, CYAN, ORANGE, AMBER, ORANGE])

def micro_frame(p):
    img = backdrop(); e = ease(p); cx, cy = W/2, H/2-10
    for (nm, tx, ty, col) in MICRO:
        x, y = cx+tx*e, cy+ty*e
        img = glow(img, [x-70, y-44, x+70, y+44], col, 14, int(140*e), 20)
    d = ImageDraw.Draw(img, "RGBA")
    for (nm, tx, ty, col) in MICRO:
        d.line([cx, cy, cx+tx*e, cy+ty*e], fill=col+(80,), width=2)
    d.ellipse([cx-20, cy-20, cx+20, cy+20], fill=ORANGE+(235,))
    for (nm, tx, ty, col) in MICRO:
        x, y = cx+tx*e, cy+ty*e
        d.rounded_rectangle([x-70, y-44, x+70, y+44], radius=14, fill=CARD+(255,), outline=col+(255,), width=4)
        tb = d.textbbox((0, 0), nm, font=F); d.text((x-(tb[2]-tb[0])/2, y+50), nm, font=F, fill=TEXT+(255,))
    return img.convert("RGB")

def render(name, fn, count):
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    for i in range(count):
        fn(i/(count-1)).save(os.path.join(d, f"frame_{i:03d}.jpg"), quality=84)
    print(f"{name}: {count}")

render("charger-internals", charger_frame, 72)
render("microgrid-explode", micro_frame, 48)
