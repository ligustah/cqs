# UV-space rasterizer (numpy, no Blender needed): which triangle covers each texel of a W x H
# texture, with the barycentric weights, so per-corner attributes (ship-frame position, normal)
# and per-face values (region label) can be written into texture-aligned maps.
#
#   cover = raster(uv, W, H)            uv: (m, 3, 2) per-corner UVs of m triangles (glTF: v down)
#   cover.face  (H, W) int32  covering triangle, -1 = no triangle
#   cover.bary  (H, W, 3) float32
#   cover.interp(attr)  attr (m, 3, k) per-corner -> (H, W, k)
#
# Texel (x, y) is sampled at its centre ((x + 0.5) / W, (y + 0.5) / H) in glTF UV space (row 0 = v 0,
# the top of the image as stored). Triangles are binned by bounding-box size and rasterised as
# vectorised batches; where two triangles overlap (mirrored or stacked UVs) the later one wins.
import numpy as np


class Cover:
    def __init__(self, face, bary):
        self.face, self.bary = face, bary

    def interp(self, attr):
        f = self.face
        ok = f >= 0
        out = np.zeros(f.shape + (attr.shape[2],), np.float32)
        a = attr[f[ok]]  # (n, 3, k)
        out[ok] = np.einsum('nc,nck->nk', self.bary[ok], a)
        return out

    def per_face(self, vals, fill=-1):
        f = self.face
        out = np.full(f.shape, fill, dtype=np.asarray(vals).dtype)
        ok = f >= 0
        out[ok] = np.asarray(vals)[f[ok]]
        return out


def raster(uv, W, H, faces=None, dilate=0.0):
    """uv (m, 3, 2) -> Cover. faces: optional subset of triangle indices. dilate: barycentric
    slack (in texels, approximate) so seams get covered on both sides."""
    uv = np.asarray(uv, np.float64)
    m = len(uv)
    idx = np.arange(m) if faces is None else np.asarray(faces)
    face = np.full((H, W), -1, np.int32)
    bary = np.zeros((H, W, 3), np.float32)
    P = uv[idx] * np.array([W, H]) - 0.5  # texel-centre coordinates
    x0 = np.floor(P[:, :, 0].min(1)).astype(int); x1 = np.ceil(P[:, :, 0].max(1)).astype(int)
    y0 = np.floor(P[:, :, 1].min(1)).astype(int); y1 = np.ceil(P[:, :, 1].max(1)).astype(int)
    size = np.maximum(x1 - x0, y1 - y0) + 1
    edges = [0, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096 * 4]
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = np.where((size > lo) & (size <= hi))[0]
        if not len(sel):
            continue
        B = hi
        # chunk so a batch holds at most ~8M candidate texels
        step = max(1, int(8e6 // (B * B)))
        g = np.arange(B)
        for s in range(0, len(sel), step):
            ch = sel[s:s + step]
            a, b, c = P[ch, 0], P[ch, 1], P[ch, 2]
            X = x0[ch, None, None] + g[None, None, :]
            Y = y0[ch, None, None] + g[None, :, None]
            X = np.broadcast_to(X, (len(ch), B, B)); Y = np.broadcast_to(Y, (len(ch), B, B))
            den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
            den = np.where(np.abs(den) < 1e-12, 1e-12, den)[:, None, None]
            l1 = ((b[:, 1] - c[:, 1])[:, None, None] * (X - c[:, None, None, 0]) + (c[:, 0] - b[:, 0])[:, None, None] * (Y - c[:, None, None, 1])) / den
            l2 = ((c[:, 1] - a[:, 1])[:, None, None] * (X - c[:, None, None, 0]) + (a[:, 0] - c[:, 0])[:, None, None] * (Y - c[:, None, None, 1])) / den
            l3 = 1 - l1 - l2
            # slack in barycentric units ~ dilate texels / triangle extent
            ext = np.maximum(1.0, (np.abs(den[:, 0, 0]) ** 0.5))[:, None, None]
            e = -dilate / ext
            inside = (l1 >= e) & (l2 >= e) & (l3 >= e) & (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
            n, yy, xx = np.nonzero(inside)
            if not len(n):
                continue
            Xi, Yi = X[n, yy, xx], Y[n, yy, xx]
            face[Yi, Xi] = idx[ch[n]]
            bary[Yi, Xi] = np.stack([l1[n, yy, xx], l2[n, yy, xx], l3[n, yy, xx]], 1)
    return Cover(face, bary)
