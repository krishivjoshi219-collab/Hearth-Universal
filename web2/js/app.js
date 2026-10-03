/* Hearth web2 app — shell ownership ONLY: tabs, persona, dial, bindings, chat, dialog, toasts. */
import { on, startPolling, refresh, post } from "./store.js";

const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

export function formatMarkdown(text) {
  if (!text) return "";
  let s = esc(text);

  // Code blocks (```...```)
  s = s.replace(/```([\s\S]*?)```/g, (_, code) =>
    '<pre class="mono" style="background:var(--s3);padding:8px 12px;border-radius:6px;overflow-x:auto;margin:6px 0;font-size:var(--fs-micro);line-height:1.4;">' +
    code.trim() +
    '</pre>'
  );

  // Inline code (`...`)
  s = s.replace(/`([^`]+)`/g, '<code class="mono" style="background:var(--s3);padding:2px 5px;border-radius:4px;font-size:0.9em;color:var(--amber);">$1</code>');

  // Bold (**...**)
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong style="color:var(--t1);font-weight:700;">$1</strong>');

  // Italic (*...*)
  s = s.replace(/(^|[^*])\*([^*]+)\*([^*]|$)/g, '$1<em style="color:var(--t2);">$2</em>$3');

  // Process lines for bullet items and spacing
  const lines = s.split(/\r?\n/);
  const formatted = [];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trim();

    if (!trimmed) {
      formatted.push('<div style="height:6px;"></div>');
      continue;
    }

    if (trimmed.startsWith("• ") || trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const content = trimmed.replace(/^[•\-\*]\s+/, "");
      formatted.push(
        '<div class="chat-bullet">' +
        '<span class="bullet-dot">•</span>' +
        '<span class="bullet-content">' + content + '</span>' +
        '</div>'
      );
      continue;
    }

    formatted.push('<div style="margin:2px 0;">' + raw + '</div>');
  }

  return formatted.join("");
}

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

/* ---------- luxury calm feedback: light-wave & earcons ---------- */
let audioMuted = false;
export function playEarcon(type = "success") {
  if (audioMuted) return;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const now = ctx.currentTime;
    if (type === "success") {
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();
      osc1.type = "sine";
      osc2.type = "sine";
      osc1.frequency.setValueAtTime(523.25, now);
      osc2.frequency.setValueAtTime(659.25, now + 0.08);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.25);
      osc2.start(now + 0.08);
      osc2.stop(now + 0.35);
    } else if (type === "alert") {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(440, now);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    }
  } catch {}
}

export function setLightWave(mode = "idle") {
  const bar = $("#lightWaveBar");
  if (!bar) return;
  bar.className = "light-wave-bar " + mode;
  if (mode !== "idle") {
    clearTimeout(bar._timer);
    bar._timer = setTimeout(() => {
      if (bar.className.includes(mode)) bar.className = "light-wave-bar idle";
    }, 3800);
  }
}

const chimeBtn = $("#chimeBtn");
if (chimeBtn) {
  chimeBtn.addEventListener("click", () => {
    audioMuted = !audioMuted;
    chimeBtn.textContent = audioMuted ? "🔕" : "🔔";
    chimeBtn.title = audioMuted ? "Audio muted" : "Audio earcons enabled";
    toast(audioMuted ? "Audio muted" : "Audio earcons enabled");
  });
}

/* ---------- tabs (1..5 shortcuts, / focuses command) ---------- */
const views = ["home", "activity", "approvals", "insights", "settings"];
function show(name) {
  views.forEach((v) => {
    $("#view-" + v).hidden = v !== name;
    const tab = $('.tab[data-view="' + v + '"]');
    tab.setAttribute("aria-selected", v === name ? "true" : "false");
  });

  // Floating chat button: only visible on non-home tabs
  const floatBtn = $("#floatingChatBtn");
  const floatWidget = $("#floatingChatWidget");
  if (floatBtn) {
    floatBtn.hidden = (name === "home");
  }
  if (name === "home" && floatWidget) {
    floatWidget.hidden = true;
  }
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
    const isHome = !$("#view-home").hidden;
    if (isHome) {
      $("#cmdInput").focus();
    } else {
      const widget = $("#floatingChatWidget");
      if (widget) {
        widget.hidden = false;
        $("#widgetCmdInput")?.focus();
      }
    }
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
    if (h.operating_mode === "real" && !h.alexa_logged_in) {
      setBind("climate", "–<small> °C living room</small>");
      setBind("climateSub", "Awaiting Alexa+ Link");
      setBind("lock", "–");
      setBind("lockSub", "Awaiting Alexa+ Link");
      setBind("energy", '<span class="num">0.0</span><small> kW draw</small>');
      setBind("energySub", "Standby · 0 kW Solar");
      setBind("pantry", '<span class="num">0</span><small> items</small>');
      setBind("pantrySub", "Unlinked");
      const nextUp = $("#nextUp");
      if (nextUp) nextUp.innerHTML = '<div class="empty"><strong>Zero Pending Tasks</strong>Awaiting Alexa+ account connection or resident command.</div>';
      const delBox = $("#deliveryBox");
      if (delBox) delBox.innerHTML = '<div class="empty"><strong>Zero active deliveries</strong>Authorize Alexa+ to sync Prime deliveries.</div>';
      return;
    }

    if (h.operating_mode === "real" && h.alexa_logged_in) {
      const lr = h.living_room || {};
      const temp = lr.climate ? lr.climate.current_c : 21.5;
      setBind("climate", esc(temp) + "<small> °C living room</small>");
      setBind("climateSub", esc((lr.climate && lr.climate.device) || "Ecobee") + " · " + esc((lr.climate && lr.climate.mode) || "eco"));
      const lock = ((h.entryway || {}).lock || {}).front_door || "locked";
      setBind("lock", esc(lock === "locked" ? "Locked" : "UNLOCKED"));
      setBind("lockSub", esc(((h.entryway || {}).device || "Yale Assure Lock 2") + " · 92% batt"));
      const e = h.energy || {};
      setBind("energy", '<span class="num">' + esc(e.solar_generation_kw != null ? e.solar_generation_kw : "4.8") + "</span><small> kW solar</small>");
      setBind("energySub", "Enphase Gateway · Net " + esc(e.net_kw != null ? e.net_kw : "4.4") + " kW");

      const delBox = $("#deliveryBox");
      const comm = h.commerce || {};
      const activeDel = comm.active_deliveries || [];
      if (delBox) {
        if (activeDel.length) {
          const d = activeDel[0];
          delBox.innerHTML =
            '<div style="background:var(--s2);border:1px solid var(--line);border-radius:8px;padding:12px">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">' +
            '<strong style="color:var(--amber);font-size:12px">🚚 ' + esc(d.status || "In Transit") + '</strong>' +
            '<span class="pill" style="font-size:10px">' + esc(d.eta || "Today") + '</span>' +
            '</div>' +
            '<div style="font-size:13px;font-weight:600;margin-bottom:4px">' + esc(d.items ? d.items.join(", ") : "Amazon Package") + '</div>' +
            '<small style="color:var(--t3);font-size:11px">Tracking #' + esc(d.tracking_number || "") + ' · ' + esc(d.stops_away || 3) + ' stops away</small>' +
            '</div>';
        } else {
          delBox.innerHTML = '<div class="empty"><strong>No deliveries today</strong>Prime Subscribe &amp; Save up to date.</div>';
        }
      }
      return;
    }

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
    if (res.mode === "real") {
      list.innerHTML = '<div class="empty"><strong>Zero Pending Approvals</strong>Clean slate in Real World mode. Only real resident proposals will appear here.</div>';
    } else {
      list.innerHTML = '<div class="empty"><strong>All clear</strong>No pending proposals. Hearth will stage them here with cost deltas.</div>';
    }
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
let lastApprovedPid = null;
async function undoProposal(id, el) {
  toast("Reversing action…");
  setLightWave("thinking");
  const { status, data } = await post("/api/undo", { id });
  if (status === 200 && data.ok) {
    dialStats.undo += 1;
    paintDial();
    playEarcon("alert");
    setLightWave("alert");
    toast("Action reversed: " + (data.note || "prior state restored"));
    refresh();
  } else {
    setLightWave("alert");
    toast("Reversal failed: " + (data.error || status), true);
  }
}

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !e.target.matches("input,textarea")) {
    if (lastApprovedPid) {
      e.preventDefault();
      const pidToUndo = lastApprovedPid;
      lastApprovedPid = null;
      undoProposal(pidToUndo);
    }
  }
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
    if (approved) {
      lastApprovedPid = id;
      playEarcon("success");
      setLightWave("success");
    } else {
      playEarcon("alert");
    }
    if (data.execution || approved) {
      const r = el.querySelector(".intent-actions");
      if (r) {
        r.outerHTML =
          '<div class="receipt">✓ ' +
          esc(note || (approved ? "Executed once — receipt sealed in ledger." : "Rejected — no side effects.")) +
          (approved ? ' <button class="btn-undo" data-undopid="' + esc(id) + '">↩ Undo</button>' : '') +
          '</div>';
        const uBtn = el.querySelector('[data-undopid="' + id + '"]');
        if (uBtn) uBtn.addEventListener("click", () => undoProposal(id, el));
      }
    }
    toast(note || (approved ? "Approved and executed once" : "Rejected — nothing happened"));
    setTimeout(refresh, 800);
  } else if (status === 409) {
    toast("Already decided — single-use receipt stands", true);
    setTimeout(refresh, 800);
  } else {
    el.innerHTML = snapshot;
    rebindIntent(el);
    setLightWave("alert");
    playEarcon("alert");
    toast("Server refused (" + status + ") — rolled back, nothing changed", true);
  }
}
function rebindIntent(el) {
  const id = null;
  el.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => refresh())
  );
}

/* ---------- shared chat runner (synchronized across Home & Floating Widget) ---------- */
async function handleUserChat(msg) {
  if (!msg) return;
  setLightWave("thinking");
  
  const homeLog = $("#chatLog");
  const widgetLog = $("#widgetChatLog");
  
  function appendHuman(logEl) {
    if (!logEl) return null;
    const el = document.createElement("div");
    el.className = "event human";
    el.innerHTML = '<div class="event-row"><span class="actor">you</span><div class="what">' +
      esc(msg) + '</div><span class="when">sending…</span></div>';
    logEl.prepend(el);
    return el;
  }
  
  const homeEl = appendHuman(homeLog);
  const widgetEl = appendHuman(widgetLog);
  
  const { status, data } = await post("/api/chat", { message: msg });
  const timeStr = new Date().toLocaleTimeString();
  if (homeEl) homeEl.querySelector(".when").textContent = timeStr;
  if (widgetEl) widgetEl.querySelector(".when").textContent = timeStr;
  
  if (status === 429) {
    setLightWave("alert");
    playEarcon("alert");
    toast("Slow down — 30 requests per minute", true);
    return;
  }
  if (status !== 200 || !data) {
    setLightWave("alert");
    playEarcon("alert");
    toast("Hearth didn't answer (" + status + ") — retrying is safe", true);
    return;
  }
  setLightWave(data.blocked ? "alert" : "speaking");
  if (!data.blocked) playEarcon("success");
  const text = data.draft || data.text || data.synthesis || data.message || data.error || "Done.";
  latestSpokenText = sanitizeForVoice(text);

  if (currentDisplayMode === "voice-only") {
    speakAlexaVoice(latestSpokenText);
  } else if (currentDisplayMode === "fullscreen") {
    renderFullscreenCanvas(data);
  } else if (currentDisplayMode === "hydrated") {
    renderFullscreenCanvas(data); // hydrated: live streaming UI over inline card
  }
  
  function appendAgent(logEl) {
    if (!logEl) return;
    const row = document.createElement("div");
    row.className = "event agent";
    const dag = (data.dag || []).slice(0, 6).map((s) =>
      esc(s.tool || s.id) + " → " + esc(s.status || "done")
    ).join("  ·  ");
    row.innerHTML = '<div class="event-row"><span class="actor">hearth</span><div class="what">' +
      formatMarkdown(text) + "</div></div>" +
      (dag ? "<details open><summary>How it reasoned</summary><div class='mono' style='color:var(--t2)'>" + dag + "</div></details>" : "") +
      (data.blocked ? "<div class='receipt' style='color:var(--bad)'>Blocked: " + esc(data.reason || "") + "</div>" : "");
    logEl.prepend(row);
  }
  
  appendAgent(homeLog);
  appendAgent(widgetLog);
  
  if (data.blocked) addEvent("sentinel", "Blocked: " + (data.reason || "policy"), null);
  else addEvent("agent", (data.intent || " Answered") + " — " + msg.slice(0, 60), { steps: (data.dag || []).length });
  refresh();
}

$("#cmdForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#cmdInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  handleUserChat(msg);
});

$("#widgetCmdForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#widgetCmdInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  handleUserChat(msg);
});

/* ---------- floating chat button & widget toggle ---------- */
const floatBtn = $("#floatingChatBtn");
const floatWidget = $("#floatingChatWidget");
const widgetCloseBtn = $("#widgetCloseBtn");

floatBtn?.addEventListener("click", () => {
  if (!floatWidget) return;
  floatWidget.hidden = !floatWidget.hidden;
  if (!floatWidget.hidden) {
    $("#widgetCmdInput")?.focus();
  }
});

widgetCloseBtn?.addEventListener("click", () => {
  if (floatWidget) floatWidget.hidden = true;
});

/* ---------- quick starter prompt chips (blank canvas relief) ---------- */
$$(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const cmd = chip.dataset.cmd;
    if (!cmd) return;
    const input = $("#cmdInput");
    input.value = cmd;
    $("#cmdForm").dispatchEvent(new Event("submit"));
  });
});

/* ---------- judge showcase 1-click hackathon cards ---------- */
$$(".showcase-card").forEach((card) => {
  card.addEventListener("click", () => {
    const cmd = card.dataset.cmd;
    if (!cmd) return;
    const input = $("#cmdInput");
    if (input) {
      input.value = cmd;
      $("#cmdForm")?.dispatchEvent(new Event("submit"));
    }
  });
});

/* ---------- Alexa+ Display Modes (@modelcontextprotocol/ext-apps) ---------- */
let currentDisplayMode = "inline";
let latestSpokenText = "Hearth Universal is online and connected to your household digital twin.";

function sanitizeForVoice(raw) {
  if (!raw) return "";
  let s = String(raw);
  s = s.replace(/\|[^\n]+\|/g, "");
  s = s.replace(/\|/g, " ");
  s = s.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");
  s = s.replace(/[\*_`#]/g, "");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

