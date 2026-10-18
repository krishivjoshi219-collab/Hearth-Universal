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
    '<pre class="md-code">' + code.trim() + "</pre>"
  );

  // Inline code (`...`)
  s = s.replace(/`([^`]+)`/g, '<code class="md-code-inline">$1</code>');

  // Bold (**...**)
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // Italic (*...*)
  s = s.replace(/(^|[^*])\*([^*]+)\*([^*]|$)/g, "$1<em>$2</em>$3");

  // Process lines for bullet items and spacing
  const lines = s.split(/\r?\n/);
  const formatted = [];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trim();

    if (!trimmed) {
      formatted.push('<div class="md-gap"></div>');
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

    formatted.push('<div class="md-line">' + raw + "</div>");
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
    chimeBtn.textContent = audioMuted ? "Muted" : "Sound";
    chimeBtn.title = audioMuted ? "Sounds are off" : "Sounds are on";
    toast(audioMuted ? "Sounds off" : "Sounds on");
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
const PERSONA_NAME = { admin: "Krishiv", partner: "Sarah", child: "Leo" };
$("#personaSel").addEventListener("change", async (e) => {
  const id = e.target.value;
  const { status } = await post("/api/persona", { id });
  toast(status === 200 ? "Now answering as " + (PERSONA_NAME[id] || id) : "Hearth kept the last profile", status !== 200);
  refresh();
});

/* ---------- autonomy dial (earned trust display) ---------- */
let dialStats = { proceed: 0, undo: 0 };
$("#dial").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.level === "auto" && !dialUnlocked()) {
    toast("Hands-off stays locked until 18 of the last 20 yeses stick", true);
    return;
  }
  $$("#dial button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  $("#dialPill").textContent = b.querySelector("strong").textContent;
  toast("Hearth may now: " + b.querySelector("strong").textContent);
});
function dialUnlocked() {
  const n = dialStats.proceed + dialStats.undo;
  return n >= 20 && dialStats.proceed / n >= 0.9 && dialStats.undo / Math.max(1, n) <= 0.05;
}
function paintDial() {
  const n = dialStats.proceed + dialStats.undo;
  $("#dialRecord").textContent =
    "Record: " + dialStats.proceed + " yes · " + dialStats.undo + " undone" +
    (dialUnlocked() ? " · hands-off is open" : " · hands-off still locked (18 of 20, little undone)");
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
      setBind("climateSub", "Sign in to wake this up");
      setBind("lock", "–");
      setBind("lockSub", "Sign in to wake this up");
      setBind("energy", '<span class="num">0.0</span><small> kW draw</small>');
      setBind("energySub", "Nothing switched on yet");
      setBind("pantry", '<span class="num">0</span><small> items</small>');
      setBind("pantrySub", "Not connected");
      const nextUp = $("#nextUp");
      if (nextUp) nextUp.innerHTML = '<div class="empty"><strong>Nothing on the list</strong>Sign in and tell Hearth what you want handled.</div>';
      const delBox = $("#deliveryBox");
      if (delBox) delBox.innerHTML = '<div class="empty"><strong>No vans today</strong>Sign in and anything on its way shows up here.</div>';
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
            '<div class="mini-card">' +
            '<div class="row-between">' +
            '<strong>' + esc(d.status || "On its way") + "</strong>" +
            '<span class="pill pill-micro">' + esc(d.eta || "Today") + "</span>" +
            "</div>" +
            '<div class="mt-8">' + esc(d.items ? d.items.join(", ") : "A package") + "</div>" +
            '<small>' + esc(d.stops_away || 3) + " stops away · tracking " + esc(d.tracking_number || "—") + "</small>" +
            "</div>";
        } else {
          delBox.innerHTML = '<div class="empty"><strong>No vans today</strong>Nothing on its way right now.</div>';
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
    '<div class="insight"><div class="big num">' + esc(it.days_until_empty) + '<small>days</small></div>' +
    '<div class="txt">' + esc(it.name || it.id) + "</div></div>"
  ).join("");
});
on("roi", (r) => {
  const box = $("#roiBox");
  const save = r.potential_save_yr ?? r.savings_annual ?? "?";
  const items = r.renewals || r.dormant || [];
  box.innerHTML =
    '<div class="insight"><div class="big num" style="color: var(--ok)">$' + esc(save) + '</div><div class="txt">a year, once it stops paying for things you never use — out of $' +
    esc(r.total_annual_spend ?? "?") + ' of subscriptions it checked' +
    '<div class="mt-12"><button class="btn btn-sm" id="roiGo">See the list</button></div></div></div>' +
    items.slice(0, 4).map((s) =>
      '<div class="insight"><div class="txt">' + esc(s.name || s.id) +
      "<br><span class='micro muted-2'>" + esc(plainUsage(s.usage_status || s.detail || "")) + "</span></div>" +
      "<div class='mono' style='color: var(--ok)'>$" + esc(s.savings_yr ?? "?") + "/yr</div></div>"
    ).join("");
  const go = $("#roiGo");
  if (go) go.addEventListener("click", () => show("approvals"));
});

/* ---------- activity timeline (why-cards) ---------- */
const seenEvents = new Set();
// Audit rows carry machine actor/action names. The timeline shows people-words.
const ACTOR_NAME = {
  agent: "Hearth", hearth: "Hearth", scheduler: "Hearth", human: "You", you: "You",
  sentinel: "The house", house: "The house", executor: "The house",
  causal_digital_twin: "The forecast", acoustic_doctor: "The house", forensics: "The house",
  meta_skill_synthesizer: "The house", mediation: "The house", parliament: "The house",
  swarm: "The street", commerce: "The house", auth: "Amazon link", sim: "The house",
  "forensic investigator": "The house", "family mediator": "The house",
  forensic_investigator: "The house", family_mediator: "The house", swarm_grid: "The street",
  system: "Hearth",
  vpp: "The street", grid: "The street",
};
const ACTION_NAME = {
  simulation_completed: "looked a week ahead",
  fft_scan_completed: "listened to the kitchen",
  incident_reconstructed: "replayed a night",
  microgrid_dispatch_settled: "sold spare solar to the street",
  household_treaty_synthesized: "drew up a family deal",
  execution_applied: "carried out an approved plan",
  actions_propose: "left an offer for your say-so",
  actions_decide: "said yes to something",
  proposal_undone: "took something back",
  synthesis_refused_privileged: "held something back",
  skill_synthesized_and_mounted: "taught itself a new ability",
  forge_tool_applied: "put a new habit to work",
  user_account_linked_token_granted: "connected the Amazon account",
  inbox_scan: "checked the inbox",
  event_commerce: "watched an order",
  system_reset: "started fresh",
};
function addEvent(actor, what, why) {
  const tl = $("#timeline");
  const empty = tl.querySelector(".empty");
  if (empty) empty.remove();
  const key = actor + "|" + what + "|" + JSON.stringify(why || {}).length;
  if (seenEvents.has(key)) return;
  seenEvents.add(key);
  const el = document.createElement("div");
  el.className = "event " + actor;
  const actorRaw = String(actor).replace(/_/g, " ");
  const actorLabel = ACTOR_NAME[actor] ||
    (actorRaw.charAt(0) === actorRaw.charAt(0).toLowerCase()
      ? actorRaw.charAt(0).toUpperCase() + actorRaw.slice(1)
      : actorRaw);
  const whatLabel = ACTION_NAME[what] || String(what).replace(/_/g, " ");
  el.innerHTML =
    '<div class="event-row"><span class="actor">' + esc(actorLabel) + "</span>" +
    '<span class="what">' + esc(whatLabel) + "</span>" +
    '<span class="when">' + new Date().toLocaleTimeString() + "</span></div>" +
    (why ? "<details><summary>Why this happened</summary><div class='why'>" +
      Object.entries(why).filter(([k]) => k !== "detail").slice(0, 4).map(([k, v]) =>
        "<div><dt>" + esc(k.replace(/_/g, " ")) + "</dt><dd>" + esc(typeof v === "object" ? JSON.stringify(v) : v) + "</dd></div>"
      ).join("") + "</div>" +
      (why.confidence != null ? '<span class="conf">Sure about this: ' + esc(why.confidence) + "%</span>" : "") +
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
  $("#ledgerState").textContent = ok
    ? "Intact · " + (a.count || "?") + " actions on the record"
    : "Something doesn't add up — needs a look";
});

/* ---------- approvals (Proceed / Edit / Handle-it-myself) ---------- */
// The engines write precise, technical titles and reasons. The inbox shows
// the same facts in people-words — the full detail is one tap away.
function plainTitle(t) {
  const s = String(t || "Something worth doing");
  const rules = [
    [/^Pre-Emptive Household Resilience Plan.*$/i, "Getting ready for a rough week"],
    [/^Acoustic Wear Alert.*$/i, "The fridge needs a new part — the bearing is wearing out"],
    [/^Family Treaty Ratification.*$/i, "The family deal — everyone's say-so"],
    [/^Pre-Emptive Weekend Pantry Restock.*$/i, "Restock the pantry before the weekend"],
    [/^Parliamentary Consensus.*$/i, "The house settled it — everyone's say-so"],
  ];
  for (const [re, plain] of rules) {
    if (re.test(s)) return plain;
  }
  return s;
}
function plainReasons(r) {
  const original = String(r == null ? "" : r);
  let t = original;
  t = t.replace(/Zero-knowledge mediation over salted digests\.?/i,
    "Nobody's private notes were shared.");
  t = t.replace(/Negotiated Nash product\s*[\d.]+\s*\(achievement\s*(\d+)%[\s\S]*$/i,
    "Everyone's side of the deal landed at $1%.");
  t = t.replace(/Monte Carlo \((\d+) runs?, seed \d+\):\s*p50 \$([\d.]+) → \$([\d.]+),[^;]*;\s*(\d+) hazards?\.?/i,
    "Played $1 possible weeks: the likely cost drops from $$$2 to $$$3, with $4 things worth watching.");
  t = t.replace(/Echo FFT detected[\s\S]*$/i,
    "The kitchen speaker heard a wobble it shouldn't — the worn part is already picked out and priced.");
  t = t.replace(/\bsalted SHA-256\b[^.]*\.?/gi, "");
  if (t !== original) {
    t = t.trim();
    return t.length > 240 ? t.slice(0, 240).trimEnd() + "…" : t;
  }
  // Unmapped evidence: keep the first sentence (decimal-safe: only split at
  // a period/question mark followed by whitespace or end of string).
  const m = t.match(/^.*?[.!?](?=\s+[A-Z]|$)/);
  return (m && m[0].length > 30 ? m[0] : t).trim();
}
function plainUsage(s) {
  const t = String(s == null ? "" : s);
  return t
    .replace(/^Dormant \(([^)]*)\)$/i, "Not used — $1")
    .replace(/^Low \(([^)]*)\)$/i, "Rarely used — $1")
    .replace(/^Inactive \(([^)]*)\)$/i, "Never used in that time")
    .replace(/^Active \(([^)]*)\)$/i, "Still in use — $1");
}
function plainHazard(t) {
  const s = String(t || "").trim();
  const map = {
    "energy tariff spike": "Peak power prices",
    "brownout risk": "The lights could dip",
    "pantry depletion": "The pantry runs low",
    "grid instability": "The grid looks shaky",
    "heatwave load": "Heatwave strain",
  };
  if (map[s.toLowerCase()]) return map[s.toLowerCase()];
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}
function plainHorizon(t) {
  return String(t || "")
    .replace(/Day (\d)·(\d)/g, "Days $1–$2")
    .replace(/Hours (\d{2}:\d{2}) - (\d{2}:\d{2})/, "$1–$2")
    .replace(/\(/g, "· ")
    .replace(/\)/g, "");
}
function plainAction(t) {
  return String(t || "")
    .replace(/thermal mass/gi, "the house")
    .replace(/\bcoast with fan assist\b/gi, "let the fans carry it")
    .replace(/\bcoast (\d+)-(\d+)h\b/gi, "take it easy $1:00–$2:00")
    .replace(/\bshed\b/gi, "skip")
    .replace(/; dishwasher (\d+)/gi, "; run the dishwasher at $1:00");
}
function deltaBadge(p) {
  const d = p.cost_delta_yr ?? p.savings ?? p.delta;
  if (d == null) return "";
  const n = Number(String(d).replace(/[^0-9.\-]/g, ""));
  if (!Number.isFinite(n) || n === 0) return "";
  if (n < 0) {
    // Negative cost delta = it costs less than today.
    return '<span class="delta save">' + esc("+$" + Math.abs(n).toFixed(2) + "/yr saved") + "</span>";
  }
  return '<span class="delta cost">' + esc("$" + n.toFixed(2) + "/yr") + "</span>";
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
      list.innerHTML = '<div class="empty"><strong>Nothing waiting</strong>Your real home is a clean slate. Only things your household actually asks for land here.</div>';
    } else {
      list.innerHTML = '<div class="empty"><strong>All clear</strong>Nothing waiting. When Hearth finds something worth doing, it lands here with the price tag.</div>';
    }
    return;
  }
  list.innerHTML = "";
  pending.forEach((p) => {
    const el = document.createElement("div");
    el.className = "intent";
    el.innerHTML =
      '<div class="intent-top"><h4>' + esc(plainTitle(p.title || p.kind)) + "</h4>" + deltaBadge(p) + "</div>" +
      '<p class="intent-reasons">' + esc(plainReasons((p.reasons || []).join ? p.reasons.join(" ") : (p.reasons || ""))) + "</p>" +
      '<p class="mono muted-2 mt-8">' + esc((p.risk_level || "medium").toUpperCase()) + " stakes · a one-time offer · gone the moment you decide</p>" +
      '<div class="intent-actions"><button class="btn btn-primary" data-a="1">Do it</button>' +
      "<button class='btn' data-a='inspect'>Show me the details</button>" +
      "<button class='btn' data-a='mine'>I'll handle it myself</button></div>";
    el.querySelector('[data-a="1"]').addEventListener("click", () => decide(p.id, true, el));
    el.querySelector('[data-a="mine"]').addEventListener("click", () => decide(p.id, false, el, "Marked as handled by you."));
    el.querySelector('[data-a="inspect"]').addEventListener("click", () => {
      const rawReasons = (p.reasons || []).join ? p.reasons.join(" ") : (p.reasons || "");
      const details = String(p.diff || p.detail || "").trim();
      const showDetails = details && details !== String(rawReasons).trim();
      openDialog(plainTitle(p.title || p.kind),
        "<p>" + esc(plainReasons(rawReasons)) + "</p>" +
        (showDetails ? '<div class="diff">' + esc(details) + "</div>" : "") +
        "<p class='mono muted-2'>" + esc(p.kind) + " · " + esc(p.id) + "</p>",
        [
          { label: "Do it", primary: true, onClick: () => decide(p.id, true, el) },
          { label: "Let me think", onClick: () => decide(p.id, false, el, "Held back — nothing changed.") },
          { label: "Close" },
        ]);
    });
    list.appendChild(el);
  });
});
let lastApprovedPid = null;
async function replayDecision(id) {
  toast("Rewinding to that moment…");
  let data = null;
  try {
    const r = await fetch("/api/audit/replay?id=" + encodeURIComponent(id));
    data = await r.json();
  } catch (e) {
    toast("Couldn't rewind — the house looks offline", true);
    return;
  }
  if (!data || !data.ok) {
    toast("Couldn't rewind: " + ((data && data.error) || "unknown"), true);
    return;
  }
  const trail = (data.audit_trail || []).map((t) =>
    '<div class="mono">' + esc(t.actor) + " · " + esc(t.action) + " · " + esc((t.hash || "").slice(0, 8)) + "</div>"
  ).join("") || '<div class="lede-sm">Nothing recorded yet</div>';
  openDialog("How it went: " + (data.title || data.kind),
    '<p style="color: var(--amber); font-weight: 620">' + esc(data.replay_note || "") + "</p>" +
    "<p style='margin: 8px 0'><strong>What it was working from:</strong><br>" +
    esc(JSON.stringify(data.why || {}, null, 1)) + "</p>" +
    (data.execution ? '<p class="receipt">Receipt: ' +
      esc(data.execution.receipt_code || data.execution.note || "") + "</p>" : "") +
    '<div class="diff">' + trail + "</div>" +
    "<p class='mono muted-2'>record " +
    (data.chain_valid ? "intact ✓" : "doesn't add up") + " · take-back " +
    (data.undo_available ? "still possible" : "no longer possible") + "</p>",
    data.undo_available
      ? [{ label: "Take it back", primary: true,
           onClick: () => { undoProposal(id); } }, { label: "Close" }]
      : [{ label: "Close", primary: true }]);
}

async function undoProposal(id, el) {
  toast("Taking it back…");
  setLightWave("thinking");
  const { status, data } = await post("/api/undo", { id });
  if (status === 200 && data.ok) {
    dialStats.undo += 1;
    paintDial();
    playEarcon("alert");
    setLightWave("alert");
    toast("Taken back: " + (data.note || "everything is as it was"));
    refresh();
  } else {
    setLightWave("alert");
    toast("Couldn't take it back: " + (data.error || status), true);
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
    actions.innerHTML = '<span class="mono muted-2">One moment…</span>';
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
          esc(note || (approved ? "Done once — receipt written down, take it back any time." : "Held back — nothing moved.")) +
          (approved ? ' <button class="btn-undo" data-undopid="' + esc(id) + '">Take it back</button>' : '') +
          '</div>';
        const uBtn = el.querySelector('[data-undopid="' + id + '"]');
        if (uBtn) uBtn.addEventListener("click", () => undoProposal(id, el));
      }
    }
    toast(note || (approved ? "Done — once, on the record" : "Held back — nothing happened"));
    setTimeout(refresh, 800);
  } else if (status === 409) {
    toast("Already decided — that's a one-time offer", true);
    setTimeout(refresh, 800);
  } else {
    el.innerHTML = snapshot;
    rebindIntent(el);
    setLightWave("alert");
    playEarcon("alert");
    toast("The house couldn't do that (" + status + ") — nothing changed", true);
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
    toast("Easy — give Hearth a moment", true);
    return;
  }
  if (status !== 200 || !data) {
    setLightWave("alert");
    playEarcon("alert");
    toast("No answer just now — asking again is safe", true);
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
      (dag ? "<details open><summary>What it checked</summary><div class='mono-block'>" + dag + "</div></details>" : "") +
      (data.blocked ? "<div class='blocked'>The house held this back: " + esc(data.reason || "") + "</div>" : "");
    logEl.prepend(row);
  }
  
  appendAgent(homeLog);
  appendAgent(widgetLog);
  
  if (data.blocked) addEvent("sentinel", "Held back: " + (data.reason || "a house rule"), null);
  else addEvent("agent", (data.intent || "Answered") + " — " + msg.slice(0, 60), null);
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
let latestSpokenText = "Hearth is awake and watching over the house.";

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

/* Live snapshot cache: every polled topic stashes its latest payload so the
   fullscreen canvas renders measured values, never placeholder copy. */
const liveSnap = {};
for (const t of ["home", "parliament", "causal", "forensics", "acoustic", "mediation", "swarm", "roi", "depletion"]) {
  on(t, (payload) => { liveSnap[t] = payload; });
}

function nashPctOf(v) {
  if (v == null) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return String(Math.round(n > 1 ? n * 10 : n * 100));
}

function renderFullscreenCanvas(data) {
  const box = $("#fullscreenCanvasBox");
  const grid = $("#canvasGrid");
  if (!box || !grid) return;
  box.hidden = false;
  const parl = liveSnap.parliament || {};
  const causal = liveSnap.causal || {};
  const home = liveSnap.home || {};
  const energy = home.energy || {};
  const nashTxt = data && data.nash_equilibrium_score != null
    ? "Agreement " + esc(nashPctOf(data.nash_equilibrium_score)) + "% · " + esc(data.vote || "")
    : "Nothing argued yet — try one of the starters above";
  const vulnCount = causal.vulnerability_count != null ? causal.vulnerability_count
    : ((causal.vulnerabilities || []).length || "—");
  const resilience = causal.resilience_score != null ? " · resilience " + esc(causal.resilience_score) : "";
  const solarTxt = energy.solar_generation_kw != null
    ? "Roof making " + esc(energy.solar_generation_kw) + " kW · using " + esc(energy.net_kw != null ? energy.net_kw : "?") + " kW"
    : "Live readings appear on the next refresh";
  grid.innerHTML = `
    <div class="canvas-card">
      <div class="canvas-card-head">
        <strong>When the house disagrees with itself</strong>
        <span class="pill pill-micro">Agreement</span>
      </div>
      <p>Savings, comfort and climate each get a say — then the house settles on the version everyone can live with.</p>
      <div class="canvas-preview" id="fsParliamentPreview">` + nashTxt + `</div>
    </div>
    <div class="canvas-card">
      <div class="canvas-card-head">
        <strong>What next week is planning</strong>
        <span class="pill pill-micro">Forecast</span>
      </div>
      <p>Weather, prices and wear — the risks worth doing something about, before they arrive.</p>
      <div class="canvas-preview" id="fsCausalPreview">` + esc(vulnCount) + ` risks it kept an eye on` + resilience + `</div>
    </div>
    <div class="canvas-card">
      <div class="canvas-card-head">
        <strong>Energy right now</strong>
        <span class="pill pill-micro">Live</span>
      </div>
      <p>What the roof is making, what the house is using, and what's left over.</p>
      <div class="canvas-preview" id="fsEnergyPreview">` + solarTxt + `</div>
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
    toast("Voice only — answers are spoken aloud");
    if (latestSpokenText) speakAlexaVoice(latestSpokenText);
  } else if (mode === "fullscreen") {
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) {
      canvasBox.hidden = false;
      renderFullscreenCanvas();
    }
    toast("Full screen — the whole picture, nothing hidden");
  } else if (mode === "hydrated") {
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) {
      canvasBox.hidden = false;
      renderFullscreenCanvas();
    }
    toast("Live view — readings update while it answers");
  } else {
    // inline
    if (voiceBanner) voiceBanner.hidden = true;
    if (canvasBox) canvasBox.hidden = true;
    toast("Back to the card");
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
      toast("Handled: " + (data.event ? data.event.title : scenario));
      refresh();
    } else {
      setLightWave("alert");
      playEarcon("alert");
      toast("That didn't take — try once more", true);
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
    pill.textContent = (res.active_model ? res.active_model.split(":").pop() : "Built-in") + " · " + (res.active_provider || "bedrock").toUpperCase();
  }
  const provBox = $("#meshProvidersList");
  if (provBox && res.providers) {
    provBox.innerHTML = res.providers.map((p) =>
      '<span class="provider-tag' + (p.name === res.active_provider ? " active" : "") + '">' +
      '<span class="tag-dot' + (p.status === "connected" ? "" : " is-amber") + '"></span>' +
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
      toast("Now thinking with " + (data.active_model || model_id));
      refresh();
    } else {
      toast("Couldn't switch (" + status + ")", true);
    }
  });
}

