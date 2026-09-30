/**
 * Hearth Universal — Beyond-Human 4D Ambient Holodeck & Operations Engine
 * Spec 2025-11-25 Streamable HTTP · Propose-Never-Execute · Glass-Box Core
 * Features: Three.js WebGL 3D Holodeck, Neural Core, 3D ReAct DAG, Chronos Helix,
 * Web Audio Synthesizer with Real-Time FFT Analyzer, Smart Twin Raycasting, Multi-Modal Alexa+
 */

const $ = id => document.getElementById(id);
let sfxEnabled = true;
let ttsEnabled = true;
let isRecording = false;
let currentHomeState = null;
let currentMode = "holodeck"; // "holodeck" | "neural" | "dag" | "merkle"
let currentPalette = "cyan"; // "cyan" | "solar" | "matrix" | "void"
let autoSpin = true;
let wireframeActive = false;
let activeCamPreset = "iso"; // "iso" | "top" | "front"
let recognition = null;
let isExecutingAgent = false;

// =============================================================================
// 1. Synthesized Web Audio Spatial Sound Engine & FFT Spectrum Analyzer
// =============================================================================
let audioCtx = null;
let analyserNode = null;
let audioDataArray = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
      analyserNode = audioCtx.createAnalyser();
      analyserNode.fftSize = 64;
      audioDataArray = new Uint8Array(analyserNode.frequencyBinCount);
      analyserNode.connect(audioCtx.destination);
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
  return audioCtx;
}

