# Grit and mood check of a colony building render against its concept (BUILDING-GUIDE.md section 9, rows G0 / M1):
#   python3 tools/buildings/grit-check.py <concept.jpg> <render.png> <regions.json>
# regions.json: {"concept": {"name": [x0, y0, x1, y1], ...}, "render": {"name": [...], ...}} in fractions of each
# image (the same surfaces: e.g. tower shell, shed wall, roof, plinth). Both images are resized to 1152 px wide first
# (the concept's size), so the measures compare at one scale. Per region it prints the luminance std (tonal variation:
# panels, stains, streaks) and the high-pass energy (std of the luminance minus its 3 px Gaussian blur: fine grit), and
# the render / concept ratios; target 0.8-1.2x. Mood: the darkest 20 % of the building's pixels (GrabCut mask, as
# paint-check.py), mean luminance p5-p20 of render vs concept (shadow side; target 0.8-1.2x).
# Prints JSON.
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

L = np.array([0.2126, 0.7152, 0.0722])


def load(path, W=1152):
    im = Image.open(path).convert('RGB')
    h = round(im.height * W / im.width)
    return im.resize((W, h), Image.LANCZOS)


def lum(im):
    return np.asarray(im).astype(float) @ L / 255.0


def region(im, box):
    w, h = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    y = lum(c)
    hp = y - lum(c.filter(ImageFilter.GaussianBlur(3)))
    return {'mean': round(float(y.mean()), 4), 'std': round(float(y.std()), 4), 'hp': round(float(hp.std()), 4)}


def shadow(im):
    import cv2
    a = np.asarray(im)
    H, W = a.shape[:2]
    mk = np.zeros((H, W), np.uint8)
    bm, fm = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(a[..., ::-1].copy(), mk, (int(W * 0.03), int(H * 0.03), int(W * 0.94), int(H * 0.94)), bm, fm, 5, cv2.GC_INIT_WITH_RECT)
    m = (mk == cv2.GC_FGD) | (mk == cv2.GC_PR_FGD)
    y = lum(im)[m]
    lo, hi = np.percentile(y, 5), np.percentile(y, 20)
    return round(float(y[(y >= lo) & (y <= hi)].mean()), 4)


def main():
    cpath, rpath, rj = sys.argv[1:4]
    R = json.load(open(rj))
    ci, ri = load(cpath), load(rpath)
    out = {'regions': {}}
    for name, box in R['concept'].items():
        c = region(ci, box)
        r = region(ri, R['render'][name])
        out['regions'][name] = {'concept': c, 'render': r, 'std_ratio': round(r['std'] / max(c['std'], 1e-6), 2),
                                'hp_ratio': round(r['hp'] / max(c['hp'], 1e-6), 2), 'mean_ratio': round(r['mean'] / max(c['mean'], 1e-6), 2)}
    cs, rs = shadow(ci), shadow(ri)
    out['shadow'] = {'concept': cs, 'render': rs, 'ratio': round(rs / max(cs, 1e-6), 2)}
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
