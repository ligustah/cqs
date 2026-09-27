// Screen-space annotation for the scale chart (lineup view): callouts with leader lines and a
// metre ruler, drawn as DOM + SVG over the WebGL canvas and laid out every frame from projected
// anchor points, so the text stays crisp and never overlaps at any zoom or orbit.
//   - Callouts sit in one right-aligned column on the stern side of the chart. They start level
//     with their anchor; where two would collide they are spread apart as a group (clusters
//     centred on their anchors), and a leader line runs from each label to its anchor.
//   - The ruler is a baseline with tick marks of fixed pixel length. Tick labels are placed by
//     priority (0 and every 100 m first, then 50 m, then the 10 m marks as one group) and only
//     where they touch no label already placed, so the 10 m labels appear once there is room
//     for all of them (close-ups) and drop out when the whole 900 m chart is in view.
import * as THREE from 'three';

const NS = 'http://www.w3.org/2000/svg';
const _v = new THREE.Vector3();

function project(p, camera, W, H) {
  _v.copy(p).project(camera);
  return { x: (_v.x + 1) / 2 * W, y: (1 - _v.y) / 2 * H, ok: _v.z > -1 && _v.z < 1 };
}

export function createChartOverlay(container) {
  const root = document.createElement('div');
  root.className = 'chart';
  const svg = document.createElementNS(NS, 'svg');
  root.appendChild(svg);
  container.appendChild(root);
  const callouts = [];
  let ruler = null;
  let limits = { t: 0, b: 0 }; // px kept clear above / below the callout column (overlay panels)

  const measure = (item) => { if (!item.w) { item.w = item.el.offsetWidth; item.h = item.el.offsetHeight; } };

  return {
    root,
    /** Keep the callout column inside [t, H - b] (px), e.g. clear of overlay panels. */
    bounds(b) { limits = { t: b.t ?? 0, b: b.b ?? 0 }; },
    /** A label with a leader line to `anchor` (world space). */
    callout(anchor, title, detail) {
      const el = document.createElement('div');
      el.className = 'callout';
      el.innerHTML = `<b>${title}</b>${detail ? `<span>${detail}</span>` : ''}`;
      root.appendChild(el);
      const item = { anchor: anchor.clone(), el, w: 0, h: 0 };
      callouts.push(item);
      return item;
    },
    /**
     * Ruler along `axis` from `origin` (world), ticks pointing along `toward` (on screen).
     * marks: [{ m, size: 0 (minor) | 1 (medium) | 2 (major), label, priority, group }]
     */
    ruler(opts) {
      ruler = { ...opts, labels: opts.marks.map((mk) => {
        if (!mk.label) return null;
        const el = document.createElement('div');
        el.className = 'tick';
        el.textContent = mk.label;
        root.appendChild(el);
        return { el, w: 0, h: 0 };
      }) };
    },
    update(camera, W, H) {
      let out = '';
      // --- ruler --------------------------------------------------------------------------
      if (ruler) {
        const { origin, axis, toward, length, marks } = ruler;
        const a = project(origin, camera, W, H), b = project(origin.clone().addScaledVector(axis, length), camera, W, H);
        if (a.ok && b.ok) out += `<line class="base" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}"/>`;
        const placed = [];
        const order = marks.map((mk, i) => i).sort((i, j) => (marks[j].priority ?? 0) - (marks[i].priority ?? 0));
        const pos = marks.map((mk) => {
          const p = origin.clone().addScaledVector(axis, mk.m);
          const s = project(p, camera, W, H), t = project(p.addScaledVector(toward, 1), camera, W, H);
          const dx = t.x - s.x, dy = t.y - s.y, d = Math.hypot(dx, dy) || 1;
          return { ...s, dx: dx / d, dy: dy / d };
        });
        marks.forEach((mk, i) => {
          const s = pos[i];
          if (!s.ok || s.x < -20 || s.x > W + 20 || s.y < -20 || s.y > H + 20) return;
          const len = [5, 8, 12][mk.size ?? 0];
          out += `<line class="tick${mk.size ?? 0}" x1="${s.x.toFixed(1)}" y1="${s.y.toFixed(1)}" x2="${(s.x + s.dx * len).toFixed(1)}" y2="${(s.y + s.dy * len).toFixed(1)}"/>`;
        });
        // labels go in by priority; marks that share a `group` (the 10 m labels) are placed all
        // together or not at all, so the fine scale never shows a stray label
        const units = [];
        for (const i of order) {
          if (!ruler.labels[i]) continue;
          const g = marks[i].group;
          const u = g && units.find((x) => x.group === g);
          if (u) u.items.push(i); else units.push({ group: g, items: [i] });
        }
        const hit = (r, list) => list.some((q) => r.x0 < q.x1 && r.x1 > q.x0 && r.y0 < q.y1 && r.y1 > q.y0);
        for (const u of units) {
          const rects = u.items.map((i) => {
            const lab = ruler.labels[i], s = pos[i];
            measure(lab);
            const len = [5, 8, 12][marks[i].size ?? 0] + 4;
            const cx = s.x + s.dx * len, top = s.y + s.dy * len;
            return { i, cx, top, ok: s.ok, x0: cx - lab.w / 2 - 4, x1: cx + lab.w / 2 + 4, y0: top, y1: top + lab.h };
          });
          const fits = rects.every((r, k) => r.ok && r.x0 > 0 && r.x1 < W && r.y1 < H && !hit(r, placed) && !hit(r, rects.slice(0, k)));
          for (const r of rects) {
            const lab = ruler.labels[r.i];
            lab.el.style.visibility = fits ? 'visible' : 'hidden';
            if (fits) lab.el.style.transform = `translate(${(r.cx - lab.w / 2).toFixed(1)}px, ${r.top.toFixed(1)}px)`;
          }
          if (fits) placed.push(...rects);
        }
      }
      // --- callouts -----------------------------------------------------------------------
      const on = [];
      for (const c of callouts) {
        measure(c);
        const s = project(c.anchor, camera, W, H);
        c.sx = s.x; c.sy = s.y;
        const vis = s.ok && s.x > 0 && s.x < W && s.y > 0 && s.y < H;
        c.el.style.visibility = vis ? 'visible' : 'hidden';
        if (vis) on.push(c);
      }
      if (on.length) {
        const pad = 6, maxW = Math.max(...on.map((c) => c.w));
        const colRight = Math.max(maxW + 12, Math.min(...on.map((c) => c.sx)) - 34);
        // 1-D layout: clusters of touching labels are stacked and centred on their anchors
        on.sort((p, q) => p.sy - q.sy);
        const clusters = on.map((c) => ({ items: [c] }));
        const fit = (k) => {
          k.total = k.items.reduce((acc, c) => acc + c.h, 0) + pad * (k.items.length - 1);
          k.top = THREE.MathUtils.clamp(k.items.reduce((acc, c) => acc + c.sy, 0) / k.items.length - k.total / 2, limits.t + 4, H - limits.b - 4 - k.total);
        };
        clusters.forEach(fit);
        for (let k = 0; k + 1 < clusters.length;) {
          const p = clusters[k], q = clusters[k + 1];
          if (p.top + p.total + pad > q.top) { p.items.push(...q.items); clusters.splice(k + 1, 1); fit(p); k = Math.max(0, k - 1); } else k++;
        }
        for (const k of clusters) {
          let y = k.top;
          for (const c of k.items) {
            const cy = y + c.h / 2;
            c.el.style.transform = `translate(${(colRight - c.w).toFixed(1)}px, ${y.toFixed(1)}px)`;
            const x0 = colRight + 5, x1 = colRight + 14;
            out += `<path class="leader" d="M${x0.toFixed(1)},${cy.toFixed(1)} H${x1.toFixed(1)} L${(c.sx - 3).toFixed(1)},${c.sy.toFixed(1)}"/>`;
            out += `<circle class="anchor" cx="${c.sx.toFixed(1)}" cy="${c.sy.toFixed(1)}" r="2"/>`;
            y += c.h + pad;
          }
        }
      }
      svg.innerHTML = out;
    },
  };
}

