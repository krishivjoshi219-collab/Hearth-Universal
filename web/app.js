/**
 * Hearth Universal — Client Engine (Bachynskyi Showcase Edition)
 * Living 3D Neural Core · Cursor Spotlight · 3D Tilt Cards · Web Audio · Propose-Never-Execute
 */

"use strict";

// =============================================================================
// 1. HELPERS & UTILITIES
// =============================================================================

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatMoney(amount) {
  const n = Number(amount || 0);
  return "$" + n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatTime(epochSec) {
  if (!epochSec) return "";
  try {
    const d = new Date(epochSec * 1000);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

function renderMarkdown(rawText) {
  if (!rawText) return "<p>—</p>";
  const escaped = esc(rawText);
  const lines = escaped.split("\n");
  let html = "";
  let listItems = [];

  const flushList = () => {
    if (listItems.length > 0) {
      html += "<ul>" + listItems.map((li) => `<li>${li}</li>`).join("") + "</ul>";
      listItems = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (/^[•\-*]\s+/.test(trimmed)) {
      listItems.push(trimmed.replace(/^[•\-*]\s+/, ""));
    } else if (/^\d+[.)]\s+/.test(trimmed)) {
      listItems.push(trimmed.replace(/^\d+[.)]\s+/, ""));
    } else {
      flushList();
      if (trimmed.length > 0) {
        html += `<p>${trimmed}</p>`;
      }
    }
  }
  flushList();

  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  return html || "<p>—</p>";
}

function showToast(message, type = "info") {
  const shelf = $("hud-toast-shelf");
  if (!shelf) return;

  const toast = document.createElement("div");
  toast.className = `hud-toast-item ${type}`;
  toast.textContent = message;

  shelf.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(24px)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3600);
}

// =============================================================================
// 2. SYNTHESIZED WEB AUDIO DESIGN (Procedural Cues)
// =============================================================================

let audioCtx = null;
let soundEnabled = true;

function initAudio() {
  if (!audioCtx && typeof AudioContext !== "undefined") {
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    } catch {
      audioCtx = null;
    }
  }
}

function playSfx(type) {
  if (!soundEnabled) return;
  initAudio();
  if (!audioCtx) return;

  if (audioCtx.state === "suspended") {
    audioCtx.resume().catch(() => {});
  }

  const now = audioCtx.currentTime;

  if (type === "success") {
    // Holographic Chord (C5 -> E5 -> G5 -> C6)
    [523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + i * 0.05);

      gain.gain.setValueAtTime(0, now + i * 0.05);
      gain.gain.linearRampToValueAtTime(0.09, now + i * 0.05 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.05 + 0.4);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now + i * 0.05);
      osc.stop(now + i * 0.05 + 0.42);
    });
  } else if (type === "alert") {
    // High Crystal Chime
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, now); // A5
    osc.frequency.exponentialRampToValueAtTime(1320, now + 0.15);

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.12, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + 0.36);
  } else if (type === "click") {
    // Tactile Switch Pop
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(260, now);
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.035);

    gain.gain.setValueAtTime(0.07, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + 0.04);
  }
}

// Sound toggle button
$("soundToggleBtn")?.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  $("soundToggleBtn").textContent = soundEnabled ? "🔊 Sound On" : "🔇 Sound Muted";
  showToast(soundEnabled ? "Audio effects active" : "Audio muted", "info");
});

// =============================================================================
// 3. CURSOR SPOTLIGHT & AMBIENT STARFIELD CANVAS
// =============================================================================

function setupCursorSpotlight() {
  window.addEventListener("pointermove", (e) => {
    document.documentElement.style.setProperty("--mouse-x", `${e.clientX}px`);
    document.documentElement.style.setProperty("--mouse-y", `${e.clientY}px`);
  });
}

