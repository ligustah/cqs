# Contact shadow for tools/blender/assemble.py: how much the placed parts occlude the hull,
# baked with Cycles (CPU) into the hull's UV atlas and multiplied into its base colour, so the
# parts sit in the surface instead of floating on it.
#
# One EMIT bake of  AO(all objects) / AO(hull only)  per hull texel: the hull's own cavities cancel
# out and only the occlusion added by the parts is left (1 = none). It is baked at `res` (default
# 2048, texel ~8 cm on the corvette), de-noised (dead zone + 3x3 blur), upsampled to the base
# colour size and applied as base *= 1 - strength * occlusion.
import os
import time
import bpy
import numpy as np


def _base_image(hull):
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
            return m, nd.image
    return None, None


def _blur3(a):
    p = np.pad(a, 1, mode='edge')
    return sum(p[1 + dy:1 + dy + a.shape[0], 1 + dx:1 + dx + a.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9


def bake_contact(hull, parts, cfg, threads=2, tmpdir=None):
    t0 = time.time()
    res = cfg.get('res', 2048)
    dist = cfg.get('distance', 0.6)
    ns = cfg.get('samples', 16)
    strength = cfg.get('strength', 0.85)
    mat, base = _base_image(hull)
    if base is None:
        return {'skipped': 'no base colour image'}
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = cfg.get('aa', 4)
    sc.cycles.use_denoising = False
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = threads
    sc.render.bake.margin = 6
    sc.render.bake.use_clear = True
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    # bake shader on the hull: emission = AO(all) / AO(local)
    nt = mat.node_tree
    out = next(nd for nd in nt.nodes if nd.type == 'OUTPUT_MATERIAL')
    old_link = out.inputs['Surface'].links[0].from_socket if out.inputs['Surface'].is_linked else None
    ao_all = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao_all.samples = ns; ao_all.only_local = False
    ao_loc = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao_loc.samples = ns; ao_loc.only_local = True
    for a in (ao_all, ao_loc):
        a.inputs['Distance'].default_value = dist
    div = nt.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'; div.use_clamp = True
    nt.links.new(ao_all.outputs['AO'], div.inputs[0])
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; mx.inputs[1].default_value = 0.02
    nt.links.new(ao_loc.outputs['AO'], mx.inputs[0])
    nt.links.new(mx.outputs[0], div.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(div.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    img = bpy.data.images.new('contact_bake', res, res, float_buffer=True, alpha=False)
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    for nd in nt.nodes:
        nd.select = False
    tex.select = True
    nt.nodes.active = tex
    # only the hull is baked; parts are ray targets
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    hull.select_set(True)
    bpy.context.view_layer.objects.active = hull
    with bpy.context.temp_override(active_object=hull, selected_objects=[hull], object=hull):
        bpy.ops.object.bake(type='EMIT', margin=6, use_clear=True)
    t_bake = time.time() - t0
    px = np.empty(res * res * 4, np.float32)
    img.pixels.foreach_get(px)
    ratio = px.reshape(res, res, 4)[:, :, 0]
    # texels the bake never wrote (outside the UV islands and their margin) stay 0: leave them
    occ = np.where(ratio > 1e-4, np.clip(1 - ratio, 0, 1), 0.0)
    occ = np.clip((occ - 0.06) / 0.5, 0, 1)  # dead zone for the sampling noise of the ratio
    occ = _blur3(_blur3(occ))
    if tmpdir:  # the contact term, for inspection (white = no occlusion)
        dbg = bpy.data.images.new('contact_dbg', res, res, alpha=False)
        g = np.repeat((1 - occ)[:, :, None], 4, 2).astype(np.float32)
        g[:, :, 3] = 1
        dbg.pixels.foreach_set(g.ravel())
        dbg.filepath_raw = os.path.join(tmpdir, 'contact.png')
        dbg.file_format = 'PNG'
        dbg.save()
        raw = bpy.data.images.new('contact_raw', res, res, alpha=False)
        g = np.repeat(np.clip(ratio, 0, 1)[:, :, None], 4, 2).astype(np.float32)
        g[:, :, 3] = 1
        raw.pixels.foreach_set(g.ravel())
        raw.filepath_raw = os.path.join(tmpdir, 'contact_ratio.png')
        raw.file_format = 'PNG'
        raw.save()
    # restore the hull shader
    for nd in (ao_all, ao_loc, div, mx, em, tex):
        nt.nodes.remove(nd)
    if old_link is not None:
        nt.links.new(old_link, out.inputs['Surface'])
    # apply to the base colour (stored sRGB): multiply in linear light
    W, H = base.size
    bpx = np.empty(W * H * 4, np.float32)
    base.pixels.foreach_get(bpx)
    bpx = bpx.reshape(H, W, 4)
    ky, kx = H / res, W / res
    ys = np.minimum((np.arange(H) / ky).astype(int), res - 1)
    xs = np.minimum((np.arange(W) / kx).astype(int), res - 1)
    up = occ[ys][:, xs]
    k = (1 - strength * up) ** (1 / 2.2)
    bpx[:, :, :3] *= k[:, :, None]
    base.pixels.foreach_set(bpx.ravel())
    base.pack()
    bpy.data.images.remove(img)
    return {'res': res, 'distance': dist, 'samples': ns, 'bake_s': round(t_bake, 1),
            'texels_darkened': int((up > 0.05).sum()), 'max_occlusion': round(float(up.max()), 3)}
