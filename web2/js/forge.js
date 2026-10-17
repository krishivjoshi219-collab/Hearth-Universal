/* Hearth Forge — compile a household rule into a live MCP tool.
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

  const STEPS = ["Intent", "Schema", "Sentinel", "AST", "Smoke", "MCP mount"];
  let ticker = null;

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

  function paintCatalog(tools) {
    catalogEl.innerHTML = "";
    if (!tools.length) {
      const hint = document.createElement("p");
      hint.className = "muted-sm";
      hint.textContent = "No forged tools yet — compile one above and it appears here, callable over MCP.";
      catalogEl.appendChild(hint);
      return;
    }
    tools.forEach((t) => {
      const row = document.createElement("div");
      row.className = "forge-item";
      const name = document.createElement("code");
      name.textContent = t.name;
      const desc = document.createElement("span");
      desc.textContent = t.description || "Forged household tool";
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
        countEl.textContent = `${data.tools_count} MCP tools live`;
        paintCatalog(data.tools || []);
      }
    } catch {
      /* offline: keep the last known catalog */
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const requirement = input.value.trim();
    if (!requirement || go.disabled) return;
    go.disabled = true;
    out.hidden = true;
    resultEl.hidden = true;
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
        body: JSON.stringify({ requirement }),
      });
      const data = await res.json();
      clearInterval(ticker);
      if (!data.ok) {
        paintSteps(STEPS.length - 1, STEPS.length - 1);
        resultEl.hidden = false;
        resultEl.textContent = `Forge refused: ${data.error || "unknown error"}`;
        return;
      }
      paintSteps(STEPS.length);
      out.hidden = false;
      codeEl.textContent = data.code || "";
      toolEl.textContent = data.mcp_tool || "";
      safetyEl.textContent = data.safety_audit || "passed";
      smokeEl.textContent = data.test_report && data.test_report.ok ? "passed" : "failed";
      callBtn.dataset.tool = data.mcp_tool || "";
      countEl.textContent = `${data.tools_count} MCP tools live`;
      await loadCatalog();
    } catch (err) {
      clearInterval(ticker);
      paintSteps(STEPS.length - 1, STEPS.length - 1);
      resultEl.hidden = false;
      resultEl.textContent = `Network error: ${err}`;
    } finally {
      go.disabled = false;
    }
  });

  callBtn.addEventListener("click", async () => {
    const tool = callBtn.dataset.tool;
    if (!tool) return;
    callBtn.disabled = true;
    resultEl.hidden = false;
    resultEl.textContent = "Calling the mounted MCP tool…";
    try {
      const res = await fetch("/api/forge/invoke", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ tool, params: {} }),
      });
      const data = await res.json();
      resultEl.textContent = data.ok
        ? JSON.stringify(data.result, null, 2)
        : `Tool error: ${data.error}`;
    } catch (err) {
      resultEl.textContent = `Network error: ${err}`;
    } finally {
      callBtn.disabled = false;
    }
  });

  paintSteps(-1);
  loadCatalog();
}
