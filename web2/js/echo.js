/* ============================================================================
   Hearth — Echo surface logic ("Ambient OS", rebuilt from scratch).
   A quiet device: household state, the ask → answer theater, the living log
   (approvals + receipts), the settings sheet, the bring-your-own-brain
   dialog, and voice. The MCP server owns every action; this file only speaks
   to real endpoints and shows only consumer-facing language.
   ========================================================================= */
(function () {
  "use strict";

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------------ dom */
  function $(sel) { return document.querySelector(sel); }

  function icon(name, cls) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", cls || "ico");
    svg.setAttribute("aria-hidden", "true");
    var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "#i-" + name);
    svg.appendChild(use);
    return svg;
  }

  var el = {
    stage: $("#stage"),
    orbGlyph: $("#orbGlyph"),
    voiceWave: $("#voiceWave"),
    said: $("#said"),
    sceneLine: $("#sceneLine"),
    vTemp: $("#vTemp"),
    vClimate: $("#vClimate"),
    vDraw: $("#vDraw"),
    vSolar: $("#vSolar"),
    vLock: $("#vLock"),
    vLights: $("#vLights"),
    vPantry: $("#vPantry"),
    vPantryName: $("#vPantryName"),
    answer: $("#answer"),
    answerKicker: $("#answerKicker"),
    answerBig: $("#answerBig"),
    answerVerdict: $("#answerVerdict"),
    answerSub: $("#answerSub"),
    answerLines: $("#answerLines"),
    trustStrip: $("#trustStrip"),
    answerCta: $("#answerCta"),
    response: $("#response"),
    ticker: $("#ticker"),
    rail: $(".rail"),
    connChip: $("#connChip"),
    connDot: $("#connDot"),
    connText: $("#connText"),
    statusBody: $("#statusBody"),
    trayCount: $("#trayCount"),
    trayLead: $("#trayLead"),
    trayBody: $("#trayBody"),
    proofChainPill: $("#proofChainPill"),
    proofTotal: $("#proofTotal"),
    proofSub: $("#proofSub"),
    askForm: $("#askForm"),
    askText: $("#askText"),
    askSend: $("#askSend"),
    micBtn: $("#micBtn"),
    askLane: $("#askLane"),
    moreAsksBtn: $("#moreAsksBtn"),
    settingsBtn: $("#settingsBtn"),
    settingsPanel: $("#settingsPanel"),
    settingsCloseBtn: $("#settingsCloseBtn"),
    brainBtn: $("#brainBtn"),
    brainDot: $("#brainDot"),
    brainLabel: $("#brainLabel"),
    brainCallout: $("#brainCallout"),
    personaToggleBtn: $("#personaToggleBtn"),
    personaLabel: $("#personaToggleBtn") ? $("#personaToggleBtn").querySelector("span") : null,
    personaNote: $("#personaToggleBtn") ? $("#personaToggleBtn").querySelector(".row-note") : null,
    clockTime: $("#clockTime"),
    clockDate: $("#clockDate"),
    receiptBackdrop: $("#receiptBackdrop"),
    receiptTitle: $("#receiptTitle"),
    receiptSub: $("#receiptSub"),
    receiptCode: $("#receiptCode"),
    receiptBody: $("#receiptBody"),
    receiptDoneBtn: $("#receiptDoneBtn"),
    receiptUndoBtn: $("#receiptUndoBtn"),
    receiptCloseBtn: $("#receiptCloseBtn"),
    keyBackdrop: $("#keyBackdrop"),
    keyProvider: $("#keyProvider"),
    keyBaseUrlField: $("#keyBaseUrlField"),
    keyBaseUrl: $("#keyBaseUrl"),
    keyModelField: $("#keyModelField"),
    keyModel: $("#keyModel"),
    keyApiKeyField: $("#keyApiKeyField"),
    keyApiKey: $("#keyApiKey"),
    keyRegionField: $("#keyRegionField"),
    keyRegion: $("#keyRegion"),
    keyAccessField: $("#keyAccessField"),
    keyAccess: $("#keyAccess"),
    keySecretField: $("#keySecretField"),
    keySecret: $("#keySecret"),
    keyNote: $("#keyNote"),
    keyStatus: $("#keyStatus"),
    keySaveBtn: $("#keySaveBtn"),
    keyTestBtn: $("#keyTestBtn"),
    keyClearBtn: $("#keyClearBtn"),
    keyCloseBtn: $("#keyCloseBtn"),
    splash: $("#splash"),
    splashStart: $("#splashStart"),
    tourbar: $("#tourbar"),
    tourCap: $("#tourCap"),
    toast: $("#toast"),
    live: $("#live"),
  };

  /* ---------------------------------------------------------------- utils */
  function num(v, digits) {
    var n = Number(v);
    return isFinite(n) ? n.toFixed(digits == null ? 0 : digits) : "--";
  }
  function cToF(c) {
    var n = Number(c);
    return isFinite(n) ? n * 9 / 5 + 32 : null;
  }
  function usd(n) {
    var v = Number(n);
    if (!isFinite(v)) return "$--";
    var sign = v < 0 ? "-" : "";
    return sign + "$" + Math.abs(v).toFixed(2);
  }
  function shortHash(h, n) {
    var s = String(h || "");
    return s ? s.slice(0, n || 10) + "…" : "—";
  }
  function titleCase(s) {
    return String(s || "").replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }
  function stripMd(s) {
    return String(s || "").replace(/\*\*/g, "").replace(/\*/g, "").trim();
  }
  function firstSentence(text) {
    var t = stripMd(text);
    var m = t.match(/^.*?[.!?](?=\s|$)/);
    var s = m ? m[0] : t;
    if (s.length > 150) s = s.slice(0, 147).replace(/\s+\S*$/, "") + "…";
    return s;
  }
  function restAfterFirst(text) {
    var t = stripMd(text);
    var m = t.match(/^.*?[.!?](?=\s|$)/);
    if (!m) return "";
    var rest = t.slice(m[0].length).trim();
    return rest.length > 320 ? rest.slice(0, 317) + "…" : rest;
  }
  function timeLabel(ts) {
    var n = Number(ts);
    if (!isFinite(n) || n <= 0) return "";
    var d = new Date(n < 1e12 ? n * 1000 : n);
    return d.toTimeString().slice(0, 5);
  }
  function announce(text) {
    if (el.live) el.live.textContent = String(text || "").slice(0, 300);
  }
  var toastTimer = null;
  function toast(msg, ms) {
    if (!el.toast) return;
    el.toast.textContent = msg;
    el.toast.hidden = false;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.toast.hidden = true; }, ms || 2800);
  }

  async function getJSON(path) {
    try {
      var r = await fetch(path, { headers: { Accept: "application/json" } });
      if (!r.ok) return null;
      return await r.json();
    } catch (e) {
      return null;
    }
  }
  async function postJSON(path, body) {
    try {
      var r = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      var d = null;
      try { d = await r.json(); } catch (e2) { d = null; }
      return { ok: r.ok, status: r.status, data: d };
    } catch (e) {
      return { ok: false, status: 0, data: null };
    }
  }

  /* ----------------------------------------------------------------- clock */
  function tickClock() {
    var d = new Date();
    if (el.clockTime) {
      el.clockTime.textContent = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    }
    if (el.clockDate) {
      el.clockDate.textContent = d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
    }
  }

  /* ----------------------------------------------------------------- motes */
  (function motes() {
    var canvas = document.getElementById("motes");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    var W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
    var parts = [];
    var COUNT = 30;

    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width = W * DPR;
      canvas.height = H * DPR;
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    }
    function seed() {
      parts = [];
      for (var i = 0; i < COUNT; i++) {
        parts.push({
          x: Math.random() * W,
          y: Math.random() * H,
          r: 0.6 + Math.random() * 1.6,
          v: 0.05 + Math.random() * 0.18,
          w: Math.random() * Math.PI * 2,
          a: 0.04 + Math.random() * 0.16,
          warm: Math.random() < 0.75,
        });
      }
    }
    function frame(t) {
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        if (!reducedMotion) {
          p.y -= p.v;
          p.x += Math.sin(t / 2600 + p.w) * 0.08;
          if (p.y < -8) { p.y = H + 8; p.x = Math.random() * W; }
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.warm
          ? "rgba(255, 196, 122, " + p.a + ")"
          : "rgba(186, 210, 255, " + p.a * 0.8 + ")";
        ctx.fill();
      }
      if (!reducedMotion) requestAnimationFrame(frame);
    }
    resize();
    seed();
    window.addEventListener("resize", function () { resize(); seed(); });
    frame(0);
  })();

  /* ---------------------------------------------------------------- tilt */
  (function tilt() {
    if (reducedMotion) return;
    var root = document.documentElement;
    var rx = 0, ry = 0, tx = 0, ty = 0, raf = null;

    function apply() {
      raf = null;
      rx += (tx - rx) * 0.12;
      ry += (ty - ry) * 0.12;
      root.style.setProperty("--rx", rx.toFixed(3) + "deg");
      root.style.setProperty("--ry", ry.toFixed(3) + "deg");
      if (Math.abs(tx - rx) > 0.01 || Math.abs(ty - ry) > 0.01) raf = requestAnimationFrame(apply);
    }
    window.addEventListener("pointermove", function (e) {
      tx = ((e.clientY / window.innerHeight) - 0.5) * -1.2;
      ty = ((e.clientX / window.innerWidth) - 0.5) * 1.2;
      if (!raf) raf = requestAnimationFrame(apply);
    });
    window.addEventListener("pointerleave", function () {
      tx = 0; ty = 0;
      if (!raf) raf = requestAnimationFrame(apply);
    });
  })();

  /* --------------------------------------------------------- display modes */
  function paintModes() {
    var chips = document.querySelectorAll("[data-mode]");
    var mode = document.body.dataset.display || "inline";
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", c.dataset.mode === mode ? "true" : "false");
    });
  }
  document.querySelectorAll("[data-mode]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      document.body.dataset.display = chip.dataset.mode || "inline";
      paintModes();
    });
  });

  /* ------------------------------------------------------------ settings sheet */
  function setSettings(open) {
    if (!el.settingsPanel) return;
    el.settingsPanel.hidden = !open;
    if (el.settingsBtn) el.settingsBtn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  el.settingsBtn && el.settingsBtn.addEventListener("click", function () {
    setSettings(!!el.settingsPanel && el.settingsPanel.hidden);
  });
  el.settingsCloseBtn && el.settingsCloseBtn.addEventListener("click", function () { setSettings(false); });
  document.addEventListener("click", function (e) {
    if (!el.settingsPanel || el.settingsPanel.hidden) return;
    if (el.settingsPanel.contains(e.target)) return;
    if (el.settingsBtn && el.settingsBtn.contains(e.target)) return;
    setSettings(false);
  });

  /* ------------------------------------------------------------ more asks */
  function setExtras(open) {
    document.querySelectorAll(".ask[data-extra]").forEach(function (b) { b.hidden = !open; });
    if (el.moreAsksBtn) el.moreAsksBtn.classList.toggle("is-open", open);
  }
  el.moreAsksBtn && el.moreAsksBtn.addEventListener("click", function () {
    setExtras(!!!el.moreAsksBtn.classList.contains("is-open"));
  });

  /* --------------------------------------------------------- stage states */
  var stageTimer = null;
  function setIdle() {
    if (el.stage) el.stage.dataset.state = "idle";
    if (el.answer) el.answer.hidden = true;
    if (el.said) el.said.hidden = true;
    if (el.voiceWave) el.voiceWave.hidden = true;
  }
  function setAsk(said) {
    if (stageTimer) { clearTimeout(stageTimer); stageTimer = null; }
    if (el.stage) el.stage.dataset.state = "ask";
    if (el.said) { el.said.hidden = false; el.said.textContent = "“" + said + "”"; }
    if (el.voiceWave) el.voiceWave.hidden = false;
    if (el.answer) el.answer.hidden = true;
    announce("Hearth is working on: " + said);
  }
  function setAnswer(state) {
    if (stageTimer) { clearTimeout(stageTimer); stageTimer = null; }
    if (el.stage) el.stage.dataset.state = "answer";
    if (el.said) el.said.hidden = true;
    if (el.voiceWave) el.voiceWave.hidden = true;
    paintAnswer(state);
    announce([state.verdict, state.sub].filter(Boolean).join(". "));
  }

  function countUp(node, text) {
    if (reducedMotion) { node.textContent = text; return; }
    var m = String(text).match(/^([^0-9]*)([0-9][0-9,]*(?:\.[0-9]+)?)(.*)$/);
    if (!m) { node.textContent = text; return; }
    var prefix = m[1], raw = m[2].replace(/,/g, ""), suffix = m[3];
    var target = parseFloat(raw);
    if (!isFinite(target) || target <= 0) { node.textContent = text; return; }
    var dec = (raw.split(".")[1] || "").length;
    var t0 = performance.now(), dur = 680;
    function frame(t) {
      var p = Math.min(1, (t - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      var v = (target * eased).toFixed(dec);
      v = v.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      node.textContent = prefix + v + suffix;
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function paintAnswer(state) {
    state = state || {};
    if (el.answer) el.answer.hidden = false;
    if (el.answerKicker) el.answerKicker.textContent = state.kicker || "HEARTH";
    if (el.answerBig) {
      if (state.big) {
        var bigTone = state.bigTone || state.tone;
        el.answerBig.hidden = false;
        el.answerBig.className = "answer-big num" + (bigTone ? " is-" + bigTone : "");
        countUp(el.answerBig, String(state.big));
      } else {
        el.answerBig.hidden = true;
        el.answerBig.textContent = "";
      }
    }
    if (el.answerVerdict) {
      el.answerVerdict.textContent = state.verdict || "Done.";
      el.answerVerdict.className = "answer-verdict" + (state.tone === "bad" ? " is-bad" : "");
    }
    if (el.answerSub) {
      el.answerSub.textContent = state.sub || "";
      el.answerSub.hidden = !state.sub;
    }
    if (el.answerLines) {
      el.answerLines.innerHTML = "";
      (state.lines || []).slice(0, 5).forEach(function (row) {
        var div = document.createElement("div");
        div.className = "line" + (row.tone ? " is-" + row.tone : "");
        var k = document.createElement("b");
        k.textContent = String(row.k == null ? "" : row.k);
        var v = document.createElement("span");
        v.textContent = String(row.v == null ? "" : row.v);
        div.append(k, v);
        el.answerLines.appendChild(div);
      });
    }
    if (el.trustStrip) {
      el.trustStrip.innerHTML = "";
      (state.trust || []).forEach(function (chip) {
        var span = document.createElement("span");
        span.className = "trust" + (chip.tone ? " is-" + chip.tone : "");
        if (chip.icon) span.appendChild(icon(chip.icon));
        var t = document.createElement("span");
        t.textContent = chip.text || "";
        span.appendChild(t);
        el.trustStrip.appendChild(span);
      });
    }
    if (el.answerCta) {
      el.answerCta.innerHTML = "";
      if (state.cta && state.cta.href) {
        var a = document.createElement("a");
        a.className = "cta-link";
        a.href = state.cta.href;
        var t = document.createElement("span");
        t.textContent = state.cta.label || "Open";
        a.appendChild(t);
        a.appendChild(icon("arrow"));
        el.answerCta.appendChild(a);
      }
    }
    if (el.response) el.response.textContent = [state.verdict, state.sub].filter(Boolean).join(" ");
    if (el.answer && el.answer.scrollTo) el.answer.scrollTo({ top: 0 });
    stageTimer = setTimeout(setIdle, 90000);
  }

  /* forensics verdicts arrive as codes — say them the way a person would */
  var VERDICTS = {
    INTRUDER_LIKELY_ENTRY: "Someone probably walked in",
    BENIGN_PHYSICAL_DISPLACEMENT: "Nothing to worry about — the house moved",
    EQUIPMENT_POWER_STARVATION: "An appliance caused it",
    NOMINAL_RECORD: "A quiet, ordinary night",
  };
  function humanVerdict(code) {
    var c = String(code || "").trim();
    if (!c) return "";
    if (VERDICTS[c]) return VERDICTS[c];
    if (c.length > 44 || /[a-z]/.test(c.slice(1))) return "";
    return titleCase(c.toLowerCase());
  }

  /* --------------------------------------------------- showcase renderers */
  var RENDERERS = {
    "/api/forensics/reconstruct": (d) => {
      var conf = Number(d.confidence_score);
      if (isFinite(conf)) conf = conf <= 1 ? conf * 100 : conf;
      var code = String(d.verdict || "");
      var tl = Array.isArray(d.timeline) ? d.timeline.slice(-4) : [];
      var lines = tl.map(function (t) {
        if (typeof t === "string") return { k: "·", v: t.slice(0, 110) };
        var key = t.timestamp || t.time || t.label || timeLabel(t.ts) || "·";
        var val = String(t.event || t.description || t.summary || t.detail || "").replace(/\s*\([^)]*\)/g, "").trim();
        return { k: key, v: val.slice(0, 110) };
      });
      var proof = d.audit_proof;
      if (proof && typeof proof === "object") {
        proof = proof.merkle_root || proof.root || proof.hash || proof.proof || "";
      }
      var tone = code === "INTRUDER_LIKELY_ENTRY" ? "bad"
        : (code === "BENIGN_PHYSICAL_DISPLACEMENT" || code === "NOMINAL_RECORD") ? "good" : null;
      return {
        kicker: "What happened",
        big: isFinite(conf) ? Math.round(conf) + "%" : null,
        bigTone: tone,
        verdict: humanVerdict(code) || "Here is the full story",
        sub: "Rebuilt from what the house recorded — wind, doors, climate. Nothing added, nothing guessed.",
        lines: lines,
        trust: [
          { icon: "shield", text: "Checked for safety" },
          proof ? { icon: "key", text: "Signed " + String(proof).slice(0, 10) } : null,
          { icon: "receipt", text: "Saved to the ledger" },
        ],
        cta: { label: "See every detail in the cockpit", href: "/web2/index.html" },
      };
    },

    "/api/parliament/deliberate": (d) => {
      var speeches = Array.isArray(d.speeches) ? d.speeches.slice(-3) : [];
      var lines = speeches.map(function (s) {
        if (typeof s === "string") return { k: "voice", v: s.slice(0, 110) };
        var who = s.speaker || s.persona || s.minister || s.role || "member";
        var what = s.position || s.stance || s.text || s.summary || s.speech || "";
        return { k: titleCase(who).slice(0, 24), v: String(what).slice(0, 110) };
      });
      var nash = Number(d.nash_equilibrium_score);
      return {
        kicker: "Household vote",
        big: isFinite(nash) ? nash.toFixed(2) : null,
        verdict: "The house voted: " + String(d.vote || "recorded").replace(/_/g, " "),
        sub: isFinite(nash) ? "Fairness " + nash.toFixed(2) + " — a split every member prefers to no deal at all." : "",
        lines: lines,
        trust: [
          { icon: "scale", text: (d.candidate_count || 0) + " options weighed" },
          { icon: "users", text: "everyone's voice heard" },
        ],
      };
    },

    "/api/causal/simulate": (d) => {
      var vulns = Array.isArray(d.vulnerabilities) ? d.vulnerabilities.slice(0, 4) : [];
      var lines = vulns.map(function (v) {
        if (typeof v === "string") return { k: v.slice(0, 46), v: "watch this" };
        var name = v.name || v.title || v.asset || v.id || "risk";
        var sev = v.severity || v.risk || v.probability || v.impact || "";
        return { k: titleCase(name).slice(0, 46), v: sev ? titleCase(sev) : "watch this" };
      });
      var score = Number(d.grid_resilience_score);
      var tone = isFinite(score) ? (score >= 70 ? "good" : score <= 40 ? "bad" : null) : null;
      var savings = Number(d.expected_savings_usd);
      return {
        kicker: "The week ahead",
        big: isFinite(score) ? String(Math.round(score)) : null,
        bigTone: tone,
        verdict: "Steadiness " + (isFinite(score) ? Math.round(score) : "--") + " out of 100",
        sub: (d.monte_carlo_iterations ? d.monte_carlo_iterations + " what-if runs" : "what-if run") +
             (isFinite(savings) ? " · " + usd(savings) + " on the table if you act on it" : ""),
        lines: lines,
        trust: [
          { icon: "chart", text: "computed live, not scripted" },
          { icon: "spark", text: "backup plans already prepared" },
        ],
      };
    },

    "/api/swarm/grid": (d) => {
      var txs = Array.isArray(d.p2p_transactions) ? d.p2p_transactions : [];
      var lines = [];
      if (txs.length) {
        txs.slice(0, 2).forEach(function (t) {
          if (typeof t === "string") { lines.push({ k: "trade", v: t.slice(0, 90) }); return; }
          var who = t.peer || t.neighbor || t.house || t.id || "neighbour";
          var what = t.kwh || t.amount_kwh || t.volume || t.kwh_traded;
          lines.push({ k: "→ " + String(who), v: what ? what + " kWh shared" : "settled" });
        });
      } else {
        lines.push({ k: "trades", v: "settled with the neighbourhood pool" });
      }
      lines.push({ k: "economic impact", v: String(d.economic_impact || "—").slice(0, 100) });
      lines.push({ k: "environmental impact", v: String(d.environmental_impact || "—").slice(0, 100) });
      var rate = Number(d.cooperative_rate_kwh);
      return {
        kicker: "Neighbourhood energy",
        big: isFinite(rate) ? "$" + rate.toFixed(2) + "/kWh" : null,
        bigTone: "good",
        verdict: "Extra solar sold to the neighbourhood",
        sub: d.voice_summary || "Stored solar went to neighbours instead of the wall.",
        lines: lines,
        trust: [{ icon: "bolt", text: "surplus shared, nobody overpaid" }],
      };
    },

    "/api/mediation/treaty": (d) => {
      var cov = Array.isArray(d.covenants) ? d.covenants : [];
      var lines = [];
      cov.slice(0, 3).forEach(function (c) {
        if (typeof c === "string") { lines.push({ k: "agreement", v: c.slice(0, 100) }); return; }
        lines.push({
          k: titleCase(c.name || c.title || c.id || "agreement").slice(0, 40),
          v: String(c.terms || c.summary || c.text || "agreed").slice(0, 100),
        });
      });
      lines.push({ k: "fair-score", v: num(d.nash_achievement, 2) });
      lines.push({ k: "shared budget covered", v: num(d.cooperation_coverage_pct, 0) + "%" });
      lines.push({ k: "nobody left envious", v: num(d.envy_gap, 2) + " envy gap" });
      var fair = Number(d.fairness_index_out_of_10);
      var save = Number(d.projected_monthly_savings_usd);
      return {
        kicker: "House treaty",
        big: isFinite(fair) ? fair.toFixed(1) + "/10" : null,
        bigTone: isFinite(fair) && fair >= 8 ? "good" : null,
        verdict: "Settled — " + (cov.length || "no") + " agreements, " + "everyone signed",
        sub: save ? "About " + usd(save) + " a month saved for the household, and nobody feeling shortchanged." : "Every member prefers this split to a fight.",
        lines: lines,
        trust: [
          { icon: "users", text: "everyone agreed" },
          { icon: "receipt", text: "waiting for your OK" },
        ],
      };
    },

    "/api/acoustic/scan": (d) => {
      var apps = Array.isArray(d.appliances) ? d.appliances.slice(0, 4) : [];
      var lines = apps.map(function (a) {
        if (typeof a === "string") return { k: a, v: "answered" };
        return {
          k: titleCase(a.name || a.appliance || a.id || "appliance").slice(0, 40),
          v: titleCase(String(a.status || a.health || a.state || a.verdict || "healthy")).slice(0, 60),
        };
      });
      var healthy = apps.filter(function (a) {
        var s = String((a && (a.status || a.health || a.state || a.verdict)) || "healthy").toLowerCase();
        return s.indexOf("healthy") >= 0 || s.indexOf("ok") >= 0 || s.indexOf("nominal") >= 0 || s.indexOf("good") >= 0;
      }).length;
      return {
        kicker: "Appliance hearing test",
        big: String(apps.length || "—"),
        verdict: (apps.length ? apps.length : "Every") + " appliances answered" + (apps.length && healthy === apps.length ? " — all healthy" : ""),
        sub: d.voice_summary || "Each machine hums its own signature — Hearth listened and matched it.",
        lines: lines,
        trust: [{ icon: "wave", text: "one small mic, the whole house" }],
      };
    },

    "/api/commerce/autopilot-checkout": (d) => {
      if (d.blocked) {
        return {
          kicker: "Blocked for safety",
          verdict: d.message || "Held back by Leo's guardrails",
          sub: "Nothing was staged and nothing was bought.",
          lines: [],
          tone: "bad",
          trust: [{ icon: "shield", text: "kept Leo safe", tone: "bad" }],
        };
      }
      var cart = d.cart_preview || {};
      var items = Array.isArray(cart.items) ? cart.items.slice(0, 3) : [];
      var lines = items.map(function (it) {
        if (typeof it === "string") return { k: it, v: "" };
        var qty = it.qty || it.quantity || 1;
        var price = Number(it.price);
        return {
          k: String(it.name || it.title || "item").slice(0, 44),
          v: "×" + qty + (isFinite(price) ? " · " + usd(price) : ""),
        };
      });
      var total = Number(cart.final_total);
      var save = Number(cart.savings);
      return {
        kicker: "Groceries, handled",
        big: isFinite(total) ? usd(total) : null,
        verdict: "The cart is built and waiting for you",
        sub: (isFinite(save) && save > 0 ? "You save " + usd(save) + " with Subscribe & Save. " : "") + "Nothing is bought until you tap approve.",
        lines: lines,
        trust: [
          { icon: "receipt", text: "waiting for your OK" },
          { icon: "lock", text: "no real payment" },
        ],
      };
    },

    "/api/renewals": (d) => {
      var rs = Array.isArray(d.renewals) ? d.renewals.slice(0, 4) : [];
      var lines = rs.map(function (r) {
        if (typeof r === "string") return { k: r, v: "" };
        var cost = Number(r.cost_yr || r.yearly_cost || r.cost);
        var why = r.recommendation || r.status || r.reason || "";
        return {
          k: String(r.title || r.name || r.service || "subscription").slice(0, 44),
          v: (isFinite(cost) ? usd(cost) + "/yr" : "") + (why ? " · " + String(why).replace(/_/g, " ").slice(0, 40) : ""),
        };
      });
      var pot = Number(d.potential_save_yr);
      var spend = Number(d.total_annual_spend);
      return {
        kicker: "Forgotten money",
        big: isFinite(pot) ? usd(pot) + "/yr" : null,
        bigTone: "good",
        verdict: "Subscriptions nobody uses anymore",
        sub: "Untouched for 60+ days, instantly resumable — cancelling costs you nothing.",
        lines: lines,
        trust: [
          { icon: "scissors", text: isFinite(spend) ? usd(spend) + "/yr under watch" : "under watch" },
          { icon: "tag", text: "cancel one and it appears for your OK" },
        ],
      };
    },

    "/api/renewals/stage": (d) => {
      if (d.blocked || d.ok === false) {
        return {
          kicker: "Blocked for safety",
          verdict: "That one needs a grown-up to approve",
          sub: "Nothing was staged. Leo keeps the fun stuff, not the money stuff.",
          tone: "bad",
          lines: [],
          trust: [{ icon: "shield", text: "kept Leo safe", tone: "bad" }],
        };
      }
      var prop = d.proposal || {};
      var delta = Number(prop.cost_delta_yr);
      var abs = Math.abs(delta);
      return {
        kicker: "Cancellation ready",
        big: isFinite(delta) ? "+" + usd(abs) + "/yr" : null,
        bigTone: "good",
        verdict: "Waiting in your OK list",
        sub: "Approve and it's done — undo any time, and the receipt is kept forever.",
        lines: prop.title ? [{ k: String(prop.title).slice(0, 50), v: "one tap · reversible" }] : [],
        trust: [{ icon: "receipt", text: "nothing cancels without your OK" }],
      };
    },
  };

  function genericTheater(d, label) {
    d = d || {};
    var msg = d.message || d.verdict || d.summary || d.voice_summary || "";
    return {
      kicker: "Hearth",
      verdict: msg ? humanVerdict(msg) || firstSentence(msg) : (label || "Done — recorded in the ledger"),
      sub: msg ? restAfterFirst(msg) : "",
      lines: [],
      trust: [{ icon: "receipt", text: "every move lands in the ledger" }],
    };
  }

  /* --------------------------------------------------------------- chatting */
  var busy = false;
  function setBusy(state) {
    busy = state;
    if (el.askSend) el.askSend.disabled = state;
    if (el.askText) el.askText.disabled = state;
    document.querySelectorAll(".ask").forEach(function (b) { b.disabled = state; });
  }

  function chatTheater(d, message) {
    d = d || {};
    var draft = String(d.draft || "").trim();
    draft = draft.replace(/\[[^\]]*\]/g, " ").replace(/\s+/g, " ").trim();
    var blocked = /blocked by the safety contract/i.test(draft);
    var lines = [];
    var steps = Array.isArray(d.dag) ? d.dag : [];
    steps.slice(0, 3).forEach(function (s) {
      var tool = typeof s === "string" ? s : (s.tool || s.name || s.step || s.action || "step");
      var status = typeof s === "object" && s ? (s.status || s.state || "done") : "done";
      lines.push({ k: titleCase(tool).slice(0, 44), v: titleCase(status).slice(0, 26) });
    });
    var staged = Array.isArray(d.proposals_created) ? d.proposals_created : [];
    staged.slice(0, 2).forEach(function (p) {
      var title = typeof p === "string" ? p : (p.title || p.kind || p.id || "a plan");
      lines.push({ k: "waiting for your OK", v: String(title).replace(/_/g, " ").slice(0, 60), tone: "good" });
    });
    var trust = [];
    if (d.fallback) {
      trust.push({ icon: "hub", text: "built-in brain answered — connect your own to go further" });
    } else if (d.provider || d.model) {
      trust.push({ icon: "hub", text: [titleCase(d.provider), d.model].filter(Boolean).join(" · ").slice(0, 48) });
    }
    trust.push(blocked
      ? { icon: "shield", text: "the guardrail held the line", tone: "bad" }
      : { icon: "lock", text: "Checked for safety" });
    trust.push({ icon: "receipt", text: "receipt issued when it happens" });
    return {
      kicker: "Hearth",
      verdict: draft ? humanVerdict(draft) || firstSentence(draft) : "I heard you.",
      sub: restAfterFirst(draft),
      lines: lines,
      trust: trust,
      tone: blocked ? "bad" : null,
      raw: message,
    };
  }

  async function ask(message, label) {
    var text = String(message || "").trim();
    if (!text || busy) return;
    setBusy(true);
    setAsk(label || text);
    var res = await postJSON("/api/chat", { message: text });
    setBusy(false);
    if (!res.ok || !res.data) {
      setAnswer({
        kicker: "Offline",
        verdict: "I couldn't reach the house's brain for that one.",
        sub: "The connection said " + (res.status || "no reply") + ". Everything else in the house still works.",
        lines: [],
        trust: [{ icon: "wave", text: "local hiccup", tone: "bad" }],
        tone: "bad",
      });
      return;
    }
    setAnswer(chatTheater(res.data, text));
    refreshTray();
    tourNext();
  }

  el.askForm && el.askForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = el.askText ? el.askText.value.trim() : "";
    if (!text) return;
    if (el.askText) el.askText.value = "";
    ask(text);
  });

  /* ------------------------------------------------------------- showcase */
  document.querySelectorAll(".ask[data-go]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (busy) return;
      var path = btn.dataset.go;
      var payload = {};
      try { payload = JSON.parse(btn.dataset.body || "{}"); } catch (e) { payload = {}; }
      var label = btn.textContent.replace(/^\s*[^\w]*/, "").trim();
      setBusy(true);
      setAsk(label);
      var res = await postJSON(path, payload);
      setBusy(false);
      var d = (res.data && typeof res.data === "object") ? res.data : {};
      if (!res.ok && !d.blocked) {
        d.blocked = true;
        d.message = d.error || d.message || ("The house said " + res.status);
      }
      var state = null;
      try {
        state = RENDERERS[path] ? RENDERERS[path](d) : genericTheater(d, label);
      } catch (err) {
        state = genericTheater(d, label);
      }
      setAnswer(state);
      if (!d.blocked) { refreshTray(); refreshTicker(); }
      tourNext();
    });
  });

  /* ----------------------------------------------------- the waiting list */
  var trayPids = {};
  var lastTraySig = null;

  function trayItem(p) {
    var row = document.createElement("div");
    row.className = "tray-item";

    var title = document.createElement("div");
    title.className = "tray-title";
    title.textContent = String(p.title || p.kind || p.id || "").replace(/_/g, " ");

    var meta = document.createElement("div");
    meta.className = "tray-meta";
    var delta = Number(p.cost_delta_yr);
    var dspan = document.createElement("span");
    dspan.className = "delta";
    if (isFinite(delta) && delta < 0) {
      dspan.textContent = "+" + usd(Math.abs(delta)) + "/yr saved";
    } else if (isFinite(delta) && delta > 0) {
      dspan.textContent = usd(delta) + "/yr";
      dspan.classList.add("is-muted");
    }
    var risk = document.createElement("span");
    risk.className = "risk";
    risk.textContent = [p.risk_level, p.kind].filter(Boolean).join(" · ").replace(/_/g, " ").slice(0, 40);
    meta.append(dspan, risk);

    var actions = document.createElement("div");
    actions.className = "row-actions";
    var approve = document.createElement("button");
    approve.className = "btn btn-primary";
    approve.type = "button";
    approve.textContent = "Approve";
    approve.addEventListener("click", function () { decide(p.id, true); });
    var decline = document.createElement("button");
    decline.className = "btn";
    decline.type = "button";
    decline.textContent = "Decline";
    decline.addEventListener("click", function () { decide(p.id, false); });
    actions.append(approve, decline);

    row.append(title, meta, actions);
    return row;
  }

  async function refreshTray() {
    var d = await getJSON("/api/proposals?limit=20");
    if (!d) {
      if (el.connText) el.connText.textContent = "offline";
      if (el.connDot) el.connDot.className = "dot is-bad";
      return;
    }
    if (el.connText) el.connText.textContent = "online";
    if (el.connDot) el.connDot.className = "dot is-ok";

    var all = Array.isArray(d.proposals) ? d.proposals : [];
    var pending = all.filter(function (p) { return p && p.status === "pending"; });
    trayPids = {};
    pending.forEach(function (p) { trayPids[p.id] = p; });

    if (el.trayCount) el.trayCount.textContent = String(d.pending_count != null ? d.pending_count : pending.length);
    if (!el.trayBody) return;
    var shown = pending.slice(0, 3);
    var sig = shown.map(function (p) { return p.id; }).join("|");
    if (sig === lastTraySig) { paintGlance(d); return; }
    lastTraySig = sig;
    el.trayBody.innerHTML = "";
    if (!pending.length) {
      var empty = document.createElement("div");
      empty.className = "tray-empty";
      empty.textContent = "All clear. When Hearth prepares something, it waits here with the exact cost — one tap to apply, undo any time.";
      el.trayBody.appendChild(empty);
    } else {
      shown.forEach(function (p) { el.trayBody.appendChild(trayItem(p)); });
    }
    if (el.trayLead) el.trayLead.hidden = pending.length > 0;
    paintGlance(d);
  }

  function paintGlance(tray) {
    if (!el.statusBody) return;
    el.statusBody.innerHTML = "";
    function row(k, v) {
      var div = document.createElement("div");
      div.className = "status-row";
      var a = document.createElement("span");
      a.textContent = k;
      var b = document.createElement("b");
      b.textContent = v;
      div.append(a, b);
      el.statusBody.appendChild(div);
    }
    if (el.vDraw && el.vDraw.textContent !== "--") {
      row("Drawing now", el.vDraw.textContent + " kW" + (el.vSolar && el.vSolar.dataset.kw ? " · solar " + el.vSolar.dataset.kw + " kW" : ""));
    }
    row("Waiting for your OK", String((tray && (tray.pending_count != null ? tray.pending_count : (tray.proposals || []).length)) || 0));
  }

  async function decide(pid, approved) {
    if (!pid) return;
    var res = await postJSON("/api/proposals/" + encodeURIComponent(pid) + "/decide", { approved: !!approved });
    if (!res.ok) {
      var dd = res.data || {};
      if (res.status === 403 || dd.blocked) {
        setAnswer({
          kicker: "Blocked for safety",
          verdict: "Approving money moves is a grown-up job",
          sub: "Nothing was executed. The plan stays in the waiting list for Alex.",
          tone: "bad",
          lines: [],
          trust: [{ icon: "shield", text: "kept Leo safe", tone: "bad" }],
        });
      } else {
        toast("Couldn't do that one: " + (dd.error || res.status));
      }
      return;
    }
    var prop = (res.data && (res.data.proposal || res.data.execution ? res.data.proposal || res.data : res.data)) || {};
    if (approved) {
      var led = await newestLedgerReceipt();
      openReceipt(prop, led);
    } else {
      toast("Declined — nothing moved, nothing charged.");
    }
    refreshTray();
    refreshTicker();
  }

  /* ------------------------------------------------------------ receipt sheet */
  var receiptPid = null;
  async function newestLedgerReceipt() {
    var d = await getJSON("/api/receipts?limit=10");
    var rs = (d && d.receipts) || [];
    var i;
    for (i = 0; i < rs.length; i++) {
      if (rs[i].kind === "approval_executed" || rs[i].kind === "order_staged" || rs[i].kind === "tool_applied") return rs[i];
    }
    return rs[0] || null;
  }
  function openReceipt(prop, ledger) {
    prop = prop || {};
    var ex = prop.execution || {};
    receiptPid = prop.id || null;
    if (el.receiptTitle) el.receiptTitle.textContent = "Receipt";
    if (el.receiptSub) el.receiptSub.textContent = String(prop.title || "Household action applied").replace(/_/g, " ");
    if (el.receiptCode) el.receiptCode.textContent = ex.receipt_code || (ledger && ledger.receipt_id) || "—";
    if (el.receiptBody) {
      el.receiptBody.innerHTML = "";
      function row(k, v) {
        var div = document.createElement("div");
        div.className = "status-row";
        var a = document.createElement("span");
        a.textContent = k;
        var b = document.createElement("b");
        b.textContent = v;
        div.append(a, b);
        el.receiptBody.appendChild(div);
      }
      var delta = Number(prop.cost_delta_yr);
      if (isFinite(delta) && delta < 0) row("You save", "+" + usd(Math.abs(delta)) + "/yr");
      else if (isFinite(delta) && delta > 0) row("Extra cost", usd(delta) + "/yr");
      var spent = ledger && ledger.money ? Number(ledger.money.spent_usd) : 0;
      if (isFinite(spent) && spent > 0) row("Paid", usd(spent));
      if (ex.applied) row("Done", "applied exactly once");
      if (ex.at || prop.decided_at) row("Done at", timeLabel(ex.at || prop.decided_at) || "now");
      row("Undo", ex.reversal ? "straight back" : "one tap, any time");
      row("Verified", ledger && ledger.receipt_hash ? shortHash(ledger.receipt_hash, 14) + " · hash-chained" : "written to the ledger");
    }
    if (el.receiptUndoBtn) el.receiptUndoBtn.hidden = !receiptPid;
    if (el.receiptBackdrop) el.receiptBackdrop.hidden = false;
  }
  function closeReceipt() { if (el.receiptBackdrop) el.receiptBackdrop.hidden = true; }

  el.receiptDoneBtn && el.receiptDoneBtn.addEventListener("click", closeReceipt);
  el.receiptCloseBtn && el.receiptCloseBtn.addEventListener("click", closeReceipt);
  el.receiptBackdrop && el.receiptBackdrop.addEventListener("click", function (e) {
    if (e.target === el.receiptBackdrop) closeReceipt();
  });
  el.receiptUndoBtn && el.receiptUndoBtn.addEventListener("click", async function () {
    if (!receiptPid) return;
    var res = await postJSON("/api/proposals/" + encodeURIComponent(receiptPid) + "/undo", {});
    if (res.ok) {
      toast("Undone — the reversal is in the ledger too.");
      closeReceipt();
      refreshTray();
      refreshTicker();
    } else {
      toast("Undo failed: " + ((res.data && res.data.error) || res.status));
    }
  });

  /* -------------------------------------------------------------- ambient */
  var ambientBusy = false;
  async function refreshAmbient() {
    if (ambientBusy) return;
    ambientBusy = true;
    var results = await Promise.all([getJSON("/api/home"), getJSON("/api/commerce/depletion")]);
    ambientBusy = false;
    var home = results[0], dep = results[1];

    if (home) {
      var climate = (home.living_room && home.living_room.climate) || {};
      var f = cToF(climate.current_c);
      if (el.vTemp) el.vTemp.textContent = f == null ? "--" : num(f, 0);
      if (el.vClimate) {
        var bits = [];
        if (climate.mode) bits.push(String(climate.mode).replace(/_/g, " "));
        var tgt = cToF(climate.target_c);
        if (tgt != null) bits.push("heading to " + num(tgt, 0) + "°");
        if (climate.fan && climate.fan !== climate.mode) bits.push(String(climate.fan).replace(/_/g, " "));
        el.vClimate.textContent = bits.join(" · ") || "holding steady";
      }
      var energy = home.energy || {};
      if (el.vDraw) el.vDraw.textContent = num(energy.current_draw_kw, 1);
      if (el.vSolar) {
        var solar = Number(energy.solar_generation_kw);
        el.vSolar.dataset.kw = isFinite(solar) ? solar.toFixed(1) : "";
        el.vSolar.textContent = isFinite(solar) && solar > 0.05
          ? solar.toFixed(1) + " kW solar" + (energy.eco_score != null ? " · eco " + Math.round(energy.eco_score) : "")
          : "grid only" + (energy.eco_score != null ? " · eco " + Math.round(energy.eco_score) : "");
      }
      var lock = home.entryway && home.entryway.lock && home.entryway.lock.front_door;
      if (el.vLock) {
        el.vLock.textContent = lock === "locked" ? "Locked" : lock ? "Unlocked" : "Unknown";
        el.vLock.className = lock === "locked" ? "is-ok" : lock ? "is-bad" : "";
      }
      if (el.vLights) {
        var lights = (home.living_room && home.living_room.lights) || {};
        var on = Object.keys(lights).filter(function (k) { return lights[k] === true; }).length;
        el.vLights.textContent = on ? on + (on === 1 ? " light on" : " lights on") : "lights off";
      }
      if (el.sceneLine) {
        var scene = String(home.active_scene || "").replace(/[-_]+/g, " ").trim();
        el.sceneLine.textContent = scene && scene !== "none"
          ? scene.charAt(0).toUpperCase() + scene.slice(1)
          : "All quiet";
      }
    }

    if (dep) {
      var items = Array.isArray(dep) ? dep : (dep.forecast || dep.items || dep.depletion || dep.pantry || []);
      var low = null;
      (Array.isArray(items) ? items : []).forEach(function (it) {
        if (!it || typeof it !== "object") return;
        var days = Number(it.days_until_empty != null ? it.days_until_empty : it.days_left);
        if (!isFinite(days)) return;
        if (!low || days < low.days) low = { days: days, name: it.name || it.item || "supply" };
      });
      if (el.vPantry && el.vPantryName) {
        if (low) {
          var days = Math.max(0, Math.round(low.days));
          var pname = String(low.name);
          el.vPantryName.textContent = pname.length > 28 ? pname.slice(0, 27).trim() + "…" : pname;
          el.vPantry.textContent = days + (days === 1 ? " day left" : " days left");
        } else {
          el.vPantryName.textContent = "Everything stocked";
          el.vPantry.textContent = "";
        }
      }
    }
    paintGlance({ pending_count: Object.keys(trayPids).length });
  }

  /* --------------------------------------------------------- receipts stream */
  function moneyText(m) {
    m = m || {};
    if (m.saved_usd) return { t: "+" + usd(m.saved_usd) + " saved", good: true };
    if (m.earned_usd) return { t: "+" + usd(m.earned_usd), good: true };
    if (m.spent_usd) return { t: "−" + usd(m.spent_usd), good: false };
    return null;
  }

  async function refreshTicker() {
    var d = await getJSON("/api/receipts?limit=4");
    if (!d || !d.ok) return;
    var receipts = Array.isArray(d.receipts) ? d.receipts : [];
    if (el.ticker) {
      el.ticker.innerHTML = "";
      if (!receipts.length) {
        var empty = document.createElement("span");
        empty.className = "tick is-empty";
        empty.textContent = "No receipts yet — the moment something happens, its receipt lands here.";
        el.ticker.appendChild(empty);
      }
      receipts.slice(0, 4).forEach(function (r) {
        var m = moneyText(r.money);
        var chip = document.createElement("span");
        chip.className = "tick";
        chip.appendChild(icon(m && m.good ? "check" : "receipt"));
        if (m) {
          var b = document.createElement("b");
          b.textContent = m.t;
          if (!m.good) b.className = "is-quiet";
          chip.appendChild(b);
        }
        var label = document.createElement("span");
        label.textContent = String(r.claim || "").split("—")[0]
          .replace(/^Approval executed:\s*approved\s*/i, "You approved ")
          .replace(/^Approval executed:?\s*/i, "Approved ")
          .replace(/^Tool applied:\s*/i, "")
          .trim()
          .slice(0, 40);
        var code = document.createElement("code");
        code.textContent = shortHash(r.receipt_id, 11);
        chip.append(label, code);
        el.ticker.appendChild(chip);
      });
    }
    var led = d.ledger || {};
    if (el.proofTotal) el.proofTotal.textContent = usd(led.verified_usd || 0);
    if (el.proofSub) {
      el.proofSub.textContent = (led.receipts_count || 0) + " receipts · spent " + usd(led.spent_usd || 0);
    }
    if (el.proofChainPill) {
      el.proofChainPill.textContent = led.chain_valid ? "verified" : "broken";
      el.proofChainPill.className = "pill" + (led.chain_valid ? " pill-ok" : " is-bad");
    }
  }

  /* -------------------------------------------------------------- persona */
  function paintPersona(id) {
    if (!el.personaToggleBtn) return;
    var child = id === "child";
    el.personaToggleBtn.dataset.persona = child ? "child" : "admin";
    if (el.personaLabel) el.personaLabel.textContent = child ? "Leo" : "Alex";
    if (el.personaNote) el.personaNote.textContent = child ? "child" : "adult";
    el.personaToggleBtn.title = child ? "Leo · kid-safe profile" : "Alex · adult profile";
    el.personaToggleBtn.setAttribute("aria-pressed", child ? "true" : "false");
  }
  async function loadPersona() {
    var d = await getJSON("/api/persona");
    paintPersona((d && (d.id || d.persona)) || "admin");
  }
  el.personaToggleBtn && el.personaToggleBtn.addEventListener("click", async function () {
    var cur = el.personaToggleBtn.dataset.persona === "child" ? "child" : "admin";
    var next = cur === "child" ? "admin" : "child";
    var res = await postJSON("/api/persona", { id: next });
    if (res.ok) {
      paintPersona(next);
      toast(next === "child" ? "Leo's profile is on — kid-safe guardrails active." : "Alex is back on the profile.");
      refreshTray();
    } else {
      toast("Couldn't switch profiles: " + ((res.data && res.data.error) || res.status));
    }
  });

  /* ---------------------------------------------------------------- brain */
  var BRAIN_PRESETS = [
    { id: "local", name: "Built-in brain (works offline, zero setup)" },
    { id: "openai", name: "OpenAI-compatible (OpenAI / gateway)" },
    { id: "groq", name: "Groq" },
    { id: "openrouter", name: "OpenRouter" },
    { id: "ollama", name: "Ollama (on this network)" },
    { id: "bedrock", name: "Amazon Bedrock (Claude / Nova)" },
  ];
  var brainPresets = BRAIN_PRESETS.slice();

  function paintBrain(status) {
    status = status || {};
    var provider = String(status.provider || "local");
    var name = String(status.provider_name || provider);
    if (el.brainLabel) {
      el.brainLabel.textContent = provider === "local" ? "Built-in brain" : name.split("(")[0].trim().slice(0, 22);
    }
    if (el.brainDot) el.brainDot.className = "dot" + (provider === "local" ? "" : " is-ok");
    if (el.brainCallout) el.brainCallout.hidden = provider !== "local";
  }
  async function loadBrain() {
    var st = await getJSON("/api/brain/connect");
    paintBrain(st || {});
    if (st && Array.isArray(st.presets) && st.presets.length) {
      brainPresets = st.presets;
    }
    if (st && st.key_hint && el.keyStatus) {
      el.keyStatus.textContent = "Connected · stored key " + st.key_hint;
    }
  }
  function brainFields() {
    var p = el.keyProvider ? el.keyProvider.value : "local";
    var showBase = p === "ollama" || p === "openai";
    var showKey = p === "openai" || p === "groq" || p === "openrouter";
    var showAws = p === "bedrock";
    if (el.keyBaseUrlField) el.keyBaseUrlField.hidden = !showBase;
    if (el.keyApiKeyField) el.keyApiKeyField.hidden = !showKey;
    if (el.keyRegionField) el.keyRegionField.hidden = !showAws;
    if (el.keyAccessField) el.keyAccessField.hidden = !showAws;
    if (el.keySecretField) el.keySecretField.hidden = !showAws;
    if (el.keyModelField) el.keyModelField.hidden = !(p === "ollama" || p === "openai" || p === "groq" || p === "openrouter");
    if (el.keyNote) {
      el.keyNote.textContent = p === "bedrock"
        ? "Bedrock uses your AWS credentials. They stay on this device with owner-only access and are never echoed back."
        : p === "ollama"
          ? "Ollama needs no key — just the address of the machine running it."
          : p === "local"
            ? "The built-in brain is zero setup and works offline. Connect one you own only if you want deeper reasoning."
            : "The key stays on this device with owner-only access, is shown masked, and is never echoed by any part of Hearth.";
    }
  }
  function openBrain() {
    setSettings(false);
    if (el.keyBackdrop) el.keyBackdrop.hidden = false;
    if (el.keyProvider) {
      el.keyProvider.innerHTML = "";
      brainPresets.forEach(function (p) {
        var o = document.createElement("option");
        o.value = p.id;
        o.textContent = p.name || p.id;
        el.keyProvider.appendChild(o);
      });
      el.keyProvider.value = "openai";
    }
    brainFields();
    if (el.keyStatus) { el.keyStatus.textContent = ""; el.keyStatus.className = "key-status"; }
  }
  function closeBrain() { if (el.keyBackdrop) el.keyBackdrop.hidden = true; }
  function brainPayload(extra) {
    var p = el.keyProvider ? el.keyProvider.value : "local";
    var body = { provider: p, test: true };
    var key = el.keyApiKey && el.keyApiKey.value.trim();
    var base = el.keyBaseUrl && el.keyBaseUrl.value.trim();
    var model = el.keyModel && el.keyModel.value.trim();
    var region = el.keyRegion && el.keyRegion.value.trim();
    var access = el.keyAccess && el.keyAccess.value.trim();
    var secret = el.keySecret && el.keySecret.value.trim();
    if (key) body.api_key = key;
    if (base) body.base_url = base;
    if (model) body.model = model;
    if (region) body.region = region;
    if (access) body.access_key = access;
    if (secret) body.secret_key = secret;
    return Object.assign(body, extra || {});
  }

  async function saveBrain() {
    var res = await postJSON("/api/brain/connect", brainPayload());
    var d = res.data || {};
    if (!res.ok || d.ok === false) {
      if (el.keyStatus) {
        el.keyStatus.textContent = String(d.error || "Could not save (" + res.status + ")").slice(0, 160);
        el.keyStatus.className = "key-status is-bad";
      }
      return;
    }
    if (el.keyApiKey) el.keyApiKey.value = "";
    if (el.keySecret) el.keySecret.value = "";
    if (el.keyAccess) el.keyAccess.value = "";
    var test = d.test || {};
    var testMsg = test.message || test.detail || test.error || (test.ok ? "endpoint answered" : "");
    if (el.keyStatus) {
      el.keyStatus.textContent = "Connected ✓ " + titleCase(d.provider || "") + (d.model ? " · " + d.model : "") + (testMsg ? " — " + String(testMsg).slice(0, 90) : "");
      el.keyStatus.className = "key-status is-ok";
    }
    paintBrain(d);
    toast("Connected — keys never leave this house.");
  }

  el.brainBtn && el.brainBtn.addEventListener("click", openBrain);
  el.brainCallout && el.brainCallout.addEventListener("click", openBrain);
  el.keyCloseBtn && el.keyCloseBtn.addEventListener("click", closeBrain);
  el.keyBackdrop && el.keyBackdrop.addEventListener("click", function (e) {
    if (e.target === el.keyBackdrop) closeBrain();
  });
  el.keyProvider && el.keyProvider.addEventListener("change", brainFields);
  el.keySaveBtn && el.keySaveBtn.addEventListener("click", saveBrain);
  el.keyTestBtn && el.keyTestBtn.addEventListener("click", saveBrain);
  el.keyClearBtn && el.keyClearBtn.addEventListener("click", async function () {
    var res = await postJSON("/api/brain/disconnect", {});
    if (res.ok) {
      paintBrain({ provider: "local", provider_name: "Built-in brain" });
      if (el.keyStatus) { el.keyStatus.textContent = "Disconnected — the built-in brain is back."; el.keyStatus.className = "key-status"; }
      toast("Disconnected. The built-in brain is back on duty.");
    } else {
      toast("Disconnect failed: " + ((res.data && res.data.error) || res.status));
    }
  });

  /* ----------------------------------------------------------------- voice */
  (function voice() {
    if (!el.micBtn) return;
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    var rec = null;
    if (SR) {
      rec = new SR();
      rec.lang = "en-US";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onresult = function (e) {
        var text = e.results && e.results[0] && e.results[0][0] ? e.results[0][0].transcript : "";
        stop();
        if (text) ask(text);
      };
      rec.onerror = function () { stop(); toast("The mic stayed quiet — type it and I'll answer just as fast."); };
      rec.onend = function () { stop(); };
    }
    var listening = false;
    function stop() {
      listening = false;
      el.micBtn.classList.remove("is-live");
      if (el.stage && el.stage.dataset.state === "ask" && el.voiceWave && el.voiceWave.dataset.fromMic) {
        setIdle();
      }
      if (el.voiceWave) delete el.voiceWave.dataset.fromMic;
    }
    el.micBtn.addEventListener("click", function () {
      if (listening) { if (rec) rec.stop(); stop(); return; }
      if (rec) {
        listening = true;
        el.micBtn.classList.add("is-live");
        if (el.stage) el.stage.dataset.state = "ask";
        if (el.voiceWave) { el.voiceWave.hidden = false; el.voiceWave.dataset.fromMic = "1"; }
        if (el.said) { el.said.hidden = false; el.said.textContent = "Listening…"; }
        try { rec.start(); } catch (e) { stop(); }
      } else {
        listening = true;
        el.micBtn.classList.add("is-live");
        if (el.stage) el.stage.dataset.state = "ask";
        if (el.voiceWave) { el.voiceWave.hidden = false; el.voiceWave.dataset.fromMic = "1"; }
        if (el.said) { el.said.hidden = false; el.said.textContent = "Listening…"; }
        setTimeout(function () {
          stop();
          toast("This browser can't listen — type it and I'll answer just as fast.");
        }, 1700);
      }
    });
  })();

  /* ------------------------------------------------------------------ tour */
  var TOUR_MODE = new URLSearchParams(location.search).has("tour");
  var TOUR_CAPTIONS = [
    "Ask anything. Hearth answers with the plan, the price, and the proof.",
    "Behind every answer: 50+ real abilities, wired to the house.",
    "Money moves only after your one-tap approval — and it is reversible.",
    "Even a refusal gets written down, in plain language.",
    "In the cockpit you can teach Hearth a brand-new skill, live.",
    "Hearth — the house that runs itself, with receipts.",
  ];
  var tourIdx = 0;
  function tourNext() {
    if (!TOUR_MODE || !el.tourCap || (el.tourbar && el.tourbar.hidden)) return;
    el.tourCap.textContent = TOUR_CAPTIONS[Math.min(tourIdx, TOUR_CAPTIONS.length - 1)] || "";
    tourIdx += 1;
  }
  if (TOUR_MODE && el.splash) el.splash.hidden = false;
  el.splashStart && el.splashStart.addEventListener("click", function () {
    if (el.splash) el.splash.hidden = true;
    if (el.tourbar) el.tourbar.hidden = false;
    tourNext();
  });

  /* ------------------------------------------------------------------ misc */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      setIdle();
      closeReceipt();
      closeBrain();
      setSettings(false);
    }
  });
  el.stage && el.stage.addEventListener("click", function (e) {
    if (e.target.closest("button, a, input, select, textarea, label")) return;
    if (el.stage.dataset.state === "answer") setIdle();
  });

  /* ------------------------------------------------------------------ boot */
  tickClock();
  setInterval(tickClock, 10000);
  paintModes();
  setSettings(false);
  setExtras(false);
  setIdle();
  loadPersona();
  loadBrain();
  refreshAmbient();
  refreshTray();
  refreshTicker();
  setInterval(refreshAmbient, 15000);
  setInterval(function () { refreshTray(); }, 12000);
  setInterval(refreshTicker, 20000);

})();
