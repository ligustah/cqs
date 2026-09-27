// Overlay UI: mode switch, fleet registry, and ship spec sheet.
import { SLOT_VOLUME, carrierLoads } from './lib/scale.js';
import * as THREE from 'three';

export function createUI({ mode, still, world, classes, order, envelopes = {}, onMode, onFocus, onToggle }) {
  const root = document.getElementById('ui');
  if (!root || still) { if (root) root.hidden = true; return { select() {} }; }

  const byCls = {};
  for (const s of world.ships) if (!byCls[s.cls]) byCls[s.cls] = s.group.userData.ship;
  // hangar-load envelopes: every class main.js loaded (not only the ships this view shows), so the
  // carrier's table is complete in the ship studio too; fall back to the ships in the view
  const env = { ...envelopes };
  for (const c of order) if (!env[c] && byCls[c]) env[c] = byCls[c].envelope.size;

  const fmt = (v, d = 1) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

  // mode switch
  root.querySelectorAll('[data-mode]').forEach((b) => {
    b.setAttribute('aria-pressed', String(b.dataset.mode === mode));
    b.addEventListener('click', () => { if (b.dataset.mode !== mode) onMode(b.dataset.mode); });
  });

  // registry
  const list = root.querySelector('#registry');
  list.innerHTML = '';
  for (const cls of order) {
    const s = byCls[cls];
    if (!s) continue;
    const spec = classes[cls];
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = `reg-${cls}`;
    btn.dataset.cls = cls;
    btn.innerHTML = `
      <span class="reg-name">${spec.label}</span>
      <span class="reg-class">${s.meta?.name ?? ''}</span>
      <span class="reg-len">${fmt(s.envelope.size.z)} m</span>
      <span class="reg-slots">${spec.size ? `${spec.size} slot${spec.size > 1 ? 's' : ''}` : `hangar ${spec.capacity}`}</span>`;
    btn.addEventListener('click', () => { select(cls); onFocus(cls); });
    li.appendChild(btn);
    list.appendChild(li);
  }

  const sheet = root.querySelector('#sheet');
  function select(cls) {
    const s = byCls[cls];
    if (!s) return;
    root.querySelectorAll('#registry button').forEach((b) => b.setAttribute('aria-current', String(b.dataset.cls === cls)));
    const spec = classes[cls];
    const e = s.envelope.size;
    let loads = '';
    if (cls === 'carrier' && s.anchors.hangar) {
      const hz = new THREE.Vector3(...s.anchors.hangar.size).multiplyScalar(s.scaleCorrection);
      const rows = carrierLoads(hz, env);
      loads = `
        <h3>Hangar bay</h3>
        <p class="dims">${fmt(hz.z, 0)} × ${fmt(hz.x, 0)} × ${fmt(hz.y, 0)} m clear</p>
        <table class="loads"><thead><tr><th>Full load</th><th>Needs</th><th>Fits</th></tr></thead><tbody>
        ${rows.map((r) => `<tr class="${r.ok ? 'ok' : 'bad'}"><td>${classes[r.cls].label}${r.variant ? ` (${r.variant})` : ''}</td><td>${r.need}</td><td>${r.fits} ${r.ok ? '✓' : '✗'}</td></tr>`).join('')}
        </tbody></table>`;
    }
    sheet.innerHTML = `
      <p class="eyebrow">${s.source?.gameId || spec.gameId} · ${spec.size ? `${spec.size} hangar slot${spec.size > 1 ? 's' : ''}` : `carries ${spec.capacity} slots`}</p>
      <h2>${s.meta?.name ?? spec.label}</h2>
      <p class="role">${s.meta?.blurb || spec.role}</p>
      <dl class="specs">
        <div><dt>Length</dt><dd>${fmt(e.z)} m</dd></div>
        <div><dt>Beam</dt><dd>${fmt(e.x)} m</dd></div>
        <div><dt>Height</dt><dd>${fmt(e.y)} m</dd></div>
        <div><dt>Envelope</dt><dd>${fmt(s.envelopeVolume, 0)} m³</dd></div>
        ${s.meta?.crew ? `<div><dt>Crew</dt><dd>${s.meta.crew}</dd></div>` : ''}
        ${spec.size ? `<div><dt>Slots</dt><dd>${fmt(s.envelopeVolume / SLOT_VOLUME, 2)} × ${SLOT_VOLUME} m³</dd></div>` : ''}
      </dl>
      ${loads}
      ${art(s.source)}`;
  }

  // fal concept art the mesh was reconstructed from, plus the in-orbit concept shot
  function art(src) {
    if (!src?.concept && !src?.beauty) return '';
    const fig = (url, cap) => url ? `<figure><a href="${url}" target="_blank" rel="noopener"><img src="${url}" alt="${cap}" loading="lazy"></a><figcaption>${cap}</figcaption></figure>` : '';
    return `
        <h3>Concept art</h3>
        <div class="art">${fig(src.beauty, 'In orbit (concept)')}${fig(src.concept, 'Design reference (image-to-3D input)')}</div>
        <p class="gen">${src.generator ? `Mesh: ${src.generator}` : ''}</p>`;
  }
  select(world.selected || 'carrier');

  root.querySelectorAll('[data-toggle]').forEach((el) => {
    el.addEventListener('change', () => onToggle(el.dataset.toggle, el.checked));
  });
  const hangarToggle = root.querySelector('[data-toggle="hangar"]');
  if (hangarToggle) {
    hangarToggle.closest('label').hidden = mode !== 'lineup';
    const hq = new URLSearchParams(location.search).get('hangar');
    if (hq !== null && hq !== '0') hangarToggle.checked = true;
  }
  // lineup: switch between the whole chart and the close-up of the small ships (?lineup=small)
  const detail = root.querySelector('#lineup-detail');
  if (detail) {
    detail.hidden = mode !== 'lineup';
    const q = new URLSearchParams(location.search);
    if (world.lineupSmall) q.delete('lineup'); else q.set('lineup', 'small');
    const qs = q.toString();
    detail.href = `${qs ? `?${qs}` : location.pathname}${q.get('mode') ? '' : '#lineup'}`;
    detail.textContent = world.lineupSmall ? 'Whole chart' : 'Close-up: small ships';
  }

  return { select };
}
