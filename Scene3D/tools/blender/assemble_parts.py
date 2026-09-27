# Parts for tools/blender/assemble.py: load the fal parts kit (assets/parts/*.glb), repair its
# known defects, harden the normals, and build flush cover plates ("patch").
#
# Part frame (assets/parts/parts.json "frame"): metres, +Z out of the hull, +Y up, +X along the
# width. mount.normal "+Z" parts have their back face at z = 0; "+Y" parts (rail, antenna,
# container) stand on their foot at y = 0. In Blender a part is kept in its glTF frame converted
# by the importer (glTF (x, y, z) -> Blender (x, -z, y)); assemble.py places it with b_mat().
import json
import math
import os
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

import assemble_frame as F

# Defaults for the fal kit's known defects; a spec can override any key under "fixes".
DEFAULT_FIXES = {
    # Tripo left the port's glazing out (an open hole through the frame). A dark blue-grey glass
    # plane closes it, 0.22 m out from the back face: 2 cm proud of the hull once the frame is
    # sunk 0.2 m, 8 cm behind the frame's front face. It is larger than the aperture; the part
    # outside the aperture is inside the solid frame. The colour is picked so livery.js reads
    # it as glass (dark, blue-tinted, not strongly saturated) and makes it glossy.
    'port': {'glass': {'z': 0.22, 'size': [1.12, 1.12], 'color': [0.018, 0.024, 0.034], 'roughness': 0.08}},
    # Handrail tubes came back ~90-100 mm; scale the tube cross-sections toward 50 mm about each
    # tube's own axis (top rail, mid rail, posts). The bolted foot plates are left alone.
    'rail': {'tube': {'target': 0.05}},
}
# Triangle budget: the kit parts are 1.3-4.3k triangles each, sized for a close-up of one part.
# Placed by the dozen on a 100k-triangle hull they are collapse-decimated first (UVs kept), to
# roughly these fractions (a spec's fixes.<part>.decimate overrides; 1 = keep).
DECIMATE = {'rail': 0.22, 'port': 0.3, 'pane': 0.45, 'door': 0.45, 'airlock': 0.4, 'ladder': 0.3,
            'rcs': 0.3, 'antenna': 0.5, 'dome': 0.4, 'floodlight': 0.3, 'container': 0.5, 'cargoHatch': 0.5}
HARDEN = {'angle': 30.0, 'weight': 50}  # sharp-edge angle (deg) and WeightedNormal weight


def load_manifest(parts_dir):
    p = os.path.join(parts_dir, 'parts.json')
    return json.load(open(p)) if os.path.exists(p) else {'parts': {}}


def mount_of(manifest, name):
    m = (manifest.get('parts', {}).get(name) or {}).get('mount') or {}
    return m.get('normal', '+Z')


def part_frame_coords(me):
    """vertex coordinates of a part mesh in its glTF part frame (numpy, n x 3)"""
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)


def set_part_frame_coords(me, g):
    co = np.stack([g[:, 0], -g[:, 2], g[:, 1]], 1)
    me.vertices.foreach_set('co', co.ravel())
    me.update()


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------
# fixes
# ------------------------------------------------------------------------------------------
def fix_rail(me, cfg):
    """Thin the rail tubes toward cfg.target (m) about their own axes (measured on the kit's
    rail: top rail y 0.997-1.091 / z +-0.05, mid rail y 0.512-0.565 / z +-0.03, posts at
    x = +-0.365, 0.09 m wide / z +-0.054; foot plates below y = 0.12)."""
    t = cfg.get('target', 0.05)
    g = part_frame_coords(me)
    x, y, z = g[:, 0].copy(), g[:, 1].copy(), g[:, 2].copy()
    above = smoothstep(0.10, 0.16, y)                   # 0 on the foot plates
    kz = 1 + above * (min(1.0, t / 0.10) - 1)           # tube depth (z) ~0.10 -> t
    z = z * kz
    # top rail: 0.094 m tall about y = 1.044
    wt = smoothstep(0.93, 0.99, y)
    y = y + wt * ((1.044 + (y - 1.044) * min(1.0, t / 0.094)) - y)
    # posts: 0.09 m wide about x = +-0.365, between the feet and the top rail
    post = (np.abs(np.abs(x) - 0.365) < 0.085) & (y > 0.10) & (y < 0.99)
    cx = np.sign(x) * 0.365
    wp = post * smoothstep(0.10, 0.16, y)
    x = x + wp * ((cx + (x - cx) * min(1.0, t / 0.09)) - x)
    # mid rail: 0.053 m tall about y = 0.538 (already close; tidy only)
    wm = (np.abs(y - 0.538) < 0.05) & ~post
    y = np.where(wm, 0.538 + (y - 0.538) * min(1.0, t / 0.053), y)
    set_part_frame_coords(me, np.stack([x, y, z], 1))


