/**
 * Hearth Universal — Apple Intelligence & Linear Luxury Edition
 * Spec 2025-11-25 Streamable HTTP · Propose-Never-Execute · Glass-Box Core
 * Features: Chromatic Fluid WebGL Shader Orb, Spatial Web Audio, ReAct Pipeline, Digital Twin Sync
 */

const $ = id => document.getElementById(id);
let sfxEnabled = true;
let ttsEnabled = true;
let isRecording = false;
let orbState = "idle"; // "idle" | "listening" | "thinking" | "speaking"
let recognition = null;

// =============================================================================
// 1. Apple Intelligence Chromatic Liquid Shader Orb (Three.js WebGL)
// =============================================================================
const FluidOrb = {
  renderer: null,
  scene: null,
  camera: null,
  mesh: null,
  material: null,
  uniforms: null,
  canvas: null,
  targetIntensity: 0.18,
  currentIntensity: 0.18,
  targetSpeed: 0.5,
  currentSpeed: 0.5,

  init() {
    this.canvas = $("fluidOrbCanvas");
    if (!this.canvas || typeof THREE === "undefined") return;

    const width = this.canvas.clientWidth || 140;
    const height = this.canvas.clientHeight || 140;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    this.camera.position.z = 4.2;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Custom GLSL 3D Simplex Noise & Chromatic Fresnel Shader
    const vertexShader = `
      uniform float uTime;
      uniform float uIntensity;
      varying vec3 vNormal;
      varying vec3 vViewPosition;
      varying float vDisplacement;

      // Simplex 3D Noise Implementation
      vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
      vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

      float snoise(vec3 v){
        const vec2 C = vec2(1.0/6.0, 1.0/3.0);
        const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
        vec3 i  = floor(v + dot(v, C.yyy));
        vec3 x0 = v - i + dot(i, C.xxx);
        vec3 g = step(x0.yzx, x0.xyz);
        vec3 l = 1.0 - g;
        vec3 i1 = min(g.xyz, l.zxy);
        vec3 i2 = max(g.xyz, l.zxy);
        vec3 x1 = x0 - i1 + 1.0 * C.xxx;
        vec3 x2 = x0 - i2 + 2.0 * C.xxx;
        vec3 x3 = x0 - 1.0 + 3.0 * C.xxx;
        i = mod(i, 289.0);
        vec4 p = permute(permute(permute(
                  i.z + vec4(0.0, i1.z, i2.z, 1.0))
                + i.y + vec4(0.0, i1.y, i2.y, 1.0))
                + i.x + vec4(0.0, i1.x, i2.x, 1.0));
        float n_ = 0.142857142857;
        vec3 ns = n_ * D.wyz - D.xzx;
        vec4 j = p - 49.0 * floor(p * ns.z *ns.z);
        vec4 x_ = floor(j * ns.z);
        vec4 y_ = floor(j - 7.0 * x_);
        vec4 x = x_ *ns.x + ns.yyyy;
        vec4 y = y_ *ns.x + ns.yyyy;
        vec4 h = 1.0 - abs(x) - abs(y);
        vec4 b0 = vec4(x.xy, y.xy);
        vec4 b1 = vec4(x.zw, y.zw);
        vec4 s0 = floor(b0)*2.0 + 1.0;
        vec4 s1 = floor(b1)*2.0 + 1.0;
        vec4 sh = -step(h, vec4(0.0));
        vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
        vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
        vec3 p0 = vec3(a0.xy, h.x);
        vec3 p1 = vec3(a0.zw, h.y);
        vec3 p2 = vec3(a1.xy, h.z);
        vec3 p3 = vec3(a1.zw, h.w);
        vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
        p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
        vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
        m = m * m;
        return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
      }

      void main() {
        vNormal = normalize(normalMatrix * normal);
        float noise = snoise(normal * 2.2 + vec3(0.0, 0.0, uTime));
        vDisplacement = noise;
        vec3 newPos = position + normal * (noise * uIntensity);
        vec4 mvPosition = modelViewMatrix * vec4(newPos, 1.0);
        vViewPosition = -mvPosition.xyz;
        gl_Position = projectionMatrix * mvPosition;
      }
    `;

    const fragmentShader = `
      uniform float uTime;
      varying vec3 vNormal;
      varying vec3 vViewPosition;
      varying float vDisplacement;

      void main() {
        vec3 normal = normalize(vNormal);
        vec3 viewDir = normalize(vViewPosition);

        // Apple Chromatic Fresnel Rim
        float fresnel = pow(1.0 - max(dot(normal, viewDir), 0.0), 2.2);

        // Luxury Palette Interpolation (Electric Azure, Cosmic Indigo, Magenta Flare)
        vec3 cDeep = vec3(0.04, 0.06, 0.14);
        vec3 cAzure = vec3(0.05, 0.65, 0.98);
        vec3 cIndigo = vec3(0.39, 0.40, 0.95);
        vec3 cRose = vec3(0.96, 0.25, 0.45);

        // Dynamic fluid blend
        vec3 color = mix(cDeep, cIndigo, vDisplacement * 0.5 + 0.5);
        color = mix(color, cAzure, fresnel * 0.75);
        color = mix(color, cRose, pow(fresnel, 3.5) * 0.85);

        // Soft internal glow
        float alpha = 0.88 + fresnel * 0.12;
        gl_FragColor = vec4(color, alpha);
      }
    `;

    this.uniforms = {
      uTime: { value: 0.0 },
      uIntensity: { value: 0.18 }
    };

    const geometry = new THREE.SphereGeometry(1.4, 64, 64);
    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: this.uniforms,
      transparent: true
    });

    this.mesh = new THREE.Mesh(geometry, this.material);
    this.scene.add(this.mesh);

    // Interactive ripple click
    this.canvas.addEventListener("click", () => {
      this.currentIntensity = 0.45;
      playSfx("wake");
    });

    this.animate();
  },

  setState(st) {
    orbState = st;
    const pillText = $("aiStatusText");
    if (st === "thinking") {
      this.targetIntensity = 0.38;
      this.targetSpeed = 1.6;
      if (pillText) pillText.textContent = "Cognitive Reasoning · ReAct Loop Active";
    } else if (st === "speaking") {
      this.targetIntensity = 0.30;
      this.targetSpeed = 1.2;
      if (pillText) pillText.textContent = "Voice Synthesis · Ambient Audio Active";
    } else if (st === "listening") {
      this.targetIntensity = 0.28;
      this.targetSpeed = 1.4;
      if (pillText) pillText.textContent = "Listening · Awaiting Dictation";
    } else {
      this.targetIntensity = 0.18;
      this.targetSpeed = 0.5;
      if (pillText) pillText.textContent = "Ambient Listening · Propose-Never-Execute";
    }
  },

  animate() {
    requestAnimationFrame(() => this.animate());

    // Smooth inertia lerp for fluid intensity
    this.currentIntensity += (this.targetIntensity - this.currentIntensity) * 0.08;
    this.currentSpeed += (this.targetSpeed - this.currentSpeed) * 0.08;

    if (this.uniforms) {
      this.uniforms.uTime.value += 0.015 * this.currentSpeed;
      this.uniforms.uIntensity.value = this.currentIntensity;
    }

    if (this.mesh) {
      this.mesh.rotation.y += 0.004;
      this.mesh.rotation.x += 0.002;
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
};

// =============================================================================
// 2. Refined Procedural Web Audio Sound Engine
// =============================================================================
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
  return audioCtx;
}

