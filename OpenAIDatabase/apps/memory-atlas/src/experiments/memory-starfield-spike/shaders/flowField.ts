export type FlowFieldVector = {
  x: number;
  y: number;
  z: number;
};

export const FLOW_FIELD_SHADER_CONTRACT =
  "memory_starfield_c3_spike.v1_1_7_stage4_phase2:curl_noise_shader";

export function sampleCurlNoise(x: number, y: number, z: number, time: number): FlowFieldVector {
  const nx = Math.sin(y * 1.7 + time * 0.42) - Math.cos(z * 1.1 - time * 0.31);
  const ny = Math.cos((x + z) * 1.3 + time * 0.28) * 0.5;
  const nz = Math.sin(x * 1.5 - time * 0.37) - Math.cos(y * 1.2 + time * 0.22);
  return { x: nx, y: ny, z: nz };
}

export function buildFlowFieldVector(
  position: FlowFieldVector,
  phase: number,
  elapsed: number,
  strength: number,
  reducedMotion: boolean,
): FlowFieldVector {
  const motionScale = reducedMotion ? 0.25 : 1;
  const curl = sampleCurlNoise(position.x + phase * 0.07, position.y, position.z - phase * 0.05, elapsed);
  return {
    x: curl.x * 0.0009 * strength * motionScale,
    y: curl.y * 0.00042 * strength * motionScale,
    z: curl.z * 0.0009 * strength * motionScale,
  };
}

export const STARFIELD_VERTEX_SHADER = `
uniform float uTime;
uniform float uFlowStrength;
uniform float uReducedMotion;
uniform float uPixelRatio;
attribute float particlePhase;
varying vec3 vColor;

void main() {
  float motion = mix(1.0, 0.25, uReducedMotion);
  vec3 displaced = position;
  displaced.x += sin(position.y * 1.7 + particlePhase + uTime * 0.42) * 0.055 * uFlowStrength * motion;
  displaced.y += cos((position.x + position.z) * 1.3 + particlePhase + uTime * 0.28) * 0.026 * uFlowStrength * motion;
  displaced.z += sin(position.x * 1.5 - particlePhase - uTime * 0.37) * 0.055 * uFlowStrength * motion;
  vColor = color;
  vec4 mvPosition = modelViewMatrix * vec4(displaced, 1.0);
  gl_PointSize = max(1.8, 3.4 * uPixelRatio * (1.0 / max(0.35, -mvPosition.z * 0.18)));
  gl_Position = projectionMatrix * mvPosition;
}
`;

export const STARFIELD_FRAGMENT_SHADER = `
varying vec3 vColor;

void main() {
  vec2 coord = gl_PointCoord - vec2(0.5);
  float dist = length(coord);
  float alpha = smoothstep(0.5, 0.08, dist);
  gl_FragColor = vec4(vColor, alpha * 0.88);
}
`;
