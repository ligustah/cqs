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
--dry builds R1-R2 only and prints tris and bbox; --preview <out.glb> also exports that model with flat zone colours
(check the geometry with tools/render-glb.mjs before spending a bake).
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
OUT = os.environ.get('REMODEL_OUT') or os.path.join(SCENE3D, 'assets', 'parts-colony')   # v6: REMODEL_OUT for experiments
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


def has_flag(flag):
    # build-time switches from the environment (REMODEL_FLAGS="--no-cull --no-split"), for A/B checks
    return flag in os.environ.get('REMODEL_FLAGS', '').split()


def has(flag):
    if flag in sys.argv:
        sys.argv.remove(flag)
        return True
    return False


# UV texel weight per paint zone (linear): light paint and plated shells keep the full density; dark structure (frames,
# grating, lacing, rails), glass and interiors get less (they carry little texture detail and are most of the surface of
# a lattice-heavy part: the furnace's frame and decks were 70 % of its 16,000 m2)
UV_WEIGHT = {'frame': 0.45, 'grate': 0.35, 'pipeDark': 0.6, 'pipe': 0.5, 'louvre': 0.4, 'interior': 0.25, 'soot': 0.4,
             'glassW': 0.4, 'lamp': 0.5, 'refractory': 0.6, 'hot': 1.0, 'concrete2': 0.75, 'amber': 0.8, 'frame2': 0.85,
             'roof': 0.6, 'rust': 0.8, 'concrete': 0.7}
# v4 r3: thin structure (rails, lacing, rods, rungs, small brackets) is thousands of islands a few texels wide, and each
# paid a 1.5 px margin round it: 86 % of the furnace's 10,900 islands held 9 % of its surface but cost most of the atlas
# (fill 0.37). Islands of these zones under STACK_AREA m2 are now stacked: each zone's tiny islands are normalised into
# one shared square swatch (they overlap; the bake keeps one of them per texel) and packed as one island
# (merge_overlap). At any distance a 10 cm bar shows one painted tone with edge wear, which the swatch still carries.
STACK_ZONES = {'frame', 'frame2', 'grate', 'pipeDark', 'pipe', 'soot', 'refractory', 'rust', 'interior', 'louvre',
               'amber', 'hazard', 'roof'}
STACK_AREA = 2.0
ANGLE = float(os.environ.get('REMODEL_ANGLE', 55))   # smart projection angle limit (degrees)
SHAPE = os.environ.get('REMODEL_SHAPE', 'CONCAVE')       # pack_islands shape method
MERGE = os.environ.get('REMODEL_MERGE', '1') == '1'
STACK_NARROW = 0.12     # any zone: islands narrower than this (m; ribs, trims, rungs) are stacked too
# v5: lamp lenses ARE stacked (one emissive swatch): left as tiny islands, the concave packer dropped them into gaps
# inside the 'frame' swatch, and every rail and brace that samples that swatch glowed orange at 4096
NO_STACK = {'hot', 'glassW'}


CYL = set()             # v5: zones of a surface of revolution about the part's Y axis, unrolled (set per part)
CYL_SECTORS = 24
CYL_BAND = 6.0          # horizontal cuts (m): smaller near-rectangles pack tighter (fill 0.74 -> 0.79)


