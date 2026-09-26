// Hangar containment test for generated carrier hulls.
//
// The hangar anchor is a box in the ship frame. A generated mesh has no notion
// of "interior", so we sample points on a grid inside the box and cast rays
// along the six axes against the hull:
//   - a point counts as inside if it is enclosed: the rays toward port,
//     starboard, dorsal, ventral and stern all hit the hull (the bow ray may
//     leave through the open hangar mouth), or
//   - it lies inside solid hull (an odd number of crossings on most rays).
// A hangar is plausible when nearly all of the box is inside the hull.
import * as THREE from 'three';

const DIRS = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, -1], [0, 0, 1]].map((d) => new THREE.Vector3(...d));

/**
 * @param {THREE.Object3D} ship   group built by buildShip (anchors in its local frame)
 * @param {{p: THREE.Vector3, size: number[]}} hangar  anchor (local frame, before scale correction)
 * @param {object} opts  grid: samples per axis [x, y, z]
 * @returns {{ fraction: number, samples: number, inside: number, misses: object }}
 */
export function hangarInsideFraction(ship, hangar, { grid = [4, 3, 7] } = {}) {
  ship.updateMatrixWorld(true);
  const hull = [];
  ship.traverse((o) => { if (o.isMesh && o.userData.hull) hull.push(o); });
  // count back faces too while testing
  const restore = [];
  for (const m of hull) for (const mat of [m.material].flat()) { restore.push([mat, mat.side]); mat.side = THREE.DoubleSide; }

  const ray = new THREE.Raycaster();
  const size = new THREE.Vector3(...hangar.size);
  const p = new THREE.Vector3();
  const world = new THREE.Vector3();
  const dirWorld = new THREE.Vector3();
  const rot = new THREE.Matrix3().setFromMatrix4(ship.matrixWorld);
  let inside = 0, total = 0;
  const misses = { px: 0, nx: 0, py: 0, ny: 0, nz: 0 };
  const names = ['px', 'nx', 'py', 'ny', 'nz'];
  for (let i = 0; i < grid[0]; i++) for (let j = 0; j < grid[1]; j++) for (let k = 0; k < grid[2]; k++) {
    p.set((i + 0.5) / grid[0] - 0.5, (j + 0.5) / grid[1] - 0.5, (k + 0.5) / grid[2] - 0.5).multiply(size).add(hangar.p);
    world.copy(p).applyMatrix4(ship.matrixWorld);
    let enclosed = true, odd = 0;
    DIRS.forEach((d, n) => {
      dirWorld.copy(d).applyMatrix3(rot).normalize();
      ray.set(world, dirWorld);
      const hits = ray.intersectObjects(hull, false).length;
      if (hits % 2 === 1) odd++;
      if (n < 5 && hits === 0) { enclosed = false; misses[names[n]]++; }
    });
    total++;
    if (enclosed || odd >= 4) inside++;
  }
  for (const [mat, side] of restore) mat.side = side;
  return { fraction: inside / total, samples: total, inside, misses };
}
