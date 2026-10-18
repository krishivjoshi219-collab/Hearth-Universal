/* Hearth Forge — compile a household rule into a live MCP tool.
   Grand Tier: rule templates, Sentinel refusal with plain-language reasons,
   "Repair intent" self-repair, and a shareable tool card (audit-chained).
   Self-contained so the cockpit contract (app.js) doesn't grow. */
const $ = (sel) => document.querySelector(sel);

const panel = $("#forgePanel");
if (panel) {
  const form = $("#forgeForm");
  const input = $("#forgeInput");
  const go = $("#forgeGo");
  const stepsEl = $("#forgeSteps");
  const out = $("#forgeOut");
  const codeEl = $("#forgeCode");
  const toolEl = $("#forgeToolName");
  const safetyEl = $("#forgeSafety");
  const smokeEl = $("#forgeSmoke");
  const callBtn = $("#forgeCall");
  const resultEl = $("#forgeResult");
  const catalogEl = $("#forgeCatalog");
  const countEl = $("#forgeCount");
  const tplEl = $("#forgeTemplates");
  const refuseEl = $("#forgeRefuse");
  const refuseGateEl = $("#forgeRefuseGate");
  const refuseReasonEl = $("#forgeRefuseReason");
  const refuseDetailEl = $("#forgeRefuseDetail");
  const refuseRepairEl = $("#forgeRefuseRepair");
  const refuseSuggestionEl = $("#forgeRefuseSuggestion");
  const repairBtn = $("#forgeRepair");
  const proofEl = $("#forgeProof");
  const snipEl = $("#forgeSnip");
  const copyBtn = $("#forgeCopy");
  const repairedEl = $("#forgeRepaired");

  const STEPS = ["Understanding", "Writing the plan", "Checking safety", "Double-checking", "Trying it out", "Ready"];
  const GATE_STEP = { intent: 0, schema: 1, sentinel: 2, child_gate: 2, ast: 3, smoke: 4, mount: 5 };

  const TEMPLATES = [
    {
      label: "Charge the car after 10pm, cheap power only",
      rule: "Charge the EV with at least 8 kWh after 10pm, never pay above $0.28/kWh",
    },
    {
      label: "Cool the house before the evening rush",
      rule: "Pre-cool the living room to 70F before the 4pm peak tariff",
    },
    {
      label: "Dishwasher on the cheap, quiet hours",
      rule: "Run the dishwasher after 10pm in eco mode",
    },
    {
      label: "Watch one get refused — unlock on any motion",
      rule: "Unlock the front door whenever the camera sees motion",
      danger: true,
    },
  ];

  let ticker = null;
  let lastRequirement = "";

  function paintSteps(done, failedAt = -1) {
    stepsEl.innerHTML = "";
    STEPS.forEach((label, i) => {
      const chip = document.createElement("span");
      let cls = "forge-step";
      if (i < done) cls += " is-done";
      else if (i === done && failedAt < 0) cls += " is-active";
      if (i === failedAt) cls += " is-fail";
      chip.className = cls;
      chip.textContent = label;
      stepsEl.appendChild(chip);
    });
  }

  function paintTemplates() {
    tplEl.innerHTML = "";
    TEMPLATES.forEach((t) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "forge-tpl" + (t.danger ? " is-danger" : "");
      b.textContent = t.label;
      b.addEventListener("click", () => {
        input.value = t.rule;
        input.focus();
      });
      tplEl.appendChild(b);
    });
  }

  function paintCatalog(tools) {
    catalogEl.innerHTML = "";
    if (!tools.length) {
      const hint = document.createElement("p");
      hint.className = "lede-sm";
      hint.textContent = "Nothing learned yet — teach one above and it appears here, ready to use.";
      catalogEl.appendChild(hint);
      return;
    }
    tools.forEach((t) => {
      const row = document.createElement("div");
      row.className = "forge-item";
      const name = document.createElement("code");
      name.textContent = t.name;
      const desc = document.createElement("span");
      desc.textContent = t.description || "A habit Hearth wrote";
      const live = document.createElement("span");
      live.className = "forge-live";
      live.textContent = "live";
      row.append(name, desc, live);
      catalogEl.appendChild(row);
    });
  }

  async function loadCatalog() {
    try {
      const res = await fetch("/api/forge/tools");
      const data = await res.json();
      if (data.ok) {
        const forged = (data.tools || []).length;
        countEl.textContent = `${data.tools_count} abilities · ${forged} learned here`;
        paintCatalog(data.tools || []);
      }
    } catch {
      /* offline: keep the last known catalog */
    }
  }

  function hideRefusal() {
    refuseEl.hidden = true;
    refuseRepairEl.hidden = true;
  }

  function showRefusal(data) {
    refuseEl.hidden = false;
    const gate = String(data.gate || "sentinel");
    refuseGateEl.textContent = gate === "child_gate" ? "A CHILD ASKED" : "SAFETY";
    refuseReasonEl.textContent = data.reason || "Hearth wouldn't do that";
    refuseDetailEl.textContent = data.detail || "";
    const canRepair = !!data.repair_available && !!data.suggested_repair;
    refuseRepairEl.hidden = !canRepair;
    if (canRepair) {
      refuseSuggestionEl.textContent = data.suggested_repair;
      repairBtn.dataset.suggestion = data.suggested_repair;
      repairBtn.dataset.repairedFrom = lastRequirement;
    }
  }

  async function runForge(requirement, repairedFrom = "") {
    if (!requirement || go.disabled) return;
    lastRequirement = requirement;
    go.disabled = true;
    hideRefusal();
    out.hidden = true;
    resultEl.hidden = true;
    repairedEl.hidden = true;
    let step = 0;
    paintSteps(step);
    ticker = setInterval(() => {
      step = Math.min(step + 1, STEPS.length - 1);
      paintSteps(step);
    }, 320);
    try {
      const res = await fetch("/api/forge/synthesize", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ requirement, repaired_from: repairedFrom }),
      });
      const data = await res.json();
      clearInterval(ticker);
      if (!data.ok) {
        const failedAt = GATE_STEP[data.gate] ?? STEPS.length - 1;
        paintSteps(failedAt, failedAt);
        showRefusal(data);
        return;
      }
      paintSteps(STEPS.length);
      out.hidden = false;
      codeEl.textContent = data.code || "";
      toolEl.textContent = data.mcp_tool || "";
      safetyEl.textContent = data.safety_audit || "passed";
      smokeEl.textContent = data.test_report && data.test_report.ok ? "passed" : "failed";
      callBtn.dataset.tool = data.mcp_tool || "";
      const hash = String(data.audit_hash || "");
      proofEl.textContent = hash ? `${hash.slice(0, 10)}…${hash.slice(-6)} ✓ on record` : "–";
      snipEl.textContent = data.mcp_tool || "–";
      repairedEl.hidden = !data.repaired;
      if (data.tools_count) countEl.textContent = `${data.tools_count} abilities live`;
      await loadCatalog();
    } catch (err) {
      clearInterval(ticker);
      paintSteps(STEPS.length - 1, STEPS.length - 1);
      resultEl.hidden = false;
      resultEl.textContent = `Couldn't reach the house: ${err}`;
    } finally {
      go.disabled = false;
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runForge(input.value.trim(), "");
  });

  repairBtn.addEventListener("click", () => {
    const suggestion = repairBtn.dataset.suggestion || "";
    const from = repairBtn.dataset.repairedFrom || lastRequirement;
    if (!suggestion) return;
    input.value = suggestion;
    runForge(suggestion, from);
  });

  copyBtn.addEventListener("click", async () => {
    const name = snipEl.textContent.trim();
    if (!name || name === "–") return;
    try {
      await navigator.clipboard.writeText(name);
      copyBtn.textContent = "Copied ✓";
    } catch {
      copyBtn.textContent = "Select + copy";
    }
    setTimeout(() => {
      copyBtn.textContent = "Copy";
    }, 1400);
  });

  callBtn.addEventListener("click", async () => {
    const tool = callBtn.dataset.tool;
    if (!tool) return;
    callBtn.disabled = true;
    resultEl.hidden = false;
    resultEl.textContent = "Asking the house to run it…";
    try {
      const res = await fetch("/api/forge/invoke", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ tool, params: {} }),
      });
      const data = await res.json();
      resultEl.textContent = data.ok
        ? JSON.stringify(data.result, null, 2)
        : `It didn't run: ${data.error}`;
    } catch (err) {
      resultEl.textContent = `Couldn't reach the house: ${err}`;
    } finally {
      callBtn.disabled = false;
    }
  });

  paintSteps(-1);
  paintTemplates();
  loadCatalog();
}
