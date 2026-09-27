# Mesh straightening for the fal / Tripo image-to-3D hulls: keep what the reconstruction made,
# but turn its lumpy armour panels into planes, its wavering edges into straight lines and its
# soft chamfer corners into points, with the same silhouette and the same texture.
#
#   <blender-python> tools/blender/straighten.py in.glb out.glb [--preset corvette] [--opts]
#
# Method (see straighten_core.py for the geometry):
#  1. node: decode meshopt / dequantise, drop the textures (Blender gets geometry only).
#  2. Blender: apply the node transform, weld (UVs stay per corner), drop duplicate faces,
#     dissolve degenerate triangles, triangulate.
#  3. Segment: grow regions from the flattest faces by normal similarity to the region's running
#     mean normal (--angle) and distance to its running plane (--tol, fraction of the bbox
#     diagonal). Regions under --min-area / --min-faces are merged into a neighbour whose plane
#     fits them, else left free (untouched).
#  4. Curved surfaces (bells, barrels, domes, cylinders): a region whose own quadratic fit explains
#     most of its deviation from its plane with a sagitta above --curv-sag, or that belongs to a
#     chain of shallow (< --chain-deg) creases with parallel crease axes (a faceted cylinder), is
#     'curved': it is left as generated (optionally Taubin-smoothed, --smooth-curved).
#  5. Weighted PCA plane per planar region. Each vertex goes onto its region's plane, onto the
#     intersection line of two regions, or the least-squares corner of three or more, with a
#     growing pull toward its original position if that point is further than --clamp, then a
#     hard clamp. Vertices inside --keep-box boxes never move.
#  6. Normals: planar faces get their plane's normal on every corner (flat panels, exact creases);
#     other faces are smooth with sharp edges above --crease; exported as split normals.
#  7. node: the original GLB with its mesh replaced (UVs are the original ones, so base colour and
#     ORM are reused as they are) and the normal map kept, high-passed (the low-frequency lumps
#     removed in UV space: --normal highpass, --nrm-sigma) or dropped; then
#     tools/optimize-glb.mjs (WebP at the input's texture size, meshopt).
#
# Writes out.glb and out.json (metrics). --debug writes out-regions.glb (vertex colours: planar
# regions pastel, curved red, free grey) next to it.
import argparse
import json
import math
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SCENE = os.path.dirname(os.path.dirname(HERE))

import straighten_core as core  # noqa: E402
import straighten_js as js  # noqa: E402

# Per-ship presets: the frame from src/ships/*.js (rotate, length) for metric reports and
# ship-frame keep boxes, plus tuned options. Anything on the command line overrides them.
PRESETS = {
    'fighter': dict(rotate=(0, -90, 0), length=71.712),
    'corvette': dict(rotate=(0, -90, 0), length=107.1),
    'corvette-live': dict(rotate=(0, -90, 0), length=108.1),  # working-tree hull (src/ships/corvette.js now says 108.1)
    # the v7 clean corvette hull, assembly pilot 2: small facets (bridge tower tiers, pads) count as
    # planar regions (down to ~1.2 m^2, 4 faces), and the remaining free faces shade sharp above 20
    # degrees, so lumps read as facets instead of smooth blotches
    'corvette-v7': dict(rotate=(0, -90, 0), length=108.1, min_area=0.0001, min_faces=4, crease=20.0),
    'freighter': dict(rotate=(0, -90, 0), length=134.12),
    'freighter-troops': dict(rotate=(0, -90, 0), length=128.84),
    # long, gently faceted bow: blend the shallow creases, do not call the crowned bow plates a cylinder
    'destroyer': dict(rotate=(0, -90, 0), length=204.21, soft=12.0, chain_deg=9.0),
    # the hangar cavity (liveryKeep / interiorLightGate boxes of src/ships/carrier.js, ship frame,
    # metres) keeps its geometry: scale-check ray-casts the deck and the openings
    # 900 m: the diagonal-relative tolerances would allow 2 m moves; halve them (untuned, dry-run only)
    'carrier': dict(rotate=(0, -90, 0), length=900, tol=0.0007, clamp=0.001,
                    keep_box=['-133,-97.5,-277,135,4,425']),
    # parts: already in metres, identity frame
    'pane': dict(rotate=(0, 0, 0), length=None, free_normals='original'),
    'container': dict(rotate=(0, 0, 0), length=None, free_normals='original'),
}

