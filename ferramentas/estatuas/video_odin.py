import subprocess, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, __import__("os").path.dirname(__file__))
from PIL import ImageChops
from cena_floresta import Floresta

SQUARE = len(sys.argv) > 1 and sys.argv[1] == "sq"
PREVIEW = len(sys.argv) > 2
W, H, FPS = (1080, 1080, 30) if SQUARE else (1080, 1920, 30)
DUR = 24.0; NF = int(DUR * FPS)
D = "/home/claude/odin/"
CINZ = "/usr/share/fonts/truetype/google-fonts/Cinzel-Variable.ttf"
LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
LORAI = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
import os
if not os.path.exists(CINZ): CINZ = LORA
GOLD = (250, 228, 150); PALE = (228, 255, 230); GL = (90, 255, 140)
S = 0.68 if SQUARE else 1.0
def Y(v, q): return q if SQUARE else v

def F(size, bold=True, italic=False, title=False):
    path = CINZ if title else (LORAI if italic else LORA)
    f = ImageFont.truetype(path, int(size))
    try: f.set_variation_by_axes([700 if bold else 400])
    except Exception: pass
    return f
def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.6, fo=0.6):
    return ease((t - a) / fi) * (1 - ease((t - (b - fo)) / fo))

GY = Y(1380, 790)
cena = Floresta(W, H, GY)
BASE = int(cena.stone_y + Y(28, 24))
OBJ = {k: Image.open(D + f"obj{k}.png").convert("RGBA") for k in range(1, 8)}
def valknut(size, col=(170, 255, 180)):
    import math as _m
    S = size * 3; m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m); c = S / 2; w = int(S * 0.028); R = S * 0.26
    offs = [(-0.0, -0.10), (-0.13, 0.10), (0.13, 0.10)]
    for k, (ox, oy) in enumerate(offs):
        cx, cy = c + ox * S, c + oy * S
        pts = [(cx + R * _m.cos(-_m.pi / 2 + j * 2 * _m.pi / 3), cy + R * _m.sin(-_m.pi / 2 + j * 2 * _m.pi / 3)) for j in range(3)]
        d.line(pts + [pts[0]], fill=255, width=w, joint="curve")
    d.ellipse((c - S * 0.47, c - S * 0.47, c + S * 0.47, c + S * 0.47), outline=255, width=int(w * 0.8))
    im = Image.new("RGBA", (S, S), col + (0,)); im.putalpha(m); return im.resize((size, size), Image.LANCZOS)
cena.triq = valknut(int(W * 0.30))

def place(c, im, cx, base_y, maxh, maxw, alpha=1.0, glow=0.6, lift=0.0, crop=None):
    if crop:
        x0, y0, x1, y1 = crop; im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
    sc = min(maxw / im.width, maxh / im.height)
    o = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    a = o.split()[3]
    if alpha < 1: a = a.point(lambda v: int(v * alpha)); o.putalpha(a)
    x = int(cx - o.width / 2); y = int(base_y - o.height - lift)
    if not crop:
        P = 50; sw, shh = int(o.width * 1.1), int(o.width * 0.2)
        sh = Image.new("L", (sw + 2 * P, shh + 2 * P), 0)
        ImageDraw.Draw(sh).ellipse((P, P, P + sw, P + shh), fill=int(170 * alpha / (1 + lift / 60)))
        sh = sh.filter(ImageFilter.GaussianBlur(22)); c.paste((0, 10, 5), (int(cx - sh.width / 2), int(base_y - sh.height * 0.5)), sh)
    pad = 120; ga = Image.new("L", (o.width + pad * 2, o.height + pad * 2), 0); ga.paste(a, (pad, pad))
    ga = ga.filter(ImageFilter.GaussianBlur(55)).point(lambda v: int(min(255, v * 1.4) * glow * alpha))
    c.paste(GL, (x - pad, y - pad), ga)
    # leve tom verde no produto (luz da floresta)
    rgb = np.asarray(o.convert("RGB"), np.float32) * np.array([0.92, 1.0, 0.93]); o2 = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA"); o2.putalpha(o.split()[3])
    c.paste(o2, (x, y), o2)

def text(c, lines, y, alpha, col=PALE, gcol=(60, 230, 120), sp=1.22, track=0):
    if alpha <= 0.01: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cy = y
    for txt, f in lines:
        if track:
            ws = [d.textlength(ch, font=f) + track for ch in txt]; x = (W - (sum(ws) - track)) / 2
            for ch, w_ in zip(txt, ws): d.text((x, cy), ch, font=f, fill=col + (255,)); x += w_
        else:
            tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, cy), txt, font=f, fill=col + (255,))
        cy += f.size * sp
    a = lay.split()[3]
    sh = Image.new("RGBA", (W, H), (0, 15, 5, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(min(255, v * 1.5) * 0.85 * alpha)))
    c.paste(sh, (0, 3), sh)
    g = Image.new("RGBA", (W, H), gcol + (0,)); g.putalpha(a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(min(255, v * 1.3) * 0.8 * alpha)))
    c.paste(g, (0, 0), g)
    lay.putalpha(a.point(lambda v: int(v * alpha))); c.paste(lay, (0, 0), lay)

MAXH = Y(1150, 640); MAXW = Y(820, 520)
RING = (W / 2, Y(820, 430))
# detalhes: (título, legenda, obj, recorte, alturaMax)
CAPS = [("O Pai de Todos", "o sábio que deu um olho pelo saber", 2, (0.15, 0.0, 0.85, 0.48), Y(900, 520)),
        ("Hugin e Munin", "os corvos do pensamento e da memória", 7, None, MAXH),
        ("Broche Valknut", "manto de pele e tranças esculpidas", 6, (0.0, 0.30, 1.0, 0.85), Y(760, 450))]

