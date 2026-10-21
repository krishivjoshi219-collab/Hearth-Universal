/* ============================================================================
   Hearth — The Wire.
   A real MCP client, in the browser, with no framework and no mocks:
     POST /mcp  ·  initialize → notifications/initialized → tools/list → tools/call
   Streamable HTTP responses are parsed whether the server answers with JSON
   or an SSE stream. Every string that reaches the DOM does so via
   textContent — server output is never trusted as markup.
   ========================================================================= */
(function () {
  "use strict";

  var ENDPOINT = "/mcp";
  var PROTOCOL = "2025-11-25";

  function $(sel) { return document.querySelector(sel); }

  var el = {
    transcript: $("#wireTranscript"),
    count: $("#wireCount"),
    foot: $("#footNote"),
    protoDot: $("#protoDot"),
    protoText: $("#protoText"),
    search: $("#wireSearch"),
    tools: $("#wireTools"),
    toolCount: $("#toolCount"),
    callName: $("#callName"),
    callArgs: $("#callArgs"),
    callSend: $("#callSend"),
  };

  var exchanges = 0;
  var picked = null;
  var toolsById = {};
  var busy = false;

  /* ------------------------------------------------------------------ rpc */
  function parseSSE(text) {
    var out = null;
    text.split(/\r?\n/).forEach(function (line) {
      var l = line.trim();
      if (l.indexOf("data:") !== 0) return;
      var payload = l.slice(5).trim();
      if (!payload || payload === "[DONE]") return;
      var obj = null;
      try { obj = JSON.parse(payload); } catch (e) { return; }
      if (!obj || typeof obj !== "object") return;
      if (obj.result !== undefined || obj.error !== undefined) out = obj;
      else if (!out) out = obj;
    });
    return out;
  }

  function pulseRibbon() {
    var steps = document.querySelectorAll(".arch-step");
    steps.forEach(function (step, i) {
      setTimeout(function () {
        step.classList.add("is-active-pulse");
        setTimeout(function () {
          step.classList.remove("is-active-pulse");
        }, 550);
      }, i * 90);
    });
  }

  async function wire(method, params, isNotification) {
    pulseRibbon();
    var body = { jsonrpc: "2.0", method: method, params: params || {} };
    var pending = null;
    if (!isNotification) {
      body.id = ++exchanges;
      pending = addPending(method, body.id);
    }
    var started = performance.now();
    var res, text = "", data = null;
    try {
      res = await fetch(ENDPOINT, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "accept": "application/json, text/event-stream",
          "mcp-protocol-version": PROTOCOL,
        },
        body: JSON.stringify(body),
      });
      text = await res.text();
    } catch (e) {
      text = String((e && e.message) || e);
      res = { status: 0, headers: { get: function () { return ""; } } };
    }
    var ms = Math.round(performance.now() - started);
    var ctype = (res.headers && res.headers.get && res.headers.get("content-type")) || "";
    if (text && ctype.indexOf("text/event-stream") >= 0) {
      data = parseSSE(text);
    } else if (text) {
      try { data = JSON.parse(text); } catch (e2) { data = null; }
    }
    if (isNotification) {
      addNote("Notification sent (" + method + ") — " + (res.status || 0) + " acknowledged, no reply expected.");
      return null;
    }
    renderExchange({
      method: method,
      request: body,
      status: res.status || 0,
      data: data,
      rawText: text,
      ms: ms,
    }, pending);
    return data;
  }

  /* ------------------------------------------------------------- rendering */
  function addNode(node) {
    el.transcript.appendChild(node);
    el.transcript.scrollTop = el.transcript.scrollHeight;
    return node;
  }

  function addNote(text) {
    var div = document.createElement("div");
    div.className = "note";
    div.textContent = text;
    return addNode(div);
  }

  function addPending(method, id) {
    var wrap = document.createElement("div");
    wrap.className = "ex is-pending";
    var head = document.createElement("div");
    head.className = "ex-head";
    var m = document.createElement("span");
    m.className = "ex-method";
    m.textContent = method;
    var meta = document.createElement("span");
    meta.className = "ex-meta";
    meta.textContent = "#" + (id || "—") + " · on the wire…";
    head.append(m, meta);
    var line = document.createElement("div");
    line.className = "ex-summary";
    line.textContent = "Sent — waiting for the house to answer…";
    wrap.append(head, line);
    return addNode(wrap);
  }

  function badge(text, cls) {
    var span = document.createElement("span");
    span.className = "badge" + (cls ? " " + cls : "");
    span.textContent = text;
    return span;
  }

  function exchangeSummary(ex) {
    var d = ex.data || {};
    if (d.error) {
      return { text: "The house answered with an error: " + String((d.error && d.error.message) || "unknown"), badge: "error", cls: "is-bad" };
    }
    var r = d.result || {};
    if (ex.method === "initialize") {
      var si = r.serverInfo || {};
      return {
        text: "Hello from the house — " + String(si.name || "server") + " v" + String(si.version || "?") + " speaking MCP " + String(r.protocolVersion || "?"),
        badge: "handshake complete",
        cls: "is-good",
      };
    }
    if (ex.method === "tools/list") {
      var n = Array.isArray(r.tools) ? r.tools.length : 0;
      return { text: n + " abilities answered, each with a schema the client can read.", badge: n + " abilities", cls: "is-good" };
    }
    if (ex.method === "tools/call") {
      var sc = r.structuredContent || null;
      if (!sc && Array.isArray(r.content)) {
        for (var i = 0; i < r.content.length; i++) {
          var c = r.content[i];
          if (c && c.type === "text" && c.text) {
            try { sc = JSON.parse(c.text); } catch (e) { sc = null; }
            if (sc) break;
          }
        }
      }
      if (r.isError) return { text: "The house refused that call.", badge: "refused", cls: "is-bad" };
      if (sc && typeof sc === "object") {
        if (sc.approval_required || sc.status === "approval_required") {
          return { text: "The house held it for a person's approval — exactly as designed. Nothing moved.", badge: "approval required", cls: "is-warn" };
        }
        if (sc.blocked) {
          return { text: String(sc.message || "Held back by a guardrail."), badge: "held back", cls: "is-warn" };
        }
        if (sc.message) return { text: String(sc.message), badge: "done", cls: "is-good" };
        if (sc.voice_summary) return { text: String(sc.voice_summary), badge: "done", cls: "is-good" };
      }
      if (Array.isArray(r.content) && r.content[0] && r.content[0].text) {
        var first = String(r.content[0].text).split("\n")[0].slice(0, 180);
        return { text: first, badge: "done", cls: "is-good" };
      }
      return { text: "Done — the reply is below, in full.", badge: "done", cls: "is-good" };
    }
    return { text: "Exchange recorded.", badge: "200", cls: "" };
  }

  function renderExchange(ex, replaceNode) {
    var wrap = document.createElement("div");
    wrap.className = "ex";

    var head = document.createElement("div");
    head.className = "ex-head";
    var method = document.createElement("span");
    method.className = "ex-method";
    method.textContent = ex.method;
    var meta = document.createElement("span");
    meta.className = "ex-meta";
    meta.textContent = (ex.status || 0) + " · " + ex.ms + " ms · #" + (ex.request.id || "—");
    head.append(method, meta);

    var summary = exchangeSummary(ex);
    head.appendChild(badge(summary.badge, summary.cls));

    var line = document.createElement("div");
    line.className = "ex-summary";
    line.textContent = summary.text;

    var details = document.createElement("details");
    var sum = document.createElement("summary");
    sum.textContent = "raw wire message";
    var pre = document.createElement("pre");
    var reply = ex.rawText && ex.rawText.length > 4000 ? ex.rawText.slice(0, 4000) + "\n…" : (ex.rawText || "(no body)");
    pre.textContent = "→ request\n" + JSON.stringify(ex.request, null, 2) + "\n\n← response\n" + reply;
    details.append(sum, pre);

    wrap.append(head, line, details);
    if (replaceNode && replaceNode.parentNode) {
      replaceNode.parentNode.replaceChild(wrap, replaceNode);
      el.transcript.scrollTop = el.transcript.scrollHeight;
    } else {
      addNode(wrap);
    }
    el.count.textContent = exchanges + (exchanges === 1 ? " exchange" : " exchanges");
  }

  /* ----------------------------------------------------------------- tools */
  function templateFor(tool) {
    var schema = (tool && tool.inputSchema) || {};
    var props = schema.properties || {};
    var out = {};
    Object.keys(props).forEach(function (k) {
      var t = props[k] && props[k].type;
      if (t === "number" || t === "integer") out[k] = 0;
      else if (t === "boolean") out[k] = false;
      else if (t === "array") out[k] = [];
      else out[k] = "";
    });
    return JSON.stringify(out, null, 2);
  }

  var DEFAULTS = {
    home_toggle_lock: { door: "front_door", locked: false },
  };

  function pickTool(tool) {
    picked = tool;
    el.callName.textContent = tool.name;
    var preset = DEFAULTS[tool.name];
    el.callArgs.value = preset ? JSON.stringify(preset, null, 2) : templateFor(tool);
    Array.prototype.forEach.call(el.tools.querySelectorAll(".tool"), function (b) {
      b.classList.toggle("is-picked", b.dataset.tool === tool.name);
    });
  }

  function renderTools(list) {
    toolsById = {};
    el.tools.innerHTML = "";
    list.forEach(function (t) {
      if (!t || !t.name) return;
      toolsById[t.name] = t;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "tool";
      b.dataset.tool = t.name;
      var name = document.createElement("b");
      name.textContent = t.name;
      var desc = document.createElement("span");
      desc.textContent = String(t.description || "").split("\n")[0].slice(0, 160) || "No description given.";
      b.append(name, desc);
      b.addEventListener("click", function () { pickTool(t); });
      el.tools.appendChild(b);
    });
  }

  function filterTools() {
    var q = String(el.search.value || "").trim().toLowerCase();
    Array.prototype.forEach.call(el.tools.querySelectorAll(".tool"), function (b) {
      var t = toolsById[b.dataset.tool] || {};
      var hay = (b.dataset.tool + " " + String(t.description || "")).toLowerCase();
      b.style.display = !q || hay.indexOf(q) >= 0 ? "" : "none";
    });
  }
  el.search && el.search.addEventListener("input", filterTools);

  /* ------------------------------------------------------------ call flow */
  el.callSend && el.callSend.addEventListener("click", async function () {
    if (busy || !picked) return;
    var args = {};
    try {
      args = JSON.parse(el.callArgs.value || "{}");
    } catch (e) {
      addNote("The arguments box is not valid JSON yet — fix it and send again.");
      return;
    }
    busy = true;
    el.callSend.disabled = true;
    await wire("tools/call", { name: picked.name, arguments: args });
    busy = false;
    el.callSend.disabled = false;
  });

  /* ------------------------------------------------------------ quick tests */
  document.querySelectorAll(".quick-chip").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (busy) return;
      var tool = btn.getAttribute("data-tool");
      if (!tool) return;
      var args = {};
      if (tool === "inbox_scan") args = { persona: "admin" };
      else if (tool === "home_get_state") args = {};
      else if (tool === "commerce_list_inventory") args = {};

      if (el.callName) el.callName.textContent = tool;
      if (el.callArgs) el.callArgs.value = JSON.stringify(args, null, 2);

      busy = true;
      if (el.callSend) el.callSend.disabled = true;
      await wire("tools/call", { name: tool, arguments: args });
      busy = false;
      if (el.callSend) el.callSend.disabled = false;
    });
  });

  /* ---------------------------------------------------------------- boot */
  (async function boot() {
    addNote("This page is a real MCP client. Everything below travels over Streamable HTTP to /mcp — the same server that runs the house. Nothing here is mocked.");
    var init = await wire("initialize", {
      protocolVersion: PROTOCOL,
      capabilities: {},
      clientInfo: { name: "hearth-wire", version: "1.0" },
    });
    var ok = !!(init && init.result);
    if (el.protoDot) el.protoDot.className = "dot" + (ok ? " is-ok" : " is-bad");
    if (el.protoText) el.protoText.textContent = ok ? "MCP " + String(init.result.protocolVersion || PROTOCOL) + " · live" : "no handshake";
    if (!ok) {
      if (el.foot) el.foot.textContent = "Could not reach /mcp. Start the Hearth server, then reload this page.";
      return;
    }
    await wire("notifications/initialized", {}, true);
    var list = await wire("tools/list", {});
    var tools = (list && list.result && Array.isArray(list.result.tools)) ? list.result.tools : [];
    renderTools(tools);
    if (el.toolCount) el.toolCount.textContent = tools.length + (tools.length === 1 ? " ability" : " abilities");
    if (el.foot) el.foot.textContent = "Handshake complete — " + tools.length + " abilities on the wire. Pick one and call it, live.";
    var preferred = tools.filter(function (t) {
      return /lock|unlock/.test(t.name);
    })[0];
    if (preferred) pickTool(preferred);
  })();
})();
