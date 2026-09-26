// PLACEHOLDER — replaced by the final design.
import { ShipBuilder, geo, section } from '../lib/kit.js';

export const meta = { name: 'placeholder freighter', designation: '---', blurb: '' };

export function build(mat) {
  const b = new ShipBuilder('freighter', mat, { uvScale: 4 });
  b.add(geo.loft([
    { z: -50 / 2, sec: section.superellipse(8 * 0.5, 8, 4) },
    { z: 50 * 0.2, sec: section.superellipse(8, 8, 4) },
    { z: 50 / 2, sec: section.superellipse(8 * 0.2, 8 * 0.3, 4) },
  ]), 'hull');
  b.engine({ p: [0, 0, -50 / 2], radius: 8 * 0.25 });
  b.light({ p: [8 / 2, 0, 0], color: 'green', blink: { period: 1.4, duty: 0.15 } });
  b.light({ p: [-8 / 2, 0, 0], color: 'red', blink: { period: 1.4, duty: 0.15 } });
  
  return b.finish();
}
