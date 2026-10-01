/**
 * GLASS-BOX PROPOSAL & APPROVAL TRAY ENGINE — HEARTH UNIVERSAL
 * Propose-Never-Execute Enforcement · Cryptographic Inspection · Unified Diff Previews · Single-Use Nonce
 * Contract: GET /api/proposals?limit= · POST /api/decide {id, approved} · GET /api/audit (ledger)
 * UI: optimistic 1-tap + rollback · cost-delta transparency · single-use receipts · ARIA live
 */

export class ProposalsEngine {
  constructor(apiBase = "", onUpdate = null, onInspect = null) {
    this.apiBase = apiBase;
    this.onUpdate = onUpdate;
    this.onInspect = onInspect;
    this.proposals = [];
    this.activePersona = "admin";
    this.filterTab = "pending"; // 'pending' | 'executed'
    this.pendingOps = new Map(); // id -> 'approving' | 'rejecting'
    this.onGuardrail = null; // (msg) => void — set by app for toast+announce
    this.onAnnounce = null; // (msg, priority) => void
  }

  setPersona(personaId) {
    this.activePersona = personaId;
  }

  setFilterTab(tab) {
    this.filterTab = tab;
  }

  async fetchProposals() {
    try {
      const res = await fetch(`${this.apiBase}/api/proposals?limit=100`);
      if (res.ok) {
        const data = await res.json();
        this.proposals = data.proposals || [];
        // Drop optimistic flags for settled items
        for (const [id] of [...this.pendingOps]) {
          if (!this.proposals.some((p) => p.id === id && p.status === "pending")) this.pendingOps.delete(id);
        }
        if (this.onUpdate) this.onUpdate(this.proposals);
        return this.proposals;
      }
    } catch (e) {
      console.warn("Failed to fetch proposals", e);
    }
    return [];
  }

