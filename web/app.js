/**
 * Hearth Universal — Client Application
 * Modern Glass-Box Household Operations Agent Interface
 * Zero dependencies · Vanilla ES2024 · Accessible · Propose-Never-Execute Contract
 */

"use strict";

// =============================================================================
// 1. UTILITIES & HELPERS
// =============================================================================

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

/**
 * Escapes unsafe HTML characters to prevent XSS attacks.
 */
function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Formats a currency number into standard US Dollar format.
 */
function formatMoney(amount) {
  const n = Number(amount || 0);
  return "$" + n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Formats an epoch timestamp into human-readable local time.
 */
function formatTime(epochSec) {
  if (!epochSec) return "";
  try {
    const d = new Date(epochSec * 1000);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

/**
 * Lightweight Markdown Formatter (safe after initial escape).
 */
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

  // Bold formatting: **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  return html || "<p>—</p>";
}

/**
 * Interactive Toast Notification Shelf.
 */
function showToast(message, type = "info") {
  const shelf = $("toast-shelf");
  if (!shelf) return;

  const toast = document.createElement("div");
  toast.className = `toast-message ${type}`;
  toast.textContent = message;

  shelf.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3600);
}

// =============================================================================
// 2. SYNTHESIZED WEB AUDIO FEEDBACK (Chimes & UI Clicks)
// =============================================================================

let audioContext = null;
let soundEnabled = true;

function initAudio() {
  if (!audioContext && typeof AudioContext !== "undefined") {
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch {
      audioContext = null;
    }
  }
}

function playSound(type) {
  if (!soundEnabled) return;
  initAudio();
  if (!audioContext) return;

  if (audioContext.state === "suspended") {
    audioContext.resume().catch(() => {});
  }

  const now = audioContext.currentTime;

  if (type === "success") {
    // Warm Major Triad (F4 -> A4 -> C5)
    [349.23, 440.0, 523.25].forEach((freq, idx) => {
      const osc = audioContext.createOscillator();
      const gain = audioContext.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + idx * 0.08);

      gain.gain.setValueAtTime(0, now + idx * 0.08);
      gain.gain.linearRampToValueAtTime(0.12, now + idx * 0.08 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.35);

      osc.connect(gain);
      gain.connect(audioContext.destination);

      osc.start(now + idx * 0.08);
      osc.stop(now + idx * 0.08 + 0.36);
    });
  } else if (type === "alert") {
    // Gentle High Bell
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(659.25, now); // E5

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.15, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

    osc.connect(gain);
    gain.connect(audioContext.destination);

    osc.start(now);
    osc.stop(now + 0.42);
  } else if (type === "click") {
    // Subtle tactile pop
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.exponentialRampToValueAtTime(110, now + 0.04);

    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

    osc.connect(gain);
    gain.connect(audioContext.destination);

    osc.start(now);
    osc.stop(now + 0.045);
  }
}

// =============================================================================
// 3. API CLIENT LAYER
// =============================================================================

async function request(endpoint, options = {}) {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    throw new Error(`Server returned HTTP ${response.status}`);
  }

  if (!response.ok) {
    throw new Error(data?.error || `HTTP Error ${response.status}`);
  }

  return data;
}

const api = {
  get: (url) => request(url, { method: "GET" }),
  post: (url, body = {}) => request(url, { method: "POST", body: JSON.stringify(body) }),
  del: (url, body = {}) => request(url, { method: "DELETE", body: JSON.stringify(body) }),
};

// =============================================================================
// 4. SPEECH SYNTHESIS & RECOGNITION (ALEXA+ SIMULATOR)
// =============================================================================

let speechRecognizer = null;
let isRecognizing = false;

function setupVoiceRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = $("voiceMicBtn");
  const inputMicBtn = $("inputMicBtn");
  const alexaOrb = $("alexaOrb");

  if (!SpeechRec) {
    if (micBtn) micBtn.title = "Speech recognition not supported in this browser";
    if (inputMicBtn) inputMicBtn.title = "Speech recognition not supported in this browser";
    return;
  }

  const toggleRecognition = () => {
    if (isRecognizing && speechRecognizer) {
      speechRecognizer.stop();
      return;
    }

    try {
      speechRecognizer = new SpeechRec();
      speechRecognizer.continuous = false;
      speechRecognizer.interimResults = false;
      speechRecognizer.lang = "en-US";

      speechRecognizer.onstart = () => {
        isRecognizing = true;
        micBtn?.classList.add("active");
        inputMicBtn?.classList.add("active");
        alexaOrb?.classList.add("listening");
        showToast("Listening to voice command...", "info");
      };

      speechRecognizer.onresult = (evt) => {
        const transcript = evt.results[0][0].transcript;
        const input = $("chatInput");
        if (input) {
          input.value = transcript;
          submitChat();
        }
      };

      speechRecognizer.onerror = (err) => {
        showToast(`Voice error: ${err.error}`, "error");
      };

      speechRecognizer.onend = () => {
        isRecognizing = false;
        micBtn?.classList.remove("active");
        inputMicBtn?.classList.remove("active");
        alexaOrb?.classList.remove("listening");
      };

      speechRecognizer.start();
    } catch (e) {
      showToast("Could not start voice recognition: " + e.message, "error");
    }
  };

  micBtn?.addEventListener("click", toggleRecognition);
  inputMicBtn?.addEventListener("click", toggleRecognition);
}

