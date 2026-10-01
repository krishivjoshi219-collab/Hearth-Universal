/**
 * INTERACTIVE MCP APPS — HEARTH UNIVERSAL
 * Client-Side Micro-App Renderers for Lighting Designer, Subscription ROI, & Amazon Restock
 */

export class McpAppsManager {
  // 1. SMART LIGHTING DESIGNER (COLOR WHEEL & AMBIENT PRESETS)
  static renderLightingDesigner(container, data = {}, onApply = null) {
    container.innerHTML = `
      <div class="mcp-app-wrapper">
        <div class="mcp-app-header">
          <div class="mcp-app-title">
            <span>🎨</span>
            <span>${data.title || "Smart Lighting Designer"}</span>
          </div>
          <span class="mcp-app-badge">Interactive MCP App</span>
        </div>
        <div class="lighting-designer-body">
          <div class="color-wheel-canvas-wrap">
            <canvas id="colorWheelCanvas" width="130" height="130"></canvas>
            <div class="color-wheel-reticle" id="wheelReticle"></div>
          </div>
          <div class="lighting-controls-col">
            <div class="slider-group-wrap">
              <div class="slider-meta-row">
                <span>Brightness</span>
                <strong id="liveBriLabel">80%</strong>
              </div>
              <input type="range" class="luxury-slider" id="liveBriSlider" min="5" max="100" value="80"/>
            </div>
            <div class="slider-group-wrap">
              <div class="slider-meta-row">
                <span>Color Temp (CCT)</span>
                <strong id="liveCctLabel">3200K</strong>
              </div>
              <input type="range" class="luxury-slider" id="liveCctSlider" min="2000" max="6500" value="3200"/>
            </div>
            <div class="lighting-presets-row">
              <button class="preset-chip-btn" data-color="#ff9d42" data-k="2200" data-b="40">🕯️ Warm</button>
              <button class="preset-chip-btn" data-color="#f4f8ff" data-k="5000" data-b="85">☀️ Focus</button>
              <button class="preset-chip-btn" data-color="#06b6d4" data-k="6500" data-b="70">⚡ Cyber</button>
              <button class="preset-chip-btn" data-color="#a855f7" data-k="3000" data-b="50">🎬 Violet</button>
            </div>
          </div>
        </div>
      </div>
    `;

    const canvas = container.querySelector("#colorWheelCanvas");
    const reticle = container.querySelector("#wheelReticle");
    const briSlider = container.querySelector("#liveBriSlider");
    const cctSlider = container.querySelector("#liveCctSlider");
    const briLabel = container.querySelector("#liveBriLabel");
    const cctLabel = container.querySelector("#liveCctLabel");

    // Draw circular color wheel
    if (canvas) {
      const ctx = canvas.getContext("2d");
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const r = cx - 2;

      for (let angle = 0; angle < 360; angle++) {
        const rad = (angle * Math.PI) / 180;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, rad, rad + 0.03);
        ctx.closePath();
        ctx.fillStyle = `hsl(${angle}, 90%, 55%)`;
        ctx.fill();
      }

      // Center white fade
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      grad.addColorStop(0, "rgba(255, 255, 255, 1)");
      grad.addColorStop(0.6, "rgba(255, 255, 255, 0.2)");
      grad.addColorStop(1, "transparent");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();

      canvas.addEventListener("click", (evt) => {
        const rect = canvas.getBoundingClientRect();
        const x = evt.clientX - rect.left;
        const y = evt.clientY - rect.top;
        reticle.style.left = `${x}px`;
        reticle.style.top = `${y}px`;

        const pixel = ctx.getImageData(x, y, 1, 1).data;
        const hex = `#${((1 << 24) + (pixel[0] << 16) + (pixel[1] << 8) + pixel[2]).toString(16).slice(1)}`;

        if (onApply) {
          onApply({
            room: data.room || "living_room",
            color: hex,
            bri: parseInt(briSlider.value, 10),
            temp_k: parseInt(cctSlider.value, 10)
          });
        }
      });
    }

    briSlider?.addEventListener("input", (e) => {
      briLabel.textContent = `${e.target.value}%`;
      if (onApply) onApply({ room: data.room || "living_room", bri: parseInt(e.target.value, 10) });
    });