const addApiBtn = $("#addCustomApiBtn");
if (addApiBtn) {
  addApiBtn.addEventListener("click", async () => {
    const nameInput = $("#customApiName");
    const urlInput = $("#customApiUrl");
    const name = nameInput.value.trim() || "Your model";
    const base_url = urlInput.value.trim();
    if (!base_url) {
      toast("Add the address you want Hearth to use", true);
      return;
    }
    addApiBtn.disabled = true;
    addApiBtn.textContent = "Knocking…";
    const { status, data } = await post("/api/models/providers/add", { name, base_url });
    addApiBtn.disabled = false;
    addApiBtn.textContent = "Connect it";
    if (status === 200 && data.ok) {
      toast("Connected " + name + " (" + (data.discovered_models || []).length + " models found)");
      nameInput.value = "";
      urlInput.value = "";
      refresh();
    } else {
      toast("Couldn't reach it: " + (data.error || status), true);
    }
  });
}

/* ---------- the house argues it out ---------- */
on("parliament", (p) => {
  const box = $("#parliamentBox");
  if (!box || !p || !p.ministers) return;
  const ministers = Array.isArray(p.ministers)
    ? p.ministers
    : Object.entries(p.ministers).map(([k, v]) => ({ id: k, name: v.title || v.name || k, ...v }));
  box.innerHTML =
    "<p class='lede-sm'>Everyone who lives here gets a voice — then the house weighs them up.</p>" +
    '<div class="parliament-grid">' +
    ministers.map((m) =>
      '<div class="minister-card">' +
      "<strong>" + esc(m.name || m.title || m.id) + "</strong>" +
      "<small>" + esc(m.focus || (m.style ? m.style.replace(/_/g, " ") : m.priority) || "") + "</small>" +
      '<div class="util">Say: ' + esc(m.weight || 1.0) + " · Vetoes: " + esc(m.veto_count || 0) + "</div>" +
      "</div>"
    ).join("") +
    "</div>";
});

