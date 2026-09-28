"""Shared helpers for the parametric hard-surface hulls (tools/blender/hulls/<ship>.py).

Everything is authored in the SHIP FRAME of the scene (metres, bow +Z, dorsal +Y, port +X; the
frame src/lib/glbship.js produces and assemble.py places parts in) with bmesh, one bmesh per
VOLUME (hull body, deckhouse, tower tier, pod, ...). A volume is a closed solid, so volumes can
simply interpenetrate (the seam where two meet is a real edge that catches the bake's AO) and
booleans stay robust. The pipeline (Hull.build):

  volumes (bmesh, ship frame, material index = paint zone)
    -> booleans (EXACT solver) for true recesses: glazing bands, door and airlock bays, vent
       bays, intakes; cutters are closed solids too
    -> cull: faces buried inside another volume are deleted (no texels wasted on them)
    -> bevel (ANGLE limit, per-volume width, 1 segment = an exact chamfer) + weighted normals
       (face area, keep sharp): flat panels shade flat, every edge catches a thin highlight
    -> join into one object 'hull'
    -> UVs: smart projection per face group (angle limit), islands at one texel density, packed
    -> maps baked with Cycles EMIT into the UV atlas: ship-frame position, true normal, zone id,
       ambient occlusion, curvature (bevel-node difference)
    -> paint (numpy, texture space; see paint.py): zone base colours, PATINA plate tone at the
       runtime tile, panel seams and per-panel tone, AO grime, edge wear, decals (hull number,
       bands, hazard stripes) -> base colour + ORM
    -> one glTF material, GLB with a single mesh node 'hull' (ship frame, not re-centred)

Conventions: every builder takes ship-frame coordinates (tuples or Vectors); ship -> Blender is
the rotation C (x, y, z) -> (x, -z, y) applied once when a volume becomes an object, so glTF
export (+Y up) writes the ship frame back exactly.
"""
import math
import os
import time

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

DEG = math.pi / 180
V = Vector
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # ship -> Blender
CI = C.inverted()

# paint zones = material slots, in this order on every volume (so joins keep the indices)
ZONES = ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'foil']
Z = {n: i for i, n in enumerate(ZONES)}


def log(*a):
    print('[hull]', *a, flush=True)