function playSfx(type) {
  if (!sfxEnabled) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  const now = ctx.currentTime;
  if (type === "click") {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(1400, now);
    osc.frequency.exponentialRampToValueAtTime(300, now + 0.035);
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
    osc.connect(gain);
    gain.connect(analyserNode || ctx.destination);
    osc.start(now);
    osc.stop(now + 0.035);
  } else if (type === "wake") {
    [523.25, 659.25, 783.99, 1046.5].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + idx * 0.05);
      gain.gain.setValueAtTime(0.08, now + idx * 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.05 + 0.3);
      osc.connect(gain);
      gain.connect(analyserNode || ctx.destination);
      osc.start(now + idx * 0.05);
      osc.stop(now + idx * 0.05 + 0.3);
    });
  } else if (type === "approve") {
    [440, 554.37, 659.25, 880, 1108.7].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, now + idx * 0.07);
      gain.gain.setValueAtTime(0.09, now + idx * 0.07);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.07 + 0.38);
      osc.connect(gain);
      gain.connect(analyserNode || ctx.destination);
      osc.start(now + idx * 0.07);
      osc.stop(now + idx * 0.07 + 0.38);
    });
  } else if (type === "lock") {
    // Motorized lock mechanical servo chirp
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(240, now);
    osc.frequency.linearRampToValueAtTime(480, now + 0.08);
    osc.frequency.linearRampToValueAtTime(180, now + 0.16);
    gain.gain.setValueAtTime(0.09, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
    osc.connect(gain);
    gain.connect(analyserNode || ctx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  } else if (type === "alert") {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(120, now);
    osc.frequency.linearRampToValueAtTime(60, now + 0.28);
    gain.gain.setValueAtTime(0.14, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
    osc.connect(gain);
    gain.connect(analyserNode || ctx.destination);
    osc.start(now);
    osc.stop(now + 0.28);
  }
}

// Draw Real-Time 48-band Audio Spectrum in Bottom HUD
function drawAudioSpectrum() {
  const canvas = $("audioSpectrumCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  if (analyserNode && audioDataArray) {
    analyserNode.getByteFrequencyData(audioDataArray);
    const bars = 20;
    const barWidth = (W / bars) - 1.5;
    for (let i = 0; i < bars; i++) {
      const val = audioDataArray[i] || 0;
      const pct = val / 255;
      const h = Math.max(2, pct * H);
      const x = i * (barWidth + 1.5);
      const y = H - h;
      
      const grad = ctx.createLinearGradient(0, y, 0, H);
      grad.addColorStop(0, "#00f0ff");
      grad.addColorStop(1, "#6366f1");
      ctx.fillStyle = grad;
      ctx.fillRect(x, y, barWidth, h);
    }
  } else {
    // Subtle ambient simulated pulse
    const t = performance.now() * 0.003;
    const bars = 20;
    const barWidth = (W / bars) - 1.5;
    for (let i = 0; i < bars; i++) {
      const h = Math.max(2, (Math.sin(t + i * 0.4) * 0.5 + 0.5) * 8);
      const x = i * (barWidth + 1.5);
      ctx.fillStyle = "rgba(0, 240, 255, 0.4)";
      ctx.fillRect(x, H - h, barWidth, h);
    }
  }
}

// =============================================================================
// 2. Beyond-Human Three.js 4D WebGL Holo-Nexus Scene Engine
// =============================================================================
const HoloScene = {
  renderer: null,
  scene: null,
  camera: null,
  controls: null,
  raycaster: null,
  mouse: null,
  canvas: null,
  wrapper: null,
  
  // World Groups
  groupHolodeck: null,
  groupNeural: null,
  groupDag: null,
  groupMerkle: null,
  
  // Interactive Mesh Pointers
  interactiveMeshes: [],
  hoveredMesh: null,
  
  // Dynamic Objects inside Holodeck
  livingLight: null,
  livingLightBulb: null,
  hvacTurbine: null,
  hvacParticles: [],
  deadboltLockMesh: null,
  deadboltLatch: null,
  deadboltLaserPlane: null,
  energyCorePillar: null,
  energyConduits: [],
  coffeeMachineLed: null,
  
  // Dynamic Objects inside Neural Core
  neuralShell: null,
  neuralCoreSphere: null,
  neuralGimbalRing1: null,
  neuralGimbalRing2: null,
  neuralParticles: null,
  
  // Dynamic Objects inside ReAct DAG
  dagSplinePhotons: [],
  dagNodeMeshes: [],
  
  // Dynamic Objects inside Merkle Helix
  merkleBlocks: [],
  
  // Animation Telemetry
  lastTime: performance.now(),
  frameCount: 0,
  currentFps: 60,
  
  init() {
    this.canvas = $("holoCanvas3D");
    this.wrapper = $("holoCanvasWrapper");
    if (!this.canvas || typeof THREE === "undefined") {
      console.warn("Three.js not available, falling back gracefully.");
      return;
    }

    const width = this.wrapper.clientWidth;
    const height = this.wrapper.clientHeight;

    // 1. Scene & Renderer
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x030712);
    this.scene.fog = new THREE.FogExp2(0x030712, 0.015);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 2. Camera & Orbit Controls
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.setCameraPreset("iso");

    if (typeof THREE.OrbitControls !== "undefined") {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.maxPolarAngle = Math.PI / 2.05; // Prevent flipping under floor
      this.controls.minDistance = 8;
      this.controls.maxDistance = 85;
      this.controls.autoRotate = autoSpin;
      this.controls.autoRotateSpeed = 1.0;
    }

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.45);
    this.scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f0ff, 0.6);
    dirLight.position.set(20, 40, 20);
    this.scene.add(dirLight);

    // 4. Raycasting
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);

    // 5. Build 4 Worlds
    this.buildHolodeckWorld();
    this.buildNeuralWorld();
    this.buildDagWorld();
    this.buildMerkleWorld();

    // Set Initial Active World
    this.switchMode(currentMode);

    // 6. Event Listeners
    window.addEventListener("resize", () => this.onResize());
    this.canvas.addEventListener("mousemove", e => this.onMouseMove(e));
    this.canvas.addEventListener("click", e => this.onClick(e));

    // 7. Start Render Loop
    this.animate();
  },

  onResize() {
    if (!this.wrapper || !this.renderer || !this.camera) return;
    const width = this.wrapper.clientWidth;
    const height = this.wrapper.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  },

  setCameraPreset(preset) {
    activeCamPreset = preset;
    if (!this.camera) return;
    if (preset === "iso") {
      this.camera.position.set(24, 18, 24);
      this.camera.lookAt(0, 0, 0);
    } else if (preset === "top") {
      this.camera.position.set(0, 36, 0.1);
      this.camera.lookAt(0, 0, 0);
    } else if (preset === "front") {
      this.camera.position.set(0, 10, 28);
      this.camera.lookAt(0, 2, 0);
    }
    if (this.controls) this.controls.target.set(0, 0, 0);
  },

  // ---------------------------------------------------------------------------
  // WORLD 1: 3D Smart Holodeck (Digital Twin)
  // ---------------------------------------------------------------------------
  buildHolodeckWorld() {
    this.groupHolodeck = new THREE.Group();
    this.scene.add(this.groupHolodeck);

    // Cyber-Grid Base Floor
    const gridHelper = new THREE.GridHelper(36, 36, 0x00f0ff, 0x1e293b);
    gridHelper.position.y = -0.05;
    this.groupHolodeck.add(gridHelper);

    // Translucent House Floor Slab
    const floorGeo = new THREE.BoxGeometry(26, 0.2, 22);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x0b1329,
      roughness: 0.2,
      metalness: 0.8,
      transparent: true,
      opacity: 0.85
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.position.y = -0.1;
    this.groupHolodeck.add(floorMesh);

    // Neon Room Dividers (Boundary Laser Lines)
    const lineMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.6 });
    const dividerPoints = [
      new THREE.Vector3(-13, 0.05, 0), new THREE.Vector3(13, 0.05, 0),
      new THREE.Vector3(0, 0.05, -11), new THREE.Vector3(0, 0.05, 11)
    ];
    const dividerGeo = new THREE.BufferGeometry().setFromPoints(dividerPoints);
    const dividerLines = new THREE.LineSegments(dividerGeo, lineMat);
    this.groupHolodeck.add(dividerLines);

    // ROOM A: Living Room (Top-Left Quad: -6.5, Z: -5.5)
    this.buildLivingRoom3D(-6.5, -5.5);

    // ROOM B: Master Bedroom / Climate (Top-Right Quad: 6.5, Z: -5.5)
    this.buildBedroom3D(6.5, -5.5);

    // ROOM C: Kitchen & Pantry (Bottom-Left Quad: -6.5, Z: 5.5)
    this.buildKitchen3D(-6.5, 5.5);

    // ROOM D: Entryway & Smart Lock (Bottom-Right Quad: 6.5, Z: 5.5)
    this.buildEntryway3D(6.5, 5.5);

    // CENTER: Power & Energy Nexus Reactor Column
    this.buildEnergyNexus3D(0, 0);
  },

  buildLivingRoom3D(cx, cz) {
    const group = new THREE.Group();
    group.position.set(cx, 0, cz);

    // Modern Sofa
    const sofaMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.4 });
    const baseGeo = new THREE.BoxGeometry(4.2, 0.6, 2.0);
    const baseMesh = new THREE.Mesh(baseGeo, sofaMat);
    baseMesh.position.y = 0.3;
    group.add(baseMesh);

    const backGeo = new THREE.BoxGeometry(4.2, 1.2, 0.5);
    const backMesh = new THREE.Mesh(backGeo, sofaMat);
    backMesh.position.set(0, 0.9, -0.75);
    group.add(backMesh);

    // Coffee Table (Obsidian Glass)
    const tableGeo = new THREE.BoxGeometry(2.4, 0.35, 1.2);
    const tableMat = new THREE.MeshPhysicalMaterial({ color: 0x0f172a, roughness: 0.1, transmission: 0.6, thickness: 0.5 });
    const tableMesh = new THREE.Mesh(tableGeo, tableMat);
    tableMesh.position.set(0, 0.2, 1.2);
    group.add(tableMesh);

    // 3D Suspended Pendant Lamp (Interactive Light Source!)
    const cordGeo = new THREE.CylinderGeometry(0.02, 0.02, 3.5);
    const cordMat = new THREE.MeshBasicMaterial({ color: 0x64748b });
    const cordMesh = new THREE.Mesh(cordGeo, cordMat);
    cordMesh.position.set(0, 4.25, 0.5);
    group.add(cordMesh);

    const shadeGeo = new THREE.ConeGeometry(0.8, 0.5, 16, 1, true);
    const shadeMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, side: THREE.DoubleSide });
    const shadeMesh = new THREE.Mesh(shadeGeo, shadeMat);
    shadeMesh.position.set(0, 2.5, 0.5);
    group.add(shadeMesh);

    const bulbGeo = new THREE.SphereGeometry(0.28, 16, 16);
    const bulbMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
    this.livingLightBulb = new THREE.Mesh(bulbGeo, bulbMat);
    this.livingLightBulb.position.set(0, 2.35, 0.5);
    this.livingLightBulb.userData = {
      name: "Living Room Ambient Pendant",
      action: "toggle_living_light",
      details: "Dimmable RGB lighting. Click to toggle state."
    };
    group.add(this.livingLightBulb);
    this.interactiveMeshes.push(this.livingLightBulb);

    // Real-Time Three.js PointLight casting illumination!
    this.livingLight = new THREE.PointLight(0x00f0ff, 1.6, 14);
    this.livingLight.position.set(0, 2.3, 0.5);
    group.add(this.livingLight);

    this.groupHolodeck.add(group);
  },

  buildBedroom3D(cx, cz) {
    const group = new THREE.Group();
    group.position.set(cx, 0, cz);

    // Bed Platform
    const bedMat = new THREE.MeshStandardMaterial({ color: 0x312e81, roughness: 0.5 });
    const bedBaseGeo = new THREE.BoxGeometry(3.6, 0.6, 4.2);
    const bedBase = new THREE.Mesh(bedBaseGeo, bedMat);
    bedBase.position.set(0, 0.3, 0);
    group.add(bedBase);

    // Bed Headboard
    const headGeo = new THREE.BoxGeometry(3.6, 1.6, 0.4);
    const headMesh = new THREE.Mesh(headGeo, bedMat);
    headMesh.position.set(0, 1.0, -1.9);
    group.add(headMesh);

    // HVAC Climate Column (Thermostat Vortex)
    const hvacColGeo = new THREE.CylinderGeometry(0.5, 0.5, 3.2, 16);
    const hvacColMat = new THREE.MeshPhysicalMaterial({ color: 0x1e293b, roughness: 0.2, transmission: 0.4 });
    const hvacCol = new THREE.Mesh(hvacColGeo, hvacColMat);
    hvacCol.position.set(2.4, 1.6, -1.8);
    hvacCol.userData = {
      name: "Smart HVAC Convection Turbine",
      action: "inspect_climate",
      details: "Climate Setpoint: 22.0°C. Click to view thermal stream."
    };
    group.add(hvacCol);
    this.interactiveMeshes.push(hvacCol);

    // Spinning 3D Turbine Rotor inside HVAC
    const turbineGeo = new THREE.BoxGeometry(0.7, 0.04, 0.15);
    const turbineMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
    this.hvacTurbine = new THREE.Mesh(turbineGeo, turbineMat);
    this.hvacTurbine.position.set(2.4, 2.6, -1.8);
    group.add(this.hvacTurbine);

    // Rising Thermal Convection Particles
    const pCount = 35;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount; i++) {
      pPos[i * 3] = 2.4 + (Math.random() - 0.5) * 0.6;
      pPos[i * 3 + 1] = 0.5 + Math.random() * 2.8;
      pPos[i * 3 + 2] = -1.8 + (Math.random() - 0.5) * 0.6;
    }
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x00f0ff, size: 0.12, transparent: true, opacity: 0.8 });
    const particles = new THREE.Points(pGeo, pMat);
    group.add(particles);
    this.hvacParticles.push({ points: particles, geo: pGeo });

    this.groupHolodeck.add(group);
  },

  buildKitchen3D(cx, cz) {
    const group = new THREE.Group();
    group.position.set(cx, 0, cz);

    // Kitchen Counter Island
    const islandGeo = new THREE.BoxGeometry(4.0, 1.1, 2.0);
    const islandMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.2, metalness: 0.7 });
    const island = new THREE.Mesh(islandGeo, islandMat);
    island.position.set(0, 0.55, 0);
    group.add(island);

    // Smart Espresso Machine Model
    const makerGeo = new THREE.BoxGeometry(0.8, 0.8, 0.7);
    const makerMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8 });
    const maker = new THREE.Mesh(makerGeo, makerMat);
    maker.position.set(-1.0, 1.4, 0);
    maker.userData = {
      name: "Smart Espresso & Coffee Maker",
      action: "order_coffee",
      details: "Pantry beans at 85%. Click to reorder."
    };
    group.add(maker);
    this.interactiveMeshes.push(maker);

    // Status LED on Coffee Maker
    const ledGeo = new THREE.SphereGeometry(0.06, 8, 8);
    const ledMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    this.coffeeMachineLed = new THREE.Mesh(ledGeo, ledMat);
    this.coffeeMachineLed.position.set(-1.0, 1.6, 0.38);
    group.add(this.coffeeMachineLed);

    // 3D Consumable Pantry Pods (Floating Cylinders with Stock Rings)
    const podGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.6, 16);
    const podMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.6 });
    const pod = new THREE.Mesh(podGeo, podMat);
    pod.position.set(0.8, 1.4, 0);
    group.add(pod);

    this.groupHolodeck.add(group);
  },

  buildEntryway3D(cx, cz) {
    const group = new THREE.Group();
    group.position.set(cx, 0, cz);

    // Cyber Door Frame
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 });
    const leftPost = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.4, 0.3), frameMat);
    leftPost.position.set(-1.4, 1.7, 0);
    group.add(leftPost);

    const rightPost = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.4, 0.3), frameMat);
    rightPost.position.set(1.4, 1.7, 0);
    group.add(rightPost);

    const lintel = new THREE.Mesh(new THREE.BoxGeometry(3.1, 0.3, 0.3), frameMat);
    lintel.position.set(0, 3.3, 0);
    group.add(lintel);

    // Motorized Deadbolt Lock Cylinder Mechanism
    const lockHousingGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.25, 24);
    const lockHousingMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.9, roughness: 0.2 });
    this.deadboltLockMesh = new THREE.Mesh(lockHousingGeo, lockHousingMat);
    this.deadboltLockMesh.rotation.z = Math.PI / 2;
    this.deadboltLockMesh.position.set(-1.25, 1.6, 0);
    this.deadboltLockMesh.userData = {
      name: "Front Door Motorized Deadbolt",
      action: "toggle_lock",
      details: "Perimeter Security Lock. Click to lock/unlock."
    };
    group.add(this.deadboltLockMesh);
    this.interactiveMeshes.push(this.deadboltLockMesh);

    // Sliding Latch Bolt Pin
    const latchGeo = new THREE.BoxGeometry(0.7, 0.12, 0.12);
    const latchMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.95 });
    this.deadboltLatch = new THREE.Mesh(latchGeo, latchMat);
    this.deadboltLatch.position.set(-0.85, 1.6, 0);
    group.add(this.deadboltLatch);

    // Biometric Laser Barrier Plane (Glows Red when locked, Green when unlocked)
    const planeGeo = new THREE.PlaneGeometry(2.5, 3.0);
    const planeMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.25,
      side: THREE.DoubleSide
    });
    this.deadboltLaserPlane = new THREE.Mesh(planeGeo, planeMat);
    this.deadboltLaserPlane.position.set(0, 1.6, 0);
    group.add(this.deadboltLaserPlane);

    this.groupHolodeck.add(group);
  },

  buildEnergyNexus3D(cx, cz) {
    const group = new THREE.Group();
    group.position.set(cx, 0, cz);

    // Central Energy Column
    const coreGeo = new THREE.CylinderGeometry(0.7, 0.7, 4.0, 24, 1, true);
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x00f0ff,
      roughness: 0.1,
      transmission: 0.7,
      transparent: true,
      opacity: 0.6
    });
    this.energyCorePillar = new THREE.Mesh(coreGeo, coreMat);
    this.energyCorePillar.position.y = 2.0;
    this.energyCorePillar.userData = {
      name: "Central Energy Nexus",
      action: "inspect_energy",
      details: "Active Load: 1.45 kW · Solar: 0.85 kW. Proportional power conduit pulsing."
    };
    group.add(this.energyCorePillar);
    this.interactiveMeshes.push(this.energyCorePillar);

    // Floating Energy Torus Rings
    for (let r = 0; r < 3; r++) {
      const ringGeo = new THREE.TorusGeometry(0.85, 0.04, 12, 32);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 1.0 + r * 1.0;
      group.add(ring);
    }

    // Floor Glowing Energy Conduits to each room
    const conduitMat = new THREE.LineDashedMaterial({
      color: 0x00f0ff,
      dashSize: 0.4,
      gapSize: 0.2,
      scale: 1
    });
    const paths = [
      [-6.5, -5.5], [6.5, -5.5], [-6.5, 5.5], [6.5, 5.5]
    ];
    paths.forEach(dest => {
      const pts = [new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(dest[0], 0.08, dest[1])];
      const g = new THREE.BufferGeometry().setFromPoints(pts);
      const line = new THREE.Line(g, conduitMat);
      line.computeLineDistances();
      group.add(line);
      this.energyConduits.push(line);
    });

    this.groupHolodeck.add(group);
  },

  // ---------------------------------------------------------------------------
  // WORLD 2: Quantum Neural Hypersphere (Alexa+ Deep Mind)
  // ---------------------------------------------------------------------------
  buildNeuralWorld() {
    this.groupNeural = new THREE.Group();
    this.scene.add(this.groupNeural);

    // 1. Geodesic Icosahedron Wireframe Shell
    const shellGeo = new THREE.IcosahedronGeometry(5.5, 2);
    const shellMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: 0.45
    });
    this.neuralShell = new THREE.Mesh(shellGeo, shellMat);
    this.groupNeural.add(this.neuralShell);

    // 2. Inner Crystal Core Sphere
    const innerGeo = new THREE.SphereGeometry(3.2, 32, 32);
    const innerMat = new THREE.MeshPhysicalMaterial({
      color: 0x6366f1,
      emissive: 0x1e1b4b,
      roughness: 0.1,
      transmission: 0.8,
      transparent: true,
      opacity: 0.75
    });
    this.neuralCoreSphere = new THREE.Mesh(innerGeo, innerMat);
    this.groupNeural.add(this.neuralCoreSphere);

    // 3. Dual Gyro Gimbal Rings
    const ringGeo1 = new THREE.TorusGeometry(6.6, 0.08, 16, 64);
    const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
    this.neuralGimbalRing1 = new THREE.Mesh(ringGeo1, ringMat1);
    this.groupNeural.add(this.neuralGimbalRing1);

    const ringGeo2 = new THREE.TorusGeometry(7.2, 0.08, 16, 64);
    const ringMat2 = new THREE.MeshBasicMaterial({ color: 0xa855f7 });
    this.neuralGimbalRing2 = new THREE.Mesh(ringGeo2, ringMat2);
    this.neuralGimbalRing2.rotation.x = Math.PI / 2;
    this.groupNeural.add(this.neuralGimbalRing2);

    // 4. Quantum Memory Swarm (2,000 points)
    const swarmCount = 2000;
    const swarmGeo = new THREE.BufferGeometry();
    const swarmPos = new Float32Array(swarmCount * 3);
    for (let i = 0; i < swarmCount; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 3.6 + Math.random() * 5.5;
      const sinPhi = Math.sin(phi);
      swarmPos[i * 3] = r * sinPhi * Math.cos(theta);
      swarmPos[i * 3 + 1] = r * sinPhi * Math.sin(theta);
      swarmPos[i * 3 + 2] = r * Math.cos(phi);
    }
    swarmGeo.setAttribute("position", new THREE.BufferAttribute(swarmPos, 3));
    const swarmMat = new THREE.PointsMaterial({
      color: 0x00f0ff,
      size: 0.14,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending
    });
    this.neuralParticles = new THREE.Points(swarmGeo, swarmMat);
    this.groupNeural.add(this.neuralParticles);
  },

  // ---------------------------------------------------------------------------
  // WORLD 3: 3D ReAct DAG Constellation
  // ---------------------------------------------------------------------------
  buildDagWorld() {
    this.groupDag = new THREE.Group();
    this.scene.add(this.groupDag);

    const nodeDefs = [
      { name: "User Input Stimulus", desc: "Voice or text query received", pos: [-12, 4, 0], color: 0x00f0ff },
      { name: "Sentinel Guardrail", desc: "3-tier security & exfiltration check", pos: [-6, 6, 3], color: 0x10b981 },
      { name: "Cognitive ReAct Core", desc: "Reasoning loop & tool selection", pos: [0, 5, 0], color: 0x3b82f6 },
      { name: "Amazon Bedrock / Nova", desc: "Foundation model reasoning", pos: [6, 7, -3], color: 0x8b5cf6 },
      { name: "Propose-Never-Execute", desc: "Glass-box approval staging gate", pos: [12, 4, 0], color: 0xf59e0b }
    ];

    const curvePoints = [];
    nodeDefs.forEach(def => {
      // 3D Polyhedron Node
      const nodeGeo = new THREE.OctahedronGeometry(1.2, 0);
      const nodeMat = new THREE.MeshStandardMaterial({
        color: def.color,
        emissive: def.color,
        emissiveIntensity: 0.4,
        roughness: 0.2
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.position.set(...def.pos);
      nodeMesh.userData = {
        name: def.name,
        action: "inspect_dag_node",
        details: def.desc
      };
      this.groupDag.add(nodeMesh);
      this.dagNodeMeshes.push(nodeMesh);
      this.interactiveMeshes.push(nodeMesh);
      curvePoints.push(new THREE.Vector3(...def.pos));
    });

    // 3D Catmull-Rom Spline Conduit
    const curve = new THREE.CatmullRomCurve3(curvePoints);
    const tubeGeo = new THREE.TubeGeometry(curve, 64, 0.12, 8, false);
    const tubeMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.5 });
    const tube = new THREE.Mesh(tubeGeo, tubeMat);
    this.groupDag.add(tube);

    // Glowing Traveling Photon Sprites
    for (let p = 0; p < 6; p++) {
      const photonGeo = new THREE.SphereGeometry(0.25, 12, 12);
      const photonMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const photon = new THREE.Mesh(photonGeo, photonMat);
      this.groupDag.add(photon);
      this.dagSplinePhotons.push({ mesh: photon, curve, progress: p / 6 });
    }
  },

  // ---------------------------------------------------------------------------
  // WORLD 4: Chronos Merkle Blockchain Helix
  // ---------------------------------------------------------------------------
  buildMerkleWorld() {
    this.groupMerkle = new THREE.Group();
    this.scene.add(this.groupMerkle);

    const blockCount = 14;
    for (let i = 0; i < blockCount; i++) {
      const angle = (i / blockCount) * Math.PI * 4;
      const y = (i - blockCount / 2) * 1.4;
      const x = Math.cos(angle) * 5.0;
      const z = Math.sin(angle) * 5.0;

      const cubeGeo = new THREE.BoxGeometry(1.2, 0.8, 1.2);
      const cubeMat = new THREE.MeshStandardMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.65,
        roughness: 0.2
      });
      const cube = new THREE.Mesh(cubeGeo, cubeMat);
      cube.position.set(x, y, z);
      cube.userData = {
        name: `Merkle Block #${i + 1}`,
        action: "inspect_merkle_block",
        details: `SHA-256 Verified. Parent hash linked. Nonce: ${1000 + i}`
      };
      this.groupMerkle.add(cube);
      this.merkleBlocks.push(cube);
      this.interactiveMeshes.push(cube);

      // Connecting laser beam to next block
      if (i > 0) {
        const prev = this.merkleBlocks[i - 1];
        const beamPts = [prev.position, cube.position];
        const beamGeo = new THREE.BufferGeometry().setFromPoints(beamPts);
        const beamMat = new THREE.LineBasicMaterial({ color: 0x34d399, transparent: true, opacity: 0.6 });
        const beam = new THREE.Line(beamGeo, beamMat);
        this.groupMerkle.add(beam);
      }
    }
  },

  // ---------------------------------------------------------------------------
  // 3D Scene Interactions & Raycasting
  // ---------------------------------------------------------------------------
  onMouseMove(e) {
    if (!this.wrapper || !this.raycaster || !this.camera) return;
    const rect = this.canvas.getBoundingClientRect();
    this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const visibleInteractive = this.interactiveMeshes.filter(m => m.visible && m.parent && m.parent.visible);
    const intersects = this.raycaster.intersectObjects(visibleInteractive);

    const hud = $("holoTooltipHUD");
    const raycastPill = $("hudRaycastTarget");

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      this.hoveredMesh = hit;
      this.canvas.style.cursor = "pointer";

      if (hud && hit.userData.name) {
        $("hudMeshName").textContent = hit.userData.name.toUpperCase();
        $("hudMeshDetails").textContent = hit.userData.details || "Click to interact.";
        hud.style.display = "block";
      }
      if (raycastPill && hit.userData.name) {
        raycastPill.textContent = hit.userData.name.slice(0, 16);
      }
    } else {
      this.hoveredMesh = null;
      this.canvas.style.cursor = "grab";
      if (hud) hud.style.display = "none";
      if (raycastPill) raycastPill.textContent = "SURFACE ACTIVE";
    }
  },

  onClick(e) {
    if (this.hoveredMesh && this.hoveredMesh.userData) {
      const action = this.hoveredMesh.userData.action;
      playSfx("click");

      if (action === "toggle_living_light") {
        const slider = $("livingBriSlider");
        if (slider) {
          const newVal = parseInt(slider.value, 10) > 0 ? 0 : 80;
          slider.value = newVal;
          slider.dispatchEvent(new Event("change"));
        }
      } else if (action === "toggle_lock") {
        togglePerimeterLock();
      } else if (action === "order_coffee") {
        triggerQuickPrompt("Reorder coffee and pantry essentials bundle");
      } else if (action === "inspect_climate") {
        alterClimate("living_room", 0.5);
      } else if (action === "inspect_dag_node" || action === "inspect_merkle_block") {
        playSfx("wake");
        addAssistantMessage(`**Holo-Inspector:** Inspected \`${this.hoveredMesh.userData.name}\`. Details: ${this.hoveredMesh.userData.details}`);
      }
    }
  },

  switchMode(mode) {
    currentMode = mode;
    if (!this.groupHolodeck) return;

    this.groupHolodeck.visible = (mode === "holodeck");
    this.groupNeural.visible = (mode === "neural");
    this.groupDag.visible = (mode === "dag");
    this.groupMerkle.visible = (mode === "merkle");

    const labelMap = {
      holodeck: "3D SMART HOLODECK",
      neural: "QUANTUM NEURAL HYPERSPHERE",
      dag: "3D REACT THOUGHT CONSTELLATION",
      merkle: "CHRONOS MERKLE HELIX"
    };
    if ($("active3DModeLabel")) $("active3DModeLabel").textContent = labelMap[mode] || mode.toUpperCase();

    document.querySelectorAll(".btn-holo-mode").forEach(btn => {
      btn.classList.toggle("active-mode", btn.dataset.mode === mode);
    });

    playSfx("wake");
  },

  cyclePalette() {
    const palettes = ["cyan", "solar", "matrix", "void"];
    const nextIdx = (palettes.indexOf(currentPalette) + 1) % palettes.length;
    currentPalette = palettes[nextIdx];

    const colors = {
      cyan: { main: 0x00f0ff, accent: 0x3b82f6 },
      solar: { main: 0xf59e0b, accent: 0xfbbf24 },
      matrix: { main: 0x10b981, accent: 0x059669 },
      void: { main: 0x8b5cf6, accent: 0x6366f1 }
    };
    const c = colors[currentPalette];

    if (this.livingLight) this.livingLight.color.setHex(c.main);
    if (this.livingLightBulb) this.livingLightBulb.material.color.setHex(c.main);
    if (this.neuralShell) this.neuralShell.material.color.setHex(c.main);

    playSfx("click");
  },

  toggleWireframe() {
    wireframeActive = !wireframeActive;
    this.scene.traverse(obj => {
      if (obj.isMesh && obj.material && !obj.material.isLineBasicMaterial) {
        obj.material.wireframe = wireframeActive;
      }
    });
    const btn = $("btnWireframe");
    if (btn) btn.classList.toggle("active-tool", wireframeActive);
    playSfx("click");
  },

  // ---------------------------------------------------------------------------
  // Main Animation Loop
  // ---------------------------------------------------------------------------
  animate() {
    requestAnimationFrame(() => this.animate());

    const now = performance.now();
    const delta = (now - this.lastTime) * 0.001;
    this.lastTime = now;

    // FPS Meter
    this.frameCount++;
    if (this.frameCount % 20 === 0) {
      this.currentFps = Math.round(1 / Math.max(delta, 0.001));
      if ($("hudFpsVal")) $("hudFpsVal").textContent = Math.min(this.currentFps, 60);
    }

    // 1. Controls Update
    if (this.controls) {
      this.controls.autoRotate = autoSpin;
      this.controls.update();
    }

    // 2. Mode Animations
    if (currentMode === "holodeck") {
      // Spinning HVAC Turbine
      if (this.hvacTurbine) this.hvacTurbine.rotation.y += 0.15;

      // Rising HVAC Particles
      this.hvacParticles.forEach(p => {
        const pos = p.geo.attributes.position.array;
        for (let i = 1; i < pos.length; i += 3) {
          pos[i] += 0.03;
          if (pos[i] > 3.2) pos[i] = 0.5;
        }
        p.geo.attributes.position.needsUpdate = true;
      });

      // Energy Conduit Line Dash Offset
      this.energyConduits.forEach(line => {
        line.material.dashSize = 0.4 + Math.sin(now * 0.005) * 0.15;
      });

    } else if (currentMode === "neural") {
      if (this.neuralShell) {
        this.neuralShell.rotation.y += 0.008;
        this.neuralShell.rotation.x += 0.004;
      }
      if (this.neuralGimbalRing1) this.neuralGimbalRing1.rotation.z += 0.015;
      if (this.neuralGimbalRing2) this.neuralGimbalRing2.rotation.y += 0.012;
      if (this.neuralParticles) this.neuralParticles.rotation.y += 0.003;

      // Reactive pulse to agent execution
      if (isExecutingAgent && this.neuralCoreSphere) {
        const s = 1.0 + Math.sin(now * 0.01) * 0.15;
        this.neuralCoreSphere.scale.set(s, s, s);
      }

    } else if (currentMode === "dag") {
      // Rotate DAG crystal nodes
      this.dagNodeMeshes.forEach((mesh, idx) => {
        mesh.rotation.y += 0.02 * (idx % 2 === 0 ? 1 : -1);
      });

      // Advance Traveling Photon Sprites along 3D Splines
      this.dagSplinePhotons.forEach(pt => {
        pt.progress = (pt.progress + delta * 0.25) % 1.0;
        const coord = pt.curve.getPointAt(pt.progress);
        pt.mesh.position.copy(coord);
      });

    } else if (currentMode === "merkle") {
      if (this.groupMerkle) this.groupMerkle.rotation.y += 0.006;
      this.merkleBlocks.forEach(b => {
        b.rotation.x += 0.01;
        b.rotation.y += 0.01;
      });
    }

    // 3. Render WebGL
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }

    // 4. Update HUD Audio Equalizer
    drawAudioSpectrum();
  }
};

