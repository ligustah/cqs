"""Post-assembly additions for the Drover-class ships (CT-4 / CT-7): container stacks and the
low-poly port lites, then export and optimise.

    <blender-python> tools/blender/hulls/freighter_extras.py <assembled.blend> <out.glb> --variant cargo|troops
                     [--work <dir>] [--tex 6144]

Containers (cargo): the kit's 20-ft ISO container (assets/parts-blender/container.glb, 6.06 x
2.59 x 2.44 m) baked once onto a 12-triangle box (Cycles selected-to-active: base colour,
tangent-space normal, roughness) in a 2048 atlas with two weathering variants. Every box of the
stacks (freighter_dims.containers) is one such box; the cargo colour is the material's base
colour factor (rust, ochre, blue, green, grey, white: six materials sharing the atlas), so it
multiplies the texture before the runtime livery (livery.js keeps saturated texels as muted
cargo colours). Node 'parts_container'.

Port lites: ~1 m ports on the 3 m decks, hundreds of them (the troop ship's habitats carry 750),
so not the 1160-triangle kit port: a 38-triangle sloped bezel and a recessed pane (kit port
proportions: 1.4 m frame, 1.0 m glass), flat paint and a glass material that passes livery.js's
glass test (dark, blue-tinted, glassGlow lights it). Rows are ray-cast onto the hull (mount
face on the hit, sunk 0.03 m). Node 'parts_portlite'.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image  # noqa: E402

import assemble_frame as F  # noqa: E402
import freighter_dims as D  # noqa: E402

V = Vector
KIT = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'parts-blender'))


def srgb2lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ------------------------------------------------------------------------------------------
# container: low-poly box + atlas baked from the kit container
# ------------------------------------------------------------------------------------------
# atlas 2048 x 2048: variant 0 in the upper half, variant 1 in the lower half; per half
# (2048 x 1024 px, 160 px/m): (u0, v0, u1, v1) in pixels of the half, v from its top
PXM = 160
REG = {
    '+w': (8, 8, 978, 423), '-w': (990, 8, 1960, 423),
    '+h': (8, 435, 978, 825), '+x': (990, 435, 1380, 850), '-x': (1392, 435, 1782, 850), '-h': (1794, 435, 2040, 825),
}


def box_faces(lo, hi, hax, wax):
    """The 6 faces of an axis box in the part frame, as (key, 4 corners CCW seen from outside,
    (u axis, v axis) for the atlas). Axes: 0 = x (length), hax = height, wax = width."""
    out = []
    for key, ax, s in (('+x', 0, 1), ('-x', 0, -1), ('+h', hax, 1), ('-h', hax, -1), ('+w', wax, 1), ('-w', wax, -1)):
        others = [a for a in range(3) if a != ax]
        # u/v axes: sides and ends: u horizontal (x or w), v = height; top/bottom: u = x, v = w
        if ax == 0:
            ua, va = wax, hax
        elif ax == hax:
            ua, va = 0, wax
        else:
            ua, va = 0, hax
        c = [0.0, 0.0, 0.0]
        c[ax] = hi[ax] if s > 0 else lo[ax]
        pts = []
        for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
            p = list(c)
            p[ua] = hi[ua] if du else lo[ua]
            p[va] = hi[va] if dv else lo[va]
            pts.append((p, du, dv))
        # wind CCW seen from outside: normal = (p1 - p0) x (p3 - p0) must point along +s on ax
        a, b, d = V(pts[0][0]), V(pts[1][0]), V(pts[3][0])
        n = (b - a).cross(d - a)
        if n[ax] * s < 0:
            pts = [pts[0], pts[3], pts[2], pts[1]]
        out.append((key, pts))
    return out


def face_uv(key, du, dv, variant):
    u0, v0, u1, v1 = REG[key]
    x = u0 + (u1 - u0) * du
    y = v1 - (v1 - v0) * dv          # v up = image up
    half = 0 if variant == 0 else 1024
    return (x / 2048.0, 1.0 - (y + half) / 2048.0)


class ContainerKit:
    def __init__(self, work):
        self.work = work
        os.makedirs(work, exist_ok=True)
        self.base = os.path.join(work, 'container_base.png')
        self.nrm = os.path.join(work, 'container_normal.png')
        self.orm = os.path.join(work, 'container_orm.png')
        info = os.path.join(work, 'container.json')
        if not (os.path.exists(self.base) and os.path.exists(info)):
            self.bake()
        self.info = json.load(open(info))

    def bake(self):
        """Bake the kit container onto the low box in a scratch scene (restores nothing: run
        before the assembly is loaded)."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        dec = F.decode([(os.path.join(KIT, 'container.glb'), 'kit-container')], os.path.join(self.work, 'dec'))['kit-container']
        ms, new = F.import_glb(dec)
        hi_ob = F.join(ms, 'kit_container')
        co = np.array([F.s_vec(hi_ob.matrix_world @ v.co)[:] for v in hi_ob.data.vertices])
        lo, hi = co.min(0), co.max(0)
        ext = hi - lo
        hax = int(np.argmin(np.abs(ext - D.ISO[1])))
        wax = 3 - hax
        # the low box: the kit's body (door handles 5 cm proud are left to the normal map)
        lo_b, hi_b = lo.copy(), hi.copy()
        hi_b[0] = lo_b[0] + D.ISO[0]
        info = {'lo': lo_b.tolist(), 'hi': hi_b.tolist(), 'hax': hax, 'wax': wax}
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        for key, pts in box_faces(lo_b, hi_b, hax, wax):
            vs = [bm.verts.new(F.b_vec(p)) for p, du, dv in pts]
            f = bm.faces.new(vs)
            for l, (p, du, dv) in zip(f.loops, pts):
                l[uvl].uv = face_uv(key, du, dv, 0)
        me = bpy.data.meshes.new('low_container')
        bm.to_mesh(me)
        bm.free()
        low = bpy.data.objects.new('low_container', me)
        bpy.context.collection.objects.link(low)
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 4
        sc.render.threads_mode = 'FIXED'
        sc.render.threads = 4
        bk = sc.render.bake
        bk.use_selected_to_active = True
        bk.cage_extrusion = 0.12
        bk.max_ray_distance = 0.3
        bk.margin = 6
        bk.use_clear = True
        res = {}
        for kind in ('DIFFUSE', 'NORMAL', 'ORM'):
            img = bpy.data.images.new(f'c_{kind}', 2048, 2048, alpha=False, float_buffer=True)
            if kind != 'DIFFUSE':
                img.colorspace_settings.name = 'Non-Color'
            m = bpy.data.materials.new(f'low_{kind}')
            m.use_nodes = True
            tn = m.node_tree.nodes.new('ShaderNodeTexImage')
            tn.image = img
            m.node_tree.nodes.active = tn
            me.materials.clear()
            me.materials.append(m)
            restore = []
            if kind == 'ORM':
                # wire the kit's ORM texture into an emission shader on the high poly
                for mat in hi_ob.data.materials:
                    nt = mat.node_tree
                    orm = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'orm' in n.image.name.lower()), None)
                    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
                    old = out.inputs['Surface'].links[0].from_socket if out.inputs['Surface'].links else None
                    em = nt.nodes.new('ShaderNodeEmission')
                    nt.links.new(orm.outputs['Color'], em.inputs['Color'])
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                    restore.append((nt, out, old, em))
            for o in bpy.context.view_layer.objects:
                o.select_set(False)
            hi_ob.select_set(True)
            low.select_set(True)
            bpy.context.view_layer.objects.active = low
            if kind == 'DIFFUSE':
                bk.use_pass_direct = False
                bk.use_pass_indirect = False
                bk.use_pass_color = True
                bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
            elif kind == 'NORMAL':
                bk.normal_space = 'TANGENT'
                bpy.ops.object.bake(type='NORMAL')
            else:
                bpy.ops.object.bake(type='EMIT')
            for nt, out, old, em in restore:
                if old is not None:
                    nt.links.new(old, out.inputs['Surface'])
                nt.nodes.remove(em)
            a = np.empty(2048 * 2048 * 4, np.float32)
            img.pixels.foreach_get(a)
            res[kind] = a.reshape(2048, 2048, 4)[::-1, :, :3].copy()   # rows top-down
        self.paint(res, info)
        json.dump(info, open(os.path.join(self.work, 'container.json'), 'w'), indent=1)

    def paint(self, res, info):
        """Variant 0 (upper half) = the bake with light grime; variant 1 (lower half) = heavier
        weathering: vertical run streaks and darker lower edges. Luminance only (the colour is
        the material tint)."""
        base = res['DIFFUSE']
        top = base[:1024].copy()
        lum = lambda a: a.mean(-1, keepdims=True)
        # neutralise the kit paint's own hue (the tint carries the colour), keep its value
        top = np.repeat(lum(top), 3, -1) * 0.85 + top * 0.15
        yy, xx = np.mgrid[0:1024, 0:2048].astype(np.float32)
        rng = np.random.default_rng(4)
        streak = np.zeros((1024, 2048), np.float32)
        cols = rng.integers(0, 2048, 260)
        for cx in cols:
            w = rng.uniform(2, 7)
            L = rng.uniform(40, 220)
            y0 = rng.uniform(0, 1024)
            streak += np.exp(-((xx - cx) / w) ** 2) * np.clip(1 - (yy - y0) / L, 0, 1) * (yy > y0) * rng.uniform(0.05, 0.18)
        v0 = top * (1 - 0.35 * np.clip(streak, 0, 0.5)[..., None])
        low = np.clip((yy % 512) / 512.0, 0, 1)
        v1 = top * (1 - 0.8 * np.clip(streak, 0, 0.6)[..., None]) * (0.92 + 0.08 * (1 - low))[..., None]
        out = np.concatenate([v0, v1], 0)
        # the bake stores linear colour; write sRGB
        srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
        Image.fromarray((np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(self.base)
        n = res['NORMAL'][:1024]
        Image.fromarray((np.clip(np.concatenate([n, n], 0), 0, 1) * 255 + 0.5).astype(np.uint8)).save(self.nrm)
        o = res['ORM'][:1024].copy()
        o[..., 0] = 1.0
        o[..., 2] = np.clip(o[..., 2], 0, 0.2)
        o2 = o.copy()
        o2[..., 1] = np.clip(o2[..., 1] + 0.08, 0, 1)
        Image.fromarray((np.clip(np.concatenate([o, o2], 0), 0, 1) * 255 + 0.5).astype(np.uint8)).save(self.orm)

    def materials(self):
        ib = bpy.data.images.load(self.base)
        ib.colorspace_settings.name = 'sRGB'
        io_ = bpy.data.images.load(self.orm)
        io_.colorspace_settings.name = 'Non-Color'
        inn = bpy.data.images.load(self.nrm)
        inn.colorspace_settings.name = 'Non-Color'
        mats = {}
        for name, rgb in D.CARGO_COLOURS.items():
            m = bpy.data.materials.new(f'container_{name}')
            m.use_nodes = True
            t = m.node_tree
            b = t.nodes['Principled BSDF']
            lin = srgb2lin(rgb)
            b.inputs['Base Color'].default_value = (*lin, 1.0)
            ti = t.nodes.new('ShaderNodeTexImage'); ti.image = ib
            mix = t.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs['A'].default_value = (*lin, 1.0)
            t.links.new(ti.outputs['Color'], mix.inputs['B'])
            t.links.new(mix.outputs['Result'], b.inputs['Base Color'])
            to = t.nodes.new('ShaderNodeTexImage'); to.image = io_
            sep = t.nodes.new('ShaderNodeSeparateColor')
            t.links.new(to.outputs['Color'], sep.inputs['Color'])
            t.links.new(sep.outputs['Green'], b.inputs['Roughness'])
            t.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
            tn = t.nodes.new('ShaderNodeTexImage'); tn.image = inn
            nm = t.nodes.new('ShaderNodeNormalMap')
            t.links.new(tn.outputs['Color'], nm.inputs['Color'])
            t.links.new(nm.outputs['Normal'], b.inputs['Normal'])
            m.use_backface_culling = True
            mats[name] = m
        return mats


def add_containers(v, kit):
    info = kit.info
    lo, hi = np.array(info['lo']), np.array(info['hi'])
    hax, wax = info['hax'], info['wax']
    ctr = (lo + hi) / 2
    mats = kit.materials()
    names = list(D.CARGO_COLOURS)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    faces = box_faces(lo, hi, hax, wax)
    n = 0
    for c in D.containers(v):
        s = -1.0 if c['flip'] else 1.0
        # part frame -> ship: x -> s * x, height -> y, width -> s * z (a rotation about y)
        def to_ship(p):
            q = np.array(p) - ctr
            return V((s * q[0] + c['c'][0], q[hax] + c['c'][1], s * q[wax] * (1 if wax == 2 else 1) + c['c'][2]))
        vi = c['var'] % 2
        mi = names.index(c['colour'])
        cb = F.b_vec(V(c['c']))
        for key, pts in faces:
            ps = [F.b_vec(to_ship(p)) for p, du, dv in pts]
            # wind every face outward from the box centre (faces do not share verts, so no recalc)
            nrm = (ps[1] - ps[0]).cross(ps[3] - ps[0])
            if nrm.dot(sum(ps, V((0, 0, 0))) / 4 - cb) < 0:
                pts = [pts[0], pts[3], pts[2], pts[1]]
                ps = [ps[0], ps[3], ps[2], ps[1]]
            vs = [bm.verts.new(q) for q in ps]
            f = bm.faces.new(vs)
            f.material_index = mi
            for l, (p, du, dv) in zip(f.loops, pts):
                l[uvl].uv = face_uv(key, du, dv, vi)
        n += 1
    me = bpy.data.meshes.new('parts_container')
    bm.to_mesh(me)
    bm.free()
    for nm in names:
        me.materials.append(mats[nm])
    ob = bpy.data.objects.new('parts_container', me)
    bpy.context.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    print(f'[extras] containers: {n} boxes, {len(me.polygons) * 2} tris', flush=True)
    return ob


# ------------------------------------------------------------------------------------------
# port lites
# ------------------------------------------------------------------------------------------
def port_mesh():
    """Local frame: +Z out of the hull, mount face at z = 0. Returns (verts, faces, face mats):
    sloped bezel 1.14 m (chamfer 0.22) up to a 0.86 m opening 0.12 m proud, pane
    recessed 0.09 m behind the frame face."""
    def oct_(w, c):
        h = w / 2
        return [(h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c), (-h + c, -h), (h - c, -h)]
    outer, inner = oct_(1.14, 0.22), oct_(0.86, 0.16)
    zb, zf, zg = -0.02, 0.12, 0.05
    # sloped bezel from the hull (outer edge sunk) up to the opening, inner wall down to the pane
    verts = [(x, y, zb) for x, y in outer] + [(x, y, zf) for x, y in inner] + [(x, y, zg) for x, y in inner]
    faces, mats = [], []
    for i in range(8):
        j = (i + 1) % 8
        faces.append((i, j, 8 + j, 8 + i)); mats.append(0)              # bezel
        faces.append((8 + i, 8 + j, 16 + j, 16 + i)); mats.append(0)    # inner wall
    faces.append(tuple(16 + i for i in range(8))); mats.append(1)   # glass
    return verts, faces, mats


def port_materials():
    fr = bpy.data.materials.new('portlite_frame')
    fr.use_nodes = True
    b = fr.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb2lin([0.66, 0.66, 0.65]), 1)
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Metallic'].default_value = 0.2
    gl = bpy.data.materials.new('portlite_glass')
    gl.use_nodes = True
    b = gl.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.030, 0.038, 0.050, 1)   # linear: livery glass test (b/r 1.67, l 0.037, sat 0.4)
    b.inputs['Roughness'].default_value = 0.08
    # lit cabins: a second pane material with a dim warm emission (glTF emissiveFactor; the
    # livery never touches emission), on ~45 % of the ports, by compartment (hash of a 3.8 m cell on each deck)
    gl2 = gl.copy()
    gl2.name = 'portlite_glass_lit'
    b = gl2.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (0.042, 0.032, 0.020, 1)
    b.inputs['Emission Strength'].default_value = 1.0
    for m in (fr, gl, gl2):
        m.use_backface_culling = True
    return fr, gl, gl2


