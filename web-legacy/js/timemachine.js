/**
 * HEARTH TIME MACHINE — UI-ONLY temporal scrubber enhancement.
 * Adds a continuous 0..3 slider (Live/Bedtime/Deep Night/Morning) on top of the
 * existing preset chips. Debounced POST /api/timemachine (same contract as app.js),
 * projects solar/battery + night-vision tint + replenishment hints.
 *
 * Does NOT touch polling: /api/home fetchState + /api/heartbeat intervals in
 * twin.js / app.js remain the single source of truth for live telemetry.
 * This module only renders *projections* into dedicated overlay nodes.
 */
import { presetLightingMood } from "./lighting.js";

export const TM_ORDER = ["now", "bedtime", "night", "morning"];
export const TM_LABELS = {
  now: "Live (8:50 PM)",
  bedtime: "Bedtime (11:00 PM)",
  night: "Deep Night (3:00 AM)",
  morning: "Morning Wake (7:30 AM)",
};

const DEBOUNCE_MS = 180;
const NIGHT_PRESETS = new Set(["bedtime", "night"]);

function el(id) { return document.getElementById(id); }

function fmtKw(v, digits = 2) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export function renderProjectionOverlay(forecast, preset) {
  const bar = el("tmProjectionBar");
  if (!bar || !forecast) return;
  const solar = Number(forecast.solar_kw ?? 0);
  const grid = Number(forecast.grid_draw_kw ?? 0);
  const batt = Number(forecast.battery_pct ?? 0);
  const mood = presetLightingMood(preset);
  const night = NIGHT_PRESETS.has(preset);

  const flow = solar > 0
    ? "☀️ Solar +" + fmtKw(solar) + " kW"
    : "🌙 Grid " + fmtKw(grid) + " kW · Battery " + batt + "%";
  const battTone = batt >= 85 ? "var(--emerald)" : batt >= 75 ? "var(--amber)" : "var(--rose)";

  bar.innerHTML =
    '<span class="tm-proj-chip" title="Projected generation vs draw">⚡ ' + flow + "</span>" +
    '<span class="tm-proj-chip" title="Projected battery reserve" style="color:' + battTone + '">🔋 ' + batt + "% reserve</span>" +
    '<span class="tm-proj-chip" title="Projected lighting mood">💡 ' + mood.label + "</span>" +
    '<span class="tm-proj-chip ' + (night ? "night" : "") + '" title="Ring camera mode">' +
      (night ? "🌌 IR night vision 850nm" : "📷 " + (forecast.ring_cam_mode || "Color HDR")) + "</span>" +
    '<span class="tm-proj-chip pantry" title="Pantry replenishment hint">🛒 ' + (forecast.pantry_alert || "Pantry nominal") + "</span>";

  bar.dataset.preset = preset;
  bar.classList.toggle("is-night", night);
}

export function applyNightVisionTint(preset) {
  const stage = el("floorplanStage");
  if (!stage) return;
  const night = NIGHT_PRESETS.has(preset);
  stage.classList.toggle("tm-night-tint", preset === "bedtime");
  stage.classList.toggle("tm-deep-night-tint", preset === "night");
  stage.classList.toggle("tm-morning-tint", preset === "morning");
  // Hint the twin engine (same setter app.js uses) without extra fetches
  try {
    if (window.hearthApp && window.hearthApp.twin) {
      window.hearthApp.twin.setNightVision(night);
    }
  } catch (e) { /* view-only */ }
}

function syncChips(preset) {
  document.querySelectorAll("#timeMachineChips .tm-preset-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.preset === preset);
  });
  const slider = el("tmScrub");
  if (slider) {
    slider.value = String(TM_ORDER.indexOf(preset));
    slider.setAttribute("aria-valuetext", TM_LABELS[preset] || preset);
  }
}

let debounceTimer = 0;
let lastPreset = "now";
let inFlight = 0;

export async function applyPreset(preset, opts = {}) {
  if (!TM_ORDER.includes(preset)) preset = "now";
  lastPreset = preset;
  const apiBase = (window.hearthApp && window.hearthApp.apiBase) || window.location.origin;
  syncChips(preset);

  // Instant view feedback (no network wait): tint + cached mood label
  if (!opts.deferView) applyNightVisionTint(preset);

  // Debounced network projection (judges can scrub fast at 60fps)
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    const my = ++inFlight;
    try {
      const res = await fetch(apiBase + "/api/timemachine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset }),
      });
      const data = await res.json();
      if (my !== inFlight) return; // stale scrub wins
      if (!data || !data.ok || !data.forecast) return;
      if (lastPreset !== preset) return;
      renderProjectionOverlay(data.forecast, preset);
      applyNightVisionTint(preset);
      const tag = el("tmNarrativeTag");
      if (tag) tag.textContent = data.forecast.narrative || tag.textContent;
      const sliderHint = el("tmScrubHint");
      if (sliderHint) {
        sliderHint.textContent =
          data.forecast.label + " · ☀️" + fmtKw(data.forecast.solar_kw) +
          " kW · 🔋" + data.forecast.battery_pct + "% · " + (data.forecast.sun_phase || "");
      }
    } catch (e) {
      /* silent: projection is advisory, live polling untouched */
    }
  }, opts.instant ? 0 : DEBOUNCE_MS);
}

function bindScrubber() {
  const slider = el("tmScrub");
  if (!slider || slider.dataset.bound) return;
  slider.dataset.bound = "1";
  slider.addEventListener("input", () => {
    const idx = Math.max(0, Math.min(3, parseInt(slider.value, 10) || 0));
    applyPreset(TM_ORDER[idx]);
  });
  // Keyboard a11y already native to <input type=range>; announce via aria
  slider.addEventListener("change", () => {
    const idx = Math.max(0, Math.min(3, parseInt(slider.value, 10) || 0));
    applyPreset(TM_ORDER[idx], { instant: true });
  });
}

function bindChipsMirror() {
  const chips = document.querySelectorAll("#timeMachineChips .tm-preset-btn");
  chips.forEach((btn) => {
    if (btn.dataset.tmMirror) return;
    btn.dataset.tmMirror = "1";
    btn.addEventListener("click", () => {
      const p = btn.dataset.preset;
      if (TM_ORDER.includes(p)) {
        lastPreset = p;
        syncChips(p);
        // app.js handler still fires its own POST; we only mirror view + overlay
        setTimeout(() => {
          const slider = el("tmScrub");
          if (slider) slider.value = String(TM_ORDER.indexOf(p));
          applyNightVisionTint(p);
        }, 0);
        // Fetch our richer overlay (debounced, harmless duplicate of app.js call)
        applyPreset(p);
      }
    });
  });
}

function boot() {
  bindScrubber();
  bindChipsMirror();
  // Seed overlay from server once (instant, non-blocking, no polling change)
  try { applyPreset("now", { instant: false }); } catch (e) {}
  if (typeof window !== "undefined") {
    window.HearthTimeMachine = { applyPreset, TM_ORDER, TM_LABELS };
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
  boot();
}
