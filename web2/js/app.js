/* Hearth web2 app — shell ownership ONLY: tabs, persona, dial, bindings, chat, dialog, toasts. */
import { on, startPolling, refresh, post } from "./store.js";

const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

/* ---------- toasts ---------- */
export function toast(msg, err) {
  const box = $("#toasts");
  const el = document.createElement("div");
  el.className = "toast" + (err ? " err" : "");
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 5200);
  while (box.children.length > 4) box.firstChild.remove();
}

/* ---------- tabs (1..5 shortcuts, / focuses command) ---------- */
const views = ["home", "activity", "approvals", "insights", "settings"];
function show(name) {
  views.forEach((v) => {
    $("#view-" + v).hidden = v !== name;
    const tab = $('.tab[data-view="' + v + '"]');
    tab.setAttribute("aria-selected", v === name ? "true" : "false");
  });
}
$$(".tab").forEach((t) =>
  t.addEventListener("click", () => show(t.dataset.view))
);
document.addEventListener("keydown", (e) => {
  if (e.target.matches("input,select,textarea")) {
    if (e.key === "Escape") e.target.blur();
    return;
  }
  if (e.key >= "1" && e.key <= "5") show(views[+e.key - 1]);
  if (e.key === "/") {
    e.preventDefault();
    $("#cmdInput").focus();
  }
});

/* ---------- persona ---------- */
$("#personaSel").addEventListener("change", async (e) => {
  const id = e.target.value;
  const { status } = await post("/api/persona", { id });
  toast(status === 200 ? "Switched to " + id + " profile" : "Profile switch rejected", status !== 200);
  refresh();
});

/* ---------- autonomy dial (earned delegation display) ---------- */
let dialStats = { proceed: 0, undo: 0 };
$("#dial").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.level === "auto" && !dialUnlocked()) {
    toast("Auto-mode is locked — needs 18/20 approvals with ≤1 undo", true);
    return;
  }
  $$("#dial button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  $("#dialPill").textContent = b.querySelector("strong").textContent;
  toast("Autonomy: " + b.querySelector("strong").textContent);
});
function dialUnlocked() {
  const n = dialStats.proceed + dialStats.undo;
  return n >= 20 && dialStats.proceed / n >= 0.9 && dialStats.undo / Math.max(1, n) <= 0.05;
}
function paintDial() {
  const n = dialStats.proceed + dialStats.undo;
  $("#dialRecord").textContent =
    "Record: " + dialStats.proceed + " approvals · " + dialStats.undo + " undos" +
    (dialUnlocked() ? " · auto-mode eligible" : " · auto-mode locked (needs 18/20, ≤1 undo)");
}