function speakText(text) {
  if (!("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#`_]/g, "").slice(0, 320);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const orb = $("alexaOrb");
    utterance.onstart = () => orb?.classList.add("thinking");
    utterance.onend = () => orb?.classList.remove("thinking");
    utterance.onerror = () => orb?.classList.remove("thinking");

    window.speechSynthesis.speak(utterance);
  } catch {
    // Speech synthesis gracefully degraded
  }
}

// =============================================================================
// 5. LIVE CLOCK & TOP BAR STATE
// =============================================================================

function updateClock() {
  const display = $("clockDisplay");
  if (!display) return;
  const now = new Date();
  display.textContent = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
setInterval(updateClock, 1000);
updateClock();

async function refreshHealthAndLedger() {
  try {
    const health = await api.get("/health");
    const healthPill = $("healthPill");
    const healthLabel = $("healthLabel");
    const auditPill = $("auditPill");
    const brainLabel = $("activeBrainLabel");

    if (health.status === "ok") {
      healthPill?.classList.remove("warning", "danger");
      if (healthLabel) healthLabel.textContent = `MCP Online · ${health.tools_count} Tools`;
    } else {
      healthPill?.classList.add("warning");
      if (healthLabel) healthLabel.textContent = "Degraded";
    }

    if (auditPill) {
      auditPill.innerHTML = health.audit_ok
        ? "🔒 SHA-256 Valid"
        : "<span style='color:var(--rose)'>⚠️ Hash Chain Mismatch</span>";
    }

    if (brainLabel) {
      brainLabel.textContent = `Brain: ${health.active_provider || "Local Offline Engine"} · Protocol: ${health.protocol}`;
    }
  } catch {
    const healthPill = $("healthPill");
    const healthLabel = $("healthLabel");
    if (healthPill) healthPill.className = "status-badge danger";
    if (healthLabel) healthLabel.textContent = "Server Offline (:8787)";
  }
}

// Audio Toggle Button
$("audioToggleBtn")?.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  $("audioToggleBtn").textContent = soundEnabled ? "🔊 Sound On" : "🔇 Sound Muted";
  showToast(soundEnabled ? "Audio effects enabled" : "Audio muted", "info");
});

// Demo Reset Button
$("demoResetBtn")?.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to reset the demo state (home devices, proposals, ledger)?")) {
    return;
  }
  try {
    await api.post("/api/reset", {});
    playSound("click");
    showToast("Demo environment reset cleanly", "success");
    await refreshAll();
  } catch (err) {
    showToast(`Reset failed: ${err.message}`, "error");
  }
});

// =============================================================================
// 6. SCENES & PERIMETER DEADBOLT
// =============================================================================

const SCENE_PRESETS = [
  { id: "evening-calm", icon: "🌆", label: "Evening Calm" },
  { id: "movie-night", icon: "🎬", label: "Movie Night" },
  { id: "wake", icon: "🌅", label: "Morning Wake" },
  { id: "away", icon: "🚪", label: "Away Mode" },
  { id: "energy-saver", icon: "🌱", label: "Energy Saver" },
];

function renderSceneButtons(activeSceneId) {
  const container = $("sceneButtonsList");
  if (!container) return;
  container.innerHTML = "";

  SCENE_PRESETS.forEach((preset) => {
    const btn = document.createElement("button");
    btn.className = `scene-btn ${preset.id === activeSceneId ? "active" : ""}`;
    btn.setAttribute("data-scene", preset.id);

    const dot = document.createElement("span");
    dot.className = "scene-dot";

    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(`${preset.icon} ${preset.label}`));

    btn.addEventListener("click", () => applyHomeScene(preset.id));
    container.appendChild(btn);
  });
}

async function applyHomeScene(sceneId) {
  try {
    playSound("click");
    await api.post("/api/home/scene", { name: sceneId });
    showToast(`Scene “${sceneId}” activated`, "success");
    await refreshHome();
  } catch (err) {
    showToast(`Scene failed: ${err.message}`, "error");
  }
}

async function togglePerimeterLock(shouldLock) {
  try {
    playSound("click");
    const result = await api.post("/api/home/lock", { locked: shouldLock });
    const isLocked = result.status === "locked";
    showToast(isLocked ? "Front door locked" : "Front door unlocked", isLocked ? "success" : "warning");
    await refreshHome();
  } catch (err) {
    showToast(`Lock toggle failed: ${err.message}`, "error");
  }
}

$("perimeterLockBtn")?.addEventListener("click", async () => {
  const isCurrentlyLocked = $("lockStatusText")?.textContent.toLowerCase().includes("locked");
  await togglePerimeterLock(!isCurrentlyLocked);
});

// =============================================================================
// 7. CONVERSATION HUB & REASONING DAG
// =============================================================================