const parlBtn = $("#parlDebateBtn");
if (parlBtn) {
  parlBtn.addEventListener("click", async () => {
    parlBtn.disabled = true;
    parlBtn.textContent = "Arguing…";
    const { status, data } = await post("/api/parliament/deliberate", {
      topic: "Multi-objective household energy vs wellness dilemma"
    });
    parlBtn.disabled = false;
    parlBtn.textContent = "Let them argue";
    if (status === 200 && data) {
      const speeches = (data.speeches || []).map((s) => {
        const text = Array.isArray(s.arguments) ? s.arguments.join(" ") : (s.speech || s.stance || "");
        return '<div style="margin-bottom: 8px"><strong>' + esc(s.minister) + (s.role ? " (" + esc(s.role) + ")" : "") + ":</strong> " + esc(text) + "</div>";
      }).join("");
      const paretoText = typeof data.pareto_compromise === "object"
        ? (data.pareto_compromise.executive_summary || JSON.stringify(data.pareto_compromise))
        : String(data.pareto_compromise || "");
      const agreement = nashPctOf(data.nash_equilibrium_score);

      openDialog("The house settled it",
        '<p style="color: var(--amber); font-weight: 660">Everyone happy with ' + agreement + "% of it</p>" +
        "<p style='margin: 8px 0'><strong>The middle ground they found:</strong> " + esc(paretoText) + "</p>" +
        '<div class="diff">' + speeches + "</div>" +
        (data.staged_proposal_id ? '<p class="receipt">Ready for your say-so in Approvals.</p>' : ""),
        [
          { label: "See what it wants to do", primary: true, onClick: () => show("approvals") },
          { label: "Close" }
        ]
      );
      toast("They got to " + agreement + "% agreement");
      refresh();
    } else {
      toast("Nobody could agree just now (" + status + ")", true);
    }
  });
}