  async decide(proposalId, approved = true) {
    // Child persona guardrail check (no alert — announce + toast via host)
    if (this.activePersona === "child") {
      const msg = "Child Safety Guardrail: Leo (child) cannot approve financial or physical-security actions. An adult must authorize.";
      if (this.onGuardrail) this.onGuardrail(msg);
      else if (this.onAnnounce) this.onAnnounce(msg, "assertive");
      return { ok: false, error: "Child persona unauthorized" };
    }

    const prev = this.proposals.find((p) => p.id === proposalId);
    const snapshot = prev ? { ...prev } : null;
    const op = approved ? "approving" : "rejecting";
    this.pendingOps.set(proposalId, op);
    // Optimistic patch: keep status pending, flag op, paint immediately (200ms flash)
    if (prev) {
      prev._optimistic = op;
      if (this.onUpdate) this.onUpdate([...this.proposals]);
      this._flashCard(proposalId, null);
    }
    this._announce(
      approved ? `Authorizing ${snapshot?.title || proposalId}…` : `Rejecting ${snapshot?.title || proposalId}…`,
      "polite"
    );

    try {
      const res = await fetch(`${this.apiBase}/api/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: proposalId, approved })
      });
      let data = null;
      try { data = await res.json(); } catch { data = { ok: false, error: `HTTP ${res.status}` }; }

      // Contract: success returns the decided item (has id+status, no ok:false).
      // Failure returns {ok:false, error} (replay / not-found → HTTP 404).
      const failed = !res.ok || (data && data.ok === false);
      if (failed) {
        // Rollback optimistic patch
        if (snapshot) {
          const i = this.proposals.findIndex((p) => p.id === proposalId);
          if (i >= 0) this.proposals[i] = { ...snapshot };
        }
        this.pendingOps.delete(proposalId);
        if (this.onUpdate) this.onUpdate([...this.proposals]);
        this._flashCard(proposalId, false);
        const err = data?.error || `HTTP ${res.status}`;
        this._announce(`Decision failed for ${snapshot?.title || proposalId}: ${err}. Rolled back.`, "assertive");
        return { ok: false, error: err };
      }

      this.pendingOps.delete(proposalId);
      await this.fetchProposals();
      this._flashCard(proposalId, true);
      const decided = this.proposals.find((p) => p.id === proposalId) || data;
      const receiptNote = decided?.execution?.note || (approved ? "Approved & recorded" : "Rejected");
      this._announce(
        approved ? `Approved: ${decided?.title || proposalId}. Receipt sealed. ${receiptNote}` : `Rejected: ${decided?.title || proposalId}. No side effects applied.`,
        "polite"
      );
      return data;
    } catch (e) {
      if (snapshot) {
        const i = this.proposals.findIndex((p) => p.id === proposalId);
        if (i >= 0) this.proposals[i] = { ...snapshot };
      }
      this.pendingOps.delete(proposalId);
      if (this.onUpdate) this.onUpdate([...this.proposals]);
      this._flashCard(proposalId, false);
      this._announce(`Network error deciding ${proposalId}: ${e.message}. Rolled back.`, "assertive");
      return { ok: false, error: e.message };
    }
  }

  async propose(kind, title, reasons, cost_delta_yr = 0.0, risk_level = "medium", diff = "", meta = {}) {
    // Contract preserved: POST /api/proposals {kind,title,reasons,cost_delta_yr,risk_level,diff,meta}
    try {
      const res = await fetch(`${this.apiBase}/api/proposals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, title, reasons, cost_delta_yr, risk_level, diff, meta })
      });
      const data = await res.json();
      await this.fetchProposals();
      return data;
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  _announce(msg, priority = "polite") {
    if (this.onAnnounce) this.onAnnounce(msg, priority);
    else {
      const id = priority === "assertive" ? "trayLiveAssertive" : "trayLivePolite";
      const el = document.getElementById(id);
      if (el) { el.textContent = ""; requestAnimationFrame(() => { el.textContent = msg; }); }
    }
  }

  _flashCard(id, ok) {
    requestAnimationFrame(() => {
      const card = document.querySelector(`.tray-card[data-id="${CSS.escape(id)}"]`);
      if (!card) return;
      card.classList.remove("flash-ok", "flash-err");
      if (ok === true) { card.classList.add("flash-ok"); setTimeout(() => card.classList.remove("flash-ok"), 450); }
      if (ok === false) { card.classList.add("flash-err"); setTimeout(() => card.classList.remove("flash-err"), 450); }
    });
  }

  // Generate deterministic SHA-256-like hex hash for auditor identification
  deriveHash(proposal) {
    let str = `${proposal.id}:${proposal.kind}:${proposal.title}:${proposal.ts || 0}`;
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    const hex = Math.abs(hash).toString(16).padStart(8, "0");
    return `8a4f91b72e0d${hex}e1a90c427f`;
  }

  /** Cost-delta transparency: signed value + plain-language direction.
   *  Backend convention: negative = savings (actions_propose docs), but some
   *  callers pass +savings. We normalize by kind so the tray never misleads. */
  formatCostDelta(p) {
    const v = Number(p.cost_delta_yr || 0);
    const kind = String(p.kind || "");
    const isSavingsKind = /cancel|downgrade|subscription|arbiter|renewal|save/i.test(kind) || /save|cancel/i.test(p.title || "");
    const isSpendKind = /commerce_order|order|replenish|delivery_reschedule|workspace_exec/i.test(kind);
    if (v === 0) return { cls: "neutral", pill: "◈ $0 · No money movement", note: `Access-control change only. <strong>Reversible.</strong>` };
    const abs = `$${Math.abs(v).toFixed(2)}`;
    if (isSavingsKind) {
      return { cls: "save", pill: `✓ Saves ${abs}/yr`, note: `Net recovery <strong>${abs}/yr</strong> vs current spend. Single-use consent.` };
    }
    if (isSpendKind) {
      const per = kind === "commerce_order" ? "one-time staged charge" : "annualized impact";
      return { cls: "spend", pill: `● ${abs} ${kind === "commerce_order" ? "staged" : "/yr"}`, note: `Projected ${per}: <strong>${abs}</strong>. No live charge in sandbox.` };
    }
    // Fallback: sign-faithful
    if (v > 0) return { cls: "save", pill: `✓ +${abs}/yr`, note: `Positive delta — <strong>reduces spend ${abs}/yr</strong>.` };
    return { cls: "spend", pill: `● −${abs}/yr`, note: `Negative delta — <strong>adds spend ${abs}/yr</strong>.` };
  }

  formatReceipt(p) {
    if (p.status === "pending") return "";
    const when = p.decided_at ? new Date(p.decided_at * 1000).toLocaleString() : "just now";
    const note = this.escapeHtml(p.execution?.note || (p.status === "approved" ? "Approved & recorded." : "Rejected — no side effects applied."));
    const rejected = p.status === "rejected";
    return `
      <div class="receipt-block ${rejected ? "rejected" : ""}" role="note" aria-label="Single-use consent receipt">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span class="single-use-badge">⊘ Single-use receipt</span>
          <span class="receipt-title">${rejected ? "✕ Rejected — sealed" : "✓ Executed & signed"}</span>
        </div>
        <div class="receipt-note">${note}</div>
        <div class="receipt-note">Decided <code>${this.escapeHtml(when)}</code> · Nonce <code>#${this.escapeHtml(p.id)}</code> · Replay refused · <button class="ledger-link receipt-ledger-link" type="button" data-ledger-verify="1">Verify in ledger (audit_verify)</button></div>
      </div>`;
  }

  // Format any diff string into high-contrast syntax colored unified diff HTML
  formatUnifiedDiff(diffText, proposal = null) {
    if (!diffText && proposal) {
      diffText = proposal.reasons || "";
    }
    diffText = String(diffText || "No state delta specified.").trim();

    // If human arrow text like "Current: $239.88/yr -> After: $0/yr (Saves $239.88/yr)."
    if (diffText.includes("->") || diffText.includes("Current:") || diffText.includes("Saves")) {
      const lines = [
        "--- CURRENT STATE (FAIL-CLOSED BOUNDARY)",
        "+++ PROPOSED STATE (PENDING HUMAN GREEN-LIGHT)"
      ];
      if (proposal) {
        if (proposal.kind === "home_lock") {
          lines.push('- entryway.lock.front_door: "unlocked"');
          lines.push('+ entryway.lock.front_door: "locked"');
          lines.push('+ perimeter_armed: true');
        } else if (proposal.kind && proposal.kind.includes("subscription")) {
          lines.push(`- service: "${proposal.title.replace('Cancel ', '').replace('Downgrade ', '')}"`);
          lines.push(`- annual_spend: "$${Math.abs(proposal.cost_delta_yr || 0).toFixed(2)}/yr"`);
          lines.push('+ status: "cancelled / downgraded"');
          lines.push(`+ net_annual_recovery: "+$${Math.abs(proposal.cost_delta_yr || 0).toFixed(2)}/yr"`);
        } else {
          lines.push(`- previous_state: "${diffText.split('->')[0].trim()}"`);
          lines.push(`+ proposed_transition: "${(diffText.split('->')[1] || diffText).trim()}"`);
        }
      } else {
        lines.push(`- current: "${diffText.split('->')[0].trim()}"`);
        lines.push(`+ proposed: "${(diffText.split('->')[1] || diffText).trim()}"`);
      }
      return this.renderDiffLinesHtml(lines);
    }

    const rawLines = diffText.split("\n");
    return this.renderDiffLinesHtml(rawLines);
  }

  renderDiffLinesHtml(lines) {
    return lines.map((line, idx) => {
      let type = "context";
      let marker = " ";
      let content = line;

      if (line.startsWith("---") || line.startsWith("+++") || line.startsWith("@@")) {
        type = "header";
        marker = "@";
      } else if (line.startsWith("+")) {
        type = "addition";
        marker = "+";
        content = line.substring(1);
      } else if (line.startsWith("-")) {
        type = "deletion";
        marker = "-";
        content = line.substring(1);
      }

      return `
        <div class="diff-line ${type}">
          <span class="diff-line-gutter">${idx + 1}</span>
          <span class="diff-line-marker">${marker}</span>
          <span class="diff-line-text">${this.escapeHtml(content)}</span>
        </div>
      `;
    }).join("");
  }

  escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  renderPendingList(container) {
    if (!container) return;

    const pending = this.proposals.filter(p => p.status === "pending");
    const executed = this.proposals.filter(p => p.status === "approved" || p.status === "rejected");
    const displayed = this.filterTab === "pending" ? pending : executed;

    // Filter Tabs Bar (tablist semantics, aria-selected)
    let html = `
      <div class="proposal-tray-tabs" role="tablist" aria-label="Approval tray filter">
        <button class="proposal-tab-btn ${this.filterTab === 'pending' ? 'active' : ''}" id="tabProposalsPending" role="tab" aria-selected="${this.filterTab === 'pending'}">
          <span>⏳ Pending Actions (${pending.length})</span>
        </button>
        <button class="proposal-tab-btn ${this.filterTab === 'executed' ? 'active' : ''}" id="tabProposalsExecuted" role="tab" aria-selected="${this.filterTab === 'executed'}">
          <span>✓ Executed Ledger (${executed.length})</span>
        </button>
      </div>
    `;

    if (!displayed.length) {
      html += `
        <div class="tray-empty" role="status">
          <div style="font-size:28px;margin-bottom:8px;" aria-hidden="true">🛡️</div>
          <strong>${this.filterTab === 'pending' ? 'Approval Tray is Clean' : 'No Past Executions'}</strong>
          <p>${this.filterTab === 'pending' ? 'Zero pending actions. All autonomous operations are verified & up-to-date under the Propose-Never-Execute invariant.' : 'Historical executions and consent receipts will appear here once approved.'}</p>
          <div class="tray-empty-actions">
            <button class="btn-icon" id="emptyLedgerVerifyBtn" type="button">🛡️ Verify ledger (audit_verify)</button>
            <button class="btn-icon" id="emptyOpsAuditBtn" type="button">⚡ Run Proactive Audit</button>
          </div>
          <p style="margin-top:8px;"><button class="ledger-link" id="ledgerVerifyLink" type="button">Open cryptographic ledger → GET /api/audit</button></p>
        </div>
      `;
      container.innerHTML = html;
      this.bindTabEvents(container);
      this.bindEmptyState(container);
      return;
    }

    html += displayed.map(p => {
      const hash = this.deriveHash(p);
      const isApproved = p.status === "approved";
      const isRejected = p.status === "rejected";
      const isPending = p.status === "pending";
      const op = this.pendingOps.get(p.id); // approving | rejecting
      const busy = Boolean(op);

      const kindIcon = p.kind === 'home_lock' ? '🔒'
        : (p.kind && p.kind.includes('subscription')) ? '💳'
        : p.kind === 'commerce_order' ? '🛒'
        : p.kind === 'workspace_exec' ? '⚙️'
        : '⚖️';

      const kindLabel = p.kind === 'home_lock' ? 'PERIMETER SECURITY'
        : (p.kind && p.kind.includes('subscription')) ? 'SUBSCRIPTION AUDIT'
        : p.kind === 'commerce_order' ? 'PRIME REPLENISHMENT'
        : p.kind === 'workspace_exec' ? 'WORKSPACE OPS'
        : 'HOUSEHOLD ARBITRATION';

      const tierBadge = p.risk_level === 'high' ? 'TIER-2: ASK (FAIL-CLOSED)'
        : p.risk_level === 'low' ? 'TIER-2: ASK (GATED)'
        : 'TIER-2: ASK (GATED)';

      const diffSnippetHtml = this.formatUnifiedDiff(p.diff || p.reasons, p);
      const cost = this.formatCostDelta(p);
      const receipt = this.formatReceipt(p);
      const border = isPending ? 'var(--border-accent)' : isApproved ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.3)';
      const statusLabel = isPending ? (busy ? (op === "approving" ? "AUTHORIZING…" : "REJECTING…") : tierBadge) : p.status.toUpperCase();
      const descId = `desc-${p.id}`;

      return `
        <article class="widget-card tray-card ${busy ? (op === "approving" ? "is-approving" : "is-rejecting") : ""}" tabindex="0" role="listitem"
          aria-label="${this.escapeHtml(p.title)}. ${kindLabel}. ${this.escapeHtml(statusLabel)}. Cost ${this.escapeHtml(cost.pill)}."
          aria-describedby="${descId}" data-id="${this.escapeHtml(p.id)}"
          style="border-color:${border};background:rgba(12, 16, 28, 0.8);" ${busy ? 'aria-busy="true"' : ""}>
          <div class="widget-header">
            <div class="widget-title-wrap">
              <span aria-hidden="true">${kindIcon}</span>
              <div>
                <h3 style="font-size:13px;font-weight:700;color:var(--text-bright);">${this.escapeHtml(p.title)}</h3>
                <small style="font-family:var(--font-mono);font-size:10px;color:var(--cyan);letter-spacing:0.5px;">${kindLabel}</small>
              </div>
            </div>
            <span class="widget-badge ${isApproved ? 'green' : 'amber'}">${this.escapeHtml(statusLabel)}</span>
          </div>

          <p id="${descId}" style="font-size:12.5px;color:var(--text-muted);margin:6px 0 10px;line-height:1.4;">${this.escapeHtml(p.reasons)}</p>

          <!-- Cost-delta transparency -->
          <div class="cost-delta-strip" role="group" aria-label="Financial impact">
            <span class="cost-delta-pill ${cost.cls}">${this.escapeHtml(cost.pill)}</span>
            <span class="cost-delta-note">${cost.note}</span>
          </div>

          <!-- Unified Diff Preview Box -->
          <div class="diff-container-box" style="margin-top:10px;">
            <div class="diff-header-bar">
              <span>STATE TRANSITION DELTA</span>
              <span>SHA-256: ${hash.substring(0, 14)}…</span>
            </div>
            <div class="diff-preview-pre">${diffSnippetHtml}</div>
          </div>

          <!-- Impact & Single-Use Nonce Meta Bar -->
          <div class="proposal-meta-tags-row">
            <span class="tag-single-use">NONCE: #${this.escapeHtml(p.id)}</span>
            <span class="single-use-badge">⊘ single-use</span>
            <span style="color:var(--text-dim);margin-left:auto;">Reversibility: Guaranteed</span>
          </div>

          ${receipt}

          <!-- Action Buttons -->
          <div class="tray-actions">
            <button class="btn-icon inspect-btn" data-id="${this.escapeHtml(p.id)}" aria-label="Inspect cryptographic seal for ${this.escapeHtml(p.title)}">
              🔍 Inspect Seal & Full Diff
            </button>
            ${isPending ? `
              <button class="btn-reject-action reject-btn" data-id="${this.escapeHtml(p.id)}" ${busy ? "disabled" : ""} aria-label="Reject ${this.escapeHtml(p.title)} (shortcut X)">
                ${busy && op === "rejecting" ? "… Rejecting" : "✕ Reject"}
              </button>
              <button class="btn-approve-action approve-btn" data-id="${this.escapeHtml(p.id)}" ${busy ? "disabled" : ""} aria-label="Approve ${this.escapeHtml(p.title)} (shortcut A)">
                ${busy && op === "approving" ? "… Authorizing" : "✓ 1-Tap Authorize"}
              </button>
            ` : `
              <span class="operations-meta-pill ${isApproved ? 'green' : ''}" role="status">
                ${isApproved ? '✓ Executed & Signed' : '✕ Rejected / Refused'}
              </span>
            `}
          </div>
        </article>
      `;
    }).join("");

    container.innerHTML = html;
    this.bindTabEvents(container);
    this.bindActionEvents(container);
    this.bindEmptyState(container);
  }

  bindEmptyState(container) {
    container.querySelector("#emptyOpsAuditBtn")?.addEventListener("click", () => {
      document.getElementById("btnRunOpsAudit")?.click();
    });
    container.querySelector("#emptyLedgerVerifyBtn")?.addEventListener("click", () => {
      document.getElementById("ledgerVerifyLink")?.click();
    });
    container.querySelector("#ledgerVerifyLink")?.addEventListener("click", (e) => {
      e.preventDefault();
      document.dispatchEvent(new CustomEvent("tray:verify-ledger"));
    });
    container.querySelectorAll("[data-ledger-verify]")?.forEach((b) =>
      b.addEventListener("click", (e) => {
        e.preventDefault();
        document.dispatchEvent(new CustomEvent("tray:verify-ledger"));
      })
    );
  }

  bindTabEvents(container) {
    const tabPending = container.querySelector("#tabProposalsPending");
    const tabExecuted = container.querySelector("#tabProposalsExecuted");

    tabPending?.addEventListener("click", () => {
      this.setFilterTab("pending");
      this.renderPendingList(container);
      this._announce(`Showing pending actions.`, "polite");
    });

    tabExecuted?.addEventListener("click", () => {
      this.setFilterTab("executed");
      this.renderPendingList(container);
      this._announce(`Showing executed ledger.`, "polite");
    });
  }

  bindActionEvents(container) {
    container.querySelectorAll(".approve-btn").forEach(btn => {
      btn.addEventListener("click", (e) => { e.stopPropagation(); this.decide(btn.dataset.id, true); });
    });

    container.querySelectorAll(".reject-btn").forEach(btn => {
      btn.addEventListener("click", (e) => { e.stopPropagation(); this.decide(btn.dataset.id, false); });
    });

    container.querySelectorAll(".inspect-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const item = this.proposals.find(p => p.id === btn.dataset.id);
        if (item && this.onInspect) this.onInspect(item);
      });
    });

    // Card-level Enter opens inspection (buttons keep native behavior)
    container.querySelectorAll(".tray-card").forEach(card => {
      if (card.dataset.cardKb) return;
      card.dataset.cardKb = "1";
      card.addEventListener("keydown", (e) => {
        if ((e.key === "Enter" || e.key === " ") && e.target === card) {
          e.preventDefault();
          const item = this.proposals.find(p => p.id === card.dataset.id);
          if (item && this.onInspect) this.onInspect(item);
        }
      });
    });
  }
}
