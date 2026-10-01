"""The shipyard's own geometry (the 'hull' node of assets/buildings/shipyard.glb), YARD frame.

    $PY tools/blender/buildings/shipyard.py <workdir> [--tex 4096] [--threads 4] [--samples 8]
      -> <workdir>/shipyard-hull.glb (+ ground texture), read by assemble.py through
         tools/blender/specs/shipyard-v1.json (shipyard_spec.py)

Everything else in the yard is a kit part placed by the spec: yard kit (assets/parts-yard: gantry,
cranes, halls, flood masts, scaffolds, trucks, forklifts, workers, keel blocks, bollards) and the
fleet kit (assets/parts-blender: doors, panes, vents, ladders, rails, containers, floodlights, the
drive bell). The DD-12 itself is NOT in the GLB: src/buildings/shipyard.js instances
assets/ships/destroyer.glb at load and clips it to its build state (shipyard_dims.CUT).

Built here (needs specs/shipyard-dd12.json from shipyard_measure.py and parts-yard/parts.json):
  - structure (one lib.Part, baked like a kit part): the DD-12's procedural ring frames following
    its measured octagonal sections, the bare keel and stringers aft, the module the gantry lowers
    with its spreader, slings and hoist ropes, the frame segment crane A carries, the drive-bell
    cradle, gantry and crane rails on their beams, rail buffers;
  - ground (tiled, not baked): the apron slab with a generated 24 m concrete texture (8 m slabs),
    a darker berth floor, painted lines (amber berth edge and rail-zone lines, white lanes).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import lib  # noqa: E402
import yard_kit as K  # noqa: E402  (adds the yard materials to lib.MATS)
import shipyard_dims as D  # noqa: E402

V = Vector
ROOT = K.ROOT
DD = json.load(open(os.path.join(HERE, '..', 'specs', 'shipyard-dd12.json')))
YARD_KIT = json.load(open(os.path.join(ROOT, 'assets', 'parts-yard', 'parts.json')))['parts']
TY = D.SHIP_T


def m2y(x, y, z):
    """destroyer MODEL frame -> YARD frame"""
    return (x + TY[0], y + TY[1], z + TY[2])


def inward(poly):
    """Unit inward normals of the edges of a CCW polygon [(x, y)]."""
    out = []
    for i in range(len(poly)):
        a, b = V(poly[i]), V(poly[(i + 1) % len(poly)])
        d = (b - a).normalized()
        out.append(V((-d.y, d.x)))  # left of a CCW edge = inside
    return out


# --------------------------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------------------------
def frames(P):
    web, t = D.FRAME_WEB, D.FRAME_T
    for f in DD['frames']:
        poly = f['outline']
        nrm = inward(poly)
        z = f['z']
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            # 'lower' frames are the build front: an open U, no top edge
            if f['kind'] == 'lower' and a[1] >= f['top'] - 0.05 and b[1] >= f['top'] - 0.05:
                continue
            n = nrm[i]
            pa = V((a[0], a[1])) + n * (web / 2)
            pb = V((b[0], b[1])) + n * (web / 2)
            K.beam(P, m2y(pa.x, pa.y, z), m2y(pb.x, pb.y, z), t, web, 'charcoal2', up=(n.x, n.y, 0), bevel=0.05, ext=web / 2)
        # frame number stencil on the lowest web? (left as paint: lesson 30, no lettering spend)


def keel_and_stringers(P):
    k = D.KEEL
    ytop = min(f['ymin'] for f in DD['frames'] if f['z'] <= -37.0)
    y0, y1 = ytop - k['h'], ytop
    a, b = m2y(-k['w'] / 2, y0, k['z0']), m2y(k['w'] / 2, y1, k['z1'])
    P.box((b[0] - a[0], b[1] - a[1], b[2] - a[2]), at=((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), mat='charcoal', bevel=0.06)
    # stringers: between consecutive aft frames along their lower outline points (y < -18), and the deck-edge
    # points of the four forward aft frames (build progress runs aft)
    fr = [f for f in DD['frames'] if f['z'] <= -37.0]
    fr.sort(key=lambda f: -f['z'])
    lowpts = lambda f: [p for p in f['outline'] if p[1] < -18.0]
    for f0, f1 in zip(fr[:-1], fr[1:]):
        p0s, p1s = lowpts(f0), lowpts(f1)
        for p in p0s:
            q = min(p1s, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2, default=None)
            if q is None or abs(q[0] - p[0]) > 3.0 or abs(q[1] - p[1]) > 3.0:
                continue
            K.beam(P, m2y(p[0] * 0.97, p[1] + 0.6, f0['z']), m2y(q[0] * 0.97, q[1] + 0.6, f1['z']), 0.6, 0.6, 'charcoal2', bevel=0.03)
    top = [f for f in fr if f['kind'] == 'full'][:4]
    for f0, f1 in zip(top[:-1], top[1:]):
        for sx in (-1, 1):
            p = max(f0['outline'], key=lambda q: q[1] * 0.2 + sx * q[0])
            q = max(f1['outline'], key=lambda q: q[1] * 0.2 + sx * q[0])
            K.beam(P, m2y(p[0] * 0.95, p[1] - 1.0, f0['z']), m2y(q[0] * 0.95, q[1] - 1.0, f1['z']), 0.6, 0.8, 'charcoal2', bevel=0.03)
    # deck beams across the midships frames are the frames' own top edges; a centre girder over them
    mid = [f for f in DD['frames'] if f['z'] > -34.0]
    zs = [f['z'] for f in mid]
    yt = max(p[1] for p in mid[0]['outline'])
    K.beam(P, m2y(0, yt - 0.9, max(zs) + 0.5), m2y(0, yt - 0.9, min(zs) - 0.5), 1.0, 1.0, 'charcoal2', bevel=0.04)


def module_and_rig(P, hook):
    sx, sy, sz = D.MODULE['size']
    y0 = D.MODULE['bottom']
    cz = D.GANTRY['z']
    c = (0.0, y0 + sy / 2, cz)
    # the module: a deckhouse block in light primer, chamfered top edges, inset panels, amber corner guards
    with P.at(at=c):
        P.loft([(lib.chamfer_rect(sx, sz, 0.8), -sy / 2), (lib.chamfer_rect(sx, sz, 0.8), sy / 2 - 1.2),
                (lib.chamfer_rect(sx - 2.0, sz - 2.0, 0.6), sy / 2)], closed=False, rot=(-90, 0, 0), mat='cladding', bevel=0.08)
        for ex in (-1, 1):
            for ez in (-1, 1):
                P.box((1.2, sy - 0.6, 1.2), at=(ex * (sx / 2 - 0.3), -0.3, ez * (sz / 2 - 0.3)), mat='amber', bevel=0.05)
                P.box((0.8, 0.9, 0.8), at=(ex * (sx / 2 - 2.0), sy / 2 + 0.3, ez * (sz / 2 - 2.0)), mat='charcoal', bevel=0.04)  # lifting lugs
        for k in range(3):
            P.box((5.5, 4.0, 0.25), at=(-6.5 + k * 6.5, -0.5, sz / 2 + 0.05), mat='cladding2', bevel=0.03)
            P.box((5.5, 4.0, 0.25), at=(-6.5 + k * 6.5, -0.5, -sz / 2 - 0.05), mat='cladding2', bevel=0.03)
        P.box((0.25, 4.0, 5.0), at=(sx / 2 + 0.05, -0.5, 0.0), mat='cladding2', bevel=0.03)
        P.box((sx + 0.2, 0.5, sz + 0.2), at=(0, -sy / 2 + 0.25, 0), mat='charcoal2', bevel=0.04)  # bottom flange
    # spreader beam, slings to the lugs, hoist ropes to the crab
    ys = y0 + sy + 9.0
    P.box((sx + 4.0, 1.4, 2.6), at=(0, ys, cz), mat='amber', bevel=0.06)
    P.box((6.0, 2.2, 3.4), at=(0, ys + 1.6, cz), mat='charcoal', bevel=0.06)  # hook block
    for ex in (-1, 1):
        for ez in (-1, 1):
            K.tube(P, [(ex * (sx / 2 - 2.0), y0 + sy + 0.7, cz + ez * (sz / 2 - 2.0)), (ex * (sx / 2 + 1.0), ys - 0.6, cz + ez * 0.9)], 0.07, 'galv', n=5)
    hx, hy, hz = hook
    for ex in (-1, 1):
        for ez in (-1, 1):
            K.tube(P, [(ex * 1.6, ys + 2.6, cz + ez * 0.9), (hx + ex * 2.2, hy + 12.0, hz + ez * 1.4)], 0.06, 'galv', n=5)


def crane_load(P, hook):
    """Crane A lowers a side segment of an aft frame (an arc of the engine-block section)."""
    f = next(f for f in DD['frames'] if f['z'] == -49.0)
    arc = [p for p in f['outline'] if p[0] > 4.0 and p[1] > -24.0]
    arc.sort(key=lambda p: p[1])
    if len(arc) < 2:
        return
    hx, hy, hz = hook
    top = max(arc, key=lambda p: p[1])
    # hang the arc in the hook's vertical plane (the frame's x-y plane rotated to face the crane):
    # put its top point 3 m under the hook, keep the frame plane at z = hz
    dx = hx - top[0] + 1.5
    dy = hy - 3.0 - top[1]
    pts = [(p[0] + dx, p[1] + dy, hz) for p in arc]
    for a, b in zip(pts[:-1], pts[1:]):
        K.beam(P, a, b, D.FRAME_T, D.FRAME_WEB, 'charcoal2', up=(-1, 0, 0), bevel=0.05, ext=0.6)
    lo = pts[0]
    K.tube(P, [(hx, hy, hz), (pts[-1][0], pts[-1][1] + 0.6, hz)], 0.05, 'galv', n=5)
    K.tube(P, [(hx, hy, hz), (lo[0], lo[1] + 0.6, hz)], 0.05, 'galv', n=5)


def bell_cradle(P, prof):
    """Two saddles under the lying drive bell (kit bell-XL; axis along +X from its exit plane)."""
    bx, bz = D.BELL['p']
    axis_y = prof['axis_y']
    for d, r in prof['saddles']:
        top = axis_y - r - 0.05
        P.box((2.4, top - 0.4, 6.0), at=(bx + d, 0.0 + (top - 0.4) / 2, bz), mat='concrete', bevel=0.06)
        P.box((2.6, 0.4, 6.4), at=(bx + d, top - 0.2, bz), mat='timber', bevel=0.04)
        P.box((2.6, 0.5, 0.5), at=(bx + d, top + 0.2, bz + 3.2), mat='amber', bevel=0.03)
        P.box((2.6, 0.5, 0.5), at=(bx + d, top + 0.2, bz - 3.2), mat='amber', bevel=0.03)


def rails(P):
    """Gantry rails (x = +-span/2) and the crane runway (x = CRANE_X +- 6) on concrete beams, end buffers."""
    hx = D.GANTRY['span'] / 2
    runs = [(sx * hx, D.GANTRY_RAIL_Z) for sx in (-1, 1)] + [(D.CRANE_X + dx, D.CRANE_RAIL_Z) for dx in (-6.0, 6.0)]
    for x, (z0, z1) in runs:
        L = z1 - z0
        P.box((2.4, 0.3, L), at=(x, 0.0, (z0 + z1) / 2), mat='concrete', bevel=0.04)
        P.box((0.32, 0.28, L - 0.4), at=(x, 0.29, (z0 + z1) / 2), mat='galv', bevel=0.02)
        P.box((0.6, 0.08, L - 0.4), at=(x, 0.17, (z0 + z1) / 2), mat='galv', bevel=0.0)
        for z, s in ((z0 + 0.8, 1), (z1 - 0.8, -1)):
            P.box((2.0, 1.6, 1.4), at=(x, 0.8, z), mat='charcoal', bevel=0.06)
            P.box((2.1, 0.5, 1.5), at=(x, 1.35, z), mat='amber', bevel=0.03)


def bell_profile():
    """Outer radius of the kit bell-XL along its axis (from the GLB), times the placement scale."""
    import subprocess
    tmp = os.path.join(os.environ.get('YARD_SCRATCH', '/tmp/cqs-yard'), 'bell')
    os.makedirs(tmp, exist_ok=True)
    dst = os.path.join(tmp, 'bell-XL.glb')
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'blender', 'assemble_decode.mjs'), os.path.join(ROOT, 'assets', 'parts-blender', 'bell-XL.glb'), dst], check=True, cwd=ROOT)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=dst)
    obs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    co = np.concatenate([np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]) for o in obs])
    for o in [o for o in bpy.data.objects if o not in before]:
        bpy.data.objects.remove(o)
    g = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1) * D.BELL['scale']  # part frame (exit plane z = 0, body +z)
    r = np.hypot(g[:, 0], g[:, 1])
    rmax = float(r.max())
    zlen = float(g[:, 2].max())
    def r_at(z):
        sel = np.abs(g[:, 2] - z) < 0.6
        return float(r[sel].max()) if sel.any() else rmax
    axis_y = rmax + 0.9
    saddles = [(d, r_at(d)) for d in (2.2, zlen * 0.62)]
    print('[yard] bell: rmax %.2f, length %.2f, saddles %s' % (rmax, zlen, saddles), flush=True)
    return {'axis_y': axis_y, 'rmax': rmax, 'length': zlen, 'saddles': saddles}


# --------------------------------------------------------------------------------------------
# ground (tiled concrete, painted lines)
# --------------------------------------------------------------------------------------------
def concrete_texture(path, n=1024, tile=24.0, slab=8.0, seed=3):
    rng = np.random.default_rng(seed)
    px = n / tile
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    def vnoise(cell, amp):
        k = max(1, int(round(n / (cell * px))))
        g = rng.normal(0, 1, (k + 1, k + 1)).astype(np.float32)
        g[-1, :] = g[0, :]; g[:, -1] = g[:, 0]
        u, v = x / n * k, y / n * k
        i, j = u.astype(int), v.astype(int)
        fu, fv = u - i, v - j
        fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
        a = g[j, i] * (1 - fu) + g[j, i + 1] * fu
        b = g[j + 1, i] * (1 - fu) + g[j + 1, i + 1] * fu
        return (a * (1 - fv) + b * fv) * amp
    base = 0.46 + vnoise(6.0, 0.025) + vnoise(1.5, 0.018) + vnoise(0.4, 0.012)
    # per-slab tone
    ns = int(round(tile / slab))
    tone = rng.normal(0, 0.012, (ns, ns)).astype(np.float32)
    si, sj = (x / (slab * px)).astype(int) % ns, (y / (slab * px)).astype(int) % ns
    base += tone[sj, si]
    # stains (oil, tyre grime): soft dark blotches
    st = vnoise(3.0, 1.0)
    base -= np.clip(st - 1.2, 0, None) * 0.06
    # joints: 3 cm dark saw cuts with a 10 cm grime halo
    jx = np.minimum((x % (slab * px)), slab * px - (x % (slab * px))) / px
    jy = np.minimum((y % (slab * px)), slab * px - (y % (slab * px))) / px
    j = np.minimum(jx, jy)
    base -= 0.16 * (j < 0.03) + 0.04 * np.clip(1 - j / 0.12, 0, 1)
    img = np.clip(base, 0, 1)
    from PIL import Image
    Image.fromarray((np.stack([img * 0.98, img * 0.99, img], -1) * 255).astype(np.uint8)).save(path)
    return path


def flat_material(name, rgb, rough=0.7, image=None, factor=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    b = t.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    if image:
        tex = t.nodes.new('ShaderNodeTexImage')
        tex.image = image
        if factor is not None:
            mix = t.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            t.links.new(tex.outputs['Color'], mix.inputs['A'])
            mix.inputs['B'].default_value = (*factor, 1.0)
            t.links.new(mix.outputs['Result'], b.inputs['Base Color'])
        else:
            t.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*rgb, 1.0)
    return m


def ground(workdir):
    img_path = concrete_texture(os.path.join(workdir, 'yard-concrete.png'))
    img = bpy.data.images.load(img_path)
    img.colorspace_settings.name = 'sRGB'
    img.pack()
    mats = {
        'yardGround': flat_material('yardGround', None, 0.92, img, (0.27, 0.28, 0.30)),
        'berthFloor': flat_material('berthFloor', None, 0.9, img, (0.20, 0.205, 0.215)),
        'lineAmber': flat_material('lineAmber', (0.62, 0.24, 0.02), 0.65),
        'lineWhite': flat_material('lineWhite', (0.52, 0.52, 0.50), 0.65),
    }
    order = list(mats)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')

    def slab(x0, x1, z0, z1, y0, y1, mat, ch=0.0):
        pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        bot = [bm.verts.new((x, y0, z)) for x, z in pts]
        if ch > 0:
            mid = [bm.verts.new((x + (ch if x == x0 else -ch) * 0, y1 - ch, z)) for x, z in pts]
            top = [bm.verts.new((x + (ch if x == x0 else -ch), y1, z + (ch if z == z0 else -ch))) for x, z in pts]
            rings = [bot, mid, top]
        else:
            rings = [bot, [bm.verts.new((x, y1, z)) for x, z in pts]]
        fs = []
        for r0, r1 in zip(rings[:-1], rings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                fs.append(bm.faces.new((r0[i], r0[j], r1[j], r1[i])))
        fs.append(bm.faces.new(list(reversed(rings[-1]))[::-1]))
        fs.append(bm.faces.new(list(reversed(bot))))
        for f in fs:
            f.material_index = order.index(mat)
        return fs

    S, B = D.SLAB, D.BERTH
    slab(S['x'][0], S['x'][1], S['z'][0], S['z'][1], -S['depth'], 0.0, 'yardGround', ch=0.5)
    slab(-B['x'], B['x'], B['z'][0], B['z'][1], -0.05, 0.01, 'berthFloor')
    lw = 0.35
    lines = []
    # amber berth edges with corner hazard blocks, amber rail-zone lines, white lanes
    for sx in (-1, 1):
        lines.append(('lineAmber', sx * (B['x'] - 0.6), B['z'], lw))
        for dx in (-3.0, 3.0):
            lines.append(('lineAmber', sx * (D.GANTRY['span'] / 2) + dx, (D.GANTRY_RAIL_Z[0] + 2, D.GANTRY_RAIL_Z[1] - 2), 0.22))
        lines.append(('lineWhite', sx * 56.0, (-136.0, 136.0), 0.25))
    for dx in (-10.0, 10.0):
        lines.append(('lineAmber', D.CRANE_X + dx, (D.CRANE_RAIL_Z[0] + 2, D.CRANE_RAIL_Z[1] - 2), 0.22))
    for sx in (-1, 1):
        lines.append(('lineWhite', sx * 82.0, (-136.0, 136.0), 0.25))
    for mat, x, (z0, z1), w in lines:
        # dashed: 6 m dashes, 3 m gaps (rail zones), berth edges solid
        dash = mat == 'lineAmber' and abs(abs(x) - (B['x'] - 0.6)) > 0.01
        z = z0
        while z < z1 - 0.5:
            ze = min(z1, z + (6.0 if dash else z1 - z0))
            slab(x - w / 2, x + w / 2, z, ze, 0.0, 0.02, mat)
            z = ze + (3.0 if dash else 0.0)
    # berth end bars (amber / white chevrons)
    for ez in (B['z'][0] + 0.6, B['z'][1] - 0.6):
        for k in range(16):
            x0 = -B['x'] + k * (2 * B['x'] / 16)
            slab(x0 + 0.3, x0 + 2 * B['x'] / 16 - 0.3, ez - 0.6, ez + 0.6, 0.0, 0.02, 'lineAmber' if k % 2 == 0 else 'lineWhite')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('ground')
    bm.to_mesh(me)
    bm.free()
    for m in mats.values():
        me.materials.append(m)
    # planar UVs (x, z) / 24 m on every face (side faces stretch: they are the plinth edge)
    uvl = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (v.x / 24.0, v.z / 24.0 + v.y / 24.0)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new('ground', me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# --------------------------------------------------------------------------------------------
def anchor_world(part, local, at, along=(1, 0, 0)):
    """A yard-kit part's anchor (part frame) -> yard frame for a +Y placement at `at` with +X along `along`."""
    a = V(along); a.y = 0; a.normalize()
    y = V((0, 1, 0)); z = a.cross(y)
    p = V(local)
    return tuple(V(at) + a * p.x + y * p.y + z * p.z)


