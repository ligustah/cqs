"""Remodel a colony component: its fal / Tripo blueprint -> clean parametric hard-surface geometry, baked and painted in
texture space, installed under the SAME name and anchor in assets/parts-colony/ (README-colony.md, "Component remodel").

    PY=<python with bpy 5.x, numpy, pillow>
    $PY tools/blender/buildings/remodel.py <name> [<name> ...] [--tex 2048|4096] [--samples 24] [--work <dir>] [--dry]

For each part (ckit.REMODELS[name] = (builder, params, texture size, about)):
  R1 model     builder(B, params) on a bkit.Build in the part frame (metres, +Y up, footprint centre at the origin on
               y = 0, front +Z); lights and kit placements land in B.R
  R2 finish    lib.Part: per batch an angle-limited bevel (2-6 cm chamfers, harden normals) and face-area weighted
               normals, joined; one material slot per paint zone (bkit / ckit material names)
  R3 bake      smart UV at one texel density (packed), Cycles EMIT bakes of part-frame position, true normal, zone, AO
               (1.2 m) and curvature (hulls/common.bake_maps)
  R4 paint     cpaint.paint: kit colours + plating seams, bolts, corrugation, PATINA tone, AO grime, rust, edge wear,
               emissive (hot, lamps); base colour + ORM + normal (+ emissive)
  R5 install   one glTF material 'colony_<name>' (the runtime's colony_* key), GLB (WebP textures) at
               assets/parts-colony/<name>.glb; parts.json keeps the fal jobs and the source image and records
               'remodel' (builder, about, texture, px/m, times, paint check), the bbox, tris, and the part's 'lights' and
               'placements' in the part frame (bkit.component() adds them to the building's lights, transformed)
--dry builds R1-R2 only and prints tris and bbox.
"""
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.path.dirname(HERE)
SCENE3D = os.path.abspath(os.path.join(BLENDER, '..', '..'))
REPO = os.path.abspath(os.path.join(SCENE3D, '..'))
OUT = os.path.join(SCENE3D, 'assets', 'parts-colony')
sys.path.insert(0, BLENDER)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BLENDER, 'hulls'))

import bpy  # noqa: E402,F401
import numpy as np  # noqa: E402

import lib  # noqa: E402
import bkit as K  # noqa: E402
import ckit  # noqa: E402
import cpaint  # noqa: E402
import common as HC  # noqa: E402  (hulls/common.py: bakes, UV report, final material)


def arg(flag, default=None, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return cast(v)
    return default


def has(flag):
    if flag in sys.argv:
        sys.argv.remove(flag)
        return True
    return False


# UV texel weight per paint zone (linear): light paint and plated shells keep the full density; dark structure (frames,
# grating, lacing, rails), glass and interiors get less (they carry little texture detail and are most of the surface of
# a lattice-heavy part: the furnace's frame and decks were 70 % of its 16,000 m2)
UV_WEIGHT = {'frame': 0.45, 'grate': 0.35, 'pipeDark': 0.6, 'pipe': 0.5, 'louvre': 0.4, 'interior': 0.25, 'soot': 0.4,
             'glassW': 0.4, 'lamp': 0.5, 'refractory': 0.6, 'hot': 0.5, 'concrete2': 0.75, 'amber': 0.8, 'frame2': 0.85,
             'roof': 0.6, 'rust': 0.8}


def unwrap(ob, margin, weights=UV_WEIGHT):
    """Smart UV (islands at one scale), islands of low-weight zones scaled down about their centre, then packed
    (uniform scale, so the weights hold). Returns {zone: px per metre at size 1} and (surface, uv area)."""
    import bmesh
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=55 * lib.DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    names = [s.material.name for s in ob.material_slots]
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f1, f2 = e.link_faces
        l1 = [l for l in f1.loops if l.edge == e][0]
        l2 = [l for l in f2.loops if l.edge == e][0]
        # shared edge with matching UVs on both sides (l1 runs v0 -> v1, l2 the other way)
        a1, b1 = l1[uvl].uv, l1.link_loop_next[uvl].uv
        a2, b2 = l2.link_loop_next[uvl].uv, l2[uvl].uv
        if (a1 - a2).length < 1e-5 and (b1 - b2).length < 1e-5:
            ra, rb = find(f1.index), find(f2.index)
            if ra != rb:
                parent[ra] = rb
    isl = {}
    for f in bm.faces:
        isl.setdefault(find(f.index), []).append(f)
    for fs in isl.values():
        w = weights.get(names[fs[0].material_index], 1.0)
        if w >= 0.999:
            continue
        pts = [l[uvl].uv.copy() for f in fs for l in f.loops]
        cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
        for f in fs:
            for l in f.loops:
                l[uvl].uv = ((l[uvl].uv.x - cx) * w + cx, (l[uvl].uv.y - cy) * w + cy)
    bm.to_mesh(me); bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    a3, a2 = {}, {}
    for p in me.polygons:
        q = uv[list(p.loop_indices)]
        z = names[p.material_index]
        a3[z] = a3.get(z, 0.0) + p.area
        a2[z] = a2.get(z, 0.0) + abs(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])) / 2
    ppm = {z: (a2[z] / a3[z]) ** 0.5 if a3[z] > 0 else 0.0 for z in a3}
    return ppm, (sum(a3.values()), sum(a2.values()))