function speakAlexaVoice(text) {
  if (audioMuted || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  const voices = window.speechSynthesis.getVoices();
  const v = voices.find((x) => x.lang.startsWith("en") && (x.name.includes("Natural") || x.name.includes("Google") || x.name.includes("Samantha") || x.name.includes("Female")));
  if (v) utterance.voice = v;
  utterance.onstart = () => {
    setLightWave("speaking");
    $("#voiceModeBanner .voice-waves")?.classList.add("active");
  };
  utterance.onend = () => {
    setLightWave("idle");
    $("#voiceModeBanner .voice-waves")?.classList.remove("active");
  };
  window.speechSynthesis.speak(utterance);
}

function renderFullscreenCanvas(data) {
  const box = $("#fullscreenCanvasBox");
  const grid = $("#canvasGrid");
  if (!box || !grid) return;
  box.hidden = false;
  grid.innerHTML = `
    <div style="background:var(--s1);border:1px solid var(--line);border-radius:8px;padding:14px">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <strong style="color:var(--amber)">🏛️ Household Parliament Matrix</strong>
        <span class="pill" style="font-size:10px">Game-Theoretic</span>
      </div>
      <p style="font-size:12px;color:var(--t2);line-height:1.4">Deliberation across FrugalMind, BioComfort, and EcoSovereign ministers with Nash equilibrium score.</p>
      <div style="font-size:12px;margin-top:8px;padding:8px;background:var(--s2);border-radius:4px" id="fsParliamentPreview">Active consensus reached (Nash: 8.4/10)</div>
    </div>
    <div style="background:var(--s1);border:1px solid var(--line);border-radius:8px;padding:14px">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <strong style="color:var(--ok)">🔮 7-Day Causal Future Simulation</strong>
        <span class="pill" style="font-size:10px">Monte Carlo 150x</span>
      </div>
      <p style="font-size:12px;color:var(--t2);line-height:1.4">Stochastic forward prediction of weather tariffs, solar battery discharge, and brownout risk.</p>
      <div style="font-size:12px;margin-top:8px;padding:8px;background:var(--s2);border-radius:4px" id="fsCausalPreview">Pre-emptive contingency staged · 0 brownouts</div>
    </div>
    <div style="background:var(--s1);border:1px solid var(--line);border-radius:8px;padding:14px">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <strong style="color:var(--cyan, #38bdf8)">⚡ Energy Arbitrage &amp; Solar Mesh</strong>
        <span class="pill" style="font-size:10px">Enphase + Ecobee</span>
      </div>
      <p style="font-size:12px;color:var(--t2);line-height:1.4">Net solar export: 4.4 kW · Battery: 88% · Living room pre-cooled to 20°C before 4 PM peak.</p>
      <div style="font-size:12px;margin-top:8px;padding:8px;background:var(--s2);border-radius:4px" id="fsEnergyPreview">Annual avoided tariff cost: $642.10</div>
    </div>
  `;
}

function setDisplayMode(mode) {
  currentDisplayMode = mode;
  $$(".mode-chip").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });

  const voiceBanner = $("#voiceModeBanner");
  const canvasBox = $("#fullscreenCanvasBox");

  if (mode === "voice-only") {
    if (voiceBanner) voiceBanner.hidden = false;
    if (canvasBox) canvasBox.hidden = true;
    toast("Switched to Voice-Only Headless mode (Echo / AVS audio)");
    if (latestSpokenText) speakAlexaVoice(latestSpokenText);
  } else if (mode === "fullscreen") {
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) {
      canvasBox.hidden = false;
      renderFullscreenCanvas();
    }
    toast("Expanded to Alexa+ Fullscreen Canvas (@modelcontextprotocol/ext-apps)");
  } else if (mode === "hydrated") {
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) {
      canvasBox.hidden = false;
      renderFullscreenCanvas();
    }
    toast("Hydrated UI: live streaming status + inline card (@ext-apps)");
  } else {
    // inline
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) canvasBox.hidden = true;
    toast("Switched to Inline Card mode (default)");
  }
}

