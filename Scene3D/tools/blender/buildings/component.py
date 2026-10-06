"""Colony component ingest: one fal image-to-3D mesh (tripo3d/h3.1/image-to-3d of an isolated component image) ->
a clean, true-size, reusable kit part in assets/parts-colony/ (README-colony.md, stage C).

    $PY tools/blender/buildings/component.py <in.glb> <name> (--height H | --length L | --width W | --long L | --size W,H,D)
        [--rot x,y,z] [--tris 12000] [--weld 0.004] [--min-piece 0.01] [--dissolve 1.0] [--flatten 0.04]
        [--tex 1024] [--hot 0.85] [--about "..."] [--source <image path or url>] [--fal <job-id>,<job-id>] [--used-by a,b]
    $PY tools/blender/buildings/component.py --rebuild [name ...]   # re-ingest from the params recorded in parts.json

Steps (Blender, the part frame of the building kits: metres, +Y up, the part stands on y = 0, origin at the centre of
its footprint, front +Z; mount.normal '+Y', placed by assemble.py as 'colony:<name>'):
  1. import, join every mesh, apply the node transforms;
  2. --rot x,y,z (degrees, glTF frame, applied X then Y then Z): stand the mesh upright and turn its front to +Z;
  3. clean: weld at --weld (fraction of the bbox diagonal), delete loose pieces whose bbox diagonal is under
     --min-piece of the whole (Tripo floaters), limited dissolve at --dissolve degrees (UV-delimited, so the texture
     survives), then collapse-decimate to --tris;
  4. scale to true size: uniform from --height (y), --length (z), --width (x) or --long (the larger plan extent), or per
     axis from --size (only when the brief
     fixes all three dimensions: lesson "thickness squashed or inflated");
  5. origin at the footprint centre, base on y = 0; vertices within --flatten m of the base snap onto it (a flat foot
     that seats on the plinth);
  6. texture downscaled to --tex; export assets/parts-colony/<name>.glb; parts.json gets bbox, tris, mount, the fal
     job ids, the source image, the buildings that use it (the component catalogue, also listed in README-colony.md).
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(SCENE3D, 'assets', 'parts-colony')

import bpy  # noqa: E402  (bpy first: it makes bmesh / mathutils importable)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

sys.path.insert(0, os.path.dirname(HERE))
import assemble_frame as F  # noqa: E402  (decodes meshopt / Draco GLBs the Blender importer cannot read)


def arg(flag, default=None, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return cast(v)
    return default


def make_hot(me, v):
    """Emissive map from the base colour: texels that are bright, saturated orange-amber (molten metal, furnace glow,
    the concept's small amber lamps) glow; amber paint (darker) and everything else stays dark. v = minimum value
    (max channel, 0-1) of a hot texel. Returns the number of hot texels."""
    import numpy as np
    n = 0
    for mt in me.materials:
        if not mt or not mt.use_nodes:
            continue
        nt = mt.node_tree
        bsdf = next((nd for nd in nt.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf or not bsdf.inputs['Base Color'].links:
            continue
        src = bsdf.inputs['Base Color'].links[0].from_node
        if src.type != 'TEX_IMAGE' or not src.image:
            continue
        img = src.image
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        r, g, b = px[:, 0], px[:, 1], px[:, 2]
        mx = np.maximum(np.maximum(r, g), b)
        sat = (mx - np.minimum(np.minimum(r, g), b)) / np.maximum(mx, 1e-4)
        mask = (mx >= v) & (sat > 0.45) & (r >= g) & (g > b) & (r > 0.5)
        n += int(mask.sum())
        em = np.zeros_like(px)
        em[:, 3] = 1.0
        em[mask, :3] = px[mask, :3]
        out = bpy.data.images.new(f'{img.name}_hot', w, h, alpha=False)
        out.pixels.foreach_set(em.ravel())
        out.pack()
        tn = nt.nodes.new('ShaderNodeTexImage')
        tn.image = out
        for l in list(src.outputs[0].links):
            pass
        uv = src.inputs['Vector'].links[0].from_socket if src.inputs['Vector'].links else None
        if uv:
            nt.links.new(uv, tn.inputs['Vector'])
        nt.links.new(tn.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    return n


def main():
    t0 = time.time()
    height = arg('--height', None, float)
    length = arg('--length', None, float)
    width = arg('--width', None, float)
    long_ = arg('--long', None, float)
    size = arg('--size', None, lambda s: [float(v) for v in s.split(',')])
    rot = arg('--rot', [0.0, 0.0, 0.0], lambda s: [float(v) for v in s.split(',')])
    tris = arg('--tris', 12000, int)
    weld = arg('--weld', 0.004, float)
    min_piece = arg('--min-piece', 0.01, float)
    dissolve = arg('--dissolve', 1.0, float)
    flatten = arg('--flatten', 0.04, float)
    tex = arg('--tex', 1024, int)
    hot = arg('--hot', 0.0, float)
    about = arg('--about', '')
    source = arg('--source', '')
    fal = [j for j in arg('--fal', '').split(',') if j]
    used_by = [b for b in arg('--used-by', '').split(',') if b]
    src, name = os.path.abspath(sys.argv[1]), sys.argv[2]
    if not (height or length or width or long_ or size):
        sys.exit('component.py: give --height, --length, --width, --long or --size')

    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for b in list(coll):
            coll.remove(b)
    import tempfile
    tmp = tempfile.mkdtemp(prefix='component-')
    dec = F.decode([(src, 'component')], tmp)['component']
    bpy.ops.import_scene.gltf(filepath=dec)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    vl = bpy.context.view_layer
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    vl.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = vl.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.context.scene.objects):
        if o != ob:
            bpy.data.objects.remove(o)
    me = ob.data
    raw_tris = sum(len(p.vertices) - 2 for p in me.polygons)

    # glTF frame (Y up) <-> Blender (Z up): (x, y, z)_gltf = (x, z, -y)_blender
    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # gltf -> blender
    from mathutils import Euler
    R = Euler([math.radians(a) for a in rot], 'XYZ').to_matrix().to_4x4()
    me.transform(C @ R @ C.inverted())

    bm = bmesh.new()
    bm.from_mesh(me)
    diag = (Vector([max(v.co[i] for v in bm.verts) for i in range(3)]) - Vector([min(v.co[i] for v in bm.verts) for i in range(3)])).length
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld * diag)
    # loose pieces (connected components by edges)
    bm.verts.ensure_lookup_table()
    seen, pieces = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        pieces.append(comp)
    dropped = 0
    for comp in pieces:
        lo = Vector([min(v.co[i] for v in comp) for i in range(3)])
        hi = Vector([max(v.co[i] for v in comp) for i in range(3)])
        if (hi - lo).length < min_piece * diag:
            bmesh.ops.delete(bm, geom=comp, context='VERTS')
            dropped += 1
    if dissolve > 0:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve), verts=bm.verts, edges=bm.edges, delimit={'UV', 'MATERIAL'})
        bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    now = sum(len(p.vertices) - 2 for p in me.polygons)
    if now > tris:
        m = ob.modifiers.new('dec', 'DECIMATE')
        m.ratio = tris / now
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=m.name)

    # true size and origin (Blender frame: z up; glTF front +Z = Blender -Y)
    co = [v.co.copy() for v in me.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    ext = hi - lo
    if size:
        S = Matrix.Diagonal((size[0] / ext.x, size[2] / ext.y, size[1] / ext.z, 1))
    else:
        # Blender frame: x = glTF x, y = -glTF z, z = glTF y
        k = (height / ext.z) if height else (length / ext.y) if length else (width / ext.x) if width else (long_ / max(ext.x, ext.y))
        S = Matrix.Scale(k, 4)
    me.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    me.transform(S)
    for v in me.vertices:
        if v.co.z < flatten:
            v.co.z = 0.0
    me.update()
    if hot:
        hot_texels = make_hot(me, hot)
    for img in bpy.data.images:
        if img.size[0] > tex:
            img.scale(tex, int(tex * img.size[1] / img.size[0]))
            img.pack()
    for p in me.polygons:
        p.use_smooth = True
    co = [v.co for v in me.vertices]
    lo = [min(c[i] for c in co) for i in range(3)]
    hi = [max(c[i] for c in co) for i in range(3)]
    # Blender -> glTF bbox
    bb_min = [round(lo[0], 3), round(lo[2], 3), round(-hi[1], 3)]
    bb_max = [round(hi[0], 3), round(hi[2], 3), round(-lo[1], 3)]
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f'{name}.glb')
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    ob.name = name
    for i, mt in enumerate(me.materials):   # one recognisable material name per component (runtime overrides 'colony_*')
        if mt:
            mt.name = f'colony_{name}' + (f'_{i}' if i else '')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='WEBP')
    final = sum(len(p.vertices) - 2 for p in me.polygons)
    man_path = os.path.join(OUT, 'parts.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else {
        'generator': 'tools/blender/buildings/component.py',
        'frame': 'metres, +Y up, stands on y = 0, origin at the footprint centre, front +Z (placed as colony:<name>)',
        'parts': {}}
    old = man['parts'].get(name, {})
    man['parts'][name] = {
        'file': f'{name}.glb', 'part': name, 'about': about or old.get('about', ''),
        'bbox': {'min': bb_min, 'max': bb_max, 'size': [round(b - a, 3) for a, b in zip(bb_min, bb_max)]},
        'tris': final, 'trisRaw': raw_tris, 'loosePiecesDropped': dropped, 'tex': tex,
        'mount': {'normal': '+Y', 'anchor': 'footprint centre at y = 0, front +Z'},
        'source': source or old.get('source', ''), 'fal': fal or old.get('fal', []),
        'usedBy': sorted(set(old.get('usedBy', [])) | set(used_by)),
        'hot': hot, 'hotTexels': hot_texels if hot else 0,
        'params': {'rot': rot, 'hotV': hot, 'height': height, 'length': length, 'width': width, 'long': long_, 'size': size, 'tris': tris, 'weld': weld, 'minPiece': min_piece, 'dissolve': dissolve},
        'kb': round(os.path.getsize(out) / 1024), 'seconds': round(time.time() - t0, 1),
    }
    json.dump(man, open(man_path, 'w'), indent=1)
    print(f'[component] {name}: {raw_tris} -> {final} tris, {dropped} loose pieces dropped, size {man["parts"][name]["bbox"]["size"]} m -> {out}')


def rebuild(names):
    """Re-ingest components from their recorded params (parts.json) and raw meshes (assets/buildings/raw/<name>.glb,
    gitignored; re-download by the fal job id when missing). Each runs in its own Python process."""
    import subprocess
    man = json.load(open(os.path.join(OUT, 'parts.json')))['parts']
    for n in names or list(man):
        q = man[n]
        pr = q['params']
        cmd = [sys.executable, __file__, os.path.join(SCENE3D, 'assets', 'buildings', 'raw', f'{n}.glb'), n,
               '--rot', ','.join(str(v) for v in pr['rot']), '--tris', str(pr['tris']), '--weld', str(pr['weld']),
               '--min-piece', str(pr['minPiece']), '--dissolve', str(pr['dissolve']), '--tex', str(q['tex'])]
        if pr.get('hotV'):
            cmd += ['--hot', str(pr['hotV'])]
        for k in ('height', 'length', 'width', 'long'):
            if pr.get(k):
                cmd += [f'--{k}', str(pr[k])]
        if pr.get('size'):
            cmd += ['--size', ','.join(str(v) for v in pr['size'])]
        out = subprocess.run(cmd, capture_output=True, text=True)
        print(next((l for l in (out.stdout + out.stderr).split('\n') if l.startswith('[component]') or 'Error' in l), out.stderr[-400:]), flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rebuild':
        rebuild(sys.argv[2:])
    else:
        main()
