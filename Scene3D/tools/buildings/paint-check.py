# Paint check of a colony building render against its concept (README-colony.md "Paint calibration"):
#   python3 tools/buildings/paint-check.py <concept.jpg> <render.png>      (python with numpy, pillow, opencv)
# Both are resized to 768 x 512 and masked with GrabCut (the frame border seeds the backdrop); inside the mask the
# light band (p70-97 of luminance: the light paint), the mid band (p35-70) and all (p2-98) give the mean linear
# luminance Y, the mean colour (sRGB), its hue and saturation. Prints JSON {concept, render}. Target: render light Y
# within about 0.9-1.1x of the concept's, hue within ~10 degrees when sat > 0.05.
import sys, json, numpy as np
from PIL import Image
L = np.array([0.2126, 0.7152, 0.0722])
def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2s(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)
def stats(path, W=768, H=512):
    a = np.asarray(Image.open(path).convert('RGB').resize((W, H))).astype(float) / 255
    # backdrop per row from the outer 6 % columns; mask = pixels > 0.09 off it (sum abs, sRGB)
    # the building mask: GrabCut seeded with the frame border as backdrop (a radial slate gradient in both the
    # concepts and the dusk studio), 5 iterations at 768 x 512
    import cv2
    bgr = (a[..., ::-1] * 255).astype(np.uint8)
    mk = np.zeros((H, W), np.uint8)
    bm, fm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mk, (int(W * 0.03), int(H * 0.03), int(W * 0.94), int(H * 0.94)), bm, fm, 5, cv2.GC_INIT_WITH_RECT)
    m = (mk == cv2.GC_FGD) | (mk == cv2.GC_PR_FGD)
    px = a[m]; lin = s2l(px); Y = lin @ L
    out = {}
    for name, lo, hi in (('light', 70, 97), ('mid', 35, 70), ('all', 2, 98)):
        sel = (Y >= np.percentile(Y, lo)) & (Y <= np.percentile(Y, hi))
        mean = lin[sel].mean(0); s = l2s(mean)
        mx, mn = s.max(), s.min()
        r, g, b = s
        hue = (np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360)
        out[name] = dict(Y=round(float(mean @ L), 4), srgb=[int(round(v * 255)) for v in s], hue=round(float(hue), 1), sat=round(float((mx - mn) / max(mx, 1e-4)), 3))
    out['cover'] = round(float(m.mean()), 3)
    return out
if __name__ == '__main__':
    c, r = stats(sys.argv[1]), stats(sys.argv[2])
    print(json.dumps({'concept': c, 'render': r}))
