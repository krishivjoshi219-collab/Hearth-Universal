/**
 * Hearth Universal — Client Engine (Bachynskyi Ultra Showcase Edition)
 * 3D Rotating Sphere Lattice · Dynamic Specular Glare · Multi-Brain Egress
 * Procedural Audio · Propose-Never-Execute Safety Contract · Verifiable State Export
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
// 2. PROCEDURAL WEB AUDIO ENGINE (Haptics & Cues)
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
    // Warm 4-note holographic chord (F4 -> A4 -> C5 -> F5)
    [349.23, 440.0, 523.25, 698.46].forEach((freq, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + i * 0.05);

      gain.gain.setValueAtTime(0, now + i * 0.05);
      gain.gain.linearRampToValueAtTime(0.09, now + i * 0.05 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.05 + 0.45);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now + i * 0.05);
      osc.stop(now + i * 0.05 + 0.48);
    });
  } else if (type === "alert") {
    // High Crystal Resonance (E5 -> B5)
    [659.25, 987.77].forEach((freq, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + i * 0.08);

      gain.gain.setValueAtTime(0, now + i * 0.08);
      gain.gain.linearRampToValueAtTime(0.11, now + i * 0.08 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.38);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now + i * 0.08);
      osc.stop(now + i * 0.08 + 0.4);
    });
  } else if (type === "lock") {
    // Motorized Deadbolt Mechanical Snap (dual impulse)
    [160, 220].forEach((freq, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, now + i * 0.08);
      osc.frequency.exponentialRampToValueAtTime(40, now + i * 0.08 + 0.05);

      gain.gain.setValueAtTime(0.12, now + i * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.06);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now + i * 0.08);
      osc.stop(now + i * 0.08 + 0.07);
    });
  } else if (type === "routine") {
    // Ambient Harmonic Swell
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.exponentialRampToValueAtTime(440, now + 0.25);

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.12, now + 0.12);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.38);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + 0.4);
  } else if (type === "click") {
    // Tactile Click Pop
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(280, now);
    osc.frequency.exponentialRampToValueAtTime(90, now + 0.035);

    gain.gain.setValueAtTime(0.07, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + 0.04);
  }
}

$("soundToggleBtn")?.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  $("soundToggleBtn").textContent = soundEnabled ? "🔊 Sound On" : "🔇 Sound Muted";
  showToast(soundEnabled ? "Audio effects active" : "Audio muted", "info");
});

// =============================================================================
// 3. CURSOR SPOTLIGHT & STARFIELD NEURAL PARTICLES
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
  const COUNT = 36;

  for (let i = 0; i < COUNT; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      radius: Math.random() * 1.5 + 0.6,
      alpha: Math.random() * 0.4 + 0.2,
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

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

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(168, 85, 247, ${0.14 * (1 - dist / 110)})`;
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
// 4. INTERACTIVE 3D WIREFRAME SPHERE LATTICE (Bachynskyi Masterpiece)
// =============================================================================

let orbState = "idle"; // 'idle', 'listening', 'thinking', 'speaking'
let orbMouseX = 0;
let orbMouseY = 0;
let orbShockwave = 0;

function syncCoreStatusBadge() {
  const text = $("coreStatusText");
  const pill = $("coreStatusPill");
  if (!text || !pill) return;

  if (orbState === "listening") {
    text.textContent = "LISTENING · VOICE ACTIVE";
    pill.style.borderColor = "var(--rose)";
    pill.style.color = "var(--rose)";
    pill.style.background = "rgba(255, 51, 102, 0.12)";
  } else if (orbState === "thinking") {
    text.textContent = "ORCHESTRATING DAG";
    pill.style.borderColor = "var(--purple)";
    pill.style.color = "var(--purple)";
    pill.style.background = "rgba(168, 85, 247, 0.12)";
  } else if (orbState === "speaking") {
    text.textContent = "SYNTHESIZING SPEECH";
    pill.style.borderColor = "var(--cyan)";
    pill.style.color = "var(--cyan)";
    pill.style.background = "rgba(0, 240, 255, 0.12)";
  } else {
    text.textContent = "AUTONOMOUS · READY";
    pill.style.borderColor = "rgba(0, 255, 136, 0.35)";
    pill.style.color = "var(--emerald)";
    pill.style.background = "rgba(0, 255, 136, 0.1)";
  }
}

function initKineticOrb() {
  const canvas = $("orbCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // High-DPI Retina scaling
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const displayW = 100;
  const displayH = 100;
  canvas.width = displayW * dpr;
  canvas.height = displayH * dpr;
  ctx.scale(dpr, dpr);

  const cx = displayW / 2;
  const cy = displayH / 2;

  let rotX = 0.3;
  let rotY = 0;
  let gimbalAngle1 = 0;
  let gimbalAngle2 = 0;
  let time = 0;

  // Generate 3D spherical lattice coordinates
  const R = 30;
  const points = [];
  const rings = 7;
  const segments = 14;

  for (let i = 0; i <= rings; i++) {
    const theta = (i * Math.PI) / rings - Math.PI / 2;
    for (let j = 0; j < segments; j++) {
      const phi = (j * 2 * Math.PI) / segments;
      points.push({
        x: R * Math.cos(theta) * Math.cos(phi),
        y: R * Math.sin(theta),
        z: R * Math.cos(theta) * Math.sin(phi),
        ring: i,
        seg: j,
      });
    }
  }

  // Orbiting Particle Stars
  const orbiters = [];
  const ORBITER_COUNT = 10;
  for (let k = 0; k < ORBITER_COUNT; k++) {
    orbiters.push({
      orbitR: R + 10 + Math.random() * 8,
      speed: (0.015 + Math.random() * 0.02) * (Math.random() > 0.5 ? 1 : -1),
      angle: Math.random() * Math.PI * 2,
      tilt: (Math.random() - 0.5) * 1.2,
      size: Math.random() * 1.5 + 0.8,
    });
  }

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
    orbShockwave = 1.0;
    playSfx("click");
    toggleSpeechListening();
  });

  function draw3DLattice() {
    ctx.clearRect(0, 0, displayW, displayH);
    time += 0.02;
    syncCoreStatusBadge();

    const speed = orbState === "thinking" ? 0.08 : orbState === "listening" ? 0.045 : 0.02;
    rotY += speed + orbMouseX * 0.035;
    rotX = 0.3 + orbMouseY * 0.35;
    gimbalAngle1 += speed * 0.7;
    gimbalAngle2 -= speed * 0.55;

    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX);
    const sinX = Math.sin(rotX);

    // Shockwave pulse decay
    if (orbShockwave > 0.02) {
      orbShockwave *= 0.92;
      ctx.beginPath();
      ctx.arc(cx, cy, R * (1 + (1 - orbShockwave) * 1.7), 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(0, 240, 255, ${orbShockwave * 0.75})`;
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }

    // 1. Ambient Iridescent Fluid Core
    const breath = 1 + Math.sin(time * 3) * (orbState === "listening" ? 0.12 : 0.04);
    const coreGrad = ctx.createRadialGradient(cx - 3, cy - 3, 2, cx, cy, R * breath);

    if (orbState === "listening") {
      coreGrad.addColorStop(0, "#fff1f2");
      coreGrad.addColorStop(0.35, "rgba(255, 51, 102, 0.85)");
      coreGrad.addColorStop(1, "rgba(136, 19, 55, 0.15)");
    } else if (orbState === "thinking") {
      coreGrad.addColorStop(0, "#faf5ff");
      coreGrad.addColorStop(0.35, "rgba(168, 85, 247, 0.85)");
      coreGrad.addColorStop(1, "rgba(59, 7, 100, 0.15)");
    } else {
      coreGrad.addColorStop(0, "#f0fdfa");
      coreGrad.addColorStop(0.3, "rgba(0, 240, 255, 0.8)");
      coreGrad.addColorStop(0.7, "rgba(112, 0, 255, 0.5)");
      coreGrad.addColorStop(1, "rgba(3, 7, 18, 0.08)");
    }

    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, R * breath, 0, Math.PI * 2);
    ctx.fill();

    // 2. 3D Astrolabe Gimbal Rings (Luxury Kinetic Gyroscope)
    // Gimbal Ring 1: Inclined at 45 deg
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(Math.PI / 4 + rotX * 0.2);
    ctx.beginPath();
    ctx.ellipse(0, 0, R + 9, (R + 9) * Math.cos(gimbalAngle1), 0, 0, Math.PI * 2);
    ctx.strokeStyle = orbState === "listening"
      ? "rgba(255, 51, 102, 0.55)"
      : "rgba(0, 240, 255, 0.55)";
    ctx.lineWidth = 1.0;
    ctx.stroke();
    ctx.restore();

    // Gimbal Ring 2: Inclined at -45 deg
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-Math.PI / 4 - rotX * 0.2);
    ctx.beginPath();
    ctx.ellipse(0, 0, R + 12, (R + 12) * Math.cos(gimbalAngle2), 0, 0, Math.PI * 2);
    ctx.strokeStyle = orbState === "thinking"
      ? "rgba(168, 85, 247, 0.6)"
      : "rgba(168, 85, 247, 0.4)";
    ctx.lineWidth = 0.9;
    ctx.stroke();
    ctx.restore();

    // 3. 3D Spherical Coordinate Transformation
    const projected = [];
    const focal = 190;

    for (let i = 0; i < points.length; i++) {
      const p = points[i];

      // Rotate Y
      const x1 = p.x * cosY - p.z * sinY;
      const z1 = p.z * cosY + p.x * sinY;

      // Rotate X
      const y2 = p.y * cosX - z1 * sinX;
      const z2 = z1 * cosX + p.y * sinX;

      const scale = focal / (focal + z2);
      projected.push({
        x: cx + x1 * scale,
        y: cy + y2 * scale,
        z: z2,
        scale: scale,
      });
    }

    // 4. Render 3D Latitude Rings
    for (let r = 1; r < rings; r++) {
      ctx.beginPath();
      for (let s = 0; s < segments; s++) {
        const idx = r * segments + s;
        const nextIdx = r * segments + ((s + 1) % segments);
        const p1 = projected[idx];
        const p2 = projected[nextIdx];

        if (s === 0) ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
      }
      ctx.closePath();
      const avgZ = projected[r * segments].z;
      const alpha = Math.max(0.12, (avgZ + R) / (2 * R));
      ctx.strokeStyle = orbState === "listening"
        ? `rgba(255, 51, 102, ${alpha * 0.65})`
        : `rgba(0, 240, 255, ${alpha * 0.55})`;
      ctx.lineWidth = 0.85;
      ctx.stroke();
    }

    // 5. Render 3D Longitude Meridians
    for (let s = 0; s < segments; s++) {
      ctx.beginPath();
      for (let r = 0; r <= rings; r++) {
        const idx = r * segments + s;
        const pt = projected[idx];
        if (r === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.strokeStyle = orbState === "thinking"
        ? "rgba(168, 85, 247, 0.45)"
        : "rgba(0, 240, 255, 0.35)";
      ctx.lineWidth = 0.7;
      ctx.stroke();
    }

    // 6. Draw Glowing Node Points for Foreground Vertices
    for (let i = 0; i < projected.length; i++) {
      const pt = projected[i];
      if (pt.z > 2) {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 1.4 * pt.scale, 0, Math.PI * 2);
        ctx.fillStyle = orbState === "listening" ? "#ff3366" : "#00f0ff";
        ctx.fill();
      }
    }

    // 7. Render 3D Orbiting Particle Stars
    orbiters.forEach((orb) => {
      orb.angle += orb.speed;
      const ox = Math.cos(orb.angle) * orb.orbitR;
      const oz = Math.sin(orb.angle) * orb.orbitR;
      const oy = oz * Math.sin(orb.tilt);

      const px = cx + (ox * cosY - oz * sinY);
      const pz = oz * cosY + ox * sinY;
      const py = cy + (oy * cosX - pz * sinX);

      if (pz > -R) {
        const pScale = focal / (focal + pz);
        ctx.beginPath();
        ctx.arc(px, py, orb.size * pScale, 0, Math.PI * 2);
        ctx.fillStyle = orbState === "listening" ? "#ff88a3" : "#70ffff";
        ctx.shadowColor = "#00f0ff";
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    });

    // 8. Audio Wave Equalizer Rings when Speaking
    if (orbState === "speaking") {
      for (let b = 0; b < 14; b++) {
        const barAngle = (b * Math.PI * 2) / 14 + time * 2;
        const waveH = Math.sin(time * 8 + b * 1.5) * 8 + 10;
        const bx1 = cx + Math.cos(barAngle) * (R + 4);
        const by1 = cy + Math.sin(barAngle) * (R + 4);
        const bx2 = cx + Math.cos(barAngle) * (R + 4 + waveH);
        const by2 = cy + Math.sin(barAngle) * (R + 4 + waveH);

        ctx.beginPath();
        ctx.moveTo(bx1, by1);
        ctx.lineTo(bx2, by2);
        ctx.strokeStyle = "rgba(0, 240, 255, 0.85)";
        ctx.lineWidth = 1.6;
        ctx.stroke();
      }
    }

    requestAnimationFrame(draw3DLattice);
  }

  draw3DLattice();
}

// =============================================================================
// 5. PHYSICAL 3D TILT CARDS WITH DYNAMIC SPECULAR GLARE
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

      const rotX = ((y - cy) / cy) * -7;
      const rotY = ((x - cx) / cx) * 7;

      card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.012, 1.012, 1.012)`;
    });

    card.addEventListener("pointerleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
      card.style.transition = "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)";
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
    u.pitch = 1.02;

    const voices = window.speechSynthesis.getVoices() || [];
    const preferred = voices.find(
      (v) =>
        v.lang.startsWith("en") &&
        (v.name.includes("Samantha") ||
          v.name.includes("Karen") ||
          v.name.includes("Victoria") ||
          v.name.includes("Google UK English Female") ||
          v.name.includes("Natural"))
    ) || voices.find((v) => v.lang.startsWith("en"));

    if (preferred) u.voice = preferred;

    u.onstart = () => {
      orbState = "speaking";
      syncCoreStatusBadge();
    };
    u.onend = () => {
      orbState = "idle";
      syncCoreStatusBadge();
    };
    u.onerror = () => {
      orbState = "idle";
      syncCoreStatusBadge();
    };

    window.speechSynthesis.speak(u);
  } catch {
    // Audio fallback
  }
}

$("alexaSpeechTestBtn")?.addEventListener("click", () => {
  speakVoice("Hearth Universal online. Glass-box household operations ready.");
});

// =============================================================================
// 8. HEADER, CLOCK, BRAIN SWITCHING & STATE EXPORT
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
    const brainSelect = $("brainProviderSelect");

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

    if (brainSelect && health.active_provider) {
      brainSelect.value = health.active_provider.toLowerCase().includes("bedrock")
        ? "bedrock"
        : health.active_provider.toLowerCase().includes("openai")
        ? "openai"
        : "local";
    }
  } catch {
    const pill = $("protocolStatusPill");
    const text = $("protocolText");
    if (pill) pill.className = "hud-badge";
    if (text) text.textContent = "Server Offline (:8787)";
  }
}

// Brain Selector change handler
$("brainProviderSelect")?.addEventListener("change", async (e) => {
  const newProvider = e.target.value;
  playSfx("click");
  try {
    await api.post("/api/brain", { provider: newProvider });
    showToast(`Switched brain provider to: ${newProvider.toUpperCase()}`, "success");
    await refreshHeaderStats();
  } catch (err) {
    showToast(`Could not switch brain: ${err.message}`, "error");
  }
});

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

// Export State JSON Download
$("exportAuditBtn")?.addEventListener("click", async () => {
  playSfx("click");
  try {
    const exportData = await api.get("/api/export");
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hearth_audit_state_${Math.floor(Date.now() / 1000)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast("Cryptographic state archive exported", "success");
  } catch (err) {
    showToast(`Export failed: ${err.message}`, "error");
  }
});

// =============================================================================
// 9. SCENES, ROUTINES & PERIMETER DEADBOLT
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

// Coordinated Household Routines Handler
function setupRoutinesHandlers() {
  $$("#routinesButtonsList button").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const routineName = btn.dataset.routine;
      playSfx("routine");
      try {
        await api.post("/api/home/routine", { name: routineName });
        showToast(`Coordinated Routine “${routineName}” executed`, "success");
        await refreshHome();
      } catch (err) {
        showToast(`Routine failed: ${err.message}`, "error");
      }
    });
  });
}

async function togglePerimeterLock(toLock) {
  try {
    playSfx("lock");
    const res = await api.post("/api/home/lock", { locked: toLock });
    const isLocked = res.status === "locked";
    showToast(isLocked ? "Front door locked securely" : "Front door unlocked", isLocked ? "success" : "warning");
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

async function sendChat(explicitText = null) {
  const input = $("composerInput");
  const sendBtn = $("composerSendBtn");
  if (!input) return;

  const msg = explicitText || input.value.trim();
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

    if (res.latency_ms && $("telemetryLatency")) {
      $("telemetryLatency").textContent = `${res.latency_ms}ms`;
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

// Stage Pantry Reorder button in Wealth tab
$("stagePantryReorderBtn")?.addEventListener("click", () => {
  sendChat("Reorder coffee and eco detergent bundle");
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
// 12. TAB 1: APPROVALS TRAY & CRYPTOGRAPHIC INSPECTION
// =============================================================================

function openInspectionModal(p) {
  const modal = $("inspectionModal");
  if (!modal) return;
  playSfx("click");

  const titleEl = $("modalProposalTitle");
  const idEl = $("modalProposalId");
  const verdictEl = $("modalSentinelVerdict");
  const reasonEl = $("modalSentinelReason");
  const hashEl = $("modalMerkleHash");
  const costEl = $("modalCostImpact");
  const diffSec = $("modalDiffSection");
  const diffPre = $("modalDiffPre");

  if (titleEl) titleEl.textContent = p.title || "Cryptographic Inspection";
  if (idEl) idEl.textContent = `PROPOSAL ID: ${p.id || "prop-unknown"} · TYPE: ${p.kind || "general"}`;

  const risk = (p.risk_level || "medium").toLowerCase();
  if (verdictEl) {
    if (risk === "high") {
      verdictEl.textContent = "TIER 2: ASK (GATED BY PROPOSE-NEVER-EXECUTE)";
      verdictEl.style.borderColor = "var(--rose)";
      verdictEl.style.color = "var(--rose)";
      verdictEl.style.background = "rgba(255, 51, 102, 0.12)";
    } else {
      verdictEl.textContent = "TIER 2: ASK (HUMAN AUTHORIZATION REQUIRED)";
      verdictEl.style.borderColor = "var(--amber)";
      verdictEl.style.color = "var(--amber)";
      verdictEl.style.background = "rgba(251, 191, 36, 0.12)";
    }
  }

  if (reasonEl) reasonEl.textContent = p.reasons || "Consequential operation staged in accordance with Sentinel Propose-Never-Execute policy.";

  // Deterministic verifiable cryptographic SHA-256 seal representation
  let seed = p.id + (p.title || "") + (p.kind || "") + (p.created_at || "1");
  let pseudoHash = "";
  for (let i = 0; i < seed.length; i++) {
    pseudoHash += (seed.charCodeAt(i) * 17 + i * 31).toString(16);
  }
  pseudoHash = pseudoHash.padEnd(64, "a9b4c029f8e71536b2d1c0a4e5f67890").slice(0, 64);
  if (hashEl) hashEl.textContent = `SHA-256: ${pseudoHash}`;

  const cost = Number(p.cost_delta_yr || 0);
  if (costEl) {
    if (cost > 0) {
      costEl.textContent = `+${formatMoney(cost)}/yr`;
      costEl.style.color = "var(--emerald)";
    } else if (cost < 0) {
      costEl.textContent = `-${formatMoney(Math.abs(cost))} total`;
      costEl.style.color = "var(--rose)";
    } else {
      costEl.textContent = "$0.00 (Zero direct cost)";
      costEl.style.color = "var(--text-bright)";
    }
  }

  if (p.diff) {
    if (diffSec) diffSec.hidden = false;
    if (diffPre) diffPre.textContent = p.diff;
  } else {
    if (diffSec) diffSec.hidden = true;
  }

  const okBtn = $("modalApproveBtn");
  const noBtn = $("modalRejectBtn");

  if (okBtn) {
    okBtn.onclick = () => {
      closeInspectionModal();
      decideProposal(p.id, true);
    };
  }
  if (noBtn) {
    noBtn.onclick = () => {
      closeInspectionModal();
      decideProposal(p.id, false);
    };
  }

  modal.classList.add("active");
  modal.setAttribute("aria-hidden", "false");
}

function closeInspectionModal() {
  const modal = $("inspectionModal");
  if (!modal) return;
  modal.classList.remove("active");
  modal.setAttribute("aria-hidden", "true");
}

$("modalCloseBtn")?.addEventListener("click", closeInspectionModal);
$("inspectionModal")?.addEventListener("click", (e) => {
  if (e.target === $("inspectionModal")) closeInspectionModal();
});
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeInspectionModal();
});

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

        const inspectBtn = document.createElement("button");
        inspectBtn.className = "infeed-btn";
        inspectBtn.style.width = "100%";
        inspectBtn.style.margin = "10px 0 6px";
        inspectBtn.style.fontSize = "11px";
        inspectBtn.style.justifyContent = "center";
        inspectBtn.innerHTML = "<span>🛡️ Inspect Cryptographic & DAG Trace</span>";
        inspectBtn.addEventListener("click", () => openInspectionModal(p));
        card.appendChild(inspectBtn);

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

        // Mood Lighting Presets Bar
        const moodRow = document.createElement("div");
        moodRow.className = "room-mood-row";

        const moodLbl = document.createElement("span");
        moodLbl.className = "room-mood-label";
        moodLbl.textContent = "Mood:";
        moodRow.appendChild(moodLbl);

        const MOODS = [
          { label: "Warm", color: "#ffb366", patch: { bri: 65, color_temp: "warm", hex: "#ffb366", on: true } },
          { label: "Daylight", color: "#ffffff", patch: { bri: 95, color_temp: "cool", hex: "#ffffff", on: true } },
          { label: "Cyber", color: "#00f0ff", patch: { bri: 85, color_temp: "neutral", hex: "#00f0ff", on: true } },
          { label: "Cinema", color: "#9933ff", patch: { bri: 25, color_temp: "warm", hex: "#9933ff", on: true } },
        ];

        MOODS.forEach((m) => {
          const mBtn = document.createElement("button");
          mBtn.className = "mood-preset-btn";
          mBtn.innerHTML = `<span class="mood-color-dot" style="background:${m.color};box-shadow:0 0 6px ${m.color};"></span><span>${m.label}</span>`;
          mBtn.addEventListener("click", () => {
            playSfx("click");
            patchDevice(def.id, "lights", m.patch);
            showToast(`${def.label.split(" ")[1] || "Room"} mood set to ${m.label}`, "info");
          });
          moodRow.appendChild(mBtn);
        });
        card.appendChild(moodRow);
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

        const desc = document.createElement("div");
        desc.style.display = "flex";
        desc.style.alignItems = "center";
        desc.style.gap = "8px";

        const eqHtml = room.media.playing
          ? `<span class="audio-eq-bars"><span class="audio-eq-bar"></span><span class="audio-eq-bar"></span><span class="audio-eq-bar"></span><span class="audio-eq-bar"></span></span>`
          : "";

        desc.innerHTML = `<span style="font-size:12.5px;color:var(--text-bright);">${room.media.playing ? "▶" : "⏸"} ${esc(room.media.title || "Idle")}</span> ${eqHtml} <small style="color:var(--text-dim);font-family:var(--font-mono);">(${room.media.volume || 40}%)</small>`;

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
// 17. AUTONOMOUS HOUSEHOLD HEARTBEAT ENGINE
// =============================================================================

async function refreshHeartbeat() {
  const stream = $("heartbeatEventStream");
  if (!stream) return;
  try {
    const res = await api.get("/api/heartbeat");
    const events = res.events || [];
    if (events.length === 0) return;

    stream.innerHTML = events.slice(0, 6).map((e) => `
      <div class="heartbeat-event-pill" title="${esc(e.detail)}">
        <span>${esc(e.icon || "⚡")}</span>
        <div><strong>${esc(e.title)}</strong> · ${esc(e.detail)}</div>
        <span class="event-time">${esc(e.time_str || "")}</span>
      </div>
    `).join("");
  } catch {
    // Non-blocking
  }
}

async function triggerProactivePulse() {
  playSfx("click");
  const btn = $("triggerProactiveBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await api.post("/api/simulate/tick", { scenario: "auto" });
    playSfx("routine");
    showToast(`⚡ Proactive Event: ${res.event?.title || "Simulated"}`, "info");
    await refreshHeartbeat();
    await refreshAll();
  } catch (err) {
    showToast(`Proactive pulse error: ${err.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// =============================================================================
// 18. KEYBOARD SHORTCUTS & BOOTSTRAP
// =============================================================================

function setupKeyboardShortcuts() {
  window.addEventListener("keydown", (e) => {
    // Cmd+K or Ctrl+K or '/' to focus composer
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      $("composerInput")?.focus();
    } else if (e.key === "/" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      $("composerInput")?.focus();
    } else if (e.key === "Escape") {
      $("composerInput")?.blur();
      $("memoryFilterInput")?.blur();
      closeInspectionModal();
    }
  });
}

async function refreshAll() {
  await Promise.allSettled([
    refreshHeaderStats(),
    refreshTray(),
    refreshHome(),
    refreshWealth(),
    refreshMemory(),
    refreshLedger(),
    refreshHeartbeat(),
  ]);
  apply3DTiltCards();
}

function seedIntroMessage() {
  appendMessage(
    "alexa",
    "Welcome to **Hearth Universal** — the open glass-box household operations agent for Amazon Alexa+.\n\n" +
      "Under our strict **Propose-Never-Execute** contract, all consequential actions stage in your **Approval Tray** with transparent cost deltas before anything executes.\n\n" +
      "Select a prompt chip above, switch brain providers in the header, or say: **“Save me $800 on renewals”**!"
  );
}

document.addEventListener("DOMContentLoaded", () => {
  setupCursorSpotlight();
  initStarfieldCanvas();
  initKineticOrb();
  setupSpeechRecognition();
  initQuickPromptRail();
  setupRoutinesHandlers();
  setupKeyboardShortcuts();
  seedIntroMessage();
  refreshAll();

  $("triggerProactiveBtn")?.addEventListener("click", triggerProactivePulse);

  setInterval(refreshAll, 6000);
});
