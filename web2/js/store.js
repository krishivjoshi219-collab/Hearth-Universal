/* Hearth web2 store — single poll + pub/sub. One fetch path, no duplicate polling. */
const subs = new Map();

export function on(topic, fn) {
  if (!subs.has(topic)) subs.set(topic, new Set());
  subs.get(topic).add(fn);
  return () => subs.get(topic).delete(fn);
}

function emit(topic, data) {
  (subs.get(topic) || []).forEach((fn) => {
    try {
      fn(data);
    } catch (e) {
      console.error("[store]", topic, e);
    }
  });
}

async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}

let timer = null;
let failures = 0;

export async function refresh() {
  try {
    const [home, props, audit] = await Promise.all([
      get("/api/home").catch(() => null),
      get("/api/proposals?limit=100").catch(() => null),
      get("/api/audit").catch(() => null),
    ]);
    failures = 0;
    emit("status", { ok: true });
    if (home) emit("home", home);
    if (props) emit("proposals", props);
    if (audit) emit("audit", audit);
    try {
      const dep = await get("/api/commerce/depletion").catch(() => null);
      if (dep) emit("depletion", dep);
    } catch {}
    try {
      const roi = await get("/api/renewals").catch(() => null);
      if (roi) emit("roi", roi);
    } catch {}
  } catch (e) {
    failures++;
    emit("status", { ok: false, failures });
  }
}

export function startPolling(ms = 5000) {
  refresh();
  if (timer) clearInterval(timer);
  timer = setInterval(refresh, ms);
}

export async function post(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await r.json().catch(() => ({}));
  return { status: r.status, data };
}