def _unroll(bm, uvl, names):
    """v5: unroll the side faces of revolved shells (zones in CYL, axis = the part's Y axis) into 30-degree sectors:
    u = arc length at the vertex's own radius, v = height. Smart projection cut the furnace's cones into curved,
    foreshortened bananas that packed at 0.50 fill; the unrolled sectors are near-rectangles at true density."""
    import math as _m
    step = 2 * _m.pi / CYL_SECTORS
    faces = [f for f in bm.faces if names[f.material_index] in CYL and abs(f.normal.y) < 0.7]
    if not faces:
        return
    a3 = sum(f.calc_area() for f in faces)
    a2 = 0.0
    for f in faces:
        q = [l[uvl].uv for l in f.loops]
        a2 += abs(sum(q[i].x * q[i - 1].y - q[i - 1].x * q[i].y for i in range(len(q)))) / 2
    k = (a2 / max(a3, 1e-9)) ** 0.5          # keep the smart projection's UV scale (uv units per metre)
    for f in faces:
        c = f.calc_center_median()
        tc = _m.atan2(c.x, c.z)
        sec = _m.floor((tc + _m.pi) / step)
        t0 = -_m.pi + (sec + 0.5) * step
        band = _m.floor(c.y / CYL_BAND)
        for l in f.loops:
            v = l.vert.co
            r = _m.hypot(v.x, v.z)
            dt = (_m.atan2(v.x, v.z) - t0 + _m.pi) % (2 * _m.pi) - _m.pi
            # sectors parked apart (the pack moves them); radius bands apart too (flanges, drums at other radii)
            l[uvl].uv = (k * (dt * r) + 40.0 * sec * k, k * (v.y + 20.0 * band))
    print(f'[remodel] unrolled {len(faces)} revolved faces of {sorted(CYL)} into {CYL_SECTORS} sectors', flush=True)


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
    bpy.ops.uv.smart_project(angle_limit=ANGLE * lib.DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    names = [s.material.name for s in ob.material_slots]
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    if CYL:
        _unroll(bm, uvl, names)
    def islands():
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
        out = {}
        for f in bm.faces:
            out.setdefault(find(f.index), []).append(f)
        return out
    isl = islands()
    import math as _m

    def uv_area(fs):
        a = 0.0
        for f in fs:
            q = [l[uvl].uv for l in f.loops]
            a += abs(sum(q[i].x * q[i - 1].y - q[i - 1].x * q[i].y for i in range(len(q)))) / 2
        return a
    # the smart projection's UV-per-3D area scale (one scale for every island: area_weight 0, no scale to bounds)
    allf = [fs for fs in isl.values()]
    kuv = sum(uv_area(fs) for fs in allf) / max(1e-9, sum(f.calc_area() for fs in allf for f in fs))
    stacks = {}
    for k, fs in list(isl.items()):
        z = names[fs[0].material_index]
        if z in NO_STACK:
            continue
        uvs = [l[uvl].uv for f in fs for l in f.loops]
        bw = (max(u.x for u in uvs) - min(u.x for u in uvs)) / _m.sqrt(kuv)
        bh = (max(u.y for u in uvs) - min(u.y for u in uvs)) / _m.sqrt(kuv)
        short = min(bw, bh)
        a = sum(f.calc_area() for f in fs)
        # v5: hollow islands (the flat annuli of hoops, lap rings and lips: a 20 m circle of 3 cm ribbon) hold almost no
        # area in a huge box and wrecked the pack (the furnace shell set filled 0.50): stack them too
        hollow = a < 12.0 and a < 0.12 * bw * bh
        if (z in STACK_ZONES and a < STACK_AREA) or short < STACK_NARROW or a < 0.15 or hollow:
            stacks.setdefault(z, []).append(fs)
            del isl[k]
    stacked = {f.index for g in stacks.values() for fs in g for f in fs}
    nst = 0
    for zi, (z, groups) in enumerate(sorted(stacks.items())):
        # one square swatch per zone, a sixth of the zone's stacked area at the zone's weight (they overlap)
        tot = sum(f.calc_area() for fs in groups for f in fs)
        side = _m.sqrt(kuv * tot * weights.get(z, 1.0) ** 2 / 6.0)
        x0 = 2.0 + 10.0 * zi       # parked off the unit square, apart, until the pack moves them in
        for fs in groups:
            uvs = [l[uvl].uv for f in fs for l in f.loops]
            ux0 = min(u.x for u in uvs); ux1 = max(u.x for u in uvs)
            uy0 = min(u.y for u in uvs); uy1 = max(u.y for u in uvs)
            sx = side / max(ux1 - ux0, 1e-6); sy = side / max(uy1 - uy0, 1e-6)
            for f in fs:
                for l in f.loops:
                    u = l[uvl].uv
                    l[uvl].uv = (x0 + (u.x - ux0) * sx, 0.5 + (u.y - uy0) * sy)
            nst += 1
        isl.setdefault(('stack', z), [])
    for fs in isl.values():
        if not fs:
            continue
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
    bpy.ops.uv.pack_islands(udim_source=os.environ.get('REMODEL_UDIM', 'CLOSEST_UDIM'), rotate=True, margin=margin, margin_method=os.environ.get('REMODEL_MARGIN', 'SCALED'), merge_overlap=MERGE, shape_method=SHAPE)
    print(f'[remodel] stacked {nst} tiny islands of {sorted(stacks)} into {len(stacks)} swatches; {len(isl) - len(stacks)} islands packed', flush=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    a3, a2 = {}, {}
    for p in me.polygons:
        if p.index in stacked:      # swatches overlap: their texel density is not a density
            continue
        q = uv[list(p.loop_indices)]
        z = names[p.material_index]
        a3[z] = a3.get(z, 0.0) + p.area
        a2[z] = a2.get(z, 0.0) + abs(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])) / 2
    ppm = {z: (a2[z] / a3[z]) ** 0.5 if a3[z] > 0 else 0.0 for z in a3}
    return ppm, (sum(a3.values()), sum(a2.values()))