// =============================================================================
// 3. Mini Header Orb Canvas Visualizer
// =============================================================================
function initMiniHeaderOrb() {
  const canvas = $("orbMiniCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  const cx = W / 2;
  const cy = H / 2;

  let t = 0;
  function render() {
    t += 0.04;
    ctx.clearRect(0, 0, W, H);

    // Glowing core
    const radGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 20);
    radGrad.addColorStop(0, "#ffffff");
    radGrad.addColorStop(0.4, "#00f0ff");
    radGrad.addColorStop(1, "transparent");
    ctx.fillStyle = radGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, 18, 0, Math.PI * 2);
    ctx.fill();

    // Orbital ring
    ctx.strokeStyle = "rgba(0, 240, 255, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(cx, cy, 20, 8, t * 0.5, 0, Math.PI * 2);
    ctx.stroke();

    requestAnimationFrame(render);
  }
  render();
}

// =============================================================================
// 4. Conversational Alexa+ Core & Autonomous ReAct Engine
// =============================================================================
async function sendUserPrompt(overrideText = null) {
  const input = $("userPromptInput");
  const prompt = (overrideText || (input ? input.value : "")).trim();
  if (!prompt) return;

  if (input) input.value = "";
  playSfx("wake");

  addUserMessage(prompt);
  isExecutingAgent = true;

  // Show live visual DAG node flow
  const dagCard = $("dagCard");
  const dagFlow = $("dagNodeFlow");
  if (dagCard && dagFlow) {
    dagCard.style.display = "block";
    dagFlow.innerHTML = `
      <div class="dag-node status-completed">
        <div class="node-label"><span>📥</span> Stimulus</div>
        <div class="node-subtext">${escapeHtml(prompt.slice(0, 20))}...</div>
      </div>
      <div class="node-arrow">➔</div>
      <div class="dag-node">
        <div class="node-label"><span>🛡️</span> Sentinel</div>
        <div class="node-subtext">Security Scan</div>
      </div>
      <div class="node-arrow">➔</div>
      <div class="dag-node">
        <div class="node-label"><span>🧠</span> ReAct</div>
        <div class="node-subtext">Planning</div>
      </div>
    `;
  }

  const startTime = performance.now();
  const brain = $("brainSelector") ? $("brainSelector").value : "local";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt, brain_override: brain })
    });
    const data = await res.json();
    const elapsed = (performance.now() - startTime).toFixed(1);

    if ($("latencyTelemetryBadge")) {
      $("latencyTelemetryBadge").textContent = `Latency: ${elapsed}ms`;
    }

    if (data.ok) {
      addAssistantMessage(data.reply, data.steps || []);
      if (data.steps && data.steps.length > 0) {
        renderDagNodes(data.steps);
      }
      if (ttsEnabled && data.reply) {
        speakText(data.reply);
      }
    } else {
      addAssistantMessage(`⚠️ **Agent Error**: ${data.error || "Failed to process request."}`);
      playSfx("alert");
    }
  } catch (err) {
    addAssistantMessage(`🚨 **Connection Error**: ${err.message}`);
    playSfx("alert");
  } finally {
    isExecutingAgent = false;
    refreshTelemetry();
  }
}

