/**
 * Hearth Universal — Alexa+ Simulated Experience Client
 * Connects to MCP 2025-11-25 Streamable HTTP server on :8787
 * Supports multi-modal voice, DAG orchestration visualizer, and glass-box approval tray.
 */

const $ = id => document.getElementById(id);
let ttsEnabled = true;
let isRecording = false;
let currentHomeState = null;

// Escape HTML utility
function esc(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

// JSON Fetch helper
async function fetchJson(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`Fetch error on ${url}:`, err);
    return null;
  }
}

// Speech Synthesis (Alexa voice response)
function speakAlexa(text) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  
  // Clean markdown syntax for speech
  const cleanText = text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/•/g, "")
    .replace(/\[.*?\]/g, "")
    .trim();

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  
  const voices = window.speechSynthesis.getVoices();
  const naturalVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha")));
  if (naturalVoice) utterance.voice = naturalVoice;

  const orb = $("alexaOrb");
  utterance.onstart = () => orb.classList.add("pulsing");
  utterance.onend = () => orb.classList.remove("pulsing");
  utterance.onerror = () => orb.classList.remove("pulsing");

  window.speechSynthesis.speak(utterance);
}

// Append Chat Message
function appendMessage(role, text, metadata = {}) {
  const box = $("chatBox");
  const msg = document.createElement("div");
  msg.className = `chat-msg ${role === "user" ? "msg-user" : "msg-alexa"}`;
  
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const senderName = role === "user" ? "You" : (metadata.model ? `Alexa+ (${metadata.model})` : "Alexa+");

  // Format markdown-like text to HTML
  let formatted = esc(text)
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/•/g, "&bull;");

  msg.innerHTML = `
    <div class="msg-header">
      <span>${senderName}</span>
      <div style="display: flex; align-items: center; gap: 8px;">
        ${role === "alexa" ? `<button class="msg-tts-btn" data-say="1">🔊 Replay</button>` : ""}
        <span>${now}</span>
      </div>
    </div>
    <div class="msg-content"><p>${formatted}</p></div>
  `;

  // Closure-based listener: brain text never touches HTML markup (XSS-safe).
  msg.querySelector('[data-say]')?.addEventListener('click', () => speakAlexa(text));

  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
}

// Display ReAct / DAG Orchestration Flow
function renderDagFlow(dagSteps, goal) {
  const dagBox = $("dagBox");
  const stepsContainer = $("dagSteps");
  if (!dagSteps || dagSteps.length === 0) {
    dagBox.style.display = "none";
    return;
  }

  dagBox.style.display = "block";
  stepsContainer.innerHTML = dagSteps.map(step => {
    let icon = "✓";
    let color = "#34d399";
    if (step.status === "blocked") {
      icon = "⛔";
      color = "#ef4444";
    } else if (step.status === "gated") {
      icon = "⏳";
      color = "#f59e0b";
    }
    return `
      <div class="dag-step">
        <span class="dag-step-icon" style="color: ${color}; font-weight: 700;">${icon}</span>
        <span style="font-weight: 600; color: #f8fafc;">${esc(step.tool)}:</span>
        <span>${esc(step.why)}</span>
      </div>
    `;
  }).join("");
}

// Send Message Flow
async function handleSend() {
  const input = $("userInput");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  appendMessage("user", text);
  
  const orb = $("alexaOrb");
  orb.classList.add("pulsing");
  $("sendBtn").disabled = true;
  $("sendBtn").textContent = "Planning...";

  const provider = $("brainSelect").value;
  const res = await fetchJson("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, provider })
  });

  orb.classList.remove("pulsing");
  $("sendBtn").disabled = false;
  $("sendBtn").textContent = "Send";

  if (!res) {
    appendMessage("alexa", "Unable to connect to Hearth Universal MCP server. Please ensure `python mcp-server/server.py` is running on :8787.");
    return;
  }

  // Update latency badge
  if (res.latency_ms) {
    $("latencySpan").textContent = `Latency: ${res.latency_ms}ms · ${res.provider || "local"}`;
  }

  // Render multi-tool DAG flow
  renderDagFlow(res.dag, res.goal);

  // Append Alexa response
  appendMessage("alexa", res.draft, { model: res.model });
  speakAlexa(res.draft);

  // Refresh multi-modal dashboards
  refreshAll();

  // If proposals created, auto-switch to Tray tab
  if (res.proposals_created && res.proposals_created.length > 0) {
    switchTab("tabTray");
  }
}