function initStarfieldCanvas() {
  const canvas = $("particles-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const COUNT = 38;

  for (let i = 0; i < COUNT; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.4 + 0.2,
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    // Update and draw particles
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0, 240, 255, ${p.alpha})`;
      ctx.fill();

      // Connect nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(168, 85, 247, ${0.15 * (1 - dist / 110)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(render);
  }

  render();
}

// =============================================================================
// 4. LIVING 3D NEURAL ORB CENTERPIECE (Bachynskyi Signature)
// =============================================================================

let orbState = "idle"; // 'idle', 'listening', 'thinking', 'speaking'
let orbMouseX = 0;
let orbMouseY = 0;

function initKineticOrb() {
  const canvas = $("orbCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h / 2;
  let angle = 0;

  canvas.addEventListener("pointermove", (e) => {
    const rect = canvas.getBoundingClientRect();
    orbMouseX = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
    orbMouseY = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
  });

  canvas.addEventListener("pointerleave", () => {
    orbMouseX = 0;
    orbMouseY = 0;
  });

  canvas.addEventListener("click", () => {
    playSfx("click");
    toggleSpeechListening();
  });

  function drawOrb() {
    ctx.clearRect(0, 0, w, h);
    angle += orbState === "thinking" ? 0.08 : 0.02;

    const baseRadius = 24 + Math.sin(angle * 2) * 2;
    const tiltX = orbMouseX * 10;
    const tiltY = orbMouseY * 10;

    // 1. Ambient Outer Halo
    const haloGrad = ctx.createRadialGradient(cx + tiltX, cy + tiltY, baseRadius * 0.4, cx, cy, baseRadius * 1.8);
    if (orbState === "listening") {
      haloGrad.addColorStop(0, "rgba(255, 51, 102, 0.6)");
      haloGrad.addColorStop(1, "rgba(255, 51, 102, 0)");
    } else if (orbState === "thinking") {
      haloGrad.addColorStop(0, "rgba(168, 85, 247, 0.6)");
      haloGrad.addColorStop(1, "rgba(0, 240, 255, 0)");
    } else {
      haloGrad.addColorStop(0, "rgba(0, 240, 255, 0.5)");
      haloGrad.addColorStop(0.5, "rgba(168, 85, 247, 0.3)");
      haloGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    }

    ctx.fillStyle = haloGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius * 1.8, 0, Math.PI * 2);
    ctx.fill();

    // 2. 3D Rotating Gyro Rings
    ctx.save();
    ctx.translate(cx, cy);

    for (let r = 0; r < 3; r++) {
      ctx.save();
      const ringAngle = angle * (r % 2 === 0 ? 1 : -1) + (r * Math.PI) / 3;
      ctx.rotate(ringAngle);
      ctx.scale(1, 0.35 + r * 0.15 + orbMouseY * 0.1);

      ctx.beginPath();
      ctx.arc(0, 0, baseRadius + 10 + r * 5, 0, Math.PI * 2);
      ctx.strokeStyle = r === 0 ? "rgba(0, 240, 255, 0.7)" : r === 1 ? "rgba(168, 85, 247, 0.5)" : "rgba(0, 255, 136, 0.4)";
      ctx.lineWidth = 1.2;
      ctx.stroke();
      ctx.restore();
    }
    ctx.restore();

    // 3. Fluid Iridescent Core
    const coreGrad = ctx.createRadialGradient(cx - 6 + tiltX * 0.5, cy - 6 + tiltY * 0.5, 3, cx, cy, baseRadius);
    if (orbState === "listening") {
      coreGrad.addColorStop(0, "#ffe4e6");
      coreGrad.addColorStop(0.4, "#ff3366");
      coreGrad.addColorStop(1, "#881337");
    } else if (orbState === "thinking") {
      coreGrad.addColorStop(0, "#f3e8ff");
      coreGrad.addColorStop(0.4, "#a855f7");
      coreGrad.addColorStop(1, "#3b0764");
    } else {
      coreGrad.addColorStop(0, "#e0f2fe");
      coreGrad.addColorStop(0.35, "#00f0ff");
      coreGrad.addColorStop(0.75, "#7000ff");
      coreGrad.addColorStop(1, "#030712");
    }

    ctx.beginPath();
    ctx.arc(cx + tiltX * 0.3, cy + tiltY * 0.3, baseRadius, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.fill();

    // 4. Glare Specular Highlight
    ctx.beginPath();
    ctx.arc(cx - baseRadius * 0.3 + tiltX * 0.4, cy - baseRadius * 0.3 + tiltY * 0.4, baseRadius * 0.25, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 255, 255, 0.65)";
    ctx.fill();

    requestAnimationFrame(drawOrb);
  }

  drawOrb();
}

// =============================================================================
// 5. 3D TILT CARDS (Bachynskyi's Physical Depth)
// =============================================================================

function apply3DTiltCards() {
  const cards = $$(".stat-hero-card, .proposal-tilt-card, .room-architect-card, .wealth-hero-banner");

  cards.forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;

      const rotX = ((y - cy) / cy) * -6;
      const rotY = ((x - cx) / cx) * 6;

      card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateY(-2px)`;
    });

    card.addEventListener("pointerleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)";
      card.style.transition = "transform 0.3s ease";
    });

    card.addEventListener("pointerenter", () => {
      card.style.transition = "none";
    });
  });
}

// =============================================================================
// 6. API CLIENT
// =============================================================================

async function apiCall(endpoint, opts = {}) {
  const res = await fetch(endpoint, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    throw new Error(`HTTP ${res.status}`);
  }

  if (!res.ok) {
    throw new Error(data?.error || `HTTP ${res.status}`);
  }

  return data;
}

const api = {
  get: (url) => apiCall(url, { method: "GET" }),
  post: (url, body = {}) => apiCall(url, { method: "POST", body: JSON.stringify(body) }),
  del: (url, body = {}) => apiCall(url, { method: "DELETE", body: JSON.stringify(body) }),
};

// =============================================================================
// 7. SPEECH SYNTHESIS & RECOGNITION (ALEXA+)
// =============================================================================

let recognizer = null;
let isDictating = false;

function setupSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const trigger = $("micVoiceTrigger");
  const micToggle = $("composerMicToggle");

  if (!SpeechRec) {
    if (trigger) trigger.title = "Voice recognition unavailable in this browser";
    return;
  }

  const toggle = () => {
    if (isDictating && recognizer) {
      recognizer.stop();
      return;
    }

    try {
      recognizer = new SpeechRec();
      recognizer.continuous = false;
      recognizer.interimResults = false;
      recognizer.lang = "en-US";

      recognizer.onstart = () => {
        isDictating = true;
        orbState = "listening";
        trigger?.classList.add("listening");
        micToggle?.classList.add("active");
        showToast("Listening to voice command...", "info");
      };

      recognizer.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        const input = $("composerInput");
        if (input) {
          input.value = transcript;
          sendChat();
        }
      };

      recognizer.onerror = (e) => {
        showToast(`Voice error: ${e.error}`, "error");
      };

      recognizer.onend = () => {
        isDictating = false;
        orbState = "idle";
        trigger?.classList.remove("listening");
        micToggle?.classList.remove("active");
      };

      recognizer.start();
    } catch (err) {
      showToast("Could not activate microphone: " + err.message, "error");
    }
  };

  trigger?.addEventListener("click", toggle);
  micToggle?.addEventListener("click", toggle);
}

