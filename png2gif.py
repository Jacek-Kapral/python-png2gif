"""PNGi z katalogu → animowany GIF (po nazwie, z przezroczystością)."""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise ImportError("Wymagana biblioteka Pillow: pip install Pillow")

TRANSPARENT_IDX = 255


def _to_p_transparent(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    w, h = img.size
    rgb = img.convert("RGB")
    alpha = img.split()[3]
    p = rgb.convert("P", palette=Image.ADAPTIVE, colors=255)
    pal = bytearray(p.getpalette() or [0] * 768)
    pal.extend((0, 0, 0))
    p.putpalette(pal)
    data, ad = list(p.getdata()), list(alpha.getdata())
    for i in range(len(data)):
        if ad[i] < 128:
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
) -> Path:
    source_dir = Path(source_dir)
    output_path = Path(output_path) if output_path else source_dir / "anim.gif"
    files = sorted(source_dir.glob("*.png"))
    if not files:
        raise FileNotFoundError(f"Brak plików .png w: {source_dir}")
    frames = [_to_p_transparent(Image.open(f).convert("RGBA")) for f in files]
    frames[0].save(
        output_path, format="GIF", save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=loop, transparency=TRANSPARENT_IDX, disposal=2,
    )
    return output_path


if __name__ == "__main__":
    import sys
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    dur = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    print(pngs_to_gif(d, out, duration_ms=dur))