def cull_buried(ob):
    """v5: delete faces buried inside other solids (lathe pole caps inside the next station, box ends inside columns,
    hoop inner walls on the shell). They are never seen but took UV space: the v4 furnace atlas spent large discs on
    hidden caps. A face is buried when every sample point (its centre, corners and edge midpoints pulled 5 % in, the
    fan-triangle centroids; lifted 4 mm off the face) sees, along the normal and four directions tilted 35 degrees off it, a BACK face first, i.e. lies inside a
    closed solid. Open or one-sided geometry never reads as inside from every ray, so the test errs toward keeping."""
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    dead = []

    def winding(q, d, self_idx):
        """Solids containing q, counted along the ray q + t d: +1 per back face crossed (leaving a solid), -1 per
        front face (entering one); coincident faces at one hit (stacked solids) are all counted."""
        w, o, seen = 0, q, set()
        for _ in range(48):
            hit, hn, idx, dist = tree.ray_cast(o, d)
            if hit is None:
                return w
            group = {idx} | {j for (_c, _n, j, _d) in tree.find_nearest_range(hit, 0.0006)}
            for j in group - seen:
                if j == self_idx:
                    continue
                dn = bm.faces[j].normal.dot(d)
                if abs(dn) > 0.05:
                    w += 1 if dn > 0 else -1
            seen |= group
            o = hit + d * 0.001
        return w

    for f in bm.faces:
        n = f.normal
        if n.length < 0.5:
            continue
        c = f.calc_center_median()
        t1 = (f.verts[1].co - f.verts[0].co).normalized() if len(f.verts) > 1 else Vector((1, 0, 0))
        t2 = n.cross(t1).normalized()
        dirs = [n] + [(n * 0.82 + d * 0.57).normalized() for d in (t1, -t1, t2, -t2)]
        vs = [v.co for v in f.verts]
        # samples: the centre, the corners and edge midpoints pulled 5 % in, and the centroids of the fan triangles
        # (a big n-gon partly covered, e.g. a plinth top under the leg shoes, must not read as buried)
        pts = [c] + [v + (c - v) * 0.05 for v in vs] + [(vs[i] + vs[i - 1]) / 2 * 0.95 + c * 0.05 for i in range(len(vs))]
        pts += [(vs[0] + vs[i] + vs[i + 1]) / 3 for i in range(1, len(vs) - 1)] if len(vs) > 3 else []
        # faces on the ground facing down (the undersides of plinths, footings, pads) are never seen either
        if n.y < -0.95 and c.y < 0.02:
            dead.append(f)
            continue
        buried = True
        for q in pts:
            q = q + n * 0.004
            for d in dirs:
                if winding(q, d, f.index) <= 0:
                    buried = False
                    break
            if not buried:
                break
        if buried:
            dead.append(f)
    nf = len(bm.faces)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(ob.data); bm.free()
    ob.data.update()
    print(f'[remodel] culled {len(dead)} buried faces of {nf}', flush=True)
    return len(dead)


def split_off(ob, zones, suffix='_2'):
    """v5: a second object with the faces of `zones` (their own texture set), removed from ob."""
    import bmesh
    names = [s.material.name for s in ob.material_slots]
    keep = {i for i, nm in enumerate(names) if nm in zones}
    ob2 = ob.copy(); ob2.data = ob.data.copy(); ob2.name = ob.name + suffix
    bpy.context.collection.objects.link(ob2)
    for o, drop_in in ((ob, True), (ob2, False)):
        bm = bmesh.new(); bm.from_mesh(o.data)
        dead = [f for f in bm.faces if (f.material_index in keep) == drop_in]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(o.data); bm.free()
        o.data.update()
    return ob2


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


