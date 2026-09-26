// Tiny shared registry so environment modules can see each other without
// changing their public signatures (the sky needs the planet to occlude the sun).
export const ENV = {
  planet: null, // { center: Vector3 (world), radius, top } once createPlanet() ran
};
