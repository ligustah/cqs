// Split a GLB into the artifact package's tiered layout (used by build-artifact.mjs; read by src/lib/glbship.js loadB64):
//   <name>.glb.shared.b64.txt   the geometry (meshopt buffers, bit-identical) and every texture all tiers use unchanged
//   <name>.glb[.<tier>].b64.txt  per tier: a small GLB whose JSON describes the whole model and whose BIN holds that
//                                tier's own textures (downscaled copies, or originals another tier does not use)
//   assets/tex/<hash>.webp       textures of --ext px or more as plain WebP files (no base64 overhead), shared by hash
// The runtime decodes shared + tier into one GLB: BIN = shared bytes, then the tier's bytes (the tier JSON's offsets
// already point there). Tier 'full' is desktop: original textures (capped at its own cap, if given). A tier may drop
// nodes (a building's small dressing parts on the phone): they are left out of the scene graph in its JSON only, and the
// split fails if that moves the bounding box the runtime frames on.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { NodeIO, getBounds } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const ALIGN = 16;
const pad = (n, a = ALIGN) => Math.ceil(n / a) * a;

export function readGLB(buf) {
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error('not a GLB');
  const jl = buf.readUInt32LE(12);
  const json = JSON.parse(buf.subarray(20, 20 + jl).toString('utf8'));
  const bo = 20 + jl;
  const bin = bo < buf.length ? buf.subarray(bo + 8, bo + 8 + buf.readUInt32LE(bo)) : Buffer.alloc(0);
  return { json, bin };
}

export function writeGLB(json, bin) {
  let j = Buffer.from(JSON.stringify(json), 'utf8');
  j = Buffer.concat([j, Buffer.alloc(pad(j.length, 4) - j.length, 0x20)]);
  const b = Buffer.concat([bin, Buffer.alloc(pad(bin.length, 4) - bin.length)]);
  const head = Buffer.alloc(12);
  head.writeUInt32LE(0x46546c67, 0); head.writeUInt32LE(2, 4); head.writeUInt32LE(12 + 8 + j.length + 8 + b.length, 8);
  const ch = (len, type) => { const c = Buffer.alloc(8); c.writeUInt32LE(len, 0); c.writeUInt32LE(type, 4); return c; };
  return Buffer.concat([head, ch(j.length, 0x4e4f534a), j, ch(b.length, 0x004e4942), b]);
}

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });

/** Bounding box and triangles of the default scene, before and after dropping the named nodes. */
async function dropCheck(path, drop) {
  await MeshoptDecoder.ready;
  const doc = await io.read(path);
  const scene = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
  const tris = () => { let n = 0; scene.traverse((nd) => { const m = nd.getMesh(); if (m) for (const p of m.listPrimitives()) n += (p.getIndices() || p.getAttribute('POSITION')).getCount() / 3; }); return n; };
  const box = () => { const b = getBounds(scene); return [...b.min, ...b.max].map((v) => +v.toFixed(3)); };
  const before = { tris: tris(), box: box() };
  for (const n of doc.getRoot().listNodes()) if (drop.includes(n.getName())) n.dispose();
  return { before, after: { tris: tris(), box: box() } };
}

/**
 * tiers: [{ name: 'full' | 'lite' | 'mini', cap: max texture px (0 = keep), roleCaps: { metallicRoughness: px, ... },
 *   drop: [node names] }]; roleCaps caps the images a material uses in that role (baseColor, metallicRoughness, normal,
 *   occlusion, emissive)
 * ext: textures of at least this many px (after the tier's cap) go out as plain WebP files.
 * Returns { shared: Buffer, tiers: { name: Buffer (GLB) }, tex: { hash: Buffer (webp) }, report }.
 */