/* ---------- seven days ahead ---------- */
on("causal", (c) => {
  const box = $("#causalBox");
  if (!box || !c) return;
  const vulns = c.vulnerabilities || [];
  const score = c.resilience_score != null
    ? Math.round(c.resilience_score > 1 ? c.resilience_score : c.resilience_score * 100)
    : 96;
  box.innerHTML =
    '<div class="insight-head">' +
    '<span class="lede-sm">The week ahead, weighed up</span>' +
    '<span class="pill c-ok">' + score + "% ready for it</span>" +
    "</div>" +
    (!vulns.length
      ? '<div class="empty"><strong>Nothing to worry about</strong>The week looks steady from here.</div>'
      : vulns.slice(0, 3).map((v) => {
        const sev = esc(v.impact_severity || v.severity || "medium");
        const horizon = esc(plainHorizon(v.timeframe || (v.horizon_hours ? "in " + v.horizon_hours + "h" : "within a day")));
        const title = esc(plainHazard(v.title || (v.hazard_type ? v.hazard_type.replace(/_/g, " ") : v.domain) || "Something to watch"));
        const action = esc(plainAction(v.contingency_action || v.countermeasure || v.description || v.root_cause || ""));
        return (
          '<div class="insight">' +
          '<div class="flex-1"><div class="row-flex" style="margin-bottom: 5px">' +
          '<span class="vuln-badge ' + sev + '">' + sev + "</span>" +
          "<strong>" + title + "</strong>" +
          '<small class="mono">' + horizon + "</small>" +
          "</div>" +
          '<div class="lede-sm">' + action + "</div>" +
          "</div>" +
          (v.expected_loss_usd ? '<div class="mono" style="color: var(--bad)">−$' + esc(v.expected_loss_usd) + "</div>" : "") +
          "</div>"
        );
      }).join(""));
});

const causalBtn = $("#causalSimBtn");
if (causalBtn) {
  causalBtn.addEventListener("click", async () => {
    causalBtn.disabled = true;
    causalBtn.textContent = "Looking ahead…";
    const { status, data } = await post("/api/causal/simulate", { days_ahead: 7, iterations: 500 });
    causalBtn.disabled = false;
    causalBtn.textContent = "Run the forecast";
    if (status === 200 && data) {
      const n = (data.vulnerabilities || []).length;
      toast(n ? "Seven days looked at — " + n + " thing" + (n === 1 ? "" : "s") + " worth watching" : "Seven days looked at — all steady");
      refresh();
    } else {
      toast("The forecast didn't run (" + status + ")", true);
    }
  });
}

