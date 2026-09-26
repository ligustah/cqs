// PLACEHOLDER — replaced by the final design.
import { ShipBuilder, geo, section } from '../lib/kit.js';

export const meta = { name: 'placeholder corvette', designation: '---', blurb: '' };

export function build(mat) {
  const b = new ShipBuilder('corvette', mat, { uvScale: 4 });
  b.add(geo.loft([
    { z: -32 / 2, sec: section.superellipse(14 * 0.5, 9, 4) },
    { z: 32 * 0.2, sec: section.superellipse(14, 9, 4) },
    { z: 32 / 2, sec: section.superellipse(14 * 0.2, 9 * 0.3, 4) },
  ]), 'hull');
  b.engine({ p: [0, 0, -32 / 2], radius: 9 * 0.25 });
  b.light({ p: [14 / 2, 0, 0], color: 'green', blink: { period: 1.4, duty: 0.15 } });
  b.light({ p: [-14 / 2, 0, 0], color: 'red', blink: { period: 1.4, duty: 0.15 } });
  
  return b.finish();
}
