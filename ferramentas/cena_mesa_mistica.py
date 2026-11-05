"""Mesa mística procedural (fundo estático + elementos animados) para os vídeos da Runa Verde."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
PURPLE_D = np.array([18, 6, 30], np.float32)
PURPLE = np.array([62, 24, 96], np.float32)
GOLD = (236, 196, 120)
COPPER = (214, 128, 72)


def lerp(a, b, k):
    return a * (1 - k) + b * k


class Mesa:
    def __init__(self, W, H, horizon, seed=11, moon_y=0.36):
        self.moon_y = moon_y
        self.W, self.H, self.hz = W, H, horizon
        rng = np.random.default_rng(seed)
        self.rng = rng
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        # parede: roxo profundo com brilho central
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - horizon * 0.75) / H) ** 2 * 2.2)
        k = np.clip(r / 0.75, 0, 1)[..., None]
        wall = lerp(PURPLE, PURPLE_D, k)
        # mesa: madeira escura arroxeada em perspectiva
        ty = np.clip((yy - horizon) / (H - horizon), 0, 1)
        persp = 1 / (0.15 + ty)  # frequência maior perto do horizonte
        grain = (np.sin((xx - W / 2) * 0.004 * persp * 6 + np.sin(yy * 0.02) * 0.8) * 0.5 + 0.5)
        noise = rng.normal(0, 1, (H // 8 + 1, W // 8 + 1)).astype(np.float32)
        noise = np.asarray(Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        wood = np.array([46, 22, 30], np.float32) * (0.7 + 0.3 * grain[..., None]) * (0.8 + 0.4 * noise[..., None])
        wood = wood * (0.55 + 0.6 * ty[..., None])  # mais claro perto da câmera
        table = (yy >= horizon)[..., None]
        img = np.where(table, wood, wall)
        # toalha de veludo roxo com bordado dourado (trapézio central)
        cloth = Image.new("L", (W, H), 0); dc = ImageDraw.Draw(cloth)
        topw, botw = W * 0.42, W * 1.1
        poly = [(W / 2 - topw / 2, horizon + 6), (W / 2 + topw / 2, horizon + 6), (W / 2 + botw / 2, H), (W / 2 - botw / 2, H)]
        dc.polygon(poly, fill=255)
        cm = np.asarray(cloth.filter(ImageFilter.GaussianBlur(2)), np.float32)[..., None] / 255
        vel = np.array([78, 26, 110], np.float32) * (0.55 + 0.55 * ty[..., None]) * (0.85 + 0.3 * noise[..., None])
        img = lerp(img, vel, cm)
        self.base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(self.base, "RGBA")
        # bordas douradas da toalha
        for off, wdt in ((10, 3), (26, 2)):
            sx = off * 0.5
            pl = [(W / 2 - topw / 2 + sx, horizon + 6), (W / 2 - botw / 2 + off * 1.6, H)]
            pr = [(W / 2 + topw / 2 - sx, horizon + 6), (W / 2 + botw / 2 - off * 1.6, H)]
            d.line(pl, fill=(214, 168, 90, 200), width=wdt); d.line(pr, fill=(214, 168, 90, 200), width=wdt)
        # padrão de estrelas bordadas na toalha
        for _ in range(70):
            fy = rng.uniform(0.08, 1.0); y = horizon + fy * (H - horizon)
            half = (topw + (botw - topw) * fy) / 2 - 30
            x = W / 2 + rng.uniform(-half, half); s = 3 + 9 * fy
            self._star(d, x, y, s, (220, 170, 95, int(90 + 80 * fy)))
        # linha do horizonte da mesa (borda frontal brilhante)
        d.line([(0, horizon), (W, horizon)], fill=(120, 70, 60, 160), width=3)
        # parede: arco de fases da lua + constelações
        self._moon_arc(d, W / 2, horizon * self.moon_y, W * 0.42)
        for _ in range(9):
            pts = [(rng.uniform(0, W), rng.uniform(0, horizon * 0.85)) for _ in range(4)]
            d.line(pts, fill=(170, 140, 220, 50), width=1)
            for p in pts: d.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=(230, 210, 255, 140))
        # artefatos sobre a mesa (atrás do produto)
        S = W / 1080
        self.candles = []
        self._artifacts(d, S)
        self.base = self.base.filter(ImageFilter.GaussianBlur(0.6))
        # profundidade: desfoca levemente o fundo distante
        self.base_np = np.asarray(self.base, np.float32)
        # partículas
        self.stars = [(rng.uniform(0, W), rng.uniform(0, horizon), rng.uniform(0.6, 2.2), rng.uniform(0, 6.28), rng.uniform(0.6, 2.0)) for _ in range(160)]
        self.dust = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4.0), rng.uniform(18, 55), rng.uniform(0, 6.28), rng.random() < 0.5) for _ in range(70)]
        self.circle = self._magic_circle(int(900 * S))
        yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
        rv = np.sqrt(((xv - W / 2) / W) ** 2 + ((yv - H / 2) / H) ** 2)
        self.vig = (1 - 0.6 * np.clip((rv - 0.32) / 0.42, 0, 1) ** 1.5)[..., None]

    # ---------- desenhos ----------
    @staticmethod
    def _star(d, x, y, s, col):
        pts = []
        for i in range(8):
            a = i * math.pi / 4; rr = s if i % 2 == 0 else s * 0.35
            pts.append((x + rr * math.sin(a), y - rr * math.cos(a)))
        d.polygon(pts, fill=col)

    def _moon_arc(self, d, cx, cy, R):
        n = 9
        for i in range(n):
            a = math.pi * (0.15 + 0.7 * i / (n - 1))
            x = cx - R * math.cos(a); y = cy + R * 0.28 * (1 - math.sin(a)) * -1 + R * 0.12
            rr = 22 * self.W / 1080
            ph = (i / (n - 1)) * 2 - 1  # -1..1
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(226, 190, 120, 210))
            off = ph * rr * 2.0
            if abs(ph) < 0.98:
                d.ellipse((x - rr + off, y - rr, x + rr + off, y + rr), fill=(30, 12, 48, 235))
            d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(226, 190, 120, 120), width=1)

    def _magic_circle(self, D):
        im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        c = D / 2; col = (232, 186, 110, 255); col2 = (205, 125, 75, 255)
        for rr, w in ((0.49, 3), (0.46, 1), (0.36, 2), (0.34, 1)):
            d.ellipse((c - D * rr, c - D * rr, c + D * rr, c + D * rr), outline=col, width=w)
        # runas desenhadas a traço ao redor
        R_ = {
            'f': [((.3,0),(.3,1)),((.3,.15),(.75,0)),((.3,.42),(.75,.27))],
            'u': [((.3,1),(.3,0)),((.3,0),(.72,.3)),((.72,.3),(.72,1))],
            'th': [((.3,0),(.3,1)),((.3,.28),(.7,.5)),((.7,.5),(.3,.72))],
            'a': [((.3,0),(.3,1)),((.3,.1),(.7,.32)),((.3,.36),(.7,.58))],
            'r': [((.3,0),(.3,1)),((.3,0),(.7,.25)),((.7,.25),(.3,.5)),((.3,.5),(.72,1))],
            'k': [((.65,0),(.3,.5)),((.3,.5),(.65,1))],
            'g': [((.25,0),(.75,1)),((.75,0),(.25,1))],
            'h': [((.3,0),(.3,1)),((.7,0),(.7,1)),((.3,.35),(.7,.65))],
            'n': [((.5,0),(.5,1)),((.32,.35),(.68,.6))],
            'i': [((.5,0),(.5,1))],
            's': [((.65,0),(.35,.4)),((.35,.4),(.65,.6)),((.65,.6),(.35,1))],
            't': [((.5,0),(.5,1)),((.5,0),(.25,.3)),((.5,0),(.75,.3))],
            'b': [((.3,0),(.3,1)),((.3,0),(.7,.25)),((.7,.25),(.3,.5)),((.3,.5),(.7,.75)),((.7,.75),(.3,1))],
            'e': [((.25,1),(.25,0)),((.25,0),(.5,.3)),((.5,.3),(.75,0)),((.75,0),(.75,1))],
            'm': [((.25,0),(.25,1)),((.75,0),(.75,1)),((.25,0),(.75,.45)),((.75,0),(.25,.45))],
            'l': [((.35,0),(.35,1)),((.35,0),(.7,.3))],
            'o': [((.5,0),(.8,.35)),((.8,.35),(.2,1)),((.5,0),(.2,.35)),((.2,.35),(.8,1))],
            'd': [((.2,0),(.2,1)),((.8,0),(.8,1)),((.2,0),(.8,1)),((.8,0),(.2,1))],
            'z': [((.5,0),(.5,1)),((.5,.4),(.2,0)),((.5,.4),(.8,0))],
            'j': [((.4,.1),(.15,.4)),((.15,.4),(.4,.6)),((.6,.4),(.85,.6)),((.85,.6),(.6,.9))],
        }
        keys = list(R_.keys()) * 2
        gs = D * 0.05
        for i, kname in enumerate(keys[:24]):
            a = 2 * math.pi * i / 24
            x = c + D * 0.41 * math.sin(a); y = c - D * 0.41 * math.cos(a)
            ca_, sa_ = math.cos(a), math.sin(a)
            for (x1, y1), (x2, y2) in R_[kname]:
                p1 = ((x1 - .5) * gs, (y1 - .5) * gs); p2 = ((x2 - .5) * gs, (y2 - .5) * gs)
                q1 = (x + p1[0] * ca_ - p1[1] * sa_, y + p1[0] * sa_ + p1[1] * ca_)
                q2 = (x + p2[0] * ca_ - p2[1] * sa_, y + p2[0] * sa_ + p2[1] * ca_)
                d.line([q1, q2], fill=col, width=2)
        # hexagrama + pentagrama interno
        for k, colk in ((5, col2),):
            R = D * (0.34 if k == 5 else 0.30)
            step = 2 if k == 5 else 1
            pts = [(c + R * math.sin(2 * math.pi * i / k), c - R * math.cos(2 * math.pi * i / k)) for i in range(k)]
            if k == 5:
                order = [pts[(i * step) % 5] for i in range(6)]
                d.line(order, fill=colk, width=2)
            else:
                d.polygon(pts[0::2], outline=colk); d.polygon(pts[1::2], outline=colk)
        # pequenos pontos
        for i in range(72):
            a = 2 * math.pi * i / 72
            x = c + D * 0.475 * math.sin(a); y = c - D * 0.475 * math.cos(a)
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=col)
        return im

    def _artifacts(self, d, S):
        W, H, hz = self.W, self.H, self.hz
        rng = self.rng
        # velas (x, y_base, altura, largura)
        specs = [(0.12, 0.10, 260, 46), (0.20, 0.03, 170, 40), (0.86, 0.06, 230, 46), (0.93, 0.16, 150, 38)]
        for fx, fy, ht, wd in specs:
            x = W * fx; yb = hz + fy * (H - hz) + 20 * S; ht *= S; wd *= S
            sc = 0.8 + fy
            ht *= sc; wd *= sc
            # sombra
            d.ellipse((x - wd * 0.9, yb - wd * 0.18, x + wd * 0.9, yb + wd * 0.18), fill=(0, 0, 0, 120))
            # corpo
            d.rectangle((x - wd / 2, yb - ht, x + wd / 2, yb), fill=(226, 214, 190, 255))
            d.rectangle((x - wd / 2, yb - ht, x - wd / 6, yb), fill=(240, 232, 214, 255))
            d.rectangle((x + wd / 4, yb - ht, x + wd / 2, yb), fill=(190, 176, 150, 255))
            d.ellipse((x - wd / 2, yb - ht - wd * 0.15, x + wd / 2, yb - ht + wd * 0.15), fill=(246, 236, 214, 255))
            # pingos de cera
            for _ in range(3):
                dx = rng.uniform(-wd / 2.4, wd / 2.4); dl = rng.uniform(ht * 0.08, ht * 0.3)
                d.rounded_rectangle((x + dx - 4 * S, yb - ht, x + dx + 4 * S, yb - ht + dl), 4, fill=(246, 238, 220, 255))
            d.ellipse((x - wd / 2, yb - wd * 0.15, x + wd / 2, yb + wd * 0.15), fill=(200, 186, 160, 255))
            d.line([(x, yb - ht - wd * 0.1), (x, yb - ht - wd * 0.45)], fill=(40, 30, 20, 255), width=max(2, int(3 * S)))
            self.candles.append((x, yb - ht - wd * 0.45, wd))
        # cristais (cluster) à esquerda e direita
        for cx, cy, s, hue in ((0.27, 0.11, 1.0, (150, 90, 210)), (0.76, 0.13, 0.85, (170, 110, 230))):
            x0 = W * cx; y0 = hz + cy * (H - hz) + 20 * S; s *= S * (0.9 + cy)
            d.ellipse((x0 - 90 * s, y0 - 14 * s, x0 + 90 * s, y0 + 14 * s), fill=(0, 0, 0, 110))
            for ang, ln, wd in ((-28, 120, 34), (-8, 170, 42), (14, 140, 36), (32, 95, 30), (-45, 80, 26)):
                a = math.radians(ang); L = ln * s; w2 = wd * s / 2
                bx, by = x0 + math.sin(a) * 10 * s, y0
                tx, ty = bx + L * math.sin(a), by - L * math.cos(a)
                nx, ny = math.cos(a) * w2, math.sin(a) * w2
                mid = (bx + (tx - bx) * 0.78, by + (ty - by) * 0.78)
                body = [(bx - nx, by - ny), (bx + nx, by + ny), (mid[0] + nx, mid[1] + ny), (tx, ty), (mid[0] - nx, mid[1] - ny)]
                d.polygon(body, fill=hue + (235,))
                d.polygon([(bx, by), (bx + nx, by + ny), (mid[0] + nx, mid[1] + ny), (tx, ty), (mid[0], mid[1])], fill=tuple(min(255, c + 45) for c in hue) + (235,))
                d.line([(bx, by), (mid[0], mid[1]), (tx, ty)], fill=(235, 215, 255, 160), width=1)
        # cartas de tarô espalhadas à frente
        for cx, cy, rot in ((0.17, 0.62, -22), (0.27, 0.70, -6), (0.80, 0.66, 18)):
            cw, ch = 150 * S, 250 * S
            card = Image.new("RGBA", (int(cw), int(ch)), (0, 0, 0, 0)); dd = ImageDraw.Draw(card)
            dd.rounded_rectangle((0, 0, cw - 1, ch - 1), 10, fill=(58, 20, 70, 255), outline=(214, 168, 90, 255), width=3)
            dd.rounded_rectangle((10, 10, cw - 11, ch - 11), 6, outline=(214, 168, 90, 200), width=1)
            r0 = cw * 0.28; ccx, ccy = cw / 2, ch / 2
            dd.ellipse((ccx - r0, ccy - r0, ccx + r0, ccy + r0), outline=(214, 168, 90, 255), width=2)
            dd.ellipse((ccx - r0 * 0.55, ccy - r0 * 0.75, ccx + r0 * 0.75, ccy + r0 * 0.75), fill=(226, 190, 120, 255))
            dd.ellipse((ccx - r0 * 0.35, ccy - r0 * 0.8, ccx + r0 * 0.95, ccy + r0 * 0.7), fill=(58, 20, 70, 255))
            # perspectiva: achata verticalmente
            card = card.rotate(rot, Image.BICUBIC, expand=True)
            card = card.resize((card.width, int(card.height * 0.55)), Image.LANCZOS)
            x = W * cx - card.width / 2; y = hz + cy * (H - hz) - card.height / 2
            sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.split()[3].point(lambda v: int(v * 0.5)))
            self.base.paste(sh, (int(x + 8 * S), int(y + 10 * S)), sh.filter(ImageFilter.GaussianBlur(6)))
            self.base.paste(card, (int(x), int(y)), card)
        # bola de cristal à direita, atrás
        x0, y0, R = W * 0.66, self.hz + 0.02 * (H - self.hz), 62 * S
        d.ellipse((x0 - R * 1.1, y0 - R * 0.25, x0 + R * 1.1, y0 + R * 0.25), fill=(0, 0, 0, 120))
        d.polygon([(x0 - R * 0.8, y0), (x0 + R * 0.8, y0), (x0 + R * 0.55, y0 - R * 0.35), (x0 - R * 0.55, y0 - R * 0.35)], fill=(150, 96, 60, 255))
        ball = Image.new("RGBA", (int(2 * R), int(2 * R)), (0, 0, 0, 0))
        by_, bx_ = np.mgrid[0:ball.height, 0:ball.width].astype(np.float32)
        rr = np.sqrt((bx_ - R) ** 2 + (by_ - R) ** 2) / R
        hl = np.sqrt((bx_ - R * 0.65) ** 2 + (by_ - R * 0.6) ** 2) / R
        colb = np.stack([110 + 120 * np.clip(1 - hl, 0, 1), 80 + 100 * np.clip(1 - hl, 0, 1), 170 + 80 * np.clip(1 - hl, 0, 1)], -1)
        alpha = (np.clip((1 - rr) * 40, 0, 1) * 220)
        ball = Image.fromarray(np.dstack([np.clip(colb, 0, 255), alpha]).astype(np.uint8), "RGBA")
        self.base.paste(ball, (int(x0 - R), int(y0 - R * 0.35 - 2 * R + 6)), ball)
        self.ball = (x0, y0 - R * 0.35 - R + 6, R)

    # ---------- por quadro ----------
    def frame(self, t, circle_a=0.0, circle_c=None, circle_scale=1.0):
        W, H = self.W, self.H
        img = self.base.copy()
        # chamas das velas + brilho
        glow = Image.new("RGB", (W // 4, H // 4), 0); dg = ImageDraw.Draw(glow)
        d = ImageDraw.Draw(img, "RGBA")
        for i, (x, y, wd) in enumerate(self.candles):
            fl = 1 + 0.12 * math.sin(t * 13 + i * 2.1) + 0.08 * math.sin(t * 7.3 + i)
            sway = 3 * math.sin(t * 5 + i)
            hgt = wd * 0.9 * fl; wdt = wd * 0.32
            d.ellipse((x - wdt + sway * 0.3, y - hgt, x + wdt + sway * 0.3, y + wdt * 0.6), fill=(255, 170, 60, 230))
            d.ellipse((x - wdt * 0.55 + sway * 0.5, y - hgt * 0.75, x + wdt * 0.55 + sway * 0.5, y + wdt * 0.4), fill=(255, 236, 170, 255))
            R = wd * 3.2 * fl / 4
            dg.ellipse((x / 4 - R, (y - hgt / 2) / 4 - R, x / 4 + R, (y - hgt / 2) / 4 + R), fill=(255, 150, 60))
        bx, by, bR = self.ball
        pr = bR / 4 * (1.6 + 0.2 * math.sin(t * 1.7))
        dg.ellipse((bx / 4 - pr, by / 4 - pr, bx / 4 + pr, by / 4 + pr), fill=(150, 90, 255))
        glow = glow.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
        arr = np.asarray(img, np.float32) + np.asarray(glow, np.float32) * 0.55
        # círculo mágico girando atrás do produto
        if circle_a > 0.01 and circle_c is not None:
            D = int(self.circle.width * circle_scale)
            c = self.circle.rotate(t * 9, Image.BICUBIC).resize((D, D), Image.BILINEAR)
            a = np.zeros((H, W), np.float32)
            cx, cy = circle_c
            x0, y0 = int(cx - D / 2), int(cy - D / 2)
            ca = np.asarray(c.split()[3], np.float32) / 255
            cg = np.asarray(c.split()[3].filter(ImageFilter.GaussianBlur(8)), np.float32) / 255
            xs0, ys0 = max(0, x0), max(0, y0); xs1, ys1 = min(W, x0 + D), min(H, y0 + D)
            if xs1 > xs0 and ys1 > ys0:
                sub = ca[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]; subg = cg[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
                col = np.array(GOLD, np.float32)
                pulse = 0.75 + 0.25 * math.sin(t * 2.4)
                arr[ys0:ys1, xs0:xs1] += (sub[..., None] * 0.85 + subg[..., None] * 1.1) * col * circle_a * pulse
        # partículas (estrelas na parede + poeira dourada/cobre subindo)
        lay = Image.new("RGB", (W // 2, H // 2), 0); dl = ImageDraw.Draw(lay)
        for x, y, s, ph, sp in self.stars:
            v = int(220 * (0.45 + 0.55 * math.sin(ph + t * sp)) ** 2)
            if v > 8: dl.ellipse((x / 2 - s / 2, y / 2 - s / 2, x / 2 + s / 2, y / 2 + s / 2), fill=(v, v, min(255, v + 25)))
        for x, y, s, sp, ph, cop in self.dust:
            y_ = (y - t * sp) % H; x_ = x + 16 * math.sin(t * 0.7 + ph); a = 0.5 + 0.5 * math.sin(t * 2 + ph)
            col = COPPER if cop else GOLD
            dl.ellipse((x_ / 2 - s / 2, y_ / 2 - s / 2, x_ / 2 + s / 2, y_ / 2 + s / 2), fill=tuple(int(c * a) for c in col))
        lay = ImageChops.add(lay, lay.filter(ImageFilter.GaussianBlur(3)))
        arr += np.asarray(lay.resize((W, H), Image.BILINEAR), np.float32)
        return arr