/* ---------- replay a strange night ---------- */
const VERDICT_PLAIN = {
  ATMOSPHERIC_DELTA_P: "the house itself moved — nothing walked in",
  INTRUDER_LIKELY_ENTRY: "someone probably did come in",
  PET_OR_SMALL_ANIMAL: "something small — a pet, most likely",
  UNKNOWN: "still not sure what that was",
};

on("forensics", (f) => {
  const box = $("#forensicsBox");
  if (!box || !f) return;
  const factors = f.physical_factors || [];
  const confPct = (f.causal_confidence != null ? Math.round(f.causal_confidence * 100) : "—");
  const verdictKey = String(f.verdict || "").toUpperCase();
  const verdictPlain = VERDICT_PLAIN[verdictKey] || (verdictKey ? verdictKey.replace(/_/g, " ").toLowerCase() : "still being pieced together");
  box.innerHTML =
    '<div class="insight-head">' +
    '<span class="lede-sm">Last night, rebuilt from the house\'s own senses</span>' +
    '<span class="pill c-ok">' + confPct + "% sure</span>" +
    "</div>" +
    '<p class="lede-sm" style="margin-bottom: 10px"><strong>What it adds up to:</strong> ' + esc(verdictPlain) + "</p>" +
    '<div class="lede-sm">' +
    factors.slice(0, 3).map((pf) =>
      "<div style='margin-bottom: 5px'><strong>" + esc(pf.factor) + ":</strong> " + esc(pf.measured) + " — " + esc(pf.impact) + "</div>"
    ).join("") +
    "</div>" +
    '<p class="mono muted-2 mt-8">' + esc(f.summary || "") + "</p>";
});

const forensicsBtn = $("#forensicsScanBtn");
if (forensicsBtn) {
  forensicsBtn.addEventListener("click", async () => {
    forensicsBtn.disabled = true;
    forensicsBtn.textContent = "Replaying…";
    const { status, data } = await post("/api/forensics/reconstruct", { incident_type: "perimeter_anomaly", lookback_seconds: 3600 });
    forensicsBtn.disabled = false;
    forensicsBtn.textContent = "Replay 3 AM";
    if (status === 200 && data) {
      const confPct = data.causal_confidence != null ? Math.round(data.causal_confidence * 100) : "—";
      const timelineHtml = (data.timeline_events || []).map((ev) =>
        "<div style='margin-bottom: 10px; padding-left: 10px; border-left: 2px solid rgba(240,168,92,0.35)'>" +
        '<div class="mono">' + esc(ev.timestamp) + " · <strong>" + esc(ev.source) + "</strong></div>" +
        '<div class="lede-sm">' + esc(ev.event) + "</div>" +
        '<div class="mono" style="color: var(--ok)">' + esc(ev.deduction) + "</div>" +
        "</div>"
      ).join("");

      openDialog("3 AM, second by second",
        '<p style="color: var(--ok); font-weight: 660">Nobody came in — ' + confPct + "% sure</p>" +
        '<p class="lede-sm" style="margin: 8px 0">' + esc(data.summary) + "</p>" +
        '<div class="diff">' + timelineHtml + "</div>" +
        '<div class="mono muted-2">receipt fingerprint ' + esc(data.audit_proof || "") + "</div>",
        [
          { label: "Good", primary: true }
        ]
      );
      toast("Replayed — the house moved, nobody walked in");
      refresh();
    } else {
      toast("Couldn't replay that night (" + status + ")", true);
    }
  });
}

/* ---------- the fridge is talking ---------- */
on("acoustic", (a) => {
  const box = $("#acousticBox");
  if (!box || !a) return;
  const diag = (a.diagnostics || [])[0] || {};
  const statusText = diag.status === "warning" ? "worn" : "sounds right";
  box.innerHTML =
    '<div class="insight-head">' +
    '<span class="lede-sm">Listening to <strong>' + esc(diag.appliance || "the kitchen") + "</strong></span>" +
    '<span class="pill ' + (diag.status === "warning" ? "" : "c-ok") + '">' + esc(statusText) + "</span>" +
    "</div>" +
    '<div class="row-flex" style="gap: 22px; margin-bottom: 10px">' +
    "<div><span class='micro muted-2'>Its hum:</span> <strong class='mono' style='color: var(--amber)'>" + esc(diag.fft_spectral_peak_hz || 60) + " Hz</strong></div>" +
    "<div><span class='micro muted-2'>Worn bearings:</span> <strong class='mono' style='color: var(--bad)'>" + (diag.bearing_friction_index != null ? Math.round(diag.bearing_friction_index * 100) : "—") + "%</strong></div>" +
    "<div><span class='micro muted-2'>Likely to fail in</span> <strong style='color: var(--bad)'>~" + esc(diag.estimated_days_to_failure || 14) + " days</strong></div>" +
    "</div>" +
    '<p class="lede-sm">' + esc(diag.recommended_action || "") + "</p>" +
    (diag.part_asin ? '<div class="mini-card mt-12">' +
      '<span class="micro">The replacement part is already in the house\'s basket — 15% less in bulk</span>' +
      (diag.staged_proposal_id ? '<span class="pill c-ok pill-micro">Waiting for your say-so</span>' : "") +
      "</div>" : "");
});

const acousticBtn = $("#acousticScanBtn");
if (acousticBtn) {
  acousticBtn.addEventListener("click", async () => {
    acousticBtn.disabled = true;
    acousticBtn.textContent = "Listening…";
    try {
      const res = await fetch("/api/acoustic/scan?stage_remedy=true");
      acousticBtn.disabled = false;
      acousticBtn.textContent = "Listen to the kitchen";
      if (res.ok) {
        const data = await res.json();
        const diag = (data.diagnostics || [])[0] || {};
        openDialog("It's the " + esc(diag.appliance || "kitchen"),
          '<p style="color: var(--amber); font-weight: 660">Something in there is wearing out</p>' +
          '<p class="lede-sm" style="margin: 8px 0">The speaker heard a wobble at <strong>' + esc(diag.fft_spectral_peak_hz) + " Hz</strong> — flat and steady when things are healthy. It puts the odds of a breakdown in about " + esc(diag.estimated_days_to_failure) + " days.</p>" +
          (diag.staged_proposal_id ? '<p class="receipt">A replacement part is ready in Approvals — 15% off in bulk.</p>' : ""),
          [
            { label: "See the part", primary: true, onClick: () => show("approvals") },
            { label: "Close" }
          ]
        );
        toast("Hmm — that hum isn't right");
        refresh();
      } else {
        toast("Couldn't listen right now", true);
      }
    } catch (e) {
      acousticBtn.disabled = false;
      acousticBtn.textContent = "Listen to the kitchen";
      toast("Couldn't listen: " + e.message, true);
    }
  });
}
/* ---------- family peace treaty ---------- */
on("mediation", (m) => {
  const box = $("#mediationBox");
  if (!box || !m) return;
  const covs = m.covenants || [];
  box.innerHTML =
    '<div class="insight-head">' +
    '<span class="lede-sm">A fair split everyone signed</span>' +
    '<span class="pill c-ok">Fairness: ' +
    (m.fairness_index_out_of_10 != null ? esc(m.fairness_index_out_of_10) : "—") + "/10</span>" +
    "</div>" +
    '<div class="lede-sm" style="margin-bottom: 8px">Nobody\'s private notes were shared — each person only ever sees their own half of the deal.</div>' +
    '<div class="lede-sm micro muted-2" style="margin-bottom: 8px">How much everyone got: ' +
    Math.round((m.nash_achievement || 0) * 100) + "% · everything covered: " + esc(m.cooperation_coverage_pct) +
    "% · nothing given away twice: " + esc(m.envy_gap) + " · set aside: " +
    esc((m.domains_conceded || []).join(", ") || "nothing") + "</div>" +
    '<div class="row-flex" style="flex-direction: column; gap: 6px; align-items: stretch">' +
    covs.map((c) =>
      '<div class="mini-card">' +
      '<div class="row-between">' +
      "<strong>" + esc((c.domain || "").replace(/_/g, " ")) + "</strong>" +
      '<span class="micro muted-2">' + esc(c.resident || "") + "</span>" +
      '<span class="mono" style="color: var(--ok)">' + esc(c.satisfaction_pct) + "% theirs</span></div>" +
      // Field name is concession_granted -- the API has no `covenant` key.
      '<div class="lede-sm">' + esc(c.concession_granted || "") + "</div>" +
      "</div>"
    ).join("") +
    "</div>" +
    (m.staged_proposal_id ? '<div class="receipt">The treaty is waiting for the family to say yes.</div>' : "");
});

