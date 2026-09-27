# Geometry core of tools/blender/straighten.py: segmentation of a triangle mesh into near-planar
# regions, curved-region detection, per-region plane fits and the vertex solve that puts every
# vertex on its region's plane, on the intersection line of two regions or on the corner point
# of three or more, with every move clamped. Pure numpy on arrays (no bpy), so it can be tested
# on its own:
#
#   V (n,3) float64 vertex positions (world units), T (m,3) int triangle indices.
#
# Everything is scale-free: tolerances are given as fractions of the bounding-box diagonal.
import math
import heapq
import numpy as np


def face_geometry(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    cr = np.cross(b - a, c - a)
    area2 = np.linalg.norm(cr, axis=1)
    N = cr / np.maximum(area2, 1e-30)[:, None]
    return N, 0.5 * area2, (a + b + c) / 3.0


def edge_table(T):
    """Unique undirected edges and, per edge, the faces that use it.
    Returns (E (k,2) vertex pairs, edge_faces list-of-arrays via CSR (ef_ptr, ef_face), face_edges (m,3))."""
    m = len(T)
    e = np.stack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], axis=1).reshape(-1, 2)
    e.sort(axis=1)
    key = e[:, 0].astype(np.int64) * (int(T.max()) + 1) + e[:, 1]
    uniq, inv = np.unique(key, return_inverse=True)
    E = np.stack([uniq // (int(T.max()) + 1), uniq % (int(T.max()) + 1)], axis=1)
    face_of = np.repeat(np.arange(m), 3)
    order = np.argsort(inv, kind='stable')
    counts = np.bincount(inv, minlength=len(uniq))
    ptr = np.concatenate([[0], np.cumsum(counts)])
    return E, ptr, face_of[order], inv.reshape(m, 3)


def face_adjacency(T, ptr, ef_face):
    """CSR face adjacency across shared edges (non-manifold edges link every pair of their faces)."""
    m = len(T)
    counts = np.diff(ptr)
    pairs_a, pairs_b = [], []
    # manifold edges (the bulk): vectorised
    two = np.where(counts == 2)[0]
    fa, fb = ef_face[ptr[two]], ef_face[ptr[two] + 1]
    pairs_a += [fa, fb]
    pairs_b += [fb, fa]
    for k in np.where(counts > 2)[0]:
        fs = ef_face[ptr[k]:ptr[k + 1]]
        for i in range(len(fs)):
            for j in range(len(fs)):
                if i != j:
                    pairs_a.append(np.array([fs[i]]))
                    pairs_b.append(np.array([fs[j]]))
    A = np.concatenate(pairs_a)
    B = np.concatenate(pairs_b)
    o = np.lexsort((B, A))
    A, B = A[o], B[o]
    cnt = np.bincount(A, minlength=m)
    fptr = np.concatenate([[0], np.cumsum(cnt)])
    return fptr, B


def grow_regions(V, T, N, area, fptr, fnbr, cos_t, tol, locked=None):
    """Region growing by normal similarity to the region's running mean normal and distance of
    the candidate face's corners to the region's running plane. Seeds: flattest faces first
    (smallest mean normal deviation from their neighbours), larger faces first on ties.
    locked: optional bool (m,) faces that never join any region (label -1)."""
    m = len(T)
    # flatness score of each face: 1 - mean cos to neighbours
    src = np.repeat(np.arange(m), np.diff(fptr))
    cosn = np.einsum('ij,ij->i', N[src], N[fnbr])
    s = np.zeros(m)
    np.add.at(s, src, 1.0 - cosn)
    s /= np.maximum(np.diff(fptr), 1)
    order = np.lexsort((-area, np.round(s, 4)))
    label = np.full(m, -1, dtype=np.int64)
    if locked is not None:
        label[locked] = -2
    Vl = V.tolist()
    Tl = T.tolist()
    Nl = N.tolist()
    Al = area.tolist()
    Cl = ((V[T[:, 0]] + V[T[:, 1]] + V[T[:, 2]]) / 3.0).tolist()
    fp = fptr.tolist()
    fn = fnbr.tolist()
    lab = label.tolist()
    r = 0
    for seed in order.tolist():
        if lab[seed] != -1:
            continue
        lab[seed] = r
        n = Nl[seed]; a = Al[seed]; c = Cl[seed]
        nx, ny, nz = n[0] * a, n[1] * a, n[2] * a
        cx, cy, cz = c[0] * a, c[1] * a, c[2] * a
        asum = a
        stack = [seed]
        while stack:
            f = stack.pop()
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            ux, uy, uz = nx / ln, ny / ln, nz / ln
            ox, oy, oz = cx / asum, cy / asum, cz / asum
            for k in range(fp[f], fp[f + 1]):
                g = fn[k]
                if lab[g] != -1:
                    continue
                ng = Nl[g]
                if ng[0] * ux + ng[1] * uy + ng[2] * uz < cos_t:
                    continue
                ok = True
                for vi in Tl[g]:
                    p = Vl[vi]
                    if abs((p[0] - ox) * ux + (p[1] - oy) * uy + (p[2] - oz) * uz) > tol:
                        ok = False
                        break
                if not ok:
                    continue
                lab[g] = r
                ag = Al[g]; cg = Cl[g]
                nx += ng[0] * ag; ny += ng[1] * ag; nz += ng[2] * ag
                cx += cg[0] * ag; cy += cg[1] * ag; cz += cg[2] * ag
                asum += ag
                stack.append(g)
        r += 1
    label = np.array(lab, dtype=np.int64)
    label[label == -2] = -1
    return label


def fit_planes(V, T, area, label, R):
    """Weighted PCA plane per region from its triangle corners (weight area/3).
    Returns normals (R,3), offsets d (R,) with n.x = d, eigenvalue spread, region area."""
    ok = label >= 0
    L = label[ok]
    w = np.repeat(area[ok] / 3.0, 3)
    P = V[T[ok]].reshape(-1, 3)
    LL = np.repeat(L, 3)
    W = np.bincount(LL, weights=w, minlength=R)
    S = np.zeros((R, 3))
    for k in range(3):
        S[:, k] = np.bincount(LL, weights=w * P[:, k], minlength=R)
    C = S / np.maximum(W, 1e-30)[:, None]
    M = np.zeros((R, 3, 3))
    for i in range(3):
        for j in range(i, 3):
            M[:, i, j] = np.bincount(LL, weights=w * P[:, i] * P[:, j], minlength=R)
            M[:, j, i] = M[:, i, j]
    Cov = M / np.maximum(W, 1e-30)[:, None, None] - C[:, :, None] * C[:, None, :]
    ev, evec = np.linalg.eigh(Cov)
    n = evec[:, :, 0]
    return n, C, ev, W


def orient_planes(n, N, area, label, R):
    ok = label >= 0
    s = np.zeros((R, 3))
    for k in range(3):
        s[:, k] = np.bincount(label[ok], weights=N[ok, k] * area[ok], minlength=R)
    flip = np.einsum('ij,ij->i', n, s) < 0
    n = n.copy()
    n[flip] *= -1
    return n


def region_stats(V, T, label, R, n, C):
    """Per region: max |distance| of its corners to its plane."""
    ok = np.where(label >= 0)[0]
    L = label[ok]
    P = V[T[ok]]  # (k,3,3)
    d = np.abs(np.einsum('kcj,kj->kc', P - C[L][:, None, :], n[L])).max(axis=1)
    dmax = np.zeros(R)
    np.maximum.at(dmax, L, d)
    return dmax, d, ok


def quadratic_curvature(V, T, label, r_faces, n, C):
    """Fit h = a u^2 + b uv + c v^2 + d u + e v + f over a region's vertices in its plane frame.
    Returns (sagitta of the quadratic part over the region's extent, fraction of the plane
    residual variance the quadratic explains, principal curvatures (k1, k2) sorted by |k|)."""
    vid = np.unique(T[r_faces].ravel())
    P = V[vid] - C
    # plane frame
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a); u /= np.linalg.norm(u)
    v = np.cross(n, u)
    x, y, h = P @ u, P @ v, P @ n
    if len(vid) < 8:
        return 0.0, 0.0, (0.0, 0.0), 0.0
    # principal extent
    Q = np.stack([x, y], 1)
    _, _, vt = np.linalg.svd(Q - Q.mean(0), full_matrices=False)
    proj = Q @ vt.T
    ext = (proj.max(0) - proj.min(0))
    A = np.stack([x * x, x * y, y * y, x, y, np.ones_like(x)], 1)
    coef, *_ = np.linalg.lstsq(A, h, rcond=None)
    res2 = h - A @ coef
    var0 = float(np.mean(h * h)) + 1e-30
    var2 = float(np.mean(res2 * res2))
    H = np.array([[2 * coef[0], coef[1]], [coef[1], 2 * coef[2]]])
    k, kv = np.linalg.eigh(H)
    i = int(np.argmax(np.abs(k)))
    kdir = kv[:, i]
    # extent of the region along the direction of strongest curvature: a cylinder strip curves
    # across its width, a lumpy (bowed) flat panel usually along its length
    t = x * kdir[0] + y * kdir[1]
    w_along = float(t.max() - t.min())
    Lmax = float(ext.max())
    sag = abs(k[i]) * w_along * w_along / 8.0
    k = sorted(k, key=abs)
    # curvature runs across the short side (cylinder strip), or both ways alike (dome / bell)
    across = w_along < 0.75 * Lmax or abs(k[0]) > 0.5 * abs(k[1])
    if not across:
        sag = -sag
    return sag, 1.0 - var2 / var0, (float(k[0]), float(k[1])), Lmax


def solve_vertices(V, T, label, planar, n, d, clamp, lam=1e-3, parallel_deg=4.0, frozen=None):
    """Move every vertex that touches a planar region: onto its plane (1 region), onto the
    intersection line (2), or the least-squares corner point (3+). Near-parallel planes
    (< parallel_deg) are averaged instead of intersected. Moves longer than clamp are
    re-solved with a stronger pull toward the original position, then scaled to clamp.
    Returns new V and per-vertex region count."""
    nv = len(V)
    fl = label.copy()
    fl[~planar[np.maximum(label, 0)] | (label < 0)] = -1
    # vertex -> set of planar regions (unique pairs)
    vf = np.stack([T.ravel(), np.repeat(fl, 3)], 1)
    vf = vf[vf[:, 1] >= 0]
    vf = np.unique(vf, axis=0)
    cnt = np.bincount(vf[:, 0], minlength=nv)
    ptr = np.concatenate([[0], np.cumsum(cnt)])
    Vn = V.copy()
    cos_par = math.cos(math.radians(parallel_deg))
    moved = np.zeros(nv, dtype=bool)
    # 1 region: vectorised projection
    one = np.where(cnt == 1)[0]
    r1 = vf[ptr[one], 1]
    dist = np.einsum('ij,ij->i', V[one], n[r1]) - d[r1]
    Vn[one] = V[one] - dist[:, None] * n[r1]
    moved[one] = True
    # 2+ regions: small least-squares systems
    I3 = np.eye(3)
    for v in np.where(cnt >= 2)[0].tolist():
        rs = vf[ptr[v]:ptr[v + 1], 1]
        ns, ds = n[rs], d[rs]
        # merge near-parallel planes (greedy clusters) into averaged planes
        groups = []
        for i in range(len(rs)):
            for g in groups:
                if abs(float(ns[i] @ ns[g[0]])) > cos_par:
                    g.append(i)
                    break
            else:
                groups.append([i])
        gn, gd = [], []
        for g in groups:
            s = np.zeros(3); sd = 0.0
            for i in g:
                sg = 1.0 if float(ns[i] @ ns[g[0]]) > 0 else -1.0
                s += sg * ns[i]; sd += sg * ds[i]
            ln = np.linalg.norm(s)
            gn.append(s / ln); gd.append(sd / ln)
        gn = np.array(gn); gd = np.array(gd)
        x0 = V[v]
        l = lam
        for _ in range(6):
            A = gn.T @ gn + l * I3
            b = gn.T @ gd + l * x0
            x = np.linalg.solve(A, b)
            if np.linalg.norm(x - x0) <= clamp:
                break
            l *= 10.0
        Vn[v] = x
        moved[v] = True
    D = Vn - V
    ln = np.linalg.norm(D, axis=1)
    over = ln > clamp
    D[over] *= (clamp / ln[over])[:, None]
    if frozen is not None:
        D[frozen] = 0.0
    return V + D, cnt, ln, over


def taubin(V, T, mask, iters=4, lam=0.5, mu=-0.53):
    """Taubin (lambda|mu) smoothing of the masked vertices over the mesh's 1-ring (volume-preserving)."""
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    E = np.unique(np.sort(E, 1), axis=0)
    a, b = E[:, 0], E[:, 1]
    deg = np.bincount(a, minlength=len(V)) + np.bincount(b, minlength=len(V))
    X = V.copy()
    for it in range(iters * 2):
        f = lam if it % 2 == 0 else mu
        S = np.zeros_like(X)
        np.add.at(S, a, X[b])
        np.add.at(S, b, X[a])
        Lp = S / np.maximum(deg, 1)[:, None] - X
        X[mask] += f * Lp[mask]
    return X