DEFAULTS = dict(angle=10.0, tol=0.0012, clamp=0.002, min_area=0.0004, min_faces=6,
                merge_angle=14.0, curv_sag=0.6, curv_expl=0.7, chain_deg=16.0, crease=35.0,
                parallel=4.0, soft=8.0, free_normals='crease', smooth_curved=0, weld=1e-6, normal='highpass', nrm_sigma=0.006,
                variants='', tex=0, uvmaps=0, tris=10_000_000, rotate=None, length=None, keep_box=None,
                debug=False, optimize=True, work=None)


def parse():
    ap = argparse.ArgumentParser(description='Straighten a lumpy hard-surface GLB (planar panels, straight edges).')
    ap.add_argument('input'); ap.add_argument('output')
    ap.add_argument('--preset', choices=sorted(PRESETS))
    ap.add_argument('--angle', type=float, help='region growth: max angle (deg) to the region mean normal [10]')
    ap.add_argument('--tol', type=float, help='region growth: max distance to the region plane, fraction of bbox diagonal [0.0012]')
    ap.add_argument('--clamp', type=float, help='max vertex move, fraction of bbox diagonal [0.002]')
    ap.add_argument('--min-area', type=float, help='min planar region area, fraction of total area [0.0004]')
    ap.add_argument('--min-faces', type=int, help='min faces per planar region [6]')
    ap.add_argument('--merge-angle', type=float, help='small regions merge into a neighbour plane within this angle (deg) [14]')
    ap.add_argument('--curv-sag', type=float, help='curved if the quadratic sagitta exceeds this x tol ... [0.6]')
    ap.add_argument('--curv-expl', type=float, help='... and the quadratic explains this fraction of the variance [0.7]')
    ap.add_argument('--chain-deg', type=float, help='creases shallower than this (deg) with parallel axes chain into a curved surface [16]; 0 = off')
    ap.add_argument('--crease', type=float, help='sharp edges between non-planar faces above this angle (deg) [35]')
    ap.add_argument('--parallel', type=float, help='planes closer than this (deg) are averaged at shared vertices [4]')
    ap.add_argument('--soft', type=float, help='planar regions meeting under this angle (deg) get a blended (soft) crease [8; 0 = all sharp]')
    ap.add_argument('--free-normals', choices=['crease', 'original'], help='normals of faces outside planar regions: recomputed with --crease, or the generated ones [crease]')
    ap.add_argument('--smooth-curved', type=int, help='Taubin smoothing iterations on curved regions [0]')
    ap.add_argument('--weld', type=float, help='weld distance, fraction of bbox diagonal [1e-6]')
    ap.add_argument('--normal', choices=['highpass', 'keep', 'drop'], help='normal map treatment [highpass]')
    ap.add_argument('--variants', help='extra normal-map variants to write as out-<v>.glb, comma list')
    ap.add_argument('--nrm-sigma', type=float, help='high-pass gaussian sigma, fraction of texture width [0.006]')
    ap.add_argument('--tex', type=int, help='texture size for optimize-glb [input size]')
    ap.add_argument('--tris', type=int, help='triangle budget for optimize-glb [no simplification]')
    ap.add_argument('--rotate', help='ship frame rotation x,y,z deg (as in src/ships/*.js)')
    ap.add_argument('--length', type=float, help='ship length (m) for metric reports and keep boxes')
    ap.add_argument('--keep-box', action='append', help='x0,y0,z0,x1,y1,z1 in the ship frame (metres): vertices inside never move')
    ap.add_argument('--debug', action='store_true', help='also write out-regions.glb')
    ap.add_argument('--uvmaps', type=int, help='also write out-uvmaps.npz: texture-aligned region / class / ship-frame position and normal maps at this size (for tools/blender/hulltex.py)')
    ap.add_argument('--no-optimize', dest='optimize', action='store_false', default=None)
    ap.add_argument('--work', help='work folder [out.work]')
    a = ap.parse_args()
    o = dict(DEFAULTS)
    if a.preset:
        o.update(PRESETS[a.preset])
    for k, v in vars(a).items():
        if v is not None and k in o:
            o[k] = v
    if isinstance(o['rotate'], str):
        o['rotate'] = tuple(float(x) for x in o['rotate'].split(','))
    o['input'], o['output'], o['preset'] = a.input, a.output, a.preset
    return o


