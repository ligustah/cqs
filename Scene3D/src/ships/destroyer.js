// PLACEHOLDER — replaced by the final design.
import { ShipBuilder, geo, section } from '../lib/kit.js';

export const meta = { name: 'placeholder destroyer', designation: '---', blurb: '' };

export function build(mat) {
  const b = new ShipBuilder('destroyer', mat, { uvScale: 4 });
  b.add(geo.loft([
    { z: -68 / 2, sec: section.superellipse(14 * 0.5, 10, 4) },
    { z: 68 * 0.2, sec: section.superellipse(14, 10, 4) },
    { z: 68 / 2, sec: section.superellipse(14 * 0.2, 10 * 0.3, 4) },
  ]), 'hull');
  b.engine({ p: [0, 0, -68 / 2], radius: 10 * 0.25 });
  b.light({ p: [14 / 2, 0, 0], color: 'green', blink: { period: 1.4, duty: 0.15 } });
  b.light({ p: [-14 / 2, 0, 0], color: 'red', blink: { period: 1.4, duty: 0.15 } });
  
  return b.finish();
}