def glass_material(cfg):
    m = bpy.data.materials.new('glass')
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    c = cfg.get('color', [0.018, 0.024, 0.034])
    b.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1)
    b.inputs['Roughness'].default_value = cfg.get('roughness', 0.08)
    b.inputs['Metallic'].default_value = 0.0
    return m


def add_glass(obj, cfg):
    """A glass plane in the part frame at z = cfg.z, facing +Z."""
    w, h = cfg.get('size', [1.1, 1.1])
    z = cfg.get('z', 0.2)
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
    # part frame (x, y, z) -> Blender (x, -z, y); CCW seen from +Z (part) = from -Y (Blender)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    vs = [bm.verts.new((px, -z, py)) for px, py in pts]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:  # must face part +Z = Blender -Y
        f.normal_flip()
    mat = glass_material(cfg)
    me.materials.append(mat)
    f.material_index = len(me.materials) - 1
    for l in f.loops:
        l[uv].uv = (0.5, 0.5)
    bm.to_mesh(me)
    bm.free()


def harden(obj, angle=HARDEN['angle'], weight=HARDEN['weight']):
    """Crisp hard-surface shading: split normals at edges sharper than `angle`, then face-area
    weighted normals (large flat faces dominate their vertices), applied as custom normals."""
    me = obj.data
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(angle))
    mod = obj.modifiers.new('wn', 'WEIGHTED_NORMAL')
    mod.mode = 'FACE_AREA'
    mod.weight = weight
    mod.keep_sharp = True
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def decimate(obj, ratio):
    mod = obj.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=mod.name)


class Part:
    """One kit part in Blender: `mesh` (as authored) and `mirror` (mirrored in X, winding
    flipped), both hardened, plus its size/mount info."""

    def __init__(self, name, mesh, mirror, mount, bbox):
        self.name, self.mesh, self.mirror, self.mount, self.bbox = name, mesh, mirror, mount, bbox


def load_part(name, parts_dir, manifest, tmpdir, fixes):
    src = os.path.join(parts_dir, f'{name}.glb')
    dec = F.decode([(src, f'part-{name}')], tmpdir)[f'part-{name}']
    ms, new = F.import_glb(dec)
    obj = F.join(ms, f'src_{name}')
    for o in new:
        if o.name in bpy.data.objects and o != obj:
            bpy.data.objects.remove(o)
    fx = {**DEFAULT_FIXES.get(name, {}), **(fixes.get(name) or {})}
    if fx.get('tube'):
        fix_rail(obj.data, fx['tube'])
    ratio = fx.get('decimate', DECIMATE.get(name, 1))
    if ratio < 1:
        decimate(obj, ratio)
    if fx.get('glass'):
        add_glass(obj, fx['glass'])
    # mirrored twin (X flipped, faces re-wound) for mirrorX placements: handed parts stay handed
    mir = obj.copy()
    mir.data = obj.data.copy()
    mir.name = f'src_{name}_mirror'
    bpy.context.collection.objects.link(mir)
    mir.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0))))
    mir.data.flip_normals()
    harden(obj)
    harden(mir)
    g = part_frame_coords(obj.data)
    bbox = (g.min(0), g.max(0))
    return Part(name, obj, mir, mount_of(manifest, name), bbox)


