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
    { re: /pantry|milk|coffee|restock|order|buy|grocery/i, go: "/api/acoustic/scan", body: {}, label: "Checking the pantry" },
  ];

  async function handleUtterance(phrase) {
    const hit = UTTERANCE_ROUTES.find((r) => r.re.test(phrase));
    if (!hit) {
      const msg =
        "I did not match that to a capability. Try asking about a break-in, the household parliament, a seven day forecast, selling solar, the family treaty, or the fridge.";
      el.response.textContent = msg;
      speak(msg);
      return;
    }
    await run(hit.go, hit.body, hit.label);
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
        verdictBanner("🔍", d.verdict, num(Number(d.confidence_score) * 100, 0) + "%", toneFor(d.verdict)) +
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
        name: (v.hazard_type || "").replace(/_/g, " "),
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
        tag: (c.domain || "").replace(/_/g, " "),
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
      // Recede the ambient hero so the reply owns the stage, and start the
      // reply region scrolled to the top of the new content.
      document.body.classList.add("has-result");
      el.said.parentElement.scrollTop = 0;
      speak(speechLineFor(path, data));
      el.eyebrow.textContent = label || "Result";
      await refreshTray();
    } catch (err) {
      el.response.innerHTML =
        '<span style="color:var(--e-bad)">Could not complete that: ' + esc(err.message) + "</span>";
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
      const res = await fetch("/api/audit?limit=3", { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("audit unavailable");
      setConn("ok", "connected");
    } catch (_) {
      setConn("warn", "degraded");
    }
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

  tickClock();
  setInterval(tickClock, 15000);
  setupMic();
  refreshAmbient();
  setInterval(refreshAmbient, 20000);
})();