export async function splitGLB(path, tiers, { ext = 2048, quality = 85 } = {}) {
  const { json, bin } = readGLB(await readFile(path));
  const views = json.bufferViews;
  const imageView = new Map((json.images || []).map((im, i) => [im.bufferView, i]));
  // texture versions per tier: originals when within the cap, else a downscaled WebP (as tools/lite-glb.mjs made them)
  const resized = new Map(); // `${img}|${cap}` -> Buffer
  const meta = await Promise.all((json.images || []).map(async (im) => {
    const v = views[im.bufferView];
    const bytes = bin.subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength);
    const m = await sharp(bytes).metadata();
    return { bytes, w: m.width, h: m.height, mime: im.mimeType };
  }));
  // material roles of each image (roleCaps)
  const roles = (json.images || []).map(() => new Set());
  const srcOf = (ti) => { const t = json.textures?.[ti]; return t?.extensions?.EXT_texture_webp?.source ?? t?.source; };
  for (const m of json.materials || []) {
    const pb = m.pbrMetallicRoughness || {};
    for (const [role, ref] of [['baseColor', pb.baseColorTexture], ['metallicRoughness', pb.metallicRoughnessTexture], ['normal', m.normalTexture], ['occlusion', m.occlusionTexture], ['emissive', m.emissiveTexture]]) {
      const i = ref ? srcOf(ref.index) : undefined;
      if (i !== undefined) roles[i].add(role);
    }
  }
  const capOf = (t, i) => {
    let cap = t.cap || 0;
    for (const r of roles[i]) { const c = t.roleCaps?.[r]; if (c && (!cap || c < cap)) cap = c; }
    return cap;
  };
  const version = async (i, cap) => {
    const m = meta[i];
    if (!cap || Math.max(m.w, m.h) <= cap) return { key: `${i}|0`, bytes: m.bytes, w: m.w, h: m.h, mime: m.mime };
    const k = `${i}|${cap}`;
    if (!resized.has(k)) resized.set(k, await sharp(m.bytes).resize(cap, cap, { fit: 'inside', withoutEnlargement: true }).webp({ quality }).toBuffer({ resolveWithObject: true }));
    const r = resized.get(k);
    return { key: k, bytes: r.data, w: r.info.width, h: r.info.height, mime: 'image/webp' };
  };
  // per tier and image: the version it uses, and where that version lives
  const use = {}; // tier -> [version]
  for (const t of tiers) use[t.name] = await Promise.all((json.images || []).map((_, i) => version(i, capOf(t, i))));
  const hashOf = (b) => createHash('sha256').update(b).digest('hex').slice(0, 16);
  const tex = {};
  const usedBy = new Map(); // version key -> Set(tier)
  for (const t of tiers) for (const v of use[t.name]) { if (!usedBy.has(v.key)) usedBy.set(v.key, new Set()); usedBy.get(v.key).add(t.name); }
  const external = (v) => Math.max(v.w, v.h) >= ext;
  const inShared = (v) => !external(v) && usedBy.get(v.key).size === tiers.length;

  // shared BIN: every non-image range of buffer 0 (bufferViews and meshopt payloads), then the shared textures
  const parts = [];
  let off = 0;
  const place = (bytes) => { const at = off; parts.push([at, bytes]); off = pad(at + bytes.length); return at; };
  const geo = views.map((v, vi) => {
    if (imageView.has(vi)) return null;
    const out = {};
    if ((v.buffer ?? 0) === 0) out.view = place(bin.subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength));
    const mo = v.extensions?.EXT_meshopt_compression;
    if (mo && (mo.buffer ?? 0) === 0) out.meshopt = place(bin.subarray(mo.byteOffset || 0, (mo.byteOffset || 0) + mo.byteLength));
    return out;
  });
  const sharedAt = new Map();
  for (const t of tiers) for (const v of use[t.name]) if (inShared(v) && !sharedAt.has(v.key)) sharedAt.set(v.key, place(v.bytes));
  const shared = Buffer.alloc(off);
  for (const [at, b] of parts) b.copy(shared, at);

  const out = {};
  const report = [];
  for (const t of tiers) {
    const j = structuredClone(json);
    const tparts = [];
    let toff = 0;
    const tplace = (bytes) => { const at = toff; tparts.push([at, bytes]); toff = pad(at + bytes.length); return shared.length + at; };
    j.bufferViews.forEach((v, vi) => {
      const g = geo[vi];
      if (!g) return;
      if (g.view !== undefined) v.byteOffset = g.view;
      if (g.meshopt !== undefined) v.extensions.EXT_meshopt_compression.byteOffset = g.meshopt;
    });
    let texBytes = 0, extCount = 0, maxPx = 0;
    use[t.name].forEach((v, i) => {
      const im = j.images[i];
      const bv = j.bufferViews[im.bufferView];
      maxPx = Math.max(maxPx, v.w, v.h);
      if (external(v)) {
        const h = hashOf(v.bytes);
        tex[h] = v.bytes;
        delete im.bufferView;
        im.uri = `assets/tex/${h}.webp`;
        im.mimeType = v.mime;
        // the image's old view stays (indices do not move) as a 1-byte stub nothing reads
        Object.assign(bv, { byteOffset: 0, byteLength: 1 });
        extCount++;
      } else {
        bv.byteOffset = sharedAt.has(v.key) ? sharedAt.get(v.key) : tplace(v.bytes);
        bv.byteLength = v.bytes.length;
        im.mimeType = v.mime;
      }
      texBytes += v.bytes.length;
    });
    const tbin = Buffer.alloc(toff);
    for (const [at, b] of tparts) b.copy(tbin, at);
    j.buffers[0].byteLength = shared.length + tbin.length;
    j.extras = { ...(j.extras || {}), sharedByteLength: shared.length };
    let check = null;
    if (t.drop?.length) {
      const drop = new Set(t.drop);
      const gone = new Set(j.nodes.map((n, i) => (drop.has(n.name) ? i : -1)).filter((i) => i >= 0));
      for (const n of j.nodes) if (n.children) n.children = n.children.filter((c) => !gone.has(c));
      for (const s of j.scenes) s.nodes = s.nodes.filter((c) => !gone.has(c));
      check = await dropCheck(path, t.drop);
      if (check.before.box.some((x, i) => Math.abs(x - check.after.box[i]) > 0.01)) throw new Error(`${path} .${t.name}: dropping ${t.drop} moved the bbox ${check.before.box} -> ${check.after.box}`);
    }
    out[t.name] = writeGLB(j, tbin);
    report.push({ tier: t.name, cap: t.cap || 0, maxPx, ownBytes: tbin.length, external: extCount, texBytes, ...(check ? { tris: [check.before.tris, check.after.tris] } : {}) });
  }
  return { shared, tiers: out, tex, report };
}
