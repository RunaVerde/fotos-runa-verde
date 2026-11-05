import subprocess, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from cena import Mesa

SQUARE = len(sys.argv) > 1 and sys.argv[1] == "sq"
PREVIEW = len(sys.argv) > 2  # renderiza só alguns quadros para conferir
W, H, FPS = (1080, 1080, 30) if SQUARE else (1080, 1920, 30)
DUR = 24.0; NF = int(DUR * FPS)
D = "/home/claude/mistica/"
LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
LORAI = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
GOLD = (240, 200, 122); COPPER = (232, 150, 92); PALE = (242, 232, 255)
S = 0.68 if SQUARE else 1.0
def Y(v, q): return q if SQUARE else v

def F(size, bold=True, italic=False):
    f = ImageFont.truetype(LORAI if italic else LORA, int(size)); f.set_variation_by_axes([700 if bold else 400]); return f
def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.6, fo=0.6):
    return ease((t - a) / fi) * (1 - ease((t - (b - fo)) / fo))

HZ = Y(1180, 640)
mesa = Mesa(W, H, HZ, moon_y=Y(0.36, 0.30))

OBJ = {k: Image.open(D + f"obj{k}.png").convert("RGBA") for k in ("7", "4", "5", "2", "3", "1", "6u")}

def place(canvas, im, cx, base_y, width, alpha=1.0, glow=0.6, lift=0.0):
    """Coloca o produto com a base em base_y (sobre a mesa), sombra e brilho cobre."""
    sc = min(width / im.width, MAXH / im.height)
    o = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    a = o.split()[3]
    if alpha < 1: a = a.point(lambda v: int(v * alpha)); o.putalpha(a)
    x = int(cx - o.width / 2); y = int(base_y - o.height - lift)
    # sombra na mesa
    sh = Image.new("L", (int(o.width * 1.2), int(o.width * 0.22)), 0)
    ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, sh.height - 1), fill=int(190 * alpha / (1 + lift / 60)))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    canvas.paste((0, 0, 0), (int(cx - sh.width / 2), int(base_y - sh.height * 0.55)), sh)
    # brilho dourado/cobre atrás
    pad = 110
    ga = Image.new("L", (o.width + pad * 2, o.height + pad * 2), 0); ga.paste(a, (pad, pad))
    ga = ga.filter(ImageFilter.GaussianBlur(50)).point(lambda v: int(min(255, v * 1.4) * glow * alpha))
    canvas.paste(COPPER, (x - pad, y - pad), ga)
    canvas.paste(o, (x, y), o)

def glow_text(canvas, lines, y, alpha, col=PALE, gcol=(190, 120, 255), sp=1.22, track=0):
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
    # contorno escuro sutil para leitura
    sh = Image.new("RGBA", (W, H), (10, 0, 20, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(min(255, v * 1.3) * 0.75 * alpha)))
    canvas.paste(sh, (0, 3), sh)
    g = Image.new("RGBA", (W, H), gcol + (0,)); g.putalpha(a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(min(255, v * 1.5) * alpha)))
    canvas.paste(g, (0, 0), g)
    lay.putalpha(a.point(lambda v: int(v * alpha))); canvas.paste(lay, (0, 0), lay)

BASE = Y(1500, 860)      # onde a base da caixa encosta na mesa
CIRC = (W / 2, Y(960, 470))
PW = Y(880, 560)         # largura do produto
MAXH = Y(1060, 600)      # altura máxima do produto
CAPS = [("Tampa deslizante", "abre e fecha com suavidade", "1"),
        ("Pentagrama, luas e runas", "relevo em cobre sobre o preto", "4"),
        ("Guarda e protege", "baralhos de até 12 x 7 x 3 cm", "3")]

