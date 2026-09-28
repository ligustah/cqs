"""Texture-space paint for the destroyer (tools/blender/hulls/destroyer.py): paint.py's layers,
run in row chunks at a larger texture than the bake.

The 200 m hull has ~53,000 m^2 of surface: at 4096 that is ~14 px/m, so seams go soft in
close-ups. The maps are baked at 4096 (Cycles EMIT: position, true normal, zone, AO,
curvature) and then UPSAMPLED to the paint size (8192): position and normal bilinearly (both are
linear inside a face, and the bake's 8 px EXTEND margin keeps island borders clean), zones by
nearest texel, AO / curvature bilinearly. Every layer of paint.py (zone colours, plating seams,
per-panel tone, access panels, PATINA plate tone, AO grime, edge wear, blotches, streaks,
decals) is evaluated per texel on those upsampled maps, in bands of rows so the 67 M texels fit
in memory. Base colour is written at the paint size; ORM and the tangent-space normal map at
`normal_size` (4096; the normal map comes from the seam-groove height field, area-averaged).

Changes from paint.py (copied here, per the shared-code rule):
  - zone 10 is COPPER (railgun coils and bus bars), not MLI foil: warm copper, no crinkle; the
    livery keeps part of its hue (copperSat);
  - access panels: a wider size range and a second hash per cell, so the outlines do not repeat
    in a visible rhythm; some cells carry a pair of small panels, some a vertical service strip;
  - a stencil with the glyphs D, D-12 needs (hulltex's fleet stencil has only K - 1 2 4).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint as PT  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


# ------------------------------------------------------------------------------------------
# stencil (hulltex.stencil_alpha plus 'D')
# ------------------------------------------------------------------------------------------
def stencil_alpha(text, h, px_per_m=200):
    from PIL import ImageDraw
    H = int(round(h * px_per_m)); s = 0.185 * H; g = 0.11 * H
    widths = {'D': 0.64, '-': 0.40, '1': 0.46, '2': 0.66, ' ': 0.4}
    Wt = int(sum(widths.get(ch, 0.62) * H for ch in text) + g * (len(text) - 1)) + 4
    im = Image.new('L', (Wt, H + 4), 0)
    d = ImageDraw.Draw(im)
    x = 2; y0 = 2; i = s / 2

    def poly(pts):
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)

    def bar(x0, y0_, x1, y1):
        d.rectangle([x0, y0_, x1, y1], fill=255)

    def stroke(pts):
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** 0.5
            nx, ny = -dy / L * s / 2, dx / L * s / 2
            poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        for (cx, cy) in pts[1:-1]:
            bar(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
    for ch in text:
        w = widths.get(ch, 0.62) * H
        top, bot, mid = y0, y0 + H, y0 + 0.52 * H
        if ch == 'D':
            bar(x, top, x + s, bot)
            c = 0.26 * H
            stroke([(x + s / 2, top + i), (x + w - i - c, top + i), (x + w - i, top + i + c), (x + w - i, bot - i - c), (x + w - i - c, bot - i), (x + s / 2, bot - i)])
        elif ch == '-':
            bar(x, y0 + 0.53 * H - s * 0.525, x + w, y0 + 0.53 * H + s * 0.525)
        elif ch == '1':
            sx = x + w - s * 1.1
            bar(sx, top, sx + s * 1.1, bot)
            poly([(sx, top), (sx, top + s * 1.25), (x, top + 0.36 * H), (x, top + 0.36 * H - s * 1.25)])
        elif ch == '2':
            stroke([(x, top + i), (x + w - i, top + i), (x + w - i, mid), (x + i, mid), (x + i, bot - i), (x + w, bot - i)])
        x += w + g
    return im, Wt / px_per_m, (H + 4) / px_per_m


_STENCILS = {}


def stencil(text, h):
    if (text, h) not in _STENCILS:
        im, wm, hm = stencil_alpha(text, h)
        _STENCILS[(text, h)] = (np.asarray(im, np.float32) / 255, wm, hm)
    return _STENCILS[(text, h)]


def apply_decals(col, rough, pos, nrm, decals):
    """paint.apply_decals with this module's stencil."""
    for d0 in decals:
        for d in PT.mirrored(d0):
            m, u, v = PT.decal_mask(pos, nrm, d)
            if not m.any():
                continue
            k = d['kind']
            c = PT.srgb2lin(d.get('color', [0.9, 0.45, 0.1]))
            wear = d.get('wear', 0.25)
            cover = np.ones(m.sum(), np.float32)
            if k == 'fill':
                a = np.ones(m.sum(), np.float32)
            elif k == 'hazard':
                pitch = d.get('pitch', 0.6)
                s = (u[m] + v[m]) / pitch
                a = (np.floor(s) % 2 == 0).astype(np.float32)
                border = d.get('border')
                if border:
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
            chip = PT.fbm(pos[m], 3.0, 3, seed=7)
            keep = 1 - wear * PT.smooth(0.6, 0.7, chip)
            cur = col[m]
            tone = np.clip(cur.mean(1, keepdims=True) / max(float(np.median(cur.mean(1))), 1e-3), 0.8, 1.15)
            if 'alt' in d:
                new = (PT.srgb2lin(d['alt'])[None] * (1 - a[:, None]) + c[None] * a[:, None]) * tone
                w_ = (cover * keep)[:, None]
            else:
                new = c[None] * tone
                w_ = (a * cover * keep)[:, None]
            col[m] = cur * (1 - w_) + new * w_
            rough[m] = rough[m] * (1 - w_[:, 0]) + d.get('rough', 0.55) * w_[:, 0]