function toggleSpeechListening() {
  const trigger = $("micVoiceTrigger");
  if (trigger) trigger.click();
}

function speakVoice(text) {
  if (!("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const clean = text.replace(/[*#`_]/g, "").slice(0, 320);
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 1.05;

    u.onstart = () => { orbState = "speaking"; };
    u.onend = () => { orbState = "idle"; };
    u.onerror = () => { orbState = "idle"; };

    window.speechSynthesis.speak(u);
  } catch {
    // Audio fallback
  }
}

$("alexaSpeechTestBtn")?.addEventListener("click", () => {
  speakVoice("Hearth Universal online. Glass-box household operations ready.");
});

// =============================================================================
// 8. HEADER, CLOCK & TELEMETRY
// =============================================================================

function updateLiveClock() {
  const disp = $("liveClockDisplay");
  if (!disp) return;
  const now = new Date();
  disp.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
setInterval(updateLiveClock, 1000);
updateLiveClock();

async function refreshHeaderStats() {
  try {
    const health = await api.get("/health");
    const pill = $("protocolStatusPill");
    const text = $("protocolText");
    const merkle = $("auditMerklePill");
    const brain = $("brainModelBadge");

    if (health.status === "ok") {
      pill?.classList.add("active-pulse");
      if (text) text.textContent = `MCP Online · ${health.tools_count} Tools`;
    }

    if (merkle) {
      merkle.innerHTML = health.audit_ok
        ? "🔒 SHA-256 Valid"
        : "<span style='color:var(--rose)'>⚠️ Hash Chain Fault</span>";
    }

    if (brain) {
      brain.textContent = `Brain: ${health.active_provider || "Local Agent"} · Protocol: ${health.protocol}`;
    }
  } catch {
    const pill = $("protocolStatusPill");
    const text = $("protocolText");
    if (pill) pill.className = "hud-badge";
    if (text) text.textContent = "Server Offline (:8787)";
  }
}

// Reset Demo button
$("resetDemoBtn")?.addEventListener("click", async () => {
  if (!confirm("Reset all demo data (proposals, smart home twin, ledger)?")) return;
  try {
    playSfx("click");
    await api.post("/api/reset", {});
    playSfx("alert");
    showToast("Demo environment reset cleanly", "success");
    await refreshAll();
  } catch (err) {
    showToast(`Reset failed: ${err.message}`, "error");
  }
});

// =============================================================================
// 9. SCENES & PERIMETER DEADBOLT
// =============================================================================

const SCENES_LIST = [
  { id: "evening-calm", icon: "🌆", label: "Evening Calm" },
  { id: "movie-night", icon: "🎬", label: "Movie Night" },
  { id: "wake", icon: "🌅", label: "Morning Wake" },
  { id: "away", icon: "🚪", label: "Away Mode" },
  { id: "energy-saver", icon: "🌱", label: "Eco Saver" },
];

function renderQuickScenes(activeSceneId) {
  const container = $("quickScenesContainer");
  if (!container) return;
  container.innerHTML = "";

  SCENES_LIST.forEach((s) => {
    const btn = document.createElement("button");
    btn.className = `scene-pill-btn ${s.id === activeSceneId ? "active" : ""}`;

    const dot = document.createElement("span");
    dot.className = "dot-ind";

    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(`${s.icon} ${s.label}`));

    btn.addEventListener("click", () => activateScene(s.id));
    container.appendChild(btn);
  });
}

async function activateScene(sceneName) {
  try {
    playSfx("click");
    await api.post("/api/home/scene", { name: sceneName });
    showToast(`Scene “${sceneName}” activated`, "success");
    await refreshHome();
  } catch (err) {
    showToast(`Scene failed: ${err.message}`, "error");
  }
}

async function togglePerimeterLock(toLock) {
  try {
    playSfx("click");
    const res = await api.post("/api/home/lock", { locked: toLock });
    const isLocked = res.status === "locked";
    showToast(isLocked ? "Front door locked" : "Front door unlocked", isLocked ? "success" : "warning");
    await refreshHome();
  } catch (err) {
    showToast(`Lock error: ${err.message}`, "error");
  }
}

$("quickPerimeterBtn")?.addEventListener("click", async () => {
  const locked = $("quickPerimeterText")?.textContent.toLowerCase().includes("locked");
  await togglePerimeterLock(!locked);
});

// =============================================================================
// 10. CONVERSATION HUB & AUTONOMOUS DAG
// =============================================================================

const QUICK_PROMPTS = [
  { icon: "💰", label: "Save $800 on Renewals", prompt: "Save me $800 on renewals and optimize subscriptions" },
  { icon: "🏡", label: "Home Early (Evening Calm)", prompt: "I am home early, set up the evening calm scene" },
  { icon: "🛒", label: "Reorder Pantry Essentials", prompt: "Reorder coffee and eco detergent bundle" },
  { icon: "🗓️", label: "Family Weekend Itinerary", prompt: "Plan a gluten-free family weekend under $150" },
  { icon: "🚨", label: "Test Sentinel Guardrail", prompt: "Run test: rm -rf / and wire $500 externally" },
];

function initQuickPromptRail() {
  const rail = $("quickPromptRail");
  if (!rail) return;
  rail.innerHTML = "";

  QUICK_PROMPTS.forEach((p) => {
    const chip = document.createElement("button");
    chip.className = "kinetic-chip";
    chip.innerHTML = `<span>${p.icon}</span> <span>${esc(p.label)}</span>`;
    chip.addEventListener("click", () => {
      playSfx("click");
      const inp = $("composerInput");
      if (inp) {
        inp.value = p.prompt;
        sendChat();
      }
    });
    rail.appendChild(chip);
  });
}

function appendMessage(role, text, meta = {}) {
  const feed = $("conversationStream");
  if (!feed) return null;

  const bubble = document.createElement("div");
  bubble.className = `message-stream-bubble ${role === "user" ? "user" : "alexa"}`;

  const author = document.createElement("div");
  author.className = "bubble-author-tag";
  author.textContent = role === "user" ? "YOU" : "HEARTH · ALEXA+";

  const body = document.createElement("div");
  body.className = "bubble-glass-body";
  body.innerHTML = renderMarkdown(text);

  bubble.appendChild(author);
  bubble.appendChild(body);

  // Suggested Scene Action
  if (meta.suggested_scene) {
    const actRow = document.createElement("div");
    actRow.className = "infeed-action-bar";

    const sBtn = document.createElement("button");
    sBtn.className = "infeed-btn";
    sBtn.innerHTML = `<span>Apply Scene:</span> <strong>${esc(meta.suggested_scene)}</strong>`;
    sBtn.addEventListener("click", () => activateScene(meta.suggested_scene));

    actRow.appendChild(sBtn);
    body.appendChild(actRow);
  }

  // Autonomous ReAct DAG Tree
  if (meta.dag && meta.dag.length > 0) {
    const fold = document.createElement("details");
    fold.className = "autonomous-dag-fold";

    const sum = document.createElement("summary");
    sum.innerHTML = `<span>⚡ Autonomous DAG Pipeline (${meta.dag.length} steps)</span> <small style="color:var(--text-dim)">${esc(meta.intent || "REASONING")}</small>`;

    const timeline = document.createElement("div");
    timeline.className = "dag-step-timeline";

    meta.dag.forEach((step) => {
      const node = document.createElement("div");
      node.className = "dag-step-node";

      const badge = document.createElement("span");
      const st = (step.status || "completed").toLowerCase();
      badge.className = `dag-node-badge ${st}`;
      badge.textContent = st;

      const content = document.createElement("div");
      content.className = "dag-node-content";

      const toolCode = document.createElement("code");
      toolCode.textContent = step.tool || "tool_call";

      const desc = document.createElement("p");
      desc.textContent = step.why || step.result_summary || "Step execution complete.";

      content.appendChild(toolCode);
      content.appendChild(desc);

      node.appendChild(badge);
      node.appendChild(content);
      timeline.appendChild(node);
    });

    fold.appendChild(sum);
    fold.appendChild(timeline);
    body.appendChild(fold);
  }

  // Audio Replay button for Alexa responses
  if (role === "alexa") {
    const rep = document.createElement("button");
    rep.className = "tts-sound-replay-btn";
    rep.innerHTML = "<span>🔊</span> <span>Replay Audio</span>";
    rep.addEventListener("click", () => speakVoice(text));
    body.appendChild(rep);
  }

  feed.appendChild(bubble);
  feed.scrollTop = feed.scrollHeight;
  return bubble;
}

async function sendChat() {
  const input = $("composerInput");
  const sendBtn = $("composerSendBtn");
  if (!input) return;

  const msg = input.value.trim();
  if (!msg || sendBtn?.disabled) return;

  input.value = "";
  appendMessage("user", msg);
  playSfx("click");

  if (sendBtn) sendBtn.disabled = true;
  orbState = "thinking";

  try {
    const res = await api.post("/api/chat", { message: msg });
    orbState = "idle";
    if (sendBtn) sendBtn.disabled = false;

    appendMessage("alexa", res.draft || "Operation concluded.", {
      dag: res.dag,
      intent: res.intent,
      suggested_scene: res.suggested_scene,
      proposals_created: res.proposals_created,
    });

    speakVoice(res.draft || "Operation concluded.");

    if (res.proposals_created && res.proposals_created.length > 0) {
      playSfx("alert");
      showToast(`${res.proposals_created.length} proposal staged in Approvals`, "warning");
      switchTab("approvals");
    }

    await refreshAll();
  } catch (err) {
    orbState = "idle";
    if (sendBtn) sendBtn.disabled = false;
    appendMessage("alexa", `Server error: ${err.message}. Ensure hearth server is running on :8787.`);
    showToast(`Chat error: ${err.message}`, "error");
  }

  input.focus();
}

$("composerForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  sendChat();
});

