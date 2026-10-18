/* Hearth Proof Engine — hash-chained receipts, live verification, tamper demo.
   Self-contained so the cockpit contract (app.js) doesn't grow. */
const $ = (sel) => document.querySelector(sel);

const panel = $("#proofPanel");
if (panel) {
  const listEl = $("#proofList");
  const totalEl = $("#proofTotal");
  const breakEl = $("#proofBreak");
  const headEl = $("#proofHead");
  const chainEl = $("#proofChainOk");
  const countEl = $("#proofCount");
  const verifyBtn = $("#proofVerify");
  const tamperBtn = $("#proofTamper");
  const resultEl = $("#proofResult");
  const hintEl = $("#proofHint");

  const KIND = {
    vpp_dispatch: "VPP",
    tool_applied: "TOOL",
    order_staged: "ORDER",
    approval_executed: "APPROVE",
  };

  let selected = "";
  let snap = null;

  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  const short = (h, n = 18) => (h ? String(h).slice(0, n) + "…" : "–");
  const usd = (n) => `$${Number(n || 0).toFixed(2)}`;

  function moneyView(m) {
    m = m || {};
    if (m.saved_usd) return { text: `+${usd(m.saved_usd)}`, cls: "is-good" };
    if (m.earned_usd) return { text: `+${usd(m.earned_usd)}`, cls: "is-good" };
    if (m.spent_usd) return { text: `−${usd(m.spent_usd)}`, cls: "is-spent" };
    return { text: "no money moved", cls: "is-none" };
  }

  function paint(data) {
    snap = data;
    const led = data.ledger || {};
    const receipts = data.receipts || [];
    if (!selected && receipts.length) selected = receipts[0].receipt_id;

    totalEl.textContent = usd(led.verified_usd);
    breakEl.textContent =
      `${usd(led.saved_usd)} tool savings · ${usd(led.earned_usd)} VPP dividends · ` +
      `${usd(led.spent_usd)} orders placed (net +${usd(led.net_usd)})`;
    headEl.textContent = short(led.chain_head, 22);
    chainEl.textContent = led.chain_valid
      ? `✓ chain intact · ${led.receipts_count} receipts re-derived`
      : "✕ chain broken";
    chainEl.classList.toggle("is-bad", !led.chain_valid);
    countEl.textContent = `${led.receipts_count || 0} receipts`;

    listEl.innerHTML = "";
    receipts.forEach((r) => {
      const m = moneyView(r.money);
      const row = document.createElement("button");
      row.type = "button";
      row.className = "proof-item" + (r.receipt_id === selected ? " is-selected" : "");
      const srcCount = (r.source_events || []).length;
      row.innerHTML =
        `<span class="proof-kind proof-kind-${esc(r.kind)}">${esc(KIND[r.kind] || r.kind)}</span>` +
        `<span class="proof-claim">${esc(r.claim)}</span>` +
        `<span class="proof-money ${m.cls}">${esc(m.text)}</span>` +
        `<span class="proof-sub"><code>${esc(r.receipt_id)}</code>` +
        `<span>${srcCount} source event${srcCount === 1 ? "" : "s"}</span>` +
        `<span>prev ${esc(short(r.prev_receipt_hash, 12))}</span></span>`;
      row.addEventListener("click", () => {
        selected = r.receipt_id;
        paint(snap);
      });
      listEl.appendChild(row);
    });
  }

  async function load() {
    try {
      const res = await fetch("/api/receipts?limit=6");
      const data = await res.json();
      if (data.ok) paint(data);
    } catch {
      /* offline: keep the last known ledger */
    }
  }

  async function run(tamper) {
    if (!selected) return;
    verifyBtn.disabled = true;
    tamperBtn.disabled = true;
    resultEl.hidden = false;
    resultEl.className = "proof-result is-waiting";
    resultEl.innerHTML = `<strong>${
      tamper ? "EDITING THE RECEIPT BY HAND…" : "RE-DERIVING SHA-256 FROM THE FIELDS…"
    }</strong>`;
    try {
      const res = await fetch("/api/receipts/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ receipt_id: selected, tamper }),
      });
      const d = await res.json();
      if (tamper && d.tamper) {
        const t = d.tamper;
        resultEl.className = "proof-result is-bad";
        resultEl.innerHTML =
          `<strong>TAMPER DETECTED ✕</strong>` +
          `field       ${esc(t.field)}: claimed ${usd(t.tampered)} — the receipt says ${usd(t.original)}\n` +
          `recomputed  ${esc(short(t.recomputed_hash, 24))}\n` +
          `stated      ${esc(short(d.stated_hash, 24))}\n` +
          `verdict     ${esc(t.reason)}`;
      } else {
        resultEl.className = "proof-result " + (d.ok ? "is-good" : "is-bad");
        resultEl.innerHTML =
          `<strong>${d.ok ? "VERIFIED ✓" : "MISMATCH ✕"}</strong>` +
          `receipt     ${esc(d.receipt_id)} · ${esc(d.claim || "")}\n` +
          `stated      ${esc(short(d.stated_hash, 24))}\n` +
          `recomputed  ${esc(short(d.recomputed_hash, 24))}  ${d.match ? "MATCH" : "≠ MISMATCH"}\n` +
          `chain       ${d.chain_valid ? "intact — re-derived to the head" : "BROKEN"}`;
      }
    } catch (err) {
      resultEl.className = "proof-result is-bad";
      resultEl.innerHTML = `<strong>NETWORK ERROR</strong>${esc(err)}`;
    } finally {
      verifyBtn.disabled = false;
      tamperBtn.disabled = false;
    }
  }

  verifyBtn.addEventListener("click", () => run(false));
  tamperBtn.addEventListener("click", () => run(true));
  hintEl.addEventListener("click", () => {
    resultEl.hidden = true;
  });

  load();
}