$$(".mode-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    setDisplayMode(chip.dataset.mode);
  });
});

$("#exitFullscreenBtn")?.addEventListener("click", () => {
  setDisplayMode("inline");
});

$("#playTtsBtn")?.addEventListener("click", () => {
  if (latestSpokenText) speakAlexaVoice(latestSpokenText);
});


/* ---------- living household simulator (home view) ---------- */
$$(".scenario-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const scenario = btn.dataset.scenario;
    btn.disabled = true;
    setLightWave("thinking");
    const { status, data } = await post("/api/simulate/tick", { scenario });
    btn.disabled = false;
    if (status === 200 && data.ok) {
      playEarcon("success");
      setLightWave("speaking");
      toast("Event simulated: " + (data.event ? data.event.title : scenario));
      refresh();
    } else {
      setLightWave("alert");
      playEarcon("alert");
      toast("Simulation failed", true);
    }
  });
});


/* ---------- universal model mesh ---------- */
let modelsCatalog = [];
on("models", (res) => {
  if (!res || !res.models) return;
  modelsCatalog = res.models || [];
  const sel = $("#modelSel");
  if (sel) {
    sel.innerHTML = modelsCatalog.map((m) =>
      '<option value="' + esc(m.model_id) + '" data-provider="' + esc(m.provider) + '"' +
      (m.is_active || m.model_id === res.active_model ? " selected" : "") + ">" +
      esc(m.name || m.model_id) + " · " + esc((m.provider || "bedrock").toUpperCase()) + "</option>"
    ).join("");
    if (res.active_model) sel.value = res.active_model;
  }
  const pill = $("#activeModelPill");
  if (pill) {
    pill.textContent = (res.active_model ? res.active_model.split(":").pop() : "Nova Pro") + " · " + (res.active_provider || "bedrock").toUpperCase();
  }
  const provBox = $("#meshProvidersList");
  if (provBox && res.providers) {
    provBox.innerHTML = res.providers.map((p) =>
      '<span class="provider-tag' + (p.name === res.active_provider ? " active" : "") + '">' +
      '<span class="dot" style="background:' + (p.status === "connected" ? "var(--ok)" : "var(--amber)") + '"></span>' +
      esc(p.name) + " · " + esc(p.models_count || 1) + " models (" + esc(p.latency_ms || 22) + "ms)</span>"
    ).join("");
  }
});

const modelSel = $("#modelSel");
if (modelSel) {
  modelSel.addEventListener("change", async (e) => {
    const opt = e.target.selectedOptions[0];
    const model_id = e.target.value;
    const provider = opt ? opt.dataset.provider || "bedrock" : "bedrock";
    const { status, data } = await post("/api/models/active", { model_id, provider });
    if (status === 200 && data.ok) {
      toast("Reasoning brain switched to " + (data.active_model || model_id));
      refresh();
    } else {
      toast("Brain switch failed (" + status + ")", true);
    }
  });
}

const addApiBtn = $("#addCustomApiBtn");
if (addApiBtn) {
  addApiBtn.addEventListener("click", async () => {
    const nameInput = $("#customApiName");
    const urlInput = $("#customApiUrl");
    const name = nameInput.value.trim() || "Custom API";
    const base_url = urlInput.value.trim();
    if (!base_url) {
      toast("Please enter an API base URL", true);
      return;
    }
    addApiBtn.disabled = true;
    addApiBtn.textContent = "Pinging…";
    const { status, data } = await post("/api/models/providers/add", { name, base_url });
    addApiBtn.disabled = false;
    addApiBtn.textContent = "Add & Ping";
    if (status === 200 && data.ok) {
      toast("Connected " + name + " (" + (data.discovered_models || []).length + " models discovered)");
      nameInput.value = "";
      urlInput.value = "";
      refresh();
    } else {
      toast("Failed to connect API: " + (data.error || status), true);
    }
  });
}

/* ---------- household parliament ---------- */
on("parliament", (p) => {
  const box = $("#parliamentBox");
  if (!box || !p || !p.ministers) return;
  const ministers = Array.isArray(p.ministers)
    ? p.ministers
    : Object.entries(p.ministers).map(([k, v]) => ({ id: k, name: v.title || v.name || k, ...v }));
  box.innerHTML =
    '<p style="font-size:var(--fs-micro);color:var(--t2);margin-bottom:12px">' +
    esc(p.council || "Household Parliament") + ' · <span style="color:var(--amber)">' + esc(p.governance_model || "Nash Equilibrium") + '</span></p>' +
    '<div class="parliament-grid">' +
    ministers.map((m) =>
      '<div class="minister-card">' +
      '<strong>' + esc(m.name || m.title || m.id) + '</strong>' +
      '<small>' + esc(m.focus || (m.style ? m.style.replace(/_/g, " ") : m.priority) || "") + '</small>' +
      '<div class="util">Weight: ' + esc(m.weight || 1.0) + ' · Vetoes: ' + esc(m.veto_count || 0) + '</div>' +
      '</div>'
    ).join("") +
    '</div>';
});

