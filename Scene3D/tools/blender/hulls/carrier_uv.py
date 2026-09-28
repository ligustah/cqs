"""UV layout for the carrier hull (tools/blender/hulls/carrier.py).

destroyer_uv's method (per-volume smart projection BEFORE the bevel, one metre per UV unit, one
uniform pack), plus two things a 900 m hull needs:
  1. tiling: smart projection keeps a whole flat deck or ceiling (537 x 242 m) as one island,
     and a few giant islands pack badly (34 % fill). Faces are grouped by a 48 m cell of the
     ship frame (and their density class) and every group is shifted apart in UV, so the pack
     sees ~48 m tiles; the paint is evaluated in the ship frame, so tile borders are invisible
     (the bake's 8 px margin extends each island);
  2. density classes: the texture budget goes where it is seen. Every group is scaled about its
     own UV centre: island facades x1.35, the hangar deck x0.85, the other hangar surfaces
     x0.7, the hangar ceiling and the belly (keel wedge, bottoms) x0.55, everything else x1.
"""
import math

import bmesh
import numpy as np

import destroyer_uv as DU

pre_unwrap = DU.pre_unwrap


def pack(ob, margin=0.0004):
    """destroyer_uv.pack with a FRACTION margin (~1.6 px at 4096, 3.3 px at 8192): the carrier has
    ~46,000 islands, and destroyer_uv's SCALED margin left 85 % of the atlas empty."""
    import bpy
    DU._select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method='FRACTION', margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    a3, a2 = DU._areas(ob.data)
    return {'surface_m2': round(a3, 1), 'uv_fill': round(a2, 3), 'px_per_m_at_4096': round(4096 * math.sqrt(a2 / a3), 1)}


def density_class(c, n):
    """c, n: ship-frame face centre and normal."""
    x, y, z = c
    if abs(x) < 121.5 and -97.5 < y < 0.5 and -277 < z < 419:
        if n[1] > 0.9:
            return 'hdeck', 0.85
        if n[1] < -0.9:
            return 'hceil', 0.55
        return 'hwall', 0.7
    if y < -116.0 or (n[1] < -0.7 and y < -100):
        return 'belly', 0.55
    if y > 25.0 and abs(n[1]) < 0.5:
        return 'island', 1.35
    return 'hull', 1.0


def tile_and_scale(ob, cell=48.0):
    me = ob.data
    if not me.uv_layers or not len(me.polygons):
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    groups = {}
    for f in bm.faces:
        c = f.calc_center_median()
        n = f.normal
        cs = (c.x, c.z, -c.y)            # Blender -> ship frame
        ns = (n.x, n.z, -n.y)
        cls, k = density_class(cs, ns)
        key = (cls, math.floor(cs[0] / cell), math.floor(cs[1] / cell), math.floor(cs[2] / cell))
        groups.setdefault(key, (k, []))[1].append(f)
    for gi, (key, (k, faces)) in enumerate(groups.items()):
        pts = [l[uvl].uv.copy() for f in faces for l in f.loops]
        cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
        # scale about the group's centre, then shift the group far from every other group
        ox, oy = (gi % 64) * 1000.0, (gi // 64) * 1000.0
        for f in faces:
            for l in f.loops:
                u = l[uvl].uv
                l[uvl].uv = ((u.x - cx) * k + ox, (u.y - cy) * k + oy)
    bm.to_mesh(me)
    bm.free()
    me.update()