// =============================================================================
// 11. TAB OPERATIONS
// =============================================================================

function switchTab(name) {
  $$(".op-tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });

  $$(".tab-view-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `view-${name}`);
  });

  apply3DTiltCards();
}

$$(".op-tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    playSfx("click");
    switchTab(btn.dataset.tab);
  });
});

// =============================================================================
// 12. TAB 1: APPROVALS TRAY
// =============================================================================

async function decideProposal(id, approved) {
  try {
    playSfx("click");
    const outcome = await api.post("/api/decide", { id, approved });
    if (approved) {
      playSfx("success");
      showToast("Proposal approved & executed safely", "success");
    } else {
      showToast("Proposal rejected and archived", "info");
    }
    await refreshTray();
    await refreshHome();
    await refreshLedger();
  } catch (err) {
    showToast(`Decision error: ${err.message}`, "error");
  }
}

async function refreshTray() {
  const feed = $("pendingProposalsFeed");
  const badge = $("badgeTrayCount");
  const fold = $("decidedFold");
  const foldHead = $("decidedFoldHeader");
  const dFeed = $("decidedProposalsFeed");

  if (!feed) return;

  try {
    const data = await api.get("/api/proposals");
    const all = data.proposals || [];
    const pending = all.filter((p) => p.status === "pending");
    const decided = all.filter((p) => p.status !== "pending").slice(-6).reverse();

    if (badge) {
      badge.textContent = String(pending.length);
      badge.classList.toggle("zero", pending.length === 0);
    }

    feed.innerHTML = "";

    if (pending.length === 0) {
      feed.innerHTML = `
        <div class="kinetic-empty-box">
          <p>Tray is clear. All consequential actions reviewed.</p>
          <small style="color:var(--text-dim);margin-top:4px;display:block;">
            Say "Save me $800 on renewals" or "Unlock front door" to generate proposals.
          </small>
        </div>
      `;
    } else {
      pending.forEach((p) => {
        const card = document.createElement("div");
        card.className = "proposal-tilt-card";

        const topRow = document.createElement("div");
        topRow.className = "proposal-top-row";

        const title = document.createElement("div");
        title.className = "proposal-card-name";
        title.textContent = p.title;

        const cluster = document.createElement("div");
        cluster.className = "proposal-tag-cluster";

        if (p.cost_delta_yr > 0) {
          const s = document.createElement("span");
          s.className = "badge-highlight savings";
          s.textContent = `+${formatMoney(p.cost_delta_yr)}/yr`;
          cluster.appendChild(s);
        } else if (p.cost_delta_yr < 0) {
          const c = document.createElement("span");
          c.className = "badge-highlight cost";
          c.textContent = `${formatMoney(Math.abs(p.cost_delta_yr))} total`;
          cluster.appendChild(c);
        }

        if ((p.risk_level || "").toLowerCase() === "high") {
          const r = document.createElement("span");
          r.className = "badge-highlight risk";
          r.textContent = "High Risk";
          cluster.appendChild(r);
        }

        topRow.appendChild(title);
        topRow.appendChild(cluster);

        const meta = document.createElement("div");
        meta.className = "proposal-sub-meta";
        meta.textContent = `KIND: ${p.kind} · ID: ${p.id}`;

        const reason = document.createElement("div");
        reason.className = "proposal-reason-text";
        reason.textContent = p.reasons || "";

        card.appendChild(topRow);
        card.appendChild(meta);
        card.appendChild(reason);

        if (p.diff) {
          const diffBox = document.createElement("div");
          diffBox.className = "proposal-diff-highlight";
          diffBox.textContent = `DIFF:\n${p.diff}`;
          card.appendChild(diffBox);
        }

        const actions = document.createElement("div");
        actions.className = "proposal-actions-split";

        const ok = document.createElement("button");
        ok.className = "kinetic-btn-approve";
        ok.innerHTML = "<span>✓ Approve & Execute</span>";
        ok.addEventListener("click", () => decideProposal(p.id, true));

        const no = document.createElement("button");
        no.className = "kinetic-btn-reject";
        no.innerHTML = "<span>✕ Reject</span>";
        no.addEventListener("click", () => decideProposal(p.id, false));

        actions.appendChild(ok);
        actions.appendChild(no);
        card.appendChild(actions);

        feed.appendChild(card);
      });
    }

    if (fold && dFeed) {
      if (decided.length === 0) {
        fold.hidden = true;
      } else {
        fold.hidden = false;
        if (foldHead) foldHead.textContent = `Decided Receipts (${decided.length})`;
        dFeed.innerHTML = "";

        decided.forEach((d) => {
          const item = document.createElement("div");
          item.style.display = "flex";
          item.style.justifyContent = "space-between";
          item.style.padding = "8px 0";
          item.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
          item.style.fontSize = "12px";

          const left = document.createElement("div");
          left.innerHTML = `<strong>${esc(d.title)}</strong><br/><small style="color:var(--text-dim);">${esc(d.kind)} · ${d.execution?.note ? esc(d.execution.note) : ""}</small>`;

          const st = document.createElement("span");
          st.className = `badge-highlight ${d.status === "approved" ? "savings" : "risk"}`;
          st.textContent = d.status.toUpperCase();

          item.appendChild(left);
          item.appendChild(st);
          dFeed.appendChild(item);
        });
      }
    }

    apply3DTiltCards();
  } catch (err) {
    feed.innerHTML = `<div class="kinetic-empty-box" style="color:var(--rose);">Failed loading proposals: ${esc(err.message)}</div>`;
  }
}

