/**
 * Hearth Universal — God-Tier Alexa+ Ambient Operations Engine
 * Spec 2025-11-25 Streamable HTTP · Propose-Never-Execute · Glass-Box Core
 * Features: 3D Quantum Acoustic Orb, Web Audio Synthesizer, Live Visual DAG, Smart Home Digital Twin
 */

const $ = id => document.getElementById(id);
let sfxEnabled = true;
let ttsEnabled = true;
let isRecording = false;
let currentHomeState = null;
let orbState = "idle"; // "idle" | "listening" | "thinking" | "speaking"

// =============================================================================
// 1. Synthesized Web Audio Spatial Sound Effects (Pure Native AudioContext)
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
    // Ultra-soft glass micro-click
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(1200, now);
    osc.frequency.exponentialRampToValueAtTime(300, now + 0.04);
    gain.gain.setValueAtTime(0.06, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.04);
  } else if (type === "wake") {
    // Alexa ambient wake chime (dual harmonic)
    [523.25, 659.25, 783.99].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + idx * 0.06);
      gain.gain.setValueAtTime(0.08, now + idx * 0.06);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.28);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.06);
      osc.stop(now + idx * 0.06 + 0.28);
    });
  } else if (type === "approve") {
    // Celebratory harmonic resolution
    [440, 554.37, 659.25, 880].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, now + idx * 0.08);
      gain.gain.setValueAtTime(0.09, now + idx * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.08);
      osc.stop(now + idx * 0.08 + 0.35);
    });
  } else if (type === "alert") {
    // Sentinel security block alert (deep sub-buzz)
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(110, now);
    osc.frequency.linearRampToValueAtTime(55, now + 0.25);
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.25);
  }
}

