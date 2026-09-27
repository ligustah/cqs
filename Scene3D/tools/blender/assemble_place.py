# Placement expansion and hull snapping for tools/blender/assemble.py.
# The spec format is src/lib/compose.js's (same expansion and orientation rules), plus the
# mount conventions of assets/parts/parts.json, sink depth and cover patches:
#
#   { part, p: [x,y,z], n?: [x,y,z], up?: [x,y,z], along?: [x,y,z], rot?: deg, scale?,
#     mirrorX?, snap?: true, normal?: 'authored'|'hit', lift?: 0.02, sink?: m, reach?: 6,
#     patch?: { size: [w,h], depth?, proud?, color?: [r,g,b] sRGB 0-1 | 'sample' }, id? }
#   { part, row: { from, to, pitch }, rows?: { count, step: [x,y,z] }, ... }
#   { part: 'patch', size: [w, h], p, n, up, depth?, proud?, color? }   (a cover plate alone)
#
# Orientation: mount "+Z" parts (door, port, pane, ...) put their +Z along n and +Y toward up;
# mount "+Y" parts (rail, antenna, container) stand with +Y along n and +X along `along`
# (default: the row direction for a row, else the up vector projected, else +Z / bow). `rot`
# turns the part about its mount axis. Snapping casts a ray from 8 m outside p along -n and
# puts the mount face on the first hull hit, `lift - sink` metres out along n.
import math
from mathutils import Matrix, Vector

V = Vector


def vec(a, d=(0, 0, 0)):
    return V(a if a is not None else d)


def expand(placements):
    out = []
    for q in placements:
        base = []
        row_dir = None
        if q.get('row'):
            a, b = vec(q['row']['from']), vec(q['row']['to'])
            L = (b - a).length
            pitch = q['row']['pitch']
            k = max(1, int(math.floor(L / pitch + 1e-6)) + 1)
            off = (L - (k - 1) * pitch) / 2
            d = (b - a).normalized() if L > 1e-9 else V((0, 0, 1))
            row_dir = d
            base = [a + d * (off + i * pitch) for i in range(k)]
        else:
            base = [vec(q['p'])]
        step = vec(q['rows']['step']) if q.get('rows') else None
        count = q['rows']['count'] if q.get('rows') else 1
        n = vec(q.get('n'), (0, 0, 1)).normalized()
        up = vec(q.get('up'), (0, 1, 0))
        along = vec(q['along']) if q.get('along') else row_dir
        for r in range(count):
            for i, p0 in enumerate(base):
                p = p0 + step * r if step is not None else p0.copy()
                one = {**q, 'p': p, 'n': n.copy(), 'up': up.copy(), 'along': along.copy() if along is not None else None,
                       'mirrored': False, 'index': (r, i)}
                out.append(one)
                if q.get('mirrorX'):
                    m = lambda v: V((-v.x, v.y, v.z)) if v is not None else None
                    out.append({**one, 'p': m(p), 'n': m(n), 'up': m(up), 'along': m(along), 'mirrored': True})
    return out


def basis_z(n, up, rot=0.0):
    """+Z along n, +Y toward up, then rot degrees about n (compose.js basis())."""
    z = n.normalized()
    y = up - z * up.dot(z)
    if y.length_squared < 1e-6:
        y = (V((0, 1, 0)) - z * z.y) if abs(z.y) < 0.9 else (V((0, 0, 1)) - z * z.z)
    y.normalize()
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed()
    if rot:
        m = m @ Matrix.Rotation(math.radians(rot), 3, 'Z')
    return m


def basis_y(n, along, up, rot=0.0):
    """+Y along n, +X along `along` (projected); then rot degrees about n."""
    yv = n.normalized()
    a = along if along is not None else None
    if a is None or (a - yv * a.dot(yv)).length_squared < 1e-6:
        a = V((0, 0, 1)) if abs(yv.z) < 0.9 else V((1, 0, 0))
    x = a - yv * a.dot(yv)
    x.normalize()
    z = x.cross(yv)
    m = Matrix((x, yv, z)).transposed()
    if rot:
        m = m @ Matrix.Rotation(math.radians(rot), 3, 'Y')
    return m


def snap(caster, q, sink=0.0):
    """Returns (p_mount, n, hit) or None when the ray misses."""
    p, n = q['p'], q['n']
    if q.get('snap', True) is False:
        return p - n * sink, n, None
    reach = q.get('reach', 6)
    hit = caster.cast(p + n * 8, -n, 8 + reach)
    if hit is None:
        return None
    hp, hn = hit[0], hit[1]
    nn = hn if q.get('normal') == 'hit' else n
    return hp + nn * (q.get('lift', 0.02) - sink), nn, hit


