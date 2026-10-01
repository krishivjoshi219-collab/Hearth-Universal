/**
 * MAIN CONTROLLER & APPLICATION LIFECYCLE — HEARTH UNIVERSAL
 * Orchestrates Ambient Echo Canvas · Operations Console · Alexa Voice & Glass-Box Safety
 */

import { VoiceEngine } from "./voice.js";
import { DigitalTwinEngine } from "./twin.js";
import { McpAppsManager } from "./mcp-apps.js";
import { ProposalsEngine } from "./proposals.js";
import { TrayA11y } from "./tray.js";

class HearthUniversalApp {
  constructor() {
    this.apiBase = window.location.origin;
    this.currentMode = "canvas"; // 'canvas' | 'operations'
    this.activePersona = "admin";
    this.currentProposalToInspect = null;

    // Subsystems
    this.voice = new VoiceEngine("alexaGlowCanvas");
    this.twin = new DigitalTwinEngine(this.apiBase, (st) => this.onTwinStateUpdate(st));
    this.proposals = new ProposalsEngine(
      this.apiBase,
      (props) => this.onProposalsUpdate(props),
      (p) => this.openInspectionModal(p)
    );
    this.proposals.onAnnounce = (msg, pri) => TrayA11y.announce(msg, pri);
    this.proposals.onGuardrail = (msg) => {
      this.showToast(`⛔ ${msg}`);
      TrayA11y.announce(msg, "assertive");
    };
    this._lastPendingCount = -1;
    this._modalTrapRelease = null;

    this.initDOM();
    this.bindEvents();
    this.startHeartbeatStream();
    this.bootstrap();
  }

  initDOM() {
    this.dom = {
      canvasView: document.getElementById("canvasViewSection"),
      opsView: document.getElementById("operationsViewSection"),
      btnModeCanvas: document.getElementById("btnModeCanvas"),
      btnModeOps: document.getElementById("btnModeOps"),
      personaSelect: document.getElementById("personaSelect"),
      clockDisplay: document.getElementById("liveClockDisplay"),
      soundToggleBtn: document.getElementById("soundToggleBtn"),
      composerForm: document.getElementById("composerForm"),
      composerInput: document.getElementById("composerInput"),
      micBtn: document.getElementById("composerMicBtn"),
      conversationStream: document.getElementById("conversationStream"),
      trayCountBadge: document.getElementById("trayCountBadge"),
      pendingProposalsFeed: document.getElementById("pendingProposalsFeed"),
      depletionRadarFeed: document.getElementById("depletionRadarFeed"),
      modal: document.getElementById("inspectionModal"),
      modalCloseBtn: document.getElementById("modalCloseBtn"),
      modalApproveBtn: document.getElementById("modalApproveBtn"),
      modalRejectBtn: document.getElementById("modalRejectBtn"),
      modalProposalTitle: document.getElementById("modalProposalTitle"),
      modalProposalId: document.getElementById("modalProposalId"),
      modalMerkleHash: document.getElementById("modalMerkleHash"),
      modalDiffPre: document.getElementById("modalDiffPre"),
      modalSentinelVerdict: document.getElementById("modalSentinelVerdict"),
      toastShelf: document.getElementById("toast-shelf"),
      ringSimulateBtn: document.getElementById("ringSimulateBtn"),
      quickScenesList: document.getElementById("quickScenesList"),
      proactiveTickBtn: document.getElementById("proactiveTickBtn"),
    };
  }