# ------------------------------------------------------------------------------------------
# seams with varied access panels
# ------------------------------------------------------------------------------------------
def seams(pos, nrm, cfg):
    sm, pid, d, _ = PT.seams(pos, nrm, {**cfg, 'access': 0.0})
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    w = cfg.get('width', 0.08)
    ap = cfg.get('access', 0.0)
    wall = np.abs(nrm[:, 1]) < 0.9
    hx, hz = nrm[:, 2], -nrm[:, 0]
    hl = np.maximum(np.hypot(hx, hz), 1e-6)
    hx, hz = hx / hl, hz / hl
    flip = np.where(np.abs(hz) > 0.3, hz < 0, hx < 0)
    hx = np.where(flip, -hx, hx); hz = np.where(flip, -hz, hz)
    sw = x * hx + z * hz
    frames = np.asarray(sorted(cfg['frames']), np.float32)
    bands = np.asarray(sorted(cfg['bands']), np.float32)
    strakes = np.asarray(sorted(cfg['strakes']), np.float32)
    stag_v = cfg.get('stagger', 2.4)

    def cell(v, L):
        i = np.clip(np.searchsorted(L, v), 1, len(L) - 1)
        return L[i - 1], L[i], i
    b0, b1, bi = cell(y, bands)
    stag = np.where(bi % 2 == 0, 0.0, stag_v).astype(np.float32)
    f0, f1, fi = cell(sw + stag, frames)
    s0, s1, si = cell(np.abs(x), strakes)
    stag2 = np.where(si % 2 == 0, 0.0, stag_v).astype(np.float32)
    g0, g1, gi = cell(z + stag2, frames)
    a = np.where(wall, sw + stag, z + stag2)
    a0 = np.where(wall, f0, g0); a1 = np.where(wall, f1, g1)
    b = np.where(wall, y, np.abs(x))
    c0 = np.where(wall, b0, s0); c1 = np.where(wall, b1, s1)
    d_acc = np.full(len(x), 1e3, np.float32)
    if ap > 0:
        H = lambda k: PT.hash3(pid, pid // (k + 2) + 7 * k, pid // (k + 5) + 3, 40 + k)
        ca, cb = a1 - a0, c1 - c0
        kind = H(0)
        # single panel, size from a wide range
        hw = np.minimum(0.3 + 1.1 * H(1) ** 1.5, ca / 2 - 0.35)
        hh = np.minimum(0.25 + 0.8 * H(2) ** 1.5, cb / 2 - 0.3)
        ok1 = (kind < ap) & (hw > 0.22) & (hh > 0.18)
        cxa = a0 + 0.3 + hw + (ca - 0.6 - 2 * hw) * H(3)
        cxb = c0 + 0.3 + hh + (cb - 0.6 - 2 * hh) * H(4)
        q = np.maximum(np.abs(a - cxa) - hw, np.abs(b - cxb) - hh)
        d_acc = np.where(ok1, np.minimum(d_acc, np.abs(q)), d_acc)
        # a pair of small hatches side by side
        ok2 = (kind >= ap) & (kind < ap * 1.35) & (ca > 2.4) & (cb > 1.6)
        for side in (-1, 1):
            cxa2 = (a0 + a1) / 2 + side * 0.75 + (H(5) - 0.5) * (ca - 3.2)
            q2 = np.maximum(np.abs(a - cxa2) - 0.45, np.abs(b - (c0 + c1) / 2) - 0.45)
            d_acc = np.where(ok2, np.minimum(d_acc, np.abs(q2)), d_acc)
        # a narrow vertical service strip
        ok3 = (kind >= ap * 1.35) & (kind < ap * 1.55) & (cb > 1.8)
        cxa3 = a0 + 0.6 + (ca - 1.2) * H(6)
        q3 = np.maximum(np.abs(a - cxa3) - 0.22, np.abs(b - (c0 + c1) / 2) - (cb / 2 - 0.35))
        d_acc = np.where(ok3, np.minimum(d_acc, np.abs(q3)), d_acc)
    ma = (1 - PT.smooth(w * 0.25, w * 0.7, d_acc)) * cfg.get('access_dark', 0.6)
    return np.maximum(sm, ma).astype(np.float32), pid, d, d_acc


# ------------------------------------------------------------------------------------------
# per-texel layers (paint.paint's body, on a chunk of texels)
# ------------------------------------------------------------------------------------------
def paint_texels(P, N, Zn, ao, cv, spec, hm):
    zones, names = spec['zones'], spec['zone_names']
    n = len(P)
    base = np.zeros((n, 3), np.float32); rough = np.zeros(n, np.float32); metal = np.zeros(n, np.float32)
    for i, nm in enumerate(names):
        z = zones.get(nm, zones['paint'])
        m = Zn == i
        base[m] = PT.srgb2lin(z['color']); rough[m] = z.get('rough', 0.6); metal[m] = z.get('metal', 0.0)
    painted = np.isin(Zn, [names.index(x) for x in spec.get('plated', ['paint', 'deck', 'trim', 'belly'])])
    sm, pid, d_seam, d_acc = seams(P, N, spec['seams'])
    ptone = 1 + spec['seams'].get('tone', 0.06) * (PT.hash3(pid, pid // 7, pid // 13, 11) * 2 - 1)
    base *= np.where(painted, ptone, 1.0)[:, None]
    base *= (1 - spec['seams'].get('dark', 0.45) * sm * painted)[:, None]
    rough = np.where(painted, rough + 0.08 * sm, rough)
    pt = spec.get('patina')
    if pt:
        h = PT.triplanar(hm, P, N, pt['tile'])
        k = 1 + pt['tone'] * (h / hm.mean() - 1)
        base *= np.where(painted, k, 1.0)[:, None]
    g = spec['grime']
    aof = np.clip(ao, 0, 1)
    base *= (1 - g['ao'] * (1 - aof))[:, None]
    grime_c = PT.srgb2lin(g.get('color', [0.42, 0.40, 0.37]))
    gm = g['crease'] * PT.smooth(0.9, 0.55, aof)
    base = base * (1 - gm[:, None]) + (base * grime_c / 0.6) * gm[:, None]
    rough += 0.1 * gm
    edge = PT.smooth(0.08, 0.35, cv) * PT.smooth(0.8, 0.97, aof)
    chip = PT.fbm(P, 2.2, 3, seed=5)
    # edge wear only on painted plate (bare copper coils and steel machinery have no paint to chip; on
    # their thin, low-density turns the whole face reads as an 'edge' and went white)
    wear = edge * PT.smooth(0.35, 0.6, chip) * g['edge'] * painted
    base = base * (1 - wear[:, None]) + PT.srgb2lin(g.get('edge_color', [0.9, 0.9, 0.88]))[None] * wear[:, None]
    metal = np.maximum(metal, wear * 0.5)
    rough -= 0.15 * wear
    blot = PT.fbm(P, 0.09, 3, seed=1)
    base *= (1 + g.get('blotch', 0.08) * (blot - 0.5) * 2)[:, None]
    # a second, larger weathering scale: whole plates a little lighter or darker (repair patches)
    blot2 = PT.fbm(P, 0.025, 2, seed=2)
    base *= (1 + g.get('blotch2', 0.06) * (blot2 - 0.5) * 2)[:, None]
    walls = np.abs(N[:, 1]) < 0.5
    st = PT.fbm(P * np.array([1.0, 0.08, 1.0], np.float32), 1.6, 2, seed=9)
    streak = walls * PT.smooth(0.55, 0.8, st) * g.get('streak', 0.08)
    base *= (1 - streak)[:, None]
    if 'copper' in names:
        cm = Zn == names.index('copper')
        if cm.any():
            v = PT.fbm(P[cm], 1.5, 2, seed=31)
            base[cm] *= (0.8 + 0.4 * v)[:, None]
    apply_decals(base, rough, P, N, spec.get('decals', []))
    nm = spec['normal']
    sw = spec['seams'].get('width', 0.08)
    gro = nm['seam_depth'] * (1 - PT.smooth(0.0, sw * nm.get('seam_w', 1.0), d_seam))
    gro = np.maximum(gro, nm['access_depth'] * (1 - PT.smooth(0.0, sw * 0.7, d_acc)))
    return base, np.clip(rough, 0.05, 1), np.clip(metal, 0, 1), (-gro * painted).astype(np.float32)


def _up(a, f, order=1):
    """Upsample a 2D (or HxWxC) array by integer factor f: bilinear (order 1) or nearest."""
    if f == 1:
        return a
    if order == 0:
        return np.repeat(np.repeat(a, f, 0), f, 1)
    from scipy.ndimage import zoom
    if a.ndim == 3:
        return np.stack([zoom(a[..., c], f, order=1, mode='nearest', grid_mode=True) for c in range(a.shape[2])], -1)
    return zoom(a, f, order=1, mode='nearest', grid_mode=True)


def paint(maps, spec, out, size=8192, normal_size=4096, rows=512):
    S0 = maps['zone'].shape[0]
    f = size // S0
    assert f * S0 == size
    hm = np.asarray(Image.open(os.path.join(PT.SCENE, 'assets/materials/hull/height.webp')).convert('L'), np.float32) / 255
    zone0 = maps['zone'].astype(np.int16)
    ao_full = PT.upsample(maps['ao'], S0)       # to the bake size first (as paint.py)
    cv_full = PT.upsample(maps['curv'], S0)
    base_img = np.zeros((size, size, 3), np.uint8)
    orm_hi = np.zeros((size, size, 2), np.uint8)       # roughness, metal at the paint size (averaged down)
    height = np.zeros((size, size), np.float32)
    cov_hi = np.zeros((size, size), bool)
    fill = PT.srgb2lin(spec['zones']['paint']['color'])
    band0 = rows // f                                   # bake rows per chunk
    for r0 in range(0, S0, band0):
        r1 = min(S0, r0 + band0)
        # one extra bake row each side so bilinear upsampling is continuous across chunks
        a0, a1 = max(0, r0 - 1), min(S0, r1 + 1)
        sl = lambda a: a[a0:a1]
        pos = _up(sl(maps['pos']), f); nrm = _up(sl(maps['nrm']), f)
        zon = _up(sl(zone0), f, order=0); ao = _up(sl(ao_full), f); cv = _up(sl(cv_full), f)
        cut = slice((r0 - a0) * f, (r0 - a0) * f + (r1 - r0) * f)
        pos, nrm, zon, ao, cv = pos[cut], nrm[cut], zon[cut], ao[cut], cv[cut]
        cov = zon >= 0
        idx = np.where(cov.ravel())[0]
        img = np.tile(fill[None], (cov.size, 1)).astype(np.float32)
        rgh = np.full(cov.size, spec['zones']['paint'].get('rough', 0.6), np.float32)
        met = np.zeros(cov.size, np.float32)
        hh = np.zeros(cov.size, np.float32)
        if len(idx):
            P = pos.reshape(-1, 3)[idx].astype(np.float32)
            N = nrm.reshape(-1, 3)[idx].astype(np.float32)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
            b, rr, mm, gh = paint_texels(P, N, zon.ravel()[idx].astype(np.int32), ao.ravel()[idx], cv.ravel()[idx], spec, hm)
            img[idx] = b; rgh[idx] = rr; met[idx] = mm; hh[idx] = gh
        R0, R1 = r0 * f, r1 * f
        base_img[R0:R1] = (PT.lin2srgb(img).reshape(R1 - R0, size, 3) * 255 + 0.5).astype(np.uint8)
        orm_hi[R0:R1, :, 0] = (rgh.reshape(R1 - R0, size) * 255 + 0.5).astype(np.uint8)
        orm_hi[R0:R1, :, 1] = (met.reshape(R1 - R0, size) * 255 + 0.5).astype(np.uint8)
        height[R0:R1] = hh.reshape(R1 - R0, size)
        cov_hi[R0:R1] = cov
        print(f'[paint] rows {R0}-{R1} of {size}', flush=True)
    bp = os.path.join(out, 'base.png')
    Image.fromarray(base_img).save(bp)
    Image.fromarray(base_img).resize((2048, 2048), Image.BOX).save(os.path.join(out, 'base-2k.jpg'), quality=90)
    k = size // normal_size
    def down(a):
        return a.reshape(normal_size, k, normal_size, k, *a.shape[2:]).mean((1, 3)) if k > 1 else a
    orm = np.zeros((normal_size, normal_size, 3), np.uint8)
    orm[..., 0] = 255
    orm[..., 1:] = (down(orm_hi.astype(np.float32)) + 0.5).astype(np.uint8)
    op = os.path.join(out, 'orm.png')
    Image.fromarray(orm).save(op)
    del orm_hi
    cov_n = down(cov_hi.astype(np.float32)) > 0.5
    h_n = down(height)
    nimg = PT.height_to_normal(h_n, cov_n, spec['px_per_m'] / k, spec['normal'].get('strength', 1.0))
    np_ = os.path.join(out, 'normal.png')
    Image.fromarray(nimg).save(np_)
    return bp, op, np_


# ------------------------------------------------------------------------------------------
# DD-12's paint scheme (from the approved concept)
# ------------------------------------------------------------------------------------------
ORANGE = [0.93, 0.45, 0.10]
COBALT = [0.24, 0.40, 0.82]
STENCIL_WHITE = [0.95, 0.94, 0.91]
HAZ = {'kind': 'hazard', 'pitch': 0.55, 'color': ORANGE, 'alt': [0.16, 0.16, 0.17], 'mirrorX': True}


def _frames():
    out, z = [], -101.5
    steps = [5.6, 6.4, 4.9, 6.8, 5.5, 6.1, 5.2, 6.6, 5.9, 5.0, 6.3, 5.7, 6.0, 5.3, 6.7, 5.1, 6.2, 5.8]
    i = 0
    while z < 102:
        out.append(z); z += steps[i % len(steps)]; i += 1
    out.append(z)
    return out


def spec():
    tn = math.atan2(17.5 - 13.26, 43.5 - 21.0)    # mid hull forward taper
    n_taper = [round(math.cos(tn), 4), 0, round(math.sin(tn), 4)]
    decals = [
        # hull number on the forward taper of the mid hull, both flanks (concept: DD-12 ahead of the
        # boat hatch, upper flank), 3.4 m stencil reading left to right from outside
        {'kind': 'text', 'text': 'DD-12', 'height': 3.4, 'p': [16.1, -19.0, 28.5], 'n': n_taper, 'size': [14.0, 4.4, 2.0], 'mirrorX': True, 'color': STENCIL_WHITE, 'wear': 0.15},
        # cobalt bands: round the bow block ahead of its rear taper, and on the mid hull ahead of the tower
        {'kind': 'fill', 'p': [17.1, -18.0, 62.0], 'n': [1, 0, 0], 'size': [1.8, 11.0, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.3},
        {'kind': 'fill', 'p': [14.2, -10.0, 62.0], 'n': [0.774, 0.634, 0], 'up': [-0.634, 0.774, 0], 'size': [1.8, 9.4, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.3},
        {'kind': 'fill', 'p': [14.2, -26.5, 62.0], 'n': [0.774, -0.634, 0], 'up': [0.634, 0.774, 0], 'size': [1.8, 9.4, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.3},
        {'kind': 'fill', 'p': [5.5, -6.4, 62.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [11.5, 1.8, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.5},
        {'kind': 'fill', 'p': [17.5, -20.0, -3.0], 'n': [1, 0, 0], 'size': [1.6, 9.6, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.3},
        {'kind': 'fill', 'p': [15.0, -11.8, -3.0], 'n': [0.814, 0.581, 0], 'up': [-0.581, 0.814, 0], 'size': [1.6, 8.8, 3.0], 'mirrorX': True, 'color': COBALT, 'facing': 0.3},
        # orange marks on the engine block armour (concept: short bars and diagonal patches)
        {'kind': 'fill', 'p': [27.67, -18.5, -52.4], 'n': [1, 0, 0], 'size': [0.9, 6.0, 1.0], 'mirrorX': True, 'color': ORANGE},
        {'kind': 'fill', 'p': [27.67, -18.5, -79.0], 'n': [1, 0, 0], 'size': [0.9, 6.0, 1.0], 'mirrorX': True, 'color': ORANGE},
        {**HAZ, 'p': [27.67, -24.2, -62.5], 'n': [1, 0, 0], 'size': [4.0, 1.4, 1.2]},
        {**HAZ, 'p': [21.5, -9.8, -68.0], 'n': [0.645, 0.764, 0], 'up': [-0.764, 0.645, 0], 'size': [5.0, 1.2, 1.2]},
        # hazard frames: boat hatch, intake bays, shoulder vents, gun-gap faces
        {**HAZ, 'p': [17.5, -19.9, -19.0], 'n': [1, 0, 0], 'size': [8.6, 9.6, 1.6], 'border': 0.6},
        {**HAZ, 'p': [20.9, -9.4, -45.0], 'n': [0.645, 0.764, 0], 'up': [-0.764, 0.645, 0], 'size': [10.4, 7.8, 1.2], 'border': 0.55},
        {**HAZ, 'p': [0.0, -17.0, 42.9], 'n': [0, 0, 1], 'size': [26.0, 26.0, 0.8], 'border': 0.6, 'mirrorX': False},
        {**HAZ, 'p': [0.0, -17.0, 54.9], 'n': [0, 0, -1], 'size': [26.0, 26.0, 0.8], 'border': 0.6, 'mirrorX': False},
        # walkway edge lines in the gun gap (safety yellow) and on the spine
        {'kind': 'fill', 'p': [10.9, -26.3, 48.9], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.2, 12.0, 0.6], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
        {'kind': 'fill', 'p': [4.0, -5.5, 30.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.18, 62.0, 0.6], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
        # deck markings: turret arcs as bands, landing cross on the aft deck
        {'kind': 'fill', 'p': [0.0, -4.3, -60.8], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [10.0, 0.5, 0.6], 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
        # muzzle mouth: dark heat-stained metal on the lip
        {'kind': 'fill', 'p': [0.0, -18.55, 101.2], 'n': [0, 0, 1], 'size': [24.0, 18.0, 0.6], 'color': [0.33, 0.32, 0.31], 'wear': 0.5, 'rough': 0.5},
    ]
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'copper'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.77], 'rough': 0.62},
            'trim': {'color': [0.72, 0.72, 0.70], 'rough': 0.6},
            'belly': {'color': [0.42, 0.42, 0.43], 'rough': 0.72},
            'deck': {'color': [0.64, 0.64, 0.63], 'rough': 0.8},
            'dark': {'color': [0.22, 0.22, 0.23], 'rough': 0.7},
            'recess': {'color': [0.52, 0.52, 0.52], 'rough': 0.7},
            'metal': {'color': [0.46, 0.46, 0.46], 'rough': 0.45, 'metal': 0.5},
            'fin': {'color': [0.36, 0.36, 0.37], 'rough': 0.5, 'metal': 0.4},
            'glass': {'color': [0.13, 0.16, 0.2], 'rough': 0.1},
            'nozzle': {'color': [0.2, 0.2, 0.2], 'rough': 0.5, 'metal': 0.6},
            # railgun coils and bus bars: weathered copper (livery keeps part of the hue)
            'copper': {'color': [0.55, 0.33, 0.2], 'rough': 0.4, 'metal': 0.7},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': _frames(),
                  'bands': [-35.8, -32.9, -30.4, -27.8, -25.4, -22.7, -20.2, -17.6, -15.0, -12.1, -9.4, -6.4, -4.3, -1.3, 1.2,
                            4.3, 7.3, 10.3, 13.3, 16.3, 19.3, 22.3, 25.3],
                  'strakes': [0.0, 2.3, 4.4, 6.9, 9.4, 11.2, 13.3, 15.0, 17.5, 20.1, 22.4, 25.0, 27.7],
                  'width': 0.08, 'stagger': 2.9, 'tone': 0.07, 'dark': 0.5, 'access': 0.3, 'access_dark': 0.45},
        'normal': {'seam_depth': 0.015, 'access_depth': 0.008, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.35},
        'grime': {'ao': 0.35, 'crease': 0.35, 'edge': 0.55, 'blotch': 0.07, 'blotch2': 0.06, 'streak': 0.07},
        'decals': decals,
    }
