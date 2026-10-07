"""wxprep.py <download_dir> <out_dir>: the downloaded PATINA maps (basecolor/roughness/height PNGs, untrusted) ->
the weathering library set: base.png (RGB 2048), rough.png (L), height.png (L), stats.json. Run with python3 -I."""
import json
import os
import sys

from PIL import Image

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
Image.MAX_IMAGE_PIXELS = 80_000_000
stats = {}
for kind, name, mode in (('basecolor', 'base.png', 'RGB'), ('roughness', 'rough.png', 'L'), ('height', 'height.png', 'L'), ('normal', 'normal.png', 'RGB')):
    p = os.path.join(src, kind + '.png')
    if not os.path.exists(p):
        continue
    im = Image.open(p)
    im.load()
    im = im.convert(mode)
    if im.width > 2048:
        im = im.resize((2048, 2048), Image.LANCZOS)
    im.save(os.path.join(out, name), optimize=True)
    stats[kind] = {'size': im.size}
json.dump(stats, open(os.path.join(out, 'stats.json'), 'w'), indent=1)
print(out, stats)