def log(*a):
    print('[straighten]', *a, flush=True)


# --------------------------------------------------------------------------------------------
# Blender
# --------------------------------------------------------------------------------------------
def load_mesh(path, weld_frac):
    import bpy
    import bmesh
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path, import_shading='NORMALS')
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in objs:
        o.data.transform(o.matrix_world)
        o.matrix_world.identity()
        # keep the generated normals as a corner attribute (bmesh carries it through the weld)
        cn = np.zeros(len(o.data.loops) * 3)
        o.data.corner_normals.foreach_get('vector', cn)
        a = o.data.attributes.new('orig_nrm', 'FLOAT_VECTOR', 'CORNER')
        a.data.foreach_set('vector', cn)
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs):
            bpy.ops.object.join()
    ob = objs[0]
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    co = np.array([v.co[:] for v in bm.verts])
    diag = float(np.linalg.norm(co.max(0) - co.min(0)))
    stats = dict(verts_in=len(bm.verts), faces_in=len(bm.faces))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld_frac * diag)
    # duplicate faces (same vertex set)
    seen, dup = set(), []
    bm.verts.index_update()
    for f in bm.faces:
        k = tuple(sorted(v.index for v in f.verts))
        if k in seen:
            dup.append(f)
        else:
            seen.add(k)
    if dup:
        bmesh.ops.delete(bm, geom=dup, context='FACES_ONLY')
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=weld_frac * diag)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    ngons = [f for f in bm.faces if len(f.verts) > 3]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    stats.update(dup_faces=len(dup), loose=len(loose), verts=len(bm.verts), faces=len(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob, diag, stats


def mesh_arrays(me):
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get('co', V)
    T = np.zeros(len(me.loops), dtype=np.int64)
    me.loops.foreach_get('vertex_index', T)
    return V.reshape(-1, 3), T.reshape(-1, 3)


def set_positions(me, V):
    me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.update()


def set_normals(me, T, label, planar, plane_n, E, ptr, ef_face, crease_deg, parallel_deg, crease_free_deg, soft_deg=0.0, free_mode='crease'):
    """Sharp edges + custom split normals: planar faces carry their plane normal exactly."""
    V, _ = mesh_arrays(me)
    N, _, _ = core.face_geometry(V, T)
    m = len(T)
    fp = (label >= 0) & planar[np.maximum(label, 0)]
    counts = np.diff(ptr)
    sharp = np.zeros(len(E), dtype=bool)
    sharp[counts != 2] = True
    two = np.where(counts == 2)[0]
    fa, fb = ef_face[ptr[two]], ef_face[ptr[two] + 1]
    ang = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', N[fa], N[fb]), -1, 1)))
    la, lb = label[fa], label[fb]
    both = fp[fa] & fp[fb]
    diff_region = both & (la != lb)
    rn = np.degrees(np.arccos(np.clip(np.abs(np.einsum('ij,ij->i', plane_n[np.maximum(la, 0)], plane_n[np.maximum(lb, 0)])), -1, 1)))
    s = np.where(diff_region, rn > max(parallel_deg * 0.5, soft_deg),
                 np.where(fp[fa] ^ fp[fb], ang > crease_free_deg, np.where(both, False, ang > crease_deg)))
    sharp[two] = s
    # map to Blender's edges
    nvert = len(me.vertices)
    ek = E[:, 0].astype(np.int64) * nvert + E[:, 1]
    be = np.zeros(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get('vertices', be)
    be = be.reshape(-1, 2)
    be.sort(1)
    bk = be[:, 0] * nvert + be[:, 1]
    o = np.argsort(ek)
    pos = np.searchsorted(ek[o], bk)
    bsharp = sharp[o][np.clip(pos, 0, len(o) - 1)]
    attr = me.attributes.get('sharp_edge') or me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    attr.data.foreach_set('value', bsharp.tolist())
    sf = me.attributes.get('sharp_face')
    if sf:
        me.attributes.remove(sf)
    me.update()
    ln = np.zeros(len(me.loops) * 3)
    me.corner_normals.foreach_get('vector', ln)
    ln = ln.reshape(m, 3, 3)
    if free_mode == 'original' and me.attributes.get('orig_nrm'):
        on = np.zeros(len(me.loops) * 3)
        me.attributes['orig_nrm'].data.foreach_get('vector', on)
        on = on.reshape(m, 3, 3)
        ok = np.linalg.norm(on, axis=2) > 0.5
        ln = np.where(ok[:, :, None], on, ln)
    pn = plane_n[np.maximum(label, 0)]
    pn = np.where((np.einsum('ij,ij->i', pn, N) < 0)[:, None], -pn, pn)
    ln[fp] = pn[fp][:, None, :]
    if soft_deg > 0:
        # soft creases: where planar regions meet at less than soft_deg, their shared vertices
        # carry the average of those planes' normals (a one-triangle blend instead of a step)
        cos_s = math.cos(math.radians(soft_deg))
        fl = np.where(fp, label, -1)
        vf = np.unique(np.stack([T.ravel(), np.repeat(fl, 3)], 1), axis=0)
        vf = vf[vf[:, 1] >= 0]
        cnt = np.bincount(vf[:, 0], minlength=len(V))
        vptr = np.concatenate([[0], np.cumsum(cnt)])
        multi = np.where(cnt >= 2)[0]
        soft = {}
        for v in multi.tolist():
            rs = vf[vptr[v]:vptr[v + 1], 1]
            ns = plane_n[rs]
            for i, r in enumerate(rs.tolist()):
                c = ns @ ns[i]
                sel = c > cos_s
                if sel.sum() > 1:
                    a = ns[sel].sum(0)
                    soft[(v, r)] = a / np.linalg.norm(a)
        if soft:
            fidx = np.where(fp)[0]
            for f in fidx.tolist():
                r = int(label[f])
                for k in range(3):
                    q = soft.get((int(T[f, k]), r))
                    if q is not None:
                        ln[f, k] = q if q @ N[f] > 0 else -q
    me.normals_split_custom_set(ln.reshape(-1, 3).tolist())
    me.update()
    return int(sharp.sum())


def export_glb(ob, path, colors=False):
    import bpy
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_normals=True, export_texcoords=True, export_tangents=False,
                              export_materials='PLACEHOLDER' if not colors else 'EXPORT',
                              export_vertex_color='ACTIVE' if colors else 'NONE', export_apply=False)


def debug_colors(me, label, klass):
    rng = np.random.default_rng(7)
    R = int(label.max()) + 1 if len(label) else 0
    pal = 0.35 + 0.6 * rng.random((max(R, 1), 3))
    col = np.full((len(label), 4), 1.0)
    col[:, :3] = 0.5
    ok = label >= 0
    col[ok, :3] = pal[label[ok]]
    cur = ok & (klass[np.maximum(label, 0)] == 2)
    col[cur, :3] = (0.9, 0.15, 0.1)
    free = (~ok) | (klass[np.maximum(label, 0)] == 0)
    col[free, :3] = 0.45
    attr = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    attr.data.foreach_set('color', np.repeat(col, 3, axis=0).ravel().tolist())
    me.color_attributes.active_color = attr


def write_uvmaps(me, T, S, label, klass, size, path):
    """Texture-aligned maps of the straightened mesh (glTF UV convention, row 0 = v 0):
    face class (-1 no face, 0 free, 1 planar, 2 curved), region id (-1 = free / none), ship-frame
    position (m) and face normal (planar faces: their region's fitted plane is where they now lie)."""
    import uvraster
    uv = np.zeros(len(me.loops) * 2)
    me.uv_layers.active.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 3, 2)
    uv[:, :, 1] = 1 - uv[:, :, 1]  # Blender -> glTF v
    t0 = time.time()
    cov = uvraster.raster(uv, size, size, dilate=0.75)
    tri = S[T]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-12)[:, None]
    cls = np.where(label >= 0, klass[np.maximum(label, 0)], 0).astype(np.int8)
    np.savez_compressed(path, face=cov.face, cls=cov.per_face(cls, -1).astype(np.int8),
                        region=cov.per_face(np.where(cls == 1, label, -1).astype(np.int32), -1),
                        pos=cov.interp(tri.astype(np.float32)).astype(np.float16),
                        nrm=cov.interp(np.repeat(fn[:, None, :], 3, 1).astype(np.float32)).astype(np.float16))
    log(f'uvmaps {size}px {time.time() - t0:.1f}s -> {path}')