out_name = D + ("vq.mp4" if SQUARE else "v.mp4")
frames = range(NF) if not PREVIEW else [int(x * FPS) for x in (1.5, 5.0, 8.5, 11.5, 14.5, 17.5, 21.5)]
if not PREVIEW:
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out_name], stdin=subprocess.PIPE)
prev = []
for n in frames:
    t = n / FPS
    circ_a = 0.35 + 0.65 * win(t, 0.0, 10.2, 0.8, 0.8) + 0.5 * win(t, 18.8, 30, 0.9, 0.1)
    circ_a = min(circ_a, 1.0) * (0.55 if 10.2 <= t < 18.8 else 1.0)
    arr = mesa.frame(t, circle_a=circ_a, circle_c=CIRC, circle_scale=Y(1.0, 0.72) * (1 + 0.03 * math.sin(t * 0.8)))
    for hit in (3.0, 10.0, 19.0):
        if hit - 0.05 < t < hit + 0.9: arr = arr + 80 * math.exp(-(t - hit) * 3.5) * np.array([1.0, 0.8, 0.55])
    c = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # GANCHO 0–3
    glow_text(c, [("Suas cartas", F(76 * S + 8, bold=False, italic=True)), ("guardam segredos…", F(76 * S + 8, bold=False, italic=True))], Y(200, 50), win(t, 0.3, 3.1, 0.7, 0.5))
    glow_text(c, [("PROTEJA", F(110 * S + 10)), ("SUA MAGIA", F(110 * S + 10))], Y(1520, 790), win(t, 1.2, 3.15, 0.6, 0.45), col=GOLD, gcol=(255, 150, 60), track=8)

    # HERÓI 3–10.2: caixa fechada flutuando e pousando na mesa
    if 2.9 <= t < 10.4:
        lt = t - 2.9; a = win(t, 2.9, 10.4, 0.7, 0.6)
        lift = 70 * (1 - ease(lt / 2.2)) + 10 * math.sin(lt * 1.4) * ease(lt / 2.2)
        place(c, OBJ["7"], W / 2, BASE, PW * (0.94 + 0.06 * ease(lt / 7)), alpha=a, glow=0.55 + 0.2 * math.sin(lt * 2), lift=lift)
        glow_text(c, [("Caixa Mística Mágica", F(86 * S + 8, italic=True))], Y(170, 40), win(t, 3.4, 10.2, 0.6, 0.5), col=PALE)
        glow_text(c, [("EDIÇÃO LIMITADA", F(76 * S + 8))], Y(1640, 960), win(t, 5.0, 10.2, 0.5, 0.5), col=GOLD, gcol=(255, 160, 70), track=12)

    # DETALHES 10–19: 3 tomadas
    if 9.9 <= t < 19.2:
        st = t - 10.0; SH = 3.0; i = min(2, int(max(0, st) // SH)); lt = max(0, st - i * SH)
        a = win(t, 9.9, 19.2, 0.4, 0.5)
        fade = ease(lt / 0.45) * (1 - ease((lt - (SH - 0.4)) / 0.4)) if i < 2 else ease(lt / 0.45)
        cap = CAPS[i]; im = OBJ[cap[2]]
        dx = (-1 if i % 2 == 0 else 1) * 36 * (lt / SH - 0.5)
        wfac = 1.04 if i == 1 else 1.1
        place(c, im, W / 2 + dx, BASE, PW * wfac * (1.0 + 0.06 * lt / SH), alpha=a * fade, glow=0.5)
        glow_text(c, [(cap[0], F(72 * S + 8))], Y(190, 40), a * fade, col=GOLD, gcol=(255, 150, 60))
        glow_text(c, [(cap[1], F(54 * S + 6, bold=False, italic=True))], Y(1640, 965), a * fade)

    # CTA 19–24
    if t >= 18.9:
        lt = t - 18.9; a = ease(lt / 0.8)
        place(c, OBJ["5"], W / 2, BASE - Y(40, 20), PW * 0.86, alpha=a, glow=0.75, lift=8 * math.sin(lt * 1.4) + 8)
        glow_text(c, [("CAIXA MÍSTICA", F(84 * S + 8)), ("MÁGICA", F(84 * S + 8))], Y(150, 30), a, col=GOLD, gcol=(255, 150, 60), track=6)
        glow_text(c, [("Para tarot e oráculos", F(54 * S + 6, bold=False, italic=True))], Y(1560, 905), ease((lt - 0.7) / 0.8))
        glow_text(c, [("Runa Verde", F(52 * S + 6, bold=False))], Y(1690, 985), ease((lt - 1.3) / 0.8), col=(215, 200, 235))

    out = np.asarray(c, np.float32) * mesa.vig
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
    name = "caixa-mistica-magica-video" + ("-quadrado" if SQUARE else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_name, "-i", D + "trilha-caixa.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", str(DUR), "-movflags", "+faststart", D + name + ".mp4"], check=True)
    print("ok", name)