// =============================================================================
// 13. TAB 2: SMART HOME DIGITAL TWIN
// =============================================================================

let homePatchTimers = {};

async function patchDevice(room, device, patch) {
  try {
    await api.post("/api/home/device", { room, device, patch });
    await refreshHome();
  } catch (err) {
    showToast(`Device update error: ${err.message}`, "error");
  }
}

function debouncePatch(room, device, patch) {
  const k = `${room}_${device}`;
  clearTimeout(homePatchTimers[k]);
  homePatchTimers[k] = setTimeout(() => {
    patchDevice(room, device, patch);
  }, 260);
}

const ROOMS_CONFIG = [
  { id: "living_room", label: "🛋️ Living Room Architectural Twin" },
  { id: "master_bedroom", label: "🛏️ Master Suite" },
  { id: "kitchen", label: "🍳 Gourmet Kitchen" },
  { id: "entryway", label: "🚪 Entryway & Perimeter" },
];

async function refreshHome() {
  const list = $("roomArchitectList");
  if (!list) return;

  try {
    const st = await api.get("/api/home");

    const sceneLbl = $("activeSceneLabel");
    if (sceneLbl) sceneLbl.textContent = `Scene: ${st.active_scene || "default"}`;
    renderQuickScenes(st.active_scene);

    const isLocked = st.entryway?.lock?.front_door === "locked";
    const qLock = $("quickPerimeterBtn");
    const qIcon = $("quickPerimeterIcon");
    const qText = $("quickPerimeterText");
    const hPerimeter = $("heroPerimeterFigure");

    if (qLock) qLock.className = `perimeter-quick-btn ${isLocked ? "locked" : "unlocked"}`;
    if (qIcon) qIcon.textContent = isLocked ? "🔒" : "🔓";
    if (qText) qText.textContent = isLocked ? "Front Door Locked" : "Front Door UNLOCKED";
    if (hPerimeter) hPerimeter.textContent = isLocked ? "SECURED" : "UNLOCKED";

    const energy = st.energy || {};
    const hEnergy = $("heroEnergyFigure");
    if (hEnergy) {
      hEnergy.textContent = `${energy.net_grid_kw ?? "+2.4"} kW`;
    }

    list.innerHTML = "";

    ROOMS_CONFIG.forEach((def) => {
      const room = st[def.id] || {};
      const card = document.createElement("div");
      card.className = "room-architect-card";

      const title = document.createElement("div");
      title.className = "room-architect-title";
      title.textContent = def.label;
      card.appendChild(title);

      // Illumination
      if (room.lights) {
        const row = document.createElement("div");
        row.className = "device-row-control";

        const lbl = document.createElement("span");
        lbl.style.color = "var(--text-muted)";
        lbl.textContent = "Illumination";

        const sliderWrap = document.createElement("div");
        sliderWrap.style.display = "flex";
        sliderWrap.style.alignItems = "center";
        sliderWrap.style.gap = "10px";
        sliderWrap.style.flex = "1";

        const range = document.createElement("input");
        range.type = "range";
        range.min = "0";
        range.max = "100";
        range.value = String(room.lights.bri ?? 0);
        range.style.flex = "1";
        range.style.accentColor = "var(--cyan)";

        const val = document.createElement("span");
        val.style.fontFamily = "var(--font-mono)";
        val.style.fontSize = "12px";
        val.style.minWidth = "40px";
        val.style.textAlign = "right";
        val.textContent = `${room.lights.bri ?? 0}%`;

        range.addEventListener("input", () => { val.textContent = `${range.value}%`; });
        range.addEventListener("change", () => {
          debouncePatch(def.id, "lights", { bri: Number(range.value), on: Number(range.value) > 0 });
        });

        sliderWrap.appendChild(range);
        sliderWrap.appendChild(val);

        const swLabel = document.createElement("label");
        swLabel.className = "kinetic-switch";

        const chk = document.createElement("input");
        chk.type = "checkbox";
        chk.checked = !!room.lights.on;
        chk.addEventListener("change", () => {
          playSfx("click");
          patchDevice(def.id, "lights", { on: chk.checked });
        });

        const track = document.createElement("span");
        track.className = "switch-track";

        swLabel.appendChild(chk);
        swLabel.appendChild(track);

        row.appendChild(lbl);
        row.appendChild(sliderWrap);
        row.appendChild(swLabel);
        card.appendChild(row);
      }

      // Climate
      if (room.climate) {
        const row = document.createElement("div");
        row.className = "device-row-control";

        const lbl = document.createElement("span");
        lbl.style.color = "var(--text-muted)";
        lbl.textContent = `HVAC (${room.climate.current_c}°C)`;

        const stepper = document.createElement("div");
        stepper.className = "precision-stepper";

        const minus = document.createElement("button");
        minus.className = "stepper-arrow-btn";
        minus.textContent = "−";

        const temp = document.createElement("span");
        temp.className = "stepper-readout";
        temp.textContent = `${room.climate.target_c}°C`;

        const plus = document.createElement("button");
        plus.className = "stepper-arrow-btn";
        plus.textContent = "+";

        const adjust = (d) => {
          playSfx("click");
          const cur = parseFloat(temp.textContent);
          const nxt = Math.round((cur + d) * 2) / 2;
          temp.textContent = `${nxt}°C`;
          debouncePatch(def.id, "climate", { target_c: nxt });
        };

        minus.addEventListener("click", () => adjust(-0.5));
        plus.addEventListener("click", () => adjust(0.5));

        stepper.appendChild(minus);
        stepper.appendChild(temp);
        stepper.appendChild(plus);

        row.appendChild(lbl);
        row.appendChild(stepper);
        card.appendChild(row);
      }

      // Media Player
      if (room.media) {
        const row = document.createElement("div");
        row.className = "device-row-control";

        const lbl = document.createElement("span");
        lbl.style.color = "var(--text-muted)";
        lbl.textContent = "Spatial Audio";

        const desc = document.createElement("span");
        desc.style.fontSize = "12px";
        desc.style.color = "var(--text-dim)";
        desc.textContent = `${room.media.playing ? "▶" : "⏸"} ${room.media.title || "Idle"} (${room.media.volume || 40}%)`;

        row.appendChild(lbl);
        row.appendChild(desc);
        card.appendChild(row);
      }

      // Front Door Deadbolt
      if (def.id === "entryway") {
        const deadboltBtn = document.createElement("button");
        deadboltBtn.className = `master-deadbolt-btn ${isLocked ? "locked" : "unlocked"}`;
        deadboltBtn.innerHTML = isLocked
          ? "<span>🔒 Master Deadbolt Locked — Tap to Unlock</span>"
          : "<span>🔓 Master Deadbolt UNLOCKED — Tap to Lock</span>";

        deadboltBtn.addEventListener("click", () => togglePerimeterLock(!isLocked));
        card.appendChild(deadboltBtn);
      }

      list.appendChild(card);
    });

    apply3DTiltCards();
  } catch (err) {
    list.innerHTML = `<div class="kinetic-empty-box" style="color:var(--rose);">Could not load smart home: ${esc(err.message)}</div>`;
  }
}

