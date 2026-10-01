"""Shipyard placement spec and module data, from the dimension tables and the kits' anchors.

    python3 tools/blender/buildings/shipyard_spec.py
      -> tools/blender/specs/shipyard-v1.json     (assemble.py: every kit part in the yard, YARD frame)
      -> src/buildings/shipyard.js                (the block between the GENERATED markers: lights,
                                                   lamps, slits, fixtures, floods, berth / build state)

Plain Python (no bpy). Reads shipyard_dims.py, tools/blender/specs/shipyard-dd12.json
(shipyard_measure.py) and assets/parts-yard/parts.json (yard_kit.py anchors).

Kit parts used at true size (never scaled; corrections 6, 32): fleet kit door (1 x 2 m), pane,
vent, ladder, rail (3 m stretched segments as on the ships), container (ISO 20 ft), floodlight,
bell-XL (x1.106, the destroyer's own centre bell); yard kit gantry, crane-A / crane-B, hall,
floodMast, scaffold-S/M/L, truck, forklift, worker, keelBlock (scaled in y to the measured
hull bottom), bollard.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shipyard_dims as D  # noqa: E402

SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SPEC = os.path.join(HERE, '..', 'specs', 'shipyard-v1.json')
MODULE = os.path.join(SCENE3D, 'src', 'buildings', 'shipyard.js')
DD = json.load(open(os.path.join(HERE, '..', 'specs', 'shipyard-dd12.json')))
YK = json.load(open(os.path.join(SCENE3D, 'assets', 'parts-yard', 'parts.json')))['parts']
HULLINFO = os.environ.get('SHIPYARD_HULL_JSON')  # shipyard.py's <work>/shipyard-hull.json (bell profile)


def r3(v):
    return [round(float(a), 3) for a in v]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


class Place:
    """A +Y yard placement: part frame -> yard frame (x along `along`, y up, z = x cross y)."""

    def __init__(self, at, along=(1, 0, 0)):
        a = (along[0], 0.0, along[2])
        L = math.hypot(a[0], a[2])
        self.x = (a[0] / L, 0.0, a[2] / L)
        self.y = (0.0, 1.0, 0.0)
        self.z = cross(self.x, self.y)
        self.at = at

    def p(self, q):
        return tuple(self.at[i] + self.x[i] * q[0] + self.y[i] * q[1] + self.z[i] * q[2] for i in range(3))

    def n(self, q):
        return tuple(self.x[i] * q[0] + self.y[i] * q[1] + self.z[i] * q[2] for i in range(3))


placements = []
L = {'pins': [], 'beacons': [], 'nav': [], 'slits': [], 'windows': [], 'glow': [], 'floods': [], 'lenses': []}


def yard(part, at, along=(1, 0, 0), **kw):
    placements.append({'part': f'yard:{part}', 'p': r3(at), 'n': [0, 1, 0], 'up': [0, 0, 1], 'along': r3(along),
                       'snap': False, 'seat': {'check': False}, **kw})
    return Place(at, along)


def kit(part, p, n, up=(0, 1, 0), **kw):
    placements.append({'part': part, 'p': r3(p), 'n': r3(n), 'up': r3(up), 'snap': False, 'seat': {'check': False}, **kw})


def anchors(part):
    return YK[part]['anchors']


def collect(part, pl, lit_share=1.0, seed=0):
    """Lamps, beacons, obstruction lights, slits and windows of a placed yard part -> L."""
    a = anchors(part)
    for q in a.get('lampsAmber', []):
        L['pins'].append(r3(pl.p(q)))
    for q in a.get('beacons', []):
        L['beacons'].append(r3(pl.p(q)))
    for q in a.get('obstruction', []):
        L['nav'].append(r3(pl.p(q)))
    for s in a.get('slits', []):
        L['slits'].append({'p': r3(pl.p(s['p'])), 'u': r3(pl.n(s['u'])), 'n': r3(pl.n(s['n'])), 'len': s.get('len', 1.4),
                           'width': s.get('width', 0.2), 'door': bool(s.get('door'))})
    for i, w in enumerate(a.get('windows', [])):
        L['windows'].append({'p': r3(pl.p(w['p'])), 'n': r3(pl.n(w['n'])), 'size': w['size']})
    for g in a.get('glow', []):
        L['glow'].append({'p': r3(pl.p(g['p'])), 'n': r3(pl.n(g['n'])), 'size': g['size']})


def hash01(*v):
    h = 2166136261
    for x in v:
        h = ((h ^ (int(round(x * 100)) & 0xffffffff)) * 16777619) & 0xffffffff
    return h / 2 ** 32


# ---- big structures ----------------------------------------------------------------------------
g = yard('gantry', (0.0, 0.0, D.GANTRY['z']), id='portal gantry 01 straddling midships')
collect('gantry', g)
for lad in anchors('gantry')['ladders']:
    for k in range(lad['count']):
        kit('ladder', g.p((lad['p'][0], lad['p'][1] + 1.5 + 3.0 * k, lad['p'][2])), g.n(lad['n']), id='gantry leg ladders')
for r in anchors('gantry')['rails']:
    a, b = g.p(r['from']), g.p(r['to'])
    placements.append({'part': 'rail', 'row': {'from': r3(a), 'to': r3(b), 'pitch': 3.0}, 'n': [0, 1, 0], 'snap': False,
                       'seat': {'check': False}, 'id': 'gantry girder walkway rails'})

for c in D.CRANES:
    pl = yard(c['part'], (D.CRANE_X, 0.0, c['z']), id=f"luffing crane {c['part']}")
    collect(c['part'], pl)

for i, h in enumerate(D.HALLS):
    pl = yard('hall', (h['c'][0], 0.0, h['c'][1]), h['along'], id=f'workshop hall {i}')
    collect('hall', pl)
    a = anchors('hall')
    for d in a['doors']:
        p = list(d['p']); p[1] = 1.2; p[0] += 0.1 * d['n'][0]
        kit('door', pl.p(p), pl.n(d['n']), id='hall crew doors')
    for k, q in enumerate(a['panes']):
        kit('pane', pl.p(q['p']), pl.n(q['n']), id='hall office windows')
        if hash01(i, k, 7) < 0.55:
            L['windows'].append({'p': r3(pl.p(q['p'])), 'n': r3(pl.n(q['n'])), 'size': [1.0, 1.2], 'office': True})
    for q in a['vents']:
        kit('vent', pl.p(q['p']), pl.n(q['n']), up=(0, 0, 1) if q['n'][1] > 0.5 else (0, 1, 0), id='hall vents')
    for lad in a['ladders']:
        for k in range(lad['count']):
            kit('ladder', pl.p((lad['p'][0], lad['p'][1] + 1.5 + 3.0 * k, lad['p'][2])), pl.n(lad['n']), id='hall roof ladder')

for (x, z) in D.MASTS:
    along = (0, 0, -1) if x < 0 else (0, 0, 1)   # floods (+Z of the part) face the berth
    pl = yard('floodMast', (x, 0.0, z), along, id='flood masts')
    a = anchors('floodMast')
    for f in a['floods']:
        kit('floodlight', pl.p(f['p']), pl.n(f['n']), up=pl.n(f['up']), id='mast floodlights')
        lp = pl.p((f['p'][0], f['p'][1] - 0.28, f['p'][2] + 0.18))
        L['lenses'].append(r3(lp))
    li = a['light']
    L['floods'].append({'p': r3(pl.p(li['p'])), 'target': r3((x * 0.25, 0.0, z * 0.9 + (0 if abs(z) < 60 else -math.copysign(10, z))))})

# ---- the berth: keel and bilge blocks under the DD-12, scaffolds, the drive bell ----------------------
T = D.SHIP_T
keel_top = min(f['ymin'] for f in DD['frames'] if f['z'] <= -37.0)
keel_bottom = keel_top - D.KEEL['h']
blocks = []
for key, xs in (('keel', [0.0]), ('bilge', [-D.BILGE_X, D.BILGE_X])):
    for z, yb in DD['bottom'][key]:
        if yb is None:
            continue
        if z < D.CUT['aft']:            # aft of the plating: blocks carry the bare keel / the frames' bilge corners
            yb = keel_bottom if key == 'keel' else min(f['ymin'] for f in DD['frames'] if f['z'] <= -37.0)
            if key == 'bilge' and z < -76:
                continue
        h = yb + T[1]
        for x in xs:
            blocks.append((x, z + T[2], h))
hmin = min(b[2] for b in blocks)
assert hmin >= D.BLOCK_MIN - 1e-3, f'lowest keel block {hmin:.2f} m < {D.BLOCK_MIN}'
for x, z, h in blocks:
    kit('yard:keelBlock', (x, 0.0, z), (0, 1, 0), up=(0, 0, 1), scale=[1.0, round(h / 2.0, 4), 1.0], id='keel and bilge blocks')
    # yard:keelBlock is a +Y part: kit() passes n = up, along defaults to +Z
    placements[-1]['along'] = [1, 0, 0]

# scaffold towers along the midships flanks (main hull 35 m) and the aft frames (55 m)
mid_half = max(f['halfBeam'] for f in DD['frames'] if -34 < f['z'] < 20)
aft_half = max(f['halfBeam'] for f in DD['frames'] if f['z'] <= -37.0)
sc = []
for sx, zs in ((1, (-21.0, -9.0, 3.0, 15.0, 26.0)), (-1, (-16.0, -3.0, 9.0, 21.0))):
    for k, z in enumerate(zs):
        sc.append((sx * (mid_half + 1.6), z, 'scaffold-L' if (k + (sx > 0)) % 2 else 'scaffold-M'))
for sx, zs in ((1, (-36.0, -54.0, -70.0)), (-1, (-42.0, -62.0))):
    for z in zs:
        sc.append((sx * (aft_half + 1.6), z, 'scaffold-L'))
for x, z, part in sc:
    yard(part, (x, 0.0, z), (0, 0, 1), id='scaffold towers')
    if hash01(x, z) < 0.6:
        H = anchors(part).get('height', 14.0) if isinstance(anchors(part), dict) else 14.0
        deck = (int((YK[part]['params'].get('lifts', 7)) // 2) * 2) * 2.0 + 0.1
        yard('worker', (x, deck, z + 0.8), (1, 0, 0) if x > 0 else (-1, 0, 0), id='workers on scaffold decks')

# drive bell lying on its cradle (axis +X from its exit plane), kit bell-XL x1.106
bell = json.load(open(HULLINFO))['bell'] if HULLINFO and os.path.exists(HULLINFO) else {'axis_y': 9.5}
bx, bz = D.BELL['p']
kit('bell-XL', (bx, bell['axis_y'], bz), (1, 0, 0), up=(0, 1, 0), scale=D.BELL['scale'], id='spare drive bell (bell-XL x1.106) on its cradle')

# ---- vehicles, containers, people, bollards ----------------------------------------------------
for at, along in [((-70.0, 0.0, 78.0), (1, 0, 0)), ((-106.0, 0.0, 52.0), (1, 0, 0)), ((81.0, 0.0, 60.0), (-1, 0, 0)), ((-12.0, 0.0, 134.0), (0, 0, -1)),
                  ((66.0, 0.0, 112.0), (-1, 0, 0))]:
    pl = yard('truck', at, along, id='semi trucks')
    collect('truck', pl)
for at, along in [((-64.0, 0.0, 50.0), (0, 0, 1)), ((-96.0, 0.0, 38.0), (1, 0, 0)), ((76.0, 0.0, 40.0), (-1, 0, 0)), ((20.0, 0.0, -124.0), (0, 0, -1)), ((-28.0, 0.0, 120.0), (1, 0, 0))]:
    pl = yard('forklift', at, along, id='forklifts')
    collect('forklift', pl)


def container_stack(origin, cols, rows, tiers, length_axis='x', skip=()):
    """Kit containers (ISO 20 ft) in a stack: cols along the length axis, rows across, tiers up."""
    Lc, Wc, Hc = 6.11, 2.44, 2.59
    for c in range(cols):
        for r in range(rows):
            for t in range(tiers):
                if (c, r, t) in skip:
                    continue
                if length_axis == 'x':
                    p = (origin[0] + c * (Lc + 0.3), t * Hc, origin[1] + r * (Wc + 0.2)); up = (0, 0, 1)
                else:
                    p = (origin[0] + r * (Wc + 0.2), t * Hc, origin[1] + c * (Lc + 0.3)); up = (1, 0, 0)
                kit('container', p, (0, 1, 0), up=up, id='container stacks (kit 20-ft)')


container_stack((-76.0, 40.0), 3, 2, 2, skip={(2, 1, 1)})
container_stack((-66.0, 64.0), 2, 1, 3, skip={(1, 0, 2)})
container_stack((84.0, -40.0), 3, 2, 1, length_axis='z')
container_stack((24.0, 130.0), 2, 2, 1)
container_stack((56.0, 84.0), 2, 2, 2, length_axis='z', skip={(1, 1, 1)})
container_stack((-46.0, -136.0), 3, 1, 2, skip={(0, 0, 1)})

groups = [((14.0, 118.0), 4), ((24.0, 6.0), 3), ((-23.0, -14.0), 3), ((-32.0, -55.0), 3), ((22.0, -122.0), 2),
          ((-86.0, 24.0), 3), ((80.0, 30.0), 2), ((42.0, 28.0), 2), ((-6.0, 30.0), 3), ((-60.0, 56.0), 2), ((62.0, 100.0), 3)]
for (x, z), n in groups:
    for k in range(n):
        a = hash01(x, z, k) * 2 * math.pi
        r = 1.0 + 1.2 * hash01(z, x, k)
        yard('worker', (x + r * math.cos(a), 0.0, z + r * math.sin(a)), (math.cos(a * 1.7), 0, math.sin(a * 1.7)), id='crew figures (1.8 m)')

for sx in (-1, 1):
    for z in (-120.0, -80.0, -40.0, 40.0, 80.0, 120.0):
        pl = yard('bollard', (sx * (D.BERTH['x'] + 1.5), 0.0, z), id='berth-edge lamp bollards')
        L['pins'].append(r3(pl.p(anchors('bollard')['lamp'])))

spec = {
    'about': 'Planetside shipyard (cqs-fleet), v1: YARD frame (metres, ground y = 0, +Z front / bow end of the berth, +X left). '
             'The hull node is the yard\'s own geometry (tools/blender/buildings/shipyard.py: ground, rails, the DD-12\'s '
             'procedural ring frames and keel, the module on the gantry); this spec places the yard kit (assets/parts-yard, '
             '+Y mounts) and the fleet kit (assets/parts-blender, +Z mounts) at true size. Generated by shipyard_spec.py.',
    'hull': {'glb': 'HULL_GLB_FROM_COMMAND_LINE', 'rotate': [0, 0, 0], 'scale': 1.0, 'centre': False},
    'partsDir': '../../../assets/parts-blender',
    'kits': {'yard': '../../../assets/parts-yard'},
    'partDefaults': {'rail': {'sink': 0.0, 'xAlong': True, 'scale': [3, 1, 1]}, 'door': {'sink': 0.0}, 'pane': {'sink': 0.0},
                     'ladder': {'sink': 0.0}, 'vent': {'sink': 0.0}, 'floodlight': {'sink': 0.0}},
    'fixes': {'container': {'decimate': 0.35}, 'door': {'decimate': 0.3}, 'ladder': {'decimate': 0.4}, 'floodlight': {'decimate': 0.45},
              'vent': {'decimate': 0.5}, 'bell-XL': {'decimate': 0.4}},
    'seat': {'check': False},
    'bake': {'ao': False},
    'placements': placements,
}
json.dump(spec, open(SPEC, 'w'), indent=1)
counts = {}
for q in placements:
    counts[q['part']] = counts.get(q['part'], 0) + 1
print('[spec] placements', len(placements), counts)
print('[spec] lights', {k: len(v) for k, v in L.items()}, 'lowest block %.2f m' % hmin)

# ---- module data block ---------------------------------------------------------------------------
data = {
    'shipT': list(T),
    'cut': D.CUT,
    'keelBlockMin': round(hmin, 3),
    'lights': L,
}
if os.path.exists(MODULE):
    src = open(MODULE).read()
    block = '// <GENERATED by tools/blender/buildings/shipyard_spec.py: do not edit by hand>\nconst DATA = ' + json.dumps(data, separators=(',', ':')) + ';\n// </GENERATED>'
    src2 = re.sub(r'// <GENERATED.*?// </GENERATED>', lambda m: block, src, flags=re.S)
    open(MODULE, 'w').write(src2)
    print('[spec] module data written', MODULE)