function playSfx(type) {
  if (!sfxEnabled) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  const now = ctx.currentTime;
  if (type === "click") {
    // Ultra-crisp subtle micro-click
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(1400, now);
    osc.frequency.exponentialRampToValueAtTime(350, now + 0.03);
    gain.gain.setValueAtTime(0.06, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.03);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.03);
  } else if (type === "wake") {
    // Elegant warm harmonic chime
    [523.25, 659.25, 783.99].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + idx * 0.05);
      gain.gain.setValueAtTime(0.06, now + idx * 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.05 + 0.28);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.05);
      osc.stop(now + idx * 0.05 + 0.28);
    });
  } else if (type === "approve") {
    // Resolved celebratory major chord
    [440, 554.37, 659.25, 880].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, now + idx * 0.06);
      gain.gain.setValueAtTime(0.07, now + idx * 0.06);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.32);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.06);
      osc.stop(now + idx * 0.06 + 0.32);
    });
  } else if (type === "lock") {
    // Mechanical servo chirp
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(320, now);
    osc.frequency.linearRampToValueAtTime(440, now + 0.06);
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.12);
  }
}

// =============================================================================
// 3. Conversational Surface & ReAct Flow
// =============================================================================
async function sendUserPrompt(overrideText = null) {
  const input = $("promptInput");
  const prompt = (overrideText || (input ? input.value : "")).trim();
  if (!prompt) return;

  if (input) input.value = "";
  playSfx("wake");

  appendMessage("user", prompt);
  FluidOrb.setState("thinking");

  // Show Pipeline Drawer with animated step
  const drawer = $("pipelineDrawer");
  const flow = $("pipelineFlow");
  if (drawer && flow) {
    drawer.style.display = "block";
    flow.innerHTML = `
      <div class="pipeline-step step-success"><span>📥</span> Stimulus Received</div>
      <div style="color: var(--text-tertiary); font-size: 11px;">➔</div>
      <div class="pipeline-step"><span>🛡️</span> Sentinel Safety Gate</div>
      <div style="color: var(--text-tertiary); font-size: 11px;">➔</div>
      <div class="pipeline-step"><span>🧠</span> ReAct Planning</div>
    `;
  }

  const startTime = performance.now();
  const engine = $("engineSelect") ? $("engineSelect").value : "local";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt, brain_override: engine })
    });
    const data = await res.json();
    const elapsed = Math.round(performance.now() - startTime);

    if ($("latencyBadge")) $("latencyBadge").textContent = `Latency: ${elapsed}ms`;
    if ($("pipelineTimeTag")) $("pipelineTimeTag").textContent = `${elapsed}ms`;

    if (data.ok) {
      appendMessage("assistant", data.reply, data.steps || []);
      if (data.steps && data.steps.length > 0) {
        renderPipeline(data.steps);
      }
      if (ttsEnabled && data.reply) {
        speakResponse(data.reply);
      }
    } else {
      appendMessage("assistant", `⚠️ **Engine Notice**: ${data.error || "Unable to process request."}`);
    }
  } catch (err) {
    appendMessage("assistant", `🚨 **Connection Notice**: ${err.message}`);
  } finally {
    FluidOrb.setState("idle");
    refreshTelemetry();
  }
}