/* ---------- dialog (focus trap + Esc, no brick) ---------- */
let lastFocus = null;
function openDialog(title, bodyHTML, buttons) {
  lastFocus = document.activeElement;
  $("#dlgTitle").textContent = title;
  $("#dlgBody").innerHTML = bodyHTML;
  const row = $("#dlgRow");
  row.innerHTML = "";
  (buttons || [{ label: "Close", primary: true }]).forEach((b) => {
    const btn = document.createElement("button");
    btn.className = "btn" + (b.primary ? " btn-primary" : "");
    btn.textContent = b.label;
    btn.addEventListener("click", () => {
      closeDialog();
      if (b.onClick) b.onClick();
    });
    row.appendChild(btn);
  });
  $("#scrim").hidden = false;
  const first = row.querySelector("button");
  if (first) first.focus();
}
function closeDialog() {
  $("#scrim").hidden = true;
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
$("#scrim").addEventListener("click", (e) => {
  if (e.target.id === "scrim") closeDialog();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !$("#scrim").hidden) closeDialog();
  if (e.key === "Tab" && !$("#scrim").hidden) {
    const f = $$("#dialog button");
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});

/* ---------- home bindings (skeleton -> value, never frozen) ---------- */
function setBind(name, html) {
  const el = $('[data-bind="' + name + '"]');
  if (!el) return;
  el.classList.remove("skel");
  el.innerHTML = html;
}
on("home", (h) => {
  try {
    const lr = h.living_room || {};
    const temp = lr.climate ? lr.climate.current_c : "?";
    setBind("climate", esc(temp) + "<small> °C living room</small>");
    setBind("climateSub", esc((lr.lights && lr.lights.on ? "Lights on" : "Lights off") + " · " + ((lr.climate && lr.climate.mode) || "auto")));
    const lock = ((h.entryway || {}).lock || {}).front_door || "locked";
    setBind("lock", esc(lock === "locked" ? "Locked" : "UNLOCKED"));
    setBind("lockSub", esc(((h.entryway || {}).security_mode || "armed_home").replace(/_/g, " ")));
    const e = h.energy || {};
    setBind("energy", '<span class="num">' + esc(e.current_draw_kw != null ? e.current_draw_kw : "?") + "</span><small> kW draw</small>");
    setBind("energySub", "Solar " + esc(e.solar_generation_kw != null ? e.solar_generation_kw : "?") + " kW · score " + esc(e.eco_score != null ? e.eco_score : "?"));
  } catch (err) {
    console.error(err);
  }
});
on("depletion", (d) => {
  const f = d.forecast || d.items || [];
  if (!f.length) return;
  const worst = f.slice().sort((a, b) => (a.days_until_empty || 99) - (b.days_until_empty || 99))[0];
  setBind("pantry", '<span class="num">' + esc(worst.days_until_empty) + "</span><small>d left</small>");
  setBind("pantrySub", esc(worst.name || worst.id));
  const box = $("#pantryBox");
  box.innerHTML = f.slice(0, 5).map((it) =>
    '<div class="insight"><div class="big num">' + esc(it.days_until_empty) + '<small style="font-size:12px;color:var(--t2)">d</small></div>' +
    '<div class="txt">' + esc(it.name || it.id) + "<br><span class='mono'>" + esc(it.id || "") + "</span></div></div>"
  ).join("");
});
on("roi", (r) => {
  const box = $("#roiBox");
  const save = r.potential_save_yr ?? r.savings_annual ?? "?";
  const items = r.renewals || r.dormant || [];
  box.innerHTML =
    '<div class="insight"><div class="big num" style="color:var(--ok)">$' + esc(save) + '</div><div class="txt">recoverable per year · $' +
    esc(r.total_annual_spend ?? "?") + ' tracked spend' +
    '<br><button class="btn" id="roiGo" style="min-height:36px;margin-top:8px">Review in Approvals</button></div></div>' +
    items.slice(0, 4).map((s) =>
      '<div class="insight"><div class="txt">' + esc(s.name || s.id) + '<br><span class="mono">' +
      esc(s.usage_status || s.detail || "") + "</span></div><div class='mono' style='color:var(--ok)'>$" +
      esc(s.savings_yr ?? "?") + "/yr</div></div>"
    ).join("");
  const go = $("#roiGo");
  if (go) go.addEventListener("click", () => show("approvals"));
});

/* ---------- activity timeline (why-cards) ---------- */
const seenEvents = new Set();
function addEvent(actor, what, why) {
  const tl = $("#timeline");
  const empty = tl.querySelector(".empty");
  if (empty) empty.remove();
  const key = actor + "|" + what + "|" + JSON.stringify(why || {}).length;
  if (seenEvents.has(key)) return;
  seenEvents.add(key);
  const el = document.createElement("div");
  el.className = "event " + actor;
  const dt = why && why.detail ? why.detail : null;
  el.innerHTML =
    '<div class="event-row"><span class="actor">' + esc(actor) + "</span>" +
    '<span class="what">' + esc(what) + "</span>" +
    '<span class="when">' + new Date().toLocaleTimeString() + "</span></div>" +
    (why ? "<details><summary>Why this happened</summary><div class='why'>" +
      Object.entries(why).filter(([k]) => k !== "detail").slice(0, 4).map(([k, v]) =>
        "<div><dt>" + esc(k) + "</dt><dd>" + esc(typeof v === "object" ? JSON.stringify(v) : v) + "</dd></div>"
      ).join("") + "</div>" +
      (why.confidence != null ? '<span class="conf">Confidence ' + esc(why.confidence) + "%</span>" : "") +
      "</details>" : "");
  tl.prepend(el);
  while (tl.children.length > 30) tl.lastChild.remove();
}
on("audit", (a) => {
  const items = a.recent || a.events || [];
  items.slice(-6).forEach((ev) =>
    addEvent(ev.actor || "agent", ev.action || ev.event || "event", { detail: ev.detail || ev.hash || "" })
  );
  const ok = a.valid;
  $("#ledgerState").textContent = ok ? "Chain intact · " + (a.count || "?") + " sealed events" : "Chain BROKEN — investigate";
});

/* ---------- approvals (Proceed / Edit / Handle-it-myself) ---------- */
function deltaBadge(p) {
  const d = p.cost_delta_yr ?? p.savings ?? p.delta;
  if (d == null) return "";
  const n = Number(String(d).replace(/[^0-9.\-]/g, ""));
  const cls = n >= 0 ? "save" : "cost";
  const txt = (n >= 0 ? "+" : "−") + "$" + Math.abs(n).toFixed(2) + "/yr";
  return '<span class="delta ' + cls + '">' + esc(txt) + "</span>";
}
on("proposals", (res) => {
  const all = res.proposals || [];
  const pending = all.filter((p) => p.status === "pending");
  const badge = $("#apprCount");
  badge.hidden = !pending.length;
  badge.textContent = pending.length;
  const list = $("#intentList");
  if (!pending.length) {
    list.innerHTML = '<div class="empty"><strong>All clear</strong>No pending proposals. Hearth will stage them here with cost deltas.</div>';
    return;
  }
  list.innerHTML = "";
  pending.forEach((p) => {
    const el = document.createElement("div");
    el.className = "intent";
    el.innerHTML =
      '<div class="intent-top"><h4>' + esc(p.title || p.kind) + "</h4>" + deltaBadge(p) + "</div>" +
      '<p class="intent-reasons">' + esc((p.reasons || []).join ? p.reasons.join(" ") : (p.reasons || "")) + "</p>" +
      '<p class="mono" style="padding:2px 16px 0;color:var(--t3)"><span class="risk ' + esc(p.risk_level || "medium") + '">' +
      esc(p.risk_level || "medium") + "</span> · single-use · expires on decide</p>" +
      '<div class="intent-actions"><button class="btn btn-primary" data-a="1">Proceed</button>' +
      "<button class='btn' data-a='inspect'>Inspect</button>" +
      "<button class='btn' data-a='mine'>I'll do it</button></div>";
    el.querySelector('[data-a="1"]').addEventListener("click", () => decide(p.id, true, el));
    el.querySelector('[data-a="mine"]').addEventListener("click", () => decide(p.id, false, el, "Noted — marked as handled by you."));
    el.querySelector('[data-a="inspect"]').addEventListener("click", () =>
      openDialog(p.title || p.kind,
        "<p style='color:var(--t2)'>" + esc((p.reasons || []).join ? p.reasons.join(" ") : (p.reasons || "")) + "</p>" +
        '<div class="diff">' + esc(p.diff || p.detail || JSON.stringify(p.meta || {}, null, 1)) + "</div>" +
        "<p class='mono' style='color:var(--t3)'>id " + esc(p.id) + " · kind " + esc(p.kind) + "</p>",
        [
          { label: "Proceed", primary: true, onClick: () => decide(p.id, true, el) },
          { label: "Reject", onClick: () => decide(p.id, false, el) },
        ])
    );
    list.appendChild(el);
  });
});
async function decide(id, approved, el, note) {
  // Optimistic: settle the row instantly (reversible until server answers), roll back on failure.
  const actions = el.querySelector(".intent-actions");
  const snapshot = el.innerHTML;
  if (actions) {
    actions.innerHTML = '<span class="mono" style="color:var(--t2)">Settling…</span>';
  }
  const { status, data } = await post("/api/decide", { id, approved });
  if (status === 200 && data && data.ok !== false) {
    dialStats.proceed += approved ? 1 : 0;
    dialStats.undo += 0;
    paintDial();
    if (data.execution || approved) {
      const r = el.querySelector(".intent-actions");
      if (r) r.outerHTML = '<div class="receipt">✓ ' + esc(note || (approved ? "Executed once — receipt sealed in ledger." : "Rejected — no side effects.")) + "</div>";
    }
    toast(note || (approved ? "Approved and executed once" : "Rejected — nothing happened"));
    setTimeout(refresh, 800);
  } else if (status === 409) {
    toast("Already decided — single-use receipt stands", true);
    setTimeout(refresh, 800);
  } else {
    el.innerHTML = snapshot;
    rebindIntent(el);
    toast("Server refused (" + status + ") — rolled back, nothing changed", true);
  }
}
function rebindIntent(el) {
  const id = null;
  el.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => refresh())
  );
}

