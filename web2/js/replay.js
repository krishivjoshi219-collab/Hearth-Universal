/* Hearth Household Replay — 24h scrubber over the ledger.
   Read-only: every frame is read back from recorded events + receipts.
   Self-contained so the cockpit contract (app.js) doesn't grow. */
const $ = (sel) => document.querySelector(sel);

const panel = $("#replayPanel");
if (panel) {
  const stageEl = $("#replayStage");
  const timeEl = $("#replayTime");
  const dateEl = $("#replayDate");
  const narrationEl = $("#replayNarration");
  const chipsEl = $("#replayChips");
  const playBtn = $("#replayPlay");
  const speedsEl = $("#replaySpeeds");
  const scrubEl = $("#replayScrub");
  const markersEl = $("#replayMarkers");
  const moneyEl = $("#replayMoney");

  const SPEEDS = [
    { v: 60, label: "60×" },
    { v: 600, label: "600×" },
    { v: 3600, label: "3600×" },
  ];
  const ACTION_VIEW = {
    microgrid_dispatch_settled: ["⚡", "VPP settlement", ""],
    fft_scan_completed: ["🎧", "sonar sweep", ""],
    incident_reconstructed: ["🔍", "reconstruction", ""],
    household_treaty_synthesized: ["🏛", "treaty draft", ""],
    simulation_completed: ["🔮", "simulation", ""],
    execution_applied: ["✅", "executed", ""],
    actions_propose: ["📋", "proposal staged", ""],
    synthesis_refused_privileged: ["⚠", "Sentinel refusal", "is-alert"],
    skill_synthesized_and_mounted: ["⚒", "tool forged", "is-forge"],
    forge_tool_applied: ["🔧", "tool applied", "is-forge"],
  };

  let frames = [];
  let markers = [];
  let idx = 0;
  let speed = 3600;
  let timer = null;

  const usd = (n) => `$${Number(n || 0).toFixed(2)}`;
  const fmtDay = (f) => (f ? f.day : "the last 24 hours");

  function cumulativeMoney(upTo) {
    let earned = 0, saved = 0, spent = 0;
    for (let i = 0; i <= upTo; i++) {
      const m = frames[i].money || {};
      earned += m.earned_usd || 0;
      saved += m.saved_usd || 0;
      spent += m.spent_usd || 0;
    }
    return { earned, saved, spent, banked: earned + saved };
  }

  function paintFrame(i) {
    const f = frames[i];
    if (!f) return;
    idx = i;
    timeEl.textContent = f.label;
    dateEl.textContent = `${f.day} · ${f.events} event${f.events === 1 ? "" : "s"} recorded`;
    narrationEl.textContent = f.narration;
    chipsEl.innerHTML = "";
    const entries = Object.entries(f.by_action || {}).slice(0, 4);
    entries.forEach(([action, count]) => {
      const [icon, label, cls] = ACTION_VIEW[action] || ["•", action.replace(/_/g, " "), ""];
      const chip = document.createElement("span");
      chip.className = "replay-chip" + (cls ? " " + cls : "");
      chip.textContent = `${icon} ${count} ${label}`;
      chipsEl.appendChild(chip);
    });
    if (!entries.length) {
      const quiet = document.createElement("span");
      quiet.className = "replay-chip";
      quiet.textContent = "🌙 quiet hour";
      chipsEl.appendChild(quiet);
    }
    const cum = cumulativeMoney(i);
    moneyEl.textContent = `+${usd(cum.banked)} banked by ${f.label}`;
    scrubEl.value = String(i);
  }

  function stopPlay() {
    if (timer) clearInterval(timer);
    timer = null;
    playBtn.textContent = "▶ Play the day";
  }

  function startPlay() {
    if (timer) return stopPlay();
    if (idx >= frames.length - 1) idx = -1;
    playBtn.textContent = "⏸ Pause";
    const ms = Math.max(120, Math.round((3600 * 1000) / speed));
    timer = setInterval(() => {
      if (idx >= frames.length - 1) {
        stopPlay();
        return;
      }
      paintFrame(idx + 1);
    }, ms);
  }

  function paintSpeeds() {
    speedsEl.innerHTML = "";
    SPEEDS.forEach(({ v, label }) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "replay-speed" + (v === speed ? " is-active" : "");
      b.textContent = label;
      b.title = `a day plays back in ${Math.round((24 * 3600) / v / 60)} minute(s)`;
      b.addEventListener("click", () => {
        speed = v;
        paintSpeeds();
        if (timer) {
          stopPlay();
          startPlay();
        }
      });
      speedsEl.appendChild(b);
    });
  }

  function paintMarkers() {
    markersEl.innerHTML = "";
    markers.forEach((m) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "replay-marker" + (m.kind ? ` is-${m.kind}` : "");
      const icon = document.createElement("span");
      icon.className = "replay-marker-icon";
      icon.textContent = m.icon || "•";
      const label = document.createElement("span");
      label.textContent = m.label;
      b.append(icon, label);
      b.addEventListener("click", () => {
        stopPlay();
        paintFrame(m.frame);
        stageEl.classList.remove("is-pulse");
        void stageEl.offsetWidth;
        stageEl.classList.add("is-pulse");
        setTimeout(() => stageEl.classList.remove("is-pulse"), 1600);
      });
      markersEl.appendChild(b);
    });
  }

  playBtn.addEventListener("click", startPlay);
  scrubEl.addEventListener("input", () => {
    stopPlay();
    paintFrame(Number(scrubEl.value));
  });

  async function load() {
    try {
      const res = await fetch("/api/replay/day?hours=24");
      const data = await res.json();
      if (!data.ok || !data.frames || !data.frames.length) return;
      frames = data.frames;
      markers = data.markers || [];
      scrubEl.min = "0";
      scrubEl.max = String(frames.length - 1);
      paintSpeeds();
      paintMarkers();
      paintFrame(frames.length - 1);
    } catch {
      narrationEl.textContent = "Replay offline — the ledger could not be read.";
    }
  }

  load();
}
