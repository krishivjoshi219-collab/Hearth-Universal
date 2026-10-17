/* Hearth — consumer landing page controller.
 *
 * The page works fully without JS (static copy + figures). This file only:
 *   1. hydrates the hero tray + stats strip with live numbers from the local
 *      MCP server (same origin; the preview runs offline-first, so failures
 *      are silent and the static figures stay),
 *   2. adds scroll-reveal and the sticky-nav shadow.
 *
 * CSP: loaded as an external file (script-src 'self'), no inline handlers.
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

  const targets = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    targets.forEach((el) => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
    );
    targets.forEach((el) => io.observe(el));
  }

  // ------------------------------------------------------------------ money

  const money = (v) => {
    const n = Number(v);
    return Number.isFinite(n)
      ? "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : null;
  };

  async function hydrateLive() {
    // Subscription audit: real figures from the running engine.
    try {
      const res = await fetch("/api/renewals", { headers: { Accept: "application/json" } });
      if (res.ok) {
        const d = await res.json();
        const saveEl = $("#statSaveVal");
        const total = money(d.potential_save_yr);
        if (saveEl && total) saveEl.textContent = total;

        const subsEl = $("#statSubsVal");
        if (subsEl && Array.isArray(d.renewals)) subsEl.textContent = String(d.renewals.length);

        // Feature the largest cancellable service in the hero tray card.
        const rows = Array.isArray(d.renewals) ? d.renewals : [];
        const worst = rows
          .filter((r) => r && r.recommendation !== "keep")
          .sort((a, b) => (b.savings_yr || 0) - (a.savings_yr || 0))[0];
        if (worst) {
          const nameEl = $("#heroLeakName");
          const saveHero = $("#heroLeakSave");
          const daysEl = $("#heroLeakDays");
          const verbEl = $("#heroLeakVerb");
          if (nameEl) nameEl.textContent = worst.name || "Unused subscription";
          if (saveHero && money(worst.savings_yr)) saveHero.textContent = money(worst.savings_yr);
          if (verbEl) {
            const rec = String(worst.recommendation || "").toLowerCase();
            verbEl.textContent = rec === "cancel" ? "Cancel" : rec === "downgrade" ? "Downgrade" : "Change";
          }
          if (daysEl) {
            const days = Number(worst.last_used_days);
            const fallback = /(\d+)\s*(?:days?|d)\b/i.exec(worst.usage_status || worst.reason || "");
            const n = Number.isFinite(days) && days > 0 ? String(days) : fallback ? fallback[1] : "";
            daysEl.textContent = n ? `dormant ${n} days` : "barely used";
          }
        }
      }
    } catch (_) { /* static figures remain */ }

    // Tool count from the live MCP server (spec 2025-11-25).
    try {
      const res = await fetch("/health", { headers: { Accept: "application/json" } });
      if (res.ok) {
        const d = await res.json();
        const toolsEl = $("#statTools");
        if (toolsEl && d.tools_count) toolsEl.textContent = String(d.tools_count);
      }
    } catch (_) { /* static figure remains */ }
  }

  hydrateLive();

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
