"""V-31 wheeled 4x4 (ground unit "jeep" chassis): clean hard-surface body, rebuilt from the approved concept A
(style-library/styles/cqs-fleet/images/spread-vehicle-r1-A.jpg) and measurements of the fal / Tripo H3.1
blueprint (assets/ships/raw/vehicle.glb), built to the brief's true size (briefs/vehicle.md): body 6.5 x 2.6
x 2.5 m, weapon station to about 2.9 m, 1.15 m tyres.

    <blender-python> tools/blender/hulls/vehicle.py <workdir> [--stage all|model|paint]
                     [--tex 2048] [--ao 1024] [--threads 4] [--no-cull] [--preview] [--bake]

Stages: model -> <workdir>/vehicle-hull.blend (+ maps.npz with --bake); paint -> base / orm / normal PNGs
(vehicle_paint.py over paint.py) and <workdir>/vehicle-hull.glb (node 'hull', vehicle frame, ground at y 0,
not re-centred). assemble.py adds the kit parts (specs/vehicle-v3.json from vehicle_spec.py): the four
wheels and suspension corners, the remote weapon station, roof hatches, doors, marker lamps, the roof vent
and the foil box. Dimension tables: vehicle_dims.py (shared with vehicle_spec.py).

Vehicle frame = ship frame: metres, front +Z, up +Y, left +X.

Layout: a chamfered octagonal body (flat roof 2.5 m, upper chamfers, vertical flanks, a gunmetal belly band
and lower chamfers to a 0.55 m belly) running unbroken from the tail to the cab brow at z 1.4; a raked
windscreen with two armoured panes down to a sloping bonnet and the nose face at z 3.25, framed by a
gunmetal octagonal collar; faceted wheel arches cut to a wheelhouse wall at x 0.84, with fender flares;
a gunmetal end frame round the tail; a small louvred vent above each rear arch.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import common as K  # noqa: E402
from common import V, Z, Volume  # noqa: E402

import vehicle_dims as D  # noqa: E402


def prof(z):
    return K.interp_table(D.ST, z, D.COLS)


def half_profile(z):
    p = prof(z)
    return [(0.0, p['T']), (p['TX'], p['T']), (p['W'], p['FT']), (p['W'], p['FM']), (p['W'], p['FB']), (p['BX'], p['B']), (0.0, p['B'])]


SEG_ZONE = ['deck', 'paint', 'paint', 'dark', 'dark', 'belly']


def ring_zones():
    segs = len(SEG_ZONE)
    return [SEG_ZONE[j] if j < segs else SEG_ZONE[2 * segs - 1 - j] for j in range(2 * segs)]


def section(z):
    return K.mirror_half(half_profile(z))


# ------------------------------------------------------------------------------------------
# volumes
# ------------------------------------------------------------------------------------------
def windscreen_frame(x):
    """Centre, outward normal and up (along the slope) of a windscreen pane at x."""
    a = V((x, D.ST[3][1]['T'], D.ST[3][0]))       # brow
    b = V((x, D.ST[4][1]['T'], D.ST[4][0]))       # base
    c = (a + b) / 2
    along = (a - b).normalized()                  # up the slope
    n = V((0, along.z, -along.y)).normalized()
    if n.y < 0:
        n = -n
    return c, n, along


def body():
    vol = Volume('body', bevel=0.035)
    bm = vol.bm
    rings = [[V((x, y, z)) for x, y in section(z)] for z, _ in D.ST]
    grid, caps = K.loft(bm, rings, zone=Z['paint'])
    zones = ring_zones()
    for row in grid:
        for j, f in enumerate(row):
            if f is not None:
                f.material_index = Z[zones[j]]
    caps[0].material_index = Z['paint']      # tail face (tail door, lamps)
    caps[1].material_index = Z['recess']     # nose face (behind the collar)
    K.solid(bm)
    cut = vol.cutters
    # wheel arches -> wheelhouses (inner wall at x WELL_X)
    for za in D.AXLES:
        pts = [(za + dz, y) for dz, y in D.ARCH] + [(za + D.ARCH[-1][0], -0.5), (za + D.ARCH[0][0], -0.5)]
        for sx in (1, -1):
            K.prism(cut, pts, 'zy', sx * D.WELL_X, sx * 2.0, zone=Z['recess'])
    # windscreen panes (true recesses), glass added after the cut
    W = D.WINDSCREEN
    for x in W['xs']:
        c, n, up = windscreen_frame(x)
        K.oriented_prism(cut, K.chamfer_rect(0, 0, W['w'], W['h'], 0.05), c, n, up, -W['depth'], 0.6, zone=Z['recess'])
        vol.adds.append(('glass', lambda bm, c=c, n=n, up=up: K.plate(bm, c - n * (W['depth'] - 0.004), n, up, W['w'] - 0.04, W['h'] - 0.04, 0.012, zone=Z['glass'], back=0.02)))
    # side panes on the cab flank and the louvred tail vents
    S = D.SIDE_PANE
    VT = D.SIDE_VENT
    for sx in (1, -1):
        n = V((sx, 0, 0))
        c = V((sx * prof(S['z'])['W'], S['y'], S['z']))
        K.oriented_prism(cut, K.chamfer_rect(0, 0, S['w'], S['h'], 0.04), c, n, (0, 1, 0), -S['depth'], 0.6, zone=Z['recess'])
        vol.adds.append(('glass', lambda bm, c=c, n=n: K.plate(bm, c - n * (S['depth'] - 0.004), n, (0, 1, 0), S['w'] - 0.04, S['h'] - 0.04, 0.012, zone=Z['glass'], back=0.02)))
        cv = V((sx * prof(VT['z'])['W'], VT['y'], VT['z']))
        K.oriented_prism(cut, K.chamfer_rect(0, 0, VT['w'], VT['h'], 0.04), cv, n, (0, 1, 0), -VT['depth'], 0.6, zone=Z['recess'])
        for k in range(6):
            y = VT['y'] - VT['h'] / 2 + 0.06 + k * 0.077
            vol.adds.append(('fins', lambda bm, y=y, sx=sx, cv=cv: K.box(bm, (cv.x - sx * 0.06, y, cv.z), (0.012, 0.075, VT['w'] - 0.04), R=_fin_R(sx), zone=Z['fin'])))
    # nose: recessed panel inside the collar, two horizontal intake slots with bars
    C = D.COLLAR
    K.oriented_prism(cut, K.chamfer_rect(0, 0, C['wi'], C['hi'], C['ci']), V((0, C['y'], D.Z_NOSE)), (0, 0, 1), (0, 1, 0), -0.1, 0.6, zone=Z['recess'])
    for dy in (0.11, -0.11):
        vol.adds.append(('bars', lambda bm, dy=dy: K.box(bm, (0, C['y'] + dy, D.Z_NOSE - 0.07), (C['wi'] - 0.3, 0.12, 0.06), zone=Z['dark'])))
    vol.adds.append(('bars', lambda bm: K.box(bm, (0, C['y'], D.Z_NOSE - 0.075), (0.06, C['hi'] - 0.04, 0.05), zone=Z['dark'])))
    return vol


def _fin_R(sx):
    """Louvre fin: a thin plate in the (y, z) plane tilted 40 degrees, its lower edge out (sheds rain)."""
    a = 40 * K.DEG * sx
    return Matrix(((math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0), (0, 0, 1)))


def collar():
    """Gunmetal chamfered octagonal frame round the nose face (the fleet's bow collar language)."""
    C = D.COLLAR
    v = Volume('collar', bevel=0.03)
    o = K.chamfer_rect(0, C['y'], C['w'], C['h'], C['c'])
    i = K.chamfer_rect(0, C['y'], C['wi'], C['hi'], C['ci'])
    o0 = K.offset_poly(o, -0.04)
    K.loft(v.bm, [K.ring3(o0, 'xy', C['z0']), K.ring3(o, 'xy', C['z0'] + 0.08), K.ring3(o, 'xy', C['z1'] - 0.04), K.ring3(K.offset_poly(o, -0.04), 'xy', C['z1']),
                  K.ring3(i, 'xy', C['z1']), K.ring3(i, 'xy', C['z0']), K.ring3(o0, 'xy', C['z0'])], cap0=False, cap1=False, zone=Z['dark'])
    K.solid(v.bm)
    return v


def tail_frame():
    """Gunmetal end frame round the tail face (the concept's dark rear corners)."""
    T = D.TAILFRAME
    v = Volume('tail_frame', bevel=0.025)
    s = section(-3.17)
    o = K.offset_poly(s, 0.03)
    i = K.offset_poly(s, -T['t'])
    K.loft(v.bm, [K.ring3(o, 'xy', T['z0']), K.ring3(o, 'xy', T['z1']), K.ring3(i, 'xy', T['z1']), K.ring3(i, 'xy', T['z0']), K.ring3(o, 'xy', T['z0'])],
           cap0=False, cap1=False, zone=Z['dark'])
    K.solid(v.bm)
    return v


def flares():
    """Fender flares over each arch top, from the shoulders up (clear of the doors)."""
    F = D.FLARE
    v = Volume('flares', bevel=0.02)
    arch_top = D.ARCH[1:5]
    for za in D.AXLES:
        pts = [(za + dz, y) for dz, y in arch_top]
        out = K.offset_open(pts, F['w'], left=True)
        poly = pts + list(reversed(out))
        for sx in (1, -1):
            K.prism(v.bm, poly, 'zy', sx * F['x0'], sx * F['x1'], zone=Z['trim'])
    K.solid(v.bm)
    return v


def skirts():
    """Belly skid plate, door step plates, rear bumper with a tow pintle, front lower guard."""
    v = Volume('skirts', bevel=0.02)
    K.plate(v.bm, (0, 0.55, 0.0), (0, -1, 0), (0, 0, 1), 1.0, 4.0, 0.04, ch=0.02, back=0.05, zone=Z['belly'])
    for sx in (1, -1):
        for zc in D.DOORS:
            # step plate under each door, on the lower chamfer
            K.box(v.bm, (sx * 0.98, 0.66, zc), (0.26, 0.04, 0.62), zone=Z['dark'])
            for dz in (-0.27, 0.27):
                K.box(v.bm, (sx * 0.9, 0.71, zc + dz), (0.12, 0.1, 0.05), zone=Z['dark'])
    # rear bumper bar and tow pintle
    K.box(v.bm, (0, 0.95, -3.33), (2.0, 0.16, 0.14), zone=Z['dark'])
    K.box(v.bm, (0, 0.84, -3.42), (0.16, 0.1, 0.12), zone=Z['metal'])
    # front lower guard under the collar
    K.box(v.bm, (0, 0.98, 3.22), (1.5, 0.12, 0.2), zone=Z['dark'])
    K.solid(v.bm)
    return v


def roof_plates():
    """Raised roof appliqué panels between the fittings (catch a highlight, break the long roof)."""
    v = Volume('roof_plates', bevel=0.015)
    for zc, L in ((0.3, 2.2), (-2.05, 0.5)):
        for sx in (1, -1):
            K.plate(v.bm, (sx * 0.62, D.ROOF, zc), (0, 1, 0), (0, 0, 1), 0.34, L, 0.03, ch=0.012, back=0.03, zone=Z['deck'])
    K.solid(v.bm)
    return v


def grab(bm, a, b, n, h=0.1, r=0.018):
    a, b, n = V(a), V(b), V(n).normalized()
    K.cyl(bm, a - n * 0.03, a + n * h, r, n=8, zone=Z['metal'])
    K.cyl(bm, b - n * 0.03, b + n * h, r, n=8, zone=Z['metal'])
    K.cyl(bm, a + n * h - (b - a).normalized() * r, b + n * h + (b - a).normalized() * r, r, n=8, zone=Z['metal'])


def grabs():
    g = Volume('grabs', bevel=0.0, cull=False)
    up = (0, 1, 0)
    for sx in (1, -1):
        # roof edge rails beside the hatches and aft of the weapon station (low grab rails, not 1.1 m rails)
        grab(g.bm, (sx * 0.74, D.ROOF, 0.0), (sx * 0.74, D.ROOF, 1.1), up, h=0.12)
        grab(g.bm, (sx * 0.74, D.ROOF, -2.85), (sx * 0.74, D.ROOF, -1.95), up, h=0.12)
        # vertical grab handles beside each door (handle side)
        for zc in D.DOORS:
            x = sx * D.ST[2][1]['W']
            grab(g.bm, (x, D.DOOR_Y - 0.35, zc + 0.6), (x, D.DOOR_Y + 0.35, zc + 0.6), (sx, 0, 0), h=0.07)
    p = prof(2.25)
    grab(g.bm, (0.45, p['T'] - 0.02, 2.2), (-0.45, p['T'] - 0.02, 2.2), (0, 1, 0.12), h=0.1)
    # tail: grab handles beside the tail door
    for sx in (1, -1):
        grab(g.bm, (sx * 0.58, 1.2, -3.17), (sx * 0.58, 1.9, -3.17), (0, 0, -1), h=0.07)
    return g


def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    vols = [body(), collar(), tail_frame(), flares(), skirts(), roof_plates(), grabs()]
    obs = []
    for v in vols:
        ob = v.to_object()
        ob['bevel'] = v.bevel
        ob['angle'] = v.angle
        ob['cull'] = v.cull
        ob['small'] = v.name in SMALL
        if len(v.cutters.faces):
            cut = v.to_object(v.cutters, v.name + '_cut')
            K.boolean(ob, cut)
            bpy.data.objects.remove(cut)
        obs.append(ob)
        for nm, fn in v.adds:
            bm = bmesh.new()
            fn(bm)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            vv = Volume(f'{v.name}_{nm}')
            ob2 = vv.to_object(bm, f'{v.name}_{nm}')
            ob2['bevel'] = 0.006 if nm in ('fins', 'glass') else 0.012
            ob2['angle'] = 30.0
            ob2['cull'] = False
            ob2['small'] = nm in ('fins', 'bars')
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        K.cull_hidden(obs)
    for ob in obs:
        K.finish(ob, ob['bevel'], ob['angle'])
        a = ob.data.attributes.new('small', 'INT', 'FACE')
        a.data.foreach_set('value', [1 if ob.get('small') else 0] * len(ob.data.polygons))
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


SMALL = {'grabs'}
SMALL_UV = 0.4


def unwrap(ob, angle=50.0, margin=0.002):
    """As fighter.unwrap: the fine parts (grab rails, louvre fins, nose bars) at SMALL_UV of the body's
    texel density, so the plated faces get the texels."""
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle * K.DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    small = np.zeros(len(me.polygons), np.int32)
    me.attributes['small'].data.foreach_get('value', small)
    uv = me.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get('uv', co)
    co = co.reshape(-1, 2)
    for p in me.polygons:
        if small[p.index]:
            co[list(p.loop_indices)] *= SMALL_UV
    uv.foreach_set('uv', co.ravel())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = me.uv_layers.active.data
    a3 = {0: 0.0, 1: 0.0}; a2 = {0: 0.0, 1: 0.0}
    for p in me.polygons:
        k = int(small[p.index])
        a3[k] += p.area
        pts = [uv[i].uv for i in p.loop_indices]
        a2[k] += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
    return {'surface_m2': round(a3[0] + a3[1], 1), 'small_m2': round(a3[1], 1), 'uv_fill': round(a2[0] + a2[1], 3),
            'px_per_m_at_4096': round(4096 * math.sqrt(a2[0] / a3[0]), 1), 'small_px_per_m_at_4096': round(4096 * math.sqrt(a2[1] / max(a3[1], 1e-6)), 1)}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, 'vehicle-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 2048))
    if stage in ('all', 'model'):
        ob = build({'no_cull': '--no-cull' in argv})
        info = unwrap(ob)
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        if '--preview' in argv:
            import preview
            preview.shots(ob, os.path.join(work, 'preview'), views=(opt('--views').split(',') if opt('--views') else None))
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
        if stage == 'model' and '--bake' not in argv:
            return
        m = K.bake_maps(ob, size=tex, ao_size=int(opt('--ao', 1024)), ao_dist=0.4, curv_r=0.025, threads=int(opt('--threads', 4)))
        np.savez_compressed(maps, **m)
    if stage in ('all', 'paint'):
        import vehicle_paint
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = dict(np.load(maps))
        spec = vehicle_paint.spec()
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * tex / 4096
        base, orm = vehicle_paint.paint(m, spec=spec, out=work)
        K.set_final_material(ob, base, orm, normal_png=spec.get('_normal_png'))
        glb = os.path.join(work, 'vehicle-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()