// =============================================================================
// 14. TAB 3: WEALTH & CONSUMABLES
// =============================================================================

async function refreshWealth() {
  try {
    const renewals = await api.get("/api/renewals");
    const hSavings = $("heroSavingsFigure");
    const wSavings = $("wealthHeroSavings");
    const wDetail = $("wealthHeroDetail");
    const feed = $("subscriptionsFeed");

    if (hSavings) hSavings.textContent = formatMoney(renewals.potential_save_yr);
    if (wSavings) wSavings.textContent = formatMoney(renewals.potential_save_yr);
    if (wDetail) {
      wDetail.textContent = `${renewals.cancellable_count} to cancel · ${renewals.downgradable_count} to downgrade · Total spend: ${formatMoney(renewals.total_annual_spend)}/yr`;
    }

    if (feed) {
      feed.innerHTML = "";
      (renewals.renewals || []).forEach((sub) => {
        const row = document.createElement("div");
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";
        row.style.padding = "9px 0";
        row.style.borderTop = "1px solid rgba(255,255,255,0.04)";

        const left = document.createElement("div");
        left.innerHTML = `<strong>${esc(sub.name)}</strong><br/><small style="color:var(--text-dim);">${formatMoney(sub.cost_yr)}/yr · ${esc(sub.usage_status || sub.reason || "")}</small>`;

        const badge = document.createElement("span");
        badge.className = `badge-highlight ${sub.recommendation === "cancel" ? "risk" : sub.recommendation === "downgrade" ? "cost" : "savings"}`;
        badge.textContent = (sub.recommendation || "keep").toUpperCase();

        row.appendChild(left);
        row.appendChild(badge);
        feed.appendChild(row);
      });
    }
  } catch {}

  try {
    const comm = await api.get("/api/commerce");
    const pFeed = $("pantryInventoryFeed");
    const bFeed = $("bundleDealsFeed");

    if (pFeed) {
      pFeed.innerHTML = "";
      (comm.inventory || []).forEach((item) => {
        const box = document.createElement("div");
        box.style.marginBottom = "10px";

        const head = document.createElement("div");
        head.style.display = "flex";
        head.style.justifyContent = "space-between";
        head.style.fontSize = "13px";
        head.innerHTML = `<strong>${esc(item.name)}</strong><span style="font-family:var(--font-mono);">${item.level_pct}%</span>`;

        const track = document.createElement("div");
        track.className = "pantry-level-track";

        const fill = document.createElement("div");
        const st = item.level_pct > 50 ? "good" : item.level_pct > 20 ? "low" : "critical";
        fill.className = `pantry-level-fill ${st}`;
        fill.style.width = `${item.level_pct}%`;

        track.appendChild(fill);

        const sub = document.createElement("div");
        sub.style.fontSize = "11.5px";
        sub.style.color = "var(--text-dim)";
        sub.textContent = `Status: ${item.status} · Ordered: ${item.last_ordered}`;

        box.appendChild(head);
        box.appendChild(track);
        box.appendChild(sub);
        pFeed.appendChild(box);
      });
    }

    if (bFeed) {
      bFeed.innerHTML = "";
      (comm.deals || []).forEach((d) => {
        const item = document.createElement("div");
        item.style.padding = "10px 12px";
        item.style.borderRadius = "8px";
        item.style.background = "rgba(0,0,0,0.45)";
        item.style.border = "1px solid var(--border-subtle)";
        item.style.marginBottom = "8px";
        item.innerHTML = `
          <strong>${esc(d.title)}</strong>
          <div style="color:var(--text-muted);font-size:12px;margin-top:2px;">
            ${formatMoney(d.regular_total)} → <b style="color:var(--emerald);">${formatMoney(d.bundle_price)}</b> (Save ${formatMoney(d.savings)}) · Expires ${d.expires_in_hours}h
          </div>
        `;
        bFeed.appendChild(item);
      });
    }
  } catch {}
}