def gltf_occlusion(mt):
    """Route the ORM's red channel (the baked AO) to the glTF exporter's occlusion slot (the 'glTF Material Output'
    custom group the Blender glTF add-on reads); the exporter then writes occlusionTexture on the same ORM image."""
    g = bpy.data.node_groups.get('glTF Material Output')
    if g is None:
        g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    t = mt.node_tree
    sep = next(n for n in t.nodes if n.bl_idname == 'ShaderNodeSeparateColor')
    gn = t.nodes.new('ShaderNodeGroup')
    gn.node_tree = g
    t.links.new(sep.outputs['Red'], gn.inputs['Occlusion'])


def final_material(ob, name, paths):
    HC.set_final_material(ob, paths['base'], paths['orm'], name=name, normal_png=paths['normal'])
    mt = ob.data.materials[0]
    gltf_occlusion(mt)
    if paths.get('emit'):
        t = mt.node_tree
        bsdf = t.nodes['Principled BSDF']
        ie = bpy.data.images.load(paths['emit']); ie.colorspace_settings.name = 'sRGB'
        te = t.nodes.new('ShaderNodeTexImage'); te.image = ie
        t.links.new(te.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    return mt


def export(ob, path):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    ob.rotation_euler = (90 * lib.DEG, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT',
                              export_animations=False, export_extras=False, export_image_format='WEBP', export_image_quality=90)


def xform_lights(R):
    return {'lights': R.light_data(), 'placements': R.placements}


def build(name, tex, samples, work, dry=False):
    builder, params, tex0, about = ckit.REMODELS[name]
    tex = tex or tex0
    t0 = time.time()
    lib.reset_scene(4)
    B = K.Build(name)
    spec = builder(B, params) or {}
    P = B.part()
    ob = P.finish()
    tris = lib.tris_of(ob)
    co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    lo, hi = co.min(0), co.max(0)
    t1 = time.time()
    zones = [s.material.name for s in ob.material_slots]
    print(f'[remodel] {name}: {tris} tris, bbox {np.round(lo, 2).tolist()} .. {np.round(hi, 2).tolist()}, zones {zones}, {t1 - t0:.0f}s', flush=True)
    if dry:
        return {'tris': tris, 'bbox': [lo.tolist(), hi.tolist()]}
    ppm, (a3, a2) = unwrap(ob, margin=max(0.0005, 1.5 / tex))
    ppm = {z: v * tex for z, v in ppm.items()}
    px_per_m = max(ppm.get(z, 0.0) for z in ppm)
    t2 = time.time()
    print(f'[remodel] unwrap {t2 - t1:.0f}s, surface {a3:.0f} m2, uv fill {a2:.2f}, px/m at {tex}: '
          + ', '.join(f'{z} {v:.1f}' for z, v in sorted(ppm.items(), key=lambda kv: -kv[1])), flush=True)
    maps = HC.bake_maps(ob, size=tex, ao_size=tex // 2, ao_samples=samples, ao_dist=1.2, curv_r=0.05, threads=4)
    # hulls/common converts Blender -> ship frame (x, z, -y); the kit authors the part frame directly in Blender (Y up)
    for k in ('pos', 'nrm'):
        a = maps[k]
        maps[k] = np.stack([a[..., 0], -a[..., 2], a[..., 1]], -1)
    t3 = time.time()
    res = cpaint.paint(maps, zones, spec, os.path.join(work, name), [ppm.get(z, px_per_m) for z in zones], lib.MATS)
    del maps
    t4 = time.time()
    print(f'[remodel] bake {t3 - t2:.0f}s, paint {t4 - t3:.0f}s, stats {res["stats"]}', flush=True)
    final_material(ob, f'colony_{name}', res)
    path = os.path.join(OUT, f'{name}.glb')
    export(ob, path)
    t5 = time.time()
    rec = {'tris': tris, 'bbox': {'min': [round(float(v), 3) for v in (lo[0], lo[1], lo[2])],
                                  'max': [round(float(v), 3) for v in (hi[0], hi[1], hi[2])]},
           'tex': tex, 'kb': round(os.path.getsize(path) / 1024), 'about': about,
           'remodel': {'builder': f'ckit.{builder.__name__}', 'script': 'tools/blender/buildings/remodel.py', 'pxPerM': {z: round(v, 1) for z, v in ppm.items()},
                       'surfaceM2': round(a3), 'paint': res['stats'], 'seconds': {'model': round(t1 - t0), 'unwrap': round(t2 - t1),
                                                                                  'bake': round(t3 - t2), 'paint': round(t4 - t3), 'export': round(t5 - t4)},
                       'date': time.strftime('%Y-%m-%d')},
           **xform_lights(B.R)}
    rec['bbox']['size'] = [round(rec['bbox']['max'][i] - rec['bbox']['min'][i], 3) for i in range(3)]
    print(f'[remodel] {name} -> {path} ({rec["kb"]} kB), {t5 - t0:.0f}s total', flush=True)
    return rec


def register(name, rec):
    pj = os.path.join(OUT, 'parts.json')
    d = json.load(open(pj))
    old = d['parts'].get(name, {})
    keep = {k: old[k] for k in ('fal', 'source', 'usedBy', 'mount') if k in old}
    # the blueprint's ingest record stays for the record (and component.py --rebuild skips remodelled parts)
    bp = {k: old[k] for k in ('params', 'albedo', 'tris', 'tex', 'hot', 'bbox') if k in old}
    if 'blueprint' in old:
        bp = old['blueprint']
    new = {'part': name, 'file': f'{name}.glb', **keep, **rec, 'blueprint': {'raw': f'assets/buildings/raw/{name}.glb', **bp}}
    new.setdefault('mount', {'anchor': 'footprint centre at y = 0, front +Z', 'normal': '+Y'})
    d['parts'][name] = new
    json.dump(d, open(pj, 'w'), indent=1)


def main():
    tex = arg('--tex', None, int)
    samples = arg('--samples', 24, int)
    work = arg('--work', os.path.join('/tmp', 'remodel'))
    dry = has('--dry')
    names = sys.argv[1:] or list(ckit.REMODELS)
    os.makedirs(work, exist_ok=True)
    for name in names:
        rec = build(name, tex, samples, work, dry)
        if not dry:
            register(name, rec)


if __name__ == '__main__':
    main()
