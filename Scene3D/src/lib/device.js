// Device tier. Phones and tablets get a "lite" scene: ship textures capped (the full set is
// ~2 GB of GPU texture memory, which mobile browsers kill the tab for), a lower pixel ratio,
// fewer MSAA samples and a smaller sun shadow map. ?lite=1 / ?lite=0 force either tier.
const params = new URLSearchParams(globalThis.location?.search || '');
const forced = params.get('lite');
const nav = globalThis.navigator || {};
const coarse = !!globalThis.matchMedia?.('(pointer: coarse)').matches && (nav.maxTouchPoints || 0) > 0;
const smallMemory = typeof nav.deviceMemory === 'number' && nav.deviceMemory <= 4;
const mobileUA = /Android|iPhone|iPad|iPod|Mobile/i.test(nav.userAgent || '');

export const LITE = forced === '1' || (forced !== '0' && (coarse || smallMemory || mobileUA));

export const TIER = LITE
  ? { pixelRatio: 1.5, samples: 2, shadowSize: 2048 }
  : { pixelRatio: 2, samples: 4, shadowSize: 4096 };