function triggerQuickPrompt(txt) {
  playSfx("click");
  sendUserPrompt(txt);
}

function addUserMessage(txt) {
  const vp = $("chatViewport");
  if (!vp) return;
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble bubble-user";
  bubble.innerHTML = `<div class="bubble-content"><p>${escapeHtml(txt)}</p></div>`;
  vp.appendChild(bubble);
  vp.scrollTop = vp.scrollHeight;
}

function addAssistantMessage(txt, steps = []) {
  const vp = $("chatViewport");
  if (!vp) return;
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble bubble-alexa";

  let stepSummary = "";
  if (steps && steps.length > 0) {
    stepSummary = `<div style="margin-top: 8px; font-size: 11.5px; color: var(--alexa-cyan);">
      ⚡ Executed ${steps.length} ReAct actions (${steps.map(s => `<code>${s.tool || s.type}</code>`).join(", ")})
    </div>`;
  }

  bubble.innerHTML = `
    <div class="bubble-header">
      <span>Alexa+ Universal Core</span>
      <button class="btn-audio-speak" onclick="speakText('${escapeAttr(txt)}')">🔊 Listen</button>
    </div>
    <div class="bubble-content">
      ${formatMarkdown(txt)}
      ${stepSummary}
    </div>
  `;
  vp.appendChild(bubble);
  vp.scrollTop = vp.scrollHeight;
}