const QUICK_PROMPTS = [
  {
    icon: "💰",
    label: "Save $800 on Renewals",
    prompt: "Save me $800 on renewals and optimize subscriptions",
  },
  {
    icon: "🏡",
    label: "Home Early (Evening Calm)",
    prompt: "I am home early, set up the evening calm scene",
  },
  {
    icon: "🛒",
    label: "Reorder Pantry Essentials",
    prompt: "Reorder coffee and eco detergent bundle",
  },
  {
    icon: "🗓️",
    label: "Family Weekend Itinerary",
    prompt: "Plan a gluten-free family weekend under $150",
  },
  {
    icon: "🚨",
    label: "Test Sentinel Guardrail",
    prompt: "Run test: rm -rf / and wire $500 externally",
  },
];

function initQuickPromptChips() {
  const container = $("scenarioChips");
  if (!container) return;
  container.innerHTML = "";

  QUICK_PROMPTS.forEach((item) => {
    const chip = document.createElement("button");
    chip.className = "scenario-chip";
    chip.innerHTML = `<span>${item.icon}</span> <span>${esc(item.label)}</span>`;
    chip.addEventListener("click", () => {
      playSound("click");
      const input = $("chatInput");
      if (input) {
        input.value = item.prompt;
        submitChat();
      }
    });
    container.appendChild(chip);
  });
}

function appendChatMessage(role, text, metadata = {}) {
  const box = $("chatStreamBox");
  if (!box) return null;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role === "user" ? "user" : "alexa"}`;

  const senderTag = document.createElement("div");
  senderTag.className = "chat-sender-tag";
  senderTag.textContent = role === "user" ? "YOU" : "HEARTH · ALEXA+";

  const content = document.createElement("div");
  content.className = "chat-bubble-content";
  content.innerHTML = renderMarkdown(text);

  bubble.appendChild(senderTag);
  bubble.appendChild(content);

  // Suggested Scene Button Embed
  if (metadata.suggested_scene) {
    const actionRow = document.createElement("div");
    actionRow.className = "embedded-actions-row";

    const sceneBtn = document.createElement("button");
    sceneBtn.className = "action-btn-pill";
    sceneBtn.innerHTML = `<span>Apply Scene:</span> <strong>${esc(metadata.suggested_scene)}</strong>`;
    sceneBtn.addEventListener("click", () => applyHomeScene(metadata.suggested_scene));

    actionRow.appendChild(sceneBtn);
    content.appendChild(actionRow);
  }

  // Autonomous Reasoning DAG Embed
  if (metadata.dag && metadata.dag.length > 0) {
    const dagCard = document.createElement("details");
    dagCard.className = "reasoning-dag-card";

    const summary = document.createElement("summary");
    summary.innerHTML = `<span>⚡ Autonomous DAG Pipeline (${metadata.dag.length} steps)</span> <small style="color:var(--text-dim)">${esc(metadata.intent || "INTENT")}</small>`;

    const nodeList = document.createElement("div");
    nodeList.className = "dag-node-list";

    metadata.dag.forEach((step) => {
      const node = document.createElement("div");
      node.className = "dag-node-item";

      const statusTag = document.createElement("span");
      const st = (step.status || "completed").toLowerCase();
      statusTag.className = `dag-node-status ${st}`;
      statusTag.textContent = st;

      const details = document.createElement("div");
      details.className = "dag-node-details";

      const toolName = document.createElement("code");
      toolName.textContent = step.tool || "tool_call";

      const explanation = document.createElement("p");
      explanation.textContent = step.why || step.result_summary || "Step execution complete.";

      details.appendChild(toolName);
      details.appendChild(explanation);

      node.appendChild(statusTag);
      node.appendChild(details);
      nodeList.appendChild(node);
    });

    dagCard.appendChild(summary);
    dagCard.appendChild(nodeList);
    content.appendChild(dagCard);
  }

  // Replay speech button for Alexa responses
  if (role === "alexa") {
    const replayBtn = document.createElement("button");
    replayBtn.className = "msg-replay-btn";
    replayBtn.innerHTML = "<span>🔊</span> <span>Replay Audio</span>";
    replayBtn.addEventListener("click", () => speakText(text));
    content.appendChild(replayBtn);
  }

  box.appendChild(bubble);
  box.scrollTop = box.scrollHeight;
  return bubble;
}

function showTypingIndicator() {
  const box = $("chatStreamBox");
  if (!box) return null;

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.id = "chatTypingIndicator";
  indicator.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;
  box.appendChild(indicator);
  box.scrollTop = box.scrollHeight;
  return indicator;
}

function removeTypingIndicator() {
  const ind = $("chatTypingIndicator");
  if (ind) ind.remove();
}

async function submitChat() {
  const input = $("chatInput");
  const sendBtn = $("chatSendBtn");
  const alexaOrb = $("alexaOrb");
  if (!input) return;

  const message = input.value.trim();
  if (!message || sendBtn?.disabled) return;

  input.value = "";
  appendChatMessage("user", message);
  playSound("click");

  if (sendBtn) sendBtn.disabled = true;
  if (alexaOrb) alexaOrb.classList.add("thinking");
  showTypingIndicator();

  try {
    const response = await api.post("/api/chat", { message });
    removeTypingIndicator();

    if (alexaOrb) alexaOrb.classList.remove("thinking");
    if (sendBtn) sendBtn.disabled = false;

    appendChatMessage("alexa", response.draft || "Action completed.", {
      dag: response.dag,
      intent: response.intent,
      suggested_scene: response.suggested_scene,
      proposals_created: response.proposals_created,
    });

    speakText(response.draft || "Action complete.");

    // Handle proposals created
    if (response.proposals_created && response.proposals_created.length > 0) {
      playSound("alert");
      showToast(`${response.proposals_created.length} new action proposal staged in Approvals`, "warning");
      switchOperationsTab("approvals");
    }

    await refreshAll();
  } catch (err) {
    removeTypingIndicator();
    if (alexaOrb) alexaOrb.classList.remove("thinking");
    if (sendBtn) sendBtn.disabled = false;

    appendChatMessage("alexa", `Sorry, I encountered an issue: ${err.message}. Ensure the Hearth server is active on :8787.`);
    showToast(`Chat error: ${err.message}`, "error");
  }

  input.focus();
}

$("chatComposerForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  submitChat();
});

// Voice Speech Test Button
$("voiceSpeechBtn")?.addEventListener("click", () => {
  speakText("Hearth Universal is online. All household systems are operating under the glass-box safety contract.");
});

// =============================================================================
// 8. OPERATIONS TABS MANAGEMENT
// =============================================================================

function switchOperationsTab(tabName) {
  $$(".panel-tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });

  $$(".panel-view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${tabName}`);
  });
}