def port_rows(v):
    """Candidate ports (p, n) in the ship frame, before the hull snap: crew-module decks (all
    variants), the troop habitats' outboard decks."""
    out = []
    cm0, L = v['CM0'], v['CM_LEN']
    fx = D.CM['fx']
    doors = [cm0 + 4.6, cm0 + 17.2]
    ladder = cm0 + 6.4
    svc = (cm0 + 10.5 - 2.4, cm0 + 10.5 + 2.4)

    def clear(z, y):
        if any(abs(z - d) < 1.5 for d in doors) and y < D.DECKS[0] + 3.4:
            return False
        if abs(z - ladder) < 0.9:
            return False
        if svc[0] < z < svc[1] and -5.4 < y < -2.2:
            return False
        if abs(z - (cm0 + 11.0)) < 0.2:
            return False
        return True
    for yf in D.DECKS:
        y = yf + 1.5
        xw = fx if y < D.CM['ledge'] else fx - D.CM['ins']
        for z in np.arange(cm0 + 1.4, cm0 + D.CM['taper'] - 0.6, 1.9):
            if y > 0.7 and y < 2.2:
                continue
            if clear(z, y):
                out.append(((xw, y, z), (1, 0, 0)))
        # the tapered bow flank: rows below the bridge band
        if y < 0.5:
            for u in np.arange(D.CM['taper'] + 1.4, L - 1.6, 1.9):
                x = D.cm_half(u, L)[4][0]
                dx = (D.CM['nose']['fx'] - fx) / (L - D.CM['taper'])
                n = V((1, 0, -dx)).normalized()
                if y > D.cm_half(u, L)[5][1] + 0.8:
                    out.append(((x, y, cm0 + u), tuple(n)))
    # roof tier windows on the upper tier are covered by the rows above (y 6.1)
    if v['variant'] == 'troops':
        H = D.HAB
        z0, z1 = D.hab_span(v)
        zc0, zc1 = z0 + H['dome'], z1 - H['dome']
        n_r = max(2, int(round((zc1 - zc0) / H['ring_pitch'])))
        rings = [zc1 - i * (zc1 - zc0) / n_r for i in range(n_r + 1)]
        zm = (z0 + z1) / 2
        door = zm + 2.3
        for yc, dys in ((H['yu'], (-1.7, 1.3, 3.5)), (H['yl'], (-3.5, -1.7, 1.3))):
            for dy in dys:
                dxx = math.sqrt(H['r'] ** 2 - dy ** 2)
                n = V((dxx, dy, 0)).normalized()
                for z in np.arange(zc0 + 0.9, zc1 - 0.6, 1.45):
                    if any(abs(z - r) < 0.75 for r in rings):
                        continue
                    if abs(z - door) < 1.4 and abs(dy) < 2.0:
                        continue
                    out.append(((H['x'] + dxx, yc + dy, z), tuple(n)))
    # mirror to starboard
    return out + [((-p[0], p[1], p[2]), (-n[0], n[1], n[2])) for p, n in out]


