// Placeholder planet (to be replaced by the full procedural planet).
import * as THREE from 'three';
import { SUN_DIR } from './lighting.js';

export function createPlanet(scene, { radius = 6000, position = new THREE.Vector3(0, -6800, -2500) } = {}) {
  const group = new THREE.Group();
  group.name = 'planet';
  group.position.copy(position);
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 128, 64),
    new THREE.MeshStandardMaterial({ color: '#2a5fa8', roughness: 0.8 }),
  );
  group.add(mesh);
  scene.add(group);
  return { group, radius, update() {}, sunDir: SUN_DIR };
}
