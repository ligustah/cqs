"""assemble.py for the destroyer, with the guns protected from the kit decimation (v9).

    <blender-python> tools/blender/hulls/destroyer_assemble.py <spec.json> <out.glb> [assemble.py options]

The spec's fixes decimate the kit parts to a fraction of their triangles (a dozen turrets and 28 point-defence
mounts on a 180k budget). Collapse decimation takes thin round pieces first: v8's 0.26 left the turret barrels
6-8-sided and flat-shaded in close-ups, and the point-defence mounts' barrel bundles collapsed while their clamp
rings survived as small blobs floating in the air. Here (a wrapper, per the shared-code rule: assemble_parts.py
is untouched) each part's connected pieces are sorted before the decimation:
  - keep: kept at full resolution (turret-M: every piece wholly in front of the mantlet face, i.e. the two
    32-sided barrels with their muzzle brakes and collars, plus the rounded mantlet cheeks and front plates;
    pdc: the seven barrel rods);
  - drop: deleted (turret-M: the base discs and ring bolts below the housing, 1.0 m, which the destroyer's own
    seat rings and barbettes replace, the turrets are seated 0.98 x scale into them; pdc: the 4 cm bolts);
  - the rest is decimated at the spec's ratio.
Components are found on welded positions (the glTF import splits vertices at UV seams), so the mesh topology
the decimator sees is unchanged. Blender frame of a part here: x across, -y = height (part +Z), z = part +Y
(along the guns).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import assemble_parts as P  # noqa: E402

# part object name -> (keep(lo, hi), drop(lo, hi)) on a piece's bounding box (Blender frame, see above)
PROTECT = {
    # mantlet face at part y 5.04, barrels to 19.04; the base discs and bolts reach 1.0 m high; also kept: the two
    # rounded mantlet cheeks (0.24 m thick, part y 2.4 .. 5.28: decimated they showed notched, faceted outlines in
    # close-ups) and the mantlet front plates (full width 4.48 m)
    'src_turret-M': (lambda lo, hi: lo.z > 4.95 or (lo.z > 2.3 and hi.z > 5.0 and hi.y - lo.y > 0.5 and (hi.x - lo.x < 0.3 or hi.x - lo.x > 4.4)),
                     lambda lo, hi: lo.y > -1.001),
    # barrel rods: 5-8 cm thick, 1.1 m long, from part y 0.54
    'src_pdc': (lambda lo, hi: lo.z > 0.5 and hi.x - lo.x < 0.1 and hi.z - lo.z > 0.8, lambda lo, hi: max(hi - lo) < 0.06),
}

_decimate = P.decimate


def _components(bm, eps=1e-4):
    """Face index -> component id, faces joined by (welded) shared vertex positions."""
    key = lambda co: (round(co.x / eps), round(co.y / eps), round(co.z / eps))
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in bm.faces:
        ks = [key(v.co) for v in f.verts]
        r0 = find(('f', f.index))
        for k in ks:
            r1 = find(('v', k))
            if r1 != r0:
                parent[r1] = r0
    return {f.index: find(('f', f.index)) for f in bm.faces}


def decimate(obj, ratio):
    rule = PROTECT.get(obj.name)
    if rule is None:
        return _decimate(obj, ratio)
    keep_fn, drop_fn = rule
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    comp = _components(bm)
    lo, hi = {}, {}
    for f in bm.faces:
        c = comp[f.index]
        for v in f.verts:
            a, b = lo.get(c), hi.get(c)
            lo[c] = v.co.copy() if a is None else Vector((min(a.x, v.co.x), min(a.y, v.co.y), min(a.z, v.co.z)))
            hi[c] = v.co.copy() if b is None else Vector((max(b.x, v.co.x), max(b.y, v.co.y), max(b.z, v.co.z)))
    kc = {c for c in lo if keep_fn(lo[c], hi[c])}
    dc = {c for c in lo if c not in kc and drop_fn(lo[c], hi[c])}
    keep = {i for i, c in comp.items() if c in kc}
    drop = {i for i, c in comp.items() if c in dc}
    n_drop = sum(len(bm.faces[i].verts) - 2 for i in drop)
    # the kept pieces as their own object, the dropped ones deleted, the rest decimated, then joined back
    # (both deletions index the faces before either, on the copy and on the original)
    bk = bm.copy()
    bk.faces.index_update()
    bk.faces.ensure_lookup_table()
    bmesh.ops.delete(bk, geom=[f for f in bk.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sorted(keep | drop)], context='FACES')
    n_keep = sum(len(f.verts) - 2 for f in bk.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    me2 = bpy.data.meshes.new(obj.name + '_guns')
    bk.to_mesh(me2)
    bk.free()
    for m in me.materials:
        me2.materials.append(m)
    ob2 = bpy.data.objects.new(obj.name + '_guns', me2)
    ob2.matrix_world = obj.matrix_world
    bpy.context.collection.objects.link(ob2)
    _decimate(obj, ratio)
    n_body = sum(len(p.vertices) - 2 for p in me.polygons)
    with bpy.context.temp_override(active_object=obj, selected_editable_objects=[obj, ob2], selected_objects=[obj, ob2]):
        bpy.ops.object.join()
    print(f'[dassemble] {obj.name}: guns kept at {n_keep} tris, {n_drop} hidden tris dropped, body decimated x{ratio} to {n_body} tris', flush=True)


P.decimate = decimate

import assemble  # noqa: E402

if __name__ == '__main__':
    assemble.main()