function renderDagNodes(steps) {
  const flow = $("dagNodeFlow");
  if (!flow) return;

  const html = steps.map((s, idx) => {
    const isCompleted = s.status === "completed" || s.decision === "pass";
    const isGated = s.status === "gated";
    const isBlocked = s.decision === "block";

    let stateClass = "status-completed";
    if (isGated) stateClass = "status-gated";
    if (isBlocked) stateClass = "status-blocked";

    return `
      <div class="dag-node ${stateClass}">
        <div class="node-label">
          <span>${s.tool ? "🛠️" : "🧠"}</span> ${escapeHtml(s.tool || s.type || `Step ${idx + 1}`)}
        </div>
        <div class="node-subtext">${escapeHtml(s.summary || s.decision || "Executed")}</div>
      </div>
      ${idx < steps.length - 1 ? '<div class="node-arrow">➔</div>' : ''}
    `;
  }).join("");

  flow.innerHTML = html;
}

// =============================================================================
// 5. Digital Twin & Multi-Modal Telemetry Synchronization
// =============================================================================
async function refreshTelemetry() {
  try {
    const res = await fetch("/api/telemetry");
    if (!res.ok) return;
    const data = await res.json();
    currentHomeState = data;

    // 1. Update Living Room Light
    const livingBri = data.living_room?.lights?.brightness ?? 80;
    const livingOn = data.living_room?.lights?.on ?? true;
    const briLabel = $("livingBriLabel");
    if (briLabel) briLabel.textContent = livingOn ? `${livingBri}% Warm` : "0% Off";

    // Sync with 3D Holodeck Scene
    if (HoloScene.livingLight) {
      HoloScene.livingLight.intensity = livingOn ? (livingBri / 100) * 2.0 : 0.0;
    }
    if (HoloScene.livingLightBulb) {
      HoloScene.livingLightBulb.material.color.setHex(livingOn ? 0x00f0ff : 0x334155);
    }

    // 2. Update Front Door Lock
    const lockLocked = data.front_door?.lock?.locked ?? true;
    const lockPill = $("lockStatusPill");
    if (lockPill) {
      lockPill.textContent = lockLocked ? "LOCKED" : "UNLOCKED";
      lockPill.className = `status-pill ${lockLocked ? 'live-green' : 'live-cyan'}`;
    }

    // Sync 3D Deadbolt Cylinder & Laser Barrier
    if (HoloScene.deadboltLatch) {
      HoloScene.deadboltLatch.position.x = lockLocked ? -0.85 : -1.2;
    }
    if (HoloScene.deadboltLaserPlane) {
      HoloScene.deadboltLaserPlane.material.color.setHex(lockLocked ? 0xef4444 : 0x10b981);
    }

    // 3. Update Pending Proposals Tray Badge
    const pRes = await fetch("/api/proposals");
    if (pRes.ok) {
      const pData = await pRes.json();
      const count = pData.count || 0;
      if ($("pendingTrayBadge")) $("pendingTrayBadge").textContent = count;
      renderProposals(pData.proposals || []);
    }

    // 4. Update Commerce Data
    const cRes = await fetch("/api/commerce");
    if (cRes.ok) {
      const cData = await cRes.json();
      renderCommerce(cData);
    }
  } catch (e) {
    console.debug("Telemetry poll tick", e);
  }
}