function triggerPrompt(txt) {
  playSfx("click");
  sendUserPrompt(txt);
}

function appendMessage(role, text, steps = []) {
  const stream = $("chatStream");
  if (!stream) return;

  const entry = document.createElement("div");
  entry.className = `chat-entry chat-${role}`;

  let meta = "";
  if (role === "assistant") {
    meta = `
      <div class="chat-header-meta">
        <span>Alexa+ Core</span>
        <button class="btn-speak-listen" onclick="speakResponse('${escapeAttr(text)}')">🔊 Listen</button>
      </div>
    `;
  }

  let stepsSummary = "";
  if (steps && steps.length > 0) {
    stepsSummary = `
      <div style="margin-top: 8px; font-size: 11.5px; color: var(--accent-cyan); display: flex; align-items: center; gap: 6px;">
        <span>⚡ Executed ${steps.length} ReAct actions:</span>
        <code>${steps.map(s => s.tool || s.type).join(" · ")}</code>
      </div>
    `;
  }

  entry.innerHTML = `
    ${meta}
    <div>${formatMarkdown(text)}</div>
    ${stepsSummary}
  `;

  stream.appendChild(entry);
  stream.scrollTop = stream.scrollHeight;
}

function renderPipeline(steps) {
  const flow = $("pipelineFlow");
  if (!flow) return;

  flow.innerHTML = steps.map((s, idx) => {
    const isCompleted = s.status === "completed" || s.decision === "pass";
    const isGated = s.status === "gated";
    const statusClass = isGated ? "step-gated" : "step-success";
    const icon = s.tool ? "🛠️" : "🧠";

    return `
      <div class="pipeline-step ${statusClass}">
        <span>${icon}</span>
        <span>${escapeHtml(s.tool || s.type || `Action ${idx + 1}`)}</span>
      </div>
      ${idx < steps.length - 1 ? '<div style="color: var(--text-tertiary); font-size: 11px;">➔</div>' : ''}
    `;
  }).join("");
}