// Quick Prompt Chips
function quickPrompt(text) {
  $("userInput").value = text;
  handleSend();
}
window.quickPrompt = quickPrompt;

// Speech-to-Text Recognition
function setupSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    $("micBtn").title = "Voice recognition not supported in this browser";
    $("micBtn").style.opacity = "0.5";
    return;
  }

  const rec = new SpeechRec();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = "en-US";

  rec.onstart = () => {
    isRecording = true;
    $("micBtn").classList.add("recording");
    $("alexaOrb").classList.add("pulsing");
  };

  rec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    $("userInput").value = transcript;
    handleSend();
  };

  rec.onerror = () => {
    isRecording = false;
    $("micBtn").classList.remove("recording");
    $("alexaOrb").classList.remove("pulsing");
  };

  rec.onend = () => {
    isRecording = false;
    $("micBtn").classList.remove("recording");
    $("alexaOrb").classList.remove("pulsing");
  };

  $("micBtn").onclick = () => {
    if (isRecording) {
      rec.stop();
    } else {
      rec.start();
    }
  };
}

// Proposal Tray Decision
async function decideProposal(pid, approved) {
  const res = await fetchJson("/api/decide", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: pid, approved })
  });

  if (res && res.status) {
    const actionWord = approved ? "Approved" : "Rejected";
    appendMessage("alexa", `✓ Proposal **${pid}** has been ${actionWord.toLowerCase()}. Changes were recorded in the immutable SHA-256 audit ledger.`);
    refreshAll();
  }
}
window.decideProposal = decideProposal;

