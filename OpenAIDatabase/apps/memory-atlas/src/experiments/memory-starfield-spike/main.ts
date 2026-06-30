import * as THREE from "three";
import { memoryStarfieldFixture, type MemoryClusterFixture } from "./fixture";

type Quality = "high" | "mid" | "low";

type ParticleSystemState = {
  positions: Float32Array;
  velocities: Float32Array;
  clusterIndexes: Uint16Array;
  phases: Float32Array;
  geometry: THREE.BufferGeometry;
  points: THREE.Points;
};

type SpikeMetrics = {
  particleCount: number;
  fps: number;
  quality: Quality;
  hoveredClusterId: string | null;
  consoleErrors: number;
};

declare global {
  interface Window {
    __memoryStarfieldSpike?: {
      metrics: SpikeMetrics;
      fixture: typeof memoryStarfieldFixture;
    };
  }
}

const PARTICLE_COUNTS: Record<Quality, number> = {
  high: 12000,
  mid: 10000,
  low: 8000,
};

const app = requireElement<HTMLDivElement>("app");
const particleCountElement = requireElement<HTMLElement>("particleCount");
const fpsReadoutElement = requireElement<HTMLElement>("fpsReadout");
const qualityReadoutElement = requireElement<HTMLElement>("qualityReadout");
const qualityControl = requireElement<HTMLSelectElement>("qualityControl");
const flowControl = requireElement<HTMLInputElement>("flowControl");
const reducedMotionControl = requireElement<HTMLInputElement>("reducedMotionControl");
const hoverCard = requireElement<HTMLElement>("hoverCard");
const smokeStatus = requireElement<HTMLElement>("smokeStatus");
const smokeMode = new URLSearchParams(window.location.search).get("smoke") === "1";
const smokeMaxFrames = 96;

const metrics: SpikeMetrics = {
  particleCount: PARTICLE_COUNTS.mid,
  fps: 0,
  quality: "mid",
  hoveredClusterId: null,
  consoleErrors: 0,
};

window.__memoryStarfieldSpike = {
  metrics,
  fixture: memoryStarfieldFixture,
};

window.addEventListener("error", () => {
  metrics.consoleErrors += 1;
});

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x03050a, 1);
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x050812, 0.035);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 80);
camera.position.set(0, 1.4, 7.2);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2(99, 99);
const clock = new THREE.Clock();
const clusterObjects: THREE.Mesh[] = [];
const clusters = memoryStarfieldFixture.clusters;

const ambientLight = new THREE.AmbientLight(0xc8e6ff, 0.78);
scene.add(ambientLight);

const keyLight = new THREE.PointLight(0x8fd3ff, 16, 22);
keyLight.position.set(-3.5, 4.2, 5.5);
scene.add(keyLight);

const protoLight = new THREE.PointLight(0xffef9a, 14, 12);
protoLight.position.fromArray(findCluster("proto_star").position);
scene.add(protoLight);

const disk = createGravitationalDisk();
scene.add(disk);

for (const cluster of clusters) {
  const marker = createClusterMarker(cluster);
  clusterObjects.push(marker);
  scene.add(marker);
}

const nebula = createNebulaDust(1800);
scene.add(nebula);

let particleSystem = createParticleSystem(metrics.particleCount);
scene.add(particleSystem.points);

let frameCount = 0;
let totalFrames = 0;
let fpsWindowStart = performance.now();
let animationStart = performance.now();
let simulationFrame = 0;

qualityControl.addEventListener("change", () => {
  const quality = qualityControl.value as Quality;
  setQuality(quality);
});

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

window.addEventListener("pointermove", (event) => {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
});