def main():
    argv = sys.argv[1:]
    work = os.path.abspath(argv[0])
    tex = int(argv[argv.index('--tex') + 1]) if '--tex' in argv else 4096
    threads = int(argv[argv.index('--threads') + 1]) if '--threads' in argv else 4
    samples = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 8
    os.makedirs(work, exist_ok=True)
    lib.reset_scene(threads)
    prof = bell_profile()
    lib.reset_scene(threads)
    lib.BAKE.clear()
    lib.BAKE.update({'ao': 2.0, 'curv': 0.05, 'panel': (3.0, 2.0, 3.0)})
    P = lib.Part('yard')
    frames(P)
    keel_and_stringers(P)
    g = YARD_KIT['gantry']['anchors']['hook']
    module_and_rig(P, anchor_world('gantry', g, (0, 0, D.GANTRY['z'])))
    ca = next(c for c in D.CRANES if c['part'] == 'crane-A')
    if 'crane-A' in YARD_KIT:
        crane_load(P, anchor_world('crane-A', YARD_KIT['crane-A']['anchors']['hook'], (D.CRANE_X, 0, ca['z'])))
    else:
        print('[yard] WARNING: no crane-A in parts-yard/parts.json (run yard_kit.py first): no crane load', flush=True)
    bell_cradle(P, prof)
    rails(P)
    ob = P.finish()
    lib.unwrap(ob)
    t = lib.bake(ob, tex, samples)
    print('[yard] structure tris', lib.tris_of(ob), 'bake %.0fs' % t, flush=True)
    gr = ground(work)
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    gr.select_set(True); ob.select_set(True); vl.objects.active = ob
    bpy.ops.object.join()
    ob = vl.objects.active
    ob.name = 'hull'; ob.data.name = 'hull'
    out = os.path.join(work, 'shipyard-hull.glb')
    lib.export(ob, out)
    json.dump({'bell': prof}, open(os.path.join(work, 'shipyard-hull.json'), 'w'), indent=1)
    print('[yard] wrote', out, 'tris', lib.tris_of(ob), flush=True)


if __name__ == '__main__':
    main()