def add_ports(v, hull):
    caster = F.HullCaster(hull)
    verts, faces, mats = port_mesh()
    fr, gl, gl2 = port_materials()
    bm = bmesh.new()
    n_ok = n_miss = 0
    for p, n in port_rows(v):
        p, n = V(p), V(n).normalized()
        hit = caster.cast(p + n * 3, -n, 5)
        if hit is None or hit[1].dot(n) < 0.8 or abs(hit[3] - 3) > 0.8:
            n_miss += 1
            continue
        nn = hit[1]
        up = V((0, 1, 0)) - nn * nn.y
        if up.length < 1e-3:
            up = V((0, 0, 1))
        up.normalize()
        r = up.cross(nn)
        base = hit[0] - nn * 0.03
        vs = [bm.verts.new(F.b_vec(base + r * x + up * y + nn * z)) for x, y, z in verts]
        cell = (math.floor(base.x / 6.0), math.floor(base.y / 3.0), math.floor(base.z / 3.8))
        lit = D._hash(cell[0] + 50, cell[1] + 50, cell[2] + 80, 17) < 0.45
        for f, m in zip(faces, mats):
            ff = bm.faces.new([vs[i] for i in f])
            ff.material_index = 2 if (m == 1 and lit) else m
        n_ok += 1
    # the winding is authored outward (bezel, pane) and inward (opening wall): no recalc, which
    # flips an open mesh at random
    me = bpy.data.meshes.new('parts_portlite')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(fr)
    me.materials.append(gl)
    me.materials.append(gl2)
    ob = bpy.data.objects.new('parts_portlite', me)
    bpy.context.collection.objects.link(ob)
    import assemble_parts as AP
    AP.harden(ob)
    print(f'[extras] port lites: {n_ok} placed, {n_miss} missed, {sum(len(p.vertices) - 2 for p in me.polygons)} tris', flush=True)
    return ob, n_ok


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    blend, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    v = D.V(opt('--variant', 'cargo'))
    work = os.path.abspath(opt('--work', os.path.join(os.path.dirname(out), 'extras')))
    tex = int(opt('--tex', 6144))
    kit = ContainerKit(work) if v['variant'] == 'cargo' else None
    bpy.ops.wm.open_mainfile(filepath=blend)
    hull = bpy.data.objects['hull']
    report = {}
    if kit:
        add_containers(v, kit)
    _, report['ports'] = add_ports(v, hull)
    tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'}
    report['tris'] = {**tris, 'total': sum(tris.values())}
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type == 'MESH':
            a, b = F.vert_box(o)
            lo = V(map(min, lo, a)); hi = V(map(max, hi, b))
    report['bbox'] = [list(lo), list(hi)]
    report['size'] = list(hi - lo)
    raw = out.replace('.glb', '.raw.glb')
    bpy.ops.export_scene.gltf(filepath=raw, export_format='GLB', export_yup=True, export_apply=False, export_normals=True, export_tangents=False,
                              export_texcoords=True, export_materials='EXPORT', export_image_format='AUTO', export_cameras=False, export_lights=False,
                              export_extras=False, use_selection=False)
    subprocess.run(['node', os.path.join(F.SCENE3D, 'tools/optimize-glb.mjs'), raw, out, '--tris', '100000000', '--tex', str(tex)], check=True, cwd=F.SCENE3D)
    report['bytes'] = os.path.getsize(out)
    json.dump(report, open(out.replace('.glb', '.extras.json'), 'w'), indent=1)
    print('[extras]', json.dumps({k: report[k] for k in ('ports', 'size', 'bytes')}), 'tris', report['tris']['total'], flush=True)


if __name__ == '__main__':
    main()