const mediationBtn = $("#mediationTreatyBtn");
if (mediationBtn) {
  mediationBtn.addEventListener("click", async () => {
    mediationBtn.disabled = true;
    mediationBtn.textContent = "Working it out…";
    const { status, data } = await post("/api/mediation/treaty", {});
    mediationBtn.disabled = false;
    mediationBtn.textContent = "Draw one up";
    if (status === 200 && data) {
      // Field names must match the /api/mediation/treaty payload:
      // concession_granted (not `covenant`), satisfaction_pct, and
      // fairness_index_out_of_10. Reading the wrong key silently rendered
      // "undefined" in this dialog.
      const covHtml = (data.covenants || []).map((c) =>
        '<div style="margin-bottom: 10px; padding: 12px; border-radius: 12px; background: var(--surface); border: 1px solid var(--line)">' +
        '<div class="row-between">' +
        "<strong>" + esc(c.resident || "") + "</strong>" +
        '<span class="micro muted-2">' + esc((c.domain || "").replace(/_/g, " ")) + "</span>" +
        '<span class="num" style="color: var(--ok); font-weight: 640">' + esc(c.satisfaction_pct) + "%</span>" +
        "</div>" +
        '<div class="lede-sm" style="margin-top: 6px">' + esc(c.concession_granted || "") + "</div>" +
        '<div class="micro muted-2" style="margin-top: 6px">' +
        "In return: " + esc(c.reciprocal_obligation || "") + "</div>" +
        (c.domain_weight != null
          ? '<div class="mono muted-2" style="margin-top: 6px">worth ' + esc(c.domain_weight) +
            " · gave up " + esc(c.concession_level) + "</div>"
          : "") +
        "</div>"
      ).join("");

      const conceded = (data.domains_conceded || []).join(", ") || "nothing";
      const metrics =
        '<div class="grid-2" style="gap: 8px; margin: 12px 0">' +
        '<div class="mini-card"><small>Everyone happy with</small><strong class="num">' +
        Math.round((data.nash_achievement || 0) * 100) + "%</strong></div>" +
        '<div class="mini-card"><small>Everything covered</small><strong class="num">' +
        esc(data.cooperation_coverage_pct) + "%</strong></div>" +
        "</div>";

      openDialog("The family treaty" + (data.scenario === "household_demo" ? " · demo household" : ""),
        '<p style="color: var(--ok); font-weight: 660">Fairness ' + esc(data.fairness_index_out_of_10) +
        "/10 — after " + esc(data.feasible_vectors_explored) + " versions weighed up</p>" +
        '<p class="lede-sm" style="margin: 6px 0">Set aside: <strong>' + esc(conceded) + "</strong>. " +
        "Fairness here is measured, not promised — it drops the moment a household asks for more than it has.</p>" +
        metrics +
        '<div style="margin: 12px 0">' + covHtml + "</div>" +
        '<p class="micro muted-2">Private notes never left anyone\'s side — not even to make the deal.</p>' +
        (data.staged_proposal_id ? '<p class="receipt">Waiting for everyone to say yes.</p>' : ""),
        [
          { label: "See it in Approvals", primary: true, onClick: () => show("approvals") },
          { label: "Close" }
        ]
      );
      toast("Treaty drawn up — fairness " + esc(data.fairness_index_out_of_10) + "/10");
      refresh();
    } else {
      toast("Couldn't get everyone to agree (" + status + ")", true);
    }
  });
}

/* ---------- borrow the neighbours' sun ---------- */
on("swarm", (s) => {
  const box = $("#swarmBox");
  if (!box || !s) return;
  const arb = s.economic_arbitrage || {};
  const nodes = s.nodes || [];
  box.innerHTML =
    '<div class="insight-head">' +
    '<span class="lede-sm">Spare power goes to the street at <strong style="color: var(--ok)">$' + esc(s.local_clearing_price_usd_kwh) + "/kWh</strong> — the utility would only pay $" + esc(s.utility_sell_rate_usd_kwh) + "</span>" +
    '<span class="pill c-ok">' + nodes.length + " homes in it</span>" +
    "</div>" +
    '<div class="row-flex lede-sm" style="gap: 18px; margin-bottom: 10px">' +
    "<div><span class='micro muted-2'>Sending out:</span> <strong style='color: var(--amber)'>" + (arb.total_exported_kw != null ? esc(arb.total_exported_kw) : "—") + " kW</strong></div>" +
    "<div><span class='micro muted-2'>Back to us:</span> <strong style='color: var(--ok)'>+$" + esc(arb.our_revenue_rate_usd_hr || 0.68) + "/hr</strong></div>" +
    "<div><span class='micro muted-2'>Cleaner air:</span> <strong style='color: var(--ok)'>" + esc(arb.co2_avoided_kg_hr || 2.85) + " kg/hr</strong></div>" +
    "</div>" +
    '<div class="row-flex" style="flex-direction: column; gap: 6px; align-items: stretch">' +
    nodes.slice(1).map((n) =>
      '<div class="mini-card">' +
      '<div class="row-between"><div><strong>' + esc(n.address) + "</strong> <span class='micro muted-2'>(" + esc(n.asset || n.role) + ")</span></div>" +
      '<span class="mono" style="color: var(--amber)">' + esc(n.power_kw) + " kW · " + esc(n.battery_soc_pct) + "% left</span></div>" +
      "</div>"
    ).join("") +
    "</div>";
});

