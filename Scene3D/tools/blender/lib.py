# Shared library for the procedural parts kit (see kit.py).
#
# Part frame (= glTF frame of the exported GLB): metres, X width, Y up, Z out of the hull; the
# origin is the centre of the mounting face. Geometry is authored directly in this frame inside
# Blender (so Blender's +Z is "out of the hull" while modelling); export() rotates the finished
# mesh +90 degrees about X, which the glTF exporter's Z-up -> Y-up conversion turns back into
# exactly the part frame. Drive bells use the same frame with the exit plane at z = 0.
#
# A Part collects primitives (each one bmesh -> one object with a material name, a bevel width
# and a sharp-edge angle). finish() bevels (harden normals) and weights normals per primitive,
# joins, unwraps, bakes a weathered base colour (AO grime, curvature edge wear, panel tone) and a
# roughness/metal map with Cycles into one atlas, then swaps in a single glTF material, so a
# part is one mesh / one material / one draw call per instance batch.
import bpy
import bmesh
import math
import os
import time
from contextlib import contextmanager
from mathutils import Matrix, Vector, Euler

DEG = math.pi / 180


# --------------------------------------------------------------------------------------------
# scene
# --------------------------------------------------------------------------------------------
def reset_scene(threads=2):
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images,
                 bpy.data.curves, bpy.data.node_groups):
        for b in list(coll):
            coll.remove(b)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = threads
    sc.cycles.use_denoising = False
    sc.unit_settings.system = 'METRIC'
    return sc


def mat_xf(at=(0, 0, 0), rot=(0, 0, 0), scale=None):
    M = Matrix.Translation(Vector(at)) @ Euler([r * DEG for r in rot], 'XYZ').to_matrix().to_4x4()
    if scale is not None:
        s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
        M = M @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    return M