// Alter Climate Setpoint
async function alterClimate(room, delta) {
  playSfx("click");
  const display = room === "living_room" ? $("livingTempDisplay") : $("bedroomTempDisplay");
  if (!display) return;
  let cur = parseFloat(display.textContent) || 22.0;
  cur = Math.round((cur + delta) * 10) / 10;
  display.textContent = `${cur.toFixed(1)}°C`;

  await fetch("/api/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room,
      device: "thermostat",
      patch: { setpoint: cur }
    })
  });
}

// Toggle Perimeter Smart Lock
async function togglePerimeterLock() {
  const isLocked = $("lockStatusPill")?.textContent === "LOCKED";
  const newLocked = !isLocked;
  playSfx("lock");

  if ($("lockStatusPill")) {
    $("lockStatusPill").textContent = newLocked ? "LOCKED" : "UNLOCKED";
    $("lockStatusPill").className = `status-pill ${newLocked ? 'live-green' : 'live-cyan'}`;
  }

  // Animate 3D Holodeck Deadbolt
  if (HoloScene.deadboltLatch) {
    HoloScene.deadboltLatch.position.x = newLocked ? -0.85 : -1.2;
  }
  if (HoloScene.deadboltLaserPlane) {
    HoloScene.deadboltLaserPlane.material.color.setHex(newLocked ? 0xef4444 : 0x10b981);
  }

  await fetch("/api/devices/front_door_lock", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ locked: newLocked })
  });
}