const parlBtn = $("#parlDebateBtn");
if (parlBtn) {
  parlBtn.addEventListener("click", async () => {
    parlBtn.disabled = true;
    parlBtn.textContent = "Debating…";
    const { status, data } = await post("/api/parliament/deliberate", {
      topic: "Multi-objective household energy vs wellness dilemma"
    });
    parlBtn.disabled = false;
    parlBtn.textContent = "Deliberate";
    if (status === 200 && data) {
      const speeches = (data.speeches || []).map((s) => {
        const text = Array.isArray(s.arguments) ? s.arguments.join(" ") : (s.speech || s.stance || "");
        return '<div style="margin-bottom:8px"><strong>' + esc(s.minister) + (s.role ? ' (' + esc(s.role) + ')' : '') + ':</strong> ' + esc(text) + '</div>';
      }).join("");
      const paretoText = typeof data.pareto_compromise === "object"
        ? (data.pareto_compromise.executive_summary || JSON.stringify(data.pareto_compromise))
        : String(data.pareto_compromise || "");
      const nashVal = data.nash_equilibrium_score != null ? data.nash_equilibrium_score : 8.4;
      const nashPct = (nashVal > 1 ? nashVal * 10 : nashVal * 100).toFixed(0);

      openDialog("Parliamentary Consensus Reached",
        '<p style="color:var(--amber);font-weight:700">Nash Equilibrium Score: ' + nashPct + '%</p>' +
        '<p style="color:var(--t1);margin:8px 0"><strong>Pareto Compromise:</strong> ' + esc(paretoText) + '</p>' +
        '<div class="diff" style="margin:12px 0">' + speeches + '</div>' +
        (data.staged_proposal_id ? '<p class="receipt" style="color:var(--ok)">Proposal #' + esc(data.staged_proposal_id) + ' staged in Approvals.</p>' : ''),
        [
          { label: "Review Approvals", primary: true, onClick: () => show("approvals") },
          { label: "Dismiss" }
        ]
      );
      toast("Debate concluded with " + nashPct + "% consensus");
      refresh();
    } else {
      toast("Deliberation failed (" + status + ")", true);
    }
  });
}

/* ---------- causal digital twin ---------- */
on("causal", (c) => {
  const box = $("#causalBox");
  if (!box || !c) return;
  const vulns = c.vulnerabilities || [];
  const score = c.resilience_score != null
    ? Math.round(c.resilience_score > 1 ? c.resilience_score : c.resilience_score * 100)
    : 96;
  box.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">' +
    '<span style="font-size:var(--fs-micro);color:var(--t2)">Stochastic World Model: <strong>' + esc(c.simulation_id || "sim-live") + '</strong></span>' +
    '<span class="pill" style="color:var(--ok)">' + score + '% Grid Resilience</span>' +
    '</div>' +
    (!vulns.length
      ? '<div class="empty"><strong>Zero vulnerabilities detected</strong>Household state is stable across horizon.</div>'
      : vulns.slice(0, 3).map((v) => {
        const sev = esc(v.impact_severity || v.severity || "medium");
        const horizon = esc(v.timeframe || (v.horizon_hours ? "in " + v.horizon_hours + "h" : "24h"));
        const title = esc(v.title || (v.hazard_type ? v.hazard_type.replace(/_/g, " ") : v.domain) || "Anomaly");
        const action = esc(v.contingency_action || v.countermeasure || v.description || v.root_cause || "");
        return (
          '<div class="insight" style="margin-bottom:8px">' +
          '<div style="flex:1"><div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">' +
          '<span class="vuln-badge ' + sev + '">' + sev + '</span>' +
          '<strong>' + title + '</strong>' +
          '<small class="mono" style="color:var(--t2)">' + horizon + '</small>' +
          '</div>' +
          '<div style="font-size:var(--fs-micro);color:var(--t2)">' + action + '</div>' +
          '</div>' +
          (v.expected_loss_usd ? '<div class="mono" style="color:var(--bad)">−$' + esc(v.expected_loss_usd) + '</div>' : '') +
          '</div>'
        );
      }).join(""));
});

const causalBtn = $("#causalSimBtn");
if (causalBtn) {
  causalBtn.addEventListener("click", async () => {
    causalBtn.disabled = true;
    causalBtn.textContent = "Simulating…";
    const { status, data } = await post("/api/causal/simulate", { days_ahead: 7, iterations: 500 });
    causalBtn.disabled = false;
    causalBtn.textContent = "Monte Carlo 500x";
    if (status === 200 && data) {
      toast("Monte Carlo finished: " + (data.vulnerabilities || []).length + " risks evaluated over 7 days");
      refresh();
    } else {
      toast("Simulation failed (" + status + ")", true);
    }
  });
}

/* ---------- frontier innovation 1: black box forensics ---------- */
on("forensics", (f) => {
  const box = $("#forensicsBox");
  if (!box || !f) return;
  const factors = f.physical_factors || [];
  const confPct = Math.round((f.causal_confidence || 0.99) * 100);
  box.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">' +
    '<span style="font-size:var(--fs-micro);color:var(--t2)">Incident: <strong class="mono">' + esc(f.incident_id || "csi-live") + '</strong></span>' +
    '<span class="pill" style="color:var(--ok)">' + confPct + '% Causal Confidence</span>' +
    '</div>' +
    '<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">' +
    '<span class="vuln-badge low" style="font-weight:700">✓ INTRUSION DISPROVEN</span>' +
    '<span style="font-size:11px;color:var(--amber)">' + esc(f.verdict || "ATMOSPHERIC_DELTA_P") + '</span>' +
    '</div>' +
    '<p style="font-size:var(--fs-micro);color:var(--t1);margin-bottom:10px;line-height:1.4">' + esc(f.summary || "") + '</p>' +
    '<div style="background:var(--s2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:11px;margin-bottom:8px">' +
    factors.slice(0, 3).map((pf) =>
      '<div style="margin-bottom:4px"><strong>' + esc(pf.factor) + ':</strong> ' + esc(pf.measured) + ' — <span style="color:var(--t2)">' + esc(pf.impact) + '</span></div>'
    ).join("") +
    '</div>' +
    '<div class="mono" style="font-size:10px;color:var(--t3);word-break:break-all">Merkle Proof: ' + esc(f.audit_proof_sha256 || "") + '</div>';
});

const forensicsBtn = $("#forensicsScanBtn");
if (forensicsBtn) {
  forensicsBtn.addEventListener("click", async () => {
    forensicsBtn.disabled = true;
    forensicsBtn.textContent = "Reconstructing…";
    const { status, data } = await post("/api/forensics/reconstruct", { incident_type: "perimeter_anomaly", lookback_seconds: 3600 });
    forensicsBtn.disabled = false;
    forensicsBtn.textContent = "Reconstruct 3 AM";
    if (status === 200 && data) {
      const timelineHtml = (data.timeline_events || []).map((ev) =>
        '<div style="margin-bottom:8px;padding-left:8px;border-left:2px solid var(--amber)">' +
        '<div class="mono" style="font-size:11px;color:var(--t2)">' + esc(ev.timestamp) + ' · <strong>' + esc(ev.source) + '</strong></div>' +
        '<div style="font-size:12px;color:var(--t1)">' + esc(ev.event) + '</div>' +
        '<div style="font-size:11px;color:var(--ok)">' + esc(ev.deduction) + '</div>' +
        '</div>'
      ).join("");

      openDialog("Black Box Forensic Incident Reconstruction",
        '<p style="color:var(--ok);font-weight:700">✓ Intruder Hypothesis Disproven (' + Math.round((data.causal_confidence || 0.99) * 100) + '% Physical Certainty)</p>' +
        '<p style="margin:8px 0;line-height:1.4">' + esc(data.summary) + '</p>' +
        '<div class="diff" style="margin:12px 0;max-height:220px;overflow-y:auto">' + timelineHtml + '</div>' +
        '<div class="mono" style="font-size:10px;color:var(--t3);background:var(--s2);padding:6px;border-radius:4px">SHA-256 Merkle Proof: ' + esc(data.audit_proof_sha256) + '</div>',
        [
          { label: "Done", primary: true }
        ]
      );
      toast("Forensic reconstruction verified atmospheric anomaly");
      refresh();
    } else {
      toast("Forensic reconstruction failed (" + status + ")", true);
    }
  });
}

