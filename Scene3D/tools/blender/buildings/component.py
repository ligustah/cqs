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


def make_hot(me, v, sat_min=0.45):
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
        mask = (mx >= v) & (sat > sat_min) & (r >= g) & (g > b) & (r > min(0.5, v))
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


REPO = os.path.abspath(os.path.join(SCENE3D, '..'))
STYLE = os.path.join(REPO, 'style-library', 'styles', 'cqs-fleet')
LUMA = (0.2126, 0.7152, 0.0722)
# albedo normalisation (README-colony.md "Paint calibration", lessons 48): Tripo H3.1 de-lights its texture a step to
# three darker than the component image it came from, and warmer (a brown cast on the greys): measured over all 50
# components the surface-weighted linear albedo was 0.84-4.2x (median 1.6x) below the image's foreground, with twice
# its saturation on the neutral paint. Each component is normalised once, at ingest, against its own source image:
# white balance on the neutral texels, then one linear gain so the trimmed mean (p30-p97) matches the image's. The
# image's light paint lands at linear ~0.5-0.6, the kit's 'panel' (0.60) scale, so the runtime needs no lift.
NORM = {'gain': (0.85, 3.2), 'wb': 0.15, 'trim': (30, 97), 'neutral': 0.15, 'knee': 0.72, 'ceil': 0.94, 'metal': 0.15, 'chroma': 0.45, 'match': 0.6, 'matchClamp': (0.6, 2.2)}