// =============================================================================
// 4. Executive Glass-Box Approval Tray & State Synchronization
// =============================================================================
async function refreshTelemetry() {
  try {
    // 1. Digital Twin State
    const homeRes = await fetch("/api/home");
    if (homeRes.ok) {
      const data = await homeRes.json();
      updateHomeState(data);
    }

    // 2. Proposals State
    const propRes = await fetch("/api/proposals");
    if (propRes.ok) {
      const pData = await propRes.json();
      const list = pData.proposals || [];
      const count = pData.pending_count ?? list.filter(p => p.status === "pending").length;

      if ($("badgeTrayCount")) $("badgeTrayCount").textContent = count;
      if ($("heroPendingCount")) $("heroPendingCount").textContent = `${count} Actions`;

      renderProposals(list);
    }

    // 3. Commerce State
    const comRes = await fetch("/api/commerce");
    if (comRes.ok) {
      const cData = await comRes.json();
      renderCommerce(cData);
    }
  } catch (err) {
    console.debug("Telemetry sync tick", err);
  }
}

function updateHomeState(data) {
  // Living Room Light
  const livingBri = data.living_room?.lights?.bri ?? 80;
  const livingOn = data.living_room?.lights?.on ?? true;
  if ($("livingLightLabel")) $("livingLightLabel").textContent = livingOn ? `${livingBri}% Warm` : "0% Off";
  if ($("sliderLivingLight")) $("sliderLivingLight").value = livingOn ? livingBri : 0;

  // Front Door Lock
  const locked = data.front_door?.lock?.locked ?? true;
  const pillLock = $("pillLockStatus");
  if (pillLock) {
    pillLock.textContent = locked ? "LOCKED" : "UNLOCKED";
    pillLock.className = `pill-badge ${locked ? 'active-green' : 'active-cyan'}`;
  }
}

function renderProposals(proposals) {
  const container = $("proposalsList");
  if (!container) return;

  const pending = (proposals || []).filter(p => p.status === "pending");
  if (pending.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-tertiary); padding: 48px 0; font-size: 13px;">
        No pending action proposals.<br/>Ask Alexa+ to <i>"Save me $437 on renewals"</i> or <i>"Reorder coffee"</i> to draft proposals.
      </div>
    `;
    return;
  }

  container.innerHTML = pending.map(p => `
    <div class="proposal-card" id="card-${p.id}">
      <div class="proposal-top">
        <div>
          <div class="proposal-name">🛡️ ${escapeHtml(p.action)}</div>
          <div class="proposal-meta-tag font-mono">Contract #${p.id}</div>
        </div>
        <span class="pill-badge active-cyan font-mono">PENDING REVIEW</span>
      </div>
      <div style="font-size: 12.5px; color: var(--text-secondary); margin-bottom: 6px;">
        ${escapeHtml(p.reason || 'Consequential operation requiring human verification.')}
      </div>
      <div class="proposal-diff-box font-mono">
        ${escapeHtml(JSON.stringify(p.params || {}, null, 2))}
      </div>
      <div class="proposal-actions">
        <button class="btn-approve" onclick="decideAction('${p.id}', true)">
          ✓ Authorize & Execute
        </button>
        <button class="btn-reject" onclick="decideAction('${p.id}', false)">
          ✕ Dismiss
        </button>
      </div>
    </div>
  `).join("");
}

async function decideAction(id, approved) {
  playSfx(approved ? "approve" : "click");
  const card = $(`card-${id}`);
  if (card) card.style.opacity = "0.5";

  try {
    const res = await fetch(`/api/proposals/${id}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved })
    });
    const data = await res.json();
    if (data.ok) {
      appendMessage("assistant", `Proposal **#${id}** was **${approved ? 'AUTHORIZED' : 'DISMISSED'}** by user.`);
    }
  } catch (err) {
    console.error("Decision failed", err);
  } finally {
    refreshTelemetry();
  }
}

// Digital Twin Controls
async function applyScene(sceneName) {
  playSfx("wake");
  document.querySelectorAll(".scene-btn").forEach(b => b.classList.remove("active"));
  event.currentTarget.classList.add("active");

  await fetch("/api/home/scene", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: sceneName })
  });
  refreshTelemetry();
}