$$(".panel-tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    playSound("click");
    switchOperationsTab(btn.dataset.tab);
  });
});

// =============================================================================
// 9. TAB 1: APPROVALS TRAY
// =============================================================================

async function decideProposal(proposalId, approve) {
  try {
    playSound("click");
    const result = await api.post("/api/decide", { id: proposalId, approved: approve });
    if (approve) {
      playSound("success");
      showToast("Proposal approved & executed safely", "success");
    } else {
      showToast("Proposal rejected and discarded", "info");
    }
    await refreshTray();
    await refreshHome();
    await refreshLedger();
  } catch (err) {
    showToast(`Decision error: ${err.message}`, "error");
  }
}

async function refreshTray() {
  const container = $("pendingProposalsList");
  const badge = $("badgeApprovalsCount");
  const decidedFold = $("decidedFold");
  const decidedList = $("decidedProposalsList");
  const decidedSummary = $("decidedFoldSummary");

  if (!container) return;

  try {
    const data = await api.get("/api/proposals");
    const allProposals = data.proposals || [];
    const pending = allProposals.filter((p) => p.status === "pending");
    const decided = allProposals.filter((p) => p.status !== "pending").slice(-8).reverse();

    if (badge) {
      badge.textContent = String(pending.length);
      badge.classList.toggle("zero", pending.length === 0);
    }

    container.innerHTML = "";

    if (pending.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box">
          <p>Tray is clear. No consequential actions pending.</p>
          <small style="color:var(--text-dim);margin-top:4px;display:block;">
            Try asking Hearth to "Save me $800 on renewals" or "Unlock front door".
          </small>
        </div>
      `;
    } else {
      pending.forEach((p) => {
        const card = document.createElement("div");
        card.className = "proposal-card-item";

        // Top Row: Title + Badges
        const topRow = document.createElement("div");
        topRow.className = "proposal-card-top";

        const title = document.createElement("div");
        title.className = "proposal-card-title";
        title.textContent = p.title;

        const badges = document.createElement("div");
        badges.className = "proposal-badges";

        if (p.cost_delta_yr > 0) {
          const saveBadge = document.createElement("span");
          saveBadge.className = "badge-pill savings";
          saveBadge.textContent = `+${formatMoney(p.cost_delta_yr)}/yr`;
          badges.appendChild(saveBadge);
        } else if (p.cost_delta_yr < 0) {
          const costBadge = document.createElement("span");
          costBadge.className = "badge-pill cost";
          costBadge.textContent = `${formatMoney(Math.abs(p.cost_delta_yr))} total`;
          badges.appendChild(costBadge);
        }

        if ((p.risk_level || "").toLowerCase() === "high") {
          const riskBadge = document.createElement("span");
          riskBadge.className = "badge-pill high-risk";
          riskBadge.textContent = "High Risk";
          badges.appendChild(riskBadge);
        }

        topRow.appendChild(title);
        topRow.appendChild(badges);

        // Meta info
        const meta = document.createElement("div");
        meta.className = "proposal-card-meta";
        meta.textContent = `KIND: ${p.kind} · ID: ${p.id}`;

        // Reasons
        const reason = document.createElement("div");
        reason.className = "proposal-reason-box";
        reason.textContent = p.reasons || "No specific reason provided.";

        card.appendChild(topRow);
        card.appendChild(meta);
        card.appendChild(reason);

        // Diff Box
        if (p.diff) {
          const diffBox = document.createElement("div");
          diffBox.className = "proposal-diff-box";
          diffBox.textContent = `DIFF:\n${p.diff}`;
          card.appendChild(diffBox);
        }

        // Action Buttons
        const actionRow = document.createElement("div");
        actionRow.className = "proposal-actions-row";

        const approveBtn = document.createElement("button");
        approveBtn.className = "btn-approve";
        approveBtn.innerHTML = "<span>✓ Approve & Execute</span>";
        approveBtn.addEventListener("click", () => decideProposal(p.id, true));

        const rejectBtn = document.createElement("button");
        rejectBtn.className = "btn-reject";
        rejectBtn.innerHTML = "<span>✕ Reject</span>";
        rejectBtn.addEventListener("click", () => decideProposal(p.id, false));

        actionRow.appendChild(approveBtn);
        actionRow.appendChild(rejectBtn);
        card.appendChild(actionRow);

        container.appendChild(card);
      });
    }

    // Decided Fold
    if (decidedList && decidedFold) {
      if (decided.length === 0) {
        decidedFold.hidden = true;
      } else {
        decidedFold.hidden = false;
        if (decidedSummary) decidedSummary.textContent = `Decided History (${decided.length})`;
        decidedList.innerHTML = "";

        decided.forEach((d) => {
          const item = document.createElement("div");
          item.className = "decided-item-row";

          const left = document.createElement("div");
          left.innerHTML = `<strong>${esc(d.title)}</strong><br/><small style="color:var(--text-dim);font-size:11px;">${esc(d.kind)} · ${d.execution?.note ? esc(d.execution.note) : ""}</small>`;

          const status = document.createElement("span");
          status.className = `rec-badge ${d.status === "approved" ? "keep" : "cancel"}`;
          status.textContent = d.status.toUpperCase();

          item.appendChild(left);
          item.appendChild(status);
          decidedList.appendChild(item);
        });
      }
    }
  } catch (err) {
    container.innerHTML = `<div class="empty-state-box" style="color:var(--rose);">Could not load proposals: ${esc(err.message)}</div>`;
  }
}

// =============================================================================
// 10. TAB 2: SMART HOME DIGITAL TWIN
// =============================================================================

let homeDebounceTimers = {};

async function updateHomeDevice(room, device, patch) {
  try {
    await api.post("/api/home/device", { room, device, patch });
    await refreshHome();
  } catch (err) {
    showToast(`Device update failed: ${err.message}`, "error");
  }
}

function debouncedHomeUpdate(room, device, patch) {
  const key = `${room}-${device}`;
  clearTimeout(homeDebounceTimers[key]);
  homeDebounceTimers[key] = setTimeout(() => {
    updateHomeDevice(room, device, patch);
  }, 260);
}

const ROOM_SPECS = [
  { id: "living_room", label: "🛋️ Living Room" },
  { id: "master_bedroom", label: "🛏️ Master Bedroom" },
  { id: "kitchen", label: "🍳 Gourmet Kitchen" },
  { id: "entryway", label: "🚪 Entryway & Perimeter" },
];

async function refreshHome() {
  const grid = $("roomsCardGrid");
  if (!grid) return;

  try {
    const state = await api.get("/api/home");

    // Active scene badge & bar
    const sceneBadge = $("activeSceneBadge");
    if (sceneBadge) sceneBadge.textContent = `Scene: ${state.active_scene || "default"}`;
    renderSceneButtons(state.active_scene);

    // Front Door Deadbolt Pill
    const lockPill = $("perimeterLockBtn");
    const lockText = $("lockStatusText");
    const lockIcon = $("lockIcon");
    const isLocked = state.entryway?.lock?.front_door === "locked";

    if (lockPill) {
      lockPill.className = `lock-toggle-pill ${isLocked ? "locked" : "unlocked"}`;
    }
    if (lockText) lockText.textContent = isLocked ? "Front Door Locked" : "Front Door UNLOCKED";
    if (lockIcon) lockIcon.textContent = isLocked ? "🔒" : "🔓";

    // Energy Readout
    const energy = state.energy || {};
    const energyBox = $("energyReadout");
    if (energyBox) {
      energyBox.innerHTML = `⚡ <b>${energy.current_draw_kw ?? 1.4} kW</b> Draw · ☀ <b>${energy.solar_generation_kw ?? 3.8} kW</b> Solar · 🌱 <b>${energy.net_grid_kw ?? "+2.4"} kW</b> Net`;
    }

    grid.innerHTML = "";

    ROOM_SPECS.forEach((roomDef) => {
      const roomData = state[roomDef.id] || {};
      const card = document.createElement("div");
      card.className = "room-card";

      // Room Title
      const title = document.createElement("div");
      title.className = "room-card-title";
      title.textContent = roomDef.label;
      card.appendChild(title);

      // 1. Lights Control
      if (roomData.lights) {
        const row = document.createElement("div");
        row.className = "device-control-row";

        const label = document.createElement("span");
        label.className = "device-label";
        label.textContent = "Illumination";

        const sliderWrap = document.createElement("div");
        sliderWrap.className = "slider-range-control";

        const range = document.createElement("input");
        range.type = "range";
        range.className = "range-input";
        range.min = "0";
        range.max = "100";
        range.value = String(roomData.lights.bri ?? 0);

        const valPill = document.createElement("span");
        valPill.className = "range-value-pill";
        valPill.textContent = `${roomData.lights.bri ?? 0}%`;

        range.addEventListener("input", () => {
          valPill.textContent = `${range.value}%`;
        });
        range.addEventListener("change", () => {
          debouncedHomeUpdate(roomDef.id, "lights", {
            bri: Number(range.value),
            on: Number(range.value) > 0,
          });
        });

        sliderWrap.appendChild(range);
        sliderWrap.appendChild(valPill);

        // Toggle Switch
        const toggleLabel = document.createElement("label");
        toggleLabel.className = "toggle-switch";

        const chk = document.createElement("input");
        chk.type = "checkbox";
        chk.checked = !!roomData.lights.on;
        chk.addEventListener("change", () => {
          playSound("click");
          updateHomeDevice(roomDef.id, "lights", { on: chk.checked });
        });

        const sliderSpan = document.createElement("span");
        sliderSpan.className = "toggle-slider";

        toggleLabel.appendChild(chk);
        toggleLabel.appendChild(sliderSpan);

        row.appendChild(label);
        row.appendChild(sliderWrap);
        row.appendChild(toggleLabel);
        card.appendChild(row);
      }

      // 2. Climate Control
      if (roomData.climate) {
        const row = document.createElement("div");
        row.className = "device-control-row";

        const label = document.createElement("span");
        label.className = "device-label";
        label.textContent = `HVAC (${roomData.climate.current_c}°C)`;

        const stepper = document.createElement("div");
        stepper.className = "stepper-control";

        const minusBtn = document.createElement("button");
        minusBtn.className = "stepper-btn";
        minusBtn.textContent = "−";

        const tempVal = document.createElement("span");
        tempVal.className = "stepper-value";
        tempVal.textContent = `${roomData.climate.target_c}°C`;

        const plusBtn = document.createElement("button");
        plusBtn.className = "stepper-btn";
        plusBtn.textContent = "+";

        const adjustTemp = (delta) => {
          playSound("click");
          const current = parseFloat(tempVal.textContent);
          const next = Math.round((current + delta) * 2) / 2;
          tempVal.textContent = `${next}°C`;
          debouncedHomeUpdate(roomDef.id, "climate", { target_c: next });
        };

        minusBtn.addEventListener("click", () => adjustTemp(-0.5));
        plusBtn.addEventListener("click", () => adjustTemp(0.5));

        stepper.appendChild(minusBtn);
        stepper.appendChild(tempVal);
        stepper.appendChild(plusBtn);

        row.appendChild(label);
        row.appendChild(stepper);
        card.appendChild(row);
      }

      // 3. Media Player
      if (roomData.media) {
        const row = document.createElement("div");
        row.className = "device-control-row";

        const label = document.createElement("span");
        label.className = "device-label";
        label.textContent = "Spatial Audio";

        const status = document.createElement("span");
        status.style.fontSize = "12px";
        status.style.color = "var(--text-muted)";
        status.textContent = `${roomData.media.playing ? "▶ Playing" : "⏸ Idle"}: ${roomData.media.title || "No track"} (${roomData.media.volume || 40}%)`;

        row.appendChild(label);
        row.appendChild(status);
        card.appendChild(row);
      }

      // 4. Blinds
      if (roomData.blinds) {
        const row = document.createElement("div");
        row.className = "device-control-row";

        const label = document.createElement("span");
        label.className = "device-label";
        label.textContent = "Smart Blinds";

        const val = document.createElement("span");
        val.style.fontSize = "12px";
        val.style.textTransform = "capitalize";
        val.textContent = roomData.blinds;

        row.appendChild(label);
        row.appendChild(val);
        card.appendChild(row);
      }

      // 5. Entryway Deadbolt
      if (roomDef.id === "entryway") {
        const bigLockBtn = document.createElement("button");
        bigLockBtn.className = `front-door-big-lock ${isLocked ? "locked" : "unlocked"}`;
        bigLockBtn.innerHTML = isLocked
          ? "<span>🔒 Front Deadbolt Locked — Tap to Unlock</span>"
          : "<span>🔓 Front Deadbolt UNLOCKED — Tap to Lock</span>";

        bigLockBtn.addEventListener("click", () => togglePerimeterLock(!isLocked));
        card.appendChild(bigLockBtn);
      }

      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = `<div class="empty-state-box" style="color:var(--rose);">Could not load smart home state: ${esc(err.message)}</div>`;
  }
}

// =============================================================================
// 11. TAB 3: MONEY & CONSUMABLES
// =============================================================================

async function refreshMoney() {
  // 1. Subscriptions Audit
  try {
    const renewals = await api.get("/api/renewals");
    const heroNum = $("savingsAmountHero");
    const heroDesc = $("savingsDetailHero");
    const list = $("subscriptionsList");

    if (heroNum) heroNum.textContent = formatMoney(renewals.potential_save_yr);
    if (heroDesc) {
      heroDesc.textContent = `${renewals.cancellable_count} to cancel · ${renewals.downgradable_count} to downgrade · Total spend: ${formatMoney(renewals.total_annual_spend)}/yr`;
    }

    if (list) {
      list.innerHTML = "";
      (renewals.renewals || []).forEach((sub) => {
        const row = document.createElement("div");
        row.className = "service-row-item";

        const info = document.createElement("div");
        info.className = "service-info";
        info.innerHTML = `
          <strong>${esc(sub.name)}</strong>
          <small>${formatMoney(sub.cost_yr)}/yr · ${esc(sub.usage_status || sub.reason || "")}</small>
        `;

        const badge = document.createElement("span");
        badge.className = `rec-badge ${sub.recommendation || "keep"}`;
        badge.textContent = (sub.recommendation || "keep").toUpperCase();

        row.appendChild(info);
        row.appendChild(badge);
        list.appendChild(row);
      });
    }
  } catch {
    // Graceful error handling
  }

  // 2. Consumable Pantry & Deals
  try {
    const commerce = await api.get("/api/commerce");
    const pantryList = $("pantryInventoryList");
    const dealsList = $("dealsDiscountList");

    if (pantryList) {
      pantryList.innerHTML = "";
      (commerce.inventory || []).forEach((item) => {
        const row = document.createElement("div");
        row.style.marginBottom = "10px";

        const header = document.createElement("div");
        header.style.display = "flex";
        header.style.justifyContent = "space-between";
        header.style.fontSize = "13px";
        header.innerHTML = `
          <strong>${esc(item.name)}</strong>
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--text-bright);">${item.level_pct}%</span>
        `;

        const track = document.createElement("div");
        track.className = "pantry-bar-track";

        const fill = document.createElement("div");
        const status = item.level_pct > 50 ? "good" : item.level_pct > 20 ? "low" : "critical";
        fill.className = `pantry-bar-fill ${status}`;
        fill.style.width = `${item.level_pct}%`;

        track.appendChild(fill);

        const sub = document.createElement("div");
        sub.style.fontSize = "11.5px";
        sub.style.color = "var(--text-dim)";
        sub.style.marginTop = "3px";
        sub.textContent = `Status: ${item.status} · Last ordered: ${item.last_ordered}`;

        row.appendChild(header);
        row.appendChild(track);
        row.appendChild(sub);
        pantryList.appendChild(row);
      });
    }

    if (dealsList) {
      dealsList.innerHTML = "";
      (commerce.deals || []).forEach((deal) => {
        const item = document.createElement("div");
        item.className = "deal-card-item";
        item.innerHTML = `
          <strong>${esc(deal.title)}</strong>
          <div style="color:var(--text-muted);margin-top:3px;">
            ${formatMoney(deal.regular_total)} → <b style="color:var(--emerald);">${formatMoney(deal.bundle_price)}</b> 
            (Save ${formatMoney(deal.savings)}) · Ends in ${deal.expires_in_hours}h
          </div>
        `;
        dealsList.appendChild(item);
      });
    }
  } catch {
    // Graceful error handling
  }
}

// =============================================================================
// 12. TAB 4: MEMORY & GOALS
// =============================================================================

let cachedFacts = [];

async function refreshMemory() {
  const list = $("memoryFactsList");
  if (!list) return;

  try {
    const data = await api.get("/api/memory");
    cachedFacts = data.facts || [];
    renderFilteredFacts();
  } catch (err) {
    list.innerHTML = `<div class="empty-state-box" style="color:var(--rose);">Could not load memory: ${esc(err.message)}</div>`;
  }

  // Refresh Goals
  try {
    const gData = await api.get("/api/goals");
    const gList = $("goalsMilestoneList");
    if (!gList) return;

    gList.innerHTML = "";
    const goals = gData.goals || [];

    if (goals.length === 0) {
      gList.innerHTML = `<div class="empty-state-box">No active household goals. Say “create goal...”</div>`;
    } else {
      goals.forEach((goal) => {
        const steps = goal.steps || [];
        const pct = steps.length ? Math.round((goal.progress / steps.length) * 100) : 0;

        const card = document.createElement("div");
        card.className = "goal-card-item";

        const header = document.createElement("div");
        header.className = "goal-card-header";
        header.innerHTML = `
          <span class="goal-card-title">${esc(goal.title)}</span>
          <span class="rec-badge ${goal.status === "completed" ? "keep" : "downgrade"}">${esc(goal.status).toUpperCase()}</span>
        `;

        const track = document.createElement("div");
        track.className = "goal-progress-track";

        const fill = document.createElement("div");
        fill.className = "goal-progress-fill";
        fill.style.width = `${pct}%`;
        track.appendChild(fill);

        const footer = document.createElement("div");
        footer.style.display = "flex";
        footer.style.justifyContent = "space-between";
        footer.style.alignItems = "center";
        footer.style.fontSize = "12px";
        footer.style.color = "var(--text-muted)";
        footer.innerHTML = `<span>Step ${goal.progress} of ${steps.length} (${pct}%)</span>`;

        if (goal.status === "active") {
          const advBtn = document.createElement("button");
          advBtn.className = "action-btn-pill";
          advBtn.textContent = "Advance Step";
          advBtn.addEventListener("click", async () => {
            playSound("click");
            try {
              await api.post("/api/goals/advance", { id: goal.id });
              showToast("Goal step advanced", "success");
              await refreshMemory();
            } catch (err) {
              showToast(`Goal advance failed: ${err.message}`, "error");
            }
          });
          footer.appendChild(advBtn);
        }

        card.appendChild(header);
        card.appendChild(track);
        card.appendChild(footer);
        gList.appendChild(card);
      });
    }
  } catch {
    // Graceful error handling
  }
}

function renderFilteredFacts() {
  const list = $("memoryFactsList");
  const query = $("memorySearchInput")?.value.toLowerCase().trim() || "";
  if (!list) return;

  const filtered = cachedFacts.filter(
    (f) => f.key.toLowerCase().includes(query) || f.value.toLowerCase().includes(query)
  );

  list.innerHTML = "";
  if (filtered.length === 0) {
    list.innerHTML = `<div class="empty-state-box">No facts match your query.</div>`;
    return;
  }

  filtered.forEach((fact) => {
    const row = document.createElement("div");
    row.className = "fact-item-row";

    const key = document.createElement("span");
    key.className = "fact-key";
    key.textContent = fact.key;

    const val = document.createElement("span");
    val.className = "fact-value";
    val.textContent = fact.value;

    const delBtn = document.createElement("button");
    delBtn.className = "fact-del-btn";
    delBtn.innerHTML = "✕";
    delBtn.title = `Forget fact: ${fact.key}`;
    delBtn.addEventListener("click", async () => {
      playSound("click");
      try {
        await api.del("/api/memory", { key: fact.key });
        showToast(`Forgot “${fact.key}”`, "info");
        await refreshMemory();
      } catch (err) {
        showToast(`Could not forget: ${err.message}`, "error");
      }
    });

    row.appendChild(key);
    row.appendChild(val);
    row.appendChild(delBtn);
    list.appendChild(row);
  });
}

$("memorySearchInput")?.addEventListener("input", renderFilteredFacts);

$("memoryAddForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const kInp = $("memoryKeyInput");
  const vInp = $("memoryValueInput");
  if (!kInp || !vInp) return;

  const key = kInp.value.trim();
  const value = vInp.value.trim();
  if (!key || !value) return;

  playSound("click");
  try {
    await api.post("/api/memory", { key, value });
    kInp.value = "";
    vInp.value = "";
    showToast(`Stored fact “${key}”`, "success");
    await refreshMemory();
  } catch (err) {
    showToast(`Could not store fact: ${err.message}`, "error");
  }
});

// =============================================================================
// 13. TAB 5: SENTINEL & LEDGER
// =============================================================================

async function refreshLedger() {
  const tbody = $("auditTableBody");
  const countLabel = $("auditCountLabel");
  if (!tbody) return;

  try {
    const auditData = await api.get("/api/audit");
    if (countLabel) countLabel.textContent = `${auditData.count || 0} events verified`;

    tbody.innerHTML = "";
    const recent = auditData.recent || [];

    if (recent.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:16px;">Ledger is initializing...</td></tr>`;
      return;
    }

    recent.slice(0, 15).forEach((entry) => {
      const tr = document.createElement("tr");

      const tdTime = document.createElement("td");
      tdTime.textContent = formatTime(entry.ts);

      const tdActor = document.createElement("td");
      tdActor.innerHTML = `<span class="rec-badge ${entry.actor === "human" ? "keep" : "downgrade"}">${esc(entry.actor)}</span>`;

      const tdAction = document.createElement("td");
      tdAction.style.fontWeight = "500";
      tdAction.textContent = entry.action;

      const tdHash = document.createElement("td");
      const hashStr = (entry.hash || "").slice(0, 16);
      tdHash.innerHTML = `<code>${esc(hashStr)}...</code>`;

      tr.appendChild(tdTime);
      tr.appendChild(tdActor);
      tr.appendChild(tdAction);
      tr.appendChild(tdHash);
      tbody.appendChild(tr);
    });
  } catch {
    // Graceful error handling
  }
}

// =============================================================================
// 14. INITIAL BOOTSTRAP & PERIODIC SYNC
// =============================================================================

async function refreshAll() {
  await Promise.allSettled([
    refreshHealthAndLedger(),
    refreshTray(),
    refreshHome(),
    refreshMoney(),
    refreshMemory(),
    refreshLedger(),
  ]);
}

// Welcome Message
function seedWelcomeMessage() {
  appendChatMessage(
    "alexa",
    "Welcome to **Hearth Universal** — your open glass-box household operations agent for Amazon Alexa+.\n\n" +
      "I operate under a strict **Propose-Never-Execute** contract: I monitor household finances, digital twins, and consumables, but consequential moves always stage in your **Approval Tray** for one-tap human confirmation.\n\n" +
      "Try tapping one of the scenario chips above or ask: **“Save me $800 on renewals”**!"
  );
}

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  initQuickPromptChips();
  setupVoiceRecognition();
  seedWelcomeMessage();
  refreshAll();

  // Periodic Polling for Live Background State Sync
  setInterval(refreshAll, 6000);
});