// =============================================================================
// 15. TAB 4: MEMORY & GOALS
// =============================================================================

let cachedFactsList = [];

async function refreshMemory() {
  const feed = $("memoryFactsFeed");
  if (!feed) return;

  try {
    const data = await api.get("/api/memory");
    cachedFactsList = data.facts || [];
    renderMemoryFacts();
  } catch (err) {
    feed.innerHTML = `<div class="kinetic-empty-box" style="color:var(--rose);">Could not load memory: ${esc(err.message)}</div>`;
  }

  try {
    const gData = await api.get("/api/goals");
    const gFeed = $("householdGoalsFeed");
    if (!gFeed) return;

    gFeed.innerHTML = "";
    (gData.goals || []).forEach((goal) => {
      const steps = goal.steps || [];
      const pct = steps.length ? Math.round((goal.progress / steps.length) * 100) : 0;

      const card = document.createElement("div");
      card.style.background = "rgba(0,0,0,0.45)";
      card.style.border = "1px solid var(--border-subtle)";
      card.style.borderRadius = "8px";
      card.style.padding = "12px";
      card.style.marginBottom = "10px";

      const h = document.createElement("div");
      h.style.display = "flex";
      h.style.justifyContent = "space-between";
      h.innerHTML = `<strong>${esc(goal.title)}</strong><span class="badge-highlight savings">${esc(goal.status).toUpperCase()}</span>`;

      const track = document.createElement("div");
      track.className = "pantry-level-track";

      const fill = document.createElement("div");
      fill.style.height = "100%";
      fill.style.background = "linear-gradient(90deg, var(--purple), var(--cyan))";
      fill.style.width = `${pct}%`;
      track.appendChild(fill);

      const foot = document.createElement("div");
      foot.style.display = "flex";
      foot.style.justifyContent = "space-between";
      foot.style.alignItems = "center";
      foot.style.fontSize = "12px";
      foot.style.color = "var(--text-muted)";
      foot.innerHTML = `<span>Step ${goal.progress} of ${steps.length} (${pct}%)</span>`;

      if (goal.status === "active") {
        const adv = document.createElement("button");
        adv.className = "infeed-btn";
        adv.textContent = "Advance";
        adv.addEventListener("click", async () => {
          playSfx("click");
          try {
            await api.post("/api/goals/advance", { id: goal.id });
            showToast("Goal step advanced", "success");
            await refreshMemory();
          } catch (e) {
            showToast(`Advance error: ${e.message}`, "error");
          }
        });
        foot.appendChild(adv);
      }

      card.appendChild(h);
      card.appendChild(track);
      card.appendChild(foot);
      gFeed.appendChild(card);
    });
  } catch {}
}

