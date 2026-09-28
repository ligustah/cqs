"""Texture-space paint for the remodelled hulls: base colour + ORM from the baked maps.

    base_png, orm_png = paint(maps, spec, out)      (numpy + pillow; no Blender needed)

maps (common.bake_maps, rows top-down, 4096^2 unless noted): pos (ship frame, m), nrm (ship
frame, true normal), zone (int, -1 = empty), ao (2048^2), curv (2048^2, 1 - n_bevel . n).

The base colour is LIGHT PAINT on purpose: the runtime livery (src/lib/livery.js 'dark') repaints
neutral texels to the dark operational grey, keeping their luminance variation (compressed), and
keeps a hint of the hue of saturated markings. So everything that should read on the dark hull is
luminance: plate-to-plate tone, seams, grime, AO, edge wear, decals.

Layers, in order (all in the SHIP FRAME, so they line up with the geometry and with the runtime
PATINA detail layer, which samples the same hull set tri-planar at the same tile):
  1. zone base colours (spec['zones']: sRGB paint per material zone)
  2. structural plating: seam planes (spec['seams']: frames along z, bands along y, strakes along
     x) drawn where the surface crosses them; bands are staggered like real plating; every panel
     cell gets its own tone (+-tone)
  3. PATINA plate tone: the hull set's height map, tri-planar at spec['patina']['tile'] m
  4. AO (grime in the creases) and curvature edge wear (lighter, slightly metallic)
  5. low-frequency weathering noise, vertical streaks on walls
  6. decals (spec['decals']): hull number stencils, colour bands, hazard stripes, marks, each a
     box in the ship frame with a facing test, like hulltex.py features
ORM: R = 1, G = roughness, B = metalness.
"""
import math
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def srgb2lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hash3(i, j, k, seed=0):
    h = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / 0xFFFFFF


def vnoise(p, seed=0):
    """3D value noise, p (N, 3) -> (N,) in 0..1."""
    f = np.floor(p).astype(np.int64)
    t = p - f
    t = t * t * (3 - 2 * t)
    out = np.zeros(len(p), np.float32)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                out += w * hash3(f[:, 0] + dx, f[:, 1] + dy, f[:, 2] + dz, seed)
    return out


def fbm(p, scale, octaves=3, seed=0):
    a, s, tot, acc = 1.0, scale, 0.0, 0.0
    for o in range(octaves):
        acc = acc + a * vnoise(p * s, seed + o)
        tot += a
        a *= 0.5; s *= 2.0
    return acc / tot


def upsample(a, size):
    im = Image.fromarray(a.astype(np.float32), mode='F').resize((size, size), Image.BILINEAR)
    return np.asarray(im, np.float32)


def triplanar(img, pos, nrm, tile):
    """As hulltex.triplanar / src/lib/patina.js (flipY)."""
    Hh, Ww = img.shape[:2]
    p = pos / tile
    w = np.abs(nrm) ** 6
    w /= np.maximum(w.sum(-1, keepdims=True), 1e-9)

    def samp(u, v):
        x = (u % 1) * Ww - 0.5; y = (v % 1) * Hh - 0.5
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
        x0 %= Ww; y0 %= Hh; x1 = (x0 + 1) % Ww; y1 = (y0 + 1) % Hh
        return img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy) + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy
    return samp(p[..., 2], 1 - p[..., 1]) * w[..., 0] + samp(p[..., 0], 1 - p[..., 2]) * w[..., 1] + samp(p[..., 0], 1 - p[..., 1]) * w[..., 2]


# ------------------------------------------------------------------------------------------
# seams
# ------------------------------------------------------------------------------------------
def nearest(v, lines):
    L = np.asarray(sorted(lines), np.float32)
    i = np.clip(np.searchsorted(L, v), 1, len(L) - 1)
    return np.minimum(np.abs(v - L[i - 1]), np.abs(v - L[i])), i


