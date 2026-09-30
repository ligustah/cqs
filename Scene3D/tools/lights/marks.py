"""Count visible warm/amber light marks on a studio render (ship mode: blue-grey backdrop).

usage: blender-venv/bin/python marks.py a.png [b.png ...]
prints: marks (connected lit blobs, amber lamps + warm windows), hull pixels (B/R < 1.35 mask),
marks per 10k hull px and the mean on-screen spacing between marks (sqrt(hull px / marks)).
A relative metric: compare renders of the same query before/after, and classes against each other.
White and cool lights (nav, strobes, drive status) are not counted.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def run(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    hull = B / np.maximum(R, 1) < 1.35
    hull = ndimage.binary_opening(hull, iterations=2)
    hull = ndimage.binary_fill_holes(ndimage.binary_closing(hull, iterations=4))
    hull = ndimage.binary_opening(hull, iterations=4)
    bg = ndimage.uniform_filter(L, 15)
    warm = (L - bg > 25) & (L > 90) & (R > B + 25)
    _, n = ndimage.label(warm)
    return n, int(hull.sum())


for p in sys.argv[1:]:
    n, area = run(p)
    print(f"{p.split('/')[-1]:26s} marks {n:5d} hullpx {area:8d} per10kpx {n / max(area, 1) * 1e4:6.1f} spacing_px {np.sqrt(area / max(n, 1)):6.1f}")