# --------------------------------------------------------------------------------------------
# ship frame (src/lib/glbship.js: rotate (Euler XYZ), scale to length on z, centre)
# --------------------------------------------------------------------------------------------
def ship_frame(V_bl, rotate, length):
    G = np.stack([V_bl[:, 0], V_bl[:, 2], -V_bl[:, 1]], 1)  # Blender Z-up -> glTF Y-up
    ax, ay, az = [math.radians(a) for a in (rotate or (0, 0, 0))]
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    R = Rx @ Ry @ Rz
    P = G @ R.T
    lo, hi = P.min(0), P.max(0)
    s = (length / (hi[2] - lo[2])) if length else 1.0
    c = (lo + hi) / 2
    return lambda X: (np.stack([X[:, 0], X[:, 2], -X[:, 1]], 1) @ R.T - c) * s, s


# --------------------------------------------------------------------------------------------
def straighten(o):
    t0 = time.time()
    out = os.path.abspath(o['output'])
    work = os.path.abspath(o['work'] or os.path.splitext(out)[0] + '.work')
    os.makedirs(work, exist_ok=True)
    src = os.path.abspath(o['input'])
    geom, info_p = os.path.join(work, 'geom.glb'), os.path.join(work, 'info.json')
    js.run('prep', SCENE, input=src, geom=geom, info=info_p)
    info = json.load(open(info_p))
    tex = o['tex'] or max([t['size'][0] for t in info['textures'] if t.get('size')] or [2048])
    log(f'prep {time.time() - t0:.1f}s  textures {[t["size"] for t in info["textures"]]}')

    ob, diag, stats = load_mesh(geom, o['weld'])
    me = ob.data
    V0, T = mesh_arrays(me)
    to_ship, s_m = ship_frame(V0, o['rotate'], o['length'])
    unit = s_m  # metres per world unit (1 if no length)
    tol, clamp = o['tol'] * diag, o['clamp'] * diag
    log(f'mesh {stats}  diag {diag:.4g} ({diag * unit:.2f} m)  tol {tol * unit:.3f} m  clamp {clamp * unit:.3f} m')

    t1 = time.time()
    N, area, cent = core.face_geometry(V0, T)
    E, ptr, ef_face, face_edges = core.edge_table(T)
    fptr, fnbr = core.face_adjacency(T, ptr, ef_face)
    frozen_v = np.zeros(len(V0), dtype=bool)
    for kb in o['keep_box'] or []:
        b = np.array([float(x) for x in kb.split(',')]).reshape(2, 3)
        S = to_ship(V0)
        frozen_v |= np.all((S >= b[0]) & (S <= b[1]), axis=1)
    locked = frozen_v[T].all(1) if frozen_v.any() else None
    cos_t = math.cos(math.radians(o['angle']))
    label = core.grow_regions(V0, T, N, area, fptr, fnbr, cos_t, tol, locked)
    R = int(label.max()) + 1
    log(f'grow {time.time() - t1:.1f}s  {R} regions')

    # small regions: merge into the best-fitting big neighbour, else free
    total = area.sum()
    rarea = np.bincount(label[label >= 0], weights=area[label >= 0], minlength=R)
    rfaces = np.bincount(label[label >= 0], minlength=R)
    big = (rarea >= o['min_area'] * total) & (rfaces >= o['min_faces'])
    n, C, ev, W = core.fit_planes(V0, T, area, label, R)
    n = core.orient_planes(n, N, area, label, R)
    d = np.einsum('ij,ij->i', n, C)
    cos_m = math.cos(math.radians(o['merge_angle']))
    fsrc = np.repeat(np.arange(len(T)), np.diff(fptr))
    for _ in range(3):
        lab_s, lab_n = label[fsrc], label[fnbr]
        cand = (lab_s >= 0) & (lab_n >= 0) & (lab_s != lab_n)
        cand &= ~big[np.maximum(lab_s, 0)] & big[np.maximum(lab_n, 0)]
        fs, rn_ = fsrc[cand], lab_n[cand]
        ok = np.einsum('ij,ij->i', N[fs], n[rn_]) > cos_m
        dist = np.abs(np.einsum('kcj,kj->kc', V0[T[fs]], n[rn_]) - d[rn_][:, None]).max(1)
        ok &= dist < 1.5 * tol
        fs, rn_ = fs[ok], rn_[ok]
        # a small region moves as a whole only if all its faces that border big regions agree
        small_r = label[fs]
        changed = 0
        for r_small in np.unique(small_r):
            sel = small_r == r_small
            targets, cnts = np.unique(rn_[sel], return_counts=True)
            tgt = targets[np.argmax(cnts)]
            faces = np.where(label == r_small)[0]
            dd = np.abs(V0[T[faces]] @ n[tgt] - d[tgt]).max()
            nn = N[faces] @ n[tgt]
            if dd < 1.5 * tol and np.average(nn, weights=area[faces]) > cos_m:
                label[faces] = tgt
                changed += 1
        if not changed:
            break
    small = ~big
    label[(label >= 0) & small[np.maximum(label, 0)]] = -1
    # compact labels
    used = np.unique(label[label >= 0])
    remap = np.full(R, -1)
    remap[used] = np.arange(len(used))
    label = np.where(label >= 0, remap[np.maximum(label, 0)], -1)
    R = len(used)
    n, C, ev, W = core.fit_planes(V0, T, area, label, R)
    n = core.orient_planes(n, N, area, label, R)
    d = np.einsum('ij,ij->i', n, C)

    # curved-region detection: 1 = planar, 2 = curved
    klass = np.ones(R, dtype=np.int64)
    faces_of = np.split(np.argsort(label, kind='stable')[np.sum(label < 0):], np.cumsum(np.bincount(label[label >= 0], minlength=R))[:-1])
    sag = np.zeros(R); expl = np.zeros(R)
    for r in range(R):
        sg, ex, k, L = core.quadratic_curvature(V0, T, label, faces_of[r], n[r], C[r])
        sag[r], expl[r] = sg, ex
        if ex > o['curv_expl'] and sg > o['curv_sag'] * tol:
            klass[r] = 2
    n_quad = int((klass == 2).sum())
    quad_curved = klass == 2
    # chains of shallow creases with parallel axes (faceted cylinders / cones)
    n_chain = 0
    if o['chain_deg'] > 0:
        counts = np.diff(ptr)
        two = np.where(counts == 2)[0]
        fa, fb = ef_face[ptr[two]], ef_face[ptr[two] + 1]
        la, lb = label[fa], label[fb]
        m_ = (la >= 0) & (lb >= 0) & (la != lb)
        ea = E[two[m_]]
        elen = np.linalg.norm(V0[ea[:, 0]] - V0[ea[:, 1]], axis=1)
        pa, pb = np.minimum(la[m_], lb[m_]), np.maximum(la[m_], lb[m_])
        key = pa * R + pb
        uk, inv = np.unique(key, return_inverse=True)
        blen = np.bincount(inv, weights=elen)
        A_, B_ = uk // R, uk % R
        dih = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', n[A_], n[B_]), -1, 1)))
        # region "size": sqrt of area; a join counts when its shared boundary is long
        rsz = np.sqrt(np.bincount(label[label >= 0], weights=area[label >= 0], minlength=R))
        shallow = (dih > o['parallel']) & (dih < o['chain_deg']) & (blen > 0.5 * np.minimum(rsz[A_], rsz[B_]))
        axis = np.cross(n[A_], n[B_])
        axis /= np.maximum(np.linalg.norm(axis, axis=1), 1e-12)[:, None]
        joins = {}
        for i in np.where(shallow)[0]:
            joins.setdefault(A_[i], []).append(i)
            joins.setdefault(B_[i], []).append(i)
        for r, js_ in joins.items():
            if len(js_) < 2 or klass[r] == 2:
                continue
            ax_ = axis[js_]
            # two joins with parallel axes (|cos| > 0.97) on the same region = a strip of a cylinder
            cc = np.abs(ax_ @ ax_.T)
            np.fill_diagonal(cc, 0)
            if cc.max() > 0.97:
                klass[r] = 2
                n_chain += 1
        # a region that only the quadratic test calls curved but that meets no neighbour at a
        # shallow crease is a soft chamfer / fillet between steeper panels: flatten it
        has_shallow = np.zeros(R, dtype=bool)
        has_shallow[A_[shallow]] = True
        has_shallow[B_[shallow]] = True
        demote = (klass == 2) & quad_curved & ~has_shallow
        klass[demote] = 1
        n_quad -= int(demote.sum())
        # propagate along shallow parallel joins from curved strips (end strips of a cylinder)
        for _ in range(2):
            for i in np.where(shallow)[0]:
                a_, b_ = A_[i], B_[i]
                if klass[a_] == 2 and klass[b_] == 1:
                    klass[b_] = 2
                elif klass[b_] == 2 and klass[a_] == 1:
                    klass[a_] = 2
    planar = klass == 1
    log(f'classes: planar {int(planar.sum())}  curved {int((klass == 2).sum())} (quadratic {n_quad}, chain {n_chain})')

    V1, cnt, disp_raw, over = core.solve_vertices(V0, T, label, planar, n, d, clamp,
                                                  parallel_deg=o['parallel'], frozen=frozen_v)
    if o['smooth_curved']:
        fl = (label >= 0) & (klass[np.maximum(label, 0)] == 2)
        cm = np.zeros(len(V0), dtype=bool)
        cm[T[fl].ravel()] = True
        cm[T[~fl].ravel()] = False  # only vertices fully inside curved regions
        cm &= ~frozen_v
        V1 = core.taubin(V1, T, cm, iters=o['smooth_curved'])
    set_positions(me, V1)
    log(f'solve {time.time() - t1:.1f}s')

    nsharp = set_normals(me, T, label, planar, n, E, ptr, ef_face, o['crease'], o['parallel'], 30.0, o['soft'], o['free_normals'])

    # metrics
    D = np.linalg.norm(V1 - V0, axis=1) * unit
    S0, S1 = to_ship(V0), to_ship(V1)
    fplanar = (label >= 0) & planar[np.maximum(label, 0)]
    fcurved = (label >= 0) & (klass[np.maximum(label, 0)] == 2)
    # flatness before/after: area-weighted RMS distance of planar-region corners to their plane (mm)
    def rms_plane(X):
        f = np.where(fplanar)[0]
        dd = np.einsum('kcj,kj->kc', X[T[f]], n[label[f]]) - d[label[f]][:, None]
        return float(np.sqrt(np.average((dd ** 2).mean(1), weights=area[f]))) * unit
    # normal noise: area-weighted mean angle between a face and its plane
    N1, _, _ = core.face_geometry(V1, T)
    def ang(Nx):
        f = np.where(fplanar)[0]
        c = np.clip(np.einsum('ij,ij->i', Nx[f], n[label[f]]), -1, 1)
        return float(np.degrees(np.average(np.arccos(c), weights=area[f])))
    metrics = dict(
        input=src, output=out, preset=o['preset'], metres_per_unit=unit, diag_m=diag * unit,
        tol_m=tol * unit, clamp_m=clamp * unit, mesh=stats,
        tris_in=stats['faces_in'], tris_out=int(len(T)),
        regions_planar=int(planar.sum()), regions_curved=int((klass == 2).sum()),
        planar_area_frac=float(area[fplanar].sum() / total),
        curved_area_frac=float(area[fcurved].sum() / total),
        free_area_frac=float(1 - (area[fplanar].sum() + area[fcurved].sum()) / total),
        disp_max_m=float(D.max()), disp_mean_m=float(D.mean()),
        disp_mean_moved_m=float(D[D > 0].mean()) if (D > 0).any() else 0.0,
        disp_p99_m=float(np.percentile(D, 99)), disp_p999_m=float(np.percentile(D, 99.9)),
        verts_over_half_clamp=int((D > 0.5 * clamp * unit).sum()),
        verts_moved_frac=float((D > 1e-9).mean()), verts_clamped=int(over.sum()),
        bbox_before=[S0.min(0).tolist(), S0.max(0).tolist()], bbox_after=[S1.min(0).tolist(), S1.max(0).tolist()],
        bbox_change_m=float(np.abs(np.concatenate([S1.min(0) - S0.min(0), S1.max(0) - S0.max(0)])).max()),
        planar_rms_before_mm=rms_plane(V0) * 1000, planar_rms_after_mm=rms_plane(V1) * 1000,
        planar_normal_dev_before_deg=ang(N), planar_normal_dev_after_deg=ang(N1),
        sharp_edges=nsharp, frozen_verts=int(frozen_v.sum()),
        options={k: v for k, v in o.items() if k not in ('input', 'output')},
    )
    log(f'disp max {metrics["disp_max_m"]:.3f} m mean {metrics["disp_mean_m"] * 1000:.1f} mm  planar {metrics["planar_area_frac"]:.1%}  '
        f'curved {metrics["curved_area_frac"]:.1%}  rms {metrics["planar_rms_before_mm"]:.0f}->{metrics["planar_rms_after_mm"]:.0f} mm  '
        f'normal dev {metrics["planar_normal_dev_before_deg"]:.1f}->{metrics["planar_normal_dev_after_deg"]:.2f} deg')

    if o['uvmaps']:
        write_uvmaps(me, T, S1, label, klass, o['uvmaps'], os.path.splitext(out)[0] + '-uvmaps.npz')
        metrics['uvmaps'] = os.path.splitext(out)[0] + '-uvmaps.npz'

    bl = os.path.join(work, 'blender.glb')
    export_glb(ob, bl)
    if o['debug']:
        debug_colors(me, label, klass)
        dbg = os.path.splitext(out)[0] + '-regions.glb'
        mat = __import__('bpy').data.materials.new('regions')
        me.materials.clear(); me.materials.append(mat)
        export_glb(ob, os.path.join(work, 'regions-raw.glb'), colors=True)
        subprocess.run(['node', 'tools/optimize-glb.mjs', os.path.join(work, 'regions-raw.glb'), dbg, '--tris', str(o['tris']), '--tex', '256'], cwd=SCENE, check=True, capture_output=True)

    variants = [o['normal']] + [v for v in (o['variants'] or '').split(',') if v and v != o['normal']]
    metrics['outputs'] = {}
    for i, var in enumerate(variants):
        dst = out if i == 0 else os.path.splitext(out)[0] + f'-{var}.glb'
        merged = os.path.join(work, f'merged-{var}.glb')
        rep = os.path.join(work, f'normal-{var}.json')
        js.run('merge', SCENE, input=src, blender=bl, output=merged, normal=var, sigma=o['nrm_sigma'],
               report=rep, normalPng=os.path.join(work, f'normal-{var}.png') if var == 'highpass' else None)
        nrep = json.load(open(rep))
        if o['optimize']:
            r = subprocess.run(['node', 'tools/optimize-glb.mjs', merged, dst, '--tris', str(o['tris']), '--tex', str(tex)],
                               cwd=SCENE, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stderr)
            log(r.stdout.strip())
        else:
            import shutil
            shutil.copy(merged, dst)
        metrics['outputs'][var] = dict(path=dst, bytes=os.path.getsize(dst), normal=nrep)
    metrics['runtime_s'] = time.time() - t0
    with open(os.path.splitext(out)[0] + '.json', 'w') as f:
        json.dump(metrics, f, indent=1)
    log(f'done {metrics["runtime_s"]:.1f}s -> {out}')
    return metrics


if __name__ == '__main__':
    straighten(parse())