// One-Tap Coordinated Scenes
async function dispatchScene(sceneId) {
  playSfx("wake");
  document.querySelectorAll(".btn-scene-card").forEach(b => b.classList.remove("active-scene"));
  event.currentTarget.classList.add("active-scene");

  triggerQuickPrompt(`Activate ${sceneId} home scene`);
}

// =============================================================================
// 6. Glass-Box Approval Tray & Proposals Engine
// =============================================================================
function renderProposals(proposals) {
  const container = $("contractsList");
  if (!container) return;

  if (!proposals || proposals.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-tertiary); padding: 40px 0;">
        No pending action proposals. Ask Alexa+ to <i>"Save me $437 on renewals"</i> or <i>"Reorder coffee"</i> to generate action drafts.
      </div>
    `;
    return;
  }

  container.innerHTML = proposals.map(p => `
    <div class="contract-card" id="card-${p.id}">
      <div class="contract-header">
        <div>
          <div class="contract-title">🛡️ ${escapeHtml(p.action)}</div>
          <div class="contract-id-badge font-mono">ID: ${p.id} · ${p.created_at || 'Just now'}</div>
        </div>
        <span class="status-pill live-cyan font-mono">${escapeHtml(p.status || 'PENDING')}</span>
      </div>
      <div class="contract-reasoning">${escapeHtml(p.reason || 'Consequential action requiring human authorization.')}</div>
      <div class="diff-box">
        <strong>Parameters:</strong> ${JSON.stringify(p.params, null, 2)}
      </div>
      <div class="contract-action-bar">
        <button class="btn-approve-quantum" onclick="decideProposal('${p.id}', 'approve')">
          ✓ Approve & Execute
        </button>
        <button class="btn-reject-quantum" onclick="decideProposal('${p.id}', 'reject')">
          ✕ Dismiss
        </button>
      </div>
    </div>
  `).join("");
}

async function decideProposal(propId, decision) {
  playSfx(decision === "approve" ? "approve" : "click");
  const card = $(`card-${propId}`);
  if (card) card.style.opacity = "0.5";

  try {
    const res = await fetch(`/api/proposals/${propId}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision })
    });
    const data = await res.json();
    if (data.ok) {
      addAssistantMessage(`Contract **${propId}** was **${decision.toUpperCase()}D** by human operator.`);
    }
  } catch (err) {
    console.error("Decision failed", err);
  } finally {
    refreshTelemetry();
  }
}

// =============================================================================
// 7. Subscriptions, Consumables & Memory Listings
// =============================================================================
function renderCommerce(data) {
  const inv = data.inventory || [];
  const subs = inv.filter(i => i.is_subscription);
  const pantry = inv.filter(i => !i.is_subscription);

  const subsContainer = $("subsListing");
  if (subsContainer) {
    subsContainer.innerHTML = subs.map(s => `
      <div class="commerce-item-tile">
        <div>
          <div style="font-weight: 700; color: #ffffff;">${escapeHtml(s.name)}</div>
          <div style="font-size: 11px; color: var(--text-secondary);">$${s.monthly_cost}/mo · Status: ${s.usage_status}</div>
        </div>
        <span class="status-pill ${s.usage_status === 'unused' ? 'live-cyan' : ''}">
          ${s.usage_status === 'unused' ? 'Flagged Renewal' : 'Active'}
        </span>
      </div>
    `).join("");
  }

  const pantryContainer = $("pantryListing");
  if (pantryContainer) {
    pantryContainer.innerHTML = pantry.map(p => {
      const pct = Math.round((p.qty_current / (p.qty_target || 100)) * 100);
      const isLow = pct < 25;
      return `
        <div class="commerce-item-tile">
          <div>
            <div style="font-weight: 700; color: #ffffff;">${escapeHtml(p.name)}</div>
            <div style="font-size: 11px; color: var(--text-secondary);">${pct}% Remaining (${p.qty_current} units)</div>
            <div class="pantry-progress-track">
              <div class="pantry-progress-fill" style="width: ${pct}%; background: ${isLow ? '#ef4444' : '#10b981'};"></div>
            </div>
          </div>
          <button class="btn-ambient" onclick="triggerQuickPrompt('Reorder ${escapeAttr(p.name)}')">Reorder</button>
        </div>
      `;
    }).join("");
  }
}

