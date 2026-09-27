"""De-mush the texture of a straightened fal / Tripo hull, in texture space.

    python hulltex.py in.glb uvmaps.npz out.glb [--spec spec.json] [--tris N] [--tex 4096]
                      [--tau 0.06] [--iters 60] [--tone 0.5] [--tile 6] [--normal planar-flat|keep]
                      [--debug DIR]

(`python` = a Python with numpy, scipy and pillow; Blender is not needed. in.glb and uvmaps.npz
come from tools/blender/straighten.py ... --uvmaps 4096, which writes texture-aligned maps of the
straightened mesh: covering face, class (free / planar / curved), planar region, ship-frame
position and normal per texel.)

Tripo bakes soft studio lighting, grime smears and wavy relief into its base colour and normal
map. This pass keeps the paint (panel-to-panel tone, markings, panel lines) and removes the rest:

 1. DE-LIGHT. At 1/4 resolution the covered texels are joined into "paint areas": 4-neighbours
    whose colours differ by less than --tau (max channel, sRGB 0-1) and whose normals agree
    (the texel graph never crosses a UV seam, a paint edge or a crease). Inside each area an
    edge-stopped diffusion (--iters) estimates the slowly varying colour; the base colour is
    multiplied by (area mean / that estimate) per channel, clamped to 0.7-1.4, so baked light
    gradients and soft smears flatten to the area's own paint while every edge, stencil and thin
    panel line is kept (their areas are separate).
 2. PLATING TONE. A panel-to-panel tone from the PATINA hull set's height map (assets/materials/
    hull), sampled tri-planar in the SHIP FRAME at --tile metres per repeat with the weights of
    src/lib/patina.js, so it lines up with the runtime PATINA detail layer (normal, roughness,
    cavity) of a GLB delivered in the ship frame (rotate [0, 0, 0], e.g. an assemble.py output).
    base *= 1 + tone * (h / mean(h) - 1).
 3. PAINT (ship frame, metres): repaint the texels whose position lies
    in a feature's oriented box (spec "features", shared with assemble.py `flatten`), e.g. under a
    pressed relief or a garbled hull number:
      { id, p: [x,y,z] (centre), n, up?: [0,1,0], size: [w, h, d] (along right = up x n, up, n),
        mirrorX?, flatten?: ..., paint: { fill: 'ring' | [r,g,b] (sRGB 0-1), ring?: m, flatNormal?,
        (ring = median de-lit colour on a band just outside the box, facing the same way),
        text?: { string: 'K-214', height: m, color: [r,g,b], offset?: [right, up] m } }
    Painted texels also get a flat normal. The stencil uses the fleet's stencil construction
    (strokes 0.185 x height, butt ends, mitred corners), reading left to right seen from outside.
 4. NORMAL. --normal planar-flat: texels of planar regions get a flat tangent-space normal (the
    straightened planes and the runtime PATINA layer carry the relief there); free and curved
    texels keep the (straighten high-passed) map.
 5. Write: the images replaced in the GLB; --tris simplifies the mesh (meshopt, --error limit;
    it keeps UV and normal seams, and the straightened planes lose nothing), then
    tools/optimize-glb.mjs (WebP at --tex, meshopt compression).
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import straighten_js as sjs  # noqa: E402  (node HEAD: gltf-transform + meshopt + sharp)

IO = sjs.HEAD + r"""
const doc = await io.read(A.input);
const root = doc.getRoot();
const mats = root.listMaterials();
if (mats.length !== 1) throw new Error('hulltex expects one material');
const m = mats[0];
const slots = { base: m.getBaseColorTexture(), normal: m.getNormalTexture(), orm: m.getMetallicRoughnessTexture() };
if (A.mode === 'simplify') {
  const { weld, simplify } = await import('@gltf-transform/functions');
  const { MeshoptSimplifier } = await import('meshoptimizer');
  await MeshoptSimplifier.ready;
  await doc.transform(dequantize());
  const count = () => root.listMeshes().flatMap((mm) => mm.listPrimitives()).reduce((n, p) => n + p.getIndices().getCount() / 3, 0);
  const before = count();
  await doc.transform(weld(), simplify({ simplifier: MeshoptSimplifier, ratio: Math.min(1, A.tris / before), error: A.error, lockBorder: false }));
  for (const e of root.listExtensionsUsed()) if (/meshopt|quantization/.test(e.extensionName)) e.dispose();
  await io.write(A.output, doc);
  await writeFile(A.report, JSON.stringify({ before, after: count() }));
} else if (A.mode === 'extract') {
  const info = {};
  for (const [k, t] of Object.entries(slots)) {
    if (!t) continue;
    await sharp(Buffer.from(t.getImage())).removeAlpha().png({ compressionLevel: 1 }).toFile(`${A.dir}/${k}.png`);
    info[k] = t.getSize();
  }
  await writeFile(`${A.dir}/info.json`, JSON.stringify(info));
} else {
  await doc.transform(dequantize());
  for (const [k, t] of Object.entries(slots)) {
    if (!t || !A.replace[k]) continue;
    const png = await sharp(A.replace[k]).png({ compressionLevel: 6 }).toBuffer();
    t.setImage(new Uint8Array(png)).setMimeType('image/png');
  }
  for (const e of root.listExtensionsUsed()) if (/meshopt|quantization/.test(e.extensionName)) e.dispose();
  await io.write(A.output, doc);
}
"""


def node(mode, **args):
    env = dict(os.environ, STRAIGHTEN_ARGS=json.dumps({'mode': mode, **args}))
    r = subprocess.run(['node', '--input-type=module', '-e', IO], cwd=SCENE, env=env, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])


def log(*a):
    print('[hulltex]', *a, flush=True)


# ------------------------------------------------------------------------------------------
# 1. de-light
# ------------------------------------------------------------------------------------------
def block_mean(a, f, w):
    H, W = w.shape
    h, wd = H // f, W // f
    ww = w.reshape(h, f, wd, f).sum((1, 3))
    if a.ndim == 2:
        s = (a * w).reshape(h, f, wd, f).sum((1, 3))
    else:
        s = (a * w[..., None]).reshape(h, f, wd, f, a.shape[2]).sum((1, 3))
    d = np.maximum(ww, 1e-9)
    return (s / (d if a.ndim == 2 else d[..., None])), ww / (f * f)


def delight(col, cov, nrm, tau=0.06, iters=60, f=4, min_area=40, clamp=(0.7, 1.4), dbg=None):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    t0 = time.time()
    w = cov.astype(np.float32)
    C, frac = block_mean(col, f, w)
    N, _ = block_mean(nrm.astype(np.float32), f, w)
    N /= np.maximum(np.linalg.norm(N, axis=2), 1e-9)[..., None]
    valid = frac > 0.99
    h, wd = valid.shape
    ids = np.arange(h * wd).reshape(h, wd)
    rows, cols = [], []
    for sl_a, sl_b in (((slice(None), slice(0, -1)), (slice(None), slice(1, None))), ((slice(0, -1), slice(None)), (slice(1, None), slice(None)))):
        ok = valid[sl_a] & valid[sl_b]
        ok &= np.abs(C[sl_a] - C[sl_b]).max(2) < tau
        ok &= (N[sl_a] * N[sl_b]).sum(2) > 0.97
        rows.append(ids[sl_a][ok]); cols.append(ids[sl_b][ok])
    r = np.concatenate(rows); c = np.concatenate(cols)
    G = coo_matrix((np.ones(len(r), np.float32), (r, c)), shape=(h * wd, h * wd)).tocsr()
    G = G + G.T
    ncomp, comp = connected_components(G, directed=False)
    comp = np.where(valid.ravel(), comp, -1)
    deg = np.asarray(G.sum(1)).ravel()
    D = C.reshape(-1, 3).astype(np.float64)
    for _ in range(iters):
        D = (D + G @ D) / (1 + deg)[:, None]
    cnt = np.bincount(comp[comp >= 0], minlength=ncomp)
    M = np.stack([np.bincount(comp[comp >= 0], weights=C.reshape(-1, 3)[comp >= 0, k], minlength=ncomp) for k in range(3)], 1) / np.maximum(cnt, 1)[:, None]
    g = np.ones((h * wd, 3))
    ok = (comp >= 0)
    ok[ok] &= cnt[comp[ok]] >= min_area
    g[ok] = M[comp[ok]] / np.maximum(D[ok], 1e-3)
    g = np.clip(g, *clamp).reshape(h, wd, 3)
    # up to full resolution: normalised bilinear over the valid blocks (partial blocks at the
    # island rims take their neighbours' gain)
    from scipy.ndimage import zoom, uniform_filter
    vw = valid.astype(np.float64)
    num = uniform_filter(g * vw[..., None], size=(3, 3, 1)); den = uniform_filter(vw, 3)
    g = np.where(valid[..., None], g, np.where(den[..., None] > 1e-6, num / np.maximum(den, 1e-6)[..., None], 1.0))
    G4 = np.stack([zoom(g[..., k], f, order=1) for k in range(3)], 2).astype(np.float32)
    out = np.where(cov[..., None], np.clip(col * G4, 0, 1), col)
    stats = {'components': int(ncomp), 'areas_used': int((cnt >= min_area).sum()), 'gain_p5_p95': [round(float(v), 3) for v in np.percentile(g[valid], [5, 95])], 's': round(time.time() - t0, 1)}
    if dbg:
        from PIL import Image
        Image.fromarray((np.clip((g - 0.7) / 0.7, 0, 1) * 255).astype(np.uint8)).save(f'{dbg}/gain.png')
        rng = np.random.default_rng(3)
        pal = rng.random((ncomp + 1, 3))
        cm = np.where(comp.reshape(h, wd)[..., None] >= 0, pal[comp.reshape(h, wd)], 0)
        Image.fromarray((cm * 255).astype(np.uint8)).save(f'{dbg}/areas.png')
    return out, stats


# ------------------------------------------------------------------------------------------
# 2. plating tone (PATINA height, tri-planar in the ship frame, as patina.js)
# ------------------------------------------------------------------------------------------
def triplanar(img, pos, nrm, tile):
    Hh, Ww = img.shape[:2]
    p = pos / tile
    w = np.abs(nrm) ** 6
    w /= np.maximum(w.sum(-1, keepdims=True), 1e-9)

    def samp(u, v):  # bilinear, repeat; texture2D(t, uv): u -> x, v -> y (glTF / three flipY false?)
        x = (u % 1) * Ww - 0.5; y = (v % 1) * Hh - 0.5
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
        x0 %= Ww; y0 %= Hh; x1 = (x0 + 1) % Ww; y1 = (y0 + 1) % Hh
        return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy) + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)
    # three.js TextureLoader textures have flipY = true: uv (u, v) reads image row (1 - v)
    return (samp(p[..., 2], 1 - p[..., 1]) * w[..., 0] + samp(p[..., 0], 1 - p[..., 2]) * w[..., 1] + samp(p[..., 0], 1 - p[..., 1]) * w[..., 2])


# ------------------------------------------------------------------------------------------
# 3. paint ops: fill + stencil text
# ------------------------------------------------------------------------------------------
def stencil_alpha(text, h, px_per_m=200):
    """Stencil text alpha image (PIL 'L'), height h metres at px_per_m; returns (alpha, width_m).
    Fleet stencil: strokes 0.185 h, butt ends, mitred corners."""
    from PIL import Image, ImageDraw
    H = int(round(h * px_per_m)); s = 0.185 * H; g = 0.11 * H
    widths = {'K': 0.62, '-': 0.40, '1': 0.46, '2': 0.66, '4': 0.66, ' ': 0.4}
    Wt = int(sum(widths.get(ch, 0.62) * H for ch in text) + g * (len(text) - 1)) + 4
    im = Image.new('L', (Wt, H + 4), 0)
    d = ImageDraw.Draw(im)
    x = 2; y0 = 2; i = s / 2

    def poly(pts):
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)

    def bar(x0, y0_, x1, y1):
        d.rectangle([x0, y0_, x1, y1], fill=255)

    def stroke(pts):  # thick polyline with mitred joins (drawn as quads + corner squares)
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** 0.5
            nx, ny = -dy / L * s / 2, dx / L * s / 2
            poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        for (cx, cy) in pts[1:-1]:
            bar(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
    for ch in text:
        w = widths.get(ch, 0.62) * H
        top, bot, mid = y0, y0 + H, y0 + 0.52 * H
        if ch == 'K':
            bar(x, top, x + s, bot)
            j = x + s * 0.9
            stroke([(x + w - i * 0.9, top + i * 0.2), (j, mid)])
            stroke([(j + s * 0.35, mid - s * 0.25), (x + w - i * 0.9, bot - i * 0.2)])
            bar(x + w - s * 1.05, top, x + w, top + s * 0.02)
        elif ch == '-':
            bar(x, y0 + 0.53 * H - s * 0.525, x + w, y0 + 0.53 * H + s * 0.525)
        elif ch == '1':
            sx = x + w - s * 1.1
            bar(sx, top, sx + s * 1.1, bot)
            poly([(sx, top), (sx, top + s * 1.25), (x, top + 0.36 * H), (x, top + 0.36 * H - s * 1.25)])
        elif ch == '2':
            stroke([(x, top + i), (x + w - i, top + i), (x + w - i, mid), (x + i, mid), (x + i, bot - i), (x + w, bot - i)])
        elif ch == '4':
            stroke([(x + i, top), (x + i, top + 0.64 * H), (x + w, top + 0.64 * H)])
            bar(x + w - s * 1.1 - 0.12 * H, top + 0.22 * H, x + w - 0.12 * H, bot)
        x += w + g
    return im, (Wt) / px_per_m, (H + 4) / px_per_m


def frames(f):
    """Oriented box(es) of a spec feature (as assemble.py feature_frames): [(centre, R, half, mirrored)],
    R columns = right, up, n; right = up x n (reads left to right seen from outside)."""
    out = []
    for mir in ([False, True] if f.get('mirrorX') else [False]):
        s = np.array([-1.0, 1, 1]) if mir else np.ones(3)
        n = np.array(f['n'], float) * s; n /= np.linalg.norm(n)
        up = np.array(f.get('up', [0, 1, 0]), float) * s
        up = up - n * (up @ n); up /= np.linalg.norm(up)
        R = np.stack([np.cross(up, n), up, n], 1)
        out.append((np.array(f['p'], float) * s, R, np.array(f['size'], float) / 2, mir))
    return out


def paint(col, nrm_img, cov, pos, nrmmap, feats, dbg=None):
    """Repaint the texels of each feature's oriented box (spec `features` with `paint`)."""
    from scipy.ndimage import uniform_filter
    out = []
    flat = np.array([128, 128, 255], np.uint8)
    ci = np.where(cov)
    P = pos[ci]; N = nrmmap[ci]
    for f in feats:
        pt = f['paint'] if isinstance(f['paint'], dict) else {}
        for c, R, half, mir in frames(f):
            L = (P - c) @ R
            nd = N @ R[:, 2]
            # a pressed relief (flatten) turns its side walls to face n: repaint them too
            inside = np.all(np.abs(L) <= half, 1) & (nd > pt.get('facing', -1.0 if f.get('flatten') else 0.5))
            r = pt.get('ring', 1.0)
            ring = np.all(np.abs(L) <= half + np.array([r, r, 0]), 1) & ~np.all(np.abs(L) <= half, 1) & (nd > 0.9)
            fill = pt.get('fill', 'ring')
            cur = col[ci[0], ci[1]]
            if fill == 'ring':
                cc = np.median(cur[ring], 0) if ring.sum() > 20 else np.median(cur[inside], 0)
            else:
                cc = np.array(fill, float)
            rng = np.random.default_rng(11)
            k = int(inside.sum())
            grain = min(float(np.std(cur[ring].mean(1))) if ring.sum() > 20 else 0.0, 0.012)
            new = np.tile(cc, (k, 1)) * (1 + rng.normal(0, grain, (k, 1)))
            txt = pt.get('text')
            if txt:
                im, wm, hm = stencil_alpha(txt['string'], txt['height'])
                a = uniform_filter(np.asarray(im, np.float32) / 255, 5)
                ox, oy = txt.get('offset', [0, 0])
                u = (L[inside, 0] - ox) / wm + 0.5
                v = 0.5 - (L[inside, 1] - oy) / hm
                A = np.zeros(k, np.float32)
                okk = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
                X = np.clip((u[okk] * a.shape[1]).astype(int), 0, a.shape[1] - 1)
                Y = np.clip((v[okk] * a.shape[0]).astype(int), 0, a.shape[0] - 1)
                A[okk] = a[Y, X]
                tc = np.array(txt['color'], float)
                new = new * (1 - A[:, None]) + (tc[None, :] * (1 - 0.05 * rng.random((k, 1)))) * A[:, None]
            yy, xx = ci[0][inside], ci[1][inside]
            col[yy, xx] = np.clip(new, 0, 1)
            if pt.get('flatNormal', True):
                nrm_img[yy, xx] = flat
            out.append({'id': f.get('id'), 'mirror': mir, 'texels': k, 'ring_texels': int(ring.sum()), 'fill': [round(float(v), 3) for v in cc]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('uvmaps'); ap.add_argument('output')
    ap.add_argument('--spec'); ap.add_argument('--tris', type=int, default=0); ap.add_argument('--tex', type=int, default=4096)
    ap.add_argument('--error', type=float, default=0.004, help='simplification error limit (fraction of the mesh extent) for --tris')
    ap.add_argument('--tau', type=float, default=0.06); ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--tone', type=float, default=0.5); ap.add_argument('--tile', type=float, default=6.0)
    ap.add_argument('--normal', default='planar-flat', choices=['planar-flat', 'flat', 'keep'])
    ap.add_argument('--blue', type=float, default=0.55, help='cobalt markings -> this neutral grey (sRGB 0-1; the dark livery would read dark blue paint as glass or a hole); 0 = keep')
    ap.add_argument('--no-delight', action='store_true'); ap.add_argument('--debug')
    a = ap.parse_args()
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    t0 = time.time()
    out = os.path.abspath(a.output)
    work = os.path.splitext(out)[0] + '.hulltex'
    os.makedirs(work, exist_ok=True)
    dbg = os.path.abspath(a.debug) if a.debug else None
    if dbg:
        os.makedirs(dbg, exist_ok=True)
    node('extract', input=os.path.abspath(a.input), dir=work)
    spec = json.load(open(a.spec)).get('texture', {}) if a.spec else {}
    z = np.load(a.uvmaps)
    face, cls = z['face'], z['cls']
    pos = z['pos'].astype(np.float32); nrmmap = z['nrm'].astype(np.float32)
    nrmmap /= np.maximum(np.linalg.norm(nrmmap, axis=2), 1e-9)[..., None]
    col = np.asarray(Image.open(f'{work}/base.png').convert('RGB'), np.float32) / 255
    nimg = np.asarray(Image.open(f'{work}/normal.png').convert('RGB')).copy()
    if col.shape[:2] != face.shape:
        raise SystemExit(f'uvmaps {face.shape} != base colour {col.shape[:2]}')
    cov = face >= 0
    report = {'input': a.input, 'options': vars(a)}
    if not a.no_delight:
        col, report['delight'] = delight(col, cov, nrmmap, tau=spec.get('tau', a.tau), iters=spec.get('iters', a.iters), dbg=dbg)
        log('delight', report['delight'])
    if a.blue:
        mx, mn = col.max(2), col.min(2)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        r_, g_, b_ = col[..., 0], col[..., 1], col[..., 2]
        hue = np.degrees(np.arctan2(np.sqrt(3) * (g_ - b_), 2 * r_ - g_ - b_)) % 360
        w = np.clip((sat - 0.3) / 0.15, 0, 1) * (mx > 0.2) * ((hue > 190) & (hue < 260)) * cov
        col = col * (1 - w[..., None]) + a.blue * w[..., None]
        report['blue_texels'] = int((w > 0.5).sum())
    tone = spec.get('tone', a.tone)
    if tone:
        pat = os.path.join(SCENE, 'assets/materials/hull/height.webp')
        hm = np.asarray(Image.open(pat).convert('L'), np.float32) / 255
        h = np.zeros(cov.shape, np.float32)
        h[cov] = triplanar(hm, pos[cov], nrmmap[cov], spec.get('tile', a.tile))
        k = 1 + tone * (h / hm.mean() - 1)
        col = np.where(cov[..., None], np.clip(col * k[..., None], 0, 1), col)
        report['tone'] = {'amount': tone, 'tile': spec.get('tile', a.tile), 'k_p5_p95': [round(float(v), 3) for v in np.percentile(k[cov], [5, 95])]}
    feats = [f for f in (json.load(open(a.spec)).get('features', []) if a.spec else []) if f.get('paint')]
    if feats:
        report['paint'] = paint(col, nimg, cov, pos, nrmmap, feats, dbg)
        log('paint', report['paint'])
    if a.normal in ('planar-flat', 'flat'):
        pl = (cls == 1) if a.normal == 'planar-flat' else (cls >= 0) & (cls != 2)
        nimg[pl] = [128, 128, 255]
        report['normal_flat_texels'] = int(pl.sum())
    Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{work}/base-new.png')
    Image.fromarray(nimg).save(f'{work}/normal-new.png')
    if dbg:
        Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).resize((2048, 2048)).save(f'{dbg}/base-new-2k.jpg')
    raw = os.path.join(work, 'merged.glb')
    node('replace', input=os.path.abspath(a.input), output=raw, replace={'base': f'{work}/base-new.png', 'normal': f'{work}/normal-new.png'})
    if a.tris:
        simp = os.path.join(work, 'simplified.glb')
        node('simplify', input=raw, output=simp, tris=a.tris, error=a.error, report=os.path.join(work, 'simplify.json'))
        report['simplify'] = json.load(open(os.path.join(work, 'simplify.json')))
        log('simplify', report['simplify'])
        raw = simp
    r = subprocess.run(['node', 'tools/optimize-glb.mjs', raw, out, '--tris', '100000000', '--tex', str(a.tex)], cwd=SCENE, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    log(r.stdout.strip())
    report['bytes'] = os.path.getsize(out)
    report['seconds'] = round(time.time() - t0, 1)
    json.dump(report, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
    log(f'done {report["seconds"]}s -> {out}')


if __name__ == '__main__':
    main()
