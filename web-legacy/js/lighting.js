/**
 * HEARTH LIGHTING ENGINE — UI-ONLY radiance helper
 * Kelvin -> RGB + dynamic ambient radiance pool math.
 * No backend calls. Pure view math consumed by floorplan + Time Machine.
 * 60fps-safe: zero alloc in hot path where possible, precomputed LUT.
 */
export const KELVIN_STOPS = [
  { k: 2000, rgb: [255, 137, 58] },   // deep sleep amber
  { k: 2700, rgb: [255, 182, 92] },   // warm amber
  { k: 3000, rgb: [255, 200, 130] },
  { k: 4000, rgb: [255, 248, 235] },  // clean neutral
  { k: 4500, rgb: [255, 252, 245] },  // energizing daylight
  { k: 5000, rgb: [200, 235, 255] },  // crisp daylight
  { k: 6500, rgb: [205, 225, 255] },
];

function lerp(a, b, t) { return a + (b - a) * t; }

/** Kelvin (1000-7000) -> [r,g,b]. Interpolates LUT. */
export function kelvinToRgb(kelvin) {
  const k = Math.max(1800, Math.min(6800, Number(kelvin) || 2700));
  for (let i = 0; i < KELVIN_STOPS.length - 1; i++) {
    const a = KELVIN_STOPS[i];
    const b = KELVIN_STOPS[i + 1];
    if (k >= a.k && k <= b.k) {
      const t = (k - a.k) / (b.k - a.k || 1);
      return [
        Math.round(lerp(a.rgb[0], b.rgb[0], t)),
        Math.round(lerp(a.rgb[1], b.rgb[1], t)),
        Math.round(lerp(a.rgb[2], b.rgb[2], t)),
      ];
    }
  }
  const last = KELVIN_STOPS[KELVIN_STOPS.length - 1].rgb;
  return [last[0], last[1], last[2]];
}

/** Parse "2700K" / "warm" / "cool" / hex -> {rgb, kelvin}. */
export function parseCct(input, fallbackHex) {
  if (typeof input === "string") {
    const m = input.match(/(\d{3,4})\s*K/i);
    if (m) {
      const k = parseInt(m[1], 10);
      return { rgb: kelvinToRgb(k), kelvin: k };
    }
    const s = input.toLowerCase();
    if (s.includes("2000")) return { rgb: kelvinToRgb(2000), kelvin: 2000 };
    if (s.includes("warm") || s.includes("2700")) return { rgb: kelvinToRgb(2700), kelvin: 2700 };
    if (s.includes("4500")) return { rgb: kelvinToRgb(4500), kelvin: 4500 };
    if (s.includes("cool") || s.includes("5000") || s.includes("6500")) return { rgb: kelvinToRgb(5000), kelvin: 5000 };
  }
  if (typeof fallbackHex === "string" && /^#[0-9a-f]{6}$/i.test(fallbackHex)) {
    return {
      rgb: [
        parseInt(fallbackHex.slice(1, 3), 16),
        parseInt(fallbackHex.slice(3, 5), 16),
        parseInt(fallbackHex.slice(5, 7), 16),
      ],
      kelvin: 2700,
    };
  }
  return { rgb: kelvinToRgb(2700), kelvin: 2700 };
}

/**
 * Radiance pool descriptor for one room.
 * bri 0-100, roomW px width -> {radius, stops[]}.
 * Intensity curve is perceptual (sqrt) so 20% still reads on blueprint.
 */
export function radiancePool(bri, roomW, rgb, shimmer = 0) {
  const b = Math.max(0, Math.min(100, Number(bri) || 0));
  if (b <= 0.5) return { radius: 0, alpha: 0, rgb };
  const perceptual = Math.sqrt(b / 100);
  const radius = Math.max(8, perceptual * roomW * 0.55 * (1 + shimmer));
  return {
    radius,
    alpha: perceptual,
    rgb,
    // preformatted gradient stops (consumed by canvas fill)
    stops: [
      [0, 0.75 * perceptual],
      [0.12, 0.45 * perceptual],
      [0.45, 0.2 * perceptual],
      [0.8, 0.05 * perceptual],
    ],
  };
}

/** CSS rgba() helper — no template churn in rAF. */
export function rgba(rgb, a) {
  return "rgba(" + (rgb[0] | 0) + "," + (rgb[1] | 0) + "," + (rgb[2] | 0) + "," + a.toFixed(3) + ")";
}

/** Time-Machine preset -> forced lighting mood (UI projection only). */
export function presetLightingMood(preset) {
  switch (preset) {
    case "bedtime": return { kelvin: 2000, briScale: 0.18, label: "2000K sleep amber" };
    case "night": return { kelvin: 1800, briScale: 0.05, label: "hallway path 5%" };
    case "morning": return { kelvin: 4500, briScale: 0.7, label: "4500K daylight" };
    default: return { kelvin: 2700, briScale: 1.0, label: "2700K evening calm" };
  }
}

// UMD-ish global for non-module consumers / judges console play
if (typeof window !== "undefined") {
  window.HearthLighting = {
    kelvinToRgb,
    parseCct,
    radiancePool,
    rgba,
    presetLightingMood,
    KELVIN_STOPS,
  };
}