/* ---------- chat: DAG + why, never silent ---------- */
$("#cmdForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#cmdInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  const log = $("#chatLog");
  const el = document.createElement("div");
  el.className = "event human";
  el.innerHTML = '<div class="event-row"><span class="actor">you</span><span class="what">' +
    esc(msg) + '</span><span class="when">sending…</span></div>';
  log.prepend(el);
  const { status, data } = await post("/api/chat", { message: msg });
  el.querySelector(".when").textContent = new Date().toLocaleTimeString();
  if (status === 429) {
    toast("Slow down — 30 requests per minute", true);
    return;
  }
  if (status !== 200 || !data) {
    toast("Hearth didn't answer (" + status + ") — retrying is safe", true);
    return;
  }
  const text = data.draft || data.text || data.synthesis || data.message || data.error || "Done.";
  const row = document.createElement("div");
  row.className = "event agent";
  const dag = (data.dag || []).slice(0, 6).map((s) =>
    esc(s.tool || s.id) + " → " + esc(s.status || "done")
  ).join("  ·  ");
  row.innerHTML = '<div class="event-row"><span class="actor">hearth</span><span class="what">' +
    esc(text).slice(0, 600) + "</span></div>" +
    (dag ? "<details open><summary>How it reasoned</summary><div class='mono' style='color:var(--t2)'>" + dag + "</div></details>" : "") +
    (data.blocked ? "<div class='receipt' style='color:var(--bad)'>Blocked: " + esc(data.reason || "") + "</div>" : "");
  log.prepend(row);
  if (data.blocked) addEvent("sentinel", "Blocked: " + (data.reason || "policy"), null);
  else addEvent("agent", (data.intent || " Answered") + " — " + msg.slice(0, 60), { steps: (data.dag || []).length });
  refresh();
});

/* ---------- settings verify ---------- */
$("#verifyBtn").addEventListener("click", async () => {
  $("#ledgerState").textContent = "Verifying…";
  try {
    const r = await fetch("/api/audit");
    const a = await r.json();
    $("#ledgerState").textContent = a.valid
      ? "Chain intact · " + (a.count || "?") + " sealed events"
      : "Chain BROKEN — investigate";
    toast(a.valid ? "Ledger verified intact" : "Ledger verification FAILED", !a.valid);
  } catch {
    $("#ledgerState").textContent = "Unreachable — is the server up?";
  }
});

/* ---------- status pill ---------- */
on("status", (s) => {
  $("#protoText").textContent = s.ok ? "MCP 2025-11-25 · Live" : "Reconnecting… (" + (s.failures || 1) + ")";
  $("#protoPill").classList.toggle("warn", !s.ok);
});

/* ---------- boot ---------- */
paintDial();
const deep = new URLSearchParams(location.search).get("view");
if (deep && views.includes(deep)) show(deep);
startPolling(5000);
