"""Cena mística celta: floresta verde com névoa, raios de luz, vaga-lumes,
folhas de carvalho caindo e um círculo de símbolos celtas (triquetra, trisquel, ogham) girando."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

GREEN = (120, 255, 150)
PALE_GREEN = (190, 255, 200)


def _arc_pts(cx, cy, r, a0, a1, n=60):
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def triquetra(size, col=(170, 255, 180), width=None):
    """Triquetra verdadeira: arcos de cada círculo só onde ficam dentro de outro círculo."""
    S = size * 3; w = int((width or size * 0.06) * 3); c = S / 2; R = S * 0.30; off = R * 0.58
    cs = []
    for k in range(3):
        ang = -math.pi / 2 + k * 2 * math.pi / 3; cs.append((c + off * math.cos(ang), c + off * math.sin(ang)))
    out = Image.new("L", (S, S), 0)
    for k, (cx, cy) in enumerate(cs):
        ring = Image.new("L", (S, S), 0); ImageDraw.Draw(ring).ellipse((cx - R, cy - R, cx + R, cy + R), outline=255, width=w)
        m = Image.new("L", (S, S), 0); md = ImageDraw.Draw(m)
        for j, (ox, oy) in enumerate(cs):
            if j != k: md.ellipse((ox - R + w * 0.15, oy - R + w * 0.15, ox + R - w * 0.15, oy + R - w * 0.15), fill=255)
        from PIL import ImageChops
        out = ImageChops.lighter(out, ImageChops.multiply(ring, m))
    d = ImageDraw.Draw(out); rc = off * 1.05
    d.ellipse((c - rc, c - rc, c + rc, c + rc), outline=255, width=max(2, int(w * 0.7)))
    im = Image.new("RGBA", (S, S), col + (0,)); im.putalpha(out)
    return im.resize((size, size), Image.LANCZOS)


def triskele(size, col=(170, 255, 180)):
    S = size * 3; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2; w = int(S * 0.035)
    for k in range(3):
        base = k * 2 * math.pi / 3; pts = []
        for t in np.linspace(0, 1, 140):
            r = S * 0.04 + S * 0.36 * t; a = base + t * 3.4 * math.pi / 2
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.line(pts, fill=col + (255,), width=w, joint="curve")
    d.ellipse((c - S * 0.05, c - S * 0.05, c + S * 0.05, c + S * 0.05), fill=col + (255,))
    return im.resize((size, size), Image.LANCZOS)


def ogham_ring(size, col=(150, 245, 170), seed=3):
    """Anel com linhas de ogham, nós celtas pontilhados e trisquéis."""
    rng = np.random.default_rng(seed)
    S = size * 2; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2; R1, R2 = S * 0.47, S * 0.41; w = max(2, int(S * 0.004))
    for R in (R1, R2, S * 0.30):
        d.ellipse((c - R, c - R, c + R, c + R), outline=col + (230,), width=w)
    # traços de ogham entre R2 e R1
    mid = (R1 + R2) / 2; n = 72
    d.ellipse((c - mid, c - mid, c + mid, c + mid), outline=col + (160,), width=max(1, w // 2))
    for i in range(n):
        if i % 12 == 0: continue
        a = i * 2 * math.pi / n; k = rng.integers(1, 5); side = rng.choice([-1, 0, 1])
        for j in range(k):
            aa = a + (j - k / 2) * 0.012
            r0 = mid if side > 0 else (R2 + 4 if side < 0 else R2 + 4)
            r1 = R1 - 4 if side >= 0 else mid
            d.line([(c + r0 * math.cos(aa), c + r0 * math.sin(aa)), (c + r1 * math.cos(aa), c + r1 * math.sin(aa))], fill=col + (230,), width=w)
    # trisquéis pequenos nos 6 pontos
    tk = triskele(int(S * 0.07), col)
    for i in range(6):
        a = i * math.pi / 3; x, y = c + mid * math.cos(a), c + mid * math.sin(a)
        im.alpha_composite(tk, (int(x - tk.width / 2), int(y - tk.height / 2)))
    # nó em espiral entre R2 e 0.30 (pontos)
    for i in range(240):
        a = i * 2 * math.pi / 240; rr = S * 0.355 + S * 0.03 * math.sin(a * 12)
        d.ellipse((c + rr * math.cos(a) - w, c + rr * math.sin(a) - w, c + rr * math.cos(a) + w, c + rr * math.sin(a) + w), fill=col + (200,))
        rr2 = S * 0.355 + S * 0.03 * math.sin(a * 12 + math.pi)
        d.ellipse((c + rr2 * math.cos(a) - w, c + rr2 * math.sin(a) - w, c + rr2 * math.cos(a) + w, c + rr2 * math.sin(a) + w), fill=col + (140,))
    return im.resize((size, size), Image.LANCZOS)


def _tree(d, x, base, h, w, col, rng):
    d.polygon([(x - w, base), (x + w, base), (x + w * 0.45, base - h), (x - w * 0.45, base - h)], fill=col)
    for _ in range(int(rng.integers(3, 7))):
        y = base - h * rng.uniform(0.35, 0.95); s = rng.choice([-1, 1]); L = rng.uniform(0.15, 0.4) * h
        x2 = x + s * L * 0.8; y2 = y - L * 0.6
        d.line([(x, y), ((x + x2) / 2, y - L * 0.15), (x2, y2)], fill=col, width=max(2, int(w * 0.35)), joint="curve")


class Floresta:
    def __init__(self, W, H, ground_y, seed=7):
        self.W, self.H, self.gy = W, H, ground_y
        rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
        k = np.clip(r / 0.75, 0, 1)[..., None]
        self.bg = np.array([36, 120, 70], np.float32) * (1 - k) + np.array([3, 20, 12], np.float32) * k
        # camadas de árvores (longe -> perto)
        self.layers = []
        for li, (n, col, blur, hs) in enumerate([(14, (14, 62, 38), 6, 0.75), (10, (8, 38, 24), 3, 0.95), (6, (2, 14, 9), 0, 1.25)]):
            lay = Image.new("RGBA", (int(W * 1.2), H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for i in range(n):
                x = (i + rng.uniform(0.1, 0.9)) * lay.width / n
                if li == 2 and abs(x - lay.width / 2) < W * 0.32: x += np.sign(x - lay.width / 2 + 1e-3) * W * 0.32
                _tree(d, x, ground_y + 40 + li * 30, H * hs * rng.uniform(0.75, 1.05), W * (0.012 + 0.012 * li) * rng.uniform(0.8, 1.3), col + (255,), rng)
            if blur: lay = lay.filter(ImageFilter.GaussianBlur(blur))
            self.layers.append(lay)
        # chão de musgo + pedra (altar)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        for y in range(ground_y, H):
            f = (y - ground_y) / max(1, H - ground_y)
            d.line([(0, y), (W, y)], fill=(int(10 + 20 * (1 - f)), int(45 + 40 * (1 - f)), int(22 + 15 * (1 - f)), 255))
        self.ground = g
        pw = W * 0.62; ph = W * 0.13
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
        cx, cy = W / 2, ground_y + ph * 0.55
        d.ellipse((cx - pw / 2, cy - ph / 2 + 30, cx + pw / 2, cy + ph / 2 + 30), fill=(40, 52, 46, 255))
        for k_ in range(30): d.ellipse((cx - pw / 2, cy - ph / 2 + k_, cx + pw / 2, cy + ph / 2 + k_), fill=(40, 52, 46, 255))
        d.ellipse((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), fill=(78, 98, 86, 255))
        # musgo na borda
        for _ in range(260):
            a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.85, 1.02)
            x = cx + pw / 2 * rr * math.cos(a); y = cy + ph / 2 * rr * math.sin(a) + rng.uniform(0, 26)
            s = rng.uniform(4, 11); d.ellipse((x - s, y - s * 0.6, x + s, y + s * 0.6), fill=(40, int(rng.uniform(90, 140)), 50, 255))
        self.stone = st.filter(ImageFilter.GaussianBlur(1.2)); self.stone_y = cy
        self.ring = ogham_ring(int(W * 0.92))
        self.triq = triquetra(int(W * 0.30))
        self.small = [triskele(70), triquetra(80)]
        self.motes = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 3.5), rng.uniform(0, 6.28), rng.uniform(8, 30)) for _ in range(60)]
        self.leaves = [(rng.uniform(0, W), rng.uniform(-H, H), rng.uniform(10, 20), rng.uniform(0, 6.28), rng.uniform(50, 110)) for _ in range(22)]
        self.floaters = [(rng.uniform(0.05, 0.95) * W, rng.uniform(0.05, 0.7) * H, int(rng.integers(2)), rng.uniform(0, 6.28), rng.uniform(0.5, 1.1)) for _ in range(7)]
        vy, vx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.vig = (1 - 0.55 * np.clip(np.sqrt(((vx - W / 2) / (W * 0.7)) ** 2 + ((vy - H / 2) / (H * 0.7)) ** 2) - 0.25, 0, 1))[..., None]

    def frame(self, t, ring_a=1.0, ring_c=None, ring_scale=1.0):
        W, H = self.W, self.H
        c = Image.fromarray(np.clip(self.bg, 0, 255).astype(np.uint8)).convert("RGBA")
        # raios de luz
        rays = Image.new("L", (W // 2, H // 2), 0); d = ImageDraw.Draw(rays)
        for i in range(5):
            x0 = (0.15 + 0.17 * i) * W / 2 + 20 * math.sin(t * 0.3 + i); a = int(55 + 30 * math.sin(t * 0.7 + i * 1.7))
            d.polygon([(x0, 0), (x0 + 40, 0), (x0 + 160, H / 2), (x0 + 60, H / 2)], fill=a)
        rays = rays.filter(ImageFilter.GaussianBlur(18)).resize((W, H))
        c.paste((200, 255, 190), (0, 0), rays)
        for i, lay in enumerate(self.layers):
            dx = int(-(lay.width - W) / 2 + math.sin(t * 0.15) * (6 + 10 * i))
            c.alpha_composite(lay, (dx, 0))
        # névoa
        fog = Image.new("L", (W // 4, H // 4), 0); d = ImageDraw.Draw(fog)
        for i in range(6):
            x = ((i * 0.22 + t * 0.012 * (1 + i % 3)) % 1.4 - 0.2) * W / 4; y = self.gy / 4 - 10 + 8 * (i % 3)
            d.ellipse((x - 70, y - 14, x + 70, y + 14), fill=90)
        fog = fog.filter(ImageFilter.GaussianBlur(10)).resize((W, H))
        c.paste((150, 210, 170), (0, 0), fog)
        c.alpha_composite(self.ground)
        # círculo celta girando
        if ring_a > 0.01:
            cx, cy = ring_c or (W / 2, H * 0.45)
            sz = int(self.ring.width * ring_scale)
            r = self.ring.resize((sz, sz), Image.BILINEAR).rotate(t * 6, Image.BICUBIC)
            q = self.triq.rotate(-t * 10, Image.BICUBIC)
            for im_, a_ in ((r, ring_a * (0.75 + 0.25 * math.sin(t * 1.3))), (q, ring_a * 0.8)):
                al = im_.split()[3]
                g = al.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(min(255, v * 1.6) * a_))
                c.paste(GREEN, (int(cx - im_.width / 2), int(cy - im_.height / 2)), g)
                al2 = al.point(lambda v: int(v * a_))
                c.paste(PALE_GREEN, (int(cx - im_.width / 2), int(cy - im_.height / 2)), al2)
        # símbolos flutuando
        for x, y, k, ph, sp in self.floaters:
            s = self.small[k]; a = 0.25 + 0.25 * math.sin(t * sp + ph)
            yy_ = y + 25 * math.sin(t * 0.5 + ph); rim = s.rotate(t * 20 * sp, Image.BICUBIC)
            al = rim.split()[3].point(lambda v: int(v * a))
            c.paste(PALE_GREEN, (int(x - rim.width / 2), int(yy_ - rim.height / 2)), al)
        c.alpha_composite(self.stone)
        return c

    def overlay(self, c, t):
        """Vaga-lumes e folhas por cima do produto."""
        W, H = self.W, self.H
        d = ImageDraw.Draw(c, "RGBA")
        for x, y, s, ph, sp in self.motes:
            x_ = x + 30 * math.sin(t * 0.4 + ph); y_ = (y - t * sp) % H
            a = int(110 + 100 * math.sin(t * 2.2 + ph))
            d.ellipse((x_ - s * 2.5, y_ - s * 2.5, x_ + s * 2.5, y_ + s * 2.5), fill=(190, 255, 120, max(0, a // 6)))
            d.ellipse((x_ - s, y_ - s, x_ + s, y_ + s), fill=(230, 255, 170, max(0, a)))
        for x, y, s, ph, sp in self.leaves:
            y_ = (y + t * sp) % (H + 200) - 100; x_ = x + 60 * math.sin(t * 0.9 + ph)
            ang = t * 1.5 + ph; dx, dy = s * math.cos(ang), s * 0.45 * math.sin(ang)
            d.polygon([(x_ - dx, y_ - dy), (x_ + dy * 0.5, y_ - s * 0.35), (x_ + dx, y_ + dy), (x_ - dy * 0.5, y_ + s * 0.35)], fill=(70, 140, 50, 190))
        return c