function animate() {
  totalFrames += 1;
  const elapsed = clock.getElapsedTime();
  const delta = Math.min(clock.getDelta(), 0.033);
  const reducedMotion = reducedMotionControl.checked;
  const flowScale = Number(flowControl.value) * (reducedMotion ? 0.25 : 1);

  simulationFrame += 1;
  if (simulationFrame % 2 === 0) {
    updateParticles(particleSystem, elapsed, delta * 2, flowScale);
  }
  updateSceneMotion(elapsed, reducedMotion);
  updateHover();
  updateFps();

  renderer.render(scene, camera);

  if (smokeMode && totalFrames >= smokeMaxFrames) {
    const elapsedMs = Math.max(1, performance.now() - animationStart);
    metrics.fps = Math.max(metrics.fps, Math.round((totalFrames / elapsedMs) * 1000));
    syncMetrics();
    return;
  }

  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
syncMetrics();

function createParticleSystem(count: number): ParticleSystemState {
  const positions = new Float32Array(count * 3);
  const velocities = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const clusterIndexes = new Uint16Array(count);
  const phases = new Float32Array(count);
  const totalMass = clusters.reduce((sum, cluster) => sum + cluster.mass, 0);

  for (let index = 0; index < count; index += 1) {
    const clusterIndex = weightedClusterIndex(index / count, totalMass);
    const cluster = clusters[clusterIndex];
    const clusterPosition = new THREE.Vector3().fromArray(cluster.position);
    const orbitRadius = 0.25 + seededRandom(index, 3) * (1.25 + cluster.mass);
    const angle = seededRandom(index, 7) * Math.PI * 2;
    const height = (seededRandom(index, 11) - 0.5) * 0.75;
    const spiral = angle + orbitRadius * 0.85;
    const x = clusterPosition.x + Math.cos(spiral) * orbitRadius;
    const y = clusterPosition.y + height;
    const z = clusterPosition.z + Math.sin(spiral) * orbitRadius * 0.72;
    const color = new THREE.Color(cluster.color).lerp(new THREE.Color("#dff7ff"), seededRandom(index, 17) * 0.28);

    positions[index * 3] = x;
    positions[index * 3 + 1] = y;
    positions[index * 3 + 2] = z;
    velocities[index * 3] = (seededRandom(index, 19) - 0.5) * 0.002;
    velocities[index * 3 + 1] = (seededRandom(index, 23) - 0.5) * 0.002;
    velocities[index * 3 + 2] = (seededRandom(index, 29) - 0.5) * 0.002;
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
    clusterIndexes[index] = clusterIndex;
    phases[index] = seededRandom(index, 31) * Math.PI * 2;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3).setUsage(THREE.DynamicDrawUsage));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.028,
    sizeAttenuation: true,
    vertexColors: true,
    transparent: true,
    opacity: 0.86,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });

  const points = new THREE.Points(geometry, material);
  points.name = "Memory starfield particles";

  return { positions, velocities, clusterIndexes, phases, geometry, points };
}

function updateParticles(state: ParticleSystemState, elapsed: number, delta: number, flowScale: number) {
  const positions = state.positions;
  const velocities = state.velocities;
  const speed = 18 * delta;

  for (let index = 0; index < state.clusterIndexes.length; index += 1) {
    const offset = index * 3;
    const cluster = clusters[state.clusterIndexes[index]];
    const target = cluster.position;
    const px = positions[offset];
    const py = positions[offset + 1];
    const pz = positions[offset + 2];
    const dx = target[0] - px;
    const dy = target[1] - py;
    const dz = target[2] - pz;
    const distSq = Math.max(0.12, dx * dx + dy * dy + dz * dz);
    const gravity = (0.00038 + cluster.mass * 0.00019) / distSq;
    const phase = state.phases[index] + elapsed * 0.42;
    const curlX = Math.sin(py * 1.7 + phase) * 0.0009;
    const curlY = Math.cos((px + pz) * 1.3 + phase) * 0.00042;
    const curlZ = Math.sin(px * 1.5 - phase) * 0.0009;
    const blackHoleFactor = cluster.kind === "black_hole" ? 1.9 : 1;
    const protoFactor = cluster.kind === "proto_star" ? 1.35 : 1;

    velocities[offset] = (velocities[offset] + dx * gravity * blackHoleFactor + curlX * flowScale * protoFactor) * 0.992;
    velocities[offset + 1] = (velocities[offset + 1] + dy * gravity * 0.6 + curlY * flowScale) * 0.992;
    velocities[offset + 2] = (velocities[offset + 2] + dz * gravity * blackHoleFactor + curlZ * flowScale * protoFactor) * 0.992;
    positions[offset] += velocities[offset] * speed;
    positions[offset + 1] += velocities[offset + 1] * speed;
    positions[offset + 2] += velocities[offset + 2] * speed;
  }

  const positionAttribute = state.geometry.getAttribute("position");
  positionAttribute.needsUpdate = true;
}

