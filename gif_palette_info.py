"""Wypisuje liczbę kolorów w palecie i unikalnych pikseli w pliku GIF lub PNG."""

import sys
from pathlib import Path

from PIL import Image


def main(path: str | Path) -> None:
    path = Path(path)
    if not path.exists():
        print(f"Nie znaleziono: {path}")
        return
    img = Image.open(path)
    if img.mode == "P":
        pal = img.getpalette()
        n_slots = (len(pal) // 3) if pal else 0
        flat = list(img.get_flattened_data())
        _idx = lambda x: int(x[0]) if isinstance(x, (tuple, list)) else int(x)
        unique_idx = len(set(_idx(x) for x in flat))
        print(f"{path.name}: tryb P, slotów w palecie: {n_slots}, unikalnych indeksów w pikselach: {unique_idx}")
        if hasattr(img, "n_frames") and img.n_frames > 1:
            for i in range(img.n_frames):
                img.seek(i)
                flat = list(img.get_flattened_data())
                print(f"  klatka {i}: unikalnych indeksów: {len(set(_idx(x) for x in flat))}")
    else:
        flat = list(img.get_flattened_data())
        if flat and isinstance(flat[0], (tuple, list)):
            unique = len(set(tuple(int(x) for x in row) for row in flat))
        else:
            ch = 4 if img.mode == "RGBA" else 3
            n = len(flat) // ch
            unique = len(set(tuple(int(flat[ch * p + c]) for c in range(ch)) for p in range(n)))
        print(f"{path.name}: tryb {img.mode}, unikalnych kolorów: {unique}")


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else None
    if not p:
        print("Użycie: python gif_palette_info.py <ścieżka do GIF lub PNG>")
        sys.exit(1)
    main(p)