# --------------------------------------------------------------------------------------------
# 2D outlines
# --------------------------------------------------------------------------------------------
def rrect(w, h, r=0.0, n=4, cx=0.0, cy=0.0):
    """Rounded rectangle, CCW, 4*(n+1) points (4 when r == 0)."""
    if r <= 1e-6:
        return [(cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2)]
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for (x, y, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = (a0 + 90 * k / n) * DEG
            pts.append((cx + x + r * math.cos(a), cy + y + r * math.sin(a)))
    return pts


def circle(r, n=24, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def chamfer_rect(w, h, c):
    """Rectangle with 45-degree corner chamfers, CCW, 8 points."""
    x, y = w / 2, h / 2
    return [(x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + c), (-x + c, -y), (x - c, -y), (x, -y + c)]


# --------------------------------------------------------------------------------------------
# bmesh builders (all return a new bmesh in local coordinates)
# --------------------------------------------------------------------------------------------
def bm_box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    return bm


def bm_cyl(r, h, n=24, r2=None, caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=h)
    return bm


def bm_prism(pts, z0, z1):
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    m = len(pts)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bm_frame(outer, inner, z0, z1):
    """Solid ring between two closed outlines with the same point count (a window frame)."""
    assert len(outer) == len(inner), (len(outer), len(inner))
    bm = bmesh.new()
    m = len(outer)
    ob = [bm.verts.new((x, y, z0)) for x, y in outer]
    ot = [bm.verts.new((x, y, z1)) for x, y in outer]
    ib = [bm.verts.new((x, y, z0)) for x, y in inner]
    it = [bm.verts.new((x, y, z1)) for x, y in inner]
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bm_lathe(prof, n=32, closed=False, amp=None, phase=0.0, a0=0.0, a1=None):
    """Surface of revolution about +Z. prof: [(r, z), ...]. closed: the profile is a loop (a solid
    ring such as a bell with wall thickness). amp[k]: radial corrugation of profile point k
    (alternating +-amp around, a tube-wall look). Points with r == 0 become poles.
    a0/a1: partial revolution in degrees (open sector, no end caps)."""
    bm = bmesh.new()
    full = a1 is None
    segs = n if full else n + 1
    rings = []
    for k, (r, z) in enumerate(prof):
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))] * segs)
            continue
        ring = []
        for j in range(segs):
            a = (a0 + (360.0 if full else (a1 - a0)) * j / n) * DEG + phase
            rr = r + ((amp[k] if amp else 0.0) * (1 if j % 2 == 0 else -1))
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    K = len(prof)
    for k in range(K if closed else K - 1):
        A, B = rings[k], rings[(k + 1) % K]
        for j in range(n):
            j2 = (j + 1) % segs
            vs = [A[j], A[j2], B[j2], B[j]]
            uniq = []
            for v in vs:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    bm.faces.new(uniq)
                except ValueError:
                    pass
    if closed or (prof[0][0] < 1e-6 and prof[-1][0] < 1e-6):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bm_loft(rings, closed=True):
    """Solid (closed=True: the ring sequence loops back, e.g. a frame with a chamfered outer
    face and a recessed inner wall) or open loft between outlines [(pts2d, z), ...] with the
    same point count. An open loft is capped at both ends."""
    bm = bmesh.new()
    R = [[bm.verts.new((x, y, z)) for x, y in pts] for pts, z in rings]
    m = len(R[0])
    K = len(R)
    for k in range(K if closed else K - 1):
        A, B = R[k], R[(k + 1) % K]
        for j in range(m):
            j2 = (j + 1) % m
            bm.faces.new((A[j], A[j2], B[j2], B[j]))
    if not closed:
        bm.faces.new(R[0]); bm.faces.new(R[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def fillet_path(pts, rad, nseg=4):
    """Polyline with quadratic-Bezier fillets of about `rad` at the interior corners."""
    P = [Vector(p) for p in pts]
    if len(P) < 3 or rad <= 0:
        return P
    out = [P[0]]
    for i in range(1, len(P) - 1):
        A, B, C = P[i - 1], P[i], P[i + 1]
        u, v = (A - B), (C - B)
        la, lc = u.length, v.length
        u.normalize(); v.normalize()
        th = u.angle(v)
        if th > math.pi - 1e-3:
            out.append(B); continue
        t = min(rad / math.tan(th / 2), la * 0.5, lc * 0.5)
        P1, P2 = B + u * t, B + v * t
        for s in range(nseg + 1):
            s /= nseg
            out.append(P1 * (1 - s) ** 2 + B * 2 * s * (1 - s) + P2 * s * s)
    out.append(P[-1])
    return out


def bm_tube(path, r, n=8, caps=True):
    """Circular tube swept along a polyline (parallel-transport frames)."""
    P = [Vector(p) for p in path]
    m = len(P)
    T = []
    for i in range(m):
        a = P[min(i + 1, m - 1)] - P[max(i - 1, 0)]
        T.append(a.normalized())
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    N = (ref - T[0] * ref.dot(T[0])).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(m):
        if i:
            N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        # keep the wall thickness through bends (miter scale)
        sc = 1.0
        if 0 < i < m - 1:
            d0 = (P[i] - P[i - 1]).normalized(); d1 = (P[i + 1] - P[i]).normalized()
            c = max(0.5, math.cos(d0.angle(d1) / 2)) if d0.length and d1.length else 1
            sc = 1 / c
        rings.append([bm.verts.new(P[i] + (N * math.cos(2 * math.pi * j / n) + B * math.sin(2 * math.pi * j / n)) * r * sc) for j in range(n)])
    for i in range(m - 1):
        for j in range(n):
            j2 = (j + 1) % n
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bm_merge(dst, src, M=None):
    """Append bmesh src into dst (optionally transformed)."""
    me = bpy.data.meshes.new('_tmp')
    src.to_mesh(me)
    if M is not None:
        me.transform(M)
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return dst


# --------------------------------------------------------------------------------------------
# Part
# --------------------------------------------------------------------------------------------
class Part:
    def __init__(self, name):
        self.name = name
        self.items = []   # (obj, mat, bevel, seg, sharp)
        self.stack = [Matrix.Identity(4)]
        self.meta = {}

    @property
    def M(self):
        return self.stack[-1]

    @contextmanager
    def at(self, at=(0, 0, 0), rot=(0, 0, 0), scale=None, M=None):
        self.stack.append(self.M @ (M if M is not None else mat_xf(at, rot, scale)))
        try:
            yield self
        finally:
            self.stack.pop()

    def mesh(self, bm, at=(0, 0, 0), rot=(0, 0, 0), mat='paint', bevel=0.01, seg=1, sharp=35, scale=None):
        M = self.M @ mat_xf(at, rot, scale)
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        if M.determinant() < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        me = bpy.data.meshes.new(f'{self.name}.{len(self.items)}')
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(ob)
        self.items.append((ob, mat, bevel, seg, sharp))
        return ob

    # primitives (sizes in metres, rot = XYZ Euler degrees about the primitive's own centre)
    def box(self, size, at=(0, 0, 0), rot=(0, 0, 0), **kw):
        kw.setdefault('bevel', min(0.02, min(size) * 0.2))
        return self.mesh(bm_box(*size), at, rot, **kw)

    def cyl(self, r, h, at=(0, 0, 0), rot=(0, 0, 0), n=24, r2=None, caps=True, **kw):
        kw.setdefault('bevel', min(0.02, r * 0.2, h * 0.2))
        return self.mesh(bm_cyl(r, h, n, r2, caps), at, rot, **kw)

    def prism(self, pts, z0, z1, at=(0, 0, 0), rot=(0, 0, 0), **kw):
        kw.setdefault('bevel', min(0.02, abs(z1 - z0) * 0.2))
        return self.mesh(bm_prism(pts, z0, z1), at, rot, **kw)

    def frame(self, outer, inner, z0, z1, at=(0, 0, 0), rot=(0, 0, 0), **kw):
        kw.setdefault('bevel', min(0.02, abs(z1 - z0) * 0.2))
        return self.mesh(bm_frame(outer, inner, z0, z1), at, rot, **kw)

    def loft(self, rings, closed=True, at=(0, 0, 0), rot=(0, 0, 0), **kw):
        kw.setdefault('bevel', 0.015)
        return self.mesh(bm_loft(rings, closed), at, rot, **kw)

    def lathe(self, prof, n=32, at=(0, 0, 0), rot=(0, 0, 0), closed=False, amp=None, a0=0.0, a1=None, **kw):
        kw.setdefault('bevel', 0.0)
        return self.mesh(bm_lathe(prof, n, closed, amp, a0=a0, a1=a1), at, rot, **kw)

    def tube(self, path, r, n=8, fillet=0.0, caps=True, at=(0, 0, 0), rot=(0, 0, 0), **kw):
        kw.setdefault('bevel', 0.0)
        kw.setdefault('sharp', 60)
        p = fillet_path(path, fillet) if fillet else path
        return self.mesh(bm_tube(p, r, n, caps), at, rot, **kw)

    def bolts(self, pts, r=0.02, h=0.012, n=6, normal=(0, 0, 1), mat='paint', **kw):
        """Hex bolt heads at points (local frame), axis along `normal`, one object."""
        bm = bmesh.new()
        nz = Vector(normal).normalized()
        q = Vector((0, 0, 1)).rotation_difference(nz).to_matrix().to_4x4()
        for p in pts:
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r * 0.92, depth=h,
                                  matrix=Matrix.Translation(Vector(p)) @ q @ Matrix.Translation((0, 0, h / 2)))
        kw.setdefault('bevel', 0.0)
        kw.setdefault('sharp', 30)
        return self.mesh(bm, mat=mat, **kw)

    # ----------------------------------------------------------------------------------------
    def finish(self):
        """Bevel + weighted normals per primitive, join into one object (returns it)."""
        dg = bpy.context.evaluated_depsgraph_get()
        objs = []
        for ob, mat, bevel, seg, sharp in self.items:
            me = ob.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            for f in bm.faces:
                f.smooth = True
            for e in bm.edges:
                if not e.is_manifold or e.calc_face_angle(math.pi) > sharp * DEG:
                    e.smooth = False
            bm.to_mesh(me)
            bm.free()
            me.materials.append(material(mat))
            if bevel > 0:
                m = ob.modifiers.new('bevel', 'BEVEL')
                m.width = bevel
                m.segments = seg
                m.limit_method = 'ANGLE'
                m.angle_limit = 30 * DEG
                m.harden_normals = True
                m.use_clamp_overlap = True
                m.miter_outer = 'MITER_ARC'
            w = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
            w.keep_sharp = True
            w.weight = 50
            objs.append(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        for ob in objs:
            ev = ob.evaluated_get(dg)
            me2 = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
            old = ob.data
            ob.modifiers.clear()
            ob.data = me2
            bpy.data.meshes.remove(old)
        vl = bpy.context.view_layer
        for o in vl.objects:
            o.select_set(False)
        for o in objs:
            o.select_set(True)
        vl.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        ob = vl.objects.active
        ob.name = self.name
        ob.data.name = self.name
        # merge duplicate material slots (one per primitive after the join)
        slots = {}
        remap = []
        mats = [s.material for s in ob.material_slots]
        uniq = []
        for mt in mats:
            if mt.name not in slots:
                slots[mt.name] = len(uniq); uniq.append(mt)
            remap.append(slots[mt.name])
        me = ob.data
        idx = [0] * len(me.polygons)
        me.polygons.foreach_get('material_index', idx)
        idx = [remap[i] for i in idx]
        me.materials.clear()
        for mt in uniq:
            me.materials.append(mt)
        me.polygons.foreach_set('material_index', idx)
        self.obj = ob
        return ob


def tris_of(ob):
    me = ob.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


# --------------------------------------------------------------------------------------------
# materials: bake graphs (emission output = the value being baked)
# --------------------------------------------------------------------------------------------
class G:
    def __init__(self, tree):
        self.t = tree; self.n = tree.nodes; self.l = tree.links

    def node(self, kind, **props):
        nd = self.n.new(kind)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def put(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.l.new(val, sock)
        else:
            sock.default_value = val

    def math(self, op, a, b=0.0, c=None, clamp=False):
        nd = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(nd.inputs[0], a); self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def vm(self, op, a, b=None, s=None):
        nd = self.node('ShaderNodeVectorMath', operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if s is not None:
            self.put(nd.inputs['Scale'], s)
        return nd.outputs['Value'] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else nd.outputs['Vector']

    def mr(self, v, a, b, c=0.0, d=1.0, smooth=True):
        nd = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP' if smooth else 'LINEAR')
        self.put(nd.inputs['Value'], v)
        nd.inputs['From Min'].default_value = a; nd.inputs['From Max'].default_value = b
        nd.inputs['To Min'].default_value = c; nd.inputs['To Max'].default_value = d
        return nd.outputs['Result']

    def lerp(self, a, b, f):
        return self.vm('ADD', a, self.vm('SCALE', self.vm('SUBTRACT', b, a), s=f))

    def obj(self):
        return self.node('ShaderNodeTexCoord').outputs['Object']

    def noise(self, vec, scale, detail=2.0, rough=0.5):
        nd = self.node('ShaderNodeTexNoise')
        self.put(nd.inputs['Vector'], vec)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        return nd.outputs['Fac']

    def white(self, vec):
        nd = self.node('ShaderNodeTexWhiteNoise')
        self.put(nd.inputs['Vector'], vec)
        return nd.outputs['Value']

    def ao(self, dist, samples=12):
        nd = self.node('ShaderNodeAmbientOcclusion', samples=samples, only_local=True)
        nd.inputs['Distance'].default_value = dist
        return nd.outputs['AO']

    def curv(self, radius, lo=0.004, hi=0.06):
        bv = self.node('ShaderNodeBevel', samples=8)
        bv.inputs['Radius'].default_value = radius
        geo = self.node('ShaderNodeNewGeometry')
        d = self.vm('DOT_PRODUCT', bv.outputs['Normal'], geo.outputs['Normal'])
        return self.mr(self.math('SUBTRACT', 1.0, d), lo, hi)


# material definitions: name -> (base colour linear, kind, roughness, metal)
MATS = {
    'paint':    ((0.60, 0.60, 0.585), 'paint', 0.55, 0.0),
    'paint2':   ((0.50, 0.505, 0.50), 'paint', 0.6, 0.0),     # slightly darker panels / inserts
    'dark':     ((0.16, 0.162, 0.165), 'paint', 0.65, 0.0),   # dark grey fittings, seals frames
    'gunmetal': ((0.075, 0.078, 0.082), 'metal', 0.42, 0.85),
    'steel':    ((0.30, 0.30, 0.30), 'metal', 0.38, 0.9),     # bare worn steel (rungs, treads)
    'glass':    ((0.020, 0.026, 0.036), 'glass', 0.06, 0.0),
    'copper':   ((0.32, 0.16, 0.07), 'metal', 0.35, 1.0),
    'rubber':   ((0.035, 0.035, 0.036), 'paint', 0.9, 0.0),
    'nozzle':   ((0.09, 0.088, 0.086), 'nozzle', 0.5, 0.8),
    'ceramic':  ((0.22, 0.215, 0.21), 'paint', 0.8, 0.0),     # throat plate / refractory
    'hazard':   ((0.55, 0.40, 0.08), 'hazard', 0.6, 0.0),     # worn safety stripes (livery dims them)
    'lens':     ((0.55, 0.56, 0.56), 'glass', 0.1, 0.0),      # frosted lamp lens (not a window)
    'foil':     ((0.78, 0.60, 0.28), 'metal', 0.3, 0.85),     # gold MLI foil (sensor boxes; parts_ground.foil_box)
    'foil2':    ((0.62, 0.47, 0.22), 'metal', 0.4, 0.8),      # foil tape seams
}
BAKE = {'ao': 0.35, 'curv': 0.02, 'panel': (1.6, 1.1, 1.6)}   # set per part by kit.py


def material(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    base, kind, rough, metal = MATS[name]
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    t = mt.node_tree
    for nd in list(t.nodes):
        t.nodes.remove(nd)
    g = G(t)
    out = g.node('ShaderNodeOutputMaterial')
    em = g.node('ShaderNodeEmission', name='BAKE_EMIT')
    g.l.new(em.outputs[0], out.inputs['Surface'])
    obj = g.obj()
    ao = g.ao(BAKE['ao'])
    aoc = g.math('POWER', ao, 1.0)
    if kind == 'glass':
        smudge = g.mr(g.noise(obj, 0.8, 1), 0.3, 0.7, 0.99, 1.01)  # near-flat: noise in dark glass turns into WebP blocks
        col = g.vm('SCALE', base, s=smudge)
        rgh = g.math('MULTIPLY', rough, smudge)
        met = metal
    elif kind == 'hazard':
        # diagonal stripes 0.25 m, yellow / near-black, worn
        coord = g.math('ADD', g.vm('DOT_PRODUCT', obj, (1, 1, 0)), 0.0)
        stripe = g.math('GREATER_THAN', g.math('FRACT', g.math('MULTIPLY', coord, 1 / 0.35)), 0.5)
        col = g.lerp((0.04, 0.04, 0.04), base, stripe)
        wear = g.mr(g.noise(obj, 6.0, 4, 0.65), 0.52, 0.66)
        col = g.lerp(col, (0.35, 0.34, 0.32), g.math('MULTIPLY', wear, 0.6))
        col = g.vm('SCALE', col, s=g.mr(ao, 0.3, 1.0, 0.55, 1.0))
        rgh, met = rough, metal
    else:
        curv = g.curv(BAKE['curv'])
        cellv = g.vm('FLOOR', g.vm('MULTIPLY', obj, tuple(1 / c for c in BAKE['panel'])))
        tone = g.math('MULTIPLY', g.mr(g.noise(obj, 0.22, 3), 0.3, 0.7, 0.86, 1.05), g.mr(g.white(cellv), 0.0, 1.0, 0.92, 1.04, False))
        tone = g.math('MULTIPLY', tone, g.mr(g.noise(obj, 22.0, 4), 0.35, 0.65, 0.975, 1.02))
        col = g.vm('SCALE', base, s=tone)
        streak = g.mr(g.noise(g.vm('MULTIPLY', obj, (3.0, 0.35, 3.0)), 1.2, 3), 0.42, 0.68, 0.35, 1.0)
        # grime from AO: BAKE['grime'] = (ao where grime is full, ao where it ends, strength); defaults are the ship kit's
        glo, ghi, gk = BAKE.get('grime', (0.35, 0.985, 1.0))
        grime = g.math('MULTIPLY', g.math('MULTIPLY', g.mr(ao, glo, ghi, 1.0, 0.0), streak, clamp=True), gk)
        brk = g.mr(g.noise(obj, 7.0, 6, 0.7), 0.46, 0.60)
        convex = g.math('MULTIPLY', curv, g.mr(ao, 0.75, 0.97))
        wear = g.math('MULTIPLY', convex, g.math('ADD', 0.35, g.math('MULTIPLY', brk, 1.2)), clamp=True)
        if kind == 'paint':
            gcol = g.vm('MULTIPLY', col, (0.30, 0.29, 0.27))
            col = g.lerp(col, gcol, g.math('MULTIPLY', grime, 0.9))
            col = g.lerp(col, (0.92, 0.92, 0.90) if base[0] > 0.3 else (0.40, 0.40, 0.395), wear)
            rgh = g.math('ADD', rough, g.math('SUBTRACT', g.math('MULTIPLY', grime, 0.2), g.math('MULTIPLY', wear, 0.2)))
            met = g.math('MULTIPLY', wear, 0.3)
            if BAKE.get('grit'):
                col = _grit(g, name, base, col, obj, ao)
        elif kind in ('metal', 'nozzle'):
            gcol = g.vm('MULTIPLY', col, (0.55, 0.53, 0.50))
            col = g.lerp(col, gcol, g.math('MULTIPLY', grime, 0.6))
            hi = tuple(min(1, c * 2.6 + 0.05) for c in base)
            col = g.lerp(col, hi, g.math('MULTIPLY', wear, 0.8))
            if kind == 'nozzle':
                # heat tint: straw / bronze bands toward the throat (object z up to the throat depth)
                z = g.node('ShaderNodeSeparateXYZ')
                g.put(z.inputs[0], obj)
                h = g.mr(z.outputs['Z'], BAKE.get('heat0', 0.5), BAKE.get('heat1', 2.0))
                band = g.mr(g.noise(obj, 1.5, 2), 0.3, 0.7, 0.6, 1.0)
                col = g.lerp(col, (0.20, 0.12, 0.05), g.math('MULTIPLY', h, band))
            rgh = g.math('ADD', rough, g.math('MULTIPLY', grime, 0.2))
            met = metal
    g.l.new(col, em.inputs['Color'])
    # stash the three outputs for relinking between bake passes
    def value_socket(v):
        if isinstance(v, bpy.types.NodeSocket):
            return v
        nd = g.node('ShaderNodeValue'); nd.outputs[0].default_value = v
        return nd.outputs[0]
    rs, ms = value_socket(rgh), value_socket(met)
    rs.node.label = 'OUT_ROUGH'; ms.node.label = 'OUT_METAL'
    mt['bake'] = 1
    mt['_col_node'] = em.inputs['Color'].links[0].from_node.name if em.inputs['Color'].links else ''
    mt['_col_sock'] = em.inputs['Color'].links[0].from_socket.identifier if em.inputs['Color'].links else ''
    mt['_r'] = (rs.node.name, rs.identifier)
    mt['_m'] = (ms.node.name, ms.identifier)
    return mt


def _grit(g, name, base, col, obj, ao):
    """v6 (colony buildings, lib.BAKE['grit']): the concepts' grit in the hull bake.
    Light paint walls: crisp vertical grime / rust streaks, columns 12 cm wide (white noise per column and storey:
    hard sides), each from a 3 m course line fading downward over 0.5-3 m, broken along its run.
    Concrete (plinth top, footings): broad damp / oil stains, small dark oil spots, darker toward the ground's low AO."""
    geo = g.node('ShaderNodeNewGeometry')
    sep = g.node('ShaderNodeSeparateXYZ')
    g.put(sep.inputs[0], geo.outputs['Normal'])
    ny = g.math('ABSOLUTE', sep.outputs['Y'])
    if name in ('concrete', 'concrete2', 'kerb'):
        top = g.mr(ny, 0.6, 0.9)
        # r2: the r1 stains were too faint to read at the concept camera: bigger, darker, more of them
        stain = g.mr(g.noise(obj, 0.045, 4, 0.6), 0.38, 0.6, 0.0, 1.0)
        stain2 = g.mr(g.noise(obj, 0.22, 3, 0.55), 0.46, 0.66, 0.0, 1.0)
        vor = g.node('ShaderNodeTexVoronoi')
        g.put(vor.inputs['Vector'], obj)
        vor.inputs['Scale'].default_value = 0.28
        cellc = g.white(vor.outputs['Position'])
        spot = g.math('MULTIPLY', g.mr(vor.outputs['Distance'], 0.5, 0.12), g.math('GREATER_THAN', cellc, 0.72))
        spot = g.math('MULTIPLY', spot, g.mr(g.noise(obj, 1.6, 3, 0.7), 0.3, 0.6, 0.4, 1.0))   # ragged oil-spot edges
        k = g.math('ADD', g.math('ADD', g.math('MULTIPLY', stain, 0.55), g.math('MULTIPLY', stain2, 0.3)), g.math('MULTIPLY', spot, 0.7))
        k = g.math('ADD', k, 0.2)       # an overall dusty grey on the light concrete (the concept's slab is mid grey)
        k = g.math('MULTIPLY', k, g.math('ADD', 0.35, g.math('MULTIPLY', top, 0.65)), clamp=True)
        return g.lerp(col, g.vm('MULTIPLY', col, (0.42, 0.40, 0.37)), k)
    if base[0] < 0.25:
        return col
    wall = g.mr(ny, 0.5, 0.25)
    pos = g.node('ShaderNodeSeparateXYZ')
    g.put(pos.inputs[0], obj)
    H = 3.0
    below = g.math('MULTIPLY', g.math('FRACT', g.math('MULTIPLY', pos.outputs['Y'], -1.0 / H)), H)
    out = col
    for (w, dens, seed) in ((0.12, 0.74, 0.0), (0.28, 0.86, 7.0)):
        cell = g.vm('FLOOR', g.vm('MULTIPLY', obj, (1.0 / w, 1.0 / H, 1.0 / w)))
        w1 = g.white(g.vm('ADD', cell, (seed, 0.0, 0.0)))
        w2 = g.white(g.vm('ADD', cell, (seed + 31.0, 5.0, 3.0)))
        w3 = g.white(g.vm('ADD', cell, (seed + 57.0, 11.0, 2.0)))
        present = g.math('GREATER_THAN', w1, dens)
        L = g.math('ADD', 0.5, g.math('MULTIPLY', w2, 2.5))
        fade = g.math('SUBTRACT', 1.0, g.math('DIVIDE', below, L), clamp=True)
        brk = g.mr(g.noise(g.vm('MULTIPLY', obj, (6.0, 1.2, 6.0)), 1.0, 2), 0.35, 0.55, 0.45, 1.0)
        m = g.math('MULTIPLY', g.math('MULTIPLY', present, fade), g.math('MULTIPLY', brk, wall))
        m = g.math('MULTIPLY', m, g.mr(w3, 0.0, 1.0, 0.35, 0.7))
        rusty = g.math('GREATER_THAN', w3, 0.75)
        tint = g.lerp(g.vm('MULTIPLY', col, (0.45, 0.43, 0.40)), (0.16, 0.08, 0.035), rusty)
        out = g.lerp(out, tint, m)
    return out


def _relink(mt, which):
    t = mt.node_tree
    em = t.nodes['BAKE_EMIT']
    for lk in list(em.inputs['Color'].links):
        t.links.remove(lk)
    if which == 'color':
        if mt['_col_node']:
            nd = t.nodes[mt['_col_node']]
            sock = [s for s in nd.outputs if s.identifier == mt['_col_sock']][0]
            t.links.new(sock, em.inputs['Color'])
    else:
        nn, ident = mt['_r'] if which == 'rough' else mt['_m']
        nd = t.nodes[nn]
        sock = [s for s in nd.outputs if s.identifier == ident][0]
        t.links.new(sock, em.inputs['Color'])


def unwrap(ob, margin=0.004):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=60 * DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def bake(ob, size=512, samples=16):
    """Bake base colour (sRGB) and an ORM map (R 1, G roughness, B metal) for ob's materials;
    then replace the materials with one glTF-ready material. Returns seconds spent."""
    t0 = time.time()
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.render.bake.margin = max(4, size // 128)
    sc.render.bake.use_clear = True
    col = bpy.data.images.new(f'{ob.name}_basecolor', size, size, alpha=False)
    rgh = bpy.data.images.new(f'{ob.name}_rough', size, size, alpha=False, is_data=True)
    met = bpy.data.images.new(f'{ob.name}_metal', size, size, alpha=False, is_data=True)
    mats = [s.material for s in ob.material_slots]
    for mt in mats:
        tn = mt.node_tree.nodes.new('ShaderNodeTexImage')
        tn.name = 'BAKE_TARGET'
        mt.node_tree.nodes.active = tn
    for img, which, spp in ((col, 'color', samples), (rgh, 'rough', max(4, samples // 3)), (met, 'metal', 1)):
        sc.cycles.samples = spp
        for mt in mats:
            mt.node_tree.nodes['BAKE_TARGET'].image = img
            _relink(mt, which)
        bpy.ops.object.bake(type='EMIT')
    # ORM
    import numpy as np
    n = size * size * 4
    a = np.empty(n, dtype=np.float32); b = np.empty(n, dtype=np.float32)
    rgh.pixels.foreach_get(a); met.pixels.foreach_get(b)
    orm = np.ones(n, dtype=np.float32)
    orm[1::4] = a[0::4]; orm[2::4] = b[0::4]
    ormi = bpy.data.images.new(f'{ob.name}_orm', size, size, alpha=False, is_data=True)
    ormi.pixels.foreach_set(orm)
    ormi.pack()
    col.pack()
    # final material
    fm = bpy.data.materials.new(ob.name)
    fm.use_nodes = True
    t = fm.node_tree
    bsdf = t.nodes['Principled BSDF']
    ti = t.nodes.new('ShaderNodeTexImage'); ti.image = col
    t.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    to = t.nodes.new('ShaderNodeTexImage'); to.image = ormi
    sep = t.nodes.new('ShaderNodeSeparateColor')
    t.links.new(to.outputs['Color'], sep.inputs['Color'])
    t.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    t.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    ob.data.materials.clear()
    ob.data.materials.append(fm)
    return time.time() - t0


def export(ob, path):
    """Rotate the part frame into Blender's Z-up (part +Z -> Blender -Y) and write a GLB."""
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    ob.rotation_euler = (90 * DEG, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_texcoords=True, export_normals=True,
                              export_tangents=False, export_materials='EXPORT', export_animations=False,
                              export_extras=False, export_image_format='AUTO')


def basis(origin=(0, 0, 0), x=(1, 0, 0), y=(0, 1, 0), z=None):
    """4x4 matrix whose columns are the local x, y, z axes (z = x cross y if omitted)."""
    X, Y = Vector(x).normalized(), Vector(y).normalized()
    Z = Vector(z).normalized() if z else X.cross(Y)
    M = Matrix.Identity(4)
    for i in range(3):
        M[i][0], M[i][1], M[i][2], M[i][3] = X[i], Y[i], Z[i], origin[i]
    return M