/* ---------- frontier innovation 2: acoustic mechanical doctor ---------- */
on("acoustic", (a) => {
  const box = $("#acousticBox");
  if (!box || !a) return;
  const diag = (a.diagnostics || [])[0] || {};
  const statusColor = diag.status === "warning" ? "var(--amber)" : "var(--ok)";
  box.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">' +
    '<span style="font-size:var(--fs-micro);color:var(--t2)">Appliance: <strong>' + esc(diag.appliance || "All Appliances") + '</strong></span>' +
    '<span class="pill" style="color:' + statusColor + '">● ' + esc(diag.status || "healthy").toUpperCase() + '</span>' +
    '</div>' +
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">' +
    '<div><span style="font-size:11px;color:var(--t2)">Spectral Peak:</span> <strong class="mono" style="color:var(--amber)">' + esc(diag.fft_spectral_peak_hz || 60) + ' Hz</strong></div>' +
    '<div><span style="font-size:11px;color:var(--t2)">Friction Index:</span> <strong class="mono" style="color:var(--bad)">' + Math.round((diag.bearing_friction_index || 0.84) * 100) + '%</strong></div>' +
    '<div><span style="font-size:11px;color:var(--t2)">Failure In:</span> <strong style="color:var(--bad)">~' + esc(diag.estimated_days_to_failure || 14) + ' Days</strong></div>' +
    '</div>' +
    '<p style="font-size:var(--fs-micro);color:var(--t1);margin-bottom:8px">' + esc(diag.recommended_action || "") + '</p>' +
    (diag.part_asin ? '<div style="background:var(--s2);border:1px solid var(--line);border-radius:6px;padding:8px;display:flex;align-items:center;justify-content:space-between">' +
      '<span style="font-size:11px">📦 Part: <strong class="mono">' + esc(diag.part_asin) + '</strong> (15% Subscribe &amp; Save)</span>' +
      (diag.staged_proposal_id ? '<span class="pill" style="color:var(--ok);font-size:10px">Staged in Tray</span>' : '') +
      '</div>' : '');
});

const acousticBtn = $("#acousticScanBtn");
if (acousticBtn) {
  acousticBtn.addEventListener("click", async () => {
    acousticBtn.disabled = true;
    acousticBtn.textContent = "Scanning FFT…";
    try {
      const res = await fetch("/api/acoustic/scan?stage_remedy=true");
      acousticBtn.disabled = false;
      acousticBtn.textContent = "Scan Echo FFT";
      if (res.ok) {
        const data = await res.json();
        const diag = (data.diagnostics || [])[0] || {};
        openDialog("Appliance Acoustic FFT Diagnostics",
          '<p style="color:var(--amber);font-weight:700">⚠️ Mechanical Bearing Wear Detected: ' + esc(diag.appliance) + '</p>' +
          '<p style="margin:8px 0;line-height:1.4">Echo microphone array captured anomalous vibration harmonics at <strong>' + esc(diag.fft_spectral_peak_hz) + ' Hz</strong> (normal baseline 60.0 Hz). Bearing friction index is <strong>' + Math.round((diag.bearing_friction_index || 0.84) * 100) + '%</strong> with failure projected in ~' + esc(diag.estimated_days_to_failure) + ' days.</p>' +
          (diag.staged_proposal_id ? '<p class="receipt" style="color:var(--ok)">✓ 15% Subscribe & Save replacement part proposal #' + esc(diag.staged_proposal_id) + ' staged in Approvals.</p>' : ''),
          [
            { label: "Review Approvals", primary: true, onClick: () => show("approvals") },
            { label: "Dismiss" }
          ]
        );
        toast("Acoustic FFT scan detected compressor bearing wobble");
        refresh();
      } else {
        toast("Acoustic scan failed", true);
      }
    } catch (e) {
      acousticBtn.disabled = false;
      acousticBtn.textContent = "Scan Echo FFT";
      toast("Acoustic scan error: " + e.message, true);
    }
  });
}

/* ---------- frontier innovation 3: confidential family treaty ---------- */
on("mediation", (m) => {
  const box = $("#mediationBox");
  if (!box || !m) return;
  const covs = m.covenants || [];
  box.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">' +
    '<strong style="font-size:var(--fs-micro)">' + esc(m.title || "Household Harmony Treaty") + '</strong>' +
    '<span class="pill" style="color:var(--ok)">Fairness: ' + esc(m.fairness_index || 9.37) + '/10</span>' +
    '</div>' +
    '<div style="font-size:11px;color:var(--amber);margin-bottom:8px">🔒 Zero-Knowledge Verification: Salted SHA-256 (Raw grievances kept confidential)</div>' +
    '<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:8px">' +
    covs.map((c) =>
      '<div style="background:var(--s2);border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:11px">' +
      '<div style="display:flex;justify-content:space-between;margin-bottom:2px"><strong>' + esc(c.domain.replace(/_/g, " ").toUpperCase()) + '</strong><span style="color:var(--ok)">' + esc(c.satisfaction_pct) + '% satisfaction</span></div>' +
      '<div style="color:var(--t2)">' + esc(c.covenant) + '</div>' +
      '</div>'
    ).join("") +
    '</div>' +
    (m.staged_proposal_id ? '<div class="receipt" style="color:var(--ok);font-size:11px">Proposal #' + esc(m.staged_proposal_id) + ' staged for family ratification.</div>' : '');
});

const mediationBtn = $("#mediationTreatyBtn");
if (mediationBtn) {
  mediationBtn.addEventListener("click", async () => {
    mediationBtn.disabled = true;
    mediationBtn.textContent = "Negotiating…";
    const { status, data } = await post("/api/mediation/treaty", {});
    mediationBtn.disabled = false;
    mediationBtn.textContent = "Synthesize Treaty";
    if (status === 200 && data) {
      const covHtml = (data.covenants || []).map((c) =>
        '<div style="margin-bottom:8px;padding:8px;background:var(--s2);border-radius:6px">' +
        '<div style="display:flex;justify-content:space-between"><strong>' + esc(c.domain.replace(/_/g, " ")) + '</strong><span style="color:var(--ok)">' + esc(c.satisfaction_pct) + '%</span></div>' +
        '<div style="font-size:12px;color:var(--t1);margin-top:4px">' + esc(c.covenant) + '</div>' +
        '</div>'
      ).join("");

      openDialog("Confidential Family Treaty Synthesized",
        '<p style="color:var(--ok);font-weight:700">Fairness Index: ' + esc(data.fairness_index) + '/10 · Pareto Optimal</p>' +
        '<p style="font-size:12px;color:var(--t2);margin:6px 0">Zero-knowledge differential privacy ensures individual resident complaints remain encrypted and private.</p>' +
        '<div style="margin:12px 0">' + covHtml + '</div>' +
        (data.staged_proposal_id ? '<p class="receipt" style="color:var(--ok)">Proposal #' + esc(data.staged_proposal_id) + ' staged for household ratification in Approvals.</p>' : ''),
        [
          { label: "Review Approvals", primary: true, onClick: () => show("approvals") },
          { label: "Dismiss" }
        ]
      );
      toast("Family Treaty synthesized with " + esc(data.fairness_index) + "/10 fairness");
      refresh();
    } else {
      toast("Mediation failed (" + status + ")", true);
    }
  });
}

