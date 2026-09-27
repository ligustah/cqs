# Node (glTF-Transform + sharp) stages of tools/blender/straighten.py, run with the Scene3D folder
# as the working directory so the packages resolve from Scene3D/node_modules. Blender's glTF
# importer cannot read EXT_meshopt_compression, and round-tripping 4-8k textures through Blender
# only costs time and a generation of loss, so:
#   PREP   in.glb -> geometry-only GLB for Blender (meshopt decoded, dequantised, textures dropped)
#          and info.json (texture sizes, node matrix);
#   MERGE  the original document with its mesh attributes replaced by Blender's straightened
#          geometry (positions, split normals, UVs, indices) and its normal map kept, high-passed
#          (the low-frequency lumps removed in UV space, masked to the UV islands) or dropped.
import json
import os
import subprocess

HEAD = r"""
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dequantize } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';
import { writeFile } from 'node:fs/promises';
await Promise.all([MeshoptDecoder.ready, MeshoptEncoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const A = JSON.parse(process.env.STRAIGHTEN_ARGS);
const worldMatrix = (node) => node.getWorldMatrix();
"""

PREP = HEAD + r"""
const doc = await io.read(A.input);
await doc.transform(dequantize());
const root = doc.getRoot();
const info = { meshes: [], textures: [] };
for (const t of root.listTextures()) info.textures.push({ name: t.getName(), mime: t.getMimeType(), size: t.getSize() });
for (const node of root.listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  info.meshes.push({ node: node.getName(), matrix: worldMatrix(node), prims: mesh.listPrimitives().length });
}
for (const m of root.listMaterials()) {
  const n = m.getNormalTexture();
  info.normalScale = m.getNormalScale();
  info.hasNormal = !!n;
  m.setBaseColorTexture(null).setMetallicRoughnessTexture(null).setNormalTexture(null)
   .setOcclusionTexture(null).setEmissiveTexture(null);
}
for (const t of root.listTextures()) t.dispose();
for (const e of root.listExtensionsUsed()) if (/meshopt|webp|quantization/.test(e.extensionName)) e.dispose();
await io.write(A.geom, doc);
await writeFile(A.info, JSON.stringify(info, null, 1));
"""