/**
 * Aim a perspective camera along `dir` (unit vector from target to camera) so that all `points`
 * fill the viewport inside the pixel margins { l, r, t, b }. Returns the target; moves the camera.
 */
export function frameView(camera, points, dir, margins, W, H) {
  const target = new THREE.Box3().setFromPoints(points).getCenter(new THREE.Vector3());
  let dist = target.distanceTo(points[0]) * 3 + 1;
  const x0 = -1 + (2 * margins.l) / W, x1 = 1 - (2 * margins.r) / W, y0 = -1 + (2 * margins.b) / H, y1 = 1 - (2 * margins.t) / H;
  const right = new THREE.Vector3(), up = new THREE.Vector3();
  for (let it = 0; it < 40; it++) {
    camera.position.copy(target).addScaledVector(dir, dist);
    camera.lookAt(target);
    camera.updateMatrixWorld();
    camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
    let a = Infinity, b = -Infinity, c = Infinity, d = -Infinity;
    for (const p of points) { _v.copy(p).project(camera); a = Math.min(a, _v.x); b = Math.max(b, _v.x); c = Math.min(c, _v.y); d = Math.max(d, _v.y); }
    const th = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    right.setFromMatrixColumn(camera.matrixWorld, 0);
    up.setFromMatrixColumn(camera.matrixWorld, 1);
    target.addScaledVector(right, ((a + b) / 2 - (x0 + x1) / 2) * dist * th * camera.aspect * 0.8)
      .addScaledVector(up, ((c + d) / 2 - (y0 + y1) / 2) * dist * th * 0.8);
    dist *= Math.pow(Math.max((b - a) / (x1 - x0), (d - c) / (y1 - y0)), 0.8);
  }
  camera.position.copy(target).addScaledVector(dir, dist);
  camera.lookAt(target);
  return target;
}
