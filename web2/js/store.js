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
let currentInterval = 4000;
let baseInterval = 4000;

export async function refresh() {
  try {
    const [home, props, audit] = await Promise.all([
      get("/api/home").catch(() => null),
      get("/api/proposals?limit=100").catch(() => null),
      get("/api/audit").catch(() => null),
    ]);
    if (failures > 0) {
      failures = 0;
      currentInterval = baseInterval;
      if (timer) {
        clearInterval(timer);
        timer = setInterval(refresh, currentInterval);
      }
    }
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
    try {
      const models = await get("/api/models").catch(() => null);
      if (models) emit("models", models);
    } catch {}
    try {
      const parl = await get("/api/parliament/ministers").catch(() => null);
      if (parl) emit("parliament", parl);
    } catch {}
    try {
      const causal = await get("/api/causal/vulnerabilities").catch(() => null);
      if (causal) emit("causal", causal);
    } catch {}
    try {
      const meta = await get("/api/meta-skills").catch(() => null);
      if (meta) emit("metaSkills", meta);
    } catch {}
    try {
      const forensics = await get("/api/forensics/reconstruct").catch(() => null);
      if (forensics) emit("forensics", forensics);
    } catch {}
    try {
      const acoustic = await get("/api/acoustic/scan").catch(() => null);
      if (acoustic) emit("acoustic", acoustic);
    } catch {}
    try {
      const mediation = await get("/api/mediation/treaty").catch(() => null);
      if (mediation) emit("mediation", mediation);
    } catch {}
    try {
      const swarm = await get("/api/swarm/grid").catch(() => null);
      if (swarm) emit("swarm", swarm);
    } catch {}
    try {
      const diag = await get("/api/diagnostics").catch(() => null);
      if (diag) emit("diagnostics", diag);
    } catch {}
  } catch (e) {
    failures++;
    currentInterval = Math.min(15000, baseInterval * Math.pow(1.5, Math.min(failures, 4)));
    if (timer) {
      clearInterval(timer);
      timer = setInterval(refresh, currentInterval);
    }
    emit("status", { ok: false, failures });
  }
}

export function startPolling(ms = 4000) {
  baseInterval = ms;
  currentInterval = ms;
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