async function changeTemp(room, delta) {
  playSfx("click");
  const disp = room === "living_room" ? $("dispLivingTemp") : $("dispBedroomTemp");
  if (!disp) return;
  let cur = parseFloat(disp.textContent) || 22.0;
  cur = Math.round((cur + delta) * 10) / 10;
  disp.textContent = `${cur.toFixed(1)}°C`;

  await fetch("/api/home/device", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room,
      device: "climate",
      patch: { target_c: cur }
    })
  });
}

async function toggleLockAction() {
  const isLocked = $("pillLockStatus")?.textContent === "LOCKED";
  const newLocked = !isLocked;
  playSfx("lock");

  await fetch("/api/home/lock", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ locked: newLocked })
  });
  refreshTelemetry();
}

// Commerce & Pantry
function renderCommerce(data) {
  const inv = data.inventory || [];
  const subs = inv.filter(i => i.is_subscription);
  const pantry = inv.filter(i => !i.is_subscription);

  const subsBox = $("subsContainer");
  if (subsBox) {
    subsBox.innerHTML = subs.map(s => `
      <div class="commerce-row">
        <div>
          <div style="font-weight: 600; font-size: 13px;">${escapeHtml(s.name)}</div>
          <div style="font-size: 11px; color: var(--text-tertiary);">$${s.monthly_cost}/mo · ${s.usage_status}</div>
        </div>
        <span class="pill-badge ${s.usage_status === 'unused' ? 'active-cyan' : ''}">
          ${s.usage_status === 'unused' ? 'Flagged Save $437' : 'Active'}
        </span>
      </div>
    `).join("");
  }

  const pantryBox = $("pantryContainer");
  if (pantryBox) {
    pantryBox.innerHTML = pantry.map(p => {
      const pct = p.level_pct ?? Math.round((p.qty_current / (p.qty_target || 100)) * 100);
      const isLow = pct < 25;
      return `
        <div class="commerce-row">
          <div>
            <div style="font-weight: 600; font-size: 13px;">${escapeHtml(p.name)}</div>
            <div style="font-size: 11px; color: var(--text-tertiary);">${pct}% In Stock</div>
            <div class="progress-track">
              <div class="progress-fill" style="width: ${pct}%; background: ${isLow ? '#f43f5e' : '#10b981'};"></div>
            </div>
          </div>
          <button class="btn-ghost" onclick="triggerPrompt('Reorder ${escapeAttr(p.name)}')">Reorder</button>
        </div>
      `;
    }).join("");
  }
}

// Memory Vault
async function addFactAction() {
  const k = $("factKeyInput")?.value?.trim();
  const v = $("factValInput")?.value?.trim();
  if (!k || !v) return;

  playSfx("click");
  await fetch("/api/memory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: k, value: v })
  });

  if ($("factKeyInput")) $("factKeyInput").value = "";
  if ($("factValInput")) $("factValInput").value = "";
  loadFacts();
}

async function loadFacts() {
  try {
    const res = await fetch("/api/memory");
    const data = await res.json();
    const facts = data.facts || [];
    const container = $("factsContainer");
    if (!container) return;

    container.innerHTML = facts.map(f => `
      <div class="commerce-row">
        <div>
          <strong style="color: var(--accent-cyan); font-size: 12.5px;">${escapeHtml(f.key)}</strong>
          <div style="font-size: 11.5px; color: var(--text-secondary);">${escapeHtml(f.value)}</div>
        </div>
        <span class="pill-badge font-mono">SQLite Fact</span>
      </div>
    `).join("");
  } catch (err) {
    console.debug("Failed to load facts", err);
  }
}

