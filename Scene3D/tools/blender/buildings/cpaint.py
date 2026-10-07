"""Texture-space paint for the remodelled colony components (README-colony.md, "Component remodel", stage R4).

    paint(maps, zone_names, spec, out, px_per_m) -> {'base', 'orm', 'normal', 'emit' (or None), stats}

maps: tools/blender/hulls/common.bake_maps of the remodelled part, converted to the PART frame (metres, +Y up):
pos, nrm (true normal), zone (material slot, -1 empty), ao, curv. zone_names: the material name per slot (the kit's
paint zones: panel, shell, clad, frame, frame2, ...). Nothing is projected from the fal texture: every texel is
painted from the kit's calibrated colours (lib.MATS: light paint linear ~0.6, gunmetal ~0.04) and procedural layers in
the part frame, so it holds at any distance and lines up with the geometry (correction 41):

  1. zone base colour, roughness, metal (lib.MATS) and per-zone overrides (spec[zone]['color'] sRGB, ...)
  2. plating: courses (horizontal seams every `course` m in y) and joints (every `joint` m along the face's own
     horizontal direction, or round `axis` = (x, z) as arc length for round shells), staggered per course; every plate
     gets its own tone (+-`tone`); seams darken by `dark`; bolt rows along the seams every `bolts` m (normal map)
  3. corrugation (`corr` m pitch: trapezoid sheeting, ribs across the face's horizontal direction; normal map and a
     slight tone), grating bars (zone 'grate', 0.12 m)
  4. PATINA plate tone: the fleet 'hull' set's height map, tri-planar at a 6 m tile (the runtime detail layer's tile)
  5. AO grime in creases, curvature edge wear (light paint: worn primer; dark steel: bare metal and rust), large
     blotches, vertical run-off streaks and rust streaks (`rust`) on walls, rust bleeding from seams and bolt rows
  6. emissive: zones 'hot' (molten, tuyere glass) and 'lamp' (amber lenses)
Normal map (tangent space, glTF): seam grooves, bolt heads, corrugation, grating; from a height map in metres.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'hulls'))
import paint as HP  # noqa: E402  (tools/blender/hulls/paint.py: noise, tri-planar, height -> normal)

SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LUMA = np.array((0.2126, 0.7152, 0.0722), np.float32)

LIGHT = ('panel', 'panel2', 'shell', 'clad', 'clad2', 'concrete', 'concrete2', 'kerb', 'stone', 'frameL')
DARK = ('frame', 'frame2', 'pipeDark', 'grate', 'louvre', 'roof', 'charcoal')
RUST_C = HP.srgb2lin([0.47, 0.27, 0.15])
RUST_D = HP.srgb2lin([0.30, 0.15, 0.08])
EDGE_LIGHT = HP.srgb2lin([0.86, 0.85, 0.82])
EDGE_DARK = HP.srgb2lin([0.40, 0.39, 0.37])


def zone_cfg(name, spec, mats):
    base, kind, rough, metal = mats.get(name, mats['panel'])[:4]
    light = name in LIGHT
    c = {'color': np.asarray(base, np.float32), 'rough': rough, 'metal': metal, 'course': None, 'joint': None, 'axis': None,
         'tone': 0.05 if light else 0.08, 'dark': 0.35, 'bolts': None, 'corr': None, 'rust': 0.35 if light else 0.45,
         'edge': 0.55 if light else 0.8, 'grime': 1.0, 'light': light, 'hot': None, 'kind': kind}
    if name == 'hot':
        c.update({'hot': (np.asarray(base, np.float32), 1.0), 'rust': 0.0, 'edge': 0.0, 'grime': 0.0})
    if name == 'lamp':
        c.update({'hot': (np.asarray(base, np.float32), 0.9), 'rust': 0.0, 'edge': 0.0, 'grime': 0.2})
    if name in ('glassW', 'interior', 'soot', 'seam'):
        c.update({'rust': 0.0, 'edge': 0.0})
    if name == 'grate':
        c.update({'grid': 0.12})
    if name in ('concrete', 'concrete2', 'kerb'):
        c.update({'rust': 0.0, 'edge': 0.35})
    o = dict(spec.get(name, {}))
    if 'color' in o:
        o['color'] = HP.srgb2lin(o['color'])
    c.update(o)
    return c


def face_coords(P, N, axis):
    """(s, t): s along the face's horizontal direction (or the arc round `axis`), t = y on walls; on decks
    (|n.y| > 0.93) s = x, t = z."""
    wall = np.abs(N[:, 1]) < 0.93
    hx, hz = N[:, 2], -N[:, 0]
    hl = np.maximum(np.hypot(hx, hz), 1e-6)
    hx, hz = hx / hl, hz / hl
    flip = np.where(np.abs(hz) > 0.3, hz < 0, hx < 0)
    hx = np.where(flip, -hx, hx); hz = np.where(flip, -hz, hz)
    s = P[:, 0] * hx + P[:, 2] * hz
    if axis is not None:
        dx, dz = P[:, 0] - axis[0], P[:, 2] - axis[1]
        R = np.hypot(dx, dz)
        s = np.where(R > 0.5, np.arctan2(dx, dz) * np.maximum(R, 1.0), s)
    s = np.where(wall, s, P[:, 0])
    t = np.where(wall, P[:, 1], P[:, 2])
    return s.astype(np.float32), t.astype(np.float32), wall


def paint(maps, zone_names, spec, out, px_per_m, mats, size=None):
    """px_per_m: texel density per zone (list, by slot)."""
    pos, nrm, zone = maps['pos'], maps['nrm'], maps['zone'].astype(np.int32)
    S = zone.shape[0]
    cov = zone >= 0
    idx = np.where(cov.ravel())[0]
    P = pos.reshape(-1, 3)[idx].astype(np.float32)
    N = nrm.reshape(-1, 3)[idx].astype(np.float32)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    Zn = zone.ravel()[idx]
    ao = np.clip(HP.upsample(maps['ao'], S).ravel()[idx], 0, 1)
    cv = HP.upsample(maps['curv'], S).ravel()[idx]
    n = len(idx)
    base = np.zeros((n, 3), np.float32)
    rough = np.zeros(n, np.float32)
    metal = np.zeros(n, np.float32)
    height = np.zeros(n, np.float32)
    emit = np.zeros((n, 3), np.float32)
    hm = np.asarray(Image.open(os.path.join(SCENE3D, 'assets/materials/hull/height.webp')).convert('L'), np.float32) / 255
    hmean = float(hm.mean())
    cfgs = [zone_cfg(nm, spec, mats) for nm in zone_names]
    for zi, c in enumerate(cfgs):
        m = np.where(Zn == zi)[0]
        if not len(m):
            continue
        # chunked: 4096^2 atlases hold ~12 M texels
        for k0 in range(0, len(m), 1_500_000):
            mm = m[k0:k0 + 1_500_000]
            p, nn, a, cu = P[mm], N[mm], ao[mm], cv[mm]
            col = np.tile(c['color'][None], (len(mm), 1))
            rg = np.full(len(mm), c['rough'], np.float32)
            mt = np.full(len(mm), c['metal'], np.float32)
            h = np.zeros(len(mm), np.float32)
            s, t, wall = face_coords(p, nn, c['axis'])
            seam = np.zeros(len(mm), np.float32)
            if c['course'] or c['joint']:
                course = c['course'] or 1e3
                joint = c['joint'] or 1e3
                ci = np.floor(t / course)
                dt = np.abs(t - (ci + 0.5) * course)
                dt = course / 2 - dt
                stag = np.where(ci % 2 == 0, 0.0, joint / 2).astype(np.float32)
                ji = np.floor((s + stag) / joint)
                ds = joint / 2 - np.abs((s + stag) - (ji + 0.5) * joint)
                d = np.minimum(dt, ds)
                w = 0.035
                seam = 1 - HP.smooth(w * 0.3, w, d)
                pid = (ci.astype(np.int64) * 7919 + ji.astype(np.int64) * 104729 + zi * 13).astype(np.int64)
                col *= (1 + c['tone'] * (HP.hash3(pid, pid // 7, pid // 13, 11) * 2 - 1))[:, None]
                col *= (1 - c['dark'] * seam)[:, None]
                rg += 0.06 * seam
                h -= 0.006 * (1 - HP.smooth(0.0, w, d))
                if c['bolts']:
                    b = c['bolts']
                    # bolt rows 0.09 m off each course seam and along the joints
                    off = 0.09
                    du = np.abs(dt - off)
                    along = np.abs(((s + 0.5 * b) % b) - 0.5 * b)
                    r1 = np.hypot(du, along)
                    dv = np.abs(ds - off)
                    along2 = np.abs(((t + 0.5 * b) % b) - 0.5 * b)
                    r2 = np.hypot(dv, along2)
                    rb = np.minimum(r1, r2)
                    bolt = 1 - HP.smooth(0.018, 0.03, rb)
                    h += 0.008 * bolt
                    col *= (1 - 0.18 * bolt)[:, None]
            if c['kind'] == 'hazard':      # worn diagonal amber / black stripes (lib 'hazard')
                band = (np.floor((s + t) / 0.35) % 2 == 0)
                col = np.where(band[:, None], col, HP.srgb2lin([0.05, 0.05, 0.05])[None]).astype(np.float32)
            if c['corr']:
                q = np.cos(2 * np.pi * s / c['corr'])
                prof = HP.smooth(-0.35, 0.35, q)           # trapezoid ribs
                h += 0.02 * prof * wall
                col *= (1 + 0.035 * (prof - 0.5) * wall)[:, None]
            if c.get('grid'):
                g = c['grid']
                d1 = np.abs(((p[:, 0] + p[:, 2] + 0.5 * g) % g) - 0.5 * g)
                bar = 1 - HP.smooth(0.012, 0.025, d1)
                h += 0.012 * bar
                col *= (0.75 + 0.35 * bar)[:, None]
            # PATINA plate tone at the runtime tile
            if c['light'] or c['kind'] == 'paint':
                hp = HP.triplanar(hm, p, nn, 6.0)
                col *= (1 + c.get('patina', 0.06) * (hp / hmean - 1))[:, None]
            # AO grime
            g = c['grime']
            col *= (1 - 0.35 * g * (1 - a))[:, None]
            crease = g * HP.smooth(0.85, 0.45, a)
            gcol = col * HP.srgb2lin([0.40, 0.37, 0.33])[None] / 0.55
            col = col * (1 - 0.6 * crease[:, None]) + gcol * 0.6 * crease[:, None]
            rg += 0.12 * crease
            # blotches and run-off streaks
            blot = HP.fbm(p, 0.08, 3, seed=1 + zi)
            col *= (1 + c.get('blot', 0.07) * (blot - 0.5) * 2)[:, None]
            st = HP.fbm(p * np.array([1.0, 0.06, 1.0], np.float32), 1.4, 3, seed=9)
            streak = wall * HP.smooth(0.5, 0.7, st) * 0.16 * g
            col *= (1 - streak)[:, None]
            # ground dirt: walls darken and warm toward the slab (splash, dust)
            gd = wall * HP.smooth(2.2, 0.0, p[:, 1]) * (0.55 if c['light'] else 0.3) * g
            col = col * (1 - 0.45 * gd[:, None]) + HP.srgb2lin([0.33, 0.29, 0.24])[None] * 0.45 * gd[:, None]
            # rust: streaks down the walls (stronger under seams and in shadowed corners), seams bleeding, chips
            if c['rust'] > 0:
                rs = HP.fbm(p * np.array([1.0, 0.09, 1.0], np.float32), 0.9, 3, seed=17 + zi)
                patch = HP.fbm(p, 0.35, 3, seed=23 + zi)
                rmask = wall * HP.smooth(0.5, 0.68, rs) * (0.35 + 0.65 * HP.smooth(0.38, 0.62, patch))
                rmask = np.maximum(rmask, seam * HP.smooth(0.45, 0.7, patch) * 0.8)
                rmask = np.clip(rmask * c['rust'] * (0.75 + 0.5 * (1 - a)), 0, 1)
                rc = RUST_C if c['light'] else RUST_D
                tint = rc[None] * (0.85 + 0.3 * patch[:, None])
                if c['light']:
                    col = col * (1 - 0.55 * rmask[:, None]) + tint * 0.55 * rmask[:, None]
                else:
                    col = col * (1 - 0.7 * rmask[:, None]) + tint * 0.7 * rmask[:, None]
                rg = rg * (1 - rmask) + 0.85 * rmask
            # edge wear on convex edges (not creases)
            if c['edge'] > 0:
                edge = HP.smooth(0.06, 0.3, cu) * HP.smooth(0.75, 0.95, a)
                chip = HP.fbm(p, 2.4, 3, seed=5)
                wear = edge * HP.smooth(0.32, 0.55, chip) * c['edge']
                ec = EDGE_LIGHT if c['light'] else EDGE_DARK
                if not c['light'] and c['rust'] > 0:
                    rr = HP.smooth(0.5, 0.7, HP.fbm(p, 1.1, 2, seed=41))
                    ec = ec[None] * (1 - rr[:, None]) + RUST_C[None] * rr[:, None]
                col = col * (1 - wear[:, None]) + (ec if ec.ndim == 2 else ec[None]) * wear[:, None]
                mt = np.maximum(mt, wear * (0.15 if c['light'] else 0.6))
                rg -= 0.15 * wear
            if c['hot'] is not None and zone_names[zi] == 'hot':
                # molten metal / furnace glow (v4 r2): a deep orange body under the tone curve's knee with hotter yellow
                # cores and a dark cooling crust broken by glowing cracks (one flat bright orange tone-mapped to a flat
                # salmon slab at the building camera). Hue goes yellow with heat, never toward pink.
                f1 = HP.fbm(p, 0.9, 3, seed=3)
                core = HP.smooth(0.5, 0.78, f1)
                deep = HP.srgb2lin([0.86, 0.30, 0.04])
                bright = HP.srgb2lin([1.0, 0.78, 0.36])
                e = deep[None] * (1 - core[:, None]) + bright[None] * core[:, None]
                cr = float(c.get('crust', 0.35))
                if cr > 0:
                    cells = HP.fbm(p, 2.6, 3, seed=31)
                    crack = HP.smooth(0.03, 0.0, np.abs(cells - 0.5))     # thin bright seams between crust plates
                    crust = HP.smooth(0.42, 0.62, HP.fbm(p, 0.7, 2, seed=37)) * cr * (1 - crack)
                    e = e * (1 - 0.85 * crust[:, None]) + bright[None] * 0.6 * crack[:, None] * crust[:, None]
                else:
                    crust = np.zeros(len(mm), np.float32)
                emit[mm] = np.clip(e * c['hot'][1], 0, 1)
                col = np.clip(deep[None] * 0.12 * (1 - crust[:, None]) + HP.srgb2lin([0.10, 0.08, 0.07])[None] * crust[:, None], 0, 1)
                rg = 0.55 + 0.35 * crust
            elif c['hot'] is not None:
                hc, k = c['hot']
                fl = 0.8 + 0.4 * HP.fbm(p, 1.5, 2, seed=3)
                emit[mm] = np.clip(hc[None] * fl[:, None] * k, 0, 1)
                # a dark, hot-tinted albedo: the light comes from the emission (a light albedo also takes the cool dusk
                # fill and tone-maps to salmon pink)
                col = np.clip(hc[None] * fl[:, None] * 0.18, 0, 1)
            base[mm] = col
            rough[mm] = rg
            metal[mm] = mt
            height[mm] = h
    stats = {}
    # paint check (calibration): surface-weighted luminance of the light paint (UVs at one density = area-weighted)
    Y = base @ LUMA
    lightz = np.isin(Zn, [i for i, c in enumerate(cfgs) if c['light']])
    stats['Y_all'] = round(float(Y.mean()), 4)
    stats['Y_light'] = round(float(Y[lightz].mean()), 4) if lightz.any() else None
    stats['light_share'] = round(float(lightz.mean()), 3)
    fill = cfgs[0]['color']
    img = np.tile(fill[None], (S * S, 1)).astype(np.float32)
    img[idx] = base
    col8 = (HP.lin2srgb(img).reshape(S, S, 3) * 255 + 0.5).astype(np.uint8)
    orm = np.zeros((S * S, 3), np.float32)
    orm[:, 0] = 1.0
    # v4 r2: the baked AO (1.2 m) in the glTF occlusion channel as well: three applies it to the indirect light only (the
    # studio's environment and fill), so recesses, the undersides of decks and the feet of walls darken on the shadow
    # side where the grime in the base colour alone left them flat (the runtime GTAO adds the building-scale contact)
    occ = np.clip(0.18 + 0.82 * ao, 0, 1)
    orm[idx, 0] = np.where(np.isin(Zn, [i for i, c in enumerate(cfgs) if c['hot'] is not None]), 1.0, occ)
    orm[:, 1] = 0.6
    orm[idx, 1] = np.clip(rough, 0.05, 1)
    orm[idx, 2] = np.clip(metal, 0, 1)
    orm8 = (orm.reshape(S, S, 3) * 255 + 0.5).astype(np.uint8)
    hh = np.zeros(S * S, np.float32)
    hh[idx] = height
    cv2 = np.zeros(S * S, bool); cv2[idx] = True
    # px per metre per texel (zones carry different UV densities: remodel.UV_WEIGHT)
    ppm = np.full(S * S, float(max(px_per_m)), np.float32)
    ppm[idx] = np.asarray(px_per_m, np.float32)[Zn]
    nimg = HP.height_to_normal(hh.reshape(S, S), cv2.reshape(S, S), ppm.reshape(S, S), 1.0)
    os.makedirs(out, exist_ok=True)
    res = {'base': os.path.join(out, 'base.png'), 'orm': os.path.join(out, 'orm.png'), 'normal': os.path.join(out, 'normal.png'), 'emit': None, 'stats': stats}
    Image.fromarray(col8).save(res['base'])
    Image.fromarray(orm8).save(res['orm'])
    Image.fromarray(nimg).save(res['normal'])
    if emit.any():
        em = np.zeros((S * S, 3), np.float32)
        em[idx] = emit
        Image.fromarray((HP.lin2srgb(em).reshape(S, S, 3) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, 'emit.png'))
        res['emit'] = os.path.join(out, 'emit.png')
    Image.fromarray(col8).resize((1024, 1024)).save(os.path.join(out, 'base-1k.jpg'), quality=88)
    return res