def seams(pos, nrm, cfg):
    """Seam distance and panel ids per texel, in each face's own frame so seams run straight on
    every facet. Decks and the belly (|n.y| >= 0.9) are cut by strakes (|x|) and frames (z,
    staggered per strake); every other face (walls, chamfers, sloped glacis, end plates) by
    horizontal bands (y) and frames along the face's horizontal direction h = Y x n (staggered
    per band), so on a sloped facet the frames run straight down the slope."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    w = cfg.get('width', 0.08)
    frames = np.asarray(cfg['frames'], np.float32)
    bands = cfg['bands']
    strakes = cfg['strakes']
    wall = np.abs(nrm[:, 1]) < 0.9
    # horizontal in-face direction, oriented forward (or to port on end plates)
    hx, hz = nrm[:, 2], -nrm[:, 0]
    hl = np.maximum(np.hypot(hx, hz), 1e-6)
    hx, hz = hx / hl, hz / hl
    flip = np.where(np.abs(hz) > 0.3, hz < 0, hx < 0)
    hx = np.where(flip, -hx, hx); hz = np.where(flip, -hz, hz)
    sw = x * hx + z * hz
    dy, bi = nearest(y, bands)
    stag = np.where(bi % 2 == 0, 0.0, cfg.get('stagger', 2.4)).astype(np.float32)
    dz, fi = nearest(sw + stag, frames)
    dx, si = nearest(np.abs(x), strakes)
    stag2 = np.where(si % 2 == 0, 0.0, cfg.get('stagger', 2.4)).astype(np.float32)
    dz2, fi2 = nearest(z + stag2, frames)
    d = np.where(wall, np.minimum(dy, dz), np.minimum(dx, dz2))
    pid = np.where(wall, bi * 1000 + fi, 50000 + si * 1000 + fi2) + (x > 0) * 100000
    endface = np.zeros(len(x), bool)
    z_wall = sw
    # access panels: some plating cells carry a smaller bolted panel (outline only), placed and
    # sized by the cell's hash; walls use (z, y) cell coordinates, decks (z, |x|)
    ap = cfg.get('access', 0.0)
    d_acc = np.full(len(x), 1e3, np.float32)
    if ap > 0:
        L = np.asarray(sorted(frames), np.float32)
        B = np.asarray(sorted(bands), np.float32)
        St = np.asarray(sorted(strakes), np.float32)
        for mask, a, ai, lines_a, b, bi_, lines_b in ((wall, z_wall + stag, fi, L, y, bi, B), (~wall, z + stag2, fi2, L, np.abs(x), si, St)):
            a0, a1 = lines_a[np.clip(ai - 1, 0, len(lines_a) - 1)], lines_a[np.clip(ai, 0, len(lines_a) - 1)]
            b0, b1 = lines_b[np.clip(bi_ - 1, 0, len(lines_b) - 1)], lines_b[np.clip(bi_, 0, len(lines_b) - 1)]
            h1 = hash3(pid, pid // 3 + 5, pid // 11, 21)
            h2 = hash3(pid, pid // 5 + 7, pid // 3, 22)
            h3 = hash3(pid, pid // 7 + 1, pid // 5, 23)
            h4 = hash3(pid, pid // 2 + 9, pid // 9, 24)
            ca, cb = a1 - a0, b1 - b0
            hw = np.minimum(0.4 + 0.5 * h2, ca / 2 - 0.35)
            hh = np.minimum(0.3 + 0.45 * h3, cb / 2 - 0.3)
            ok = mask & (h1 < ap) & (hw > 0.25) & (hh > 0.2)
            cxa = a0 + 0.3 + hw + (ca - 0.6 - 2 * hw) * h4
            cxb = b0 + 0.3 + hh + (cb - 0.6 - 2 * hh) * hash3(pid, pid // 13, pid // 17, 25)
            q = np.maximum(np.abs(a - cxa) - hw, np.abs(b - cxb) - hh)
            d_acc = np.where(ok, np.minimum(d_acc, np.abs(q)), d_acc)
    m = 1 - smooth(w * 0.35, w, d)
    ma = (1 - smooth(w * 0.25, w * 0.7, d_acc)) * cfg.get('access_dark', 0.6)
    return np.maximum(m, ma).astype(np.float32), pid, d, d_acc


def height_to_normal(h, cov, px_per_m, strength=1.0):
    """Tangent-space normal map (glTF / OpenGL: +X = +u, +Y = +v = image up) from a height map in
    metres (rows top-down), assuming UV islands at one scale (px_per_m). Gradients never cross
    into empty texels."""
    hp = np.pad(h, 1, mode='edge'); cp = np.pad(cov, 1, mode='constant')
    def diff(a0, a1, c0, c1):
        ok = c0 & c1
        return np.where(ok, a1 - a0, 0.0)
    gx = 0.5 * (diff(hp[1:-1, :-2], hp[1:-1, 1:-1], cp[1:-1, :-2], cp[1:-1, 1:-1]) + diff(hp[1:-1, 1:-1], hp[1:-1, 2:], cp[1:-1, 1:-1], cp[1:-1, 2:]))
    gy = 0.5 * (diff(hp[:-2, 1:-1], hp[1:-1, 1:-1], cp[:-2, 1:-1], cp[1:-1, 1:-1]) + diff(hp[1:-1, 1:-1], hp[2:, 1:-1], cp[1:-1, 1:-1], cp[2:, 1:-1]))
    # per metre; image rows run down, +v runs up
    dhdu = gx * px_per_m * strength
    dhdv = -gy * px_per_m * strength
    n = np.stack([-dhdu, -dhdv, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------------------------------
# decals
# ------------------------------------------------------------------------------------------
def frame(d):
    n = np.array(d['n'], float); n /= np.linalg.norm(n)
    up = np.array(d.get('up', [0, 1, 0]), float)
    up = up - n * (up @ n); up /= np.linalg.norm(up)
    right = np.cross(up, n)
    return np.array(d['p'], float), np.stack([right, up, n], 1)


def mirrored(d):
    out = [d]
    if d.get('mirrorX'):
        m = dict(d)
        m['p'] = [-d['p'][0], d['p'][1], d['p'][2]]
        m['n'] = [-d['n'][0], d['n'][1], d['n'][2]]
        if 'up' in d:
            m['up'] = [-d['up'][0], d['up'][1], d['up'][2]]
        out.append(m)
    return out


def decal_mask(pos, nrm, d):
    """Texels inside decal d's oriented box and facing its normal: (mask, local u, v)."""
    c, R = frame(d)
    L = (pos - c) @ R
    w, h, dep = d['size']
    facing = (nrm @ R[:, 2]) > d.get('facing', 0.5)
    m = (np.abs(L[:, 0]) <= w / 2) & (np.abs(L[:, 1]) <= h / 2) & (np.abs(L[:, 2]) <= dep / 2) & facing
    return m, L[:, 0], L[:, 1]