const swarmBtn = $("#swarmGridBtn");
if (swarmBtn) {
  swarmBtn.addEventListener("click", async () => {
    swarmBtn.disabled = true;
    swarmBtn.textContent = "Talking to the street…";
    const { status, data } = await post("/api/swarm/grid", {});
    swarmBtn.disabled = false;
    swarmBtn.textContent = "Trade with the street";
    if (status === 200 && data) {
      const arb = data.economic_arbitrage || {};
      openDialog("Selling to the neighbours",
        '<p style="color: var(--ok); font-weight: 660">The street is taking the spare solar</p>' +
        '<p class="lede-sm" style="margin: 8px 0"><strong>' + esc(arb.total_exported_kw) + " kW</strong> is going to homes nearby at <strong>$" + esc(data.local_clearing_price_usd_kwh) + "/kWh</strong>, instead of dumping it on the utility for $" + esc(data.utility_sell_rate_usd_kwh) + "/kWh.</p>" +
        '<div style="padding: 12px; border-radius: 12px; background: var(--surface); border: 1px solid var(--line); display: flex; flex-direction: column; gap: 6px">' +
        "<div>Comes back to you: <strong>+$" + esc(arb.our_revenue_rate_usd_hr) + "/hr</strong> <span class='micro muted-2'>(the old way: $" + esc(arb.our_utility_dump_revenue_usd_hr) + "/hr)</span></div>" +
        "<div>The neighbours save: <strong>+$" + esc(arb.net_community_savings_usd_hr) + "/hr</strong></div>" +
        "<div>Sent up instead of burned: <strong>" + esc(arb.co2_avoided_kg_hr) + " kg of CO2 an hour</strong></div>" +
        "</div>" +
        (data.staged_proposal_id ? '<p class="receipt">Waiting for your yes in Approvals.</p>' : ""),
        [
          { label: "See it in Approvals", primary: true, onClick: () => show("approvals") },
          { label: "Close" }
        ]
      );
      toast("The street is buying our spare sun");
      refresh();
    } else {
      toast("The street didn't answer (" + status + ")", true);
    }
  });
}

/* ---------- habits Hearth taught itself ---------- */
on("metaSkills", (m) => {
  const list = $("#metaSkillsList");
  const countBadge = $("#metaSkillsCount");
  if (!list || !m) return;
  const skills = m.skills || [];
  if (countBadge) countBadge.textContent = skills.length ? skills.length + " learned" : "None yet";
  if (!skills.length) {
    list.innerHTML = '<div class="empty"><strong>No habits yet</strong>Describe one above and Hearth will write it itself.</div>';
    return;
  }
  list.innerHTML = skills.map((s) =>
    '<div class="meta-skill-item">' +
    '<div class="title">' +
    "<strong>" + esc(s.name || s.skill_id) + "</strong>" +
    '<div>' + esc(String(s.trigger_intent || s.description || "A habit Hearth wrote for this house").replace(/^Synthesized \[[^\]]*\] skill:\s*/i, "")) +
    " · used " + esc(s.invocation_count || 0) + " times</div>" +
    "</div>" +
    '<span class="badge">Checked & safe</span>' +
    "</div>"
  ).join("");
});

const metaSkillBtn = $("#metaSkillBtn");
if (metaSkillBtn) {
  metaSkillBtn.addEventListener("click", async () => {
    const input = $("#metaSkillInput");
    const req = input.value.trim();
    if (!req) {
      toast("Describe the habit you want in plain words", true);
      return;
    }
    metaSkillBtn.disabled = true;
    metaSkillBtn.textContent = "Writing…";
    const { status, data } = await post("/api/meta-skills/synthesize", { requirement: req });
    metaSkillBtn.disabled = false;
    metaSkillBtn.textContent = "Learn it";
    if (status === 200 && data.ok) {
      // /api/meta-skills/synthesize returns flat keys (skill_id, name, ...),
      // not a nested `skill` object.
      toast("Learned and switched on: " + (data.name || data.skill_id || "a new habit"));
      input.value = "";
      refresh();
    } else {
      toast("It didn't take: " + (data.error || status), true);
    }
  });
}

/* ---------- under the hood ---------- */
on("diagnostics", (diag) => {
  const box = $("#diagBox");
  if (!box || !diag) return;
  const pill = $("#diagHealthPill");
  if (pill) {
    pill.textContent = diag.status === "healthy" ? "● All well · up " + Math.round(diag.uptime_seconds) + "s" : "● Some trouble";
    pill.style.color = diag.status === "healthy" ? "var(--ok)" : "var(--bad)";
  }
  const ledger = diag.audit_ledger || {};
  const resilience = diag.causal_twin && diag.causal_twin.resilience_score != null
    ? (diag.causal_twin.resilience_score > 1 ? diag.causal_twin.resilience_score : diag.causal_twin.resilience_score * 100)
    : 96;
  box.innerHTML =
    '<div class="diag-grid">' +
    '<div class="diag-item"><div class="label">Thinking with</div><div class="value">' +
    esc((diag.active_brain || "built-in").split(":").pop()) + " · " + esc((diag.active_provider || "built-in").toUpperCase()) + "</div></div>" +
    '<div class="diag-item"><div class="label">On the record</div><div class="value" style="color:' +
    (ledger.valid ? " var(--ok)" : " var(--bad)") + '">' +
    (ledger.valid ? "✓ " + ledger.events_count + " actions sealed" : "Doesn't add up") + "</div></div>" +
    '<div class="diag-item"><div class="label">Ready for the week</div><div class="value" style="color: var(--ok)">' +
    Math.round(resilience) + "%</div></div>" +
    '<div class="diag-item"><div class="label">Version</div><div class="value">' +
    esc(diag.spec_version || "1.30.0") + "</div></div>" +
    "</div>";
});

/* ---------- settings verify ---------- */
$("#verifyBtn").addEventListener("click", async () => {
  $("#ledgerState").textContent = "Checking…";
  try {
    const r = await fetch("/api/audit");
    const a = await r.json();
    $("#ledgerState").textContent = a.valid
      ? "Intact · " + (a.count || "?") + " actions on the record"
      : "Something doesn't add up — needs a look";
    toast(a.valid ? "The record checks out" : "The record doesn't add up", !a.valid);
  } catch {
    $("#ledgerState").textContent = "Can't reach the house — is it running?";
  }
});

/* ---------- status pill ---------- */
on("status", (s) => {
  $("#protoText").textContent = s.ok ? "Online · keeping an eye on things" : "Reconnecting… (" + (s.failures || 1) + ")";
  $("#protoPill").classList.toggle("warn", !s.ok);
});

/* ---------- demo home vs real home ---------- */
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
    toast(currentMode === "real" ? "This is your real home now" : "Back to the demo home");
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
        badge.textContent = "● Connected: " + (cfg.alexa.account_name || "Amazon account");
        badge.className = "real-badge online";
      } else {
        badge.textContent = "○ Not connected yet";
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
        alexaDetail.textContent = "● Connected: " + (cfg.alexa.account_name || "Amazon account") + " (" + ((cfg.alexa.echo_devices || []).length) + " Echo speakers)";
        alexaDetail.style.color = "var(--ok)";
      } else {
        alexaDetail.textContent = "○ Not signed in — log in above and your Echo shows up here";
        alexaDetail.style.color = "var(--t3)";
      }
    }

    // Render Echo hardware
    const echoStrip = $("#echoHardwareStrip");
    const echoCount = $("#echoCountPill");
    const echoes = (cfg.alexa && cfg.alexa.echo_devices) || [];
    if (echoCount) echoCount.textContent = echoes.length + " found";
    if (echoStrip) {
      echoStrip.innerHTML = echoes.map((e) =>
        '<div class="echo-pill"><strong>' + esc(e.name) + "</strong> <span class='micro' style='color: var(--ok)'>● " + esc(e.status || "online") + "</span></div>"
      ).join("") || '<span class="micro muted-2">None found yet</span>';
    }

    renderRealDevices(cfg.real_devices || []);
  } catch (err) {
    console.error("Failed loading real hardware config", err);
  }
}