def build(name, tex, samples, work, dry=False, preview=None):
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
    if not has_flag('--no-cull'):
        cull_buried(ob)
        tris = lib.tris_of(ob)
    print(f'[remodel] {name}: {tris} tris, bbox {np.round(lo, 2).tolist()} .. {np.round(hi, 2).tolist()}, zones {zones}, {t1 - t0:.0f}s', flush=True)
    if dry:
        if preview:
            # geometry check before any bake: flat zone colours (lib.MATS), exported like the final part (40 s with
            # render-glb.mjs); hot and lamp zones orange
            for s_ in ob.material_slots:
                m = s_.material
                col = (lib.MATS.get(m.name) or ((1.0, 0.0, 1.0),))[0]
                if m.name in ('hot', 'lamp'):
                    col = (1.0, 0.45, 0.1)
                t = m.node_tree
                t.nodes.clear()
                o = t.nodes.new('ShaderNodeOutputMaterial')
                bs = t.nodes.new('ShaderNodeBsdfPrincipled')
                bs.inputs['Base Color'].default_value = (*list(col)[:3], 1)
                bs.inputs['Roughness'].default_value = 0.6
                t.links.new(bs.outputs[0], o.inputs[0])
            export(ob, preview)
            print(f'[remodel] preview -> {preview}', flush=True)
        return {'tris': tris, 'bbox': [lo.tolist(), hi.tolist()]}
    # v5: an optional second texture set (ckit.SPLIT: zones -> their own atlas and material colony_<name>_2), so a
    # hero's light shell gets a full atlas of its own (the furnace shell 34 -> ~75 px/m at 4096); each material keeps
    # the colony sampler count (base, ORM, normal, emissive)
    sets = [(ob, f'colony_{name}', tex, name)]
    # v6: SPLIT may list several sets ([(zones, tex), ...] -> colony_<name>_2, _3, ...): the furnace's dark legs and
    # bosh (frame2) got a third set so they hold at the close-up (28 -> ~60 px/m at 4096)
    cylz = {}
    if name in getattr(ckit, 'SPLIT', {}) and not has_flag('--no-split'):
        spl = ckit.SPLIT[name]
        for k, (zs, tex2) in enumerate(spl if isinstance(spl, list) else [spl]):
            sfx = f'_{k + 2}'
            ob2 = split_off(ob, zs, sfx)
            sets.append((ob2, f'colony_{name}{sfx}', min(tex2, tex), name + sfx))
            cylz[f'colony_{name}{sfx}'] = set(zs)
    ppm_all, a3, a2, stats_all = {}, 0.0, 0.0, {}
    t2 = t3 = t4 = time.time()
    global CYL
    for (o, mname, tx, wname) in sets:
        CYL = cylz.get(mname, set())
        # v6 r10: per-part UV weights (ckit.UV_W[name]) for the main set only: the furnace's main atlas lost its light
        # shell and legs to sets 2 / 3, so its dark structure can take more texels (13 -> ~25 px/m at 4096)
        wts = dict(UV_WEIGHT, **(getattr(ckit, 'UV_W', {}).get(name, {}) if mname == f'colony_{name}' else {}))
        ppm, (a3_, a2_) = unwrap(o, margin=max(0.0005, 1.5 / tx), weights=wts)
        CYL = set()
        ppm = {z: v * tx for z, v in ppm.items()}
        px_per_m = max(ppm.get(z, 0.0) for z in ppm)
        t2 = time.time()
        print(f'[remodel] {mname}: unwrap {t2 - t1:.0f}s, surface {a3_:.0f} m2, uv fill {a2_:.2f}, px/m at {tx}: '
              + ', '.join(f'{z} {v:.1f}' for z, v in sorted(ppm.items(), key=lambda kv: -kv[1])), flush=True)
        maps = HC.bake_maps(o, size=tx, ao_size=tx // 2, ao_samples=samples, ao_dist=1.2, curv_r=0.08, threads=4)
        # hulls/common converts Blender -> ship frame (x, z, -y); the kit authors the part frame directly in Blender (Y up)
        for k in ('pos', 'nrm'):
            a = maps[k]
            maps[k] = np.stack([a[..., 0], -a[..., 2], a[..., 1]], -1)
        t3 = time.time()
        zones_o = [s_.material.name for s_ in o.material_slots]
        res = cpaint.paint(maps, zones_o, spec, os.path.join(work, wname), [ppm.get(z, px_per_m) for z in zones_o], lib.MATS)
        del maps
        t4 = time.time()
        print(f'[remodel] {mname}: bake {t3 - t2:.0f}s, paint {t4 - t3:.0f}s, stats {res["stats"]}', flush=True)
        final_material(o, mname, res)
        for z, v in ppm.items():
            if v > 0:
                ppm_all[z if mname == f'colony_{name}' else f'{z} (set {mname.rsplit("_", 1)[1]})'] = v
        a3 += a3_; a2 += a2_
        stats_all[mname] = res['stats']
        t1 = t4
    if len(sets) > 1:
        vl = bpy.context.view_layer
        for o_ in vl.objects:
            o_.select_set(False)
        for (o, *_r) in sets:
            o.select_set(True)
        vl.objects.active = ob
        bpy.ops.object.join()
    ppm = ppm_all
    res = {'stats': stats_all if len(sets) > 1 else stats_all[f'colony_{name}']}
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
    preview = arg('--preview', None)     # --preview <out.glb>: model only, flat zone colours (implies --dry; one part)
    dry = has('--dry') or bool(preview)
    names = sys.argv[1:] or list(ckit.REMODELS)
    os.makedirs(work, exist_ok=True)
    for name in names:
        rec = build(name, tex, samples, work, dry, preview)
        if not dry:
            register(name, rec)


if __name__ == '__main__':
    main()
