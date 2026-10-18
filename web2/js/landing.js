/* Hearth — consumer landing page controller.
 *
 * The page works fully without JS (static copy + figures). This file only:
 *   1. hydrates the hero device frame and stats strip with live numbers from
 *      the local server (same origin; the preview runs offline-first, so
 *      failures are silent and the static figures stay),
 *   2. runs the little clock in the device frame,
 *   3. adds the scroll-reveal, the sticky-nav shadow, and a gentle pointer
 *      tilt on the device frame.
 *
 * CSP: external file (script-src 'self'), no inline handlers, and style is
 * only ever touched through CSS custom properties (style-src 'self' blocks
 * inline style attributes; CSSOM property writes are unaffected).
 */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ------------------------------------------------------------- nav chrome

  const nav = $("#nav");
  if (nav) {
    const sync = () => nav.classList.toggle("scrolled", window.scrollY > 8);
    sync();
    window.addEventListener("scroll", sync, { passive: true });
  }

  // ----------------------------------------------------------------- reveal
  //
  // Deterministic scroll-reveal (no IntersectionObserver): the sweep runs at
  // parse time, on load, on scroll (rAF-throttled) and on resize. Elements in
  // view when the script evaluates are marked before first paint, so the hero
  // is complete from frame one — important for screen captures.

  const reveals = Array.from(document.querySelectorAll(".reveal"));

  const revealSweep = () => {
    const vh = window.innerHeight;
    for (let i = reveals.length - 1; i >= 0; i--) {
      const el = reveals[i];
      const r = el.getBoundingClientRect();
      if (r.top < vh * 0.94 && r.bottom > -60) {
        el.classList.add("in");
        reveals.splice(i, 1);
      }
    }
  };

  if (reduceMotion) {
    reveals.forEach((el) => el.classList.add("in"));
  } else {
    revealSweep();
    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        revealSweep();
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    window.addEventListener("load", onScroll);
    window.setTimeout(onScroll, 900); // fonts/layout settle
  }


  // ------------------------------------------------------------------ clock

  const clockEl = $("#heroClock");
  const dateEl = $("#heroDate");
  if (clockEl && dateEl) {
    const tick = () => {
      const now = new Date();
      let h = now.getHours();
      const m = String(now.getMinutes()).padStart(2, "0");
      const ampm = h >= 12 ? "PM" : "AM";
      h = h % 12 || 12;
      clockEl.textContent = `${h}:${m} ${ampm}`;
      dateEl.textContent = now.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
      });
    };
    tick();
    window.setInterval(tick, 30000);
  }

  // ------------------------------------------------------------------ money

  const money = (v) => {
    const n = Number(v);
    return Number.isFinite(n)
      ? "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : null;
  };

  // Count a numeric element up to its target (tab-safe, motion-respecting).
  function countUp(el, target, render, ms) {
    if (!el || !Number.isFinite(target)) return;
    if (reduceMotion || ms <= 0) {
      el.textContent = render(target);
      return;
    }
    const t0 = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const step = (now) => {
      const t = Math.min(1, (now - t0) / ms);
      el.textContent = render(target * ease(t));
      if (t < 1) requestAnimationFrame(step);
      else el.textContent = render(target);
    };
    requestAnimationFrame(step);
  }

  // ------------------------------------------------------------- live numbers

  async function hydrateRenewals() {
    try {
      const res = await fetch("/api/renewals", { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const d = await res.json();

      // The hero headline number.
      const big = $("#heroBig");
      if (big && Number.isFinite(Number(d.potential_save_yr))) {
        countUp(big, Number(d.potential_save_yr), (v) => money(Math.round(v * 100) / 100), 1100);
      }

      // Stats strip.
      const saveEl = $("#statSaveVal");
      if (saveEl && Number.isFinite(Number(d.potential_save_yr))) {
        countUp(saveEl, Number(d.potential_save_yr), (v) => money(Math.round(v * 100) / 100), 1100);
      }
      const subsEl = $("#statSubsVal");
      if (subsEl && Array.isArray(d.renewals)) subsEl.textContent = String(d.renewals.length);

      // Tie the headline number to its story: how many services it comes from.
      const verdictEl = $("#heroVerdict");
      if (verdictEl && Array.isArray(d.renewals)) {
        const n = d.renewals.filter(
          (r) => r && String(r.recommendation || "").toLowerCase() !== "keep"
        ).length;
        if (n > 0) {
          verdictEl.textContent =
            n === 1
              ? "found in one service nobody uses."
              : `found in ${n} services nobody uses.`;
        }
      }

      // Feature the cleanest cancel in the device frame (the frame's second
      // and third story rows stay static copy).
      const rows = Array.isArray(d.renewals) ? d.renewals : [];
      const cancels = rows
        .filter((r) => r && String(r.recommendation || "").toLowerCase() === "cancel")
        .sort((a, b) => (b.savings_yr || 0) - (a.savings_yr || 0));
      const worst = cancels[0] || rows.filter((r) => r && r.recommendation !== "keep")[0];
      if (worst) {
        const nameEl = $("#heroLeakName");
        const saveHero = $("#heroLeakSave");
        const metaEl = $("#heroLeakMeta");
        const s = money(worst.savings_yr);
        if (nameEl && worst.name) nameEl.textContent = worst.name;
        if (saveHero && s) saveHero.textContent = s;
        if (metaEl) {
          const days = Number(worst.last_used_days);
          const fallback = /(\d+)\s*(?:days?|d)\b/i.exec(worst.usage_status || worst.reason || "");
          const n = Number.isFinite(days) && days > 0 ? String(days) : fallback ? fallback[1] : "";
          const verb =
            String(worst.recommendation || "").toLowerCase() === "cancel"
              ? "cancels cleanly"
              : "worth a change";
          metaEl.textContent = n ? `dormant ${n} days · ${verb}` : verb;
        }
      }
    } catch (_) { /* static figures remain */ }
  }

  async function hydrateHealth() {
    try {
      const res = await fetch("/health", { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const d = await res.json();
      if (d.tools_count) {
        ["#statTools", "#statTools2"].forEach((sel) => {
          const el = $(sel);
          if (el) el.textContent = String(d.tools_count);
        });
      }
    } catch (_) { /* static figure remains */ }
  }

  hydrateRenewals();
  hydrateHealth();

  // ------------------------------------------------------------- device tilt

  const visual = $("#heroVisual");
  const device = $("#heroDevice");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (visual && device && finePointer && !reduceMotion) {
    let raf = 0;
    let lastEv = null;
    const apply = () => {
      raf = 0;
      if (!lastEv) return;
      const r = visual.getBoundingClientRect();
      const x = (lastEv.clientX - r.left) / r.width - 0.5;
      const y = (lastEv.clientY - r.top) / r.height - 0.5;
      device.style.setProperty("--ry", `${(x * 3.6).toFixed(2)}deg`);
      device.style.setProperty("--rx", `${(-y * 2.8).toFixed(2)}deg`);
    };
    visual.addEventListener("pointermove", (ev) => {
      lastEv = ev;
      if (!raf) raf = requestAnimationFrame(apply);
    });
    visual.addEventListener("pointerleave", () => {
      lastEv = null;
      device.style.setProperty("--rx", "0deg");
      device.style.setProperty("--ry", "0deg");
    });
  }

  // --------------------------------------------------------------- niceties

  // Smooth-scroll fallback for browsers without CSS scroll-behavior.
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (ev) => {
      const target = document.querySelector(a.getAttribute("href"));
      if (!target) return;
      ev.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    });
  });
})();