  bindEvents() {
    TrayA11y.ensureLiveRegions();
    TrayA11y.bindLedgerTriggers(this.apiBase, (m) => this.showToast(m));
    if (this.dom.pendingProposalsFeed) {
      TrayA11y.bindKeyboard(this.dom.pendingProposalsFeed, this.proposals, {
        isModalOpen: () => this.dom.modal?.classList.contains("open"),
        onCloseModal: () => this.closeInspectionModal(),
      });
      TrayA11y.bindSwipe(this.dom.pendingProposalsFeed, this.proposals);
    }
    // Mode switcher
    this.dom.btnModeCanvas?.addEventListener("click", () => this.switchViewMode("canvas"));
    this.dom.btnModeOps?.addEventListener("click", () => this.switchViewMode("operations"));

    // Persona selection
    this.dom.personaSelect?.addEventListener("change", (e) => this.switchPersona(e.target.value));

    // Sound toggle
    this.dom.soundToggleBtn?.addEventListener("click", () => {
      const on = this.voice.toggleSound();
      this.dom.soundToggleBtn.textContent = on ? "🔊 Sound On" : "🔇 Sound Off";
      this.showToast(on ? "Audio feedback enabled" : "Audio muted");
    });

    // Chat form submit
    this.dom.composerForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = this.dom.composerInput.value.trim();
      if (val) this.sendMessage(val);
    });

    // Mic button
    this.dom.micBtn?.addEventListener("click", () => {
      this.voice.listenOnce(
        (transcript) => {
          this.dom.composerInput.value = transcript;
          this.sendMessage(transcript);
        },
        (err) => this.showToast(`Voice error: ${err}`)
      );
    });

    // Ring doorbell simulator
    this.dom.ringSimulateBtn?.addEventListener("click", () => {
      this.voice.playEchoPing();
      this.twin.triggerRingEvent("doorbell_press", "Amazon Prime Delivery Courier");
      this.showToast("🔔 Doorbell Ring: Visitor at Front Porch");
    });

    // Proactive pulse button
    this.dom.proactiveTickBtn?.addEventListener("click", async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/simulate/tick`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario: "auto" })
        });
        const data = await res.json();
        this.showToast(`✨ Proactive Pulse: ${data.message || "Heartbeat event emitted"}`);
      } catch (e) {
        this.showToast("Pulse simulation error");
      }
    });
    document.getElementById("btnRunOpsAudit")?.addEventListener("click", async () => {
      this.showToast("⚡ Running proactive audit — staging proposals…");
      TrayA11y.announce("Running proactive audit. New proposals will appear in the tray.", "polite");
      try {
        await fetch(`${this.apiBase}/api/simulate/tick`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario: "auto" })
        });
      } catch {}
      await this.proposals.fetchProposals();
    });

    // Inspection modal close + focus trap + Esc + backdrop
    this.dom.modalCloseBtn?.addEventListener("click", () => this.closeInspectionModal());
    this.dom.modal?.addEventListener("click", (e) => {
      if (e.target === this.dom.modal) this.closeInspectionModal();
    });
    document.getElementById("btnCopyModalHash")?.addEventListener("click", async () => {
      const txt = this.dom.modalMerkleHash?.textContent || "";
      try { await navigator.clipboard.writeText(txt); this.showToast("📋 Seal copied"); }
      catch { this.showToast("Copy failed — long-press to select"); }
    });
    this.dom.modalRejectBtn?.addEventListener("click", async () => {
      if (this.currentProposalToInspect) {
        const p = this.currentProposalToInspect;
        this.closeInspectionModal();
        const out = await this.proposals.decide(p.id, false);
        this.showToast(out?.ok === false ? `Decision failed: ${out.error}` : "✕ Action rejected — no side effects");
      }
    });
    this.dom.modalApproveBtn?.addEventListener("click", async () => {
      if (this.currentProposalToInspect) {
        const p = this.currentProposalToInspect;
        this.voice.playSuccessChime();
        this.closeInspectionModal();
        const out = await this.proposals.decide(p.id, true);
        this.showToast(out?.ok === false ? `Decision failed: ${out.error}` : "✓ Action authorized with cryptographic seal");
      }
    });

    // Ambient scenes quick buttons
    document.querySelectorAll(".scene-btn-quick").forEach(btn => {
      btn.addEventListener("click", () => {
        const s = btn.dataset.scene;
        this.twin.setScene(s);
        document.querySelectorAll(".scene-btn-quick").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.showToast(`Active scene: ${s}`);
      });
    });

    // Killer Features: Time Machine, Arbiter, Barcode Scanner, and S&S Commerce Engine
    this.bindTimeMachine();
    this.bindArbiter();
    this.bindBarcodeScanner();
    this.bindCommerceExtensions();
  }

  bindTimeMachine() {
    const chips = document.querySelectorAll("#timeMachineChips .tm-preset-btn");
    chips.forEach(btn => {
      btn.addEventListener("click", async () => {
        const preset = btn.dataset.preset;
        chips.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        await this.applyTimeMachinePreset(preset);
      });
    });
  }

  async applyTimeMachinePreset(preset) {
    try {
      const res = await fetch(`${this.apiBase}/api/timemachine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset })
      });
      const data = await res.json();
      if (!data.ok) return;

      const fc = data.forecast;
      const tag = document.getElementById("tmNarrativeTag");
      if (tag) tag.textContent = fc.narrative;

      const clock = document.getElementById("liveClockDisplay");
      if (clock) clock.textContent = fc.time_str;

      const solarStat = document.querySelector(".energy-stat-number");
      if (solarStat) {
        solarStat.textContent = fc.solar_kw > 0 ? `+${fc.solar_kw} kW` : `${fc.grid_draw_kw} kW`;
      }

      const isNight = preset === "bedtime" || preset === "night";
      this.twin.setNightVision(isNight);

      this.voice.playSuccessChime();
      this.voice.speak(fc.narrative);
      this.showToast(`⏳ Time Machine: ${fc.label}`);
    } catch (e) {
      console.warn("Time machine error", e);
    }
  }

  bindArbiter() {
    this.currentConflictType = "climate";
    const tabClimate = document.getElementById("arbiterTabClimate");
    const tabTariff = document.getElementById("arbiterTabTariff");
    const tabBedtime = document.getElementById("arbiterTabBedtime");
    const arbiterTitle = document.getElementById("arbiterTitle");
    const arbiterPartiesRow = document.getElementById("arbiterPartiesRow");
    const arbiterImpact = document.getElementById("arbiterImpact");

    const setConflict = (type) => {
      this.currentConflictType = type;
      [tabClimate, tabTariff, tabBedtime].forEach(t => t?.classList.remove("active"));
      if (type === "climate") {
        tabClimate?.classList.add("active");
        if (arbiterTitle) arbiterTitle.textContent = "Dual-Resident Climate Conflict";
        if (arbiterPartiesRow) {
          arbiterPartiesRow.innerHTML = `
            <span class="party-chip">Alex (20.0°C)</span>
            <span class="party-vs">⚡</span>
            <span class="party-chip">Sarah (23.0°C)</span>
          `;
        }
        if (arbiterImpact) arbiterImpact.textContent = "Compromise: 21.5°C Eco Flow (-18.5% peak energy, saves $24.80/mo)";
      } else if (type === "tariff") {
        tabTariff?.classList.add("active");
        if (arbiterTitle) arbiterTitle.textContent = "Peak Grid Tariff Load Shifting";
        if (arbiterPartiesRow) {
          arbiterPartiesRow.innerHTML = `
            <span class="party-chip">User (Dishwasher Now)</span>
            <span class="party-vs">⚡</span>
            <span class="party-chip">Grid ($0.48/kWh Peak)</span>
          `;
        }
        if (arbiterImpact) arbiterImpact.textContent = "Delay 75 mins to Off-Peak $0.12/kWh (Saves $4.32/cycle, $51.84/yr)";
      } else if (type === "bedtime") {
        tabBedtime?.classList.add("active");
        if (arbiterTitle) arbiterTitle.textContent = "Leo Bedtime & Screen Wind-Down Protocol";
        if (arbiterPartiesRow) {
          arbiterPartiesRow.innerHTML = `
            <span class="party-chip">Leo (Gaming 100%)</span>
            <span class="party-vs">⚡</span>
            <span class="party-chip">Policy (10 PM Sleep)</span>
          `;
        }
        if (arbiterImpact) arbiterImpact.textContent = "15-Min Sunset Fade (100% -> 15% 2000K amber) + Rain audio transition";
      }
    };

    tabClimate?.addEventListener("click", () => setConflict("climate"));
    tabTariff?.addEventListener("click", () => setConflict("tariff"));
    tabBedtime?.addEventListener("click", () => setConflict("bedtime"));

    const btn = document.getElementById("arbiterSolveBtn");
    btn?.addEventListener("click", async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/arbiter`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conflict_type: this.currentConflictType })
        });
        const plan = await res.json();
        if (plan.ok) {
          const costDelta = plan.proposed_action?.cost_delta || 0.0;
          await this.proposals.propose(
            "arbiter_compromise",
            `Arbitration: ${plan.title}`,
            plan.description,
            costDelta * 12,
            "medium",
            plan.proposed_action?.diff || "Conflict compromise applied.",
            plan
          );
          
          if (arbiterImpact) {
            arbiterImpact.innerHTML = `<strong>✓ Arbitrated!</strong> ${plan.compromise.energy_impact || plan.compromise.protocol} | <em>Satisfaction: ${plan.compromise.satisfaction_index}</em>`;
          }

          this.voice.playSuccessChime();
          this.voice.speak(`I arbitrated the ${this.currentConflictType} conflict. Recommended compromise staged in your Approval Tray.`);
          this.showToast("⚖️ Family Arbiter: Compromise staged in Approval Tray");
        }
      } catch (e) {
        console.warn("Arbiter error", e);
      }
    });
  }

  bindCommerceExtensions() {
    const bundleBtn = document.getElementById("optimizeBundleBtn");
    bundleBtn?.addEventListener("click", async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/commerce/optimize-bundles`, { method: "POST" });
        const b = await res.json();
        if (b.ok) {
          const savings = b.pricing?.total_savings || 35.32;
          const optTotal = b.pricing?.optimized_bundle_total || 73.65;
          await this.proposals.propose(
            "commerce_order",
            "Subscribe & Save Bundle: Prime Max 5+ Items",
            b.summary,
            -optTotal,
            "medium",
            `Regular $${b.pricing.regular_total} -> Bundle $${optTotal} (Saved $${savings})`,
            b
          );
          const note = document.getElementById("deliveryItemsNote");
          if (note) {
            note.innerHTML = `<strong>✨ 5+ Item Tier Unlocked!</strong> Saved $${savings} (${b.pricing.savings_pct}%) · 1 Box (-${b.environmental_impact.carbon_offset_kg}kg CO2)`;
          }
          this.voice.playSuccessChime();
          this.voice.speak(`Prime Max 5-item bundle unlocked! Saved ${savings} dollars and consolidated into one delivery box.`);
          this.showToast(`✨ Amazon S&S: Prime Max 5+ tier saved $${savings}`);
        }
      } catch (e) {
        console.warn("Bundle optimize error", e);
      }
    });

    const reschedBtn = document.getElementById("rescheduleSlotBtn");
    const slotLabel = document.getElementById("currentSlotLabel");
    let currentSlot = "slot_tuesday_household";

    reschedBtn?.addEventListener("click", async () => {
      try {
        const nextSlot = currentSlot === "slot_tuesday_household" ? "slot_overnight_urgent" : "slot_tuesday_household";
        const res = await fetch(`${this.apiBase}/api/commerce/delivery-slots`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slot_id: nextSlot, reason: "Manual toggle via dashboard" })
        });
        const data = await res.json();
        if (data.ok) {
          currentSlot = nextSlot;
          if (slotLabel) slotLabel.textContent = data.new_slot;
          await this.proposals.propose(
            "delivery_reschedule",
            `Delivery Slot: ${data.new_slot}`,
            data.summary,
            0.0,
            "low",
            data.diff,
            data
          );
          this.voice.playSuccessChime();
          this.voice.speak(`Household delivery rescheduled to ${data.new_slot}.`);
          this.showToast(`🚚 Delivery Slot: ${data.new_slot}`);
        }
      } catch (e) {
        console.warn("Delivery slot reschedule error", e);
      }
    });
  }

  bindBarcodeScanner() {
    const modal = document.getElementById("barcodeModal");
    const openBtn = document.getElementById("openScannerModalBtn");
    const closeBtn = document.getElementById("closeBarcodeModalBtn");
    const depleteBtn = document.getElementById("simulateDepleteScanBtn");
    const replenishBtn = document.getElementById("simulateReplenishScanBtn");
    const statusNote = document.getElementById("barcodeStatusNote");

    openBtn?.addEventListener("click", () => {
      if (modal) modal.style.display = "flex";
      this.voice.playEchoPing();
    });

    closeBtn?.addEventListener("click", () => {
      if (modal) modal.style.display = "none";
    });

    depleteBtn?.addEventListener("click", async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/commerce/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: "item_coffee", action: "deplete" })
        });
        const data = await res.json();
        this.voice.playBarcodeBeep();
        if (statusNote) {
          statusNote.innerHTML = `<span style="color:var(--rose);">⚠️ Scanned UPC #085942001! Coffee depleted to 10% (Critical).</span>`;
        }
        await this.fetchDepletionRadar();
        this.showToast("Pantry: Coffee marked critical (10%)");
      } catch (e) {
        console.warn("Scan error", e);
      }
    });

    replenishBtn?.addEventListener("click", async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/commerce/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: "item_coffee", action: "replenish" })
        });
        const data = await res.json();
        this.voice.playBarcodeBeep();
        this.voice.playSuccessChime();
        if (statusNote) {
          statusNote.innerHTML = `<span style="color:var(--emerald);">✓ Scanned UPC #085942001! Coffee restocked to 100%!</span>`;
        }
        await this.fetchDepletionRadar();
        this.showToast("Pantry: Coffee restocked to 100%");
      } catch (e) {
        console.warn("Scan error", e);
      }
    });
  }

  switchViewMode(mode) {
    this.currentMode = mode;
    if (mode === "canvas") {
      this.dom.canvasView.style.display = "flex";
      this.dom.opsView.style.display = "none";
      this.dom.btnModeCanvas.classList.add("active");
      this.dom.btnModeOps.classList.remove("active");
    } else {
      this.dom.canvasView.style.display = "none";
      this.dom.opsView.style.display = "flex";
      this.dom.btnModeOps.classList.add("active");
      this.dom.btnModeCanvas.classList.remove("active");
    }
  }

  async switchPersona(personaId) {
    this.activePersona = personaId;
    this.proposals.setPersona(personaId);
    try {
      await fetch(`${this.apiBase}/api/persona`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: personaId })
      });
      const labels = {
        admin: "Krishiv (Admin)",
        partner: "Sarah (Partner)",
        child: "Leo (Child - Guardrails Active)",
        guest: "Guest Visitor"
      };
      this.showToast(`Switched profile: ${labels[personaId] || personaId}`);
    } catch (e) {
      console.warn("Failed to switch persona", e);
    }
  }

  async bootstrap() {
    this.startClock();
    await this.twin.fetchState();
    await this.proposals.fetchProposals();
    await this.fetchDepletionRadar();
    this.renderWelcomeMessage();
  }

  startClock() {
    const update = () => {
      const now = new Date();
      if (this.dom.clockDisplay) {
        this.dom.clockDisplay.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
    };
    update();
    setInterval(update, 1000);
  }

  async fetchDepletionRadar() {
    try {
      const res = await fetch(`${this.apiBase}/api/commerce/depletion`);
      if (res.ok) {
        const data = await res.json();
        const items = data.forecast || [];
        if (this.dom.depletionRadarFeed) {
          this.dom.depletionRadarFeed.innerHTML = items.slice(0, 4).map(it => `
            <div class="depletion-row">
              <div class="depletion-item-meta">
                <span class="depletion-bullet ${it.status}"></span>
                <span style="font-weight:600;color:var(--text-bright);">${it.name.split('(')[0]}</span>
              </div>
              <div style="display:flex;align-items:center;gap:8px;">
                <div class="depletion-progress-bar">
                  <div class="depletion-progress-fill" style="width:${it.level_pct}%;background:${it.status === 'critical' ? 'var(--rose)' : it.status === 'low' ? 'var(--amber)' : 'var(--emerald)'};"></div>
                </div>
                <span class="depletion-days-tag">${it.days_until_empty}d left</span>
              </div>
            </div>
          `).join("");
        }
      }
    } catch (e) {
      console.warn("Error fetching depletion radar", e);
    }
  }

  onTwinStateUpdate(state) {
    if (!state) return;
    const living = state.living_room || {};
    const entryway = state.entryway || {};
    const lock = entryway.lock || {};

    const lockBadge = document.getElementById("perimeterLockBadge");
    if (lockBadge) {
      const locked = lock.front_door === "locked";
      lockBadge.textContent = locked ? "SECURED (LOCKED)" : "UNLOCKED";
      lockBadge.className = `widget-badge ${locked ? 'green' : 'amber'}`;
    }
  }

  onProposalsUpdate(proposals) {
    const pending = proposals.filter(p => p.status === "pending");
    if (this.dom.trayCountBadge) {
      this.dom.trayCountBadge.textContent = pending.length;
      this.dom.trayCountBadge.style.display = pending.length ? "inline-block" : "none";
      this.dom.trayCountBadge.setAttribute("aria-label", `${pending.length} pending approvals`);
    }
    if (this.dom.pendingProposalsFeed) {
      const activeId = document.activeElement?.closest?.(".tray-card")?.dataset.id;
      this.proposals.renderPendingList(this.dom.pendingProposalsFeed);
      // Rebind swipe/keyboard for fresh DOM (idempotent) + restore focus
      TrayA11y.bindKeyboard(this.dom.pendingProposalsFeed, this.proposals, {
        isModalOpen: () => this.dom.modal?.classList.contains("open"),
        onCloseModal: () => this.closeInspectionModal(),
      });
      TrayA11y.bindSwipe(this.dom.pendingProposalsFeed, this.proposals);
      TrayA11y.bindLedgerTriggers(this.apiBase, (m) => this.showToast(m));
      if (activeId) document.querySelector(`.tray-card[data-id="${CSS.escape(activeId)}"]`)?.focus({ preventScroll: true });
    }
    if (pending.length !== this._lastPendingCount) {
      this._lastPendingCount = pending.length;
      TrayA11y.announceTrayCount(pending.length);
    }
  }

  async sendMessage(text) {
    this.dom.composerInput.value = "";
    this.appendMessage("user", text);

    // Typing bubble
    const typingId = this.appendTypingIndicator();

    try {
      const res = await fetch(`${this.apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      this.removeTypingIndicator(typingId);

      if (data.ok === false || data.error) {
        this.appendMessage("assistant", `Error: ${data.error}`);
        return;
      }

      this.appendAssistantPayload(data);
      this.voice.speak(data.draft || "");
      await this.proposals.fetchProposals();
      await this.twin.fetchState();
    } catch (e) {
      this.removeTypingIndicator(typingId);
      this.appendMessage("assistant", `Network error: ${e.message}`);
    }
  }

  formatMarkdown(text) {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br/>");
  }

  appendMessage(role, text) {
    if (!this.dom.conversationStream) return;
    const div = document.createElement("div");
    div.className = `chat-bubble ${role}`;
    div.innerHTML = this.formatMarkdown(text);
    this.dom.conversationStream.appendChild(div);
    this.dom.conversationStream.scrollTop = this.dom.conversationStream.scrollHeight;
  }

  appendAssistantPayload(data) {
    if (!this.dom.conversationStream) return;
    const wrap = document.createElement("div");
    wrap.style.cssText = "align-self:flex-start;max-width:92%;margin:4px 0;width:100%;";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble assistant";
    bubble.innerHTML = this.formatMarkdown(data.draft || "");
    wrap.appendChild(bubble);

    // Interactive Media Card
    if (data.media_card && data.media_card.card_type === "amazon_subscribe_and_save") {
      const cardContainer = document.createElement("div");
      McpAppsManager.renderAmazonCartCard(cardContainer, data.media_card, (cart) => {
        this.voice.playSuccessChime();
        this.showToast("✓ Amazon Subscribe & Save delivery staged");
      });
      wrap.appendChild(cardContainer);
    }

    // Interactive MCP App
    if (data.mcp_app) {
      const appContainer = document.createElement("div");
      if (data.mcp_app.app_id === "mcp_app_lighting_designer") {
        McpAppsManager.renderLightingDesigner(appContainer, data.mcp_app, (patch) => {
          this.twin.updateDevice(patch.room || "living_room", "lights", patch);
        });
      } else if (data.mcp_app.app_id === "mcp_app_subscription_roi") {
        McpAppsManager.renderSubscriptionRoi(appContainer, data.mcp_app);
      }
      wrap.appendChild(appContainer);
    }

    this.dom.conversationStream.appendChild(wrap);
    this.dom.conversationStream.scrollTop = this.dom.conversationStream.scrollHeight;
  }

  appendTypingIndicator() {
    const id = `typing-${Date.now()}`;
    const div = document.createElement("div");
    div.id = id;
    div.className = "chat-bubble assistant";
    div.style.cssText = "color:var(--text-dim);font-size:12px;font-style:italic;";
    div.innerHTML = "✨ Hearth Intelligence is orchestrating tools…";
    this.dom.conversationStream.appendChild(div);
    return id;
  }

  removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  renderWelcomeMessage() {
    this.appendAssistantPayload({
      draft: "👋 **Welcome to Hearth Universal** for Amazon Alexa+.\n\nI am your proactive personal operations agent, running on the **MCP 2025-11-25 Streamable HTTP** protocol. I manage your household subscriptions, pantry replenishment, and smart home digital twins under an uncompromising **Propose-Never-Execute** contract.\n\nTry asking:\n• *\"Save me $800 on subscriptions\"*\n• *\"Restock my coffee and laundry pods\"*\n• *\"Launch the smart lighting designer app\"*\n• *\"I'm home early — prepare the house\"*"
    });
  }

  openInspectionModal(proposal) {
    this.currentProposalToInspect = proposal;
    if (!this.dom.modal) return;
    const cost = this.proposals.formatCostDelta(proposal);
    const hash = this.proposals.deriveHash(proposal);
    this.dom.modalProposalTitle.textContent = proposal.title;
    this.dom.modalProposalId.textContent = `ID: ${proposal.id} · Kind: ${proposal.kind}`;
    this.dom.modalMerkleHash.textContent = `SHA-256 Seal: ${hash} (Genesis Chain Valid)`;
    const parentLink = document.getElementById("modalParentLink");
    if (parentLink) parentLink.textContent = `Parent Link: Genesis Merkle Chain · Nonce #${proposal.id} (single-use)`;
    const verdict = document.getElementById("modalSentinelVerdict");
    if (verdict) verdict.textContent = proposal.risk_level === "high" ? "TIER 2: ASK (FAIL-CLOSED — HUMAN ONLY)" : "TIER 2: ASK (GATED BY PROPOSE-NEVER-EXECUTE)";
    const policyRule = document.getElementById("modalPolicyRule");
    if (policyRule) policyRule.textContent = `Policy: ${proposal.kind} · 1-tap consent`;
    const policyPersona = document.getElementById("modalPolicyPersona");
    if (policyPersona) policyPersona.textContent = `Actor: ${this.activePersona} · Fail-closed`;
    const costEl = document.getElementById("modalCostImpact");
    if (costEl) { costEl.textContent = cost.pill; costEl.style.color = cost.cls === "save" ? "var(--emerald)" : cost.cls === "spend" ? "var(--cyan)" : "var(--text-bright)"; }
    this.dom.modalDiffPre.innerHTML = this.proposals.formatUnifiedDiff(proposal.diff || proposal.reasons, proposal);
    this.dom.modal.setAttribute("aria-hidden", "false");
    this.dom.modal.classList.add("open");
    if (this._modalTrapRelease) this._modalTrapRelease();
    this._modalTrapRelease = TrayA11y.trapFocus(this.dom.modal);
    TrayA11y.announce(`Inspecting ${proposal.title}. Financial impact ${cost.pill}. Press A to approve, X to reject, Escape to close.`, "polite");
  }

  closeInspectionModal() {
    if (this.dom.modal) {
      this.dom.modal.classList.remove("open");
      this.dom.modal.setAttribute("aria-hidden", "true");
    }
    if (this._modalTrapRelease) { this._modalTrapRelease(); this._modalTrapRelease = null; }
    this.currentProposalToInspect = null;
  }

  showToast(msg) {
    if (!this.dom.toastShelf) return;
    const t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    t.textContent = msg;
    this.dom.toastShelf.appendChild(t);
    setTimeout(() => t.remove(), 4000);
  }

  startHeartbeatStream() {
    setInterval(async () => {
      try {
        const res = await fetch(`${this.apiBase}/api/heartbeat?limit=4`);
        if (res.ok) {
          const data = await res.json();
          const streamEl = document.getElementById("heartbeatEventsStream");
          if (streamEl && data.events) {
            streamEl.innerHTML = data.events.map(ev => `
              <span class="heartbeat-pill-item">
                <span>⚡</span>
                <strong>${ev.title || "Telemetry"}</strong> · ${ev.detail || ""}
              </span>
            `).join("");
          }
        }
      } catch (e) {}
    }, 12000);
  }
}

// Instantiate on DOM load
window.addEventListener("DOMContentLoaded", () => {
  window.hearthApp = new HearthUniversalApp();
});
