/**
 * VOICE & ACOUSTIC ENGINE — HEARTH UNIVERSAL
 * 3D Kinetic Neural Astrolabe Orb · Alexa Fluid Light Glow Bar · Web Audio Chimes · Speech Recognition & TTS
 */

export class VoiceEngine {
  constructor(waveCanvasId = "alexaGlowCanvas", orbCanvasId = "orbCanvas") {
    this.canvas = document.getElementById(waveCanvasId);
    this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
    this.orbCanvas = document.getElementById(orbCanvasId);
    this.orbCtx = this.orbCanvas ? this.orbCanvas.getContext("2d") : null;

    this.audioCtx = null;
    this.soundEnabled = true;
    this.isListening = false;
    this.isSpeaking = false;
    this.recognition = null;
    this.wavePhase = 0;
    this.amplitude = 0.05;
    this.targetAmplitude = 0.05;

    // 3D Astrolabe Orb State
    this.orbState = "idle"; // 'idle' | 'listening' | 'thinking' | 'speaking'
    this.orbMouseX = 0;
    this.orbMouseY = 0;
    this.orbShockwave = 0;

    this.initAudioContext();
    this.initSpeechRecognition();
    this.initKineticOrb();
    this.startGlowRenderLoop();
  }

  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioCtx = new AudioCtx();
      }
    } catch (e) {
      console.warn("Web Audio API not supported", e);
    }
  }

  unlockAudio() {
    if (this.audioCtx && this.audioCtx.state === "suspended") {
      this.audioCtx.resume();
    }
  }

  toggleSound(enable = null) {
    this.soundEnabled = (enable !== null) ? enable : !this.soundEnabled;
    return this.soundEnabled;
  }

  setOrbState(state) {
    this.orbState = state;
    const pill = document.getElementById("orbStatusPill");
    const txt = document.getElementById("orbStatusText");
    if (pill) {
      pill.className = `orb-status-pill ${state}`;
    }
    if (txt) {
      switch (state) {
        case "listening":
          txt.textContent = "LISTENING · AWAITING SPEECH";
          this.targetAmplitude = 0.9;
          break;
        case "thinking":
          txt.textContent = "ORCHESTRATING DAG";
          this.targetAmplitude = 0.5;
          break;
        case "speaking":
          txt.textContent = "SPEAKING · AUDIO RESPONSE";
          this.targetAmplitude = 0.8;
          break;
        default:
          txt.textContent = "IDLE · AMBIENT SENSING";
          this.targetAmplitude = 0.05;
          break;
      }
    }
  }

  // Authentic procedural Echo acoustic activation ping
  playEchoPing() {
    if (!this.soundEnabled || !this.audioCtx) return;
    this.unlockAudio();
    const t = this.audioCtx.currentTime;

    // Dual-tone acoustic chime: C5 (523.25Hz) blending into E5 (659.25Hz)
    const osc1 = this.audioCtx.createOscillator();
    const osc2 = this.audioCtx.createOscillator();
    const gainNode = this.audioCtx.createGain();

    osc1.type = "sine";
    osc1.frequency.setValueAtTime(523.25, t);
    osc1.frequency.exponentialRampToValueAtTime(659.25, t + 0.12);

    osc2.type = "sine";
    osc2.frequency.setValueAtTime(659.25, t);

    gainNode.gain.setValueAtTime(0.001, t);
    gainNode.gain.linearRampToValueAtTime(0.2, t + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, t + 0.45);

    osc1.connect(gainNode);
    osc2.connect(gainNode);
    gainNode.connect(this.audioCtx.destination);

    osc1.start(t);
    osc2.start(t);
    osc1.stop(t + 0.5);
    osc2.stop(t + 0.5);
  }

  // Proposal Approval Confirmation Chime: Upward acoustic arpeggio
  playSuccessChime() {
    if (!this.soundEnabled || !this.audioCtx) return;
    this.unlockAudio();
    const notes = [587.33, 783.99, 1046.50]; // D5, G5, C6
    const now = this.audioCtx.currentTime;

    notes.forEach((freq, idx) => {
      const t = now + idx * 0.08;
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.001, t);
      gain.gain.linearRampToValueAtTime(0.18, t + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.35);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(t);
      osc.stop(t + 0.4);
    });
  }

  // Sentinel Block Alert Tone
  playWarningTone() {
    if (!this.soundEnabled || !this.audioCtx) return;
    this.unlockAudio();
    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(180, t);
    osc.frequency.linearRampToValueAtTime(140, t + 0.25);

    gain.gain.setValueAtTime(0.15, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.32);
  }

  // Authentic high-pitch retail barcode scanner beep (2200 Hz)
  playBarcodeBeep() {
    if (!this.soundEnabled || !this.audioCtx) return;
    this.unlockAudio();
    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(2200, t);

    gain.gain.setValueAtTime(0.001, t);
    gain.gain.linearRampToValueAtTime(0.15, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.1);
  }

  // Speech Recognition
  initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
      this.recognition = new SpeechRec();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = "en-US";
    }
  }

  listenOnce(onResult, onError) {
    if (!this.recognition) {
      if (onError) onError("Speech recognition not supported in this browser.");
      return;
    }
    this.unlockAudio();
    this.playEchoPing();
    this.isListening = true;
    this.setOrbState("listening");

    this.recognition.onresult = (evt) => {
      this.isListening = false;
      this.setOrbState("idle");
      const transcript = evt.results[0][0].transcript;
      if (onResult) onResult(transcript);
    };

    this.recognition.onerror = (err) => {
      this.isListening = false;
      this.setOrbState("idle");
      if (onError) onError(err.error || "Speech recognition error");
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (this.orbState === "listening") {
        this.setOrbState("idle");
      }
    };

    try {
      this.recognition.start();
    } catch (e) {
      this.isListening = false;
      this.setOrbState("idle");
    }
  }

  // Speech Synthesis (Alexa voice)
  speak(text) {
    if (!this.soundEnabled || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();

    // Strip code blocks and markdown symbols
    const cleanText = text
      .replace(/```[\s\S]*?```/g, "")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/[*_#~]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 1.02;

    const voices = window.speechSynthesis.getVoices();
    const alexaVoice = voices.find(v => 
      v.name.includes("Samantha") || v.name.includes("Victoria") || v.name.includes("Google US English") || (v.lang.startsWith("en") && !v.name.includes("Male"))
    ) || voices[0];
    
    if (alexaVoice) utterance.voice = alexaVoice;

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.setOrbState("speaking");
    };
    utterance.onend = () => {
      this.isSpeaking = false;
      this.setOrbState("idle");
    };
    utterance.onerror = () => {
      this.isSpeaking = false;
      this.setOrbState("idle");
    };

    window.speechSynthesis.speak(utterance);
  }

  // 3D KINETIC ASTROLABE NEURAL ORB ENGINE
  initKineticOrb() {
    const canvas = this.orbCanvas;
    if (!canvas || !this.orbCtx) return;
    const ctx = this.orbCtx;

    // Retina / Hi-DPI Scaling
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const displayW = 90;
    const displayH = 90;
    canvas.width = displayW * dpr;
    canvas.height = displayH * dpr;
    ctx.scale(dpr, dpr);

    const cx = displayW / 2;
    const cy = displayH / 2;

    let rotX = 0.3;
    let rotY = 0;
    let gimbalAngle1 = 0;
    let gimbalAngle2 = 0;
    let time = 0;

    // Generate 3D Spherical Lattice Coordinates
    const R = 28;
    const points = [];
    const rings = 6;
    const segments = 12;

    for (let i = 0; i <= rings; i++) {
      const theta = (i * Math.PI) / rings - Math.PI / 2;
      for (let j = 0; j < segments; j++) {
        const phi = (j * 2 * Math.PI) / segments;
        points.push({
          x: R * Math.cos(theta) * Math.cos(phi),
          y: R * Math.sin(theta),
          z: R * Math.cos(theta) * Math.sin(phi),
          ring: i,
          seg: j,
        });
      }
    }

    // Orbiting Particle Stars
    const orbiters = [];
    const ORBITER_COUNT = 8;
    for (let k = 0; k < ORBITER_COUNT; k++) {
      orbiters.push({
        orbitR: R + 8 + Math.random() * 8,
        speed: (0.015 + Math.random() * 0.02) * (Math.random() > 0.5 ? 1 : -1),
        angle: Math.random() * Math.PI * 2,
        tilt: (Math.random() - 0.5) * 1.2,
        size: Math.random() * 1.5 + 0.8,
      });
    }

    canvas.addEventListener("pointermove", (e) => {
      const rect = canvas.getBoundingClientRect();
      this.orbMouseX = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
      this.orbMouseY = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
    });

    canvas.addEventListener("pointerleave", () => {
      this.orbMouseX = 0;
      this.orbMouseY = 0;
    });

    canvas.addEventListener("click", () => {
      this.orbShockwave = 1.0;
      this.playEchoPing();
      if (this.isListening) {
        if (this.recognition) this.recognition.stop();
        this.isListening = false;
        this.setOrbState("idle");
      } else {
        const input = document.getElementById("composerInput");
        this.listenOnce(
          (text) => {
            if (input) input.value = text;
            if (window.hearthApp) window.hearthApp.sendMessage(text);
          },
          (err) => console.warn(err)
        );
      }
    });

    const drawOrb = () => {
      ctx.clearRect(0, 0, displayW, displayH);
      time += 0.02;

      const speed = this.orbState === "thinking" ? 0.08 : this.orbState === "listening" ? 0.045 : 0.02;
      rotY += speed + this.orbMouseX * 0.035;
      rotX = 0.3 + this.orbMouseY * 0.35;
      gimbalAngle1 += speed * 0.7;
      gimbalAngle2 -= speed * 0.55;

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      // Shockwave Pulse
      if (this.orbShockwave > 0.02) {
        this.orbShockwave *= 0.92;
        ctx.beginPath();
        ctx.arc(cx, cy, R * (1 + (1 - this.orbShockwave) * 1.6), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${this.orbShockwave * 0.75})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // 1. Ambient Iridescent Fluid Core
      const breath = 1 + Math.sin(time * 3) * (this.orbState === "listening" ? 0.12 : 0.04);
      const coreGrad = ctx.createRadialGradient(cx - 2, cy - 2, 2, cx, cy, R * breath);

      if (this.orbState === "listening") {
        coreGrad.addColorStop(0, "#fff1f2");
        coreGrad.addColorStop(0.35, "rgba(255, 51, 102, 0.85)");
        coreGrad.addColorStop(1, "rgba(136, 19, 55, 0.15)");
      } else if (this.orbState === "thinking") {
        coreGrad.addColorStop(0, "#faf5ff");
        coreGrad.addColorStop(0.35, "rgba(168, 85, 247, 0.85)");
        coreGrad.addColorStop(1, "rgba(59, 7, 100, 0.15)");
      } else {
        coreGrad.addColorStop(0, "#f0fdfa");
        coreGrad.addColorStop(0.3, "rgba(6, 182, 212, 0.75)");
        coreGrad.addColorStop(0.7, "rgba(59, 130, 246, 0.45)");
        coreGrad.addColorStop(1, "rgba(3, 7, 18, 0.08)");
      }

      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, R * breath, 0, Math.PI * 2);
      ctx.fill();

      // 2. 3D Astrolabe Gimbal Rings
      // Ring 1: 45 degrees
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(Math.PI / 4 + rotX * 0.2);
      ctx.beginPath();
      ctx.ellipse(0, 0, R + 8, (R + 8) * Math.cos(gimbalAngle1), 0, 0, Math.PI * 2);
      ctx.strokeStyle = this.orbState === "listening"
        ? "rgba(255, 51, 102, 0.55)"
        : "rgba(6, 182, 212, 0.55)";
      ctx.lineWidth = 1.0;
      ctx.stroke();
      ctx.restore();

      // Ring 2: -45 degrees
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-Math.PI / 4 - rotX * 0.2);
      ctx.beginPath();
      ctx.ellipse(0, 0, R + 10, (R + 10) * Math.cos(gimbalAngle2), 0, 0, Math.PI * 2);
      ctx.strokeStyle = this.orbState === "thinking"
        ? "rgba(168, 85, 247, 0.65)"
        : "rgba(168, 85, 247, 0.4)";
      ctx.lineWidth = 0.9;
      ctx.stroke();
      ctx.restore();

      // 3. 3D Spherical Coordinate Projection
      const projected = [];
      const focal = 180;

      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.z * cosY + p.x * sinY;
        const y2 = p.y * cosX - z1 * sinX;
        const z2 = z1 * cosX + p.y * sinX;

        const scale = focal / (focal + z2);
        projected.push({
          x: cx + x1 * scale,
          y: cy + y2 * scale,
          z: z2,
          scale: scale,
        });
      }

      // 4. Latitude Rings
      for (let r = 1; r < rings; r++) {
        ctx.beginPath();
        for (let s = 0; s < segments; s++) {
          const idx = r * segments + s;
          const nextIdx = r * segments + ((s + 1) % segments);
          const p1 = projected[idx];
          const p2 = projected[nextIdx];
          if (s === 0) ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.closePath();
        const avgZ = projected[r * segments].z;
        const alpha = Math.max(0.12, (avgZ + R) / (2 * R));
        ctx.strokeStyle = this.orbState === "listening"
          ? `rgba(255, 51, 102, ${alpha * 0.65})`
          : `rgba(6, 182, 212, ${alpha * 0.55})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      // 5. Longitude Meridians
      for (let s = 0; s < segments; s++) {
        ctx.beginPath();
        for (let r = 0; r <= rings; r++) {
          const idx = r * segments + s;
          const pt = projected[idx];
          if (r === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        ctx.strokeStyle = this.orbState === "thinking"
          ? "rgba(168, 85, 247, 0.4)"
          : "rgba(6, 182, 212, 0.35)";
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }

      // 6. Glowing Vertices for Foreground Points
      for (let i = 0; i < projected.length; i++) {
        const pt = projected[i];
        if (pt.z > 2) {
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 1.3 * pt.scale, 0, Math.PI * 2);
          ctx.fillStyle = this.orbState === "listening" ? "#ff3366" : "#06b6d4";
          ctx.fill();
        }
      }

      // 7. Orbiting Particle Stars
      orbiters.forEach((orb) => {
        orb.angle += orb.speed;
        const ox = Math.cos(orb.angle) * orb.orbitR;
        const oz = Math.sin(orb.angle) * orb.orbitR;
        const oy = oz * Math.sin(orb.tilt);

        const px = cx + (ox * cosY - oz * sinY);
        const pz = oz * cosY + ox * sinY;
        const py = cy + (oy * cosX - pz * sinX);

        if (pz > -R) {
          const pScale = focal / (focal + pz);
          ctx.beginPath();
          ctx.arc(px, py, orb.size * pScale, 0, Math.PI * 2);
          ctx.fillStyle = this.orbState === "listening" ? "#ff88a3" : "#67e8f9";
          ctx.shadowColor = "#06b6d4";
          ctx.shadowBlur = 5;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // 8. Speaking Audio Equalizer Bars
      if (this.orbState === "speaking") {
        for (let b = 0; b < 12; b++) {
          const barAngle = (b * Math.PI * 2) / 12 + time * 2;
          const waveH = Math.sin(time * 8 + b * 1.5) * 6 + 8;
          const bx1 = cx + Math.cos(barAngle) * (R + 3);
          const by1 = cy + Math.sin(barAngle) * (R + 3);
          const bx2 = cx + Math.cos(barAngle) * (R + 3 + waveH);
          const by2 = cy + Math.sin(barAngle) * (R + 3 + waveH);

          ctx.beginPath();
          ctx.moveTo(bx1, by1);
          ctx.lineTo(bx2, by2);
          ctx.strokeStyle = "rgba(6, 182, 212, 0.85)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
      }

      requestAnimationFrame(drawOrb);
    };

    requestAnimationFrame(drawOrb);
  }

  // ---- B3 multi-modal simulator state (voice + D-pad/keyboard + visual cards) ----
  initMultimodal() {
    if (this.ttsQueue) return;
    this.ttsQueue = [];
    this.reactEvents = [];
    this.visualCards = [];
    this.focusIndex = 0;
    this.lightWaveMode = "idle";
    this.chimeLog = [];
    this.onCardSelect = null;
    this._dpadBound = false;
  }

  emitReact(phase, summary, detail = {}) {
    this.initMultimodal();
    const evt = { seq: this.reactEvents.length + 1, phase, summary, detail, at: new Date().toISOString() };
    this.reactEvents.push(evt);
    if (this.reactEvents.length > 200) this.reactEvents.splice(0, this.reactEvents.length - 200);
    try {
      window.dispatchEvent(new CustomEvent("hearth:react", { detail: evt }));
    } catch (e) { /* headless: no window */ }
    const feed = typeof document !== "undefined" && document.getElementById("reactVisualizerFeed");
    if (feed) {
      const row = document.createElement("div");
      row.className = `react-step react-${phase}`;
      row.textContent = `${phase}: ${summary}`;
      feed.prepend(row);
      while (feed.children.length > 12) feed.removeChild(feed.lastChild);
    }
    return evt;
  }

  getReactEvents(limit = 20) {
    this.initMultimodal();
    return this.reactEvents.slice(-limit);
  }

  enqueueTts(text, voice = "alexa") {
    this.initMultimodal();
    const clean = String(text || "").trim();
    if (!clean) return null;
    const entry = { id: `tts-${Date.now()}-${this.ttsQueue.length}`, text: clean.slice(0, 2000), voice, status: "queued" };
    this.ttsQueue.push(entry);
    this.emitReact("speak", clean.slice(0, 120), { tts_id: entry.id });
    return entry;
  }

  drainTtsQueue() {
    this.initMultimodal();
    const next = this.ttsQueue.find((e) => e.status === "queued");
    if (!next) return null;
    next.status = "speaking";
    try {
      this.speak(next.text);
    } catch (e) { /* headless: speechSynthesis unavailable */ }
    next.status = "done";
    return next;
  }

  // Echo chime hook: maps to existing procedural tones + logs for the visualizer.
  emitChime(kind = "wake") {
    this.initMultimodal();
    try {
      if (kind === "success") this.playSuccessChime();
      else if (kind === "warning") this.playWarningTone();
      else if (kind === "scan") this.playBarcodeBeep();
      else this.playEchoPing();
    } catch (e) { /* headless audio */ }
    const entry = { kind, at: new Date().toISOString() };
    this.chimeLog.push(entry);
    this.emitReact("chime", `Echo chime: ${kind}`, entry);
    return entry;
  }

  // Light-wave hook: mirrors the Alexa fluid glow bar + orb state in one call.
  setLightWave(mode = "idle") {
    this.initMultimodal();
    const modes = { idle: "idle", listening: "listening", thinking: "thinking", speaking: "speaking", alert: "listening" };
    this.lightWaveMode = modes[mode] || "idle";
    if (this.lightWaveMode === "listening") this.setOrbState("listening");
    else if (this.lightWaveMode === "thinking") this.setOrbState("thinking");
    else if (this.lightWaveMode === "speaking") this.setOrbState("speaking");
    else if (typeof this.setOrbState === "function") this.setOrbState("idle");
    this.emitReact("light-wave", `Light wave -> ${this.lightWaveMode}`, { mode: this.lightWaveMode });
    try {
      window.dispatchEvent(new CustomEvent("hearth:light-wave", { detail: { mode: this.lightWaveMode } }));
    } catch (e) { /* headless */ }
    return this.lightWaveMode;
  }

  // Visual cards: single-flow card row with D-pad/keyboard focus highlight.
  renderVisualCards(cards, containerId = "aplCardRow") {
    this.initMultimodal();
    this.visualCards = Array.isArray(cards) ? cards : [];
    this.focusIndex = 0;
    this.emitReact("show", `APL canvas: ${this.visualCards.length} cards`, {});
    if (typeof document === "undefined") return this.visualCards;
    const row = document.getElementById(containerId);
    if (!row) return this.visualCards;
    row.innerHTML = "";
    this.visualCards.forEach((card, idx) => {
      const el = document.createElement("button");
      el.className = "apl-card" + (idx === this.focusIndex ? " focused" : "");
      el.dataset.index = String(idx);
      el.innerHTML = `<span class="apl-card-title"></span><span class="apl-card-sub"></span>`;
      el.querySelector(".apl-card-title").textContent = card.title || card.id || `Card ${idx}`;
      el.querySelector(".apl-card-sub").textContent = card.subtitle || "";
      el.addEventListener("click", () => this.handleDpad("Select", idx));
      row.appendChild(el);
    });
    return this.visualCards;
  }

  highlightFocus() {
    if (typeof document === "undefined") return;
    document.querySelectorAll("#aplCardRow .apl-card").forEach((el) => {
      el.classList.toggle("focused", Number(el.dataset.index) === this.focusIndex);
    });
  }

  // D-pad / keyboard nav: arrows move focus, Enter selects, Esc goes back.
  handleDpad(action, focusIndex = null) {
    this.initMultimodal();
    const n = Math.max(1, this.visualCards.length);
    if (focusIndex !== null && focusIndex !== undefined) this.focusIndex = Number(focusIndex) % n;
    if (action === "Right") this.focusIndex = (this.focusIndex + 1) % n;
    else if (action === "Left") this.focusIndex = (this.focusIndex - 1 + n) % n;
    else if (action === "Down") this.focusIndex = Math.min(n - 1, this.focusIndex + 1);
    else if (action === "Up" || action === "Back") this.focusIndex = 0;
    else if (action !== "Select") return { ok: false, error: `Unknown D-pad action '${action}'` };
    let selected = null;
    if (action === "Select") {
      selected = this.visualCards[this.focusIndex] || null;
      this.emitChime("success");
      this.setLightWave("speaking");
      if (selected && typeof this.onCardSelect === "function") {
        try { this.onCardSelect(selected, this.focusIndex); } catch (e) { /* ignore */ }
      }
    } else {
      this.setLightWave("thinking");
    }
    const focused = this.visualCards[this.focusIndex] || null;
    this.emitReact("dpad", `D-pad ${action} -> focus ${this.focusIndex}`, { selected: selected && selected.id });
    this.highlightFocus();
    return { ok: true, action, focus_index: this.focusIndex, focused, selected, count: n };
  }

  bindDpadKeyboard() {
    this.initMultimodal();
    if (this._dpadBound || typeof document === "undefined") return;
    this._dpadBound = true;
    const map = { ArrowUp: "Up", ArrowDown: "Down", ArrowLeft: "Left", ArrowRight: "Right", Enter: "Select", Escape: "Back" };
    document.addEventListener("keydown", (e) => {
      const action = map[e.key];
      if (!action) return;
      const tag = (e.target && e.target.tagName) || "";
      if (action !== "Escape" && (tag === "INPUT" || tag === "TEXTAREA")) return;
      e.preventDefault();
      this.handleDpad(action);
    });
  }

  // Single-flow turn: voice + visual cards + TTS + hooks + ReAct, no device needed.
  async runMultimodalTurn({ utterance = "", cards = null, speakText = "", apiBase = "" } = {}) {
    this.initMultimodal();
    this.bindDpadKeyboard();
    this.emitReact("thought", `Heard: ${String(utterance).slice(0, 140)}`, { utterance });
    this.setLightWave("listening");
    this.emitChime("wake");
    if (cards) this.renderVisualCards(cards);
    this.setLightWave("thinking");
    let server = null;
    if (utterance && apiBase && typeof fetch !== "undefined") {
      try {
        const res = await fetch(`${apiBase}/api/alexa/voice-turn`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ utterance }),
        });
        server = await res.json();
        if (server && server.multimodal && Array.isArray(server.multimodal.apl_payload?.cards)) {
          this.renderVisualCards(server.multimodal.apl_payload.cards);
        }
        if (server && server.multimodal && server.multimodal.speak_text) {
          speakText = server.multimodal.speak_text;
        }
      } catch (e) {
        this.emitReact("observation", `Simulator offline: ${e.message}`, {});
      }
    }
    if (speakText) this.enqueueTts(speakText);
    this.setLightWave("speaking");
    this.drainTtsQueue();
    this.emitReact("observation", `Turn complete: ${(speakText || "").slice(0, 120)}`, {});
    return { ok: true, speakText, cards: this.visualCards, react: this.getReactEvents(12), server };
  }

  // Consume the server `hearth` companion envelope from /api/alexa/directive.
  processAlexaEnvelope(envelope) {
    this.initMultimodal();
    if (!envelope || typeof envelope !== "object") return { ok: false };
    if (envelope.speak_text) this.enqueueTts(envelope.speak_text);
    if (envelope.chime && envelope.chime.kind) this.emitChime(envelope.chime.kind);
    else if (envelope.chime && envelope.chime.spec) this.emitChime(envelope.chime.spec.kind || "wake");
    if (envelope.light_wave && envelope.light_wave.mode) this.setLightWave(envelope.light_wave.mode);
    if (Array.isArray(envelope.apl_payload?.cards)) this.renderVisualCards(envelope.apl_payload.cards);
    this.drainTtsQueue();
    return { ok: true, queued: this.ttsQueue.length };
  }

  // Dynamic Alexa Fluid Glow Wave Animation Loop
  startGlowRenderLoop() {
    if (!this.canvas || !this.ctx) return;

    const render = () => {
      this.wavePhase += 0.04;
      this.amplitude += (this.targetAmplitude - this.amplitude) * 0.1;

      const w = this.canvas.width = this.canvas.parentElement.clientWidth || 800;
      const h = this.canvas.height = 36;
      this.ctx.clearRect(0, 0, w, h);

      // Render 3 fluid harmonic waves (Cyan, Blue, Purple)
      const layers = [
        { color: "rgba(6, 182, 212, 0.75)", freq: 0.012, speed: 1.0, offset: 0 },
        { color: "rgba(59, 130, 246, 0.65)", freq: 0.018, speed: 1.3, offset: 2.0 },
        { color: "rgba(168, 85, 247, 0.55)", freq: 0.009, speed: 0.8, offset: 4.0 },
      ];

      layers.forEach(layer => {
        this.ctx.beginPath();
        this.ctx.strokeStyle = layer.color;
        this.ctx.lineWidth = (this.isListening || this.isSpeaking) ? 3 : 1.5;
        this.ctx.shadowBlur = (this.isListening || this.isSpeaking) ? 14 : 4;
        this.ctx.shadowColor = layer.color;

        for (let x = 0; x <= w; x += 4) {
          const envelope = Math.sin((x / w) * Math.PI); // Taper at edges
          const y = (h / 2) + Math.sin(x * layer.freq + this.wavePhase * layer.speed + layer.offset) 
                    * (h * 0.42 * this.amplitude) * envelope;
          if (x === 0) this.ctx.moveTo(x, y);
          else this.ctx.lineTo(x, y);
        }
        this.ctx.stroke();
      });

      requestAnimationFrame(render);
    };

    requestAnimationFrame(render);
  }
}