// Refresh All UI State
async function refreshAll() {
  // 1. Health & MCP Status
  const health = await fetchJson("/health");
  if (health) {
    $("mcpStatus").textContent = `MCP: ${health.protocol}`;
    $("ledgerBadge").textContent = `SHA-256 Ledger: ${health.audit_ok ? "Verified OK" : "CORRUPT"}`;
    $("ledgerBadge").style.color = health.audit_ok ? "#34d399" : "#ef4444";
  }

  // 2. Proposals Tray
  const propData = await fetchJson("/api/proposals");
  if (propData && propData.proposals) {
    const pending = propData.proposals.filter(p => p.status === "pending");
    $("trayCountBadge").textContent = pending.length;
    
    if (propData.proposals.length === 0) {
      $("trayContainer").innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 40px 0;">
          No pending proposals. Ask Alexa+ to <i>"Save me money"</i> or <i>"Set up movie night"</i> to generate action drafts.
        </div>
      `;
    } else {
      const sorted = [...propData.proposals].reverse();
      $("trayContainer").innerHTML = sorted.map(p => {
        const isPending = p.status === "pending";
        const isApproved = p.status === "approved";
        
        let costBadge = "";
        if (p.cost_delta_yr > 0) {
          costBadge = `<span class="badge" style="background: rgba(16,185,129,0.15); color: #34d399;">+$${p.cost_delta_yr.toFixed(2)}/yr Saved</span>`;
        } else if (p.cost_delta_yr < 0) {
          costBadge = `<span class="badge" style="background: rgba(56,189,248,0.15); color: #38bdf8;">$${Math.abs(p.cost_delta_yr).toFixed(2)} Total</span>`;
        }

        const statusTag = isPending
          ? `<span class="badge" style="background: rgba(245,158,11,0.15); color: #f59e0b;">Pending Human Tap</span>`
          : (isApproved
              ? `<span class="badge badge-live">Approved</span>`
              : `<span class="badge" style="background: rgba(239,68,68,0.15); color: #f87171;">Rejected</span>`);

        return `
          <div class="proposal-card">
            <div class="proposal-top">
              <div>
                <div class="proposal-title">${esc(p.title)}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">ID: ${esc(p.id)} · Risk: ${esc(p.risk_level || 'Tier-2')}</div>
              </div>
              <div style="display: flex; gap: 6px; align-items: center;">
                ${costBadge}
                ${statusTag}
              </div>
            </div>
            <div class="proposal-diff">${esc(p.diff || p.reasons)}</div>
            <div class="proposal-reason">${esc(p.reasons)}</div>
            ${isPending ? `
              <div class="proposal-actions">
                <button class="btn-approve" onclick="decideProposal('${esc(p.id)}', true)">✓ Approve Action</button>
                <button class="btn-reject" onclick="decideProposal('${esc(p.id)}', false)">✕ Reject</button>
              </div>
            ` : `<div style="font-size: 11px; color: var(--text-muted);">Decided at ${new Date(p.decided_at * 1000).toLocaleTimeString()}</div>`}
          </div>
        `;
      }).join("");
    }
  }

  // 3. Smart Home Digital Twin
  const homeData = await fetchJson("/api/home");
  if (homeData) {
    currentHomeState = homeData;
    const living = homeData.living_room || {};
    const entryway = homeData.entryway || {};
    const energy = homeData.energy || {};

    if (living.lights) {
      $("livingLightBadge").textContent = `${living.lights.bri}% ${living.lights.color_temp || 'Warm'}`;
      $("livingLightSlider").value = living.lights.bri;
    }
    if (living.climate) {
      $("climateBadge").textContent = `${living.climate.target_c}°C (${living.climate.mode})`;
    }
    if (entryway.lock) {
      const isLocked = entryway.lock.front_door === "locked";
      $("lockStatusBadge").textContent = isLocked ? "LOCKED" : "UNLOCKED";
      $("lockStatusBadge").className = isLocked ? "badge badge-live" : "badge badge-cyan";
      $("lockEventText").textContent = entryway.lock.last_event || "";
    }
    if (energy) {
      $("energyDraw").textContent = `${energy.current_draw_kw || 1.45} kW`;
      $("energySolar").textContent = `${energy.solar_generation_kw || 0.85} kW`;
    }
  }

  // 4. Subscriptions & Commerce
  const renData = await fetchJson("/api/renewals");
  if (renData && renData.renewals) {
    $("subsContainer").innerHTML = renData.renewals.map(s => {
      let recBadge = "";
      if (s.recommendation === "cancel") recBadge = `<span class="badge" style="color: #f87171;">Rec: Cancel</span>`;
      else if (s.recommendation === "downgrade") recBadge = `<span class="badge" style="color: #f59e0b;">Rec: Downgrade</span>`;
      else recBadge = `<span class="badge badge-live">Keep</span>`;

      return `
        <div class="commerce-row">
          <div>
            <div style="font-size: 13px; font-weight: 700; color: #ffffff;">${esc(s.name)}</div>
            <div style="font-size: 11px; color: var(--text-muted);">$${s.cost_yr}/yr · ${esc(s.usage_status)}</div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            ${recBadge}
            ${s.recommendation !== "keep" ? `<button class="btn-header" onclick="quickPrompt('Propose ${s.recommendation} for ${esc(s.name)}')">Propose</button>` : ""}
          </div>
        </div>
      `;
    }).join("");
  }

  const comData = await fetchJson("/api/commerce");
  if (comData && comData.inventory) {
    $("inventoryContainer").innerHTML = comData.inventory.map(item => {
      const isLow = item.status === "low" || item.status === "critical";
      const badgeStyle = isLow ? "background: rgba(239,68,68,0.15); color: #f87171;" : "color: #34d399;";
      return `
        <div class="commerce-row">
          <div>
            <div style="font-size: 13px; font-weight: 600;">${esc(item.name)}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${esc(item.category)} · Level: ${item.level_pct}%</div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span class="badge" style="${badgeStyle}">${esc(item.status.toUpperCase())}</span>
            ${isLow ? `<button class="btn-header" onclick="quickPrompt('Reorder ${esc(item.name)}')">Order</button>` : ""}
          </div>
        </div>
      `;
    }).join("");
  }

  if (comData && comData.deals) {
    $("dealsContainer").innerHTML = comData.deals.map(deal => `
      <div class="commerce-row">
        <div>
          <div style="font-size: 13px; font-weight: 600; color: #38bdf8;">${esc(deal.title)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">${esc(deal.items.join(" + "))} · Saves $${deal.savings}</div>
        </div>
        <button class="btn-approve" onclick="quickPrompt('Draft proposal for bundle deal: ${esc(deal.title)}')">Draft Deal</button>
      </div>
    `).join("");
  }

  // 5. Memory Facts
  const memData = await fetchJson("/api/memory");
  if (memData && memData.facts) {
    $("factsContainer").innerHTML = memData.facts.map(f => `
      <div class="commerce-row">
        <div>
          <span style="font-weight: 700; color: #ffffff;">${esc(f.key)}:</span>
          <span style="color: var(--text-muted); margin-left: 6px;">${esc(f.value)}</span>
        </div>
        <span class="badge">${esc(f.owner || 'household')}</span>
      </div>
    `).join("");
  }
}

// Scene & Climate controls
async function applyScene(name) {
  await fetchJson("/api/home/scene", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  appendMessage("alexa", `Scene **'${name}'** applied across smart home digital twin.`);
  refreshAll();
}
window.applyScene = applyScene;

async function adjustClimate(delta) {
  if (!currentHomeState || !currentHomeState.living_room) return;
  const current = currentHomeState.living_room.climate.target_c || 21.5;
  const newTarget = Math.round((current + delta) * 10) / 10;
  
  await fetchJson("/api/home/device", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room: "living_room",
      device: "climate",
      patch: { target_c: newTarget }
    })
  });
  refreshAll();
}
window.adjustClimate = adjustClimate;

async function toggleDoorLock() {
  const isCurrentlyLocked = currentHomeState?.entryway?.lock?.front_door === "locked";
  await fetchJson("/api/home/lock", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ locked: !isCurrentlyLocked })
  });
  refreshAll();
}
window.toggleDoorLock = toggleDoorLock;

async function addMemoryFact() {
  const key = $("newFactKey").value.trim();
  const val = $("newFactVal").value.trim();
  if (!key || !val) return;

  await fetchJson("/api/memory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value: val, owner: "household" })
  });

  $("newFactKey").value = "";
  $("newFactVal").value = "";
  refreshAll();
}
window.addMemoryFact = addMemoryFact;

// Audit Modal
async function openAuditModal() {
  const modal = $("auditModal");
  const data = await fetchJson("/api/audit");
  if (data && data.recent) {
    $("modalVerifyBadge").textContent = data.valid ? "Integrity: 100% VALID" : "Integrity: CORRUPTED";
    $("modalVerifyBadge").className = data.valid ? "badge badge-live" : "badge";
    $("modalVerifyBadge").style.color = data.valid ? "#34d399" : "#ef4444";

    $("auditTableBody").innerHTML = data.recent.map(e => `
      <tr>
        <td>${new Date(e.ts * 1000).toLocaleTimeString()}</td>
        <td><span class="badge">${esc(e.actor)}</span></td>
        <td>${esc(e.action)}</td>
        <td style="color: #38bdf8;">${esc((e.hash || '').substring(0, 16))}...</td>
      </tr>
    `).join("");
  }
  modal.showModal();
}

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-content").forEach(content => {
    content.style.display = content.id === tabId ? "block" : "none";
  });
}

// Initialize Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  $("sendBtn").onclick = handleSend;
  $("userInput").addEventListener("keydown", e => {
    if (e.key === "Enter") handleSend();
  });

  $("btnAuditModal").onclick = openAuditModal;

  $("btnTtsToggle").onclick = () => {
    ttsEnabled = !ttsEnabled;
    $("btnTtsToggle").textContent = ttsEnabled ? "🔊 Voice: ON" : "🔇 Voice: OFF";
    $("btnTtsToggle").style.color = ttsEnabled ? "#ffffff" : "var(--text-muted)";
  };

  $("btnResetDemo").onclick = async () => {
    await fetchJson("/api/reset", { method: "POST" });
    appendMessage("alexa", "🧹 Household digital twin and approval tray have been reset to default state.");
    refreshAll();
  };

  $("livingLightSlider").addEventListener("change", (e) => {
    const val = parseInt(e.target.value, 10);
    fetchJson("/api/home/device", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room: "living_room",
        device: "lights",
        patch: { bri: val, on: val > 0 }
      })
    }).then(refreshAll);
  });

  $("dagToggle").onclick = () => {
    const steps = $("dagSteps");
    const isHidden = steps.style.display === "none";
    steps.style.display = isHidden ? "flex" : "none";
    $("dagChevron").textContent = isHidden ? "▼" : "▶";
  };

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.onclick = () => switchTab(btn.dataset.tab);
  });

  setupSpeechRecognition();
  refreshAll();
  setInterval(refreshAll, 6000);
});
