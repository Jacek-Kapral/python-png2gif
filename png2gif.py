"""PNGi z katalogu → animowany GIF. Tryb: per_frame (własna paleta każdej klatki) lub global (jedna paleta)."""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise ImportError("Wymagana biblioteka Pillow: pip install Pillow")

TRANSPARENT_IDX = 255


def _rgba_to_p_single_frame(img: Image.Image) -> Image.Image:
    """Jedna klatka RGBA → P z własną paletą 255 kolorów + przezroczysty. Bez globalnej palety."""
    img = img.convert("RGBA")
    w, h = img.size
    rgb = img.convert("RGB")
    alpha = img.split()[3]
    p = rgb.quantize(colors=255, method=Image.ADAPTIVE)
    pal = bytearray((p.getpalette() or [0] * 768)[: 255 * 3])
    pal.extend((0, 0, 0))
    data = list(p.getdata())
    alpha_list = list(alpha.getdata())
    a_val = lambda a: (a[0] if isinstance(a, (tuple, list)) else a)
    for i in range(len(data)):
        if a_val(alpha_list[i]) < 128:
            data[i] = TRANSPARENT_IDX
    out = Image.new("P", (w, h))
    out.putpalette(pal)
    out.putdata(data)
    out.info["transparency"] = TRANSPARENT_IDX
    return out


def pngs_to_gif(
    source_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    duration_ms: int = 100,
    loop: int = 0,
    per_frame_palette: bool = True,
) -> Path:
    """
    per_frame_palette=True: każda klatka ma własną paletę (do 255 kolorów) – „sklejka” bez utraty kolorów.
    per_frame_palette=False: jedna wspólna paleta (stary tryb).
    """
    source_dir = Path(source_dir)
    output_path = Path(output_path) if output_path else source_dir / "anim.gif"
    files = sorted(source_dir.glob("*.png"))
    if not files:
        raise FileNotFoundError(f"Brak plików .png w: {source_dir}")

    if per_frame_palette:
        frames = [_rgba_to_p_single_frame(Image.open(f).convert("RGBA")) for f in files]
    else:
        images = [Image.open(f).convert("RGBA") for f in files]
        pal = _build_global_palette([im.convert("RGB") for im in images])
        frames = [_frame_to_p(im, pal) for im in images]

    frames[0].save(
        output_path, format="GIF", save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=loop, transparency=TRANSPARENT_IDX, disposal=2,
    )
    return output_path


def _build_global_palette(images_rgb: list) -> bytearray:
    unique = set()
    for im in images_rgb:
        flat = list(im.get_flattened_data())
        if flat and isinstance(flat[0], (tuple, list)):
            for rgb in flat:
                unique.add((int(rgb[0]), int(rgb[1]), int(rgb[2])))
        else:
            for i in range(0, len(flat), 3):
                unique.add((int(flat[i]), int(flat[i + 1]), int(flat[i + 2])))
    unique_list = list(unique)
    if len(unique_list) <= 255:
        flat = []
        for r, g, b in unique_list:
            flat.extend((r, g, b))
        flat += [0, 0, 0] * (255 - len(unique_list))
        return bytearray(flat[: 255 * 3])
    img_1d = Image.new("RGB", (len(unique_list), 1))
    img_1d.putdata(unique_list)
    q = img_1d.quantize(colors=255, method=Image.MEDIANCUT)
    raw = (q.getpalette() or [0] * 768)[: 255 * 3]
    return bytearray(raw + [0] * (255 * 3 - len(raw)))


def _nearest_idx(pal: bytearray, r: int, g: int, b: int) -> int:
    n = min(255, len(pal) // 3)
    best, best_d = 0, 1e9
    for i in range(n):
        d = (pal[3 * i] - r) ** 2 + (pal[3 * i + 1] - g) ** 2 + (pal[3 * i + 2] - b) ** 2
        if d < best_d:
            best_d, best = d, i
    return best


def _frame_to_p(img: Image.Image, pal: bytearray) -> Image.Image:
    img = img.convert("RGBA")
    w, h = img.size
    rgb_seq = list(img.convert("RGB").get_flattened_data())
    alpha_seq = list(img.split()[3].get_flattened_data())
    n_pix = w * h
    if rgb_seq and isinstance(rgb_seq[0], (tuple, list)):
        R = [float(int(rgb_seq[p][0])) for p in range(n_pix)]
        G = [float(int(rgb_seq[p][1])) for p in range(n_pix)]
        B = [float(int(rgb_seq[p][2])) for p in range(n_pix)]
    else:
        R = [float(int(rgb_seq[3 * p])) for p in range(n_pix)]
        G = [float(int(rgb_seq[3 * p + 1])) for p in range(n_pix)]
        B = [float(int(rgb_seq[3 * p + 2])) for p in range(n_pix)]
    a_val = lambda i: int(alpha_seq[i][0]) if isinstance(alpha_seq[i], (tuple, list)) else int(alpha_seq[i])
    data = [0] * n_pix
    for p in range(n_pix):
        if a_val(p) < 128:
            data[p] = TRANSPARENT_IDX
            continue
        r, g, b = R[p], G[p], B[p]
        idx = _nearest_idx(pal, int(round(r)), int(round(g)), int(round(b)))
        data[p] = idx
        pr, pg, pb = pal[3 * idx], pal[3 * idx + 1], pal[3 * idx + 2]
        er, eg, eb = r - pr, g - pg, b - pb
        x, y = p % w, p // w
        if x + 1 < w:
            R[p + 1] += er * 7 / 16
            G[p + 1] += eg * 7 / 16
            B[p + 1] += eb * 7 / 16
        if y + 1 < h:
            if x > 0:
                R[p + w - 1] += er * 3 / 16
                G[p + w - 1] += eg * 3 / 16
                B[p + w - 1] += eb * 3 / 16
            R[p + w] += er * 5 / 16
            G[p + w] += eg * 5 / 16
            B[p + w] += eb * 5 / 16
            if x + 1 < w:
                R[p + w + 1] += er * 1 / 16
                G[p + w + 1] += eg * 1 / 16
                B[p + w + 1] += eb * 1 / 16
    out = Image.new("P", (w, h))
    full_pal = bytearray(pal)
    full_pal.extend((0, 0, 0))
    out.putpalette(full_pal)
    out.putdata(data)
    out.info["transparency"] = TRANSPARENT_IDX
    return out


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if a != "--global"]
    d = Path(args[0]) if args else Path.cwd()
    out = Path(args[1]) if len(args) > 1 else None
    dur = int(args[2]) if len(args) > 2 else 100
    per_frame = "--global" not in sys.argv
    print(pngs_to_gif(d, out, duration_ms=dur, per_frame_palette=per_frame))