out_name = D + ("vq.mp4" if SQUARE else "v.mp4")
frames = range(NF) if not PREVIEW else [int(x * FPS) for x in (1.5, 4.0, 8.0, 11.5, 14.5, 17.5, 21.5)]
if not PREVIEW:
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out_name], stdin=subprocess.PIPE)
prev = []
for n in frames:
    t = n / FPS
    ra = 0.5 + 0.5 * win(t, 0, 10.2, 0.8, 0.8) + 0.5 * win(t, 18.8, 30, 0.9, 0.1)
    ra = min(ra, 1.0) * (0.45 if 10.2 <= t < 18.8 else 1.0)
    c = cena.frame(t, ring_a=ra, ring_c=RING, ring_scale=Y(1.0, 0.72) * (1 + 0.03 * math.sin(t * 0.8)))
    for hit in (3.0, 10.0, 19.0):
        if hit - 0.05 < t < hit + 0.9:
            fl = Image.new("RGBA", (W, H), (120, 255, 150, int(110 * math.exp(-(t - hit) * 3.5)))); c.alpha_composite(fl)

    # GANCHO 0–3
    text(c, [("Dos salões", F(74 * S + 8, False, True)), ("de Asgard…", F(74 * S + 8, False, True))], Y(220, 50), win(t, 0.3, 3.1, 0.7, 0.5))
    text(c, [("O PAI", F(110 * S + 10, title=True)), ("DE TODOS", F(110 * S + 10, title=True))], Y(1500, 800), win(t, 1.2, 3.15, 0.6, 0.45), col=GOLD, gcol=(80, 220, 110), track=6)

    # HERÓI 3–10.2
    if 2.9 <= t < 10.4:
        lt = t - 2.9; a = win(t, 2.9, 10.4, 0.7, 0.6)
        lift = 90 * (1 - ease(lt / 2.2)) + 8 * math.sin(lt * 1.4) * ease(lt / 2.2)
        place(c, OBJ[1], W / 2, BASE, MAXH * (0.95 + 0.05 * ease(lt / 7)), MAXW, alpha=a, glow=0.55 + 0.2 * math.sin(lt * 2), lift=lift)
        text(c, [("Busto de Odin", F(92 * S + 8, title=True))], Y(150, 30), win(t, 3.4, 10.2, 0.6, 0.5), col=GOLD)
        text(c, [("DEUS NÓRDICO", F(66 * S + 8, title=True))], Y(1650, 975), win(t, 5.0, 10.2, 0.5, 0.5), col=PALE, track=14)

    # DETALHES 10–19
    if 9.9 <= t < 19.2:
        st = t - 10.0; SH = 3.0; i = min(2, int(max(0, st) // SH)); lt = max(0, st - i * SH)
        a = win(t, 9.9, 19.2, 0.4, 0.5)
        fade = ease(lt / 0.45) * (1 - ease((lt - (SH - 0.4)) / 0.4)) if i < 2 else ease(lt / 0.45)
        tt, cap, k, crop, mh = CAPS[i]
        dx = (-1 if i % 2 == 0 else 1) * 30 * (lt / SH - 0.5)
        zoom = 1.0 + 0.07 * lt / SH
        if crop:
            cy_ = Y(1000, 600) + (mh * zoom) / 2
            place(c, OBJ[k], W / 2 + dx, cy_, mh * zoom, W * 0.9 * zoom, alpha=a * fade, glow=0.5, crop=crop)
        else:
            place(c, OBJ[k], W / 2 + dx, BASE, mh * zoom, MAXW * zoom, alpha=a * fade, glow=0.5)
        text(c, [(tt, F(76 * S + 8, title=True))], Y(170, 35), a * fade, col=GOLD)
        text(c, [(cap, F(52 * S + 6, False, True))], Y(1660, 975), a * fade)

    # CTA 19–24
    if t >= 18.9:
        lt = t - 18.9; a = ease(lt / 0.8)
        place(c, OBJ[4], W / 2, BASE, MAXH * 0.92, MAXW, alpha=a, glow=0.75, lift=6 * math.sin(lt * 1.4) + 6)
        text(c, [("BUSTO", F(70 * S + 8, title=True)), ("ODIN", F(110 * S + 8, title=True))], Y(120, 25), a, col=GOLD, track=4)
        text(c, [("Decoração viking e nórdica", F(54 * S + 6, False, True))], Y(1600, 930), ease((lt - 0.7) / 0.8))
        text(c, [("Runa Verde", F(52 * S + 6, False))], Y(1720, 1000), ease((lt - 1.3) / 0.8), col=(200, 240, 205))

    cena.overlay(c, t)
    out = np.asarray(c.convert("RGB"), np.float32) * cena.vig
    if t > DUR - 0.8: out *= max(0, (DUR - t) / 0.8)
    if t < 0.4: out *= t / 0.4
    fr = np.clip(out, 0, 255).astype(np.uint8)
    if PREVIEW: prev.append(Image.fromarray(fr).resize((W // 3, H // 3)))
    else: p.stdin.write(fr.tobytes())
if PREVIEW:
    sheet = Image.new("RGB", (W // 3 * 4, H // 3 * 2), "gray")
    for k, im in enumerate(prev): sheet.paste(im, ((k % 4) * (W // 3), (k // 4) * (H // 3)))
    sheet.save(D + ("prev_sq.jpg" if SQUARE else "prev_v.jpg")); print("preview ok")
else:
    p.stdin.close(); p.wait()
    name = "busto-odin-video" + ("-quadrado" if SQUARE else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_name, "-i", D + "trilha-odin.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", str(DUR), "-movflags", "+faststart", D + name + ".mp4"], check=True)
    print("ok", name)