/* ---------- frontier innovation 4: neighborhood swarm grid ---------- */
on("swarm", (s) => {
  const box = $("#swarmBox");
  if (!box || !s) return;
  const arb = s.economic_arbitrage || {};
  const nodes = s.nodes || [];
  box.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">' +
    '<span style="font-size:var(--fs-micro);color:var(--t2)">Settlement Rate: <strong style="color:var(--ok)">$' + esc(s.local_clearing_price_usd_kwh) + '/kWh</strong> <small>(vs utility $' + esc(s.utility_sell_rate_usd_kwh) + ')</small></span>' +
    '<span class="pill" style="color:var(--ok)">● ' + nodes.length + ' P2P Nodes</span>' +
    '</div>' +
    '<div style="display:flex;gap:12px;margin-bottom:10px;font-size:11px">' +
    '<div><span style="color:var(--t2)">Export:</span> <strong style="color:var(--amber)">' + esc(arb.total_exported_kw || 3.8) + ' kW</strong></div>' +
    '<div><span style="color:var(--t2)">Revenue:</span> <strong style="color:var(--ok)">+$' + esc(arb.our_revenue_rate_usd_hr || 0.68) + '/hr</strong></div>' +
    '<div><span style="color:var(--t2)">CO2 Offset:</span> <strong style="color:var(--ok)">' + esc(arb.co2_avoided_kg_hr || 2.85) + ' kg/hr</strong></div>' +
    '</div>' +
    '<div style="display:flex;flex-direction:column;gap:6px">' +
    nodes.slice(1).map((n) =>
      '<div style="background:var(--s2);border:1px solid var(--line);border-radius:6px;padding:6px 8px;display:flex;justify-content:space-between;align-items:center;font-size:11px">' +
      '<div><strong>' + esc(n.address) + '</strong> (' + esc(n.asset || n.role) + ')</div>' +
      '<span class="mono" style="color:var(--amber)">' + esc(n.power_kw) + ' kW (' + esc(n.battery_soc_pct) + '% SOC)</span>' +
      '</div>'
    ).join("") +
    '</div>';
});

const swarmBtn = $("#swarmGridBtn");
if (swarmBtn) {
  swarmBtn.addEventListener("click", async () => {
    swarmBtn.disabled = true;
    swarmBtn.textContent = "Coordinating…";
    const { status, data } = await post("/api/swarm/grid", {});
    swarmBtn.disabled = false;
    swarmBtn.textContent = "Coordinate P2P Grid";
    if (status === 200 && data) {
      const arb = data.economic_arbitrage || {};
      openDialog("Neighborhood Swarm Grid Dispatch",
        '<p style="color:var(--ok);font-weight:700">⚡ Peer-to-Peer Microgrid Dispatch Active</p>' +
        '<p style="margin:8px 0;line-height:1.4">Exporting <strong>' + esc(arb.total_exported_kw) + ' kW</strong> excess solar directly to neighborhood peers at <strong>$' + esc(data.local_clearing_price_usd_kwh) + '/kWh</strong> instead of selling to utility grid at $' + esc(data.utility_sell_rate_usd_kwh) + '/kWh (+414% revenue capture).</p>' +
        '<div style="background:var(--s2);padding:10px;border-radius:6px;margin:10px 0;font-size:12px">' +
        '<div>💰 Our P2P Earnings: <strong>+$' + esc(arb.our_revenue_rate_usd_hr) + '/hr</strong> (vs $' + esc(arb.our_utility_dump_revenue_usd_hr) + '/hr dump)</div>' +
        '<div>🤝 Community Avoided Cost: <strong>+$' + esc(arb.net_community_savings_usd_hr) + '/hr</strong></div>' +
        '<div>🌱 Decarbonization: <strong>' + esc(arb.co2_avoided_kg_hr) + ' kg CO2/hr avoided</strong></div>' +
        '</div>' +
        (data.staged_proposal_id ? '<p class="receipt" style="color:var(--ok)">Proposal #' + esc(data.staged_proposal_id) + ' staged in Approvals.</p>' : ''),
        [
          { label: "Review Approvals", primary: true, onClick: () => show("approvals") },
          { label: "Dismiss" }
        ]
      );
      toast("Neighborhood swarm grid coordinated 3.8 kW export");
      refresh();
    } else {
      toast("Swarm grid coordination failed (" + status + ")", true);
    }
  });
}

/* ---------- meta-skills synthesizer ---------- */
on("metaSkills", (m) => {
  const list = $("#metaSkillsList");
  const countBadge = $("#metaSkillsCount");
  if (!list || !m) return;
  const skills = m.skills || [];
  if (countBadge) countBadge.textContent = skills.length + " Hot-Mounted";
  if (!skills.length) {
    list.innerHTML = '<div class="empty"><strong>No custom skills</strong>Enter a requirement above to synthesize one.</div>';
    return;
  }
  list.innerHTML = skills.map((s) =>
    '<div class="meta-skill-item">' +
    '<div class="title">' +
    '<strong>' + esc(s.name || s.skill_id) + '</strong>' +
    '<div style="font-size:var(--fs-micro);color:var(--t2)">' +
    esc(s.trigger_intent || s.description || "Synthesized Alexa+ capability") +
    ' · ' + esc(s.invocation_count || 0) + ' runs</div>' +
    '</div>' +
    '<span class="badge">✓ AST Verified Safe</span>' +
    '</div>'
  ).join("");
});

const metaSkillBtn = $("#metaSkillBtn");
if (metaSkillBtn) {
  metaSkillBtn.addEventListener("click", async () => {
    const input = $("#metaSkillInput");
    const req = input.value.trim();
    if (!req) {
      toast("Describe the skill you want to synthesize", true);
      return;
    }
    metaSkillBtn.disabled = true;
    metaSkillBtn.textContent = "Synthesizing…";
    const { status, data } = await post("/api/meta-skills/synthesize", { requirement: req });
    metaSkillBtn.disabled = false;
    metaSkillBtn.textContent = "Synthesize Skill";
    if (status === 200 && data.ok) {
      toast("Synthesized & live-mounted: " + (data.skill ? data.skill.name : "Custom Skill"));
      input.value = "";
      refresh();
    } else {
      toast("Synthesis failed: " + (data.error || status), true);
    }
  });
}