async function loadMerkleAudit() {
  playSfx("click");
  const dialog = $("auditModalDialog");
  const tbody = $("merkleTableBody");
  if (!dialog || !tbody) return;

  try {
    const res = await fetch("/api/audit");
    const data = await res.json();
    const rows = data.recent || [];

    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${new Date((r.timestamp || 0) * 1000).toLocaleTimeString()}</td>
        <td><span class="status-pill">${escapeHtml(r.actor || 'agent')}</span></td>
        <td><strong>${escapeHtml(r.action || '')}</strong></td>
        <td><code style="color: var(--alexa-cyan);">${(r.hash || '').slice(0, 18)}...</code></td>
      </tr>
    `).join("");

    dialog.showModal();
  } catch (err) {
    console.error("Failed to load audit ledger", err);
  }
}

// =============================================================================
// 8. Web Speech Synthesis & Recognition (Voice Interaction)
// =============================================================================
function speakText(txt) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const clean = txt.replace(/[*_#`]/g, "");
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;

  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    const btn = $("micCaptureBtn");
    if (btn) btn.classList.add("recording");
    playSfx("wake");
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    if ($("userPromptInput")) $("userPromptInput").value = transcript;
    sendUserPrompt(transcript);
  };

  recognition.onend = () => {
    isRecording = false;
    const btn = $("micCaptureBtn");
    if (btn) btn.classList.remove("recording");
  };
}

function toggleMic() {
  if (!recognition) {
    initSpeechRecognition();
  }
  if (!recognition) {
    alert("Speech recognition is not supported in this browser.");
    return;
  }
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// =============================================================================
// 9. Utility Formatting
// =============================================================================
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m]));
}

function escapeAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatMarkdown(md) {
  if (!md) return "";
  let html = escapeHtml(md);
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  return `<p>${html.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`;
}

// =============================================================================
// 10. Initialization & Event Binding
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize Three.js 4D Holo-Nexus Scene
  HoloScene.init();

  // 2. Initialize Mini Header Orb
  initMiniHeaderOrb();

  // 3. Initialize Speech
  initSpeechRecognition();

  // 4. Setup 3D Mode Selector Buttons
  document.querySelectorAll(".btn-holo-mode").forEach(btn => {
    btn.addEventListener("click", () => {
      HoloScene.switchMode(btn.dataset.mode);
    });
  });

  // 5. Setup 3D Viewport Action Tools
  if ($("btnAutoSpin")) {
    $("btnAutoSpin").addEventListener("click", () => {
      autoSpin = !autoSpin;
      $("btnAutoSpin").classList.toggle("active-tool", autoSpin);
      playSfx("click");
    });
  }

  if ($("btnCamAngle")) {
    $("btnCamAngle").addEventListener("click", () => {
      const presets = ["iso", "top", "front"];
      const next = presets[(presets.indexOf(activeCamPreset) + 1) % presets.length];
      HoloScene.setCameraPreset(next);
      playSfx("click");
    });
  }

  if ($("btnColorTheme")) {
    $("btnColorTheme").addEventListener("click", () => {
      HoloScene.cyclePalette();
    });
  }

  if ($("btnWireframe")) {
    $("btnWireframe").addEventListener("click", () => {
      HoloScene.toggleWireframe();
    });
  }

  if ($("btnStageFullscreen")) {
    $("btnStageFullscreen").addEventListener("click", () => {
      const card = $("holoStageCard");
      if (card) {
        card.classList.toggle("stage-fullscreen");
        HoloScene.onResize();
        playSfx("click");
      }
    });
  }

  // 6. Navigation Tabs
  document.querySelectorAll(".control-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      playSfx("click");
      document.querySelectorAll(".control-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-stage-content").forEach(c => c.style.display = "none");
      btn.classList.add("active");
      const target = $(btn.dataset.tab);
      if (target) target.style.display = "block";
    });
  });

  // 7. Input Events
  if ($("sendPromptBtn")) {
    $("sendPromptBtn").addEventListener("click", () => sendUserPrompt());
  }
  if ($("userPromptInput")) {
    $("userPromptInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendUserPrompt();
    });
  }
  if ($("micCaptureBtn")) {
    $("micCaptureBtn").addEventListener("click", () => toggleMic());
  }

  // 8. Toggles
  if ($("sfxToggleBtn")) {
    $("sfxToggleBtn").addEventListener("click", () => {
      sfxEnabled = !sfxEnabled;
      $("sfxToggleBtn").textContent = sfxEnabled ? "🔊 SFX: ON" : "🔇 SFX: OFF";
      playSfx("click");
    });
  }
  if ($("ttsToggleBtn")) {
    $("ttsToggleBtn").addEventListener("click", () => {
      ttsEnabled = !ttsEnabled;
      $("ttsToggleBtn").textContent = ttsEnabled ? "🗣️ Voice: ON" : "🔇 Voice: OFF";
      playSfx("click");
    });
  }
  if ($("auditModalTriggerBtn")) {
    $("auditModalTriggerBtn").addEventListener("click", () => loadMerkleAudit());
  }
  if ($("resetSystemBtn")) {
    $("resetSystemBtn").addEventListener("click", async () => {
      playSfx("click");
      await fetch("/api/reset", { method: "POST" });
      refreshTelemetry();
      addAssistantMessage("System state has been reset to baseline clean state.");
    });
  }

  // 9. Slider Events
  if ($("livingBriSlider")) {
    $("livingBriSlider").addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      if ($("livingBriLabel")) $("livingBriLabel").textContent = `${val}% Warm`;
      if (HoloScene.livingLight) HoloScene.livingLight.intensity = (val / 100) * 2.0;
    });
    $("livingBriSlider").addEventListener("change", async (e) => {
      const val = parseInt(e.target.value, 10);
      await fetch("/api/devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          room: "living_room",
          device: "lights",
          patch: { brightness: val, on: val > 0 }
        })
      });
      refreshTelemetry();
    });
  }

  // 10. Initial Telemetry & Recurring Polling
  refreshTelemetry();
  setInterval(refreshTelemetry, 3000);
});