def matrix(q, mount, pm, n):
    """ship-frame 4x4 for a placed part (mirrored parts use the pre-mirrored mesh, so the
    matrix itself is always a proper rotation)."""
    rot = q.get('rot', 0) or 0
    if mount == '+Y':
        R = basis_y(n, q.get('along'), q['up'], rot)
    else:
        R = basis_z(n, q['up'], rot)
    s = q.get('scale', 1) or 1
    M = R.to_4x4() @ Matrix.Scale(s, 4) if not isinstance(s, (list, tuple)) else R.to_4x4() @ Matrix.Diagonal((*s, 1))
    M.translation = pm
    return M


def seat_check(caster, M, mount, bbox, sink, tol=0.06):
    """Probe the part's footprint corners: how far the hull surface lies from the mount face.
    Returns (max_gap, max_bury): gap = the mount face floats that far above the hull at a corner;
    bury = the hull stands above the mount face by more than the sink (the part is swallowed)."""
    lo, hi = bbox
    R = M.to_3x3()
    t = M.translation
    if mount == '+Y':
        nrm = R.col[1].normalized()
        corners = [V((x, 0, z)) for x in (lo[0] * 0.8, hi[0] * 0.8) for z in (lo[2] * 0.8, hi[2] * 0.8)]
    else:
        nrm = R.col[2].normalized()
        corners = [V((x, y, 0)) for x in (lo[0] * 0.9, hi[0] * 0.9) for y in (lo[1] * 0.9, hi[1] * 0.9)]
    gap = 0.0
    bury = 0.0
    for c in corners:
        w = t + R @ c
        hit = caster.cast(w + nrm * 3, -nrm, 6)
        if hit is None:
            gap = max(gap, 3.0)
            continue
        h = 3 - hit[3]  # hull height above the mount face at this corner
        gap = max(gap, -h - 0.0)
        bury = max(bury, h - sink)
    return gap, bury


def fit_plate(caster, c, R, w, h, step=0.5, inset=0.03):
    """Hull relief under a w x h plate centred at c (frame R, +Z = normal): the lowest and highest
    hull points along the normal, relative to c, from a grid of rays about `step` m apart (at
    least 5 x 5). None if most of them miss."""
    nrm = R.col[2]
    offs = []
    nu, nv = max(5, int(w / step) + 2), max(5, int(h / step) + 2)
    for i in range(nu):
        for j in range(nv):
            u = (i / (nu - 1) - 0.5) * (w - 2 * inset)
            v = (j / (nv - 1) - 0.5) * (h - 2 * inset)
            o = c + R.col[0] * u + R.col[1] * v + nrm * 3
            hit = caster.cast(o, -nrm, 6)
            if hit is not None:
                offs.append(3 - hit[3])
    if len(offs) < 0.7 * nu * nv:
        return None
    offs.sort()
    # the floor ignores the lowest 5 % (rays into a hole or past an edge); the top is exact, so
    # nothing old pokes through the plate
    return offs[int(0.05 * len(offs))], offs[-1]


class PlateCaster:
    """BVH over the cover plates (boxes), same interface as assemble_frame.HullCaster.cast."""

    def __init__(self, patches):
        from mathutils.bvhtree import BVHTree
        verts, polys = [], []
        for (w, h), depth, _chamfer, PM, _ci in patches:
            b = len(verts)
            for z in (0, depth):
                for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
                    verts.append(PM @ V((x, y, z)))
            polys += [(b, b + 1, b + 2, b + 3), (b + 4, b + 5, b + 6, b + 7)]
            polys += [(b + k, b + (k + 1) % 4, b + 4 + (k + 1) % 4, b + 4 + k) for k in range(4)]
        self.bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False)

    def cast(self, origin, direction, far=1e4):
        p, n, i, d = self.bvh.ray_cast(V(origin), V(direction).normalized(), far)
        if p is None:
            return None
        if n.dot(direction) > 0:
            n = -n
        return p, n.normalized(), i, d


class MultiCaster:
    """Nearest hit over several casters (hull + cover plates)."""

    def __init__(self, casters):
        self.casters = casters

    def cast(self, origin, direction, far=1e4):
        best = None
        for c in self.casters:
            h = c.cast(origin, direction, far)
            if h is not None and (best is None or h[3] < best[3]):
                best = h
        return best
