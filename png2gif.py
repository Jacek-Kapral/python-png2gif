from pathlib import Path

from PIL import Image

T = 255  # indeks przezroczystości


def _to_p_frame(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    w, h = img.size
    rgb = img.convert("RGB")
    alpha = img.split()[3]
    p = rgb.quantize(colors=255, method=Image.ADAPTIVE)
    pal = bytearray((p.getpalette() or [0] * 768)[: 765])
    pal.extend((0, 0, 0))
    data = list(p.getdata())
    a_list = list(alpha.getdata())
    for i in range(len(data)):
        a = a_list[i]
        if (a[0] if isinstance(a, (tuple, list)) else a) < 128:
            data[i] = T
    out = Image.new("P", (w, h))
    out.putpalette(pal)
    out.putdata(data)
    out.info["transparency"] = T
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
        raise FileNotFoundError(f"Brak .png w: {source_dir}")

    frames = [_to_p_frame(Image.open(f).convert("RGBA")) for f in files]
    frames[0].save(
        output_path, format="GIF", save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=loop, transparency=T, disposal=2,
    )
    return output_path


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    d = Path(args[0]) if args else Path.cwd()
    out = None
    if len(args) > 1 and not args[1].replace(".", "", 1).isdigit():
        out = Path(args[1])
    dur = 100
    if len(args) > 1 and args[1].replace(".", "", 1).isdigit():
        dur = int(args[1])
    if len(args) > 2 and args[2].replace(".", "", 1).isdigit():
        dur = int(args[2])
    print(pngs_to_gif(d, out, duration_ms=dur))
