/**
 * CANVAS-AMBIENT — Echo Show fluid layer (UI ONLY).
 * Glanceable countertop mode, 60fps pointer glow (rAF, transform-only),
 * Alexa light-wave + chime sync pulse, keyboard/D-pad nav,
 * loading/empty/error states, prefers-reduced-motion.
 * Keeps existing IDs/endpoints (/api/chat, /mcp) untouched.
 */
(function () {
  "use strict";
  if (window.__HEARTH_AMBIENT_LOADED__) return;
  window.__HEARTH_AMBIENT_LOADED__ = true;

  var GLANCE_KEY = "hearth.glance.v1";
  var root = document.documentElement;
  var body = document.body;

  /* ---------- prefers-reduced-motion ---------- */
  var motionQuery = null;
  try {
    motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  } catch (e) { /* noop */ }
  function applyMotion() {
    var reduced = !!(motionQuery && motionQuery.matches);
    root.dataset.motion = reduced ? "reduced" : "full";
    body.dataset.motion = reduced ? "reduced" : "full";
    window.__HEARTH_REDUCED_MOTION__ = reduced;
  }
  applyMotion();
  if (motionQuery && motionQuery.addEventListener) {
    motionQuery.addEventListener("change", applyMotion);
  }

  var reducedMotion = function () {
    return root.dataset.motion === "reduced";
  };

  /* ---------- Glanceable ambient countertop mode ---------- */
  var glanceBtn = document.getElementById("btnGlanceToggle");
  function setGlance(on, persist) {
    body.dataset.density = on ? "glance" : "detail";
    if (glanceBtn) glanceBtn.setAttribute("aria-pressed", on ? "true" : "false");
    if (glanceBtn) {
      var label = glanceBtn.querySelector("span:last-child") || glanceBtn;
      void label;
      glanceBtn.innerHTML = on ? "☀️ Detail" : "🌙 Glance";
    }
    try {
      if (persist !== false) localStorage.setItem(GLANCE_KEY, on ? "1" : "0");
    } catch (e) { /* private mode */ }
  }
  function initGlance() {
    var on = false;
    try {
      on = localStorage.getItem(GLANCE_KEY) === "1";
    } catch (e) { /* noop */ }
    // Auto-suggest glance on very wide countertop TVs with no interaction yet
    if (!on && window.innerWidth >= 1700) on = false;
    setGlance(on, false);
    if (glanceBtn) {
      glanceBtn.addEventListener("click", function () {
        setGlance(body.dataset.density !== "glance");
      });
    }
  }

  /* ---------- 60fps pointer glow: rAF-throttled CSS vars (no layout thrash) ---------- */
  function initAmbientGlow() {
    var glow = document.getElementById("ambient-glow");
    if (!glow) return;
    if (reducedMotion()) return;
    var pending = false;
    var px = 50, py = 25;
    function flush() {
      pending = false;
      glow.style.setProperty("--mouse-x", px.toFixed(2) + "%");
      glow.style.setProperty("--mouse-y", py.toFixed(2) + "%");
    }
    window.addEventListener("pointermove", function (ev) {
      if (pending) return;
      pending = true;
      px = (ev.clientX / Math.max(window.innerWidth, 1)) * 100;
      py = (ev.clientY / Math.max(window.innerHeight, 1)) * 100;
      requestAnimationFrame(flush);
    }, { passive: true });
  }

  /* ---------- Alexa light-wave + chime sync (transform/opacity pulse) ---------- */
  function initWaveSync() {
    var wrapper = document.getElementById("glowWaveWrapper");
    if (!wrapper) return;
    var timer = null;
    function pulse(ms) {
      wrapper.classList.add("is-pulsing");
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        wrapper.classList.remove("is-pulsing");
      }, ms || 900);
    }
    // Observe orb state text changes (listening/thinking/speaking) -> pulse
    var orbText = document.getElementById("orbStatusText");
    if (orbText && window.MutationObserver) {
      new MutationObserver(function () { pulse(900); }).observe(orbText, {
        childList: true, characterData: true, subtree: true
      });
    }
    // Wrap WebAudio chime entry points once the app boots (no endpoint changes)
    var tries = 0;
    var wrapTimer = setInterval(function () {
      tries += 1;
      var app = window.hearthApp;
      if (app && app.voice) {
        ["playEchoPing", "playSuccessChime", "playWarningTone", "playBarcodeBeep"].forEach(function (name) {
          var fn = app.voice[name];
          if (typeof fn === "function" && !fn.__hearthWrapped) {
            var orig = fn.bind(app.voice);
            var wrapped = function () {
              pulse(name === "playSuccessChime" ? 1200 : 700);
              return orig.apply(null, arguments);
            };
            wrapped.__hearthWrapped = true;
            app.voice[name] = wrapped;
          }
        });
      }
      if (tries > 100) clearInterval(wrapTimer);
    }, 500);
    // Doorbell / proactive buttons also pulse instantly (before network round-trip)
    ["ringSimulateBtn", "proactiveTickBtn", "orbPingBtn"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("click", function () { pulse(900); });
    });
  }

  /* ---------- View-mode toggle: a11y tabs + keyboard/D-pad ---------- */
  function initViewModes() {
    var btnCanvas = document.getElementById("btnModeCanvas");
    var btnOps = document.getElementById("btnModeOps");
    var canvasView = document.getElementById("canvasViewSection");
    var opsView = document.getElementById("operationsViewSection");
    if (!btnCanvas || !btnOps) return;
    function select(btn) {
      [btnCanvas, btnOps].forEach(function (b) {
        var active = b === btn;
        b.classList.toggle("active", active);
        b.setAttribute("aria-selected", active ? "true" : "false");
        b.tabIndex = active ? 0 : -1;
      });
      // Let the canonical app controller own display logic if present;
      // mirror hidden attributes for AT + glance CSS.
      if (btn === btnCanvas) {
        if (canvasView) canvasView.hidden = false;
        if (opsView) opsView.hidden = true;
      } else {
        if (canvasView) canvasView.hidden = true;
        if (opsView) opsView.hidden = false;
      }
    }
    [btnCanvas, btnOps].forEach(function (btn) {
      btn.addEventListener("click", function () { select(btn); });
      btn.addEventListener("keydown", function (ev) {
        if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") {
          ev.preventDefault();
          var next = btn === btnCanvas ? btnOps : btnCanvas;
          next.focus();
          next.click();
        }
      });
    });
    // Global shortcuts: 1/2 views, G glance, / composer, Esc closes modals
    document.addEventListener("keydown", function (ev) {
      var tag = (ev.target && ev.target.tagName) || "";
      var typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
      if (ev.key === "Escape") {
        ["barcodeModal", "inspectionModal"].forEach(function (id) {
          var m = document.getElementById(id);
          if (!m) return;
          if (m.classList) m.classList.remove("open");
          if (m.style) m.style.display = "none";
          m.setAttribute("aria-hidden", "true");
        });
        return;
      }
      if (typing) return;
      if (ev.key === "1") btnCanvas.click();
      else if (ev.key === "2") btnOps.click();
      else if (ev.key === "g" || ev.key === "G") {
        if (glanceBtn) glanceBtn.click();
      } else if (ev.key === "/") {
        var input = document.getElementById("composerInput");
        if (input) { ev.preventDefault(); input.focus(); }
      }
    });
    // D-pad friendly: Enter/Space on focused widget card activates first action
    var grid = document.getElementById("ambientGrid");
    if (grid) {
      grid.addEventListener("keydown", function (ev) {
        var cards = Array.prototype.slice.call(grid.querySelectorAll(".widget-card"));
        var idx = cards.indexOf(document.activeElement);
        if (idx < 0) return;
        var cols = window.innerWidth <= 680 ? 1 : window.innerWidth <= 1100 ? 2 : 3;
        if (ev.key === "ArrowRight") { ev.preventDefault(); (cards[idx + 1] || cards[0]).focus(); }
        else if (ev.key === "ArrowLeft") { ev.preventDefault(); (cards[idx - 1] || cards[cards.length - 1]).focus(); }
        else if (ev.key === "ArrowDown") { ev.preventDefault(); (cards[idx + cols] || cards[idx]).focus(); }
        else if (ev.key === "ArrowUp") { ev.preventDefault(); (cards[idx - cols] || cards[idx]).focus(); }
        else if (ev.key === "Enter" || ev.key === " ") {
          if (document.activeElement === cards[idx] && ev.target === cards[idx]) {
            ev.preventDefault();
            var btn = cards[idx].querySelector("button");
            if (btn) btn.click();
          }
        }
      });
    }
    // Canvas keyboard ops: Ring preview Enter = doorbell; floorplan arrows cycle rooms
    var ring = document.getElementById("ringCamCanvas");
    if (ring) {
      ring.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          var b = document.getElementById("ringSimulateBtn");
          if (b) b.click();
        }
      });
    }
  }

  /* ---------- Loading / empty / error states (no endpoint changes) ---------- */
  function initAsyncStates() {
    var stream = document.getElementById("conversationStream");
    var empty = document.getElementById("conversationEmpty");
    var errBox = document.getElementById("conversationError");
    var errText = document.getElementById("conversationErrorText");
    var retryBtn = document.getElementById("conversationRetryBtn");
    var banner = document.getElementById("netErrorBanner");
    var bannerText = document.getElementById("netErrorText");
    var netRetry = document.getElementById("netRetryBtn");
    var radar = document.getElementById("depletionRadarFeed");
    var lastMessage = null;

    function refreshEmpty() {
      if (!stream || !empty) return;
      var has = stream.children.length > 0;
      empty.hidden = has;
      stream.setAttribute("aria-busy", "false");
    }
    if (stream && window.MutationObserver) {
      new MutationObserver(refreshEmpty).observe(stream, { childList: true });
    }
    refreshEmpty();

    function showNetError(msg) {
      if (banner) banner.hidden = false;
      if (msg && bannerText) bannerText.textContent = msg;
      if (errBox) errBox.hidden = false;
      if (msg && errText) errText.textContent = msg;
    }
    function clearNetError() {
      if (banner) banner.hidden = true;
      if (errBox) errBox.hidden = true;
    }
    window.addEventListener("online", clearNetError);
    window.addEventListener("offline", function () {
      showNetError("You are offline — showing last known household state.");
    });
    if (netRetry) netRetry.addEventListener("click", function () { clearNetError(); });
    if (retryBtn) retryBtn.addEventListener("click", function () {
      clearNetError();
      var app = window.hearthApp;
      if (app && lastMessage) app.sendMessage(lastMessage);
    });

    // Capture last user message for retry (capture phase, before app handler clears input)
    var form = document.getElementById("composerForm");
    var input = document.getElementById("composerInput");
    if (form && input) {
      form.addEventListener("submit", function () {
        lastMessage = input.value.trim() || lastMessage;
        if (errBox) errBox.hidden = true;
      }, true);
    }

    // Global fetch failure sniffer: only surfaces chat/commerce failures, never breaks app
    if (window.fetch && !window.fetch.__hearthWrapped) {
      var origFetch = window.fetch.bind(window);
      var wrappedFetch = function (url, opts) {
        return origFetch(url, opts).then(function (res) {
          if (!res.ok && typeof url === "string" && /\/api\/(chat|commerce|proposals|home)/.test(url)) {
            showNetError("Request failed (" + res.status + ") — showing last known household state.");
            setTimeout(clearNetError, 6000);
          } else if (res.ok && typeof url === "string" && /\/api\/chat/.test(url)) {
            clearNetError();
          }
          return res;
        }, function (err) {
          if (typeof url === "string" && /\/api\//.test(url)) {
            showNetError("Network error — showing last known household state.");
            setTimeout(clearNetError, 6000);
          }
          throw err;
        });
      };
      wrappedFetch.__hearthWrapped = true;
      window.fetch = wrappedFetch;
    }

    // Depletion radar: drop skeleton once real rows render
    if (radar && window.MutationObserver) {
      var radarObs = new MutationObserver(function () {
        var hasRows = radar.querySelector(".depletion-row");
        if (hasRows) {
          radar.classList.remove("is-loading");
          radar.setAttribute("aria-busy", "false");
          radarObs.disconnect();
        }
      });
      radarObs.observe(radar, { childList: true });
      // Safety: if backend never responds, swap skeleton for a graceful empty note
      setTimeout(function () {
        if (!radar.querySelector(".depletion-row") && !radar.querySelector("[data-radar-empty]")) {
          radar.classList.remove("is-loading");
          radar.setAttribute("aria-busy", "false");
          var div = document.createElement("div");
          div.setAttribute("data-radar-empty", "true");
          div.className = "conversation-empty";
          div.innerHTML = "<strong>Pantry data unavailable</strong><p>Check connection, then retry. Showing cached staples.</p>";
          radar.appendChild(div);
        }
      }, 9000);
    }
  }

  function init() {
    initGlance();
    initAmbientGlow();
    initWaveSync();
    initViewModes();
    initAsyncStates();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
