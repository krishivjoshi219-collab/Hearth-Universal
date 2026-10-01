/**
 * GLASS-BOX APPROVAL TRAY — A11Y + INTERACTION CONTROLLER
 * Focus trap · keyboard shortcuts · swipe · ARIA live · ledger link
 * No API contract changes. Works against GET /api/proposals, POST /api/decide, GET /api/audit.
 */

export const TrayA11y = {
  lastFocused: null,
  trapRelease: null,

  ensureLiveRegions(root = document) {
    if (!root.getElementById("trayLivePolite")) {
      const p = document.createElement("div");
      p.id = "trayLivePolite";
      p.className = "sr-only";
      p.setAttribute("role", "status");
      p.setAttribute("aria-live", "polite");
      p.setAttribute("aria-atomic", "true");
      document.body.appendChild(p);
    }
    if (!root.getElementById("trayLiveAssertive")) {
      const a = document.createElement("div");
      a.id = "trayLiveAssertive";
      a.className = "sr-only";
      a.setAttribute("role", "alert");
      a.setAttribute("aria-live", "assertive");
      a.setAttribute("aria-atomic", "true");
      document.body.appendChild(a);
    }
  },

  announce(msg, priority = "polite") {
    this.ensureLiveRegions();
    const id = priority === "assertive" ? "trayLiveAssertive" : "trayLivePolite";
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = "";
    // Force SR re-read even for identical strings
    requestAnimationFrame(() => { el.textContent = msg; });
  },

  announceTrayCount(pending) {
    if (pending === 0) this.announce("Approval tray is clean. Zero pending actions.");
    else this.announce(`${pending} action${pending === 1 ? "" : "s"} awaiting approval in the Glass-Box tray.`);
  },

  /* Focus trap for modal. Returns release fn. */
  trapFocus(modal) {
    if (!modal) return () => {};
    this.lastFocused = document.activeElement;
    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const onKey = (e) => {
      if (e.key === "Tab") {
        const items = [...modal.querySelectorAll(selector)].filter((el) => !el.disabled && el.offsetParent !== null);
        if (!items.length) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    modal.addEventListener("keydown", onKey);
    // Focus first primary action (approve) else close
    const target = modal.querySelector("#modalApproveBtn") || modal.querySelector(".modal-close-trigger");
    setTimeout(() => target?.focus(), 60);
    return () => {
      modal.removeEventListener("keydown", onKey);
      if (this.lastFocused?.focus) this.lastFocused.focus();
      this.lastFocused = null;
    };
  },

  /* Keyboard shortcuts: j/k navigate, a approve, x deny, Enter/i inspect, Esc close */
  bindKeyboard(feedEl, engine, opts = {}) {
    if (!feedEl || feedEl.dataset.kbBound) return;
    feedEl.dataset.kbBound = "1";
    const isTyping = () => {
      const t = document.activeElement;
      return t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable);
    };
    document.addEventListener("keydown", (e) => {
      // Esc always closes modal
      if (e.key === "Escape" && opts.isModalOpen?.()) { opts.onCloseModal?.(); return; }
      if (isTyping()) return;
      // Only when ops view visible or tray focused
      const trayCard = document.getElementById("opsProposalTrayCard");
      if (trayCard && trayCard.offsetParent === null) return;

      const cards = [...feedEl.querySelectorAll(".tray-card")];
      if (!cards.length) return;
      const idx = cards.indexOf(document.activeElement?.closest?.(".tray-card") || document.activeElement);
      const focusedCard = document.activeElement?.closest?.(".tray-card");
      const focusAt = (i) => {
        const c = cards[Math.max(0, Math.min(cards.length - 1, i))];
        c?.focus();
        c?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      };

      if (e.key === "j" || e.key === "ArrowDown") { e.preventDefault(); focusAt(idx < 0 ? 0 : idx + 1); }
      else if (e.key === "k" || e.key === "ArrowUp") { e.preventDefault(); focusAt(idx <= 0 ? 0 : idx - 1); }
      else if ((e.key === "a" || e.key === "A") && focusedCard) {
        e.preventDefault();
        engine.decide(focusedCard.dataset.id, true);
      }
      else if ((e.key === "x" || e.key === "X" || e.key === "d" || e.key === "D") && focusedCard) {
        e.preventDefault();
        engine.decide(focusedCard.dataset.id, false);
      }
      else if ((e.key === "Enter" || e.key === "i" || e.key === "I") && focusedCard && document.activeElement === focusedCard) {
        e.preventDefault();
        const item = engine.proposals.find((p) => p.id === focusedCard.dataset.id);
        if (item && engine.onInspect) engine.onInspect(item);
      }
    });
  },

  /* Mobile swipe: right = approve, left = reject. Visual translate, 60px threshold. */
  bindSwipe(feedEl, engine) {
    if (!feedEl || feedEl.dataset.swipeBound) return;
    feedEl.dataset.swipeBound = "1";
    let startX = 0, startY = 0, curCard = null;

    feedEl.addEventListener("touchstart", (e) => {
      const card = e.target.closest?.(".tray-card");
      if (!card) return;
      const t = e.touches[0];
      startX = t.clientX; startY = t.clientY; curCard = card;
    }, { passive: true });

    feedEl.addEventListener("touchmove", (e) => {
      if (!curCard) return;
      const t = e.touches[0];
      const dx = t.clientX - startX;
      const dy = t.clientY - startY;
      if (Math.abs(dy) > 40) return; // vertical scroll wins
      if (dx > 24) { curCard.classList.add("swipe-right"); curCard.classList.remove("swipe-left"); }
      else if (dx < -24) { curCard.classList.add("swipe-left"); curCard.classList.remove("swipe-right"); }
    }, { passive: true });

    feedEl.addEventListener("touchend", (e) => {
      if (!curCard) return;
      const t = e.changedTouches[0];
      const dx = t.clientX - startX;
      const card = curCard;
      card.classList.remove("swipe-right", "swipe-left");
      curCard = null;
      if (Math.abs(dx) < 60) return;
      const id = card.dataset.id;
      const item = engine.proposals.find((p) => p.id === id);
      if (!item || item.status !== "pending") return;
      if (navigator.vibrate) { try { navigator.vibrate(12); } catch {} }
      engine.decide(id, dx > 0);
    }, { passive: true });
  },

  /* Ledger verification link → GET /api/audit (audit_verify contract surface) */
  async verifyLedger(apiBase, onToast = null) {
    try {
      const res = await fetch(`${apiBase}/api/audit`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const msg = data.valid
        ? `Ledger verified — SHA-256 chain intact (${data.count} sealed entries).`
        : `Ledger verification FAILED — chain tamper detected.`;
      this.announce(msg, data.valid ? "polite" : "assertive");
      onToast?.(data.valid ? `🛡️ ${msg}` : `⛔ ${msg}`);
      const badge = document.getElementById("merkleVerifiedBadge");
      if (badge) {
        badge.textContent = data.valid ? "CHAIN VERIFIED ✓" : "CHAIN TAMPER ✕";
        badge.className = `widget-badge ${data.valid ? "green" : "amber"}`;
      }
      const opsPill = document.getElementById("opsMerkleStatusPill");
      if (opsPill) opsPill.innerHTML = `<span class="beacon-pulse"></span><span>${data.valid ? "SHA-256 Chain Intact" : "Chain Tamper — Investigate"}</span>`;
      return data;
    } catch (e) {
      this.announce(`Ledger verification failed: ${e.message}`, "assertive");
      onToast?.(`Ledger check failed: ${e.message}`);
      return { valid: false, error: e.message };
    }
  },

  bindLedgerTriggers(apiBase, onToast) {
    if (this._ledgerBound) return;
    this._ledgerBound = true;
    document.addEventListener("tray:verify-ledger", () => this.verifyLedger(apiBase, onToast));
    document.getElementById("ledgerVerifyLink")?.addEventListener("click", (e) => {
      e.preventDefault(); this.verifyLedger(apiBase, onToast);
    });
    document.getElementById("btnVerifyAuditChain")?.addEventListener("click", () =>
      this.verifyLedger(apiBase, onToast));
  },
};