// =============================================================================
// 2. Quantum Acoustic 3D Particle Orb Canvas Engine
// =============================================================================
function initQuantumOrb() {
  const canvas = $("orbCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  const cx = W / 2;
  const cy = H / 2;

  const NUM_PARTICLES = 120;
  const particles = [];

  for (let i = 0; i < NUM_PARTICLES; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos((Math.random() * 2) - 1);
    const radius = 28 + Math.random() * 8;
    particles.push({
      x: 0, y: 0, z: 0,
      baseRadius: radius,
      theta,
      phi,
      speed: 0.015 + Math.random() * 0.02,
      size: 1.2 + Math.random() * 1.8,
      hue: Math.random() > 0.4 ? 186 : 245 // Cyan or Indigo
    });
  }

  let angleY = 0;
  let angleX = 0;

  function render() {
    ctx.clearRect(0, 0, W, H);

    // Dynamic rotation speeds by orb state
    let rotSpeed = 0.015;
    let pulseScale = 1.0;
    const t = Date.now() * 0.003;

    if (orbState === "listening") {
      rotSpeed = 0.04;
      pulseScale = 1.15 + Math.sin(t * 3) * 0.12;
    } else if (orbState === "thinking") {
      rotSpeed = 0.08;
      pulseScale = 1.25 + Math.sin(t * 5) * 0.15;
    } else if (orbState === "speaking") {
      rotSpeed = 0.03;
      pulseScale = 1.1 + Math.sin(t * 4) * 0.18;
    } else {
      pulseScale = 1.0 + Math.sin(t) * 0.04;
    }

    angleY += rotSpeed;
    angleX += rotSpeed * 0.6;

    // Draw central ambient glow core
    const radGlow = ctx.createRadialGradient(cx, cy, 2, cx, cy, 26 * pulseScale);
    if (orbState === "thinking") {
      radGlow.addColorStop(0, "rgba(236, 72, 153, 0.85)");
      radGlow.addColorStop(0.5, "rgba(139, 92, 246, 0.5)");
      radGlow.addColorStop(1, "rgba(3, 7, 18, 0)");
    } else if (orbState === "listening") {
      radGlow.addColorStop(0, "rgba(0, 240, 255, 0.95)");
      radGlow.addColorStop(0.6, "rgba(59, 130, 246, 0.5)");
      radGlow.addColorStop(1, "rgba(3, 7, 18, 0)");
    } else {
      radGlow.addColorStop(0, "rgba(0, 240, 255, 0.75)");
      radGlow.addColorStop(0.6, "rgba(99, 102, 241, 0.45)");
      radGlow.addColorStop(1, "rgba(3, 7, 18, 0)");
    }

    ctx.fillStyle = radGlow;
    ctx.beginPath();
    ctx.arc(cx, cy, 26 * pulseScale, 0, Math.PI * 2);
    ctx.fill();

    // 3D Spherical projection for particles
    particles.forEach(p => {
      p.theta += p.speed;
      const r = p.baseRadius * pulseScale;
      let px = r * Math.sin(p.phi) * Math.cos(p.theta);
      let py = r * Math.cos(p.phi);
      let pz = r * Math.sin(p.phi) * Math.sin(p.theta);

      // Y-axis rotation
      let cosY = Math.cos(angleY), sinY = Math.sin(angleY);
      let x1 = px * cosY - pz * sinY;
      let z1 = px * sinY + pz * cosY;

      // X-axis rotation
      let cosX = Math.cos(angleX), sinX = Math.sin(angleX);
      let y2 = py * cosX - z1 * sinX;
      let z2 = py * sinX + z1 * cosX;

      const fov = 140;
      const scale = fov / (fov + z2);
      const projX = cx + x1 * scale;
      const projY = cy + y2 * scale;
      const alpha = Math.max(0.15, Math.min(1.0, (z2 + 40) / 70));

      ctx.beginPath();
      ctx.arc(projX, projY, Math.max(0.8, p.size * scale), 0, Math.PI * 2);
      ctx.fillStyle = p.hue === 186 
        ? `rgba(0, 240, 255, ${alpha})`
        : `rgba(168, 85, 247, ${alpha})`;
      ctx.shadowColor = p.hue === 186 ? "#00f0ff" : "#a855f7";
      ctx.shadowBlur = 4 * scale;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    requestAnimationFrame(render);
  }

  render();
  $("orbContainer").onclick = () => {
    playSfx("click");
    orbState = orbState === "idle" ? "speaking" : "idle";
    setTimeout(() => { if (orbState === "speaking") orbState = "idle"; }, 3000);
  };
}

// =============================================================================
// 3. Alexa Voice Synthesis (SpeechSynthesis)
// =============================================================================
function speakAlexaText(text) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  // Strip markdown, bullet points, and code markers for natural speech
  const clean = String(text || "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/•/g, "")
    .replace(/\[.*?\]/g, "")
    .replace(/`.*?`/g, "")
    .replace(/https?:\/\/\S+/g, "")
    .trim();

  if (!clean) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.03;
  utterance.pitch = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => 
    v.lang.startsWith("en") && 
    (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Victoria") || v.name.includes("Zira"))
  );
  if (preferredVoice) utterance.voice = preferredVoice;

  utterance.onstart = () => { orbState = "speaking"; };
  utterance.onend = () => { orbState = "idle"; };
  utterance.onerror = () => { orbState = "idle"; };

  window.speechSynthesis.speak(utterance);
}

// Escape HTML utility
function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

// JSON Fetch helper
async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Fetch notice on ${endpoint}:`, err.message);
    return null;
  }
}

// =============================================================================
// 4. Conversational Chat Engine & Multi-Tool DAG Visualizer
// =============================================================================
function appendChatBubble(role, text, metadata = {}) {
  const viewport = $("chatViewport");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role === "user" ? "bubble-user" : "bubble-alexa"}`;

  const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const senderLabel = role === "user" ? "You" : (metadata.model ? `Alexa+ (${metadata.model})` : "Alexa+ Universal Core");

  let parsedBody = escapeHtml(text)
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/•/g, "&bull;");

  bubble.innerHTML = `
    <div class="bubble-header">
      <span>${senderLabel}</span>
      <div style="display: flex; align-items: center; gap: 8px;">
        ${role === "alexa" ? `<button class="btn-audio-speak" onclick="playSfx('click'); speakAlexaText('${text.replace(/'/g, "\\'")}')">🔊 Replay</button>` : ""}
        <span class="font-mono">${timeStr}</span>
      </div>
    </div>
    <div class="bubble-content"><p>${parsedBody}</p></div>
  `;

  viewport.appendChild(bubble);
  viewport.scrollTop = viewport.scrollHeight;
}

// Render Autonomous Multi-Tool DAG Node Graph
function renderDagFlowNodes(dagSteps) {
  const dagCard = $("dagCard");
  const flowContainer = $("dagNodeFlow");
  if (!dagSteps || dagSteps.length === 0) {
    dagCard.style.display = "none";
    return;
  }

  dagCard.style.display = "block";
  flowContainer.innerHTML = dagSteps.map((step, idx) => {
    let statusClass = "status-completed";
    let icon = "✓";
    if (step.status === "blocked") {
      statusClass = "status-blocked";
      icon = "⛔";
    } else if (step.status === "gated") {
      statusClass = "status-gated";
      icon = "⏳";
    }

    const arrow = idx < dagSteps.length - 1 ? `<div class="node-arrow">➔</div>` : "";
    return `
      <div class="dag-node ${statusClass}" title="${escapeHtml(step.why)}" onclick="playSfx('click'); inspectDagStep('${escapeHtml(step.tool)}', '${escapeHtml(step.why)}', '${escapeHtml(step.status)}')">
        <div class="node-label">
          <span>${icon}</span>
          <span>${escapeHtml(step.tool)}</span>
        </div>
        <div class="node-subtext">${escapeHtml(step.why)}</div>
      </div>
      ${arrow}
    `;
  }).join("");
}

function inspectDagStep(tool, why, status) {
  alert(`⚡ Autonomous DAG Node Inspector\n\nTool: ${tool}\nStatus: ${status.toUpperCase()}\nRationale: ${why}\nContract: Propose-Never-Execute Enforced`);
}
window.inspectDagStep = inspectDagStep;

// Send User Prompt Flow
async function dispatchUserPrompt() {
  const input = $("userPromptInput");
  const promptText = input.value.trim();
  if (!promptText) return;

  playSfx("wake");
  input.value = "";
  appendChatBubble("user", promptText);

  orbState = "thinking";
  $("sendPromptBtn").disabled = true;
  $("sendPromptBtn").textContent = "Planning...";

  const provider = $("brainSelector").value;
  const startTime = Date.now();
  const res = await apiFetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: promptText, provider })
  });

  $("sendPromptBtn").disabled = false;
  $("sendPromptBtn").textContent = "Send";
  orbState = "idle";

  if (!res) {
    appendChatBubble("alexa", "Unable to establish connection to Hearth Universal MCP server (:8787). Please ensure server is running.");
    return;
  }

  // Update latency telemetry
  const latency = res.latency_ms || (Date.now() - startTime);
  $("latencyTelemetryBadge").textContent = `Latency: ${latency}ms · ${res.provider || "local"}`;

  // Check if Sentinel blocked an adversarial prompt
  if (res.blocked) {
    playSfx("alert");
  } else {
    playSfx("click");
  }

  // Render Visual DAG Nodes
  renderDagFlowNodes(res.dag);

  // Output Alexa synthesized response & trigger audio
  appendChatBubble("alexa", res.draft, { model: res.model });
  speakAlexaText(res.draft);

  // Refresh multi-modal telemetry
  refreshTelemetry();

  // If proposals created, auto-switch to Approval Tray tab
  if (res.proposals_created && res.proposals_created.length > 0) {
    switchControlTab("trayStage");
  }
}

function triggerQuickPrompt(text) {
  playSfx("click");
  $("userPromptInput").value = text;
  dispatchUserPrompt();
}
window.triggerQuickPrompt = triggerQuickPrompt;

// Setup Speech Recognition
function setupSpeechDictation() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    $("micCaptureBtn").title = "Web Speech Recognition not available in this browser";
    $("micCaptureBtn").style.opacity = "0.5";
    return;
  }

  const rec = new SpeechRec();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = "en-US";

  rec.onstart = () => {
    isRecording = true;
    orbState = "listening";
    $("micCaptureBtn").classList.add("recording");
    playSfx("wake");
  };

  rec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    $("userPromptInput").value = transcript;
    dispatchUserPrompt();
  };

  rec.onerror = () => {
    isRecording = false;
    orbState = "idle";
    $("micCaptureBtn").classList.remove("recording");
  };

  rec.onend = () => {
    isRecording = false;
    orbState = "idle";
    $("micCaptureBtn").classList.remove("recording");
  };

  $("micCaptureBtn").onclick = () => {
    if (isRecording) {
      rec.stop();
    } else {
      rec.start();
    }
  };
}

// =============================================================================
// 5. Consequential Proposal Decision Studio
// =============================================================================
async function commitProposalDecision(pid, approved) {
  if (approved) {
    playSfx("approve");
  } else {
    playSfx("click");
  }

  const res = await apiFetch("/api/decide", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: pid, approved })
  });

  if (res && res.status) {
    const actionLabel = approved ? "Approved" : "Rejected";
    appendChatBubble("alexa", `✓ Proposal **${pid}** has been ${actionLabel.toLowerCase()}. Changes were recorded in the immutable SHA-256 Merkle chain.`);
    refreshTelemetry();
  }
}
window.commitProposalDecision = commitProposalDecision;

// =============================================================================
// 6. Multi-Modal Telemetry & Digital Twin Synchronization
// =============================================================================
async function refreshTelemetry() {
  // 1. Health & Protocol Status
  const health = await apiFetch("/health");
  if (health) {
    $("mcpProtocolBadge").textContent = `MCP: ${health.protocol} Streamable HTTP`;
    $("merkleBadge").textContent = `SHA-256 Ledger: ${health.audit_ok ? "100% VALID" : "CORRUPT"}`;
    $("merkleBadge").className = `status-pill ${health.audit_ok ? "live-green" : "live-cyan"}`;
    $("merkleBadge").style.color = health.audit_ok ? "#34d399" : "#ef4444";
    $("activeEnginePill").textContent = `Engine: ${health.active_provider || "Intelligent Core"}`;
  }

  // 2. Glass-box Approval Tray Contracts
  const propData = await apiFetch("/api/proposals");
  if (propData && propData.proposals) {
    const pending = propData.proposals.filter(p => p.status === "pending");
    $("pendingTrayBadge").textContent = pending.length;

    if (propData.proposals.length === 0) {
      $("contractsList").innerHTML = `
        <div style="text-align: center; color: var(--text-tertiary); padding: 50px 0;">
          No pending action proposals. Ask Alexa+ to <i>"Save me $437 on renewals"</i> or <i>"Reorder coffee"</i> to generate action drafts.
        </div>
      `;
    } else {
      const reversed = [...propData.proposals].reverse();
      $("contractsList").innerHTML = reversed.map(p => {
        const isPending = p.status === "pending";
        const isApproved = p.status === "approved";

        let financialPill = "";
        if (p.cost_delta_yr > 0) {
          financialPill = `<span class="status-pill live-green font-mono">+$${p.cost_delta_yr.toFixed(2)}/yr Saved</span>`;
        } else if (p.cost_delta_yr < 0) {
          financialPill = `<span class="status-pill live-cyan font-mono">$${Math.abs(p.cost_delta_yr).toFixed(2)} Cart</span>`;
        }

        const statusTag = isPending
          ? `<span class="status-pill font-mono" style="background: rgba(245,158,11,0.15); color: #f59e0b; border-color: rgba(245,158,11,0.3);">Pending Human Tap</span>`
          : (isApproved
              ? `<span class="status-pill live-green font-mono">Approved</span>`
              : `<span class="status-pill font-mono" style="background: rgba(239,68,68,0.15); color: #f87171;">Rejected</span>`);

        return `
          <div class="contract-card">
            <div class="contract-header">
              <div>
                <div class="contract-title">${escapeHtml(p.title)}</div>
                <div class="contract-id-badge font-mono">Proposal ID: ${escapeHtml(p.id)} · Risk: ${escapeHtml(p.risk_level || 'Tier-2')}</div>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                ${financialPill}
                ${statusTag}
              </div>
            </div>
            <div class="diff-box">${escapeHtml(p.diff || p.reasons)}</div>
            <div class="contract-reasoning">${escapeHtml(p.reasons)}</div>
            ${isPending ? `
              <div class="contract-action-bar">
                <button class="btn-approve-quantum" onclick="commitProposalDecision('${escapeHtml(p.id)}', true)">✓ Approve Action</button>
                <button class="btn-reject-quantum" onclick="commitProposalDecision('${escapeHtml(p.id)}', false)">✕ Reject</button>
              </div>
            ` : `<div style="font-size: 11px; color: var(--text-tertiary);" class="font-mono">Decided at ${new Date(p.decided_at * 1000).toLocaleTimeString()}</div>`}
          </div>
        `;
      }).join("");
    }
  }

  // 3. Smart Home Living Digital Twin
  const homeData = await apiFetch("/api/home");
  if (homeData) {
    currentHomeState = homeData;
    const living = homeData.living_room || {};
    const bedroom = homeData.master_bedroom || {};
    const entryway = homeData.entryway || {};
    const kitchen = homeData.kitchen || {};
    const energy = homeData.energy || {};

    // Living Room
    if (living.lights) {
      $("livingBriLabel").textContent = `${living.lights.bri}% ${living.lights.color_temp || 'Warm'}`;
      $("livingBriSlider").value = living.lights.bri;
      // Ambient specular glow on card
      const alpha = living.lights.on ? (living.lights.bri / 100) * 0.25 : 0;
      $("livingRoomCard").style.boxShadow = `0 8px 32px rgba(255, 179, 102, ${alpha})`;
    }
    if (living.climate) {
      $("livingTempDisplay").textContent = `${living.climate.target_c}°C`;
    }

    // Bedroom
    if (bedroom.lights) {
      $("bedroomBriLabel").textContent = bedroom.lights.on ? `${bedroom.lights.bri}% Warm` : "0% Off";
      $("bedroomBriSlider").value = bedroom.lights.bri;
    }
    if (bedroom.climate) {
      $("bedroomTempDisplay").textContent = `${bedroom.climate.target_c}°C`;
    }

    // Smart Lock
    if (entryway.lock) {
      const isLocked = entryway.lock.front_door === "locked";
      $("lockStatusPill").textContent = isLocked ? "LOCKED" : "UNLOCKED";
      $("lockStatusPill").className = isLocked ? "status-pill live-green font-mono" : "status-pill live-cyan font-mono";
      $("lockEventDetail").textContent = entryway.lock.last_event || (isLocked ? "Perimeter securely locked" : "Perimeter unlocked via human tap");
    }

    // Kitchen
    if (kitchen.appliances) {
      $("coffeeMakerStatus").textContent = (kitchen.appliances.coffee_maker || "standby").toUpperCase();
    }

    // Energy Telemetry
    if (energy) {
      $("loadKwMetric").textContent = `${energy.current_draw_kw || 1.45} kW`;
      $("solarKwMetric").textContent = `${energy.solar_generation_kw || 0.85} kW`;
    }
  }

  // 4. Subscriptions & Consumable Commerce
  const renData = await apiFetch("/api/renewals");
  if (renData && renData.renewals) {
    $("subsListing").innerHTML = renData.renewals.map(s => {
      let recPill = "";
      if (s.recommendation === "cancel") recPill = `<span class="status-pill" style="color: #f87171; border-color: rgba(239,68,68,0.3);">Rec: Cancel</span>`;
      else if (s.recommendation === "downgrade") recPill = `<span class="status-pill" style="color: #f59e0b; border-color: rgba(245,158,11,0.3);">Rec: Downgrade</span>`;
      else recPill = `<span class="status-pill live-green">Keep</span>`;

      return `
        <div class="commerce-item-tile">
          <div>
            <div style="font-size: 14px; font-weight: 700; color: #ffffff;">${escapeHtml(s.name)}</div>
            <div style="font-size: 12px; color: var(--text-secondary);">$${s.cost_yr}/yr · ${escapeHtml(s.usage_status)}</div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            ${recPill}
            ${s.recommendation !== "keep" ? `<button class="btn-ambient" onclick="playSfx('click'); triggerQuickPrompt('Propose ${s.recommendation} for ${escapeHtml(s.name)}')">Propose</button>` : ""}
          </div>
        </div>
      `;
    }).join("");
  }

  const comData = await apiFetch("/api/commerce");
  if (comData && comData.inventory) {
    $("pantryListing").innerHTML = comData.inventory.map(item => {
      const isCritical = item.status === "critical";
      const isLow = item.status === "low";
      const fillColor = isCritical ? "#ef4444" : (isLow ? "#f59e0b" : "#34d399");

      return `
        <div class="commerce-item-tile">
          <div>
            <div style="font-size: 14px; font-weight: 700; color: #ffffff;">${escapeHtml(item.name)}</div>
            <div style="font-size: 11px; color: var(--text-secondary);">${escapeHtml(item.category)} · Level: ${item.level_pct}%</div>
            <div class="pantry-progress-track">
              <div class="pantry-progress-fill" style="width: ${item.level_pct}%; background: ${fillColor};"></div>
            </div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span class="status-pill font-mono" style="color: ${fillColor}; border-color: ${fillColor}40;">${item.status.toUpperCase()}</span>
            ${(isLow || isCritical) ? `<button class="btn-ambient" onclick="playSfx('click'); triggerQuickPrompt('Reorder ${escapeHtml(item.name)}')">Reorder</button>` : ""}
          </div>
        </div>
      `;
    }).join("");
  }

  if (comData && comData.deals) {
    $("dealsListing").innerHTML = comData.deals.map(deal => `
      <div class="commerce-item-tile">
        <div>
          <div style="font-size: 14px; font-weight: 700; color: var(--alexa-cyan);">${escapeHtml(deal.title)}</div>
          <div style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(deal.items.join(" + "))} · Saves $${deal.savings}</div>
        </div>
        <button class="btn-approve-quantum" onclick="playSfx('click'); triggerQuickPrompt('Draft proposal for bundle deal: ${escapeHtml(deal.title)}')">Draft Deal</button>
      </div>
    `).join("");
  }

  // 5. Persistent Memory Facts
  const memData = await apiFetch("/api/memory");
  if (memData && memData.facts) {
    $("factsListing").innerHTML = memData.facts.map(f => `
      <div class="commerce-item-tile">
        <div>
          <span style="font-weight: 700; color: #ffffff;">${escapeHtml(f.key)}:</span>
          <span style="color: var(--text-secondary); margin-left: 6px;">${escapeHtml(f.value)}</span>
        </div>
        <span class="status-pill font-mono">${escapeHtml(f.owner || 'household')}</span>
      </div>
    `).join("");
  }

  // 6. Goals Listing
  const goalsData = await apiFetch("/api/goals");
  if (goalsData && goalsData.goals) {
    $("goalsListing").innerHTML = goalsData.goals.map(g => `
      <div class="commerce-item-tile">
        <div>
          <div style="font-size: 14px; font-weight: 700; color: #ffffff;">${escapeHtml(g.title)}</div>
          <div style="font-size: 12px; color: var(--text-secondary);">Progress: Step ${g.progress} of ${g.steps.length} · Status: ${g.status.toUpperCase()}</div>
        </div>
        <button class="btn-ambient" onclick="playSfx('click'); triggerQuickPrompt('advance goal ${g.id}')">Advance</button>
      </div>
    `).join("");
  }
}

// =============================================================================
// 7. Interactive Scene, Device & Lock Dispatchers
// =============================================================================
async function dispatchScene(name) {
  playSfx("click");
  document.querySelectorAll(".btn-scene-card").forEach(btn => {
    btn.classList.toggle("active-scene", btn.textContent.toLowerCase().includes(name.replace('-', ' ')));
  });

  await apiFetch("/api/home/scene", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  appendChatBubble("alexa", `Coordinated smart home scene **'${name}'** applied across your living digital twin.`);
  refreshTelemetry();
}
window.dispatchScene = dispatchScene;

async function alterClimate(room, delta) {
  playSfx("click");
  if (!currentHomeState || !currentHomeState[room]) return;
  const current = currentHomeState[room].climate.target_c || 21.5;
  const newTarget = Math.round((current + delta) * 10) / 10;

  await apiFetch("/api/home/device", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room,
      device: "climate",
      patch: { target_c: newTarget }
    })
  });
  refreshTelemetry();
}
window.alterClimate = alterClimate;

async function togglePerimeterLock() {
  playSfx("click");
  const isLocked = currentHomeState?.entryway?.lock?.front_door === "locked";
  await apiFetch("/api/home/lock", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ locked: !isLocked })
  });
  refreshTelemetry();
}
window.togglePerimeterLock = togglePerimeterLock;

async function persistFactAction() {
  playSfx("click");
  const key = $("addFactKeyInput").value.trim();
  const val = $("addFactValInput").value.trim();
  if (!key || !val) return;

  await apiFetch("/api/memory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value: val, owner: "household" })
  });

  $("addFactKeyInput").value = "";
  $("addFactValInput").value = "";
  refreshTelemetry();
}
window.persistFactAction = persistFactAction;

// =============================================================================
// 8. Cryptographic Merkle Ledger Explorer Modal
// =============================================================================
async function openMerkleModal() {
  playSfx("click");
  const modal = $("auditModalDialog");
  const data = await apiFetch("/api/audit");
  if (data && data.recent) {
    $("modalVerifyPill").textContent = data.valid ? "Integrity: 100% VALID" : "Integrity: CORRUPTED";
    $("modalVerifyPill").className = data.valid ? "status-pill live-green font-mono" : "status-pill font-mono";
    $("modalVerifyPill").style.color = data.valid ? "#34d399" : "#ef4444";

    $("merkleTableBody").innerHTML = data.recent.map(e => `
      <tr>
        <td class="font-mono">${new Date(e.ts * 1000).toLocaleTimeString()}</td>
        <td><span class="status-pill font-mono" style="padding: 2px 8px; font-size: 11px;">${escapeHtml(e.actor)}</span></td>
        <td style="font-weight: 600;">${escapeHtml(e.action)}</td>
        <td style="color: var(--alexa-cyan);">${escapeHtml((e.hash || '').substring(0, 16))}...</td>
      </tr>
    `).join("");
  }
  modal.showModal();
}

// Switch Control Studio Tab
function switchControlTab(tabId) {
  playSfx("click");
  document.querySelectorAll(".control-tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-stage-content").forEach(content => {
    content.style.display = content.id === tabId ? "block" : "none";
  });
}

// =============================================================================
// 9. Initialization & Event Bindings
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initQuantumOrb();

  $("sendPromptBtn").onclick = dispatchUserPrompt;
  $("userPromptInput").addEventListener("keydown", e => {
    if (e.key === "Enter") dispatchUserPrompt();
  });

  $("auditModalTriggerBtn").onclick = openMerkleModal;

  $("sfxToggleBtn").onclick = () => {
    sfxEnabled = !sfxEnabled;
    $("sfxToggleBtn").textContent = sfxEnabled ? "🔊 SFX: ON" : "🔇 SFX: OFF";
    $("sfxToggleBtn").style.color = sfxEnabled ? "var(--text-primary)" : "var(--text-tertiary)";
    if (sfxEnabled) playSfx("click");
  };

  $("ttsToggleBtn").onclick = () => {
    ttsEnabled = !ttsEnabled;
    $("ttsToggleBtn").textContent = ttsEnabled ? "🗣️ Voice: ON" : "🔇 Voice: OFF";
    $("ttsToggleBtn").style.color = ttsEnabled ? "var(--text-primary)" : "var(--text-tertiary)";
    playSfx("click");
  };

  $("resetSystemBtn").onclick = async () => {
    playSfx("click");
    await apiFetch("/api/reset", { method: "POST" });
    appendChatBubble("alexa", "🧹 Household digital twin, approval tray, and device states have been reset to factory baseline.");
    refreshTelemetry();
  };

  $("livingBriSlider").addEventListener("change", (e) => {
    const val = parseInt(e.target.value, 10);
    apiFetch("/api/home/device", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room: "living_room",
        device: "lights",
        patch: { bri: val, on: val > 0 }
      })
    }).then(refreshTelemetry);
  });

  $("bedroomBriSlider").addEventListener("change", (e) => {
    const val = parseInt(e.target.value, 10);
    apiFetch("/api/home/device", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room: "master_bedroom",
        device: "lights",
        patch: { bri: val, on: val > 0 }
      })
    }).then(refreshTelemetry);
  });

  $("dagToggleHeader").onclick = () => {
    playSfx("click");
    const flow = $("dagNodeFlow");
    const isHidden = flow.style.display === "none";
    flow.style.display = isHidden ? "flex" : "none";
    $("dagChevronIcon").textContent = isHidden ? "▼" : "▶";
  };

  document.querySelectorAll(".control-tab-btn").forEach(btn => {
    btn.onclick = () => switchControlTab(btn.dataset.tab);
  });

  setupSpeechDictation();
  refreshTelemetry();
  setInterval(refreshTelemetry, 5000);
});
