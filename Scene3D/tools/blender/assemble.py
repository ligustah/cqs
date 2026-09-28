"""Blender assembly of a ship: a fal base hull plus the shared parts kit, placed at true size.

    python assemble.py <spec.json> <out.glb> [--hull hull.glb] [--rotate x,y,z] [--length m]
                       [--no-optimize] [--no-bake] [--blend out.blend] [--tex 4096] [--threads 2]

(`python` = a Python with Blender as a module, `import bpy`; Blender 5.0 tested.)

The hull is brought into the SHIP FRAME the scene uses (metres, bow +Z, dorsal +Y, port +X,
glTF Y-up) exactly as src/lib/glbship.js does: rotate (three.js XYZ Euler) -> uniform scale so
the bbox length (Z) is `length` -> centre on the bbox. Every placement is then snapped onto it
(BVH ray cast along -n from 8 m outside; misses are dropped and logged) and the parts are
merged per part. The GLB is written in that frame, so the ship module loads it with
rotate [0, 0, 0] and length = the hull length printed in the report (the parts stay inside the
hull's bbox, so the old anchors, engines and lights stay valid; the report flags any part
that would grow the bbox).

Spec (JSON; paths relative to the spec file):
  hull:        { glb, rotate: [x,y,z] deg, length: m | scale: k, centre?: false (keep the GLB origin:
               a hull modelled in the ship frame by tools/blender/hulls/) }
  partsDir:    folder with <part>.glb and parts.json (mount conventions)
  partDefaults:{ <part>: { sink, lift, ... } }   defaults merged into every placement
  fixes:       { <part>: {...} }                 overrides of assemble_parts.DEFAULT_FIXES
  cuts:        [{ box: [[x,y,z],[x,y,z]], mirrorX?, above?: y }]  delete hull faces inside
               the box (baked detail to be replaced, e.g. coarse rails)
  placements:  compose.js format, see assemble_place.py (incl. part 'patch' and per-placement
               `patch` cover plates)
  bake:        { ao: true, res: 2048, distance: 0.6, samples: 24, strength: 1 } contact shadow of
               the parts baked into the hull base colour
Output nodes (glTF): "hull" (the hull mesh, its own material and textures), "parts_<name>" (one
merged mesh per kit part, e.g. parts_door, parts_port; the port also carries the "glass"
material), "parts_patch" (cover plates, material "patch"). A report <out>.json lists counts,
drops, seat warnings, timings, bbox and triangle counts.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402  (bpy first: it makes bmesh / mathutils importable)
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import assemble_frame as F  # noqa: E402
import assemble_parts as P  # noqa: E402
import assemble_place as PL  # noqa: E402


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


def cut_hull(hull, cuts):
    """Delete hull faces whose vertices all lie inside a ship-frame box (baked detail that a kit
    part replaces). Returns the number of faces removed."""
    if not cuts:
        return 0
    me = hull.data
    # keep the hull's split normals (a straightened hull's flat panels and sharp creases) through
    # the bmesh round trip: a corner attribute survives the weld and the delete
    cn = np.empty(len(me.loops) * 3)
    me.corner_normals.foreach_get('vector', cn)
    keep = me.attributes.get('keep_nrm') or me.attributes.new('keep_nrm', 'FLOAT_VECTOR', 'CORNER')
    keep.data.foreach_set('vector', cn)
    bm = bmesh.new()
    bm.from_mesh(me)
    boxes = []  # (lo, hi, mode)
    for c in cuts:
        lo, hi = Vector(c['box'][0]), Vector(c['box'][1])
        mode = c.get('mode', 'all')
        boxes.append((lo, hi, mode))
        if c.get('mirrorX'):
            boxes.append((Vector((-hi.x, lo.y, lo.z)), Vector((-lo.x, hi.y, hi.z)), mode))
    in_box = lambda s, lo, hi: all(lo[k] <= s[k] <= hi[k] for k in range(3))
    # generated meshes come split along their UV seams; weld positions (UVs are per corner, so the
    # seams survive) so the openings left by the cut are closed loops that can be filled
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # mode 'all': faces entirely inside a box; 'any': faces with any corner inside (strips a
    # detail down to the box's lower face, e.g. rail posts down to the deck)
    def doomed(f):
        pts = [F.s_vec(v.co) for v in f.verts]
        return any((all if mode == 'all' else any)(in_box(p, lo, hi) for p in pts) for lo, hi, mode in boxes)
    dead = [f for f in bm.faces if doomed(f)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    # close the openings the cut leaves in the surface below (e.g. where rail feet met the deck);
    # each fill face takes one UV point from a neighbouring face
    grow = [(lo - Vector((0.1, 0.1, 0.1)), hi + Vector((0.1, 0.1, 0.1))) for lo, hi, _m in boxes]
    near = lambda s: any(in_box(s, lo, hi) for lo, hi in grow)
    rim = [e for e in bm.edges if e.is_boundary and all(near(F.s_vec(v.co)) for v in e.verts)]
    if rim:
        filled = bmesh.ops.holes_fill(bm, edges=rim, sides=0)['faces']
        # keep only near-planar fills (a floor under a removed post), never a membrane across a
        # long, twisted opening
        warped = []
        for f in filled:
            f.normal_update()
            c = f.calc_center_median()
            if max(abs((v.co - c).dot(f.normal)) for v in f.verts) > 0.08:
                warped.append(f)
        if warped:
            bmesh.ops.delete(bm, geom=warped, context='FACES_ONLY')
            filled = [f for f in filled if f not in set(warped)]
        print(f'[assemble] cut: {len(dead)} faces removed, {len(rim)} rim edges, {len(filled)} fill faces')
        uv = bm.loops.layers.uv.active
        if uv is not None:
            # one UV point per fill face (a neighbour's), so a fill never spans the atlas
            fset = set(filled)
            for f in filled:
                other = next((ol for l in f.loops for ol in l.vert.link_loops if ol.face not in fset), None)
                if other is not None:
                    for l in f.loops:
                        l[uv].uv = other[uv].uv
        bmesh.ops.recalc_face_normals(bm, faces=filled)
    bm.to_mesh(me)
    bm.free()
    me.update()
    kn = np.empty(len(me.loops) * 3)
    me.attributes['keep_nrm'].data.foreach_get('vector', kn)
    kn = kn.reshape(-1, 3)
    # fill faces (no stored normal) take their face normal
    lp = np.repeat(np.arange(len(me.polygons)), [p.loop_total for p in me.polygons])
    fn = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('normal', fn)
    fn = fn.reshape(-1, 3)
    bad = np.linalg.norm(kn, axis=1) < 0.5
    kn[bad] = fn[lp[bad]]
    me.normals_split_custom_set(kn.tolist())
    me.attributes.remove(me.attributes['keep_nrm'])
    me.update()
    return len(dead)


def feature_frames(f):
    """Oriented box(es) of a spec feature: [(centre, R (cols: right, up, n), half-size)], one per
    side for mirrorX. right = up x n, so a feature reads left to right seen from outside."""
    out = []
    for mir in ([False, True] if f.get('mirrorX') else [False]):
        s = Vector((-1, 1, 1)) if mir else Vector((1, 1, 1))
        m = lambda v: Vector((v[0] * s.x, v[1], v[2]))
        n = m(f['n']).normalized()
        up = m(f.get('up', [0, 1, 0]))
        up = (up - n * up.dot(n)).normalized()
        right = up.cross(n)
        R = Matrix((right, up, n)).transposed()
        w, h, d = f['size']
        out.append((m(f['p']), R, Vector((w / 2, h / 2, d / 2)), mir))
    return out


def flatten_hull(hull, feats):
    """Press a lumpy relief flat: every hull vertex inside a feature's oriented box (spec
    `features` with flatten) moves along the feature normal onto its plane; the corners of the
    faces touching the box take the plane normal. The plane passes through `p` (flatten.plane
    'p', default) or the median height of the hull surface on a band round the box ('ring',
    flatten.ring metres wide, sampled by rays on a 0.2 m grid). Collapsed side walls keep their UVs (zero area, invisible); the
    texture over the pressed area is repainted by tools/blender/hulltex.py (feature `paint`)."""
    if not feats:
        return []
    me = hull.data
    caster = F.HullCaster(hull)
    nv = len(me.vertices)
    co = np.empty(nv * 3); me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    S = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)  # ship frame
    moved = np.zeros(nv, bool)
    target_n = {}
    rep = []
    for f in feats:
        cfg = f['flatten'] if isinstance(f['flatten'], dict) else {}
        for c, R, half, mir in feature_frames(f):
            Rn = np.array(R)
            L = (S - np.array(c)) @ Rn  # local (right, up, n)
            inside = np.all(np.abs(L) <= np.array(half), 1)
            if cfg.get('plane', 'p') == 'ring':
                # the hull surface height on a band round the box, from a 0.2 m grid of rays (area
                # weighted: thin seams and small lumps do not move the median)
                r = cfg.get('ring', 0.6)
                hs = []
                for gu in np.arange(-half.x - r, half.x + r + 1e-6, 0.2):
                    for gv in np.arange(-half.y - r, half.y + r + 1e-6, 0.2):
                        if abs(gu) <= half.x and abs(gv) <= half.y:
                            continue
                        o = c + R.col[0] * gu + R.col[1] * gv + R.col[2] * (half.z + 2)
                        hit = caster.cast(o, -R.col[2], 2 * half.z + 2)
                        if hit is not None:
                            hs.append(half.z + 2 - hit[3])
                off = float(np.median(hs)) if len(hs) >= 5 else 0.0
            else:
                off = float(cfg.get('offset', 0.0))
            dz = off - L[inside, 2]
            lim = cfg.get('maxMove', half.z)
            ok = np.abs(dz) <= lim
            idx = np.where(inside)[0][ok]
            S[idx] += np.outer(dz[ok], Rn[:, 2])
            moved[idx] = True
            nn = Vector(Rn[:, 2])
            for i in idx.tolist():
                target_n[i] = nn
            rep.append({'id': f.get('id'), 'mirror': mir, 'verts': int(len(idx)), 'plane_offset': round(off, 3),
                        'max_move': round(float(np.abs(dz[ok]).max()) if ok.any() else 0.0, 3), 'skipped': int((~ok).sum())})
    if moved.any():
        B = np.stack([S[:, 0], -S[:, 2], S[:, 1]], 1)
        me.vertices.foreach_set('co', B.ravel())
        me.update()
        # corner normals: a moved vertex lies on its feature plane now; its corners on faces that
        # face the same way (the pressed area and the flat hull round it) take the plane normal
        ln = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', ln)
        ln = ln.reshape(-1, 3)
        lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
        lp = np.repeat(np.arange(len(me.polygons)), [p.loop_total for p in me.polygons])
        fn = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('normal', fn)
        fn = fn.reshape(-1, 3)
        for li in np.where(moved[lv])[0].tolist():
            nn = target_n[int(lv[li])]
            b = np.array((nn.x, -nn.z, nn.y))
            if fn[lp[li]] @ b > 0.87:  # within 30 degrees
                ln[li] = b
        me.normals_split_custom_set(ln.tolist())
        me.update()
    print(f'[assemble] flatten: {rep}')
    return rep


def main():
    t0 = time.time()
    no_opt = has('--no-optimize')
    no_bake = has('--no-bake')
    blend = arg('--blend')
    tex = arg('--tex', 4096, int)
    threads = arg('--threads', 2, int)
    hull_arg = arg('--hull')
    rotate_arg = arg('--rotate')
    length_arg = arg('--length', None, float)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    spec_path, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    spec = json.load(open(spec_path))
    base = os.path.dirname(spec_path)
    rel = lambda p: p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))
    # command-line hull override (e.g. a straightened or regenerated hull; paths relative to cwd)
    if hull_arg:
        spec['hull'] = {**spec['hull'], 'glb': os.path.abspath(hull_arg)}
    if rotate_arg is not None:
        spec['hull']['rotate'] = [float(v) for v in rotate_arg.split(',')]
    if length_arg is not None:
        spec['hull']['length'] = length_arg
        spec['hull'].pop('scale', None)
    tmp = os.path.join(os.path.dirname(out), '.assemble-tmp')
    os.makedirs(tmp, exist_ok=True)
    report = {'spec': spec_path, 'out': out, 'placed': {}, 'dropped': [], 'seat': [], 'timings': {}}
    tick = lambda k, t=[time.time()]: (report['timings'].__setitem__(k, round(time.time() - t[0], 2)), t.__setitem__(0, time.time()))

    F.reset()
    hs = spec['hull']
    hull, hinfo = F.load_hull(rel(hs['glb']), rotate=hs.get('rotate', [0, 0, 0]), length=hs.get('length'),
                              scale=hs.get('scale'), tmpdir=tmp, centre=hs.get('centre', True))
    report['hull'] = hinfo
    report['cut_faces'] = cut_hull(hull, spec.get('cuts'))
    report['flatten'] = flatten_hull(hull, [f for f in spec.get('features', []) if f.get('flatten')])
    caster = F.HullCaster(hull)
    tick('hull')

    # parts kits: partsDir (default kit) plus named kits (spec "kits": {"fal": dir}); a part name
    # "<kit>:<file>" (e.g. "fal:dome") comes from that kit, a bare name from the default one
    kits = {'': rel(spec.get('partsDir', '../../assets/parts'))}
    kits.update({k: rel(v) for k, v in (spec.get('kits') or {}).items()})
    manifests = {k: P.load_manifest(d) for k, d in kits.items()}
    placements = PL.expand(spec.get('placements', []))
    names = sorted({q['part'] for q in placements if q['part'] != 'patch'})

    def load(n):
        kit, _, file = n.rpartition(':')
        return P.load_part(n, kits[kit], manifests[kit], tmp, spec.get('fixes', {}), file=file)
    parts = {n: load(n) for n in names}
    tick('parts')

    defaults = spec.get('partDefaults', {})
    hull_tex = P.hull_texture(hull)
    patch_cfg = spec.get('patchTexture', {})
    atlas = P.PatchAtlas(**{k: patch_cfg[k] for k in ('density', 'cap', 'tile', 'tone') if k in patch_cfg})
    seat_cfg = spec.get('seat', {})
    placements = [{**defaults.get(q['part'], {}), **q} for q in placements]
    tag_of = lambda q: f"{q.get('id') or q['part']} @{[round(v, 2) for v in q['p']]}"

    # pass 1: cover plates (standalone 'patch' placements and the `patch` of any placement), fitted
    # to the hull under their whole footprint so no old detail pokes through
    patches = []  # (size, depth, PM, colour index)
    for q in placements:
        cover = q.get('patch') if q['part'] != 'patch' else q
        if not cover:
            continue
        hit = caster.cast(q['p'] + q['n'] * 8, -q['n'], 8 + q.get('reach', 6))
        if hit is None:
            report['dropped'].append(tag_of(q) + ' (patch: no hull)')
            continue
        n = q['n']
        R = PL.basis_z(n, q['up'], q.get('rot', 0) or 0)
        c = hit[0]
        if cover is not q and cover.get('offset'):
            dx, dy = cover['offset']
            c = c + R.col[0] * (-dx if q.get('mirrored') else dx) + R.col[1] * dy
        w, h = cover['size']
        fit = PL.fit_plate(caster, c, R, w, h)
        if fit is None:
            report['dropped'].append(tag_of(q) + ' (patch: footprint misses the hull)')
            continue
        hmin, hmax = fit
        proud = cover.get('proud', 0.03)
        front = hmax + proud
        depth = min(max(cover.get('depth', 0.3), front - hmin + 0.03), cover.get('maxDepth', 1.2))
        if hmax - hmin > cover.get('maxRelief', 0.6):
            report['seat'].append({'id': tag_of(q) + ' (patch)', 'relief': round(hmax - hmin, 3)})
        PM = R.to_4x4()
        PM.translation = c + n * (front - depth)
        col = cover.get('color', 'sample')
        if col == 'sample':
            col = P.sample_hull_color(caster, hull_tex, c, R.col[0], R.col[1], n, w, h)
        # the plate's front face in the ship frame (for its plating tone)
        FM = PM.copy()
        FM.translation = PM.translation + n * depth
        patches.append(((w, h), depth, cover.get('chamfer', 0.03), PM, atlas.add(w, h, FM, col)))
    plates = PL.PlateCaster(patches) if patches else None
    both = PL.MultiCaster([caster] + ([plates] if plates else []))

    # pass 2: parts, snapped onto the hull or the plate in front of it
    by_part = {}
    for q in placements:
        name = q['part']
        if name == 'patch':
            continue
        mount = parts[name].mount
        sink = q.get('sink', 0.0)
        s = PL.snap(both, q, sink)
        tag = tag_of(q)
        if s is None:
            report['dropped'].append(tag)
            continue
        pm, n, hit = s
        M = PL.matrix({**q, 'n': n}, mount, pm, n)
        seat = {**seat_cfg, **(q.get('seat') or {})}
        if seat.get('check', True):
            gap, bury = PL.seat_check(both, M, mount, parts[name].bbox, sink)
            bad = gap > seat.get('maxGap', 0.12) or bury > seat.get('maxBury', 0.3)
            if bad or gap > 0.06 or bury > 0.15:
                report['seat'].append({'id': tag, 'gap': round(gap, 3), 'bury': round(bury, 3), 'dropped': bool(bad and seat.get('drop', True))})
            if bad and seat.get('drop', True):
                report['dropped'].append(tag + ' (seat)')
                continue
        by_part.setdefault(name, []).append((M, q.get('mirrored', False)))
    report['placed'] = {k: len(v) for k, v in by_part.items()}
    report['placed']['patch'] = len(patches)
    tick('place')

    # --- merge instances per part -----------------------------------------------------------
    col = bpy.context.collection
    merged = []
    for name, inst in by_part.items():
        objs = []
        for M, mirrored in inst:
            src = parts[name].mirror if mirrored else parts[name].mesh
            o = bpy.data.objects.new(f'{name}_i', src.data)
            o.matrix_world = F.b_mat(M)
            col.objects.link(o)
            objs.append(o)
        merged.append(F.join(objs, f"parts_{name.replace(':', '-')}"))
    for p in parts.values():
        bpy.data.objects.remove(p.mesh)
        bpy.data.objects.remove(p.mirror)
    if patches:
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        for (w, h), depth, chamfer, PM, ci in patches:
            nf0 = len(bm.faces)
            pb = P.patch_bmesh(w, h, depth, chamfer)
            # UVs from the plate's own (x, y) (part frame x = Blender x, part y = Blender z)
            puv = pb.loops.layers.uv.new('UVMap')
            for f in pb.faces:
                for l in f.loops:
                    l[puv].uv = atlas.uv(ci, l.vert.co.x, l.vert.co.z)
            pb.transform(F.b_mat(PM))
            me = bpy.data.meshes.new('tmp')
            pb.to_mesh(me)
            pb.free()
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new('parts_patch')
        bm.to_mesh(me)
        bm.free()
        me.materials.append(atlas.material(tmp))
        po = bpy.data.objects.new('parts_patch', me)
        col.objects.link(po)
        P.harden(po)
        merged.append(po)
    tick('merge')

    # --- contact shadow bake ----------------------------------------------------------------
    bake = spec.get('bake', {})
    if bake.get('ao') and not no_bake:
        import assemble_bake as B
        report['bake'] = B.bake_contact(hull, merged, bake, threads=threads, tmpdir=tmp)
        tick('bake')

    # --- report: envelope and triangles ---------------------------------------------------------
    lo, hi = F.vert_box(hull)
    alo, ahi = Vector(lo), Vector(hi)
    for o in merged:
        a, b = F.vert_box(o)
        alo = Vector(map(min, alo, a)); ahi = Vector(map(max, ahi, b))
    report['bbox_hull'] = [list(lo), list(hi)]
    report['bbox_assembled'] = [list(alo), list(ahi)]
    grow = max(max(lo[k] - alo[k], ahi[k] - hi[k]) for k in range(3))
    report['bbox_growth_m'] = round(grow, 3)
    report['length'] = round(ahi.z - alo.z, 4)
    tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    report['tris'] = {'hull': tris(hull), **{o.name: tris(o) for o in merged}}
    report['tris']['total'] = sum(report['tris'].values())

    # --- export -----------------------------------------------------------------------------
    raw = os.path.join(tmp, os.path.basename(out).replace('.glb', '.raw.glb'))
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
    bpy.ops.export_scene.gltf(filepath=raw, export_format='GLB', export_yup=True, export_apply=False,
                              export_normals=True, export_tangents=False, export_texcoords=True,
                              export_materials='EXPORT', export_image_format='AUTO', export_cameras=False,
                              export_lights=False, export_extras=False, use_selection=False)
    tick('export')
    if no_opt:
        os.replace(raw, out)
    else:
        subprocess.run(['node', os.path.join(F.SCENE3D, 'tools/optimize-glb.mjs'), raw, out,
                        '--tris', '100000000', '--tex', str(tex)], check=True, cwd=F.SCENE3D)
        tick('optimize')
    report['bytes'] = os.path.getsize(out)
    report['timings']['total'] = round(time.time() - t0, 2)
    json.dump(report, open(out.replace('.glb', '.json'), 'w'), indent=1)
    print(json.dumps({k: report[k] for k in ('placed', 'dropped', 'seat', 'timings', 'bytes', 'tris', 'length', 'bbox_growth_m', 'cut_faces')}, indent=1))


if __name__ == '__main__':
    main()