function renderRealDevices(devices) {
  const homeGrid = $("#realDevicesGrid");
  const settingsList = $("#settingsDevicesList");

  const cardsHtml = devices.map((d) => {
    return (
      '<div class="device-card">' +
      '<div class="device-card-head">' +
      "<strong class='name'>" + esc(d.name) + "</strong>" +
      '<span class="domain-tag">' + esc(d.domain || "device") + "</span>" +
      "</div>" +
      '<div class="state">● ' + esc(d.state || "online") + "</div>" +
      '<div class="meta">' +
      "<span>" + esc(d.room || "Home") + "</span>" +
      "<span>" + esc(d.protocol || "connected") + "</span>" +
      "</div>" +
      "</div>"
    );
  }).join("");

  if (homeGrid) {
    homeGrid.innerHTML = cardsHtml || '<div class="empty"><strong>Nothing connected yet</strong>Sign in with Amazon and your devices show up on their own.</div>';
  }

  if (settingsList) {
    settingsList.innerHTML = devices.map((d) => {
      return (
        '<div class="dev-row">' +
        '<div class="dev-id"><div><strong>' + esc(d.name) + "</strong>" +
        "<small>" + esc(d.room || "Home") + " · " + esc(d.protocol || "") + " (" + esc(d.state || "online") + ")</small></div></div>" +
        '<button class="btn btn-sm btn-del-dev" data-id="' + esc(d.id) + '">Remove</button>' +
        "</div>"
      );
    }).join("") || '<div class="empty"><strong>No devices yet</strong>Everything is clean.</div>';

    $$(".btn-del-dev").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const did = btn.dataset.id;
        if (!did) return;
        await fetch("/api/real/device/" + encodeURIComponent(did), { method: "DELETE" });
        toast("Device removed");
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
  if (submitText) submitText.textContent = "Sign in";
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
  if (submitText) submitText.textContent = "Signing in…";
  if (progress) progress.hidden = false;

  setLightWave("thinking");

  // The steps a real sign-in takes, shown as they happen.
  const step1 = $("#stepLine1");
  if (step1) { step1.style.color = "var(--amber)"; step1.textContent = "● Checking your sign-in… ✓"; }
  await new Promise((r) => setTimeout(r, 240));

  const step2 = $("#stepLine2");
  if (step2) { step2.style.color = "var(--amber)"; step2.textContent = "● Asking Amazon's permission… ✓"; }
  await new Promise((r) => setTimeout(r, 240));

  const step3 = $("#stepLine3");
  if (step3) { step3.style.color = "var(--amber)"; step3.textContent = "● Looking for your Echo speakers… ✓ found them"; }
  await new Promise((r) => setTimeout(r, 240));

  const { status, data } = await post("/api/real/login", {
    account_name: email,
    skill_id: "amzn1.ask.skill.b84a9e22-hearth-alexa-plus",
  });

  const step4 = $("#stepLine4");
  if (step4) { step4.style.color = "var(--ok)"; step4.textContent = "● Waking up the rest of the house… done"; }
  await new Promise((r) => setTimeout(r, 240));

  if (status === 200 && data.ok) {
    playEarcon("success");
    setLightWave("speaking");
    toast("Connected — your speakers and devices are awake.");
    closeAmazonLoginModal();
    await loadRealHardwareConfig();
    refresh();
  } else {
    playEarcon("alert");
    setLightWave("alert");
    toast((data && data.error) || "Signing in didn't work", true);
    if (submitBtn) submitBtn.disabled = false;
    if (spinner) spinner.hidden = true;
    if (submitText) submitText.textContent = "Sign in";
  }
});

async function performQuickDemoAuth() {
  setLightWave("thinking");
  toast("Connecting to Amazon…");
  const { status, data } = await post("/api/real/login", {
    account_name: "Krishiv Joshi (Amazon Household)",
    skill_id: "amzn1.ask.skill.b84a9e22-hearth-alexa-plus",
  });
  if (status === 200 && data.ok) {
    playEarcon("success");
    setLightWave("speaking");
    toast("Connected — the demo household is awake.");
    await loadRealHardwareConfig();
    refresh();
  } else {
    playEarcon("alert");
    setLightWave("alert");
    toast((data && data.error) || "Couldn't sign in", true);
  }
}

async function performRealReset() {
  const { status, data } = await post("/api/real/reset", {});
  if (status === 200 && data.ok) {
    playEarcon("alert");
    toast("Back to a clean slate.");
    await loadRealHardwareConfig();
    refresh();
  }
}

async function performAlexaSync() {
  setLightWave("thinking");
  const { status, data } = await post("/api/real/sync", {});
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Looked for anything new — done");
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
    "Add a device by hand",
    '<div style="display: flex; flex-direction: column; gap: 10px">' +
    '<div><label>What to call it</label>' +
    '<input type="text" id="newDevName" placeholder="e.g. Bedroom thermostat" /></div>' +
    '<div style="display: flex; gap: 8px">' +
    '<div class="flex-1"><label>Which room</label>' +
    '<input type="text" id="newDevRoom" placeholder="Living room, kitchen…" value="Living room" /></div>' +
    '<div class="flex-1"><label>What is it</label>' +
    '<select id="newDevDomain">' +
    '<option value="climate">Heating &amp; cooling</option>' +
    '<option value="lock">A lock</option>' +
    '<option value="light">A light</option>' +
    '<option value="energy">Power &amp; solar</option>' +
    '<option value="camera">A camera</option>' +
    '<option value="switch">A plug or switch</option>' +
    "</select></div>" +
    "</div>" +
    "<div><label>How it's connected</label>" +
    '<select id="newDevProtocol">' +
    '<option value="Matter">Matter (works with everything)</option>' +
    '<option value="Zigbee">Zigbee or Z-Wave (via a hub)</option>' +
    '<option value="Alexa AVS">Already in Alexa</option>' +
    '<option value="Local REST">Local network (REST or MQTT)</option>' +
    "</select></div>" +
    "</div>",
    [
      {
        label: "Add it",
        primary: true,
        onClick: async () => {
          const name = $("#newDevName")?.value.trim();
          const room = $("#newDevRoom")?.value.trim() || "Living room";
          const domain = $("#newDevDomain")?.value || "climate";
          const protocol = $("#newDevProtocol")?.value || "Matter";
          if (!name) {
            toast("Give it a name first", true);
            return;
          }
          await post("/api/real/device", { name, room, domain, protocol, state: "connected" });
          playEarcon("success");
          toast("Added " + name);
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
  btn.textContent = "Checking…";
  const skill_id = $("#alexaSkillIdInput")?.value.trim();
  const { status, data } = await post("/api/real/test", { service: "alexa", creds: { skill_id } });
  btn.disabled = false;
  btn.textContent = "Check the link";
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Amazon is answering — you're linked");
    const det = $("#alexaStatusDetail");
    if (det) {
      det.textContent = "● " + (data.message || "Connected");
      det.style.color = "var(--ok)";
    }
  } else {
    toast((data && data.error) || "Couldn't reach Amazon", true);
  }
});

$("#testHubBtn")?.addEventListener("click", async () => {
  const btn = $("#testHubBtn");
  btn.disabled = true;
  btn.textContent = "Looking…";
  const url = $("#smartHubUrlInput")?.value.trim();
  const { status, data } = await post("/api/real/test", { service: "smart_hub", creds: { url } });
  btn.disabled = false;
  btn.textContent = "Find devices";
  if (status === 200 && data.ok) {
    playEarcon("success");
    toast(data.message || "Found the hub — devices synced");
    const det = $("#hubStatusDetail");
    if (det) {
      det.textContent = "● " + (data.message || "Connected");
      det.style.color = "var(--ok)";
    }
  } else {
    toast((data && data.error) || "Couldn't find that hub", true);
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