# --------------------------------------------------------------------------------------------
# 2D / 3D outline helpers
# --------------------------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def interp_table(table, z, cols):
    """Piecewise-linear lookup in a station table [(z, {col: value}), ...] sorted by z."""
    zs = [r[0] for r in table]
    if z <= zs[0]:
        return {c: table[0][1][c] for c in cols}
    if z >= zs[-1]:
        return {c: table[-1][1][c] for c in cols}
    for (z0, a), (z1, b) in zip(table[:-1], table[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0
            return {c: lerp(a[c], b[c], t) for c in cols}


def mirror_half(half):
    """Closed ring from a half outline in the (x, y) plane: points from the top centre (x = 0)
    down the +X (port) side to the bottom centre (x = 0). The -X side is mirrored."""
    pts = [tuple(p) for p in half]
    back = [(-x, y) for x, y in reversed(pts[1:-1])]
    return pts + back


def poly_area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def offset_poly(pts, d):
    """Offset a closed simple polygon (2D) by d (positive = outward). Mitred corners (fine for
    the convex / mildly concave outlines used here)."""
    n = len(pts)
    ccw = poly_area2(pts) > 0
    out = []
    for i in range(n):
        p0, p1, p2 = V(pts[i - 1]), V(pts[i]), V(pts[(i + 1) % n])
        e0 = (p1 - p0).normalized(); e1 = (p2 - p1).normalized()
        # outward normals
        n0 = V((e0.y, -e0.x)) if ccw else V((-e0.y, e0.x))
        n1 = V((e1.y, -e1.x)) if ccw else V((-e1.y, e1.x))
        bis = (n0 + n1)
        if bis.length < 1e-6:
            out.append(tuple(p1 + n0 * d)); continue
        bis.normalize()
        k = d / max(bis.dot(n0), 0.25)
        out.append(tuple(p1 + bis * k))
    return out


def offset_open(pts, d, left=True):
    """Offset an open 2D polyline sideways by d (left of the walking direction if left)."""
    P = [V(p) for p in pts]
    out = []
    for i, p in enumerate(P):
        ts = []
        if i > 0:
            ts.append((P[i] - P[i - 1]).normalized())
        if i < len(P) - 1:
            ts.append((P[i + 1] - P[i]).normalized())
        nrm = [V((-t.y, t.x)) if left else V((t.y, -t.x)) for t in ts]
        if len(nrm) == 2:
            b = (nrm[0] + nrm[1]).normalized()
            k = d / max(b.dot(nrm[0]), 0.25)
            out.append(tuple(p + b * k))
        else:
            out.append(tuple(p + nrm[0] * d))
    return out


def chamfer_rect(cx, cy, w, h, c):
    """Axis-aligned rectangle with 45-degree corner chamfers, CCW, 8 points (2D)."""
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    c = min(c, w / 2 - 1e-3, h / 2 - 1e-3)
    return [(x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c), (x0 + c, y0), (x1 - c, y0)]


def circle2(cx, cy, r, n=24, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def basis(n, up=(0, 1, 0)):
    """Right-handed frame (right, up, n) with n the outward normal (right = up x n)."""
    n = V(n).normalized()
    u = V(up) - n * V(up).dot(n)
    if u.length < 1e-6:
        u = V((0, 0, 1)) - n * n.z
    u.normalize()
    r = u.cross(n)
    return r, u, n


# --------------------------------------------------------------------------------------------
# bmesh builders (ship frame). Each adds to bm and returns the new faces.
# --------------------------------------------------------------------------------------------
def loft(bm, rings, cap0=True, cap1=True, closed=True, zone=0):
    """Loft through rings of 3D points (same count). closed: each ring is a closed loop.
    Returns (side faces grid [k][j], cap faces)."""
    R = [[bm.verts.new(V(p)) for p in ring] for ring in rings]
    m = len(R[0])
    grid = []
    for k in range(len(R) - 1):
        row = []
        for j in range(m if closed else m - 1):
            j2 = (j + 1) % m
            vs = [R[k][j], R[k][j2], R[k + 1][j2], R[k + 1][j]]
            try:
                f = bm.faces.new(vs)
                f.material_index = zone
            except ValueError:
                f = None
            row.append(f)
        grid.append(row)
    caps = []
    if closed:
        for want, ring in ((cap0, R[0]), (cap1, R[-1])):
            if want:
                f = bm.faces.new(ring)
                f.material_index = zone
                caps.append(f)
    return grid, caps


def solid(bm, zone=0):
    """Recalculate outward normals of the whole bmesh (closed solids)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def ring3(pts2, plane, value):
    """2D outline -> 3D ring on a coordinate plane. plane 'xy' (value = z), 'xz' (value = y),
    'zy' (value = x; 2D = (z, y))."""
    if plane == 'xy':
        return [V((a, b, value)) for a, b in pts2]
    if plane == 'xz':
        return [V((a, value, b)) for a, b in pts2]
    if plane == 'zy':
        return [V((value, b, a)) for a, b in pts2]
    raise ValueError(plane)


def prism(bm, pts2, plane, v0, v1, zone=0):
    return loft(bm, [ring3(pts2, plane, v0), ring3(pts2, plane, v1)], zone=zone)


def stack(bm, levels, plane='xz', zone=0, cap0=True, cap1=True):
    """Loft of outlines [(pts2, value), ...] along the plane's axis (e.g. plan outlines at
    heights y for a deckhouse or tower tier)."""
    return loft(bm, [ring3(p, plane, v) for p, v in levels], cap0=cap0, cap1=cap1, zone=zone)


def box(bm, c, size, R=None, zone=0):
    sx, sy, sz = (s / 2 for s in size)
    R = R or Matrix.Identity(3)
    c = V(c)
    P = lambda x, y, z: c + R @ V((x, y, z))
    a = [P(-sx, -sy, -sz), P(sx, -sy, -sz), P(sx, sy, -sz), P(-sx, sy, -sz)]
    b = [P(-sx, -sy, sz), P(sx, -sy, sz), P(sx, sy, sz), P(-sx, sy, sz)]
    return loft(bm, [a, b], zone=zone)


def plate(bm, c, n, up, w, h, t, ch=0.0, zone=0, back=0.0):
    """Chamfered plate on a surface: back face `back` metres behind c (into the surface), front
    face t in front of c, chamfer ch on the front edges. Frame: right = up x n."""
    r, u, nn = basis(n, up)
    c = V(c)
    ring = lambda hw, hh, d: [c + r * sx * hw + u * sy * hh + nn * d for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    rings = [ring(w / 2, h / 2, -back)]
    if ch > 0:
        rings += [ring(w / 2, h / 2, t - ch), ring(w / 2 - ch, h / 2 - ch, t)]
    else:
        rings += [ring(w / 2, h / 2, t)]
    return loft(bm, rings, zone=zone)


def oriented_prism(bm, pts2, c, n, up, d0, d1, zone=0):
    """2D outline (right, up) extruded along n from d0 to d1 (metres) about point c."""
    r, u, nn = basis(n, up)
    c = V(c)
    rings = [[c + r * a + u * b + nn * d for a, b in pts2] for d in (d0, d1)]
    return loft(bm, rings, zone=zone)


def cyl(bm, p0, p1, r0, r1=None, n=24, zone=0, a0=None):
    """Cylinder / cone frustum from p0 to p1."""
    p0, p1 = V(p0), V(p1)
    ax = (p1 - p0).normalized()
    ref = V((0, 1, 0)) if abs(ax.y) < 0.9 else V((1, 0, 0))
    e1 = ax.cross(ref).normalized(); e2 = ax.cross(e1)
    r1 = r0 if r1 is None else r1
    a0 = (math.pi / n) if a0 is None else a0
    ringp = lambda p, r: [p + (e1 * math.cos(a0 + 2 * math.pi * i / n) + e2 * math.sin(a0 + 2 * math.pi * i / n)) * r for i in range(n)]
    return loft(bm, [ringp(p0, r0), ringp(p1, r1)], zone=zone)


def lathe(bm, p0, axis, prof, n=24, zone=0, cap0=True, cap1=True):
    """Surface of revolution: prof = [(r, t), ...] with t along axis from p0."""
    p0, ax = V(p0), V(axis).normalized()
    ref = V((0, 1, 0)) if abs(ax.y) < 0.9 else V((1, 0, 0))
    e1 = ax.cross(ref).normalized(); e2 = ax.cross(e1)
    a0 = math.pi / n
    rings = [[p0 + ax * t + (e1 * math.cos(a0 + 2 * math.pi * i / n) + e2 * math.sin(a0 + 2 * math.pi * i / n)) * max(r, 1e-3) for i in range(n)] for r, t in prof]
    return loft(bm, rings, cap0=cap0, cap1=cap1, zone=zone)


# --------------------------------------------------------------------------------------------
# volumes -> objects
# --------------------------------------------------------------------------------------------
_MATS = {}


def zone_materials():
    if not _MATS:
        for i, n in enumerate(ZONES):
            m = bpy.data.materials.get(f'zone_{n}') or bpy.data.materials.new(f'zone_{n}')
            m['zone'] = i
            _MATS[n] = m
    return [_MATS[n] for n in ZONES]


class Volume:
    """One closed solid: name, bmesh in the ship frame, bevel width, cutters (closed bmeshes
    subtracted with an EXACT boolean), sharp angle for the bevel limit."""

    def __init__(self, name, bevel=0.08, angle=30.0, segments=1, cull=True):
        self.name, self.bevel, self.angle, self.segments, self.cull = name, bevel, angle, segments, cull
        self.bm = bmesh.new()
        self.cutters = bmesh.new()
        self.adds = []   # extra closed solids joined after the booleans (fins inside a bay)

    def to_object(self, bm=None, name=None):
        bm = bm or self.bm
        me = bpy.data.meshes.new(name or self.name)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        me.transform(C)
        for m in zone_materials():
            me.materials.append(m)
        ob = bpy.data.objects.new(name or self.name, me)
        bpy.context.collection.objects.link(ob)
        return ob


def apply_mod(ob, mod):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def boolean(ob, cutter, op='DIFFERENCE'):
    mod = ob.modifiers.new('bool', 'BOOLEAN')
    mod.operation = op
    mod.solver = 'EXACT'
    mod.object = cutter
    mod.material_mode = 'TRANSFER'
    try:
        mod.use_hole_tolerant = True
    except AttributeError:
        pass
    cutter.hide_render = True
    apply_mod(ob, mod)


def count_tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


class Inside:
    """Point-in-solid test for a set of closed objects (ray parity along two skew directions)."""

    def __init__(self, obs):
        self.trees = []
        for ob in obs:
            me = ob.data
            vs = [ob.matrix_world @ v.co for v in me.vertices]
            ps = [tuple(p.vertices) for p in me.polygons]
            self.trees.append((ob.name, BVHTree.FromPolygons(vs, ps, all_triangles=False)))
        self.dirs = [V((0.577, 0.5774, 0.5773)).normalized(), V((-0.61, 0.33, -0.72)).normalized()]

    def inside(self, p, skip=None):
        for name, t in self.trees:
            if name == skip:
                continue
            votes = 0
            for d in self.dirs:
                o = V(p)
                k = 0
                for _ in range(64):
                    hit, _n, _i, dist = t.ray_cast(o, d, 1e4)
                    if hit is None:
                        break
                    k += 1
                    o = hit + d * 1e-4
                votes += k % 2
            if votes == 2:
                return name
        return None


def cull_hidden(obs, eps=0.03):
    """Delete faces lying entirely inside another volume (their centre and all corners, nudged
    `eps` toward the centre, test inside). Keeps everything that shows."""
    solid_obs = [o for o in obs if o.get('closed', True)]
    ins = Inside(solid_obs)
    total = 0
    for ob in obs:
        if not ob.get('cull', True):
            continue
        me = ob.data
        bm = bmesh.new(); bm.from_mesh(me)
        dead = []
        for f in bm.faces:
            c = f.calc_center_median()
            c2 = c - f.normal * eps
            if ins.inside(c2, skip=ob.name) is None:
                continue
            ok = True
            for v in f.verts:
                p = v.co + (c - v.co).normalized() * min(eps * 3, (c - v.co).length * 0.5) - f.normal * eps
                if ins.inside(p, skip=ob.name) is None:
                    ok = False; break
            if ok:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(me); bm.free(); me.update()
        total += len(dead)
    log(f'cull: {total} buried faces removed')
    return total


def finish(ob, width, angle=30.0, segments=1, weight=50):
    """Exact chamfers + crisp shading: bevel (angle-limited, clamped) with harden normals, then
    face-area weighted normals keeping sharp edges."""
    me = ob.data
    if width > 0:
        mod = ob.modifiers.new('bevel', 'BEVEL')
        mod.width = width
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = angle * DEG
        mod.use_clamp_overlap = True
        mod.harden_normals = True
        mod.miter_outer = 'MITER_ARC' if segments > 1 else 'MITER_SHARP'
        apply_mod(ob, mod)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=angle * DEG)
    wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
    wn.mode = 'FACE_AREA'
    wn.weight = weight
    wn.keep_sharp = True
    apply_mod(ob, wn)


def join(obs, name):
    obs = [o for o in obs if o.type == 'MESH' and len(o.data.polygons)]
    with bpy.context.temp_override(active_object=obs[0], selected_editable_objects=obs, selected_objects=obs):
        bpy.ops.object.join()
    o = obs[0]
    o.name = name
    o.data.name = name
    return o


# --------------------------------------------------------------------------------------------
# UVs
# --------------------------------------------------------------------------------------------
def unwrap(ob, angle=50.0, margin=0.0015):
    """Smart projection (islands = face groups within `angle`, each projected flat at true
    scale), then packed at one scale for all islands: a uniform texel density."""
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle * DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    # texel density report: UV area vs surface area
    me = ob.data
    uv = me.uv_layers.active.data
    a3 = 0.0; a2 = 0.0
    for p in me.polygons:
        a3 += p.area
        idx = list(p.loop_indices)
        pts = [uv[i].uv for i in idx]
        a2 += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
    return {'surface_m2': round(a3, 1), 'uv_fill': round(a2, 3), 'px_per_m_at_4096': round(4096 * math.sqrt(a2 / a3), 1)}


# --------------------------------------------------------------------------------------------
# Cycles bakes (EMIT) into float images
# --------------------------------------------------------------------------------------------
def setup_cycles(threads=4, samples=1):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = threads
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.bake.use_clear = True
    sc.render.bake.margin = 8
    sc.render.bake.margin_type = 'EXTEND'
    return sc


def _emit_material(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    build(nt, em)
    return m


def bake_emit(ob, size, build, samples=1, name='bake', per_zone=None):
    """Bake an emission shader into a float image (size^2). build(nt, emission_node) wires the
    colour; per_zone(i) -> build for zone i (one material per slot) instead."""
    sc = bpy.context.scene
    sc.cycles.samples = samples
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=True)
    me = ob.data
    old = [s.material for s in ob.material_slots]
    mats = []
    for i in range(len(old)):
        b = per_zone(i) if per_zone else build
        m = _emit_material(f'{name}_{i}', b)
        tn = m.node_tree.nodes.new('ShaderNodeTexImage')
        tn.image = img
        m.node_tree.nodes.active = tn
        mats.append(m)
        ob.material_slots[i].material = m
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    t0 = time.time()
    bpy.ops.object.bake(type='EMIT')
    for i, m in enumerate(old):
        ob.material_slots[i].material = m
    for m in mats:
        bpy.data.materials.remove(m)
    a = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    log(f'bake {name} {size}px {time.time() - t0:.1f}s')
    return a.reshape(size, size, 4)[::-1, :, :3].copy()  # rows top-down (image convention)


def geo(nt, output):
    return nt.nodes.new('ShaderNodeNewGeometry').outputs[output]


def bake_maps(ob, size=4096, ao_size=2048, ao_samples=24, ao_dist=1.2, curv_r=0.06, threads=4):
    """Returns dict of top-down arrays: pos (ship frame), nrm (ship frame, true normal), zone
    (int, -1 = empty), ao (0..1), curv (0..1 convexity, 0..1 concavity)."""
    setup_cycles(threads)
    cov_col = lambda i: (lambda nt, em: setattr(em.inputs['Color'], 'default_value', ((i + 1) / 64.0, 0, 0, 1)))
    zone = bake_emit(ob, size, None, per_zone=cov_col, name='zone')[..., 0]
    zone = np.round(zone * 64).astype(np.int16) - 1

    def wire(sock):
        def b(nt, em):
            nt.links.new(sock(nt), em.inputs['Color'])
        return b
    pos_b = bake_emit(ob, size, wire(lambda nt: geo(nt, 'Position')), name='pos')
    nrm_b = bake_emit(ob, size, wire(lambda nt: geo(nt, 'True Normal')), name='nrm')
    pos = np.stack([pos_b[..., 0], pos_b[..., 2], -pos_b[..., 1]], -1)
    nrm = np.stack([nrm_b[..., 0], nrm_b[..., 2], -nrm_b[..., 1]], -1)

    def ao_b(nt, em):
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.samples = 16
        ao.inputs['Distance'].default_value = ao_dist
        nt.links.new(ao.outputs['AO'], em.inputs['Color'])
    ao = bake_emit(ob, ao_size, ao_b, samples=ao_samples, name='ao')[..., 0]

    def cv_b(nt, em):
        bv = nt.nodes.new('ShaderNodeBevel')
        bv.samples = 8
        bv.inputs['Radius'].default_value = curv_r
        g = nt.nodes.new('ShaderNodeNewGeometry')
        # convexity: bevel normal bends away from the true normal; sign from the cross term is
        # not available, so bake 1 - dot (edge-ness) and split by AO later
        d = nt.nodes.new('ShaderNodeVectorMath'); d.operation = 'DOT_PRODUCT'
        nt.links.new(bv.outputs['Normal'], d.inputs[0])
        nt.links.new(g.outputs['True Normal'], d.inputs[1])
        s = nt.nodes.new('ShaderNodeMath'); s.operation = 'SUBTRACT'; s.inputs[0].default_value = 1.0
        nt.links.new(d.outputs['Value'], s.inputs[1])
        nt.links.new(s.outputs[0], em.inputs['Color'])
    curv = bake_emit(ob, ao_size, cv_b, samples=8, name='curv')[..., 0]
    return {'pos': pos, 'nrm': nrm, 'zone': zone, 'ao': ao, 'curv': curv}


def set_final_material(ob, base_png, orm_png, name='hull', normal_png=None):
    """One glTF material: base colour (sRGB) + ORM (G roughness, B metal) [+ tangent-space normal]."""
    fm = bpy.data.materials.new(name)
    fm.use_nodes = True
    t = fm.node_tree
    bsdf = t.nodes['Principled BSDF']
    ib = bpy.data.images.load(base_png); ib.colorspace_settings.name = 'sRGB'
    io = bpy.data.images.load(orm_png); io.colorspace_settings.name = 'Non-Color'
    ti = t.nodes.new('ShaderNodeTexImage'); ti.image = ib
    t.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    to = t.nodes.new('ShaderNodeTexImage'); to.image = io
    sep = t.nodes.new('ShaderNodeSeparateColor')
    t.links.new(to.outputs['Color'], sep.inputs['Color'])
    t.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    t.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    if normal_png:
        inn = bpy.data.images.load(normal_png); inn.colorspace_settings.name = 'Non-Color'
        tn = t.nodes.new('ShaderNodeTexImage'); tn.image = inn
        nm = t.nodes.new('ShaderNodeNormalMap')
        t.links.new(tn.outputs['Color'], nm.inputs['Color'])
        t.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    ob.data.materials.clear()
    ob.data.materials.append(fm)


def export_glb(ob, path):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_texcoords=True, export_normals=True,
                              export_tangents=False, export_materials='EXPORT', export_animations=False,
                              export_extras=False, export_image_format='AUTO')