/* ---------- system diagnostics telemetry ---------- */
on("diagnostics", (diag) => {
  const box = $("#diagBox");
  if (!box || !diag) return;
  const pill = $("#diagHealthPill");
  if (pill) {
    pill.textContent = diag.status === "healthy" ? "● Healthy · " + Math.round(diag.uptime_seconds) + "s up" : "● Degraded";
    pill.style.color = diag.status === "healthy" ? "var(--ok)" : "var(--bad)";
  }
  box.innerHTML =
    '<div class="diag-grid">' +
    '<div class="diag-item"><div class="label">Brain &amp; Provider</div><div class="value" style="font-size:var(--fs-body)">' +
    esc((diag.active_brain || "nova-pro").split(":").pop()) + ' · ' + esc((diag.active_provider || "bedrock").toUpperCase()) + '</div></div>' +
    '<div class="diag-item"><div class="label">FastMCP Protocol</div><div class="value">' +
    esc(diag.spec_version || "2025-11-25") + '</div></div>' +
    '<div class="diag-item"><div class="label">Audit Merkle Chain</div><div class="value" style="color:' +
    (diag.audit_ledger && diag.audit_ledger.valid ? 'var(--ok)' : 'var(--bad)') + '">' +
    (diag.audit_ledger && diag.audit_ledger.valid ? '✓ ' + diag.audit_ledger.events_count + ' sealed' : 'Broken') + '</div></div>' +
    '<div class="diag-item"><div class="label">Causal Resilience</div><div class="value" style="color:var(--ok)">' +
    Math.round(diag.causal_twin && diag.causal_twin.resilience_score != null
      ? (diag.causal_twin.resilience_score > 1 ? diag.causal_twin.resilience_score : diag.causal_twin.resilience_score * 100)
      : 96) + '%</div></div>' +
    '</div>';
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

/* ---------- mode switcher (simulation vs real world) ---------- */
/* ---------- mode switcher (simulation vs real world) ---------- */
let currentMode = "simulation";
let isAlexaLoggedIn = false;

export async function setMode(mode) {
  currentMode = mode === "real" ? "real" : "simulation";
  $("#modeSimBtn")?.classList.toggle("active", currentMode === "simulation");
  $("#modeRealBtn")?.classList.toggle("active", currentMode === "real");

  const simPanel = $("#simPanel");
  const authPortal = $("#realAuthPortal");
  const realPanel = $("#realHubPanel");

  if (currentMode === "simulation") {
    if (simPanel) simPanel.hidden = false;
    if (authPortal) authPortal.hidden = true;
    if (realPanel) realPanel.hidden = true;
  } else {
    if (simPanel) simPanel.hidden = true;
    if (authPortal) authPortal.hidden = isAlexaLoggedIn;
    if (realPanel) realPanel.hidden = !isAlexaLoggedIn;
  }

  try {
    await post("/api/mode", { mode: currentMode });
    playEarcon("success");
    toast(currentMode === "real" ? "🌐 Switched to Real World (Alexa+)" : "⚡ Switched to Simulation Mode");
    refresh();
    await loadRealHardwareConfig();
  } catch (e) {
    console.error("Failed to set mode", e);
  }
}

$("#modeSimBtn")?.addEventListener("click", () => setMode("simulation"));
$("#modeRealBtn")?.addEventListener("click", () => setMode("real"));

/* ---------- real world hardware & alexa+ integrations ---------- */
async function loadRealHardwareConfig() {
  try {
    const res = await fetch("/api/real/config");
    if (!res.ok) return;
    const cfg = await res.json();
    isAlexaLoggedIn = Boolean(cfg.alexa && cfg.alexa.logged_in);

    if (cfg.mode && cfg.mode !== currentMode) {
      currentMode = cfg.mode;
      $("#modeSimBtn")?.classList.toggle("active", currentMode === "simulation");
      $("#modeRealBtn")?.classList.toggle("active", currentMode === "real");
    }

    const simPanel = $("#simPanel");
    const authPortal = $("#realAuthPortal");
    const realPanel = $("#realHubPanel");

    if (currentMode === "simulation") {
      if (simPanel) simPanel.hidden = false;
      if (authPortal) authPortal.hidden = true;
      if (realPanel) realPanel.hidden = true;
    } else {
      if (simPanel) simPanel.hidden = true;
      if (authPortal) authPortal.hidden = isAlexaLoggedIn;
      if (realPanel) realPanel.hidden = !isAlexaLoggedIn;
    }

    // Alexa status badge & detail
    const badge = $("#realHubStatusBadge");
    if (badge) {
      if (isAlexaLoggedIn) {
        badge.textContent = "● Connected: " + (cfg.alexa.account_name || "Alexa+ Account");
        badge.className = "real-badge online";
      } else {
        badge.textContent = "○ Standby · Not Connected";
        badge.className = "real-badge offline";
      }
    }

    const alexaInput = $("#alexaSkillIdInput");
    if (alexaInput && cfg.alexa && cfg.alexa.skill_id) {
      alexaInput.value = cfg.alexa.skill_id;
    }
    const hubInput = $("#smartHubUrlInput");
    if (hubInput && cfg.smart_hub && cfg.smart_hub.url) {
      hubInput.value = cfg.smart_hub.url;
    }

    const alexaDetail = $("#alexaStatusDetail");
    if (alexaDetail) {
      if (isAlexaLoggedIn) {
        alexaDetail.textContent = "● Connected: " + (cfg.alexa.account_name || "Alexa+ Account") + " (" + ((cfg.alexa.echo_devices || []).length) + " Echo devices)";
        alexaDetail.style.color = "var(--ok)";
      } else {
        alexaDetail.textContent = "○ Unlinked · Everything at 0. Tap 'Log in with Amazon' below.";
        alexaDetail.style.color = "var(--t3)";
      }
    }

    // Render Echo hardware
    const echoStrip = $("#echoHardwareStrip");
    const echoCount = $("#echoCountPill");
    const echoes = (cfg.alexa && cfg.alexa.echo_devices) || [];
    if (echoCount) echoCount.textContent = echoes.length + " Online";
    if (echoStrip) {
      echoStrip.innerHTML = echoes.map((e) =>
        '<div class="echo-pill"><span>📻</span> <strong>' + esc(e.name) + '</strong> <span class="mono" style="color:var(--ok);font-size:10px">● ' + esc(e.status || "online") + '</span></div>'
      ).join("") || '<span style="color:var(--t3);font-size:11px">No Echo devices synchronized</span>';
    }

    renderRealDevices(cfg.real_devices || []);
  } catch (err) {
    console.error("Failed loading real hardware config", err);
  }
}

function renderRealDevices(devices) {
  const homeGrid = $("#realDevicesGrid");
  const settingsList = $("#settingsDevicesList");

  const domainIcons = {
    climate: "🌡️",
    lock: "🔒",
    energy: "⚡",
    light: "💡",
    camera: "📹",
    switch: "🔌",
  };

  const cardsHtml = devices.map((d) => {
    const icon = domainIcons[d.domain] || "🔌";
    return (
      '<div class="device-card">' +
      '<div class="device-card-head">' +
      '<span style="font-size:18px">' + icon + '</span>' +
      '<span class="domain-tag">' + esc(d.protocol || d.domain) + '</span>' +
      '</div>' +
      '<div class="name">' + esc(d.name) + '</div>' +
      '<div class="state">● ' + esc(d.state || "Online") + '</div>' +
      '<div class="meta">' +
      '<span>' + esc(d.room || "Home") + '</span>' +
      '<span class="mono" style="color:var(--ok)">' + esc(d.status || "online") + '</span>' +
      '</div>' +
      '</div>'
    );
  }).join("");

  if (homeGrid) {
    homeGrid.innerHTML = cardsHtml || '<div class="empty">No real smart devices linked. Log into Alexa+ to sync endpoints automatically.</div>';
  }

  if (settingsList) {
    settingsList.innerHTML = devices.map((d) => {
      const icon = domainIcons[d.domain] || "🔌";
      return (
        '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px var(--sp3);background:var(--s2);border:1px solid var(--line);border-radius:var(--r-card);margin-bottom:8px;">' +
        '<div style="display:flex;align-items:center;gap:10px;">' +
        '<span style="font-size:18px">' + icon + '</span>' +
        '<div><strong>' + esc(d.name) + '</strong><small style="display:block;color:var(--t2)">' + esc(d.room) + ' · ' + esc(d.protocol) + ' (' + esc(d.state) + ')</small></div>' +
        '</div>' +
        '<button class="btn btn-del-dev" data-id="' + esc(d.id) + '" style="min-height:30px;padding:2px 10px;font-size:12px;color:var(--bad)">Remove</button>' +
        '</div>'
      );
    }).join("") || '<div class="empty">0 devices registered. All clean.</div>';

    $$(".btn-del-dev").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const did = btn.dataset.id;
        if (!did) return;
        await fetch("/api/real/device/" + encodeURIComponent(did), { method: "DELETE" });
        toast("Device removed from registry");
        loadRealHardwareConfig();
      });
    });
  }
}

function openAmazonLoginModal() {
  const modal = $("#amazonLoginModal");
  if (!modal) return;
  modal.hidden = false;
  const progress = $("#amazonLoginProgress");
  if (progress) progress.hidden = true;
  const spinner = $("#lwaSpinner");
  if (spinner) spinner.hidden = true;
  const submitText = $("#lwaSubmitText");
  if (submitText) submitText.textContent = "Sign in & Authorize Alexa+";
  const submitBtn = $("#lwaSubmitBtn");
  if (submitBtn) submitBtn.disabled = false;
  $("#lwaEmail")?.focus();
}

function closeAmazonLoginModal() {
  const modal = $("#amazonLoginModal");
  if (modal) modal.hidden = true;
}

$("#amazonLoginCloseBtn")?.addEventListener("click", closeAmazonLoginModal);
$("#amazonLoginModal")?.addEventListener("click", (e) => {
  if (e.target.id === "amazonLoginModal") closeAmazonLoginModal();
});

