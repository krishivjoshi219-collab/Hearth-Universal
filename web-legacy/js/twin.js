/**
 * DIGITAL TWIN & SPATIAL ARCHITECTURAL ENGINE — HEARTH UNIVERSAL
 * Architectural 2.5D CAD Blueprint · Photometric Radiance Pools · Thermal Micro-Climate Zones
 * Family Occupancy Radar · Perimeter Security · Web Audio Tactile Synthesis · Ring Cam Simulator
 */

// =============================================================================
// PROCEDURAL TACTILE WEB AUDIO SYNTHESIZER
// =============================================================================
class TactileAudioSynth {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) this.ctx = new AudioCtx();
      } catch (e) {}
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
  }

  isEnabled() {
    if (window.hearthApp?.voice && window.hearthApp.voice.soundEnabled === false) {
      return false;
    }
    return true;
  }

  playHoverTick() {
    if (!this.isEnabled()) return;
    this.init();
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(2600, t);
    osc.frequency.exponentialRampToValueAtTime(1400, t + 0.012);
    gain.gain.setValueAtTime(0.02, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.012);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(t);
    osc.stop(t + 0.015);
  }

  playToggle(isOn) {
    if (!this.isEnabled()) return;
    this.init();
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sine";
    if (isOn) {
      osc.frequency.setValueAtTime(460, t);
      osc.frequency.exponentialRampToValueAtTime(880, t + 0.06);
    } else {
      osc.frequency.setValueAtTime(880, t);
      osc.frequency.exponentialRampToValueAtTime(440, t + 0.06);
    }
    gain.gain.setValueAtTime(0.001, t);
    gain.gain.linearRampToValueAtTime(0.08, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.07);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(t);
    osc.stop(t + 0.08);
  }

  playLock(locked) {
    if (!this.isEnabled()) return;
    this.init();
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc1.type = "square";
    osc2.type = "sine";
    osc1.frequency.setValueAtTime(locked ? 320 : 280, t);
    osc2.frequency.setValueAtTime(locked ? 110 : 130, t);
    gain.gain.setValueAtTime(0.001, t);
    gain.gain.linearRampToValueAtTime(0.12, t + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(this.ctx.destination);
    osc1.start(t);
    osc2.start(t);
    osc1.stop(t + 0.13);
    osc2.stop(t + 0.13);
  }

  playTempStep() {
    if (!this.isEnabled()) return;
    this.init();
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(740, t);
    gain.gain.setValueAtTime(0.001, t);
    gain.gain.linearRampToValueAtTime(0.04, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(t);
    osc.stop(t + 0.05);
  }
}

// =============================================================================
// MAIN DIGITAL TWIN ENGINE
// =============================================================================
export class DigitalTwinEngine {
  constructor(apiBase = "", onStateChange = null) {
    this.apiBase = apiBase;
    this.onStateChange = onStateChange;
    this.state = null;
    this.audio = new TactileAudioSynth();

    // View modes: "radiance" (photometric lighting), "thermal" (HVAC micro-climate), "security" (perimeter sensors)
    this.viewMode = "radiance";

    // Ring Camera elements
    this.ringCanvas = document.getElementById("ringCamCanvas");
    this.ringCtx = this.ringCanvas ? this.ringCanvas.getContext("2d") : null;
    this.isDoorbellRinging = false;
    this.visitorOverlay = null;
    this.isNightVision = false;

    // Floorplan elements
    this.fpCanvas = document.getElementById("floorplanCanvas");
    this.fpCtx = this.fpCanvas ? this.fpCanvas.getContext("2d") : null;
    this.fpZoneHud = document.getElementById("floorplanZoneHud");
    this.hoveredRoomKey = null;
    this.selectedRoomKey = null;
    this.hoveredInteractiveElement = null; // "lock", "light_fixture", "occupant", "ring_cam"

    // Virtual CAD resolution
    this.virtualW = 920;
    this.virtualH = 380;

    // Architectural zones
    this.rooms = {
      kitchen: {
        id: "kitchen",
        stateKey: "kitchen",
        name: "Kitchen & Dining",
        area: "32.4 m²",
        icon: "🍳",
        x: 35, y: 25, w: 410, h: 130,
        lightPos: { x: 240, y: 85 },
        occupant: {
          name: "Sarah",
          status: "Active (Preparing dinner)",
          comfort: "23.0°C",
          pos: { x: 240, y: 78 }
        },
        baseTemp: 20.5
      },
      living_room: {
        id: "living_room",
        stateKey: "living_room",
        name: "Living Room Lounge",
        area: "38.2 m²",
        icon: "🛋️",
        x: 35, y: 165, w: 410, h: 185,
        lightPos: { x: 240, y: 255 },
        occupant: {
          name: "Alex",
          status: "Active (Reading)",
          comfort: "20.0°C",
          pos: { x: 135, y: 270 }
        },
        baseTemp: 21.0
      },
      bedroom: {
        id: "bedroom",
        stateKey: "master_bedroom",
        name: "Master Bedroom Suite",
        area: "36.0 m²",
        icon: "🛏️",
        x: 465, y: 25, w: 420, h: 165,
        lightPos: { x: 675, y: 105 },
        occupant: {
          name: "Leo",
          status: "Resting (Wind-Down)",
          comfort: "19.5°C",
          pos: { x: 675, y: 100 }
        },
        baseTemp: 19.5
      },
      entryway: {
        id: "entryway",
        stateKey: "entryway",
        name: "Entryway & Front Porch",
        area: "24.5 m²",
        icon: "🚪",
        x: 465, y: 200, w: 420, h: 150,
        lightPos: { x: 675, y: 275 },
        occupant: null,
        baseTemp: 18.5
      }
    };

    // Smooth animation & transition states (interpolated values)
    this.animState = {
      kitchen: { bri: 90, r: 255, g: 248, b: 235, rad: 190, hover: 0 },
      living_room: { bri: 20, r: 153, g: 51, b: 255, rad: 95, hover: 0 },
      bedroom: { bri: 0, r: 255, g: 179, b: 102, rad: 0, hover: 0 },
      entryway: { bri: 60, r: 255, g: 215, b: 160, rad: 140, hover: 0 }
    };

    // HVAC micro-particles for thermal airflow visualization
    this.hvacParticles = Array.from({ length: 32 }, () => ({
      x: Math.random() * 800 + 50,
      y: Math.random() * 320 + 30,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.35,
      size: Math.random() * 1.5 + 1,
      alpha: Math.random() * 0.4 + 0.15
    }));

    this.radarAngle = 0;
    this.tickCount = 0;

    this.initRingCameraCanvas();
    this.initFloorplanCanvas();
    this.bindHeaderControls();
  }

  // Safe resolver for room state matching both aliases and canonical keys
  getRoomState(key) {
    if (!this.state) return null;
    if (key === "bedroom" || key === "master_bedroom") {
      return this.state.master_bedroom || this.state.bedroom || null;
    }
    if (key === "living_room" || key === "living") {
      return this.state.living_room || this.state.living || null;
    }
    return this.state[key] || null;
  }

  // Color parser that converts state hex or color_temp into RGB values
  parseLightColor(lights) {
    if (!lights || !lights.on) {
      return { r: 120, g: 120, b: 130, bri: 0 };
    }
    const bri = typeof lights.bri === "number" ? lights.bri : 60;
    if (bri <= 0) return { r: 120, g: 120, b: 130, bri: 0 };

    if (lights.hex && lights.hex.startsWith("#") && lights.hex.length >= 7) {
      const r = parseInt(lights.hex.slice(1, 3), 16) || 255;
      const g = parseInt(lights.hex.slice(3, 5), 16) || 200;
      const b = parseInt(lights.hex.slice(5, 7), 16) || 120;
      return { r, g, b, bri };
    }

    const ct = (lights.color_temp || lights.ct || "warm").toLowerCase();
    if (ct.includes("warm") || ct.includes("2700") || ct.includes("3000")) {
      return { r: 255, g: 182, b: 92, bri }; // 2700K Warm amber
    } else if (ct.includes("cool") || ct.includes("5000") || ct.includes("6500")) {
      return { r: 200, g: 235, b: 255, bri }; // 5000K Crisp daylight
    } else {
      return { r: 255, g: 248, b: 235, bri }; // 4000K Clean neutral
    }
  }

  async fetchState() {
    try {
      const res = await fetch(`${this.apiBase}/api/home`);
      if (res.ok) {
        this.state = await res.json();
        if (this.onStateChange) this.onStateChange(this.state);
        this.renderZoneHud();
        return this.state;
      }
    } catch (e) {
      console.warn("Failed to fetch home state", e);
    }
    return null;
  }

  async updateDevice(room, device, patch) {
    try {
      const res = await fetch(`${this.apiBase}/api/home/device`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room, device, patch })
      });
      const data = await res.json();
      if (data.ok && data.state) {
        this.state = data.state;
        if (this.onStateChange) this.onStateChange(this.state);
        this.renderZoneHud();
      }
      return data;
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  async setScene(sceneName) {
    try {
      const res = await fetch(`${this.apiBase}/api/home/scene`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: sceneName })
      });
      const data = await res.json();
      if (data.ok && data.state) {
        this.state = data.state;
        if (this.onStateChange) this.onStateChange(this.state);
        this.renderZoneHud();
      }
      return data;
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  async toggleLock(door = "front_door", locked = true) {
    try {
      const res = await fetch(`${this.apiBase}/api/home/lock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ door, locked })
      });
      const data = await res.json();
      if (data.state) {
        this.state = data.state;
        if (this.onStateChange) this.onStateChange(this.state);
        this.renderZoneHud();
      }
      return data;
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  async triggerRingEvent(eventType = "doorbell_press", visitor = "Delivery Courier") {
    try {
      this.isDoorbellRinging = true;
      this.visitorOverlay = visitor;
      
      const res = await fetch(`${this.apiBase}/api/ring/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_type: eventType, visitor })
      });
      const data = await res.json();

      setTimeout(() => {
        this.isDoorbellRinging = false;
        this.visitorOverlay = null;
      }, 8000);

      return data;
    } catch (e) {
      this.isDoorbellRinging = false;
      return { ok: false, error: e.message };
    }
  }

  setNightVision(enabled) {
    this.isNightVision = !!enabled;
  }

  // =========================================================================
  // VIEW MODE SWITCHERS & MASTER ACTIONS
  // =========================================================================
  bindHeaderControls() {
    const modeBtns = document.querySelectorAll(".fp-mode-btn");
    modeBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const mode = btn.dataset.mode;
        if (!mode) return;
        this.viewMode = mode;
        modeBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.audio.playHoverTick();
        this.renderZoneHud();
      });
    });

    const allLightsBtn = document.getElementById("fpAllLightsBtn");
    if (allLightsBtn) {
      allLightsBtn.addEventListener("click", async () => {
        const rooms = ["living_room", "master_bedroom", "kitchen", "entryway"];
        // Check if any lights are on
        let anyOn = false;
        rooms.forEach(r => {
          const st = this.getRoomState(r);
          if (st?.lights?.on) anyOn = true;
        });

        const targetOn = !anyOn;
        this.audio.playToggle(targetOn);
        for (const r of rooms) {
          await this.updateDevice(r, "lights", { on: targetOn, bri: targetOn ? 80 : 0 });
        }
      });
    }
  }

  // =========================================================================
  // TACTILE INTERACTIVE ZONE HUD DOCK
  // =========================================================================
  renderZoneHud() {
    if (!this.fpZoneHud) return;

    const focusedKey = this.hoveredRoomKey || this.selectedRoomKey;

    if (!focusedKey) {
      // Idle Overview Bar
      const isLocked = (this.state?.entryway?.lock?.front_door ?? "locked") === "locked";
      const totalPower = this.state?.energy?.current_draw_kw || "1.1";
      this.fpZoneHud.innerHTML = `
        <div class="hud-idle-bar">
          <div class="hud-idle-tag">
            <span style="color:var(--cyan);">🏠</span>
            <strong>Hearth Spatial Twin</strong> · 4 Active Zones ·
            <span style="color:${isLocked ? 'var(--emerald)' : 'var(--rose)'};">${isLocked ? '🔒 Perimeter Armed' : '🔓 Front Door Unlocked'}</span> ·
            <span style="color:var(--amber);">${totalPower} kW Net</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:var(--text-dim);font-size:11px;font-family:var(--font-mono);">Touch any zone to inspect & command</span>
          </div>
        </div>
      `;
      return;
    }

    const room = this.rooms[focusedKey];
    if (!room) return;

    const st = this.getRoomState(focusedKey);
    const lightsOn = st ? st.lights?.on ?? false : true;
    const bri = st ? (st.lights?.bri ?? 60) : 60;
    const cct = st ? st.lights?.color_temp || "2700K" : "2700K";
    const currentTemp = st?.climate?.current_c ?? room.baseTemp;
    const targetTemp = st?.climate?.target_c ?? room.baseTemp;
    const isLocked = (this.state?.entryway?.lock?.front_door ?? "locked") === "locked";

    let occupantHtml = `<span class="hud-occupant-tag" style="background:rgba(255,255,255,0.04);color:var(--text-muted);border-color:var(--border-subtle);">👤 Vacant</span>`;
    if (room.occupant) {
      occupantHtml = `<span class="hud-occupant-tag">👤 ${room.occupant.name} · ${room.occupant.status}</span>`;
    }

    let extraControls = "";
    if (focusedKey === "entryway") {
      extraControls = `
        <button class="hud-btn-tactile lock-btn ${isLocked ? '' : 'unlocked'}" id="hudToggleLockBtn" title="Toggle Perimeter Deadbolt Lock">
          <span>${isLocked ? '🔒' : '🔓'}</span>
          <span>${isLocked ? 'LOCKED' : 'UNLOCKED'}</span>
        </button>
      `;
    }

    this.fpZoneHud.innerHTML = `
      <div class="hud-identity-cluster">
        <div class="hud-room-badge">
          <span>${room.icon}</span>
          <span>${room.name}</span>
          <span style="color:var(--text-dim);font-weight:400;font-size:11px;">(${room.area})</span>
        </div>
        <div class="hud-telemetry-tag">
          🌡️ ${currentTemp.toFixed(1)}°C <span style="color:var(--text-dim);">(Target: ${targetTemp.toFixed(1)}°C)</span>
        </div>
        ${occupantHtml}
      </div>

      <div class="hud-controls-cluster">
        <!-- Light Power Toggle -->
        <button class="hud-btn-tactile ${lightsOn ? 'active' : ''}" id="hudLightToggleBtn" title="Toggle Zone Lighting">
          <span>💡</span>
          <span>${lightsOn ? `${bri}% ON` : 'OFF'}</span>
        </button>

        <!-- Brightness Presets -->
        <div class="hud-bri-pill-group" title="Set brightness level">
          <button class="hud-bri-step ${lightsOn && bri <= 25 ? 'active' : ''}" data-bri="20">20%</button>
          <button class="hud-bri-step ${lightsOn && bri > 25 && bri <= 60 ? 'active' : ''}" data-bri="50">50%</button>
          <button class="hud-bri-step ${lightsOn && bri > 60 && bri <= 85 ? 'active' : ''}" data-bri="80">80%</button>
          <button class="hud-bri-step ${lightsOn && bri > 85 ? 'active' : ''}" data-bri="100">100%</button>
        </div>

        <!-- Micro-Climate Nudge -->
        <button class="hud-btn-tactile" id="hudTempDownBtn" title="Decrease Target Temp by 0.5°C">
          <span>− 0.5°</span>
        </button>
        <button class="hud-btn-tactile" id="hudTempUpBtn" title="Increase Target Temp by 0.5°C">
          <span>+ 0.5°</span>
        </button>

        <!-- CCT Quick Mood -->
        <button class="hud-btn-tactile glow-amber" id="hudWarmMoodBtn" title="Set Warm 2700K Amber">
          <span>🌙 Warm</span>
        </button>

        ${extraControls}
      </div>
    `;

    // Bind HUD buttons
    const lightToggleBtn = document.getElementById("hudLightToggleBtn");
    if (lightToggleBtn) {
      lightToggleBtn.addEventListener("click", () => {
        this.audio.playToggle(!lightsOn);
        this.updateDevice(room.stateKey, "lights", { on: !lightsOn });
      });
    }

    const briSteps = this.fpZoneHud.querySelectorAll(".hud-bri-step");
    briSteps.forEach(btn => {
      btn.addEventListener("click", () => {
        const val = parseInt(btn.dataset.bri, 10) || 50;
        this.audio.playHoverTick();
        this.updateDevice(room.stateKey, "lights", { on: true, bri: val });
      });
    });

    const tempDown = document.getElementById("hudTempDownBtn");
    if (tempDown) {
      tempDown.addEventListener("click", () => {
        this.audio.playTempStep();
        const nextTemp = Math.round((targetTemp - 0.5) * 10) / 10;
        this.updateDevice(room.stateKey, "climate", { target_c: nextTemp });
      });
    }

    const tempUp = document.getElementById("hudTempUpBtn");
    if (tempUp) {
      tempUp.addEventListener("click", () => {
        this.audio.playTempStep();
        const nextTemp = Math.round((targetTemp + 0.5) * 10) / 10;
        this.updateDevice(room.stateKey, "climate", { target_c: nextTemp });
      });
    }

    const warmBtn = document.getElementById("hudWarmMoodBtn");
    if (warmBtn) {
      warmBtn.addEventListener("click", () => {
        this.audio.playHoverTick();
        this.updateDevice(room.stateKey, "lights", { on: true, color_temp: "warm", hex: "#ffb366" });
      });
    }

    const lockBtn = document.getElementById("hudToggleLockBtn");
    if (lockBtn) {
      lockBtn.addEventListener("click", () => {
        const nextLocked = !isLocked;
        this.audio.playLock(nextLocked);
        this.toggleLock("front_door", nextLocked);
      });
    }
  }

  // =========================================================================
  // ARCHITECTURAL 2.5D VECTOR CANVAS RENDERING ENGINE
  // =========================================================================
  initFloorplanCanvas() {
    if (!this.fpCanvas || !this.fpCtx) return;

    const canvas = this.fpCanvas;
    const ctx = this.fpCtx;

    // Coordinate translation helper (client coordinates -> virtual 920x380)
    const getVirtualCoords = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect();
      const vx = ((clientX - rect.left) / rect.width) * this.virtualW;
      const vy = ((clientY - rect.top) / rect.height) * this.virtualH;
      return { vx, vy };
    };

    // Hit test room
    const hitTestRoom = (vx, vy) => {
      for (const [key, r] of Object.entries(this.rooms)) {
        if (vx >= r.x && vx <= r.x + r.w && vy >= r.y && vy <= r.y + r.h) {
          return key;
        }
      }
      return null;
    };

    // Hit test interactive elements inside rooms (Smart Lock, Light Fixture, Occupants)
    const hitTestHotspot = (vx, vy) => {
      // 1. Entryway smart lock cylinder
      const lockX = 735;
      const lockY = 295;
      if (Math.hypot(vx - lockX, vy - lockY) < 22) {
        return { type: "lock", room: "entryway" };
      }

      // 2. Light fixtures
      for (const [key, r] of Object.entries(this.rooms)) {
        if (Math.hypot(vx - r.lightPos.x, vy - r.lightPos.y) < 18) {
          return { type: "light_fixture", room: key };
        }
      }

      // 3. Occupants
      for (const [key, r] of Object.entries(this.rooms)) {
        if (r.occupant && Math.hypot(vx - r.occupant.pos.x, vy - r.occupant.pos.y) < 20) {
          return { type: "occupant", room: key, occupant: r.occupant };
        }
      }

      // 4. Ring porch camera
      if (Math.hypot(vx - 795, vy - 265) < 18) {
        return { type: "ring_cam", room: "entryway" };
      }

      return null;
    };

    // Mouse interactions
    canvas.addEventListener("mousemove", (e) => {
      const { vx, vy } = getVirtualCoords(e.clientX, e.clientY);
      const roomKey = hitTestRoom(vx, vy);
      const hotspot = hitTestHotspot(vx, vy);

      this.hoveredInteractiveElement = hotspot;

      if (roomKey !== this.hoveredRoomKey) {
        this.hoveredRoomKey = roomKey;
        if (roomKey) this.audio.playHoverTick();
        this.renderZoneHud();
      }

      // Cursor feedback
      if (hotspot || roomKey) {
        canvas.style.cursor = "pointer";
      } else {
        canvas.style.cursor = "crosshair";
      }
    });

    canvas.addEventListener("mouseleave", () => {
      this.hoveredRoomKey = null;
      this.hoveredInteractiveElement = null;
      this.renderZoneHud();
    });

    canvas.addEventListener("click", (e) => {
      const { vx, vy } = getVirtualCoords(e.clientX, e.clientY);
      const hotspot = hitTestHotspot(vx, vy);
      const roomKey = hitTestRoom(vx, vy);

      if (hotspot) {
        if (hotspot.type === "lock") {
          const isLocked = (this.state?.entryway?.lock?.front_door ?? "locked") === "locked";
          this.audio.playLock(!isLocked);
          this.toggleLock("front_door", !isLocked);
          return;
        }
        if (hotspot.type === "light_fixture") {
          const rKey = hotspot.room;
          const st = this.getRoomState(rKey);
          const currentOn = st?.lights?.on ?? true;
          this.audio.playToggle(!currentOn);
          this.updateDevice(this.rooms[rKey].stateKey, "lights", { on: !currentOn });
          return;
        }
        if (hotspot.type === "ring_cam") {
          this.triggerRingEvent("doorbell_press", "Front Porch Courier");
          return;
        }
      }

      if (roomKey) {
        this.selectedRoomKey = (this.selectedRoomKey === roomKey) ? null : roomKey;
        const rKey = roomKey;
        const st = this.getRoomState(rKey);
        const currentOn = st?.lights?.on ?? true;
        this.audio.playToggle(!currentOn);
        this.updateDevice(this.rooms[rKey].stateKey, "lights", { on: !currentOn });
        this.renderZoneHud();
      }
    });

    // Touch support for Echo Show 15/21 and mobile tablets
    canvas.addEventListener("touchstart", (e) => {
      if (!e.touches.length) return;
      const touch = e.touches[0];
      const { vx, vy } = getVirtualCoords(touch.clientX, touch.clientY);
      const roomKey = hitTestRoom(vx, vy);
      if (roomKey) {
        this.hoveredRoomKey = roomKey;
        this.selectedRoomKey = roomKey;
        this.renderZoneHud();
      }
    }, { passive: true });

    // Render loop
    let lastTime = performance.now();

    const render = (time) => {
      const dt = Math.min((time - lastTime) / 1000, 0.1);
      lastTime = time;
      this.tickCount++;

      // HiDPI / Retina responsive canvas scaling
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const targetPixelW = Math.max(Math.round(rect.width * dpr), 320);
      const targetPixelH = Math.max(Math.round(rect.height * dpr), 140);

      if (canvas.width !== targetPixelW || canvas.height !== targetPixelH) {
        canvas.width = targetPixelW;
        canvas.height = targetPixelH;
      }

      ctx.save();
      // Scale virtual coordinates (920x380) to physical canvas pixels
      ctx.scale(canvas.width / this.virtualW, canvas.height / this.virtualH);

      // 1. Clean blueprint backdrop & coordinate space
      this.drawBlueprintBackdrop(ctx);

      // 2. Central Gallery Corridor & navigation floor lights
      this.drawGalleryCorridor(ctx);

      // 3. Elevated 2.5D Room Floor Plates with Material Finishes
      this.drawRoomFloorSlabs(ctx, dt);

      // 4. Dynamic Photometric Radiance Pools
      if (this.viewMode === "radiance" || this.viewMode === "security") {
        this.drawPhotometricLighting(ctx, dt);
      }

      // 5. Thermal Micro-Climate Heatmaps & HVAC laminar flow
      if (this.viewMode === "thermal") {
        this.drawThermalHeatmaps(ctx, dt);
      }

      // 6. Architectural Load-Bearing Walls, Door Swings & Glazed Windows
      this.drawArchitecturalWalls(ctx);

      // 7. Minimalist CAD Architectural Furniture Silhouettes
      this.drawFurnitureCAD(ctx);

      // 8. Perimeter Security, Ring Radar Cone & Smart Deadbolt
      this.drawPerimeterAndSensors(ctx, dt);

      // 9. Family Occupant Radar Avatars
      this.drawOccupantAvatars(ctx);

      // 10. Room Header Badges & Micro-Telemetry Stamps
      this.drawRoomBadges(ctx);

      ctx.restore();
      requestAnimationFrame(render);
    };

    requestAnimationFrame(render);
  }

  // =========================================================================
  // BLUEPRINT BACKDROP & TECHNICAL CAD GRID
  // =========================================================================
  drawBlueprintBackdrop(ctx) {
    const w = this.virtualW;
    const h = this.virtualH;

    // Atmospheric deep luxury graphite-obsidian gradient
    const bgGrad = ctx.createLinearGradient(0, 0, w, h);
    bgGrad.addColorStop(0, "#080a11");
    bgGrad.addColorStop(0.5, "#0a0d17");
    bgGrad.addColorStop(1, "#07090e");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Minor CAD grid (20px pitch)
    ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 20; x < w; x += 20) {
      ctx.moveTo(x, 0); ctx.lineTo(x, h);
    }
    for (let y = 20; y < h; y += 20) {
      ctx.moveTo(0, y); ctx.lineTo(w, y);
    }
    ctx.stroke();

    // Major structural grid (60px pitch)
    ctx.strokeStyle = "rgba(56, 189, 248, 0.035)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 60; x < w; x += 60) {
      ctx.moveTo(x, 0); ctx.lineTo(x, h);
    }
    for (let y = 60; y < h; y += 60) {
      ctx.moveTo(0, y); ctx.lineTo(w, y);
    }
    ctx.stroke();

    // Blueprint border registration frame & corner alignment crosses (+)
    ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
    ctx.lineWidth = 1;
    ctx.strokeRect(15, 15, w - 30, h - 30);

    const drawCross = (cx, cy) => {
      ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx - 5, cy); ctx.lineTo(cx + 5, cy);
      ctx.moveTo(cx, cy - 5); ctx.lineTo(cx, cy + 5);
      ctx.stroke();
    };
    drawCross(15, 15);
    drawCross(w - 15, 15);
    drawCross(15, h - 15);
    drawCross(w - 15, h - 15);

    // Metric coordinate ruler ticks along top edge
    ctx.font = "8px monospace";
    ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
    const scaleTicks = [
      { x: 35, label: "0.0m" },
      { x: 240, label: "3.5m" },
      { x: 445, label: "7.0m" },
      { x: 675, label: "10.5m" },
      { x: 885, label: "14.0m" }
    ];
    scaleTicks.forEach(st => {
      ctx.beginPath();
      ctx.moveTo(st.x, 15); ctx.lineTo(st.x, 19);
      ctx.stroke();
      ctx.fillText(st.label, st.x - 10, 12);
    });

    // Blueprint title block stamp in top-left
    ctx.font = "bold 8.5px monospace";
    ctx.fillStyle = "rgba(56, 189, 248, 0.5)";
    ctx.fillText("HEARTH RESIDENTIAL DIGITAL TWIN · SPATIAL 2.5D BLUEPRINT · SCALE 1:50", 40, 21);

    // Minimalist Compass Rose / North Arrow in top-right
    const nx = w - 45;
    const ny = 20;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
    ctx.beginPath();
    ctx.moveTo(nx, ny + 8); ctx.lineTo(nx, ny - 6);
    ctx.lineTo(nx + 3, ny - 2); ctx.lineTo(nx - 3, ny - 2);
    ctx.stroke();
    ctx.font = "bold 8px monospace";
    ctx.fillStyle = "#38bdf8";
    ctx.fillText("N", nx + 5, ny - 3);
  }

  // =========================================================================
  // CENTRAL GALLERY CORRIDOR & NAVIGATION UPLIGHTS
  // =========================================================================
  drawGalleryCorridor(ctx) {
    const cx = 445;
    const cw = 20;
    const cy = 25;
    const ch = 325;

    // Subtle dark corridor base
    ctx.fillStyle = "rgba(255, 255, 255, 0.015)";
    ctx.fillRect(cx, cy, cw, ch);

    // Corridor dashed center axis line
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 6]);
    ctx.beginPath();
    ctx.moveTo(cx + cw / 2, cy + 10);
    ctx.lineTo(cx + cw / 2, cy + ch - 10);
    ctx.stroke();
    ctx.setLineDash([]);

    // Recessed floor path lights (subtle warm orientation dots)
    for (let y = cy + 30; y < cy + ch - 20; y += 45) {
      ctx.fillStyle = "rgba(251, 191, 36, 0.25)";
      ctx.beginPath();
      ctx.arc(cx + cw / 2, y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // =========================================================================
  // ELEVATED 2.5D ROOM FLOOR PLATES & ARCHITECTURAL MATERIALS
  // =========================================================================
  drawRoomFloorSlabs(ctx, dt) {
    for (const [key, r] of Object.entries(this.rooms)) {
      const isHovered = this.hoveredRoomKey === key || this.selectedRoomKey === key;
      const anim = this.animState[key];
      // Smooth hover factor lerp
      anim.hover += ((isHovered ? 1 : 0) - anim.hover) * 0.15;

      // 1. 2.5D Elevated Ambient Occlusion Shadow
      ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
      ctx.fillRect(r.x + 3, r.y + 4, r.w, r.h);

      // 2. Base Floor Slab Fill
      ctx.fillStyle = isHovered ? "rgba(18, 24, 38, 0.95)" : "rgba(13, 17, 27, 0.92)";
      ctx.fillRect(r.x, r.y, r.w, r.h);

      // 3. Room-Specific Architectural Textures
      ctx.save();
      ctx.beginPath();
      ctx.rect(r.x, r.y, r.w, r.h);
      ctx.clip();

      if (key === "living_room") {
        // Wide engineered hardwood planks (horizontal grain lines)
        ctx.strokeStyle = "rgba(255, 255, 255, 0.016)";
        ctx.lineWidth = 1;
        for (let py = r.y + 18; py < r.y + r.h; py += 18) {
          ctx.beginPath();
          ctx.moveTo(r.x, py); ctx.lineTo(r.x + r.w, py);
          ctx.stroke();
        }
      } else if (key === "kitchen") {
        // Large format 26px porcelain tile grid
        ctx.strokeStyle = "rgba(255, 255, 255, 0.022)";
        ctx.lineWidth = 1;
        for (let px = r.x + 26; px < r.x + r.w; px += 26) {
          ctx.beginPath();
          ctx.moveTo(px, r.y); ctx.lineTo(px, r.y + r.h);
          ctx.stroke();
        }
        for (let py = r.y + 26; py < r.y + r.h; py += 26) {
          ctx.beginPath();
          ctx.moveTo(r.x, py); ctx.lineTo(r.x + r.w, py);
          ctx.stroke();
        }
      } else if (key === "bedroom") {
        // Acoustic loop carpet cross-hatch stippling
        ctx.strokeStyle = "rgba(255, 255, 255, 0.014)";
        ctx.lineWidth = 1;
        for (let d = -r.h; d < r.w; d += 22) {
          ctx.beginPath();
          ctx.moveTo(r.x + d, r.y);
          ctx.lineTo(r.x + d + 30, r.y + r.h);
          ctx.stroke();
        }
      } else if (key === "entryway") {
        // Exterior cedar porch decking (vertical wood slats on right side)
        const porchStartX = r.x + 250;
        ctx.fillStyle = "rgba(180, 130, 80, 0.04)";
        ctx.fillRect(porchStartX, r.y, r.w - 250, r.h);

        ctx.strokeStyle = "rgba(255, 255, 255, 0.035)";
        ctx.lineWidth = 1;
        for (let px = porchStartX + 12; px < r.x + r.w; px += 14) {
          ctx.beginPath();
          ctx.moveTo(px, r.y); ctx.lineTo(px, r.y + r.h);
          ctx.stroke();
        }
      }
      ctx.restore();

      // 4. Subtle inner slab rim highlight
      ctx.strokeStyle = isHovered ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.05)";
      ctx.lineWidth = 1;
      ctx.strokeRect(r.x + 1, r.y + 1, r.w - 2, r.h - 2);
    }
  }

  // =========================================================================
  // DYNAMIC PHOTOMETRIC LIGHTING ENGINE (AMBIENT RADIANCE POOLS)
  // =========================================================================
  drawPhotometricLighting(ctx, dt) {
    for (const [key, r] of Object.entries(this.rooms)) {
      const roomState = this.getRoomState(key);
      const lights = roomState ? roomState.lights : { on: true, bri: 60 };
      const parsed = this.parseLightColor(lights);

      const anim = this.animState[key];
      // Smooth 60fps delta-time lerping towards target state
      anim.bri += (parsed.bri - anim.bri) * 0.1;
      anim.r += (parsed.r - anim.r) * 0.1;
      anim.g += (parsed.g - anim.g) * 0.1;
      anim.b += (parsed.b - anim.b) * 0.1;

      const targetRad = (anim.bri / 100) * (r.w * 0.55);
      anim.rad += (targetRad - anim.rad) * 0.1;

      if (anim.bri > 1 && anim.rad > 5) {
        // Living photon micro-breathing (0.5% organic drift)
        const shimmer = Math.sin(this.tickCount * 0.04 + r.x) * 0.02;
        const currentRad = Math.max(anim.rad * (1 + shimmer), 8);
        const intensity = (anim.bri / 100);

        ctx.save();
        ctx.beginPath();
        ctx.rect(r.x, r.y, r.w, r.h);
        ctx.clip();

        // Multi-stop radial dispersion gradient
        const radGrad = ctx.createRadialGradient(
          r.lightPos.x, r.lightPos.y, 4,
          r.lightPos.x, r.lightPos.y, currentRad
        );

        const cr = Math.round(anim.r);
        const cg = Math.round(anim.g);
        const cb = Math.round(anim.b);

        radGrad.addColorStop(0, `rgba(255, 255, 255, ${0.75 * intensity})`);
        radGrad.addColorStop(0.12, `rgba(${cr}, ${cg}, ${cb}, ${0.45 * intensity})`);
        radGrad.addColorStop(0.45, `rgba(${cr}, ${cg}, ${cb}, ${0.2 * intensity})`);
        radGrad.addColorStop(0.8, `rgba(${cr}, ${cg}, ${cb}, ${0.05 * intensity})`);
        radGrad.addColorStop(1, "transparent");

        ctx.fillStyle = radGrad;
        ctx.fillRect(r.x, r.y, r.w, r.h);
        ctx.restore();
      }

      // Architectural Recessed Downlight Fixture
      ctx.fillStyle = "rgba(30, 41, 59, 0.9)";
      ctx.beginPath();
      ctx.arc(r.lightPos.x, r.lightPos.y, 6, 0, Math.PI * 2);
      ctx.fill();

      // Outer bezel ring
      ctx.strokeStyle = anim.bri > 5 ? `rgb(${Math.round(anim.r)}, ${Math.round(anim.g)}, ${Math.round(anim.b)})` : "rgba(255, 255, 255, 0.2)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Diode center core
      ctx.fillStyle = anim.bri > 5 ? "#ffffff" : "rgba(255, 255, 255, 0.35)";
      ctx.beginPath();
      ctx.arc(r.lightPos.x, r.lightPos.y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // =========================================================================
  // THERMAL MICRO-CLIMATE HEATMAPS & HVAC LAMINAR AIRFLOW
  // =========================================================================
  drawThermalHeatmaps(ctx, dt) {
    for (const [key, r] of Object.entries(this.rooms)) {
      const roomState = this.getRoomState(key);
      const temp = roomState?.climate?.current_c ?? r.baseTemp;

      ctx.save();
      ctx.beginPath();
      ctx.rect(r.x, r.y, r.w, r.h);
      ctx.clip();

      // Temperature chromatic mapping: Cool (<20°C: Indigo/Cyan) · Balance (20-21.5°C: Emerald) · Warm (>21.5°C: Amber)
      let tGrad = ctx.createRadialGradient(r.x + r.w / 2, r.y + r.h / 2, 10, r.x + r.w / 2, r.y + r.h / 2, r.w * 0.6);
      if (temp < 20.0) {
        tGrad.addColorStop(0, "rgba(56, 189, 248, 0.25)");
        tGrad.addColorStop(0.7, "rgba(99, 102, 241, 0.12)");
        tGrad.addColorStop(1, "transparent");
      } else if (temp <= 21.5) {
        tGrad.addColorStop(0, "rgba(16, 185, 129, 0.22)");
        tGrad.addColorStop(0.7, "rgba(6, 182, 212, 0.1)");
        tGrad.addColorStop(1, "transparent");
      } else {
        tGrad.addColorStop(0, "rgba(245, 158, 11, 0.25)");
        tGrad.addColorStop(0.7, "rgba(239, 68, 68, 0.1)");
        tGrad.addColorStop(1, "transparent");
      }
      ctx.fillStyle = tGrad;
      ctx.fillRect(r.x, r.y, r.w, r.h);

      // HVAC Ceiling Diffuser Vent
      const vx = r.x + r.w - 40;
      const vy = r.y + 45;
      ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
      ctx.lineWidth = 1;
      ctx.strokeRect(vx - 10, vy - 10, 20, 20);
      ctx.beginPath();
      ctx.moveTo(vx - 6, vy); ctx.lineTo(vx + 6, vy);
      ctx.moveTo(vx, vy - 6); ctx.lineTo(vx, vy + 6);
      ctx.stroke();

      ctx.restore();
    }

    // Drifting conditioned airflow micro-particles
    ctx.fillStyle = "rgba(56, 189, 248, 0.4)";
    this.hvacParticles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 35) p.x = 445;
      if (p.x > 885) p.x = 465;
      if (p.y < 25) p.y = 350;
      if (p.y > 350) p.y = 25;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // =========================================================================
  // ARCHITECTURAL WALLS, DOOR SWINGS & GLAZED WINDOWS
  // =========================================================================
  drawArchitecturalWalls(ctx) {
    // 1. Room Boundary Strokes
    for (const [key, r] of Object.entries(this.rooms)) {
      const isHovered = this.hoveredRoomKey === key || this.selectedRoomKey === key;
      ctx.strokeStyle = isHovered ? "rgba(6, 182, 212, 0.85)" : "rgba(255, 255, 255, 0.16)";
      ctx.lineWidth = isHovered ? 2 : 1.5;
      ctx.strokeRect(r.x, r.y, r.w, r.h);
    }

    // 2. Heavy Structural Load-Bearing Perimeter Walls (6px outer wall thickness)
    ctx.strokeStyle = "rgba(59, 130, 246, 0.45)";
    ctx.lineWidth = 2.5;

    // West exterior wall
    ctx.beginPath();
    ctx.moveTo(35, 25); ctx.lineTo(35, 350);
    // North exterior wall
    ctx.moveTo(35, 25); ctx.lineTo(445, 25);
    ctx.moveTo(465, 25); ctx.lineTo(885, 25);
    // East exterior wall
    ctx.moveTo(885, 25); ctx.lineTo(885, 350);
    // South exterior wall
    ctx.moveTo(35, 350); ctx.lineTo(445, 350);
    ctx.moveTo(465, 350); ctx.lineTo(885, 350);
    ctx.stroke();

    // 3. Double-Pane Glazed Windows with subtle cyan light sheen
    const drawWindow = (x, y, w, h) => {
      ctx.fillStyle = "rgba(56, 189, 248, 0.15)";
      ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(x, y, w, h);
      // Double pane inner line
      ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
      ctx.lineWidth = 1;
      if (w > h) {
        ctx.beginPath();
        ctx.moveTo(x, y + h / 2); ctx.lineTo(x + w, y + h / 2);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(x + w / 2, y); ctx.lineTo(x + w / 2, y + h);
        ctx.stroke();
      }
    };

    // Kitchen North Window
    drawWindow(120, 23, 70, 4);
    // Master Bedroom East Window
    drawWindow(883, 60, 4, 75);
    // Living Room Balcony Sliding Doors (West Wall)
    drawWindow(33, 220, 4, 80);

    // 4. Vector Architectural Door Swings (Dashed 90° arc + door leaf)
    const drawDoorSwing = (hingeX, hingeY, radius, startAngle, endAngle, leafAngle) => {
      // Dashed swing arc
      ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.arc(hingeX, hingeY, radius, startAngle, endAngle);
      ctx.stroke();
      ctx.setLineDash([]);

      // Door Leaf
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(hingeX, hingeY);
      ctx.lineTo(hingeX + Math.cos(leafAngle) * radius, hingeY + Math.sin(leafAngle) * radius);
      ctx.stroke();
    };

    // Master Bedroom Door (hinge on corridor wall at 465, 175)
    drawDoorSwing(465, 175, 34, -Math.PI / 2, 0, -Math.PI / 4);

    // Front Entry Door (hinge at 720, 275)
    drawDoorSwing(720, 275, 36, -Math.PI / 2, 0, -Math.PI / 4);
  }

  // =========================================================================
  // DETAILED MINIMALIST CAD FURNITURE SILHOUETTES
  // =========================================================================
  drawFurnitureCAD(ctx) {
    ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
    ctx.lineWidth = 1;

    // --- LIVING ROOM ---
    // 1. L-Shaped Sectional Sofa
    ctx.fillStyle = "rgba(255, 255, 255, 0.035)";
    // Main seating run
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(80, 275, 140, 50, 6) : ctx.rect(80, 275, 140, 50);
    ctx.fill();
    ctx.stroke();
    // Return chaise
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(80, 220, 50, 55, 6) : ctx.rect(80, 220, 50, 55);
    ctx.fill();
    ctx.stroke();

    // Sofa cushions detail
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.strokeRect(130, 280, 42, 40);
    ctx.strokeRect(172, 280, 42, 40);

    // 2. Walnut Coffee Table
    ctx.fillStyle = "rgba(245, 158, 11, 0.06)";
    ctx.strokeStyle = "rgba(245, 158, 11, 0.25)";
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(145, 235, 65, 30, 4) : ctx.rect(145, 235, 65, 30);
    ctx.fill();
    ctx.stroke();
    // Tabletop decorative art book
    ctx.fillStyle = "rgba(255, 255, 255, 0.15)";
    ctx.fillRect(160, 242, 14, 16);

    // 3. Wall-Mounted Fire TV OLED Screen & Floating Soundbar
    const isPlaying = this.state?.living_room?.media?.playing ?? true;
    const mediaTitle = this.state?.living_room?.media?.title || "Interstellar (4K HDR)";

    // Credenza
    ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.fillRect(150, 167, 120, 10);
    ctx.strokeRect(150, 167, 120, 10);

    // OLED Screen
    ctx.fillStyle = isPlaying ? "#06b6d4" : "rgba(255, 255, 255, 0.3)";
    ctx.fillRect(165, 165, 90, 3);

    // Dynamic Chromatic OLED Backglow when playing
    if (isPlaying) {
      const tvPulse = Math.sin(this.tickCount * 0.08) * 0.15 + 0.35;
      const tvGrad = ctx.createRadialGradient(210, 165, 2, 210, 165, 60);
      tvGrad.addColorStop(0, `rgba(6, 182, 212, ${tvPulse})`);
      tvGrad.addColorStop(0.5, `rgba(168, 85, 247, ${tvPulse * 0.5})`);
      tvGrad.addColorStop(1, "transparent");
      ctx.fillStyle = tvGrad;
      ctx.fillRect(140, 155, 140, 45);

      // Mini audio equalizer bars above credenza
      for (let i = 0; i < 4; i++) {
        const barH = Math.abs(Math.sin(this.tickCount * 0.1 + i * 0.8)) * 8 + 3;
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(200 + i * 6, 182 - barH, 3, barH);
      }
    }

    // 4. Corner Architectural Potted Plant (Fiddle-Leaf Fig)
    ctx.fillStyle = "rgba(16, 185, 129, 0.18)";
    ctx.strokeStyle = "rgba(16, 185, 129, 0.5)";
    ctx.beginPath();
    ctx.arc(55, 185, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // --- KITCHEN & DINING ---
    // 1. Gourmet Waterfall Marble Island
    ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(160, 68, 140, 44, 4) : ctx.rect(160, 68, 140, 44);
    ctx.fill();
    ctx.stroke();

    // 3 Circular Barstools
    [185, 230, 275].forEach(bx => {
      ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
      ctx.beginPath();
      ctx.arc(bx, 122, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });

    // 2. North Wall Induction Cooktop
    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
    ctx.strokeRect(95, 27, 45, 22);
    // 4 concentric cooking rings
    [105, 125].forEach(rx => {
      [33, 43].forEach(ry => {
        ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
        ctx.beginPath();
        ctx.arc(rx, ry, 3.5, 0, Math.PI * 2);
        ctx.stroke();
      });
    });

    // 3. Undermount Double Sink & Gooseneck Faucet
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.strokeRect(210, 27, 20, 20);
    ctx.strokeRect(232, 27, 20, 20);

    // 4. Dining Table with 4 Chairs
    ctx.fillStyle = "rgba(255, 255, 255, 0.03)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
    ctx.fillRect(345, 62, 70, 48);
    ctx.strokeRect(345, 62, 70, 48);
    // Chairs
    ctx.strokeRect(355, 52, 20, 8);
    ctx.strokeRect(385, 52, 20, 8);
    ctx.strokeRect(355, 112, 20, 8);
    ctx.strokeRect(385, 112, 20, 8);

    // --- MASTER BEDROOM ---
    // 1. King-Size Platform Bed
    // Headboard against north wall
    ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
    ctx.fillRect(605, 30, 130, 8);
    // Mattress
    ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(610, 38, 120, 95, 6) : ctx.rect(610, 38, 120, 95);
    ctx.fill();
    ctx.stroke();
    // Pillows
    ctx.fillStyle = "rgba(255, 255, 255, 0.15)";
    ctx.fillRect(620, 44, 40, 20);
    ctx.fillRect(680, 44, 40, 20);
    // Folded duvet line
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.beginPath();
    ctx.moveTo(610, 85); ctx.lineTo(730, 85);
    ctx.stroke();

    // Floating Nightstands & Bedside Sconces
    [580, 735].forEach((nx, idx) => {
      ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
      ctx.fillRect(nx, 40, 22, 22);
      ctx.strokeRect(nx, 40, 22, 22);
      // Bedside Sconce Dot
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath();
      ctx.arc(nx + 11, 51, 2, 0, Math.PI * 2);
      ctx.fill();
    });

    // Wardrobe closet along east wall
    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
    ctx.strokeRect(845, 35, 35, 110);
    ctx.setLineDash([2, 4]);
    ctx.beginPath();
    ctx.moveTo(862, 35); ctx.lineTo(862, 145);
    ctx.stroke();
    ctx.setLineDash([]);

    // --- ENTRYWAY & PORCH ---
    // Welcome Mat
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.fillRect(728, 270, 26, 32);
    ctx.strokeRect(728, 270, 26, 32);

    // Foyer credenza
    ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
    ctx.strokeRect(490, 318, 70, 16);
  }

  // =========================================================================
  // PERIMETER SECURITY, RING RADAR CONE & SMART DEADBOLT
  // =========================================================================
  drawPerimeterAndSensors(ctx, dt) {
    const isLocked = (this.state?.entryway?.lock?.front_door ?? "locked") === "locked";

    // 1. Ring Porch Cam Housing (Mounted beside front door)
    const camX = 795;
    const camY = 265;

    ctx.fillStyle = "#1e293b";
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(camX - 8, camY - 8, 16, 16, 4) : ctx.rect(camX - 8, camY - 8, 16, 16);
    ctx.fill();
    ctx.stroke();

    // Active Camera Blue LED Diode
    ctx.fillStyle = this.isDoorbellRinging ? "#ef4444" : "#38bdf8";
    ctx.beginPath();
    ctx.arc(camX, camY, 3, 0, Math.PI * 2);
    ctx.fill();

    // 2. Ring 140° Conical PIR Infrared Motion Radar Beam
    this.radarAngle += dt * 1.5;
    const coneRadius = 110;
    const startAngle = -0.45 * Math.PI;
    const endAngle = 0.45 * Math.PI;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(camX, camY);
    ctx.arc(camX, camY, coneRadius, startAngle, endAngle);
    ctx.closePath();

    if (this.isDoorbellRinging) {
      // Urgent Pulsing Red Warning Cone
      const ringPulse = Math.sin(this.tickCount * 0.2) * 0.2 + 0.3;
      ctx.fillStyle = `rgba(239, 68, 68, ${ringPulse})`;
    } else {
      // Soft Ambient Cyan Motion Detection Cone
      const coneGrad = ctx.createRadialGradient(camX, camY, 10, camX, camY, coneRadius);
      coneGrad.addColorStop(0, "rgba(56, 189, 248, 0.15)");
      coneGrad.addColorStop(0.7, "rgba(56, 189, 248, 0.04)");
      coneGrad.addColorStop(1, "transparent");
      ctx.fillStyle = coneGrad;
    }
    ctx.fill();

    // Radar distance range arcs (5ft, 15ft, 25ft)
    [35, 70, 105].forEach((dist, idx) => {
      ctx.strokeStyle = this.isDoorbellRinging ? "rgba(239, 68, 68, 0.5)" : "rgba(56, 189, 248, 0.18)";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.arc(camX, camY, dist, startAngle, endAngle);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Sweeping Radar Scan Ray
    const sweepAngle = startAngle + (Math.sin(this.radarAngle) * 0.5 + 0.5) * (endAngle - startAngle);
    ctx.strokeStyle = this.isDoorbellRinging ? "rgba(239, 68, 68, 0.8)" : "rgba(56, 189, 248, 0.6)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(camX, camY);
    ctx.lineTo(camX + Math.cos(sweepAngle) * coneRadius, camY + Math.sin(sweepAngle) * coneRadius);
    ctx.stroke();
    ctx.restore();

    // 3. Smart Deadbolt Lock Graphic (Clickable Interactive Token)
    const lockX = 735;
    const lockY = 295;
    const isHovered = this.hoveredInteractiveElement?.type === "lock";

    ctx.fillStyle = isLocked ? "rgba(16, 185, 129, 0.16)" : "rgba(239, 68, 68, 0.16)";
    ctx.strokeStyle = isLocked ? "#10b981" : "#ef4444";
    ctx.lineWidth = isHovered ? 2 : 1;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(lockX - 34, lockY - 11, 68, 22, 5) : ctx.rect(lockX - 34, lockY - 11, 68, 22);
    ctx.fill();
    ctx.stroke();

    ctx.font = "bold 9px monospace";
    ctx.fillStyle = isLocked ? "#34d399" : "#f87171";
    ctx.fillText(isLocked ? "🔒 SECURED" : "🔓 UNLOCKED", lockX - 28, lockY + 3);
  }

  // =========================================================================
  // FAMILY OCCUPANT RADAR AVATARS
  // =========================================================================
  drawOccupantAvatars(ctx) {
    for (const [key, r] of Object.entries(this.rooms)) {
      if (!r.occupant) continue;

      const ox = r.occupant.pos.x;
      const oy = r.occupant.pos.y;
      const pulse = Math.sin(this.tickCount * 0.05 + ox) * 4;

      // 1. Dual Concentric Acoustic Harmonic Radar Rings
      ctx.strokeStyle = "rgba(59, 130, 246, 0.35)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(ox, oy, 12 + pulse, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = "rgba(59, 130, 246, 0.15)";
      ctx.beginPath();
      ctx.arc(ox, oy, 18 + pulse * 1.5, 0, Math.PI * 2);
      ctx.stroke();

      // 2. Tactile Avatar Token (18px circular token with gradient)
      const tokenGrad = ctx.createLinearGradient(ox - 8, oy - 8, ox + 8, oy + 8);
      tokenGrad.addColorStop(0, "#3b82f6");
      tokenGrad.addColorStop(1, "#1d4ed8");
      ctx.fillStyle = tokenGrad;
      ctx.beginPath();
      ctx.arc(ox, oy, 8, 0, Math.PI * 2);
      ctx.fill();

      // Avatar Initial Letter
      ctx.font = "bold 9px -apple-system, sans-serif";
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(r.occupant.name.charAt(0), ox, oy);
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      // 3. Floating Glassmorphic Activity Status Pill
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect ? ctx.roundRect(ox - 32, oy - 22, 64, 14, 4) : ctx.rect(ox - 32, oy - 22, 64, 14);
      ctx.fill();
      ctx.stroke();

      ctx.font = "bold 8px monospace";
      ctx.fillStyle = "#93c5fd";
      ctx.fillText(`👤 ${r.occupant.name}`, ox - 26, oy - 12);
    }
  }

  // =========================================================================
  // ROOM BADGES & TELEMETRY STAMPS
  // =========================================================================
  drawRoomBadges(ctx) {
    for (const [key, r] of Object.entries(this.rooms)) {
      const isHovered = this.hoveredRoomKey === key || this.selectedRoomKey === key;
      const roomState = this.getRoomState(key);
      const lightsOn = roomState ? roomState.lights?.on : true;
      const bri = roomState ? (roomState.lights?.bri || 60) : 60;
      const temp = roomState ? (roomState.climate?.current_c || r.baseTemp) : r.baseTemp;

      // Room Title Badge
      ctx.font = "bold 11px -apple-system, sans-serif";
      ctx.fillStyle = isHovered ? "#38bdf8" : "#f1f5f9";
      ctx.fillText(`${r.icon} ${r.name.toUpperCase()}`, r.x + 14, r.y + 24);

      // Micro-climate Telemetry String
      ctx.font = "10px monospace";
      ctx.fillStyle = "rgba(255, 255, 255, 0.55)";
      ctx.fillText(`${temp.toFixed(1)}°C · ${lightsOn ? `${bri}% bri` : 'OFF'}`, r.x + 14, r.y + 38);
    }
  }

  // =========================================================================
  // RING 1080P PORCH CAM CANVAS SIMULATOR (WITH INFRARED NIGHT VISION)
  // =========================================================================
  initRingCameraCanvas() {
    if (!this.ringCanvas || !this.ringCtx) return;

    let frame = 0;
    const render = () => {
      frame++;
      const w = this.ringCanvas.width = this.ringCanvas.parentElement.clientWidth || 320;
      const h = this.ringCanvas.height = 120;

      if (this.isNightVision) {
        // Authentic 850nm Infrared Night Vision monochrome
        const bgGrad = this.ringCtx.createLinearGradient(0, 0, 0, h);
        bgGrad.addColorStop(0, "#051108");
        bgGrad.addColorStop(0.6, "#0a1f10");
        bgGrad.addColorStop(1, "#030a05");
        this.ringCtx.fillStyle = bgGrad;
        this.ringCtx.fillRect(0, 0, w, h);

        // IR noise grain
        this.ringCtx.fillStyle = "rgba(34, 197, 94, 0.04)";
        for (let i = 0; i < 40; i++) {
          this.ringCtx.fillRect(Math.random() * w, Math.random() * h, 2, 2);
        }

        // Night vision IR illuminator center hotspot
        const irGrad = this.ringCtx.createRadialGradient(w * 0.5, h * 0.5, 10, w * 0.5, h * 0.5, 120);
        irGrad.addColorStop(0, "rgba(34, 197, 94, 0.15)");
        irGrad.addColorStop(1, "transparent");
        this.ringCtx.fillStyle = irGrad;
        this.ringCtx.fillRect(0, 0, w, h);
      } else {
        // Dark daylight/dusk porch scene
        const bgGrad = this.ringCtx.createLinearGradient(0, 0, 0, h);
        bgGrad.addColorStop(0, "#0a1120");
        bgGrad.addColorStop(0.6, "#0f172a");
        bgGrad.addColorStop(1, "#050814");
        this.ringCtx.fillStyle = bgGrad;
        this.ringCtx.fillRect(0, 0, w, h);

        // Ambient porch lantern glow
        const lanternGrad = this.ringCtx.createRadialGradient(w * 0.22, h * 0.3, 2, w * 0.22, h * 0.3, 35);
        lanternGrad.addColorStop(0, "rgba(251, 191, 36, 0.75)");
        lanternGrad.addColorStop(0.3, "rgba(245, 158, 11, 0.25)");
        lanternGrad.addColorStop(1, "transparent");
        this.ringCtx.fillStyle = lanternGrad;
        this.ringCtx.fillRect(0, 0, w, h);
      }

      // Distant pathway & doorway perspective lines
      this.ringCtx.strokeStyle = this.isNightVision ? "rgba(34, 197, 94, 0.15)" : "rgba(255, 255, 255, 0.08)";
      this.ringCtx.lineWidth = 1;
      this.ringCtx.beginPath();
      this.ringCtx.moveTo(w * 0.35, h);
      this.ringCtx.lineTo(w * 0.46, h * 0.45);
      this.ringCtx.moveTo(w * 0.65, h);
      this.ringCtx.lineTo(w * 0.54, h * 0.45);
      this.ringCtx.stroke();

      // Foliage swaying in breeze
      this.ringCtx.fillStyle = this.isNightVision ? "rgba(34, 197, 94, 0.25)" : "rgba(16, 185, 129, 0.15)";
      this.ringCtx.beginPath();
      const sway = Math.sin(frame * 0.03) * 6;
      this.ringCtx.arc(w * 0.82 + sway, h * 0.65, 28, 0, Math.PI * 2);
      this.ringCtx.fill();

      // If Doorbell is ringing: flash motion bounding box
      if (this.isDoorbellRinging) {
        this.ringCtx.strokeStyle = "rgba(239, 68, 68, 0.85)";
        this.ringCtx.lineWidth = 2;
        this.ringCtx.strokeRect(w * 0.4 - 15, h * 0.28, 48, 62);

        // Visitor Silhouette outline
        this.ringCtx.fillStyle = "rgba(255, 255, 255, 0.2)";
        this.ringCtx.beginPath();
        this.ringCtx.arc(w * 0.4 + 9, h * 0.4, 9, 0, Math.PI * 2);
        this.ringCtx.rect(w * 0.4 - 2, h * 0.5, 22, 34);
        this.ringCtx.fill();

        // Visitor notification banner
        this.ringCtx.fillStyle = "rgba(239, 68, 68, 0.9)";
        this.ringCtx.fillRect(0, 0, w, 20);
        this.ringCtx.font = "bold 10px monospace";
        this.ringCtx.fillStyle = "#fff";
        this.ringCtx.fillText(`🔔 DOORBELL: ${this.visitorOverlay || "VISITOR DETECTED"}`, 8, 14);
      }

      // Camera HUD Overlay (Live timestamp and IR/Color mode)
      this.ringCtx.font = "9px monospace";
      this.ringCtx.fillStyle = this.isNightVision ? "rgba(34, 197, 94, 0.85)" : "rgba(255, 255, 255, 0.6)";
      const d = new Date();
      const mode = this.isNightVision ? "IR 850nm" : "COLOR HDR";
      const ts = `${d.toLocaleDateString()} ${d.toLocaleTimeString()} [${mode}]`;
      this.ringCtx.fillText(ts, 8, h - 8);

      requestAnimationFrame(render);
    };

    requestAnimationFrame(render);
  }
}