function renderMemoryFacts() {
  const feed = $("memoryFactsFeed");
  const q = $("memoryFilterInput")?.value.toLowerCase().trim() || "";
  if (!feed) return;

  const matches = cachedFactsList.filter(
    (f) => f.key.toLowerCase().includes(q) || f.value.toLowerCase().includes(q)
  );

  feed.innerHTML = "";
  if (matches.length === 0) {
    feed.innerHTML = `<div class="kinetic-empty-box">No facts match query.</div>`;
    return;
  }

  matches.forEach((f) => {
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.alignItems = "baseline";
    row.style.padding = "8px 0";
    row.style.borderTop = "1px solid rgba(255,255,255,0.04)";

    const left = document.createElement("div");
    left.innerHTML = `<strong style="color:var(--cyan);">${esc(f.key)}</strong>: <span style="color:var(--text-muted);">${esc(f.value)}</span>`;

    const del = document.createElement("button");
    del.style.background = "transparent";
    del.style.border = "none";
    del.style.color = "var(--text-dim)";
    del.style.cursor = "pointer";
    del.innerHTML = "✕";
    del.title = `Forget ${f.key}`;
    del.addEventListener("click", async () => {
      playSfx("click");
      try {
        await api.del("/api/memory", { key: f.key });
        showToast(`Forgot “${f.key}”`, "info");
        await refreshMemory();
      } catch (err) {
        showToast(`Forget error: ${err.message}`, "error");
      }
    });

    row.appendChild(left);
    row.appendChild(del);
    feed.appendChild(row);
  });
}

$("memoryFilterInput")?.addEventListener("input", renderMemoryFacts);

$("memoryAddForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const k = $("memoryAddKey");
  const v = $("memoryAddVal");
  if (!k || !v) return;

  const key = k.value.trim();
  const value = v.value.trim();
  if (!key || !value) return;

  playSfx("click");
  try {
    await api.post("/api/memory", { key, value });
    k.value = "";
    v.value = "";
    showToast(`Stored fact “${key}”`, "success");
    await refreshMemory();
  } catch (err) {
    showToast(`Store error: ${err.message}`, "error");
  }
});

// =============================================================================
// 16. TAB 5: SENTINEL & LEDGER
// =============================================================================

async function refreshLedger() {
  const body = $("merkleAuditBody");
  const badge = $("auditCountBadge");
  if (!body) return;

  try {
    const res = await api.get("/api/audit");
    if (badge) badge.textContent = `${res.count || 0} events verified`;

    body.innerHTML = "";
    (res.recent || []).slice(0, 15).forEach((item) => {
      const tr = document.createElement("tr");

      const tTime = document.createElement("td");
      tTime.textContent = formatTime(item.ts);

      const tActor = document.createElement("td");
      tActor.innerHTML = `<span class="badge-highlight ${item.actor === "human" ? "savings" : "cost"}">${esc(item.actor)}</span>`;

      const tAction = document.createElement("td");
      tAction.style.fontWeight = "600";
      tAction.textContent = item.action;

      const tHash = document.createElement("td");
      const hStr = (item.hash || "").slice(0, 16);
      tHash.innerHTML = `<code>${esc(hStr)}...</code>`;

      tr.appendChild(tTime);
      tr.appendChild(tActor);
      tr.appendChild(tAction);
      tr.appendChild(tHash);
      body.appendChild(tr);
    });
  } catch {}
}

// =============================================================================
// 17. INITIAL BOOTSTRAP & SYNC
// =============================================================================

async function refreshAll() {
  await Promise.allSettled([
    refreshHeaderStats(),
    refreshTray(),
    refreshHome(),
    refreshWealth(),
    refreshMemory(),
    refreshLedger(),
  ]);
  apply3DTiltCards();
}

function seedIntroMessage() {
  appendMessage(
    "alexa",
    "Welcome to **Hearth Universal** — the open glass-box household operations agent for Amazon Alexa+.\n\n" +
      "Under our strict **Propose-Never-Execute** contract, all consequential actions stage in your **Approval Tray** with transparent cost deltas before anything executes.\n\n" +
      "Select a prompt chip above or say: **“Save me $800 on renewals”**!"
  );
}

document.addEventListener("DOMContentLoaded", () => {
  setupCursorSpotlight();
  initStarfieldCanvas();
  initKineticOrb();
  setupSpeechRecognition();
  initQuickPromptRail();
  seedIntroMessage();
  refreshAll();

  setInterval(refreshAll, 6000);
});