    cctSlider?.addEventListener("input", (e) => {
      cctLabel.textContent = `${e.target.value}K`;
      if (onApply) onApply({ room: data.room || "living_room", temp_k: parseInt(e.target.value, 10) });
    });

    container.querySelectorAll(".preset-chip-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const color = btn.dataset.color;
        const k = parseInt(btn.dataset.k, 10);
        const b = parseInt(btn.dataset.b, 10);
        briSlider.value = b;
        briLabel.textContent = `${b}%`;
        cctSlider.value = k;
        cctLabel.textContent = `${k}K`;
        if (onApply) onApply({ room: data.room || "living_room", color, temp_k: k, bri: b });
      });
    });
  }

  // 2. SUBSCRIPTION ROI SIMULATOR
  static renderSubscriptionRoi(container, data = {}, onUpdate = null) {
    const scan = data.data || {};
    const subs = scan.subscriptions || [];
    const annualSpend = scan.total_annual_spend || 1463.64;
    const potentialSavings = scan.potential_annual_savings || 803.76;

    container.innerHTML = `
      <div class="mcp-app-wrapper">
        <div class="mcp-app-header">
          <div class="mcp-app-title">
            <span>💳</span>
            <span>${data.title || "Subscription ROI Optimizer"}</span>
          </div>
          <span class="mcp-app-badge">Interactive MCP App</span>
        </div>
        <div class="roi-simulator-body">
          <div class="roi-stat-hero-row">
            <div class="roi-figure-wrap">
              <h4>$${potentialSavings.toFixed(2)}/yr</h4>
              <p>Actionable Recoverable Savings</p>
            </div>
            <div style="text-align:right;">
              <span class="widget-badge green">Audit Complete</span>
              <div style="font-size:11px;color:var(--text-dim);margin-top:4px;">5 Recurring Accounts</div>
            </div>
          </div>
          
          <div class="slider-group-wrap">
            <div class="slider-meta-row">
              <span>Target Household Monthly Entertainment Budget</span>
              <strong id="budgetTargetLabel">$65/mo</strong>
            </div>
            <input type="range" class="luxury-slider" id="budgetSlider" min="20" max="200" value="65"/>
          </div>

          <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px;">
            ${subs.map(s => `
              <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-radius:var(--radius-sm);background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);font-size:12px;">
                <div>
                  <strong>${s.name}</strong>
                  <div style="font-size:11px;color:var(--text-dim);">${s.usage_status}</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-family:var(--font-mono);font-weight:700;">$${s.cost_monthly}/mo</div>
                  <span style="font-size:10px;color:${s.recommendation === 'keep' ? 'var(--emerald)' : 'var(--amber)'};text-transform:uppercase;">${s.recommendation}</span>
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;

    const slider = container.querySelector("#budgetSlider");
    const label = container.querySelector("#budgetTargetLabel");
    slider?.addEventListener("input", (e) => {
      label.textContent = `$${e.target.value}/mo`;
    });
  }

  // 3. AMAZON REPLENISHMENT MEDIA CARD
  static renderAmazonCartCard(container, cartData = {}, onApprove = null) {
    const items = cartData.items || [];
    const total = cartData.final_total || 34.41;
    const savings = cartData.savings || 6.08;

    container.innerHTML = `
      <div class="amazon-media-card">
        <div class="amazon-card-header">
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="prime-brand-badge">prime</span>
            <span style="font-size:13px;font-weight:700;color:var(--text-bright);">Subscribe & Save Cart</span>
          </div>
          <span class="discount-tag-orange">SAVE 15%</span>
        </div>

        <div class="amazon-cart-items-list">
          ${items.map(it => `
            <div class="amazon-cart-item">
              <div class="item-left-info">
                <div class="item-thumb-box">${it.name.includes("Coffee") ? "☕" : it.name.includes("Laundry") ? "🧼" : "📦"}</div>
                <div>
                  <div style="font-weight:600;color:var(--text-bright);">${it.name}</div>
                  <div style="font-size:11px;color:var(--text-muted);">${it.prime_delivery || "Prime FREE Delivery"}</div>
                </div>
              </div>
              <div class="item-pricing">
                <div class="item-sale-price">$${it.unit_price.toFixed(2)}</div>
                <div class="item-reg-price">$${it.original_price.toFixed(2)}</div>
              </div>
            </div>
          `).join("")}
        </div>

        <div class="amazon-card-summary">
          <div>
            <div class="savings-highlight">Instant Bundle Savings: -$${savings.toFixed(2)}</div>
            <div style="font-size:11px;color:var(--text-dim);">${cartData.delivery_schedule || "Scheduled Delivery"}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:10px;color:var(--text-dim);text-transform:uppercase;">Subtotal</div>
            <div class="total-figure">$${total.toFixed(2)}</div>
          </div>
        </div>

        <button class="btn-approve-action" style="width:100%;padding:10px;" id="stageCartApproveBtn">
          <span>✓ 1-Tap Authorization & Staging</span>
        </button>
      </div>
    `;

    container.querySelector("#stageCartApproveBtn")?.addEventListener("click", () => {
      if (onApprove) onApprove(cartData);
    });
  }

  // B1: GENERIC MEDIA-CARD (title + carousel items + purchase action)
  // Consumes planner_dag.build_media_card() JSON: {type,title,carousel,purchase_action}.
  // Purchase actions are propose-never-execute: onAction receives {tool,args,gated}.
  static renderMediaCard(container, card = {}, handlers = {}) {
    const items = (card.carousel && card.carousel.items) || [];
    const purchase = card.purchase_action || null;
    container.innerHTML = `
      <div class="mcp-app-wrapper" data-media-card="${card.app_id || ""}">
        <div class="mcp-app-header">
          <div class="mcp-app-title"><span>🃏</span><span>${card.title || "Media Card"}</span></div>
          <span class="mcp-app-badge">Media Card</span>
        </div>
        ${card.subtitle ? `<div style="font-size:12px;opacity:.8;margin:6px 0;">${card.subtitle}</div>` : ""}
        <div class="media-carousel" style="display:flex;gap:8px;overflow-x:auto;padding:6px 0;">
          ${items.map((it, i) => `
            <div class="media-item" data-idx="${i}" style="min-width:150px;border:1px solid var(--border-subtle);border-radius:8px;padding:8px;">
              <div style="font-weight:700;font-size:12px;">${it.title || "item"}</div>
              ${it.image ? `<div style="font-size:10px;opacity:.6;overflow:hidden;text-overflow:ellipsis;">${it.image}</div>` : ""}
              ${it.meta ? `<div style="font-size:11px;opacity:.8;">${it.meta}</div>` : ""}
              <button class="preset-chip-btn media-item-btn" data-idx="${i}" style="margin-top:6px;">Apply</button>
            </div>`).join("") || `<div style="font-size:12px;opacity:.7;">No items</div>`}
        </div>
        ${purchase ? `<button class="btn-approve-action media-purchase-btn" style="width:100%;padding:10px;margin-top:8px;">
          <span>✓ ${purchase.label || "Stage order (approval required)"}</span></button>` : ""}
        ${card.hint ? `<div style="font-size:11px;opacity:.65;margin-top:6px;">${card.hint}</div>` : ""}
      </div>`;
    container.querySelectorAll(".media-item-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const it = items[parseInt(btn.dataset.idx, 10)];
        if (it && it.action && handlers.onAction) handlers.onAction(it.action);
      });
    });
    container.querySelector(".media-purchase-btn")?.addEventListener("click", () => {
      if (purchase && handlers.onAction) handlers.onAction(purchase);
      else if (handlers.onApprove) handlers.onApprove(card);
    });
    // Persist last card for cross-session resume (zero-config localStorage fallback).
    try { localStorage.setItem("hearth.lastMediaCard", JSON.stringify({ app_id: card.app_id || "", title: card.title || "", ts: Date.now() })); } catch (_) {}
  }

  static lastMediaCardRef() {
    try { return JSON.parse(localStorage.getItem("hearth.lastMediaCard") || "null"); } catch (_) { return null; }
  }
}