function createClusterMarker(cluster: MemoryClusterFixture) {
  const radius = cluster.kind === "black_hole" ? 0.18 : cluster.kind === "proto_star" ? 0.13 : 0.09 + cluster.mass * 0.035;
  const geometry = cluster.kind === "black_hole" ? new THREE.IcosahedronGeometry(radius, 2) : new THREE.SphereGeometry(radius, 24, 16);
  const material = new THREE.MeshStandardMaterial({
    color: cluster.kind === "black_hole" ? "#050712" : cluster.color,
    emissive: cluster.kind === "black_hole" ? "#02030a" : cluster.color,
    emissiveIntensity: cluster.kind === "proto_star" ? 1.7 : 0.55,
    roughness: 0.48,
    metalness: 0.12,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.fromArray(cluster.position);
  mesh.userData = { clusterId: cluster.id };

  if (cluster.kind === "black_hole") {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(radius * 1.85, 0.012, 8, 64),
      new THREE.MeshBasicMaterial({ color: "#6f7d96", transparent: true, opacity: 0.72 }),
    );
    ring.rotation.x = Math.PI / 2.8;
    mesh.add(ring);
  }

  if (cluster.kind === "proto_star") {
    const halo = new THREE.Mesh(
      new THREE.SphereGeometry(radius * 2.3, 24, 16),
      new THREE.MeshBasicMaterial({ color: cluster.color, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending }),
    );
    mesh.add(halo);
  }

  return mesh;
}

function createGravitationalDisk() {
  const group = new THREE.Group();
  for (let ringIndex = 0; ringIndex < 5; ringIndex += 1) {
    const radius = 1.1 + ringIndex * 0.62;
    const geometry = new THREE.TorusGeometry(radius, 0.004 + ringIndex * 0.0015, 8, 160);
    const material = new THREE.MeshBasicMaterial({
      color: ringIndex % 2 === 0 ? "#2a80b9" : "#7ee8d4",
      transparent: true,
      opacity: 0.1 - ringIndex * 0.01,
      blending: THREE.AdditiveBlending,
    });
    const ring = new THREE.Mesh(geometry, material);
    ring.rotation.x = Math.PI / 2.16;
    ring.rotation.z = ringIndex * 0.24;
    group.add(ring);
  }
  return group;
}

function createNebulaDust(count: number) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const palette = ["#1b7fb3", "#7ee8d4", "#f7cf6b", "#b9a8ff"];
  for (let index = 0; index < count; index += 1) {
    const radius = 1.4 + seededRandom(index, 41) * 3.7;
    const angle = seededRandom(index, 43) * Math.PI * 2;
    const color = new THREE.Color(palette[index % palette.length]);
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = (seededRandom(index, 47) - 0.5) * 2.6;
    positions[index * 3 + 2] = Math.sin(angle) * radius * 0.7;
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 0.055,
    sizeAttenuation: true,
    vertexColors: true,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  return new THREE.Points(geometry, material);
}

function updateSceneMotion(elapsed: number, reducedMotion: boolean) {
  const motion = reducedMotion ? 0.08 : 1;
  disk.rotation.z = elapsed * 0.025 * motion;
  nebula.rotation.y = elapsed * 0.012 * motion;
  particleSystem.points.rotation.y = Math.sin(elapsed * 0.08) * 0.04 * motion;
  for (const marker of clusterObjects) {
    marker.rotation.y += 0.004 * motion;
  }
  camera.position.x = Math.sin(elapsed * 0.08) * 0.24 * motion;
  camera.lookAt(0, 0, 0);
}

function updateHover() {
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(clusterObjects, true);
  const clusterId = hits.find((hit) => findClusterByChild(hit.object))?.object ? findClusterByChild(hits[0].object)?.userData.clusterId as string | undefined : undefined;
  const cluster = clusterId ? clusters.find((item) => item.id === clusterId) : null;

  if (!cluster) {
    metrics.hoveredClusterId = null;
    hoverCard.dataset.empty = "true";
    hoverCard.innerHTML = "<h2>Hover cluster</h2><p>聚焦星团可查看 redacted 摘要、confidence 和 evidence count。Spike 不读取 raw/private 数据。</p>";
    return;
  }

  metrics.hoveredClusterId = cluster.id;
  hoverCard.dataset.empty = "false";
  hoverCard.innerHTML = `<h2>${cluster.label}</h2><p>${cluster.summary}</p><p>Kind: ${cluster.kind} · Confidence: ${Math.round(cluster.confidence * 100)}% · Evidence: ${cluster.evidenceCount}</p>`;
}

function findClusterByChild(object: THREE.Object3D): THREE.Mesh | null {
  let current: THREE.Object3D | null = object;
  while (current) {
    if (current instanceof THREE.Mesh && typeof current.userData.clusterId === "string") return current;
    current = current.parent;
  }
  return null;
}

function setQuality(quality: Quality) {
  metrics.quality = quality;
  metrics.particleCount = PARTICLE_COUNTS[quality];
  scene.remove(particleSystem.points);
  particleSystem.geometry.dispose();
  const material = particleSystem.points.material;
  if (Array.isArray(material)) {
    material.forEach((item) => item.dispose());
  } else {
    material.dispose();
  }
  particleSystem = createParticleSystem(metrics.particleCount);
  scene.add(particleSystem.points);
  syncMetrics();
}

function updateFps() {
  frameCount += 1;
  const now = performance.now();
  const elapsedMs = now - fpsWindowStart;
  if (elapsedMs < 500) return;
  metrics.fps = Math.round((frameCount / elapsedMs) * 1000);
  frameCount = 0;
  fpsWindowStart = now;
  syncMetrics();
}

function syncMetrics() {
  particleCountElement.textContent = String(metrics.particleCount);
  fpsReadoutElement.textContent = String(metrics.fps);
  qualityReadoutElement.textContent = metrics.quality;
  smokeStatus.textContent = JSON.stringify({
    ...metrics,
    fixtureSchemaVersion: memoryStarfieldFixture.schemaVersion,
    rawPrivateDataIncluded: memoryStarfieldFixture.rawPrivateDataIncluded,
    plaintextSecretsIncluded: memoryStarfieldFixture.plaintextSecretsIncluded,
    localAbsolutePathsIncluded: memoryStarfieldFixture.localAbsolutePathsIncluded,
  });
}

function weightedClusterIndex(unitValue: number, totalMass: number) {
  let cursor = 0;
  for (let index = 0; index < clusters.length; index += 1) {
    cursor += clusters[index].mass / totalMass;
    if (unitValue <= cursor) return index;
  }
  return clusters.length - 1;
}

function seededRandom(index: number, salt: number) {
  const x = Math.sin(index * 12.9898 + salt * 78.233 + 20260628) * 43758.5453;
  return x - Math.floor(x);
}

function findCluster(kind: MemoryClusterFixture["kind"]) {
  const cluster = clusters.find((item) => item.kind === kind);
  if (!cluster) throw new Error(`Missing cluster kind ${kind}`);
  return cluster;
}

function requireElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing element #${id}`);
  return element as T;
}
