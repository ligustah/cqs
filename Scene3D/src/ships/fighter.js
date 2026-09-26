// PLACEHOLDER — replaced by the final design.
import { ShipBuilder, geo, section } from '../lib/kit.js';

export const meta = { name: 'placeholder fighter', designation: '---', blurb: '' };

export function build(mat) {
  const b = new ShipBuilder('fighter', mat, { uvScale: 4 });
  b.add(geo.loft([
    { z: -16 / 2, sec: section.superellipse(11 * 0.5, 4.5, 4) },
    { z: 16 * 0.2, sec: section.superellipse(11, 4.5, 4) },
    { z: 16 / 2, sec: section.superellipse(11 * 0.2, 4.5 * 0.3, 4) },
  ]), 'hull');
  b.engine({ p: [0, 0, -16 / 2], radius: 4.5 * 0.25 });
  b.light({ p: [11 / 2, 0, 0], color: 'green', blink: { period: 1.4, duty: 0.15 } });
  b.light({ p: [-11 / 2, 0, 0], color: 'red', blink: { period: 1.4, duty: 0.15 } });
  
  return b.finish();
}