def stencil(text, h, px_per_m=200):
    import sys
    sys.path.insert(0, os.path.dirname(HERE))
    import hulltex
    im, wm, hm = hulltex.stencil_alpha(text, h, px_per_m)
    return np.asarray(im, np.float32) / 255, wm, hm


def apply_decals(col, rough, pos, nrm, decals, rng):
    for d0 in decals:
        for d in mirrored(d0):
            m, u, v = decal_mask(pos, nrm, d)
            if not m.any():
                continue
            k = d['kind']
            c = srgb2lin(d.get('color', [0.9, 0.45, 0.1]))
            wear = d.get('wear', 0.25)
            cover = np.ones(m.sum(), np.float32)   # where the decal paints at all
            if k == 'fill':
                a = np.ones(m.sum(), np.float32)
            elif k == 'hazard':
                pitch = d.get('pitch', 0.6)
                s = (u[m] + v[m]) / pitch
                a = (np.floor(s) % 2 == 0).astype(np.float32)
                border = d.get('border')
                if border:  # only a frame of this width round the box
                    w, h = d['size'][0] / 2, d['size'][1] / 2
                    inner = (np.abs(u[m]) < w - border) & (np.abs(v[m]) < h - border)
                    cover[inner] = 0
            elif k == 'text':
                A, wm, hm = stencil(d['text'], d['height'])
                uu = u[m] / wm + 0.5
                vv = 0.5 - v[m] / hm
                ok = (uu >= 0) & (uu < 1) & (vv >= 0) & (vv < 1)
                a = np.zeros(m.sum(), np.float32)
                X = np.clip((uu[ok] * A.shape[1]).astype(int), 0, A.shape[1] - 1)
                Y = np.clip((vv[ok] * A.shape[0]).astype(int), 0, A.shape[0] - 1)
                a[ok] = A[Y, X]
            else:
                raise ValueError(k)
            # worn paint: chips where a noise field is high
            chip = fbm(pos[m], 3.0, 3, seed=7)
            keep = 1 - wear * smooth(0.6, 0.7, chip)
            cur = col[m]
            tone = np.clip(cur.mean(1, keepdims=True) / max(float(np.median(cur.mean(1))), 1e-3), 0.8, 1.15)
            if 'alt' in d:   # two-colour stripes over the whole covered area
                new = (srgb2lin(d['alt'])[None] * (1 - a[:, None]) + c[None] * a[:, None]) * tone
                w_ = (cover * keep)[:, None]
            else:
                new = c[None] * tone
                w_ = (a * cover * keep)[:, None]
            col[m] = cur * (1 - w_) + new * w_
            rough[m] = rough[m] * (1 - w_[:, 0]) + d.get('rough', 0.55) * w_[:, 0]


