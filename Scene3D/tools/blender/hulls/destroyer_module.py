"""Finish the destroyer's ship module after module.py wrote the draft.

    <blender-python> tools/blender/hulls/destroyer_module.py <draft.js> <assembled.glb> <out.js>

module.py writes one engine entry per bell; this keeps the installed module's CORNER_BELL
approach (the four corner bells share one const, one mirrored entry per pair), and adds what
module.py does not know about:
  - anchors.railgunMuzzle, RE-MEASURED on the assembled hull by ray casts along the bore axis:
    p = centre of the bore opening on the barrel boss face, radius = the bore's inscribed radius
    (rays across the opening), mouth = the shroud mouth (the lip's front face) on the same axis;
  - the muzzle-rim fixtures (a dim cool field-coil band just inside the lip, one strip per shroud
    face, placed on the measured shroud walls);
  - liveryKeep: the exposed barrel in the gun gap keeps a muted version of its copper coils.
All coordinates shift by minus the assembled bbox centre, as module.py's do.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,F401
from mathutils import Vector  # noqa: E402

import module as MOD  # noqa: E402
import destroyer as D  # noqa: E402


def cast(bvh, o, d, far=60):
    p, n, _i, dist = bvh.ray_cast(Vector(o), Vector(d).normalized(), far)
    return (p, dist) if p is not None else (None, None)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    draft, glb, out = argv[:3]
    bvh, lo, hi = MOD.load(glb)
    ctr = (lo + hi) / 2
    sh = lambda v: [round(float(a - b), 3) + 0.0 for a, b in zip(v, ctr)]
    by = D.BORE_Y
    # boss face: rays along -z just outside the bore opening (above and below the axis)
    faces = []
    for dy in (3.7, -3.7):
        p, _ = cast(bvh, (0, by + dy, 120), (0, 0, -1), 60)
        faces.append(p.z)
    zf = sum(faces) / len(faces)
    # bore radius: from the axis, rays in the face plane a little inside the opening
    rs = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        p, dist = cast(bvh, (0, by, zf - 0.6), (math.cos(a), math.sin(a), 0), 10)
        if p is not None:
            rs.append(dist)
    radius = min(rs)
    # bore depth (floor) and the mouth: lip front face on the same axis, shroud walls
    floor, _ = cast(bvh, (0, by, zf + 1), (0, 0, -1), 30)
    lip, _ = cast(bvh, (0, by + D.SHROUD[1] / 2 + 0.3, 120), (0, 0, -1), 30)
    walls = {}
    for name, d in (('x+', (1, 0, 0)), ('x-', (-1, 0, 0)), ('y+', (0, 1, 0)), ('y-', (0, -1, 0))):
        p, dist = cast(bvh, (0, by, lip.z - 0.9), d, 20)
        walls[name] = dist
    print('[dmodule] boss face', round(zf, 3), 'bore r', round(radius, 3), 'floor', round(floor.z, 3), 'lip', round(lip.z, 3), 'walls', {k: round(v, 3) for k, v in walls.items()}, flush=True)
    anchor = {'p': sh((0, by, zf)), 'dir': [0, 0, 1], 'radius': round(radius, 2), 'mouth': sh((0, by, lip.z))}
    # muzzle rim strips, 0.9 m inside the lip on each shroud face
    zr = lip.z - 0.9
    xw, xe = walls['x+'] - 0.03, -(walls['x-'] - 0.03)
    yt, yb = by + walls['y+'] - 0.03, by - (walls['y-'] - 0.03)
    c = D.SHROUD[2]
    hs = D.SHROUD[1] / 2 - c
    rim = []
    RIM = "...MUZZLE_RIM"
    def strip(p, L, rot):
        q = sh(p)
        rim.append(f"    {{ {RIM}, p: [{q[0]}, {q[1]}, {q[2]}], size: [{L:.2f}, 0.04, 0.12], rotZ: {rot} }},")
    strip((xw, by, zr), 2 * hs, 1.5708)
    strip((-xw if False else xe, by, zr), 2 * hs, -1.5708)
    strip((0, yt, zr), D.SHROUD[0] - 2 * c, 3.1416)
    strip((0, yb, zr), D.SHROUD[0] - 2 * c, 0)
    cl = c * math.sqrt(2)
    for sx in (1, -1):
        strip((sx * (xw - c / 2), yt - c / 2, zr), cl, round(-sx * 0.7854, 4))
        strip((sx * (xw - c / 2), yb + c / 2, zr), cl, round(sx * 0.7854 + (0 if sx > 0 else 0), 4))
    js = open(draft).read()
    # engines: corner bells -> CORNER_BELL, one mirrored entry per pair
    lines = js.split('\n')
    out_lines, corner = [], None
    i = 0
    seen = set()
    while i < len(lines):
        L = lines[i]
        if L.strip().startswith('// corner bells'):
            m = re.search(r'\{p: \[([-\d.]+), ([-\d.]+), ([-\d.]+)\], (radius.*)\},$', lines[i + 1].strip())
            x, y, z, rest = float(m.group(1)), m.group(2), m.group(3), m.group(4)
            corner = corner or '{ ' + rest.replace('wall:', 'wall:') + ' }'
            key = (abs(x), y)
            if key not in seen:
                seen.add(key)
                out_lines.append(L)
                out_lines.append(f'    {{ p: [{abs(x)}, {y}, {z}], mirrorX: true, ...CORNER_BELL }},')
            i += 2
            continue
        out_lines.append(L)
        i += 1
    js = '\n'.join(out_lines)
    consts = [
        "const STROBE = { period: 1.3, duty: 0.1 };",
        "const MUZZLE_RIM = { color: '#b4c2dc', radiance: 0.07 };",
        "// corner bells: kit bell-L x1.237 (exit r 4.33, the blueprint's inner-wall fit); depth to the throat plate,",
        "// throat and inner wall are the kit's documented engine entry times that scale",
        f"const CORNER_BELL = {corner};",
        "",
    ]
    js = js.replace('export const asset = {', '\n'.join(consts) + '\nexport const asset = {')
    js = js.replace('blink: {period: 1.3, duty: 0.1, phase: 0.5}', 'blink: { ...STROBE, phase: 0.5 }').replace('blink: {period: 1.3, duty: 0.1}', 'blink: { ...STROBE }')
    # liveryKeep + fixtures after the detail line
    g0, g1 = D.GAP
    keep = [[-11.6, -27.4, g0 + 0.3], [11.6, -11.0, g1 - 0.3]]
    keep = [sh(keep[0]), sh(keep[1])]
    extra = [
        "  // The exposed barrel in the gun gap keeps a muted version of its copper coils and bus bars instead of the",
        "  // grey repaint, a little above the hull's value, so it reads as its own machinery (box stops short of the gap faces).",
        f"  liveryKeep: [{{ box: [{keep[0]}, {keep[1]}], gain: 0.3, saturation: 0.6, feather: 0.5 }}],",
        "  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one strip per face,",
        "  // 0.9 m inside the lip, on the ray-cast shroud walls), so the gun's mouth reads as an octagon when the bow",
        "  // face is in shadow. Radiance 0.07: a faint glint, not a lamp.",
        "  fixtures: [",
        *rim,
        "  ],",
    ]
    js = re.sub(r'(  detail: .*\n)', lambda m: m.group(1) + '\n'.join(extra) + '\n', js, count=1)
    a = anchor
    anc = (f"    // Railgun, re-measured on the assembled hull: p = centre of the hexagonal bore opening on the barrel boss\n"
           f"    // face (bore floor at z {floor.z - ctr.z:.2f}), radius = inscribed bore radius, mouth = the shroud lip on the same axis.\n"
           f"    railgunMuzzle: {{ p: {a['p']}, dir: [0, 0, 1], radius: {a['radius']}, mouth: {a['mouth']} }},\n")
    js = js.replace('  anchors: {\n', '  anchors: {\n' + anc, 1)
    open(out, 'w').write(js)
    print('[dmodule] wrote', out, 'muzzle', anchor, flush=True)


if __name__ == '__main__':
    main()