# ------------------------------------------------------------------------------------------
# patches: flush cover plates in the hull's own paint
# ------------------------------------------------------------------------------------------
class Palette:
    """Patch colours as texels of one small sRGB texture (one material for every patch), so the
    livery repaints them exactly like the hull texture it samples."""

    def __init__(self, n=64):
        self.n = n
        self.colors = []

    def add(self, rgb):
        self.colors.append(tuple(rgb))
        return len(self.colors) - 1

    def uv(self, i):
        return ((i + 0.5) / self.n, 0.5)

    def material(self, tmpdir):
        n = self.n
        gen = bpy.data.images.new('patch_palette_gen', n, 1, alpha=False)
        px = np.ones((1, n, 4), np.float32)
        for i, c in enumerate(self.colors[:n]):
            px[0, i, :3] = c
        gen.pixels.foreach_set(px.ravel())
        # written to a PNG and loaded back: the glTF exporter skips unsaved generated images
        path = os.path.join(tmpdir, 'patch_palette.png')
        gen.filepath_raw = path
        gen.file_format = 'PNG'
        gen.save()
        bpy.data.images.remove(gen)
        img = bpy.data.images.load(path)
        img.name = 'patch_palette'
        img.colorspace_settings.name = 'sRGB'
        img.pack()
        m = bpy.data.materials.new('patch')
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes.get('Principled BSDF')
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img
        t.interpolation = 'Closest'
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.6
        b.inputs['Metallic'].default_value = 0.0
        return m


def patch_bmesh(w, h, d, chamfer=0.03):
    """Plate w x h x d in the part frame (back at z = 0, front at z = d), front edges chamfered."""
    bm = bmesh.new()
    c = min(chamfer, d * 0.4, w * 0.2, h * 0.2)
    ring = lambda hw, hh, z: [bm.verts.new((sx * hw, -z, sy * hh)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    back = ring(w / 2, h / 2, 0)
    mid = ring(w / 2, h / 2, d - c)
    front = ring(w / 2 - c, h / 2 - c, d)
    for a, b in ((back, mid), (mid, front)):
        for i in range(4):
            bm.faces.new((a[i], a[(i + 1) % 4], b[(i + 1) % 4], b[i]))
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sample_hull_color(caster, tex, p, x, y, n, w, h, margin=0.5):
    """Median hull base colour on a ring just outside a w x h rectangle (the old detail it covers
    is excluded)."""
    if tex is None:
        return (0.8, 0.8, 0.8)
    W, H, px = tex
    cols = []
    for sx in np.linspace(-1, 1, 5):
        for sy in (-1, 1):
            for (u, v) in ((sx * (w / 2 + margin), sy * (h / 2 + margin)), (sy * (w / 2 + margin), sx * (h / 2 + margin))):
                o = p + x * u + y * v + n * 3
                hit = caster.cast(o, -n, 6)
                if hit is None:
                    continue
                uv = caster.uv_at(hit[0], hit[2])
                if uv is None:
                    continue
                i = int((uv[0] % 1) * W); j = int((uv[1] % 1) * H)
                cols.append(px[min(j, H - 1), min(i, W - 1), :3])
    if not cols:
        return (0.8, 0.8, 0.8)
    return tuple(np.median(np.array(cols), 0))


def hull_texture(hull):
    """(W, H, pixels) of the hull's base-colour image (sRGB values as stored)."""
    for m in hull.data.materials:
        if not m or not m.use_nodes:
            continue
        b = next((nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if not b or not b.inputs['Base Color'].is_linked:
            continue
        nd = b.inputs['Base Color'].links[0].from_node
        while nd and nd.type != 'TEX_IMAGE':
            ins = [i for i in nd.inputs if i.is_linked]
            nd = ins[0].links[0].from_node if ins else None
        if nd and nd.image:
            img = nd.image
            W, H = img.size
            px = np.empty(W * H * 4, np.float32)
            img.pixels.foreach_get(px)
            return W, H, px.reshape(H, W, 4)
    return None