# ------------------------------------------------------------------------------------------
def paint(maps, spec, out, size=None):
    pos, nrm, zone = maps['pos'], maps['nrm'], maps['zone'].astype(np.int32)
    S = zone.shape[0]
    cov = zone >= 0
    idx = np.where(cov.ravel())[0]
    P = pos.reshape(-1, 3)[idx].astype(np.float32)
    N = nrm.reshape(-1, 3)[idx].astype(np.float32)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    Zn = zone.ravel()[idx]
    ao = upsample(maps['ao'], S).ravel()[idx]
    cv = upsample(maps['curv'], S).ravel()[idx]
    rng = np.random.default_rng(3)
    zones = spec['zones']
    names = spec['zone_names']
    base = np.zeros((len(idx), 3), np.float32)
    rough = np.zeros(len(idx), np.float32)
    metal = np.zeros(len(idx), np.float32)
    for i, n in enumerate(names):
        z = zones.get(n, zones['paint'])
        m = Zn == i
        base[m] = srgb2lin(z['color'])
        rough[m] = z.get('rough', 0.6)
        metal[m] = z.get('metal', 0.0)
    painted = np.isin(Zn, [names.index(n) for n in spec.get('plated', ['paint', 'deck', 'trim', 'belly'])])
    # 2. structural plating
    sm, pid, d_seam, d_acc = seams(P, N, spec['seams'])
    ptone = 1 + spec['seams'].get('tone', 0.06) * (hash3(pid, pid // 7, pid // 13, 11) * 2 - 1)
    base *= np.where(painted, ptone, 1.0)[:, None]
    base *= (1 - spec['seams'].get('dark', 0.45) * sm * painted)[:, None]
    rough = np.where(painted, rough + 0.08 * sm, rough)
    # 3. PATINA plate tone (runtime tile)
    pt = spec.get('patina')
    if pt:
        hm = np.asarray(Image.open(os.path.join(SCENE, 'assets/materials/hull/height.webp')).convert('L'), np.float32) / 255
        h = triplanar(hm, P, N, pt['tile'])
        k = 1 + pt['tone'] * (h / hm.mean() - 1)
        base *= np.where(painted, k, 1.0)[:, None]
    # 4. AO grime + edge wear
    g = spec['grime']
    aof = np.clip(ao, 0, 1)
    base *= (1 - g['ao'] * (1 - aof))[:, None]
    grime_c = srgb2lin(g.get('color', [0.42, 0.40, 0.37]))
    gm = g['crease'] * smooth(0.9, 0.55, aof)
    base = base * (1 - gm[:, None]) + (base * grime_c / 0.6) * gm[:, None]
    rough += 0.1 * gm
    edge = smooth(0.08, 0.35, cv) * smooth(0.8, 0.97, aof)  # convex edges (not creases)
    chip = fbm(P, 2.2, 3, seed=5)
    wear = edge * smooth(0.35, 0.6, chip) * g['edge']
    base = base * (1 - wear[:, None]) + srgb2lin(g.get('edge_color', [0.9, 0.9, 0.88]))[None] * wear[:, None]
    metal = np.maximum(metal, wear * 0.5)
    rough -= 0.15 * wear
    # 5. weathering: large blotches, vertical streaks on walls
    blot = fbm(P, 0.09, 3, seed=1)
    base *= (1 + g.get('blotch', 0.08) * (blot - 0.5) * 2)[:, None]
    walls = np.abs(N[:, 1]) < 0.5
    st = fbm(P * np.array([1.0, 0.08, 1.0], np.float32), 1.6, 2, seed=9)
    streak = walls * smooth(0.55, 0.8, st) * g.get('streak', 0.08)
    base *= (1 - streak)[:, None]
    # foil crinkle: tone patches and sharp creases (colour), bumps (normal map below)
    if 'foil' in names:
        fm = Zn == names.index('foil')
        if fm.any():
            cr = fbm(P[fm], 2.5, 3, seed=31)
            base[fm] *= (0.7 + 0.6 * cr)[:, None]
            rough[fm] = 0.25 + 0.3 * cr
    # 6. decals
    apply_decals(base, rough, P, N, spec.get('decals', []), rng)
    # assemble full images (empty texels: neutral paint so mip levels never pull dark)
    fill = srgb2lin(zones['paint']['color'])
    img = np.tile(fill[None], (S * S, 1)).astype(np.float32)
    img[idx] = base
    col8 = (lin2srgb(img).reshape(S, S, 3) * 255 + 0.5).astype(np.uint8)
    orm = np.zeros((S * S, 3), np.float32)
    orm[:, 0] = 1.0; orm[:, 1] = zones['paint'].get('rough', 0.6)
    orm[idx, 1] = np.clip(rough, 0.05, 1)
    orm[idx, 2] = np.clip(metal, 0, 1)
    orm8 = (orm.reshape(S, S, 3) * 255 + 0.5).astype(np.uint8)
    bp, op = os.path.join(out, 'base.png'), os.path.join(out, 'orm.png')
    Image.fromarray(col8).save(bp)
    Image.fromarray(orm8).save(op)
    # normal map: seam grooves (V profile) and access-panel outlines, on the plated zones only
    nm = spec.get('normal')
    np_ = None
    if nm:
        sw = spec['seams'].get('width', 0.08)
        gro = nm['seam_depth'] * (1 - smooth(0.0, sw * nm.get('seam_w', 1.0), d_seam))
        gro = np.maximum(gro, nm['access_depth'] * (1 - smooth(0.0, sw * 0.7, d_acc)))
        hh = np.zeros(S * S, np.float32)
        hh[idx] = -gro * painted
        if 'foil' in names:
            fm = Zn == names.index('foil')
            hh[idx[fm]] = 0.02 * fbm(P[fm], 4.0, 3, seed=33)
        cv2 = np.zeros(S * S, bool); cv2[idx] = True
        nimg = height_to_normal(hh.reshape(S, S), cv2.reshape(S, S), spec['px_per_m'], nm.get('strength', 1.0))
        np_ = os.path.join(out, 'normal.png')
        Image.fromarray(nimg).save(np_)
    spec['_normal_png'] = np_
    Image.fromarray(col8).resize((2048, 2048)).save(os.path.join(out, 'base-2k.jpg'), quality=90)
    return bp, op


# ------------------------------------------------------------------------------------------
# the corvette's paint scheme (from the approved concept and the turnaround sheet)
# ------------------------------------------------------------------------------------------
ORANGE = [0.93, 0.45, 0.10]
COBALT = [0.24, 0.40, 0.82]
STENCIL_WHITE = [0.95, 0.94, 0.91]


def _corvette():
    frames = []
    z = -49.0
    steps = [5.4, 6.2, 4.8, 6.6, 5.6, 6.0, 5.0, 6.4, 5.8, 5.2, 6.2, 5.6, 6.0, 5.4, 6.6, 5.2, 6.0, 5.8, 6.0]
    for s in steps:
        frames.append(z); z += s
    frames.append(z)
    decals = [
        # hull number on the tapered bow flank (reads left to right from outside, both sides)
        {'kind': 'text', 'text': 'K-214', 'height': 3.6, 'p': [12.55, -9.9, 35.2], 'n': [0.975, 0, 0.221], 'size': [16, 4.6, 2.0], 'mirrorX': True, 'color': STENCIL_WHITE, 'wear': 0.15},
        # orange bands: bow band round the flanks and over the bow deck, aft band on the flanks
        {'kind': 'fill', 'p': [9.4, -10.5, 48.6], 'n': [0.975, 0, 0.221], 'size': [1.6, 16, 3.0], 'mirrorX': True, 'color': ORANGE, 'facing': 0.3},
        {'kind': 'fill', 'p': [0, -4.3, 48.6], 'n': [0, 0.988, 0.156], 'up': [0, 0, 1], 'size': [18, 1.6, 4.0], 'color': ORANGE, 'facing': 0.3},
        {'kind': 'fill', 'p': [15.6, -9.5, -45.6], 'n': [1, 0, 0], 'size': [1.3, 13, 3.0], 'mirrorX': True, 'color': ORANGE},
        # deck-house bands forward of each turret (thin diagonal-free bars, concept)
        {'kind': 'fill', 'p': [9.0, 0.9, 9.4], 'n': [0.889, 0.459, 0], 'size': [0.8, 6.0, 2.0], 'mirrorX': True, 'color': ORANGE},
        {'kind': 'fill', 'p': [9.0, 0.9, -31.0], 'n': [0.889, 0.459, 0], 'size': [0.8, 6.0, 2.0], 'mirrorX': True, 'color': ORANGE},
        # cobalt identification bars and marker squares on the flank
        {'kind': 'fill', 'p': [16.15, -7.4, -2.6], 'n': [1, 0, 0], 'size': [0.9, 5.2, 1.0], 'mirrorX': True, 'color': COBALT},
        {'kind': 'fill', 'p': [15.95, -7.4, -24.6], 'n': [1, 0, 0], 'size': [0.9, 5.2, 1.0], 'mirrorX': True, 'color': COBALT},
        {'kind': 'fill', 'p': [16.37, -15.6, 4.2], 'n': [1, 0, 0], 'size': [1.4, 0.9, 1.0], 'mirrorX': True, 'color': COBALT},
        {'kind': 'fill', 'p': [16.37, -15.6, -34.0], 'n': [1, 0, 0], 'size': [1.4, 0.9, 1.0], 'mirrorX': True, 'color': COBALT},
        # hazard stripes: frames round the shoulder vent bays and the airlock / door bays
        {'kind': 'hazard', 'p': [14.83, -2.98, 11.5], 'n': [0.754, 0.657, 0], 'up': [-0.657, 0.754, 0], 'size': [11.6, 3.4, 1.2], 'border': 0.45, 'pitch': 0.55, 'mirrorX': True, 'color': ORANGE, 'alt': [0.16, 0.16, 0.17], 'solid': True},
        {'kind': 'hazard', 'p': [14.7, -3.1, -43.4], 'n': [0.754, 0.657, 0], 'up': [-0.657, 0.754, 0], 'size': [7.0, 3.4, 1.2], 'border': 0.45, 'pitch': 0.55, 'mirrorX': True, 'color': ORANGE, 'alt': [0.16, 0.16, 0.17], 'solid': True},
        {'kind': 'hazard', 'p': [14.9, -13.45, 24.65], 'n': [0.975, 0, 0.221], 'size': [3.9, 4.7, 1.2], 'border': 0.4, 'pitch': 0.5, 'mirrorX': True, 'color': ORANGE, 'alt': [0.16, 0.16, 0.17], 'solid': True},
        # walkway edge line (safety yellow-orange) along the deck edge
        {'kind': 'fill', 'p': [13.0, -1.46, -5.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.18, 48, 0.6], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
    ]
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'foil'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.77], 'rough': 0.62},
            'trim': {'color': [0.74, 0.74, 0.72], 'rough': 0.6},
            'belly': {'color': [0.30, 0.30, 0.31], 'rough': 0.72},
            'deck': {'color': [0.64, 0.64, 0.63], 'rough': 0.8},
            'dark': {'color': [0.24, 0.24, 0.25], 'rough': 0.7},
            'recess': {'color': [0.52, 0.52, 0.52], 'rough': 0.7},
            'metal': {'color': [0.46, 0.46, 0.46], 'rough': 0.45, 'metal': 0.5},
            'fin': {'color': [0.36, 0.36, 0.37], 'rough': 0.5, 'metal': 0.4},
            'glass': {'color': [0.13, 0.16, 0.2], 'rough': 0.1},
            'nozzle': {'color': [0.2, 0.2, 0.2], 'rough': 0.5, 'metal': 0.6},
            # MLI foil: gold, crinkled (tone and normal noise below); livery.js keeps part of its hue
            'foil': {'color': [0.6, 0.48, 0.27], 'rough': 0.35, 'metal': 0.8},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': frames, 'bands': [-23.3, -20.4, -17.0, -14.3, -11.6, -8.3, -5.2, -1.46, 0.7, 2.1, 3.45, 6.9, 9.4],
                  'strakes': [0.0, 1.6, 4.6, 7.9, 10.4, 13.0, 16.0], 'width': 0.08, 'stagger': 2.8, 'tone': 0.07, 'dark': 0.5,
                  'access': 0.35, 'access_dark': 0.45},
        'normal': {'seam_depth': 0.015, 'access_depth': 0.008, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.35},
        'grime': {'ao': 0.35, 'crease': 0.35, 'edge': 0.55, 'blotch': 0.07, 'streak': 0.07},
        'decals': decals,
    }


CORVETTE = _corvette()
