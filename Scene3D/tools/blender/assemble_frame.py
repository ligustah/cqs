# Ship-frame helpers for tools/blender/assemble.py.
#
# Two frames meet here:
#   ship frame  = the scene's frame (glTF, Y-up): metres, bow +Z, dorsal +Y, port +X.
#                 Every coordinate in a spec, and every placement, is in this frame.
#   Blender     = Z-up. The glTF importer maps glTF (x, y, z) to Blender (x, -z, y) and the
#                 exporter (export_yup) maps it back, so the exported GLB is in the ship frame.
# All maths in the assembler is done in the ship frame with mathutils; b_mat() / b_vec() convert
# to Blender only where an object or a BVH is touched.
import os
import subprocess
import math
import bpy
from mathutils import Matrix, Vector, Euler
from mathutils.bvhtree import BVHTree

DEG = math.pi / 180
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..'))

# glTF -> Blender basis change
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
CI = C.inverted()


def b_vec(v):
    """ship/glTF point -> Blender point"""
    return Vector((v[0], -v[2], v[1]))


def s_vec(v):
    """Blender point -> ship/glTF point"""
    return Vector((v[0], v[2], -v[1]))


def b_mat(m):
    """ship-frame 4x4 (acting on glTF-frame part coordinates) -> Blender object matrix"""
    return C @ m @ CI


def decode(pairs, tmpdir):
    """Meshopt/quantized GLBs -> plain GLBs Blender can import (node helper). pairs: [(src, name)]"""
    os.makedirs(tmpdir, exist_ok=True)
    args, out = [], {}
    for src, name in pairs:
        dst = os.path.join(tmpdir, f'{name}.glb')
        args += [src, dst]
        out[name] = dst
    subprocess.run(['node', os.path.join(HERE, 'assemble_decode.mjs'), *args], check=True, cwd=SCENE3D)
    return out


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path):
    """Import a GLB; return its mesh objects (world transforms intact)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=False)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'MESH'], new


def join(objs, name):
    """Join mesh objects into one (transforms applied, empties removed)."""
    objs = [o for o in objs if o.type == 'MESH']
    for o in objs:
        o.data = o.data.copy() if o.data.users > 1 else o.data
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        if len(objs) > 1:
            bpy.ops.object.join()
    o = objs[0]
    mw = o.matrix_world.copy()
    o.parent = None
    o.data.transform(mw)
    o.matrix_world = Matrix.Identity(4)
    o.name = name
    o.data.name = name
    return o


def three_euler_matrix(rot_deg):
    """three.js Euler(x, y, z, 'XYZ') as a matrix (= Rx @ Ry @ Rz), glTF frame."""
    x, y, z = (r * DEG for r in rot_deg)
    return Matrix.Rotation(x, 4, 'X') @ Matrix.Rotation(y, 4, 'Y') @ Matrix.Rotation(z, 4, 'Z')


def loose_box(objs, pre):
    """three.js Box3.setFromObject (precise = false): each mesh's local AABB corners through its
    world matrix (here: pre @ glTF node matrix), in the glTF frame."""
    lo = Vector((1e30,) * 3)
    hi = Vector((-1e30,) * 3)
    for o in objs:
        # object's glTF-frame node matrix = CI @ matrix_world @ C ; its local coords in glTF = CI @ co
        mg = pre @ CI @ o.matrix_world @ C
        cs = [CI @ Vector(c) for c in o.bound_box]
        xs = [c.x for c in cs]; ys = [c.y for c in cs]; zs = [c.z for c in cs]
        for cx in (min(xs), max(xs)):
            for cy in (min(ys), max(ys)):
                for cz in (min(zs), max(zs)):
                    p = mg @ Vector((cx, cy, cz))
                    lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
    return lo, hi


def vert_box(obj):
    """Exact ship-frame bbox of an object's vertices (world space)."""
    import numpy as np
    me = obj.data
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(obj.matrix_world)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    ship = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)
    return Vector(ship.min(0)), Vector(ship.max(0))


def load_hull(path, rotate=(0, 0, 0), length=None, scale=None, tmpdir='/tmp', centre=True):
    """Import the hull GLB into the ship frame exactly as glbship.js does:
    rotate (three.js XYZ Euler, degrees) -> uniform scale so the bbox Z is `length` (or `scale`)
    -> centre on the bbox. centre=False keeps the GLB's own origin (a hull modelled in the ship
    frame, tools/blender/hulls/: its kit parts complete the bbox). Returns (hull object, info)."""
    src = decode([(path, 'hull-src')], tmpdir)['hull-src']
    meshes, new = import_glb(src)
    R = three_euler_matrix(rotate)
    lo, hi = loose_box(meshes, R)
    s = scale if scale is not None else (length / (hi.z - lo.z) if length else 1.0)
    S = Matrix.Scale(s, 4)
    lo2, hi2 = loose_box(meshes, S @ R)
    c = (lo2 + hi2) / 2 if centre else Vector((0, 0, 0))
    M = Matrix.Translation(-c) @ S @ R  # glTF frame
    for o in meshes:
        o.matrix_world = b_mat(M) @ o.matrix_world
    bpy.context.view_layer.update()
    hull = join(meshes, 'hull')
    for o in new:
        if o.name in bpy.data.objects and o != hull:
            bpy.data.objects.remove(o)
    lo3, hi3 = vert_box(hull)
    info = {'scale': s, 'centre_raw': list(c / s), 'bbox': [list(lo3), list(hi3)],
            'size': list(hi3 - lo3), 'tris': sum(len(p.vertices) - 2 for p in hull.data.polygons)}
    return hull, info


class HullCaster:
    """BVH ray caster over the hull, in the ship frame."""

    def __init__(self, hull):
        dg = bpy.context.evaluated_depsgraph_get()
        self.obj = hull
        self.bvh = BVHTree.FromObject(hull, dg, epsilon=0.0)
        me = hull.data
        self.me = me
        self.uv = me.uv_layers.active.data if me.uv_layers.active else None
        me.calc_loop_triangles()
        self.tris = me.loop_triangles

    def cast(self, origin, direction, far=1e4):
        """ship-frame ray -> (point, normal, face_index, dist) or None. Normal in ship frame."""
        o = b_vec(origin)
        d = b_vec(direction).normalized()
        p, n, i, dist = self.bvh.ray_cast(o, d, far)
        if p is None:
            return None
        return s_vec(p), s_vec(n).normalized(), i, dist

    def uv_at(self, point_ship, face):
        """UV of the hull at a point on polygon `face` (BVH index = polygon index)."""
        if self.uv is None:
            return None
        from mathutils.geometry import intersect_point_tri, barycentric_transform
        me = self.me
        poly = me.polygons[face]
        p = b_vec(point_ship)
        vs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        uvs = [self.uv[li].uv for li in poly.loop_indices]
        # fan-triangulate and pick the triangle closest to p
        best = None
        for k in range(1, len(vs) - 1):
            a, b, c = vs[0], vs[k], vs[k + 1]
            uva, uvb, uvc = uvs[0], uvs[k], uvs[k + 1]
            q = barycentric_transform(p, a, b, c, uva.to_3d(), uvb.to_3d(), uvc.to_3d())
            if best is None:
                best = q
            if intersect_point_tri(p, a, b, c) is not None:
                best = q
                break
        return (best.x, best.y)
