// PLACEHOLDER — replaced by the final design.
import { ShipBuilder, geo, section } from '../lib/kit.js';

export const meta = { name: 'placeholder carrier', designation: '---', blurb: '' };

export function build(mat) {
  const b = new ShipBuilder('carrier', mat, { uvScale: 4 });
  b.add(geo.loft([
    { z: -220 / 2, sec: section.superellipse(96 * 0.5, 34, 4) },
    { z: 220 * 0.2, sec: section.superellipse(96, 34, 4) },
    { z: 220 / 2, sec: section.superellipse(96 * 0.2, 34 * 0.3, 4) },
  ]), 'hull');
  b.engine({ p: [0, 0, -220 / 2], radius: 34 * 0.25 });
  b.light({ p: [96 / 2, 0, 0], color: 'green', blink: { period: 1.4, duty: 0.15 } });
  b.light({ p: [-96 / 2, 0, 0], color: 'red', blink: { period: 1.4, duty: 0.15 } });
  b.anchor('hangar', [0, 0, 0], { size: [80, 13, 104] });
  return b.finish();
}