// Merkle Audit Ledger
async function showAuditModal() {
  playSfx("click");
  const dialog = $("auditDialog");
  const tbody = $("merkleRows");
  if (!dialog || !tbody) return;

  try {
    const res = await fetch("/api/audit");
    const data = await res.json();
    const rows = data.recent || [];

    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${new Date((r.ts || r.timestamp || 0) * 1000).toLocaleTimeString()}</td>
        <td><span class="pill-badge">${escapeHtml(r.actor || 'agent')}</span></td>
        <td><strong>${escapeHtml(r.action || '')}</strong></td>
        <td><code style="color: var(--accent-cyan); font-size: 11px;">${(r.hash || '').slice(0, 16)}...</code></td>
      </tr>
    `).join("");

    dialog.showModal();
  } catch (err) {
    console.error("Failed to load audit", err);
  }
}

// =============================================================================
// 5. Speech Synthesis & Dictation
// =============================================================================
function speakResponse(txt) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  FluidOrb.setState("speaking");

  const clean = txt.replace(/[*_#`]/g, "");
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  utterance.onend = () => FluidOrb.setState("idle");
  utterance.onerror = () => FluidOrb.setState("idle");
  window.speechSynthesis.speak(utterance);
}

function initSpeech() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;

  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    FluidOrb.setState("listening");
    const btn = $("micBtn");
    if (btn) btn.classList.add("recording");
    playSfx("wake");
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    if ($("promptInput")) $("promptInput").value = transcript;
    sendUserPrompt(transcript);
  };

  recognition.onend = () => {
    isRecording = false;
    FluidOrb.setState("idle");
    const btn = $("micBtn");
    if (btn) btn.classList.remove("recording");
  };
}

function toggleMic() {
  if (!recognition) initSpeech();
  if (!recognition) {
    alert("Speech recognition not supported in this browser.");
    return;
  }
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// =============================================================================
// 6. Markdown Formatter & Utilities
// =============================================================================
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m]));
}

function escapeAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatMarkdown(md) {
  if (!md) return "";
  let html = escapeHtml(md);
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  return `<p>${html.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`;
}

// =============================================================================
// 7. Initialization
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize Fluid Shader Orb
  FluidOrb.init();

  // 2. Initialize Speech Recognition
  initSpeech();

  // 3. Tab Navigation
  document.querySelectorAll(".deck-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      playSfx("click");
      document.querySelectorAll(".deck-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".deck-content-pane").forEach(p => p.style.display = "none");
      btn.classList.add("active");
      const target = $(btn.dataset.pane);
      if (target) target.style.display = "block";
      if (btn.dataset.pane === "paneMemory") loadFacts();
    });
  });

  // 4. Input Events
  if ($("sendBtn")) {
    $("sendBtn").addEventListener("click", () => sendUserPrompt());
  }
  if ($("promptInput")) {
    $("promptInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendUserPrompt();
    });
  }
  if ($("micBtn")) {
    $("micBtn").addEventListener("click", () => toggleMic());
  }

  // 5. Toggles & Modal
  if ($("sfxToggleBtn")) {
    $("sfxToggleBtn").addEventListener("click", () => {
      sfxEnabled = !sfxEnabled;
      $("sfxToggleBtn").textContent = sfxEnabled ? "🔊 SFX" : "🔇 Muted";
      playSfx("click");
    });
  }
  if ($("ttsToggleBtn")) {
    $("ttsToggleBtn").addEventListener("click", () => {
      ttsEnabled = !ttsEnabled;
      $("ttsToggleBtn").textContent = ttsEnabled ? "🗣️ Voice" : "🔇 Silent";
      playSfx("click");
    });
  }
  if ($("auditModalBtn")) {
    $("auditModalBtn").addEventListener("click", () => showAuditModal());
  }
  if ($("resetBtn")) {
    $("resetBtn").addEventListener("click", async () => {
      playSfx("click");
      await fetch("/api/reset", { method: "POST" });
      refreshTelemetry();
      appendMessage("assistant", "System state was reset to baseline.");
    });
  }

  // 6. Slider
  if ($("sliderLivingLight")) {
    $("sliderLivingLight").addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      if ($("livingLightLabel")) $("livingLightLabel").textContent = `${val}% Warm`;
    });
    $("sliderLivingLight").addEventListener("change", async (e) => {
      const val = parseInt(e.target.value, 10);
      await fetch("/api/home/device", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          room: "living_room",
          device: "lights",
          patch: { bri: val, on: val > 0 }
        })
      });
      refreshTelemetry();
    });
  }

  // 7. Initial Telemetry Poll
  refreshTelemetry();
  setInterval(refreshTelemetry, 3000);
});