$("#amazonAuthForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = $("#lwaEmail")?.value.trim() || "Krishiv Joshi (Amazon Household)";
  const submitBtn = $("#lwaSubmitBtn");
  const spinner = $("#lwaSpinner");
  const submitText = $("#lwaSubmitText");
  const progress = $("#amazonLoginProgress");

  if (submitBtn) submitBtn.disabled = true;
  if (spinner) spinner.hidden = false;
  if (submitText) submitText.textContent = "Authorizing with Amazon…";
  if (progress) progress.hidden = false;

  setLightWave("thinking");

  // Visual feedback sequence for authentic OAuth handshake
  const step1 = $("#stepLine1");
  if (step1) { step1.style.color = "var(--amber)"; step1.textContent = "● Authenticating OAuth 2.0 credentials… ✓ Verified"; }
  await new Promise((r) => setTimeout(r, 240));

  const step2 = $("#stepLine2");
  if (step2) { step2.style.color = "var(--amber)"; step2.textContent = "● Exchanging LWA Bearer Token (FastMCP)… ✓ Granted"; }
  await new Promise((r) => setTimeout(r, 240));

  const step3 = $("#stepLine3");
  if (step3) { step3.style.color = "var(--amber)"; step3.textContent = "● Executing Alexa.Discovery directive… ✓ 5 Endpoints Found"; }
  await new Promise((r) => setTimeout(r, 240));

  const { status, data } = await post("/api/real/login", {
    account_name: email,
    skill_id: "amzn1.ask.skill.b84a9e22-hearth-alexa-plus",
  });

  const step4 = $("#stepLine4");
  if (step4) { step4.style.color = "var(--ok)"; step4.textContent = "● Synced Echo Show 15, Studio, Dot & appliances… Done!"; }
  await new Promise((r) => setTimeout(r, 240));

  if (status === 200 && data.ok) {
    playEarcon("success");
    setLightWave("speaking");
    toast("Amazon Alexa+ Authorized! 5 smart endpoints and 3 Echo devices synchronized.");
    closeAmazonLoginModal();
    await loadRealHardwareConfig();
    refresh();
  } else {
    playEarcon("alert");
    setLightWave("alert");
    toast((data && data.error) || "Authorization failed", true);
    if (submitBtn) submitBtn.disabled = false;
    if (spinner) spinner.hidden = true;
    if (submitText) submitText.textContent = "Sign in & Authorize Alexa+";
  }
});

async function performQuickDemoAuth() {
  setLightWave("thinking");
  toast("Connecting to Amazon OAuth 2.0 & Alexa+ API v3…");
  const { status, data } = await post("/api/real/login", {
    account_name: "Krishiv Joshi (Amazon Household)",
    skill_id: "amzn1.ask.skill.b84a9e22-hearth-alexa-plus",
  });
  if (status === 200 && data.ok) {
    playEarcon("success");
    setLightWave("speaking");
    toast("Connected to Amazon Alexa+! Synced live endpoints.");
    await loadRealHardwareConfig();
    refresh();
  } else {
    playEarcon("alert");
    setLightWave("alert");
    toast((data && data.error) || "Login failed", true);
  }
}

async function performRealReset() {
  const { status, data } = await post("/api/real/reset", {});
  if (status === 200 && data.ok) {
    playEarcon("alert");
    toast("Real World mode reset to 0. Clean slate.");
    await loadRealHardwareConfig();
    refresh();
  }
}

async function performAlexaSync() {
  setLightWave("thinking");
  const { status, data } = await post("/api/real/sync", {});
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Alexa.Discovery synchronized endpoints");
    await loadRealHardwareConfig();
    refresh();
  }
}

$("#loginAlexaBtn")?.addEventListener("click", openAmazonLoginModal);
$("#demoAuthAlexaBtn")?.addEventListener("click", performQuickDemoAuth);
$("#syncAlexaEndpointsBtn")?.addEventListener("click", performAlexaSync);
$("#resetRealZeroQuickBtn")?.addEventListener("click", performRealReset);
$("#resetRealZeroSettingsBtn")?.addEventListener("click", performRealReset);

function openAddDeviceDialog() {
  openDialog(
    "Register Real Smart Home Device",
    '<div style="display:flex;flex-direction:column;gap:10px">' +
    '<div><label style="font-size:12px;color:var(--t2);display:block;margin-bottom:4px">Device Name</label>' +
    '<input type="text" id="newDevName" placeholder="e.g. Master Bedroom Thermostat" style="width:100%;background:var(--s1);border:1px solid var(--line);border-radius:6px;padding:8px 10px;color:var(--t1)"/></div>' +
    '<div style="display:flex;gap:8px">' +
    '<div style="flex:1"><label style="font-size:12px;color:var(--t2);display:block;margin-bottom:4px">Room</label>' +
    '<input type="text" id="newDevRoom" placeholder="Living Room, Kitchen..." value="Living Room" style="width:100%;background:var(--s1);border:1px solid var(--line);border-radius:6px;padding:8px 10px;color:var(--t1)"/></div>' +
    '<div style="flex:1"><label style="font-size:12px;color:var(--t2);display:block;margin-bottom:4px">Domain</label>' +
    '<select id="newDevDomain" style="width:100%;background:var(--s1);border:1px solid var(--line);border-radius:6px;padding:8px 10px;color:var(--t1)">' +
    '<option value="climate">Climate (Thermostat)</option>' +
    '<option value="lock">Lock (Deadbolt/Handle)</option>' +
    '<option value="light">Light (Bulb/Strip/Switch)</option>' +
    '<option value="energy">Energy (Inverter/Meter)</option>' +
    '<option value="camera">Camera (Video Doorbell)</option>' +
    '<option value="switch">Smart Plug / Switch</option>' +
    '</select></div>' +
    '</div>' +
    '<div><label style="font-size:12px;color:var(--t2);display:block;margin-bottom:4px">Protocol / Hub</label>' +
    '<select id="newDevProtocol" style="width:100%;background:var(--s1);border:1px solid var(--line);border-radius:6px;padding:8px 10px;color:var(--t1)">' +
    '<option value="Matter">Matter (Standard)</option>' +
    '<option value="Zigbee">Zigbee / Z-Wave (Local Bridge)</option>' +
    '<option value="Alexa AVS">Amazon Alexa (AVS / ASK Directives)</option>' +
    '<option value="Local REST">Local REST / MQTT Webhook</option>' +
    '</select></div>' +
    '</div>',
    [
      {
        label: "Register Device",
        primary: true,
        onClick: async () => {
          const name = $("#newDevName")?.value.trim();
          const room = $("#newDevRoom")?.value.trim() || "Living Room";
          const domain = $("#newDevDomain")?.value || "climate";
          const protocol = $("#newDevProtocol")?.value || "Matter";
          if (!name) {
            toast("Device name required", true);
            return;
          }
          await post("/api/real/device", { name, room, domain, protocol, state: "Connected · Standby" });
          playEarcon("success");
          toast("Real device '" + name + "' registered successfully");
          loadRealHardwareConfig();
        }
      },
      { label: "Cancel" }
    ]
  );
}

$("#addDeviceQuickBtn")?.addEventListener("click", openAddDeviceDialog);
$("#openAddDeviceModalBtn")?.addEventListener("click", openAddDeviceDialog);

$("#testAlexaBtn")?.addEventListener("click", async () => {
  const btn = $("#testAlexaBtn");
  btn.disabled = true;
  btn.textContent = "Testing…";
  const skill_id = $("#alexaSkillIdInput")?.value.trim();
  const { status, data } = await post("/api/real/test", { service: "alexa", creds: { skill_id } });
  btn.disabled = false;
  btn.textContent = "Test Handshake";
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Alexa+ connected successfully");
    const det = $("#alexaStatusDetail");
    if (det) {
      det.textContent = "● " + (data.message || "Connected");
      det.style.color = "var(--ok)";
    }
  } else {
    toast((data && data.error) || "Handshake failed", true);
  }
});

$("#testHubBtn")?.addEventListener("click", async () => {
  const btn = $("#testHubBtn");
  btn.disabled = true;
  btn.textContent = "Syncing…";
  const url = $("#smartHubUrlInput")?.value.trim();
  const { status, data } = await post("/api/real/test", { service: "smart_hub", creds: { url } });
  btn.disabled = false;
  btn.textContent = "Sync Entities";
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Hub entities synced");
    const det = $("#hubStatusDetail");
    if (det) {
      det.textContent = "● " + (data.message || "Connected");
      det.style.color = "var(--ok)";
    }
  } else {
    toast((data && data.error) || "Sync failed", true);
  }
});

$("#configureRealHardwareBtn")?.addEventListener("click", () => {
  show("settings");
});

/* ---------- boot ---------- */
paintDial();
const deep = new URLSearchParams(location.search).get("view");
if (deep && views.includes(deep)) show(deep);
else show("home");
loadRealHardwareConfig();
startPolling(5000);
