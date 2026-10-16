/* Hearth — Echo Show surface controller.
 *
 * Voice-first: a tap (or a spoken phrase) runs a real MCP-backed tool call, the
 * result is rendered as glanceable cards rather than a text dump, and the spoken
 * summary is read aloud via the Web Speech API. Display modes mirror the four
 * modes the MCP server implements in `format_display_response`.
 *
 * Loaded as an external file because the server sets CSP script-src 'self'.
 */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  const el = {
    time: $("#clockTime"),
    date: $("#clockDate"),
    eyebrow: $("#stageEyebrow"),
    ambient: $("#ambient"),
    heroTemp: $("#heroTemp"),
    heroLock: $("#heroLock"),
    heroTarget: $("#heroTarget"),
    heroMode: $("#heroMode"),
    said: $("#said"),
    response: $("#response"),
    statusBody: $("#statusBody"),
    trayBody: $("#trayBody"),
    trayCount: $("#trayCount"),
    connDot: $("#connDot"),
    connText: $("#connText"),
    toast: $("#toast"),
    live: $("#live"),
    micBtn: $("#micBtn"),
    micLabel: $("#micLabel"),
    receiptBackdrop: $("#receiptBackdrop"),
    receiptCode: $("#receiptCode"),
    receiptTitle: $("#receiptTitle"),
    receiptSub: $("#receiptSub"),
    receiptBody: $("#receiptBody"),
    receiptUndoBtn: $("#receiptUndoBtn"),
    receiptCloseBtn: $("#receiptCloseBtn"),
    receiptDoneBtn: $("#receiptDoneBtn"),
  };

  let displayMode = "inline";
  let busy = false;
  let toastTimer = null;

  // ---------------------------------------------------------------- helpers

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function num(v, digits = 0) {
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(digits) : "—";
  }

  function toast(msg, isError) {
    el.toast.textContent = msg;
    el.toast.classList.toggle("err", !!isError);
    el.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.toast.classList.remove("show"), 3200);
  }

  function thinking(label) {
    el.response.innerHTML =
      '<span class="thinking"><span class="bars"><i></i><i></i><i></i></span>' +
      esc(label) + "</span>";
  }

  async function call(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    if (!res.ok) {
      let detail = "";
      try {
        detail = (await res.json())?.error || "";
      } catch (_) { /* non-JSON error body */ }
      throw new Error(detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function setConn(state, text) {
    el.connDot.className = "dot " + (state || "");
    el.connText.textContent = text;
  }

  // ------------------------------------------------------------------- clock

  function tickClock() {
    const now = new Date();
    el.time.textContent = now.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    el.date.textContent = now.toLocaleDateString([], {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
  }

  // =========================================================== atmosphere ===
  /* A small canvas particle field plus a real spring integrator.
   *
   * Why hand-rolled rather than a library: the page is served under
   * `script-src 'self'` with no CDN available, so three.js/ogl/gsap are simply
   * not options. A 2D canvas with additive blending and a damped spring gives
   * the same perceptual result for a fraction of the weight, and degrades to a
   * plain gradient background when motion is reduced or the canvas is missing.
   */

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* Motes: slow-rising warm/cool particles with parallax by depth. */
  const MOTE_COUNT = 54;

  function initMotes() {
    const canvas = document.getElementById("motes");
    if (!canvas || !canvas.getContext) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    let w = 0;
    let h = 0;
    let motes = [];
    let raf = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const seed = () => {
      motes = [];
      for (let i = 0; i < MOTE_COUNT; i += 1) {
        // depth in [0,1] drives size, speed, opacity and blur-ish softness
        const depth = Math.random();
        motes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          depth,
          r: 0.6 + depth * 2.4,
          vy: -(0.06 + depth * 0.22),
          drift: (Math.random() - 0.5) * 0.12,
          // warm amber vs cool sky, matching the surface's two signal hues
          warm: Math.random() > 0.42,
          phase: Math.random() * Math.PI * 2,
        });
      }
    };

    const frame = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = "lighter";
      for (const m of motes) {
        m.y += m.vy;
        m.x += m.drift + Math.sin(m.phase + m.y * 0.004) * 0.16;
        if (m.y < -12) {
          m.y = h + 12;
          m.x = Math.random() * w;
        }
        if (m.x < -12) m.x = w + 12;
        if (m.x > w + 12) m.x = -12;

        const a = 0.1 + m.depth * 0.3;
        const g = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.r * 7);
        const tint = m.warm ? "255, 196, 110" : "150, 210, 255";
        g.addColorStop(0, "rgba(" + tint + "," + a + ")");
        g.addColorStop(1, "rgba(" + tint + ",0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(m.x, m.y, m.r * 7, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = window.requestAnimationFrame(frame);
    };

    resize();
    seed();
    window.addEventListener("resize", () => {
      resize();
      seed();
    });

    if (reduceMotion.matches) {
      // Draw one static frame: the material still reads, nothing moves.
      ctx.clearRect(0, 0, w, h);
      window.cancelAnimationFrame(raf);
      return { stop() {} };
    }
    raf = window.requestAnimationFrame(frame);
    return {
      stop() { window.cancelAnimationFrame(raf); },
    };
  }

  /* Critically-damped-ish spring for card tilt. Real springs settle with
   * overshoot and inertia; a CSS cubic-bezier cannot, which is exactly why
   * this felt flat before. */
  function springTilt() {
    const cards = Array.from(document.querySelectorAll(".metric"));
    if (!cards.length || reduceMotion.matches) return { stop() {} };

    const state = cards.map((el) => ({
      el,
      tx: 0, ty: 0, x: 0, y: 0, vx: 0, vy: 0,
    }));

    let raf = 0;
    let running = false;

    const step = () => {
      let settled = true;
      for (const s of state) {
        // stiffness 0.12, damping 0.78 -> slight overshoot, ~350ms settle
        const k = 0.12;
        const d = 0.78;
        s.vx += (s.tx - s.x) * k;
        s.vy += (s.ty - s.y) * k;
        s.vx *= d;
        s.vy *= d;
        s.x += s.vx;
        s.y += s.vy;
        if (Math.abs(s.tx - s.x) > 0.02 || Math.abs(s.ty - s.y) > 0.02) settled = false;
        // translateZ is already applied in CSS; append the tilt only.
        s.el.style.setProperty("--rx", s.y.toFixed(3) + "deg");
        s.el.style.setProperty("--ry", s.x.toFixed(3) + "deg");
      }
      raf = settled ? 0 : window.requestAnimationFrame(step);
      if (!raf) running = false;
    };

    const kick = () => {
      if (!running) {
        running = true;
        raf = window.requestAnimationFrame(step);
      }
    };

    const onMove = (ev) => {
      const max = 5.2;
      cards.forEach((el, i) => {
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        const nx = (ev.clientX - cx) / Math.max(1, r.width / 2);
        const ny = (ev.clientY - cy) / Math.max(1, r.height / 2);
        state[i].tx = Math.max(-1, Math.min(1, nx)) * max;
        state[i].ty = Math.max(-1, Math.min(1, ny)) * -max;
      });
      kick();
    };

    const onLeave = () => {
      state.forEach((s) => { s.tx = 0; s.ty = 0; });
      kick();
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave, { passive: true });

    return {
      stop() {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerleave", onLeave);
        if (raf) window.cancelAnimationFrame(raf);
      },
    };
  }

  // ------------------------------------------------------- speech synthesis

  /* Strip markdown/pipes/URLs the same way the server's sanitize_voice_output
   * does, so the voice channel matches the voice-only display mode. */
  function sanitizeForVoice(text) {
    return String(text || "")
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`([^`]*)`/g, "$1")
      .replace(/https?:\/\/\S+/g, " ")
      .replace(/\|/g, " ")
      .replace(/[*_#>]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function speak(text) {
    const clean = sanitizeForVoice(text);
    el.live.textContent = clean;
    if (!("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(clean);
      u.rate = 1.02;
      u.pitch = 1.0;
      u.volume = 1.0;
      window.speechSynthesis.speak(u);
    } catch (_) { /* speech unavailable; live region still updated */ }
  }

  function listening(on) {
    el.micBtn.classList.toggle("listening", on);
    el.micLabel.textContent = on ? "Listening…" : "Speak";
  }

  function setupMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      el.micBtn.disabled = true;
      el.micLabel.textContent = "No mic";
      el.micBtn.title = "Web Speech recognition is not available in this browser";
      return;
    }
    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onstart = () => listening(true);
    rec.onend = () => listening(false);
    rec.onerror = (e) => {
      listening(false);
      if (e.error && e.error !== "aborted") toast("Could not hear that", true);
    };
    rec.onresult = async (e) => {
      const phrase = e.results?.[0]?.[0]?.transcript?.trim();
      if (!phrase) return;
      el.said.innerHTML = '<span class="q">&ldquo;</span>' + esc(phrase) + '<span class="q">&rdquo;</span>';
      await handleUtterance(phrase);
    };

    el.micBtn.addEventListener("click", () => {
      if (busy) return;
      try {
        rec.start();
      } catch (_) {
        toast("Microphone busy", true);
      }
    });
  }

  /* Map a spoken sentence onto the closest showcase action. Kept deliberately
   * small and inspectable rather than pretending to be an LLM router. */
  const UTTERANCE_ROUTES = [
    { re: /break|intruder|alarm|door|perimeter|someone|patio/i, go: "/api/forensics/reconstruct", body: { incident_type: "perimeter_anomaly" }, label: "Reconstructing incident" },
    { re: /parliament|council|tariff|thermostat|comfort|debate|recommend/i, go: "/api/parliament/deliberate", body: { topic: "evening tariff vs comfort" }, label: "Convening parliament" },
    { re: /7 days|seven days|week|simulate|forecast|future|break/i, go: "/api/causal/simulate", body: { days_ahead: 7, iterations: 250 }, label: "Simulating seven days" },
    { re: /solar|sell|neighbou?r|grid|export|vpp|power plant/i, go: "/api/swarm/grid", body: {}, label: "Coordinating microgrid" },
    { re: /treaty|mediat|fight|argue|settle|family|chore/i, go: "/api/mediation/treaty", body: {}, label: "Negotiating treaty" },
    { re: /fridge|bearing|noise|acoustic|appliance|fft|dying/i, go: "/api/acoustic/scan", body: {}, label: "Analysing appliance acoustics" },
    { re: /pantry|milk|coffee|restock|order|buy|grocery|everything|fix groceries|robux|toy/i, go: "/api/commerce/autopilot-checkout", passPhrase: true, label: "Staging your restock" },
    { re: /save.*800|save money|subscription|renewal|audit.*bill|waste/i, go: "/api/renewals", body: {}, label: "Auditing subscriptions" },
  ];

  async function handleUtterance(phrase) {
    const hit = UTTERANCE_ROUTES.find((r) => r.re.test(phrase));
    if (!hit) {
      const msg =
        "I did not match that to a capability. Try asking about a break-in, the household parliament, a seven day forecast, selling solar, the family treaty, or restocking groceries.";
      el.response.textContent = msg;
      speak(msg);
      return;
    }
    const body = hit.passPhrase
      ? { utterance: phrase, voice_confidence: 0.95 }
      : hit.body;
    await run(hit.go, body, hit.label);
  }

  // -------------------------------------------------------------- rendering

  function cardList(items) {
    if (!items || !items.length) return "";
    return (
      '<div class="cards">' +
      items
        .slice(0, 4)
        .map(
          (c) =>
            '<div class="card"><div class="top">' +
            '<span class="name">' + esc(c.name) + "</span>" +
            (c.tag ? '<span class="tag">' + esc(c.tag) + "</span>" : "") +
            (c.score != null ? '<span class="score num">' + esc(c.score) + "</span>" : "") +
            "</div>" +
            (c.body ? '<div class="body">' + c.body + "</div>" : "") +
            "</div>"
        )
        .join("") +
      (items.length > 4
        ? '<div class="reply">+ ' + (items.length - 4) + " more</div>"
        : "") +
      "</div>"
    );
  }

  /* Big categorical result banner.
   *
   * `value` is an already-formatted string, not a 0-1 confidence. Several
   * callers pass quantities that are not probabilities at all (a Nash score out
   * of 10, a clearing price per kWh), and treating those as confidences produced
   * nonsense like "1000%" and a meaningless "36%". Each renderer is now
   * responsible for formatting its own measurement honestly.
   */
  function verdictBanner(icon, label, value, tone) {
    const cls = tone === "bad" ? " bad" : tone === "warn" ? " warn" : "";
    return (
      '<div class="verdict' + cls + '">' +
      '<span class="icon" aria-hidden="true">' + esc(icon || "\u2713") + "</span>" +
      '<span class="label">' + esc(label) + "</span>" +
      '<span class="conf num">' + esc(value) + "</span>" +
      "</div>"
    );
  }

  /* SHOUTING_SNAKE -> Shouting Snake. Enum-ish values come straight out of the
   * engines and read as machine output until they are formatted. */
  function humanize(v) {
    return String(v == null ? "" : v)
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  /* Tone a label from its own words so a scary result is never shown in the
   * calm green used for a benign one. */
  function toneFor(text) {
    const v = String(text || "");
    if (/INTRUDER|CORRUPT|FAIL|ERROR|CRITICAL/i.test(v)) return "bad";
    if (/STARVATION|DEGRADED|WARN|CRITICAL|HIGH/i.test(v)) return "warn";
    return "";
  }

  const RENDERERS = {
    "/api/forensics/reconstruct": (d) => {
      const timeline = (d.timeline || []).slice(0, 3).map(
        (e) =>
          '<div class="card"><div class="top"><span class="name">' +
          esc(e.subsystem || "") + '</span><span class="tag">' + esc(e.timestamp || "") +
          "</span></div><div class=\"body\"><em>" + esc(e.event || "") + "</em><br/>" +
          esc(e.causal_factor || "") + "</div></div>"
      );
      return (
        verdictBanner("🔍", humanize(d.verdict), num(Number(d.confidence_score) * 100, 0) + "%", toneFor(d.verdict)) +
        '<div class="reply">' + esc(d.summary || "") + "</div>" +
        '<div class="cards">' + timeline.join("") + "</div>" +
        (d.audit_proof
          ? '<div class="hashline">Merkle proof ' + esc(String(d.audit_proof).slice(0, 64)) + "…</div>"
          : "")
      );
    },

    "/api/parliament/deliberate": (d) => {
      const session = d.session || d;
      const speeches = (session.speeches || []).map((s) => ({
        name: s.minister,
        tag: s.stance,
        score: "U " + num(s.utility_score, 1),
        body: "<em>" + esc((s.arguments || [])[0] || "") + "</em>",
      }));
      const vote = session.vote || "";
      const minority = session.minority_report
        ? '<div class="card"><div class="top"><span class="name">Dissent — ' +
          esc(session.minority_report.minister) +
          '</span></div><div class="body">' + esc(session.minority_report.objection || "") + "</div></div>"
        : "";
      return (
        verdictBanner("🏛️",
          "NASH CONSENSUS \u00b7 " + (vote || "deliberated"),
          num(session.nash_equilibrium_score, 1) + "/10",
          session.nash_equilibrium_score < 7 ? "warn" : "") +
        cardList(speeches) +
        minority +
        '<div class="reply">Searched ' + num(session.candidate_count) + " candidate actions across a discrete action grid.</div>"
      );
    },

    "/api/causal/simulate": (d) => {
      const vulns = (d.vulnerabilities || []).map((v) => ({
        name: humanize(v.hazard_type),
        tag: v.impact_severity,
        score: num(v.probability_pct, 0) + "%",
        body: "<em>" + esc(v.contingency_action || "") + "</em><br/>" + esc(v.root_cause || ""),
      }));
      const q = d.quantiles?.baseline || {};
      return (
        verdictBanner("🔮", "GRID RESILIENCE",
          num(d.grid_resilience_score, 0) + "/100",
          d.grid_resilience_score < 60 ? "warn" : "") +
        cardList(vulns) +
        '<div class="reply">' +
        num(d.monte_carlo_iterations) + " Monte Carlo trajectories · p50 $" + num(q.p50, 2) +
        " · p95 $" + num(q.p95, 2) + " · CVaR95 $" + num(q.cvar95, 2) +
        " · saves $" + num(d.expected_savings_usd, 2) + "</div>"
      );
    },

    "/api/swarm/grid": (d) => {
      const econ = d.economic_impact || {};
      const env = d.environmental_impact || {};
      const tx = (d.p2p_transactions || []).map((t) => ({
        name: t.from_node + " → " + t.to_node,
        tag: num(t.power_kw, 1) + " kW",
        score: "$" + num(t.settlement_rate_kwh, 3) + "/kWh",
        body:
          "Seller <em>+$" + num(t.seller_dividend_hr, 2) + "/hr</em> · buyer saves <em>$" +
          num(t.buyer_savings_hr, 2) + "/hr</em>",
      }));
      return (
        // A clearing price is a price, not a probability: show $/kWh.
        verdictBanner("⚡", "P2P CLEARING PRICE",
          "$" + num(d.cooperative_rate_kwh, 3) + "/kWh", "") +
        cardList(tx) +
        '<div class="reply">Community dividend $' + num(econ.total_community_dividend_hourly_usd, 2) +
        "/hr · $" + num(econ.annualized_neighborhood_wealth_retention_usd, 0) +
        "/yr retained · " + num(env.carbon_offset_kg_co2e_hr, 2) + " kg CO₂e avoided per hour</div>"
      );
    },

    "/api/mediation/treaty": (d) => {
      const covs = (d.covenants || []).map((c) => ({
        name: c.resident,
        tag: humanize(c.domain),
        score: num(c.satisfaction_pct, 0) + "%",
        body: "<em>" + esc(c.concession_granted || "") + "</em><br/>In return: " +
          esc(c.reciprocal_obligation || ""),
      }));
      return (
        verdictBanner("🤝", "TREATY FAIRNESS",
          num(d.fairness_index_out_of_10, 2) + "/10",
          d.fairness_index_out_of_10 < 8 ? "warn" : "") +
        cardList(covs) +
        '<div class="reply">Nash achievement ' + num((d.nash_achievement || 0) * 100, 0) +
        "% · coverage " + num(d.cooperation_coverage_pct, 0) + "% · envy gap " +
        num(d.envy_gap, 3) + " · $" + num(d.projected_monthly_savings_usd, 2) +
        "/mo. Fairness is measured and falls when a household is over-subscribed. " +
        "Raw grievances were never shared between residents.</div>"
      );
    },

    "/api/renewals": (d) => {
      const cards = (d.renewals || []).map((s) => ({
        name: s.name,
        tag: s.recommendation === "cancel" ? "cancel" : "downgrade",
        score: "+$" + num(s.savings_yr, 2) + "/yr",
        body: "<em>" + esc(s.usage_status || "") + "</em><br/>" + esc(s.reason || ""),
      }));
      const stageRow = '<div class="stage-row">' + (d.renewals || []).map((s) =>
        '<button type="button" class="btn ghost" data-sub="' + esc(s.id) + '">Stage +$' +
        num(s.savings_yr, 2) + "/yr</button>").join("") + "</div>";
      return (
        verdictBanner("💸", "WASTE FOUND",
          "+$" + num(d.potential_save_yr, 2) + "/yr", "") +
        cardList(cards) + stageRow +
        '<div class="reply">Nothing cancelled — stage one tap at a time, Approve in the tray to execute. ' +
        "Total spend $" + num(d.total_annual_spend, 2) + "/yr.</div>"
      );
    },

    "/api/commerce/autopilot-checkout": (d) => {
      if (d.blocked) {
        return (
          verdictBanner("🛡️", "CHILD SAFETY GUARDRAIL", "BLOCKED", "bad") +
          '<div class="reply"><strong>🛡️ Leo (9) is blocked from purchasing by architectural design, not prompt.</strong><br/>' +
          esc(d.message || "Child profile 'Leo' is restricted from staging orders or making purchases.") + "</div>"
        );
      }
      if (d.clarification_required) {
        return (
          verdictBanner("🛒", "WHICH ITEMS?", "clarify", "warn") +
          '<div class="reply">' + esc(d.message || "Which items should I stage?") + "</div>"
        );
      }
      const cart = d.cart_preview || {};
      const items = (cart.items || []).map((it) => ({
        name: it.name,
        tag: "Subscribe & Save",
        score: "$" + num(it.unit_price, 2),
        body: "was $" + num(it.original_price, 2) + " · <em>" + esc(it.prime_delivery || "") + "</em>",
      }));
      return (
        verdictBanner("🛒", "CART STAGED — NOTHING ORDERED",
          "$" + num(cart.final_total, 2) + " (saves $" + num(cart.savings, 2) + ")",
          "") +
        cardList(items) +
        '<div class="reply">Tap Approve in the tray to order · one tap undoes. ' +
        esc(d.message || "") + "</div>"
      );
    },

    "/api/acoustic/scan": (d) => {
      const apps = (d.appliances || []).map((a) => ({
        name: a.name,
        tag: a.status === "HEALTHY" ? "healthy" : "degraded",
        score: num(a.failure_probability_14d * 100, 0) + "% / 14d",
        body:
          "<em>" + num(a.detected_peak_hz, 1) + " Hz peak</em> (+" + num(a.delta_db, 1) +
          " dB, kurtosis " + num(a.diagnostics?.kurtosis, 2) + ")<br/>" +
          esc(a.root_cause || ""),
      }));
      const degraded = (d.appliances || []).some((a) => a.status !== "HEALTHY");
      // Report the engine's own measured risk for the worst appliance rather
      // than a confidence figure invented here.
      const worstRisk = (d.appliances || []).reduce(
        (mx, a) => Math.max(mx, Number(a.failure_probability_14d) || 0), 0);
      return (
        verdictBanner("🩺",
          degraded ? "APPLIANCE WEAR DETECTED" : "ALL APPLIANCES HEALTHY",
          degraded ? num(worstRisk * 100, 0) + "% / 14d" : "0% / 14d",
          degraded ? "warn" : "") +
        cardList(apps) +
        '<div class="reply">' + esc(d.voice_summary || "") + "</div>"
      );
    },
  };

  function render(path, d) {
    const fn = RENDERERS[path];
    return fn ? fn(d) : '<div class="reply">' + esc(d.voice_summary || d.summary || d.message || JSON.stringify(d).slice(0, 400)) + "</div>";
  }

  function speechLineFor(path, d) {
    if (d.voice_summary) return d.voice_summary;
    if (path.includes("forensics")) return d.summary;
    if (path.includes("mediation")) {
      return "Treaty fairness " + num(d.fairness_index_out_of_10, 2) +
        " out of 10, with " + (d.covenants || []).length + " covenants. Recouping " +
        num(d.projected_monthly_savings_usd, 0) + " dollars a month.";
    }
    if (path.includes("swarm")) return d.voice_summary;
    if (path.includes("parliament")) return "Parliament reached a consensus at a Nash score of " + num(d.nash_equilibrium_score, 1) + ".";
    if (path.includes("causal")) return "Found " + (d.vulnerabilities || []).length + " vulnerabilities. Resilience score " + num(d.grid_resilience_score, 0) + ".";
    if (path.includes("renewals")) {
      return "Found " + num(d.potential_save_yr, 0) +
        " dollars a year in waste across " + (d.renewals || []).length +
        " subscriptions. Nothing cancelled — tap the tray to stage them.";
    }
    if (path.includes("autopilot-checkout")) {
      if (d.blocked) return "Blocked by child safety contract. Leo cannot make purchases.";
      if (d.clarification_required) return "Which items should I stage? Nothing is ordered yet.";
      const cart = d.cart_preview || {};
      return "Cart staged for " + (cart.item_count || 0) + " items, saving " +
        num(cart.savings, 2) + " dollars. Nothing ordered until you tap Approve.";
    }
    return "Done.";
  }

  // ----------------------------------------------------------------- runner

  async function run(path, body, label) {
    if (busy) return;
    busy = true;
    document.querySelectorAll(".ask").forEach((b) => (b.disabled = true));
    thinking(label || "Working…");

    try {
      const data = await call(path, body);
      el.response.innerHTML = render(path, data);
      tickMoney();
      // Recede the ambient hero so the reply owns the stage, and start the
      // reply region scrolled to the top of the new content.
      document.body.classList.add("has-result");
      el.said.parentElement.scrollTop = 0;
      speak(speechLineFor(path, data));
      el.eyebrow.textContent = label || "Result";
      await refreshTray();
    } catch (err) {
      el.response.innerHTML =
        '<span class="u-color-var-e-bad" >Could not complete that: ' + esc(err.message) + "</span>";
      speak("Sorry, that did not work.");
    } finally {
      busy = false;
      document.querySelectorAll(".ask").forEach((b) => (b.disabled = false));
    }
  }

  // ------------------------------------------------------------ ambient state

  /* Populate the glanceable resting state from real telemetry.
   *
   * `/api/home` reports temperature in Celsius (the house runs on a metric
   * digital twin), so it is converted for display: the product narrative is
   * US-centric ($0.48/kWh tariffs, a 68F office setpoint), and an Echo Show in
   * the US renders Fahrenheit. The conversion is explicit rather than silently
   * relabelling a Celsius value as Fahrenheit. */
  const cToF = (c) => (Number.isFinite(Number(c)) ? Number(c) * 9 / 5 + 32 : null);

  function setMetric(id, value, sub, tone) {
    const box = document.getElementById(id);
    if (!box) return;
    const v = box.querySelector("[data-v]");
    const s = box.querySelector("[data-s]");
    if (v) v.textContent = value;
    if (s) s.textContent = sub || "\u00a0";
    if (tone) box.classList.add(tone);
  }

  async function refreshAmbient() {
    try {
      const [home, pantry] = await Promise.all([
        fetch("/api/home").then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch("/api/commerce/depletion")
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
      ]);

      if (home) {
        const tempF = cToF(home.living_room?.climate?.current_c);
        el.heroTemp.textContent = tempF == null ? "--" : num(tempF, 0);

        const lock = home.entryway?.lock?.front_door;
        el.heroLock.textContent =
          lock === "locked" ? "Locked" : lock ? "Unlocked" : "Unknown";
        el.heroLock.style.color =
          lock === "locked" ? "var(--e-ok)" : lock ? "var(--e-bad)" : "";

        const climate = home.living_room?.climate || {};
        if (el.heroTarget) {
          const t = Number(climate.target_c);
          el.heroTarget.textContent = Number.isFinite(t)
            ? num(cToF(t), 1) + " \u00b0F"
            : "\u2014";
        }
        if (el.heroMode) {
          const bits = [climate.mode, climate.fan].filter(Boolean);
          el.heroMode.textContent = bits.length ? bits.join(" \u00b7 ") : "\u2014";
        }

        const e = home.energy || {};
        setMetric("mEnergy",
          num(e.current_draw_kw, 2) + " kW",
          e.eco_score ? "eco score " + num(e.eco_score, 0) : "",
          "ok");
        setMetric("mSolar",
          num(e.solar_generation_kw, 2) + " kW",
          e.net_grid_kw != null ? "grid " + num(e.net_grid_kw, 2) + " kW" : "",
          "cool");

        setConn("ok", "connected");
        el.statusBody.innerHTML =
          '<div class="card"><div class="body">' +
          esc("Scene: " + (home.active_scene || "—")) +
          " &middot; target " + num(home.living_room?.climate?.target_c, 1) + "°C" +
          " &middot; lights " + (home.living_room?.lights?.on ? "on" : "off") +
          "</div></div>";
      } else {
        setConn("warn", "no telemetry");
        el.statusBody.innerHTML =
          '<div class="card"><div class="body">Household telemetry unavailable.</div></div>';
      }

      // Pantry: how soon does the next staple run out?
      const items = Array.isArray(pantry) ? pantry
        : pantry?.items || pantry?.forecast || pantry?.depletion || [];
      if (items.length) {
        const soonest = items
          .slice()
          .sort((a, b) => (a.days_until_empty ?? 99) - (b.days_until_empty ?? 99))[0];
        setMetric("mPantry",
          num(soonest.days_until_empty, 0) + "d",
          soonest.name || soonest.item || "next staple",
          "warn");
      } else {
        setMetric("mPantry", "—", "no forecast");
      }
    } catch (_) {
      setConn("bad", "offline");
    }
  }

  async function refreshTray() {
    try {
      const res = await fetch("/api/proposals?limit=20", { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("tray unavailable");
      const data = await res.json();
      renderTray(data.proposals || [], data.pending_count || 0);
      setConn("ok", "connected");
    } catch (_) {
      setConn("warn", "degraded");
    }
  }

  function renderTray(items, pendingCount) {
    if (!el.trayBody) return;
    if (pendingCount > 0) {
      el.trayCount.hidden = false;
      el.trayCount.textContent = pendingCount;
    } else {
      el.trayCount.hidden = true;
    }
    const pend = items.filter((p) => p && p.status === "pending").slice(0, 5);
    const done = items.filter((p) => p && p.status !== "pending").slice(0, 3);
    if (!pend.length && !done.length) {
      el.trayBody.innerHTML =
        '<div class="empty">Nothing has run without you. Consequential actions appear here first — and undo in one tap.</div>';
      return;
    }
    el.trayBody.innerHTML =
      pend.map((p) =>
        '<div class="tray-item"><div class="tray-title">' + esc(p.title) + "</div>" +
        '<div class="tray-meta">' + esc(p.kind || "") +
        (p.cost_delta_yr ? " · $" + num(Math.abs(p.cost_delta_yr), 2) + "/yr" : "") + " · undoes in 1 tap</div>" +
        '<div class="tray-actions"><button type="button" class="btn primary" data-act="approve" data-pid="' +
        esc(p.id) + '">Approve</button>' +
        '<button type="button" class="btn ghost" data-act="reject" data-pid="' +
        esc(p.id) + '">Reject</button></div></div>').join("") +
      done.map((p) =>
        '<div class="tray-item decided"><div class="tray-title">' + esc(p.title) + "</div>" +
        '<div class="tray-actions"><button type="button" class="btn ghost" data-act="undo" data-pid="' +
        esc(p.id) + '">Undo</button></div></div>').join("");
  }

  // ---------------------------------------------------------------- wiring

  document.querySelectorAll(".ask").forEach((btn) => {
    btn.addEventListener("click", () => {
      const path = btn.dataset.go;
      let body = {};
      try {
        body = JSON.parse(btn.dataset.body || "{}");
      } catch (_) {
        body = {};
      }
      el.said.innerHTML = '<span class="q">&ldquo;</span>' + esc(btn.dataset.ask || "") + '<span class="q">&rdquo;</span>';
      run(path, body, btn.textContent.trim());
    });
  });

  // ============================================================= Earcons ===
  let audioCtx = null;
  function getAudioContext() {
    if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
      const AC = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AC();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
    return audioCtx;
  }

  function playTone(freq, type, startTime, duration, gainVal, dest) {
    try {
      const osc = dest.context.createOscillator();
      const gain = dest.context.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, startTime);
      gain.gain.setValueAtTime(0.0001, startTime);
      gain.gain.exponentialRampToValueAtTime(gainVal, startTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
      osc.connect(gain);
      gain.connect(dest);
      osc.start(startTime);
      osc.stop(startTime + duration + 0.05);
    } catch (_) {}
  }

  function playEarcon(name) {
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;
      const master = ctx.createGain();
      master.gain.setValueAtTime(0.18, t);
      master.connect(ctx.destination);

      if (name === "stage") {
        playTone(523.25, "sine", t, 0.12, 0.22, master);
        playTone(659.25, "sine", t + 0.09, 0.2, 0.25, master);
      } else if (name === "approve") {
        playTone(523.25, "sine", t, 0.22, 0.2, master);
        playTone(659.25, "triangle", t + 0.05, 0.24, 0.22, master);
        playTone(783.99, "sine", t + 0.1, 0.3, 0.26, master);
        playTone(1046.50, "sine", t + 0.15, 0.4, 0.24, master);
      } else if (name === "undo") {
        playTone(783.99, "sine", t, 0.11, 0.22, master);
        playTone(659.25, "sine", t + 0.08, 0.13, 0.2, master);
        playTone(523.25, "sine", t + 0.16, 0.22, 0.18, master);
      } else if (name === "block") {
        playTone(329.63, "sawtooth", t, 0.14, 0.12, master);
        playTone(261.63, "sine", t + 0.1, 0.22, 0.2, master);
      }
    } catch (_) {}
  }

  // ======================================================== Glass Receipt ===
  function showReceipt(p) {
    if (!el.receiptBackdrop || !p) return;
    const exec = p.execution || {};
    const code = exec.receipt_code || ("HEARTH-RC-" + (p.id || "000").toUpperCase());
    if (el.receiptCode) el.receiptCode.textContent = code;
    if (el.receiptTitle) el.receiptTitle.textContent = p.title || "Action Applied";
    if (el.receiptUndoBtn) el.receiptUndoBtn.dataset.pid = p.id || "";

    const kind = p.kind || "";
    let html = "";
    if (kind === "subscription_cancel" || kind === "cancel_subscription" || kind === "downgrade_subscription") {
      const saveYr = exec.savings_yr || Math.abs(p.cost_delta_yr || 0);
      const serv = exec.service_name || p.title;
      const portal = exec.portal_url || "";
      const phone = exec.support_phone || "";
      html =
        '<div class="receipt-row"><span class="receipt-rk">Service</span><span class="receipt-rv">' + esc(serv) + '</span></div>' +
        '<div class="receipt-row"><span class="receipt-rk">Annual Household Savings</span><span class="receipt-rv highlight num">+$' + num(saveYr, 2) + '/yr</span></div>' +
        (portal ? '<div class="receipt-row"><span class="receipt-rk">Provider Cancellation Portal</span><a class="receipt-rv link" href="' + esc(portal) + '" target="_blank" rel="noopener">Open ' + esc(portal.replace(/^https?:\/\//, '')) + ' &rarr;</a></div>' : '') +
        (phone ? '<div class="receipt-row"><span class="receipt-rk">Concierge Phone Assist</span><span class="receipt-rv num mono">' + esc(phone) + '</span></div>' : '') +
        '<div class="receipt-row"><span class="receipt-rk">Human Reversibility</span><span class="receipt-rv">100% Guaranteed reversible before billing cycle</span></div>';
    } else if (kind === "commerce_order") {
      const tot = exec.final_total || Math.abs(p.cost_delta_yr || 0);
      const sav = exec.savings || 0;
      const items = exec.items || [];
      const sched = exec.delivery_schedule?.slot_name || "Amazon Prime Dedicated Box (Tuesday)";
      html =
        '<div class="receipt-row"><span class="receipt-rk">Delivery Window</span><span class="receipt-rv">' + esc(sched) + '</span></div>' +
        '<div class="receipt-row"><span class="receipt-rk">Replenishment Total</span><span class="receipt-rv highlight num">$' + num(tot, 2) + '</span></div>' +
        (sav > 0 ? '<div class="receipt-row"><span class="receipt-rk">Subscribe & Save Discount (15%)</span><span class="receipt-rv highlight num">-$' + num(sav, 2) + '</span></div>' : '') +
        (items.length ? '<div class="receipt-items-list">' + items.map(it => '<div class="receipt-item-line"><span>' + esc(it.name || it.item_id) + '</span><span class="num mono">$' + num(it.price, 2) + '</span></div>').join('') + '</div>' : '') +
        '<div class="receipt-row"><span class="receipt-rk">Human Reversibility</span><span class="receipt-rv">Reversible in 1 tap prior to fulfillment dispatch</span></div>';
    } else {
      html =
        '<div class="receipt-row"><span class="receipt-rk">Action Verdict</span><span class="receipt-rv">' + esc(exec.note || "Executed successfully") + '</span></div>' +
        (p.cost_delta_yr ? '<div class="receipt-row"><span class="receipt-rk">Financial Impact</span><span class="receipt-rv highlight num">$' + num(Math.abs(p.cost_delta_yr), 2) + '/yr</span></div>' : '') +
        '<div class="receipt-row"><span class="receipt-rk">Audit Seal</span><span class="receipt-rv mono">SHA-256 Merkle Ratchet</span></div>';
    }
    if (el.receiptBody) el.receiptBody.innerHTML = html;
    el.receiptBackdrop.hidden = false;
  }

  function hideReceipt() {
    if (el.receiptBackdrop) {
      el.receiptBackdrop.hidden = true;
    }
  }

  if (el.receiptUndoBtn) {
    el.receiptUndoBtn.addEventListener("click", async () => {
      const pid = el.receiptUndoBtn.dataset.pid;
      if (!pid || busy) return;
      try {
        const d = await call("/api/proposals/" + encodeURIComponent(pid) + "/undo", {});
        const ok = d && d.ok !== false;
        playEarcon("undo");
        toast(ok ? "Undone — reversed in the ledger." : "Undo failed.", !ok);
        speak(ok ? "Undone. Action reversed." : "Undo failed.");
        hideReceipt();
        await refreshTray();
      } catch (err) {
        toast("Undo failed.", true);
      }
    });
  }
  if (el.receiptCloseBtn) el.receiptCloseBtn.addEventListener("click", hideReceipt);
  if (el.receiptDoneBtn) el.receiptDoneBtn.addEventListener("click", hideReceipt);
  if (el.receiptBackdrop) {
    el.receiptBackdrop.addEventListener("click", (e) => {
      if (e.target === el.receiptBackdrop) hideReceipt();
    });
  }

  /* Staged-card buttons rendered inside replies (e.g. renewals "Stage" row). */
  el.response.addEventListener("click", async (e) => {
    const st = e.target && e.target.closest ? e.target.closest("[data-sub]") : null;
    if (!st || busy) return;
    try {
      const data = await call("/api/renewals/stage", { id: st.dataset.sub });
      playEarcon("stage");
      toast(data.message || "Staged in the tray.");
      speak("Staged. Approve it in the tray when ready — nothing is cancelled yet.");
      await refreshTray();
    } catch (err) {
      playEarcon("block");
      toast("Could not stage that.", true);
    }
  });

  /* Approval tray decisions (Approve / Reject / Undo) live on the Echo surface. */
  if (el.trayBody) {
    el.trayBody.addEventListener("click", async (e) => {
      const b = e.target && e.target.closest ? e.target.closest("[data-act]") : null;
      if (!b || busy) return;
      const pid = b.dataset.pid;
      const act = b.dataset.act;
      b.disabled = true;
      try {
        if (act === "undo") {
          const d = await call("/api/proposals/" + encodeURIComponent(pid) + "/undo", {});
          const ok = d && d.ok !== false;
          playEarcon("undo");
          hideReceipt();
          toast(ok ? "Undone — reversed in the ledger." : "Undo failed.", !ok);
          speak(ok ? "Undone." : "Undo failed.");
        } else {
          const d = await call("/api/proposals/" + encodeURIComponent(pid) + "/decide",
            { approved: act === "approve" });
          const ok = d && d.ok !== false;
          if (act === "approve") {
            playEarcon("approve");
            if (ok && d) showReceipt(d);
          } else {
            playEarcon("undo");
          }
          toast(ok ? "Sealed in the ledger." : "That did not go through.", !ok);
          speak(ok ? (act === "approve" ? "Approved. Receipt sealed." : "Rejected.") : "That did not go through.");
        }
        await refreshTray();
        if (act === "approve" || act === "reject") {
          const sealed = el.trayBody.querySelector(".tray-item.decided");
          if (sealed) sealed.classList.add("sealed");
        }
      } catch (err) {
        playEarcon("block");
        toast("That did not go through.", true);
        b.disabled = false;
      }
    });
  }

  document.querySelectorAll(".chip[data-mode]").forEach((chip) => {
    chip.addEventListener("click", () => {
      displayMode = chip.dataset.mode;
      document.body.dataset.display = displayMode;
      document.querySelectorAll(".chip[data-mode]").forEach((c) =>
        c.setAttribute("aria-pressed", String(c.dataset.mode === displayMode))
      );
      toast("Display mode: " + displayMode);
    });
  });

  const personaBtn = document.querySelector("#personaToggleBtn");
  if (personaBtn) {
    async function syncPersona() {
      try {
        const r = await fetch("/api/persona");
        if (r.ok) {
          const d = await r.json();
          const pid = d.active_persona?.id || "admin";
          const isChild = pid === "child" || pid === "leo";
          personaBtn.dataset.persona = isChild ? "child" : "admin";
          personaBtn.setAttribute("aria-pressed", String(isChild));
          personaBtn.textContent = isChild ? "🧒 Leo (Child)" : "👤 Alex (Adult)";
        }
      } catch (_) {}
    }
    syncPersona();

    personaBtn.addEventListener("click", async () => {
      const cur = personaBtn.dataset.persona || "admin";
      const next = cur === "admin" ? "child" : "admin";
      try {
        const res = await fetch("/api/persona", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: next }),
        });
        if (res.ok) {
          const isChild = next === "child";
          personaBtn.dataset.persona = next;
          personaBtn.setAttribute("aria-pressed", String(isChild));
          personaBtn.textContent = isChild ? "🧒 Leo (Child)" : "👤 Alex (Adult)";
          if (isChild) {
            playEarcon("block");
            toast("Active: Leo (Child) — child guardrail engaged", false);
            speak("Switched to Leo persona. Financial orders and unlocks are restricted.");
            el.said.innerHTML = '<span class="q">&ldquo;</span>Leo: buy me Robux<span class="q">&rdquo;</span>';
            el.response.innerHTML =
              verdictBanner("🛡️", "CHILD SAFETY GUARDRAIL", "BLOCKED", "bad") +
              '<div class="reply"><strong>🛡️ Leo (9) is blocked from purchasing or unlocking by architectural design, not prompt.</strong><br/>' +
              'Child safety contract: orders, subscription cancellations, and perimeter doors are hard-refused at the AST gateway layer. Zero proposals staged.</div>';
          } else {
            playEarcon("approve");
            toast("Active: Alex (Adult) — full authorization", false);
            speak("Switched to adult profile. Full household authorization enabled.");
            el.said.innerHTML = '<span class="q">&ldquo;</span>Alexa, ask Hearth to save me $800 on renewals<span class="q">&rdquo;</span>';
            el.response.innerHTML =
              '<div class="reply">Tap a suggestion, or speak. Nothing is bought, unlocked or changed without your approval.</div>';
          }
        }
      } catch (err) {
        toast("Could not switch persona", true);
      }
    });
  }

  tickClock();
  setInterval(tickClock, 15000);
  setupMic();
  refreshAmbient();
  refreshTray();
  setInterval(() => { refreshAmbient(); refreshTray(); }, 20000);

  /* Atmosphere last: it is decoration and must never delay data. */
  initMotes();
  springTilt();

  /* ---------------------------------------------------------- guided tour
   * ?tour=1 drives the hero flow end-to-end with captions, so a recorded
   * take needs no timing skill: audit -> stage -> approve -> undo ->
   * fix groceries -> approve -> undo. Every step is a real API call. */
  /* Money count-up: verdict figures tick like a slot machine. Runs on any
   * verdict banner whose value starts with +$ or $. Pure presentation. */
  function tickMoney() {
    el.response.querySelectorAll(".verdict .conf").forEach((node) => {
      const m = (node.textContent || "").match(/^\+?\$([\d,]+\.\d{2})/);
      if (!m || node.dataset.ticked) return;
      node.dataset.ticked = "1";
      const target = parseFloat(m[1].replace(/,/g, ""));
      const prefix = node.textContent.trim().startsWith("+") ? "+$" : "$";
      const suffix = node.textContent.slice(node.textContent.indexOf(m[1]) + m[1].length);
      const t0 = performance.now();
      const step = (t) => {
        const k = Math.min(1, (t - t0) / 1400);
        const eased = 1 - Math.pow(1 - k, 3);
        node.textContent = prefix +
          (target * eased).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) +
          suffix;
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  async function runTour() {
    const capEl = document.querySelector("#tourCap");
    const bar = document.querySelector("#tourbar");
    if (!capEl || !bar) return;
    bar.hidden = false;
    const splash = document.querySelector("#splash");
    if (splash) {
      splash.hidden = false;
      await new Promise((r) => setTimeout(r, 3000));
      splash.classList.add("out");
      await new Promise((r) => setTimeout(r, 750));
      splash.hidden = true;
    }
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const cap = (t) => { capEl.textContent = t; };
    const firstSub = () => el.response.querySelector("[data-sub]");
    const trayBtn = (act) => el.trayBody.querySelector('[data-act="' + act + '"]');
    const waitForFree = async () => {
      for (let i = 0; i < 40 && busy; i++) await wait(250);
    };

    await waitForFree();
    cap("“Save me $800” — the audit");
    const renewalsBtn = document.querySelector('.ask[data-go="/api/renewals"]');
    if (renewalsBtn) renewalsBtn.click();
    await wait(6500);
    await waitForFree();

    cap("Stage one savings card — nothing is cancelled yet");
    const sub = firstSub();
    if (sub) sub.click();
    await wait(3000);
    await waitForFree();

    cap("One tap approves — a sealed receipt, not a silent charge");
    const approve = trayBtn("approve");
    if (approve) approve.click();
    await wait(3500);
    await waitForFree();

    cap("One tap undoes everything");
    const undo = trayBtn("undo");
    if (undo) undo.click();
    await wait(3500);
    await waitForFree();

    cap("“We are out of everything, fix groceries”");
    const grocBtn = document.querySelector('.ask[data-go="/api/commerce/autopilot-checkout"]');
    if (grocBtn) grocBtn.click();
    await wait(7000);
    await waitForFree();

    cap("The cart is staged — 5 items, 15% saved, still nothing ordered");
    const approve2 = trayBtn("approve");
    if (approve2) approve2.click();
    await wait(3500);
    await waitForFree();

    const undo2 = trayBtn("undo");
    if (undo2) undo2.click();
    await wait(3500);

    cap("Tour complete — the surface is yours. Nothing runs without your tap.");
  }

  if (new URLSearchParams(location.search).get("tour") === "1") {
    setTimeout(runTour, 1200);
  }
})();