def _s2l(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _l2s(c):
    import numpy as np
    c = np.maximum(c, 0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def _sat(rgb):
    import numpy as np
    mx = rgb.max(-1)
    return (mx - rgb.min(-1)) / np.maximum(mx, 1e-4)


def source_stats(path):
    """The component image's foreground (pixels > 30/255 summed off the median border colour, i.e. not the light-grey
    studio): linear RGB samples."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255
    bg = np.median(np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)]), 0)
    fg = a[np.abs(a - bg).sum(2) > 30 / 255]
    return _s2l(fg), fg


def glass_tint(me):
    """--glass: Tripo bakes the warm interior seen through glazing into the glass as an amber-brown (the university's
    atrium). Mid warm texels (hue 15-55 deg, sat 0.2-0.75, value 0.1-0.7: not the bright lamps, which --hot keeps, nor
    the near-neutral stone) are turned into a cool blue-grey glass tone of the same luminance. Returns the texel share."""
    import numpy as np
    share = 0.0
    for mt in me.materials:
        if not mt or not mt.use_nodes:
            continue
        bsdf = next((nd for nd in mt.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf or not bsdf.inputs['Base Color'].links or bsdf.inputs['Base Color'].links[0].from_node.type != 'TEX_IMAGE':
            continue
        img = bsdf.inputs['Base Color'].links[0].from_node.image
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
        c = px[:, :3].astype(np.float64)
        mx, mn = c.max(1), c.min(1)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        r, g, b = c[:, 0], c[:, 1], c[:, 2]
        hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
        m = (hue > 15) & (hue < 55) & (sat > 0.2) & (sat < 0.75) & (mx > 0.1) & (mx < 0.7)
        lin = _s2l(c[m])
        Y = lin @ np.array(LUMA)
        tint = np.array((0.80, 0.93, 1.12)); tint /= tint @ np.array(LUMA)
        px[m, :3] = _l2s(Y[:, None] * tint * 1.1).astype(np.float32)
        img.pixels.foreach_set(px.ravel()); img.update(); img.pack()
        share = float(m.mean())
        # the warm interior behind the glass becomes a dim emissive glow (it was baked into the paint): the glass then
        # reads cool in the key light and warm from within, as in the image. Added to the --hot map if there is one.
        nt = mt.node_tree
        em_src = bsdf.inputs['Emission Color'].links[0].from_node if bsdf.inputs['Emission Color'].links else None
        if em_src is not None and em_src.type == 'TEX_IMAGE' and em_src.image.size[:] == img.size[:]:
            eimg = em_src.image
            ep = np.empty(w * h * 4, dtype=np.float32); eimg.pixels.foreach_get(ep); ep = ep.reshape(-1, 4)
        else:
            eimg = bpy.data.images.new(f'{img.name}_glow', w, h, alpha=False)
            ep = np.zeros((w * h, 4), dtype=np.float32); ep[:, 3] = 1.0
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = eimg
            src = bsdf.inputs['Base Color'].links[0].from_node
            if src.inputs['Vector'].links:
                nt.links.new(src.inputs['Vector'].links[0].from_socket, tn.inputs['Vector'])
            nt.links.new(tn.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 1.0
        warm = np.array((1.0, 0.70, 0.38))
        k = np.clip(mx[m] / 0.7, 0, 1) ** 1.5 * 0.42
        ep[m, :3] = np.maximum(ep[m, :3], (_l2s(warm[None, :] * k[:, None] * 0.6)).astype(np.float32))
        eimg.pixels.foreach_set(ep.ravel()); eimg.update(); eimg.pack()
    return share


def resolve_source(src, name):
    for p in (src, os.path.join(REPO, src or ''), os.path.join(STYLE, src or ''),
              os.path.join(STYLE, 'images', 'buildings', 'components', f'{name}.jpg')):
        if p and os.path.isfile(p):
            return p
    return None


def _trimmed(Y, lo, hi):
    import numpy as np
    a, b = np.percentile(Y, lo), np.percentile(Y, hi)
    return (Y >= a) & (Y <= b)


def normalise_albedo(ob, src_path, n=200000):
    """Match the base-colour texture to its source image (see NORM). Surface-weighted texel samples (triangle area x
    barycentric) stand in for 'what the image shows'. Writes the texture in place (sRGB bytes) and caps the mean
    metalness (Tripo paints steel trim metallic, which the dim dusk env turns near black). Returns the record."""
    import numpy as np
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    loops = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('loops', loops)
    area = np.empty(nt); me.loop_triangles.foreach_get('area', area)
    uvl = me.uv_layers.active
    uv = np.empty(len(me.loops) * 2); uvl.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    rng = np.random.default_rng(7)
    tri = rng.choice(nt, n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    L = loops.reshape(-1, 3)[tri]
    suv = uv[L[:, 0]] * (1 - u - v)[:, None] + uv[L[:, 1]] * u[:, None] + uv[L[:, 2]] * v[:, None]
    rec = {}
    for mt in me.materials:
        if not mt or not mt.use_nodes:
            continue
        bsdf = next((nd for nd in mt.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf or not bsdf.inputs['Base Color'].links or bsdf.inputs['Base Color'].links[0].from_node.type != 'TEX_IMAGE':
            continue
        img = bsdf.inputs['Base Color'].links[0].from_node.image
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
        lin_img = _s2l(px[..., :3].astype(np.float64))   # Blender keeps byte images' pixels as their sRGB values
        x = (np.mod(suv[:, 0], 1) * (w - 1)).astype(int); y = (np.mod(suv[:, 1], 1) * (h - 1)).astype(int)
        tex = lin_img[y, x]
        src_lin, src_s = source_stats(src_path)
        # 1. white balance: the neutral paint's channel ratios (sat < NORM.neutral in sRGB) as the image's
        tn, sn = tex[_sat(_l2s(tex)) < NORM['neutral']], src_lin[_sat(src_s) < NORM['neutral']]
        wb = np.ones(3)
        if len(tn) > 500 and len(sn) > 500:
            rt = tn.mean(0) / max(tn.mean(0) @ LUMA, 1e-4); rs = sn.mean(0) / max(sn.mean(0) @ LUMA, 1e-4)
            wb = np.clip(rs / rt, 1 - NORM['wb'], 1 + NORM['wb'])
            wb *= (tn.mean(0) @ LUMA) / ((tn.mean(0) * wb) @ LUMA)   # balance only: keep the luminance
        # 2. one linear gain so the trimmed means match, with a soft knee so the light paint does not clip
        # 1b. chroma: the near-neutral paint (sat < 0.35) as saturated as the image's (only ever less); deliberate
        # colour (sat > 0.45: amber cranes, cobalt bands, lamps) is kept
        def sat_lin(c):
            return _sat(_l2s(c))
        tw, sw = tex * wb, src_lin
        mt_, ms_ = sat_lin(tw) < 0.35, _sat(src_s) < 0.35
        chroma = float(np.clip(np.median(_sat(src_s)[ms_]) / max(np.median(sat_lin(tw)[mt_]), 1e-4), NORM['chroma'], 1.0)) if mt_.sum() > 500 and ms_.sum() > 500 else 1.0
        def desat(c):
            Y = (c @ np.array(LUMA))[..., None]
            k = np.clip((0.45 - sat_lin(c)) / 0.2, 0, 1)[..., None] * (1 - chroma)
            return Y + (c - Y) * (1 - k)
        def tone(c, g):
            o = desat(c * wb) * g
            k, top = NORM['knee'], NORM['ceil']
            return np.where(o > k, k + (top - k) * (1 - np.exp(-(o - k) / (top - k))), o)
        Yt, Ys = tex @ LUMA, src_lin @ LUMA
        target = Ys[_trimmed(Ys, *NORM['trim'])].mean()
        lo, hi = NORM['gain']
        for _ in range(40):
            g = (lo + hi) / 2
            Yg = tone(tex, g) @ LUMA
            if Yg[_trimmed(Yg, *NORM['trim'])].mean() < target: lo = g
            else: hi = g
        g = (lo + hi) / 2
        g = min(max(g, NORM['gain'][0]), NORM['gain'][1])
        # 3. tonal match: Tripo also flattens the image's tonal range (a mid-grey yoke baked near black under a dish face
        # baked near white): a monotone curve that maps the toned texture's luminance quantiles (p5-p98) onto the image's,
        # applied at NORM.match strength (geometric blend with the gain-only tone), per texel as a luminance scale
        Yg = tone(tex, g) @ LUMA
        qs = np.linspace(5, 98, 24)
        xq = np.log(np.maximum(np.percentile(Yg, qs), 1e-4))
        yq = np.log(np.maximum(np.maximum.accumulate(np.percentile(Ys, qs)), 1e-4))
        xq = np.maximum.accumulate(xq + np.arange(len(xq)) * 1e-6)
        def match(c):
            Y = np.maximum(c @ np.array(LUMA), 1e-5)
            k = np.exp(NORM['match'] * (np.interp(np.log(Y), xq, yq) - np.log(Y)))
            k = np.clip(k, NORM['matchClamp'][0], NORM['matchClamp'][1])
            return np.minimum(c * k[..., None], NORM['ceil'])
        out = px.copy()
        out[..., :3] = _l2s(match(tone(lin_img, g))).astype(np.float32)
        img.pixels.foreach_set(out.ravel()); img.update(); img.pack()
        after = match(tone(tex, g))
        st = lambda c: [round(float(t), 3) for t in (c.mean(0) @ LUMA, np.median(_sat(_l2s(c))))]
        rec = {'gain': round(float(g), 3), 'wb': [round(float(t), 3) for t in wb], 'chroma': round(chroma, 3), 'source': os.path.relpath(src_path, REPO),
               'texY': st(tex)[0], 'texSat': st(tex)[1], 'srcY': round(float(Ys.mean()), 3), 'srcSat': round(float(np.median(_sat(src_s))), 3),
               'outY': st(after)[0], 'outSat': st(after)[1]}
        # 3. metalness: cap the mean of the metallic map at NORM.metal through the factor (painted structure)
        mr = next((nd for nd in mt.node_tree.nodes if nd.type == 'TEX_IMAGE' and nd.image and nd.image != img
                   and any(l.to_node.type == 'SEPARATE_COLOR' or l.to_socket.name == 'Metallic' for l in nd.outputs[0].links)), None)
        met = None
        if mr:
            mw, mh = mr.image.size
            mp = np.empty(mw * mh * 4, dtype=np.float32); mr.image.pixels.foreach_get(mp); mp = mp.reshape(mh, mw, 4)
            met = float(mp[(np.mod(suv[:, 1], 1) * (mh - 1)).astype(int), (np.mod(suv[:, 0], 1) * (mw - 1)).astype(int), 2].mean())
        rec['metalMean'] = round(met, 3) if met is not None else None
        rec['metalFactor'] = round(min(1.0, NORM['metal'] / met), 3) if met and met > NORM['metal'] else 1.0
        if rec['metalFactor'] < 1.0:   # scale the map's metal channel (B) in place: the exporter keeps the texture
            mp[..., 2] *= rec['metalFactor']
            mr.image.pixels.foreach_set(mp.ravel()); mr.image.update(); mr.image.pack()
    return rec


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
    hot_sat = arg('--hot-sat', 0.45, float)
    glass = '--glass' in sys.argv
    if glass:
        sys.argv.remove('--glass')
    about = arg('--about', '')
    source = arg('--source', '')
    fal = [j for j in arg('--fal', '').split(',') if j]
    used_by = [b for b in arg('--used-by', '').split(',') if b]
    no_norm = '--no-norm' in sys.argv
    if no_norm:
        sys.argv.remove('--no-norm')
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
        hot_texels = make_hot(me, hot, hot_sat)
    glass_share = glass_tint(me) if glass else 0.0
    for img in bpy.data.images:
        if img.size[0] > tex:
            img.scale(tex, int(tex * img.size[1] / img.size[0]))
            img.pack()
    # albedo normalisation against the source component image (NORM; after --hot, which reads the raw paint)
    man_path = os.path.join(OUT, 'parts.json')
    prev = (json.load(open(man_path))['parts'].get(name, {}) if os.path.exists(man_path) else {})
    src_img = resolve_source(source or prev.get('source', ''), name)
    albedo = None
    if not no_norm and src_img:
        albedo = normalise_albedo(ob, src_img)
        print(f'[component] {name}: albedo gain {albedo.get("gain")} wb {albedo.get("wb")} Y {albedo.get("texY")} -> {albedo.get("outY")} '
              f'(image {albedo.get("srcY")}), sat {albedo.get("texSat")} -> {albedo.get("outSat")} (image {albedo.get("srcSat")}), '
              f'metal {albedo.get("metalMean")} x{albedo.get("metalFactor")}')
    elif not no_norm:
        print(f'[component] {name}: WARNING no source image, albedo not normalised')
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
        'hot': hot, 'hotTexels': hot_texels if hot else 0, 'albedo': albedo, 'glassTint': round(glass_share, 4),
        'params': {'rot': rot, 'hotV': hot, 'hotSat': hot_sat, 'glass': glass, 'norm': not no_norm, 'height': height, 'length': length, 'width': width, 'long': long_, 'size': size, 'tris': tris, 'weld': weld, 'minPiece': min_piece, 'dissolve': dissolve},
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
        if pr.get('norm') is False:
            cmd += ['--no-norm']
        if pr.get('hotSat') not in (None, 0.45):
            cmd += ['--hot-sat', str(pr['hotSat'])]
        if pr.get('glass'):
            cmd += ['--glass']
        for k in ('height', 'length', 'width', 'long'):
            if pr.get(k):
                cmd += [f'--{k}', str(pr[k])]
        if pr.get('size'):
            cmd += ['--size', ','.join(str(v) for v in pr['size'])]
        out = subprocess.run(cmd, capture_output=True, text=True)
        print('\n'.join(l for l in (out.stdout + out.stderr).split('\n') if l.startswith('[component]') or 'Error' in l) or out.stderr[-400:], flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rebuild':
        rebuild(sys.argv[2:])
    else:
        main()
