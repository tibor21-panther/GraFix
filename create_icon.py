"""
GraFix lakat ikon generátor.
Futtatás: python create_icon.py
Kimenet:  assets/icon.ico  (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
"""
from pathlib import Path
from PIL import Image, ImageDraw

SIZES   = [256, 128, 64, 48, 32, 16]
OUT_DIR = Path(__file__).parent / "assets"
OUT_ICO = OUT_DIR / "icon.ico"
BG      = (0, 120, 212, 255)   # Windows-kék (#0078d4)
FG      = (255, 255, 255, 255) # fehér


def draw_lock(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    m  = size / 256           # méretarány

    # ── Háttérkör ─────────────────────────────────────────────────────────
    pad = int(6 * m)
    draw.ellipse([pad, pad, size - pad, size - pad], fill=BG)

    # ── Lakat test (lekerekített téglalap) ────────────────────────────────
    bx0 = int(68 * m);  bx1 = int(188 * m)
    by0 = int(118 * m); by1 = int(202 * m)
    r   = int(14 * m)
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=r, fill=FG)

    # ── Lakat ív (felső rész) ─────────────────────────────────────────────
    ax0 = int(82 * m);  ax1 = int(174 * m)
    ay0 = int(62 * m);  ay1 = int(150 * m)
    arc_w = max(1, int(18 * m))
    draw.arc([ax0, ay0, ax1, ay1], start=200, end=340, fill=FG, width=arc_w)

    # ── Kulcslyuk (kör + kis téglalap) ───────────────────────────────────
    cx = size // 2
    kr = max(2, int(14 * m))
    draw.ellipse([cx - kr, int(138 * m) - kr,
                  cx + kr, int(138 * m) + kr], fill=BG)

    kw = max(2, int(9 * m));  kh = max(2, int(18 * m))
    draw.rectangle([cx - kw, int(148 * m),
                    cx + kw, int(148 * m) + kh], fill=BG)

    return img


def main():
    OUT_DIR.mkdir(exist_ok=True)
    frames = [draw_lock(s) for s in SIZES]

    # PIL ico mentés: az első frame az elsődleges, a többi méretek
    frames[0].save(
        OUT_ICO,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Ikon elkészült: {OUT_ICO}")


if __name__ == "__main__":
    main()