MERGE = HEAD + r"""
import { Matrix4 } from 'three';
const invert = (_, m) => new Matrix4().fromArray(m).invert().toArray();
const multiply = (_, a, b) => new Matrix4().fromArray(a).multiply(new Matrix4().fromArray(b)).toArray();
const orig = await io.read(A.input);
await orig.transform(dequantize());
const bl = await io.read(A.blender);
const oroot = orig.getRoot(), broot = bl.getRoot();
const onodes = oroot.listNodes().filter((n) => n.getMesh());
const bnodes = broot.listNodes().filter((n) => n.getMesh());
if (onodes.length !== 1 || onodes[0].getMesh().listPrimitives().length !== 1) throw new Error('merge supports one mesh node with one primitive');
const onode = onodes[0], oprim = onode.getMesh().listPrimitives()[0];
// Blender geometry is in world units (the node transform was applied): take it back to the
// original node's local frame
const inv = invert([], worldMatrix(onode));
const bprims = bnodes.flatMap((n) => n.getMesh().listPrimitives().map((p) => [n, p]));
let P = [], Nn = [], UV = [], I = [], base = 0;
for (const [n, p] of bprims) {
  const M = multiply([], inv, worldMatrix(n));
  const pos = p.getAttribute('POSITION'), nrm = p.getAttribute('NORMAL'), uv = p.getAttribute('TEXCOORD_0');
  const c = pos.getCount();
  const v = [0, 0, 0], q = [0, 0, 0];
  for (let i = 0; i < c; i++) {
    pos.getElement(i, v);
    P.push(M[0]*v[0]+M[4]*v[1]+M[8]*v[2]+M[12], M[1]*v[0]+M[5]*v[1]+M[9]*v[2]+M[13], M[2]*v[0]+M[6]*v[1]+M[10]*v[2]+M[14]);
    nrm.getElement(i, q);
    // uniform scale + rotation: M's linear part keeps directions; renormalise
    const x = M[0]*q[0]+M[4]*q[1]+M[8]*q[2], y = M[1]*q[0]+M[5]*q[1]+M[9]*q[2], z = M[2]*q[0]+M[6]*q[1]+M[10]*q[2];
    const l = Math.hypot(x, y, z) || 1; Nn.push(x / l, y / l, z / l);
    if (uv) { const t = [0, 0]; uv.getElement(i, t); UV.push(t[0], t[1]); } else UV.push(0, 0);
  }
  const idx = p.getIndices().getArray();
  for (let i = 0; i < idx.length; i++) I.push(idx[i] + base);
  base += c;
}
const buf = oroot.listBuffers()[0];
const acc = (type, arr) => orig.createAccessor().setType(type).setArray(arr).setBuffer(buf);
for (const s of oprim.listSemantics()) oprim.setAttribute(s, null);
oprim.setAttribute('POSITION', acc('VEC3', new Float32Array(P)));
oprim.setAttribute('NORMAL', acc('VEC3', new Float32Array(Nn)));
oprim.setAttribute('TEXCOORD_0', acc('VEC2', new Float32Array(UV)));
oprim.setIndices(acc('SCALAR', base > 65535 ? new Uint32Array(I) : new Uint16Array(I)));

// normal map: keep | highpass | drop
const mat = oprim.getMaterial();
const report = { normal: A.normal };
const ntex = mat?.getNormalTexture();
if (ntex && A.normal === 'drop') {
  mat.setNormalTexture(null);
} else if (ntex && A.normal === 'highpass') {
  const img = sharp(Buffer.from(ntex.getImage()));
  const { data, info } = await img.removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const W = info.width, H = info.height, ch = info.channels;
  // UV coverage mask from the ORIGINAL UVs (same layout as Blender's; it keeps them)
  const mask = new Uint8Array(W * H);
  const U = UV, idx = I;
  for (let t = 0; t < idx.length; t += 3) {
    const xs = [], ys = [];
    for (let k = 0; k < 3; k++) { const j = idx[t + k]; xs.push(U[2 * j] * W - 0.5); ys.push(U[2 * j + 1] * H - 0.5); }
    const x0 = Math.max(0, Math.floor(Math.min(...xs))), x1 = Math.min(W - 1, Math.ceil(Math.max(...xs)));
    const y0 = Math.max(0, Math.floor(Math.min(...ys))), y1 = Math.min(H - 1, Math.ceil(Math.max(...ys)));
    const [ax, bx, cx] = xs, [ay, by, cy] = ys;
    const den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
    if (Math.abs(den) < 1e-12) continue;
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den;
      const l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den;
      const e = -0.02; // a hair of dilation
      if (l1 >= e && l2 >= e && 1 - l1 - l2 >= e) mask[y * W + x] = 1;
    }
  }
  // low-frequency tangent-space xy: masked box-average to a coarse grid, masked gaussian blur, bilinear up
  const f = Math.max(1, Math.round(W / 512)), w = Math.ceil(W / f), h = Math.ceil(H / f);
  const sx = new Float64Array(w * h), sy = new Float64Array(w * h), sm = new Float64Array(w * h);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = y * W + x; if (!mask[i]) continue;
    const j = Math.floor(y / f) * w + Math.floor(x / f);
    sx[j] += data[i * ch] / 127.5 - 1; sy[j] += data[i * ch + 1] / 127.5 - 1; sm[j] += 1;
  }
  const sigma = Math.max(0.5, (A.sigma * W) / f);
  const R = Math.ceil(sigma * 3), ker = [];
  for (let k = -R; k <= R; k++) ker.push(Math.exp(-(k * k) / (2 * sigma * sigma)));
  const blur = (src) => {
    const tmp = new Float64Array(w * h), out = new Float64Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let s = 0; for (let k = -R; k <= R; k++) { const xx = x + k; if (xx >= 0 && xx < w) s += src[y * w + xx] * ker[k + R]; } tmp[y * w + x] = s; }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let s = 0; for (let k = -R; k <= R; k++) { const yy = y + k; if (yy >= 0 && yy < h) s += tmp[yy * w + x] * ker[k + R]; } out[y * w + x] = s; }
    return out;
  };
  const bx = blur(sx), by = blur(sy), bm = blur(sm);
  const lx = new Float32Array(w * h), ly = new Float32Array(w * h);
  for (let j = 0; j < w * h; j++) { const m = bm[j]; if (m > 1e-6) { lx[j] = bx[j] / m; ly[j] = by[j] / m; } }
  const out = Buffer.from(data);
  let s2 = 0, sn = 0, d2 = 0;
  for (let y = 0; y < H; y++) {
    const gy = Math.min(h - 1, Math.max(0, (y + 0.5) / f - 0.5)), y0 = Math.floor(gy), y1 = Math.min(h - 1, y0 + 1), fy = gy - y0;
    for (let x = 0; x < W; x++) {
      const i = y * W + x; if (!mask[i]) continue;
      const gx = Math.min(w - 1, Math.max(0, (x + 0.5) / f - 0.5)), x0 = Math.floor(gx), x1 = Math.min(w - 1, x0 + 1), fx = gx - x0;
      const bil = (a) => (a[y0 * w + x0] * (1 - fx) + a[y0 * w + x1] * fx) * (1 - fy) + (a[y1 * w + x0] * (1 - fx) + a[y1 * w + x1] * fx) * fy;
      const lxv = bil(lx), lyv = bil(ly);
      const nx = data[i * ch] / 127.5 - 1, ny = data[i * ch + 1] / 127.5 - 1;
      let hx = nx - lxv, hy = ny - lyv;
      const q = hx * hx + hy * hy; if (q > 0.98) { const k = Math.sqrt(0.98 / q); hx *= k; hy *= k; }
      const hz = Math.sqrt(Math.max(0, 1 - hx * hx - hy * hy));
      out[i * ch] = Math.round((hx + 1) * 127.5); out[i * ch + 1] = Math.round((hy + 1) * 127.5); out[i * ch + 2] = Math.round((hz + 1) * 127.5);
      s2 += lxv * lxv + lyv * lyv; d2 += hx * hx + hy * hy; sn++;
    }
  }
  const png = await sharp(out, { raw: { width: W, height: H, channels: ch } }).png({ compressionLevel: 6 }).toBuffer();
  ntex.setImage(new Uint8Array(png)).setMimeType('image/png');
  report.lowFreqRmsDeg = Math.asin(Math.min(1, Math.sqrt(s2 / Math.max(1, sn)))) * 180 / Math.PI;
  report.highFreqRmsDeg = Math.asin(Math.min(1, Math.sqrt(d2 / Math.max(1, sn)))) * 180 / Math.PI;
  report.sigmaPx = A.sigma * W;
  report.coverage = sn / (W * H);
  if (A.normalPng) await writeFile(A.normalPng, png);
}
for (const n of oroot.listNodes()) if (n !== onode && !n.getMesh()) {} // untouched
await io.write(A.output, orig);
await writeFile(A.report, JSON.stringify(report));
"""


def run(stage, scene_dir, **args):
    env = dict(os.environ, STRAIGHTEN_ARGS=json.dumps(args))
    code = {'prep': PREP, 'merge': MERGE}[stage]
    r = subprocess.run(['node', '--input-type=module', '-e', code], cwd=scene_dir, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'node {stage} failed:\n{r.stderr[-3000:]}')
    return r.stdout
