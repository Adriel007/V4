import * as THREE from "three";

const container = document.getElementById("canvas-container");

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x050505, 0.02);

const camera = new THREE.PerspectiveCamera(
  50,
  container.clientWidth / container.clientHeight,
  0.1,
  100
);
camera.position.z = 8;

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  alpha: true,
});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ReinhardToneMapping;
container.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0x404040, 2);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0xffffff, 1, 100);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

// Rim light
const rimLight = new THREE.SpotLight(0x00ff41, 5);
rimLight.position.set(-5, 5, -5);
rimLight.lookAt(0, 0, 0);
scene.add(rimLight);

// Creature
const creatureGroup = new THREE.Group();
scene.add(creatureGroup);

// Body
const bodyGeo = new THREE.SphereGeometry(1.5, 64, 64);
const bodyMat = new THREE.MeshStandardMaterial({
  color: 0x000000,
  roughness: 1.0,
  metalness: 0.0,
});
const body = new THREE.Mesh(bodyGeo, bodyMat);
creatureGroup.add(body);

// Materials
const pureWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
const greenNeonMat = new THREE.MeshBasicMaterial({
  color: 0x00ff41,
  side: THREE.DoubleSide,
});

// Eyes
function createEye(x) {
  const eyeGroup = new THREE.Group();
  eyeGroup.position.set(x, 0.35, 1.45);

  // Angle adjustment
  eyeGroup.rotation.y = x * 0.2;
  eyeGroup.rotation.x = -0.1;

  // Pupil
  const pupil = new THREE.Mesh(
    new THREE.CircleGeometry(0.18, 32),
    pureWhiteMat
  );
  pupil.position.z = 0.02;
  eyeGroup.add(pupil);

  // Outer ring
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.23, 0.33, 32),
    pureWhiteMat
  );
  ring.position.z = 0.01;
  eyeGroup.add(ring);

  // Eye light
  const eyeLight = new THREE.PointLight(0x00ff41, 3, 5, 2);
  eyeLight.position.set(0, 0, 0.2);
  eyeGroup.add(eyeLight);

  return eyeGroup;
}

const leftEye = createEye(-0.6);
const rightEye = createEye(0.6);
creatureGroup.add(leftEye);
creatureGroup.add(rightEye);

// Mouth
const lips = {
  upper: {
    geo: null,
    mesh: null,
  },
  lower: {
    geo: null,
    mesh: null,
  },
};

lips.upper.geo = new THREE.TorusGeometry(0.6, 0.03, 16, 64, Math.PI * 0.5);
lips.upper.mesh = new THREE.Mesh(lips.upper.geo, pureWhiteMat);
lips.lower.geo = new THREE.TorusGeometry(0.6, 0.03, 16, 64, Math.PI * 0.5);
lips.lower.mesh = new THREE.Mesh(lips.lower.geo, pureWhiteMat);

// Position
lips.upper.mesh.position.set(0, -0.35, 1.55);
lips.lower.mesh.position.set(0, -0.35, 1.55);

// Rotation
lips.upper.mesh.rotation.set(0.3, 0, Math.PI * 3.25);
lips.lower.mesh.rotation.set(0.3, 0, Math.PI * 3.25);

// Mouth lighting
const mouthLight = new THREE.PointLight(0x00ff41, 3, 5, 2);

mouthLight.position.set(0.5, 0.5, 0.2);

lips.upper.mesh.add(mouthLight);
creatureGroup.add(lips.upper.mesh);
creatureGroup.add(lips.lower.mesh);

// Animation and interaction setup
const clock = new THREE.Clock();
let isPaused = false;

const targetPos = new THREE.Vector3(0, 0, 0);
const velocity = new THREE.Vector3(0, 0, 0);
let spinVelocity = 0;

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2(-100, -100);
const mouseWorldPos = new THREE.Vector3();
let isHovering = false;

// Camera controls state (WASD movement + mouse look)
let cameraControlsEnabled = false;
let camYaw = 0; // rotation around Y
let camPitch = 0; // rotation around X
const camSpeed = 4.0; // units per second
const camSensitivity = 0.0025; // mouse sensitivity
const camKeys = { w: false, a: false, s: false, d: false };
let _camLastMouse = { x: 0, y: 0, initialized: false };

function enableCameraControls() {
  if (cameraControlsEnabled) return;
  cameraControlsEnabled = true;

  // Initialize yaw/pitch from current camera direction
  const dir = new THREE.Vector3();
  camera.getWorldDirection(dir);
  camYaw = Math.atan2(dir.x, -dir.z);
  camPitch = Math.asin(THREE.MathUtils.clamp(dir.y, -0.999, 0.999));

  window.addEventListener("mousemove", (e) => {
    // Use relative movement based on last mouse position
    if (!_camLastMouse.initialized) {
      _camLastMouse.x = e.clientX;
      _camLastMouse.y = e.clientY;
      _camLastMouse.initialized = true;
      return;
    }
    const dx = e.clientX - _camLastMouse.x;
    const dy = e.clientY - _camLastMouse.y;
    _camLastMouse.x = e.clientX;
    _camLastMouse.y = e.clientY;

    camYaw -= dx * camSensitivity;
    camPitch -= dy * camSensitivity;
    const limit = Math.PI / 2 - 0.05;
    camPitch = Math.max(-limit, Math.min(limit, camPitch));
  });

  window.addEventListener("keydown", (e) => {
    const k = e.key.toLowerCase();
    if (k in camKeys) camKeys[k] = true;
  });
  window.addEventListener("keyup", (e) => {
    const k = e.key.toLowerCase();
    if (k in camKeys) camKeys[k] = false;
  });
}

let blinkTimer = 0;
let nextBlinkTime = Math.random() * 3 + 2;
let isBlinking = false;
let blinkDuration = 0.15;

const MAX_PUPIL_OFFSET = 0.08;

// Events
window.addEventListener("mousemove", (event) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  isHovering = true;

  // Reset pupils to center after 2s without movement
  clearTimeout(window.resetPupilTimeout);
  window.resetPupilTimeout = setTimeout(() => {
    isHovering = false;
  }, 2_000);
});

function onMouseClick() {
  // Jump impulse
  const JUMP_IMPULSE = 0.2;
  const MAX_UP_VEL = 0.5;
  velocity.y = Math.min(velocity.y + JUMP_IMPULSE, MAX_UP_VEL);

  // Small cursor ripple effect at click position
  const rect = container.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  const ripple = document.createElement("div");
  ripple.className = "click-ripple";
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
  container.appendChild(ripple);

  // Remove ripple after animation
  ripple.addEventListener("animationend", () => {
    ripple.remove();
  });

  // No spin on click
  spinVelocity = 0;
  // Trigger blink
  triggerBlink();
}

function triggerBlink() {
  isBlinking = true;
  blinkTimer = 0;
}

window.addEventListener("click", onMouseClick);

// Wander timer
let wanderTimer = 0;

// Update eyes
function updateEye(eyeGroup, targetWorldPos) {
  const pupil = eyeGroup.children[0];
  if (!pupil) return;
  // Convert target world position to eye local space
  const localTarget = targetWorldPos.clone();
  eyeGroup.worldToLocal(localTarget);
  // Desired local X/Y
  const targetX = localTarget.x;
  const targetY = localTarget.y;
  // Clamp movement radius
  const distance = Math.sqrt(targetX * targetX + targetY * targetY);
  const maxDist = MAX_PUPIL_OFFSET;

  let finalX = targetX;
  let finalY = targetY;

  if (distance > maxDist) {
    const ratio = maxDist / distance;
    finalX *= ratio;
    finalY *= ratio;
  }

  // Smooth interpolation
  pupil.position.x += (finalX - pupil.position.x) * 0.2;
  pupil.position.y += (finalY - pupil.position.y) * 0.2;
}

// Render loop

function animate() {
  requestAnimationFrame(animate);
  // Cap delta to avoid jumps on tab switches
  const delta = Math.min(clock.getDelta(), 0.05);
  if (isPaused) {
    renderer.render(scene, camera);
    return;
  }
  const time = clock.getElapsedTime();

  // Raycaster
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObject(body);
  document.body.style.cursor = "default";
  container.style.cursor = isHovering ? "pointer" : "crosshair";

  // Project mouse to 3D plane in front of creature
  const vec = new THREE.Vector3(mouse.x, mouse.y, 0.5);
  vec.unproject(camera);
  vec.sub(camera.position).normalize();
  const distance = -camera.position.z / vec.z;
  mouseWorldPos.copy(camera.position).add(vec.multiplyScalar(distance));

  // Eyes follow mouse
  if (isHovering) {
    updateEye(leftEye, mouseWorldPos);
    updateEye(rightEye, mouseWorldPos);
    // Subtle head rotation
    const targetRotationX = -mouse.y * 0.2;
    const targetRotationY = mouse.x * 0.2;
    creatureGroup.rotation.x +=
      (targetRotationX - creatureGroup.rotation.x) * 5 * delta;
    creatureGroup.rotation.y +=
      (targetRotationY - creatureGroup.rotation.y) * 5 * delta;
    // Slight mouth open
    lips.upper.mesh.scale.setScalar(
      THREE.MathUtils.lerp(lips.upper.mesh.scale.x, 1.2, 5 * delta)
    );
    lips.lower.mesh.scale.setScalar(
      THREE.MathUtils.lerp(lips.lower.mesh.scale.x, 1.2, 5 * delta)
    );
  } else {
    // Return pupils to center
    const pupilL = leftEye.children[0];
    const pupilR = rightEye.children[0];
    pupilL.position.x += (0 - pupilL.position.x) * 0.1;
    pupilL.position.y += (0 - pupilL.position.y) * 0.1;
    pupilR.position.x += (0 - pupilR.position.x) * 0.1;
    pupilR.position.y += (0 - pupilR.position.y) * 0.1;
    // Ease head rotation and mouth to neutral
    creatureGroup.rotation.x *= 0.95;
    creatureGroup.rotation.y *= 0.95;
    creatureGroup.rotation.z *= 0.95;
    lips.upper.mesh.scale.setScalar(
      THREE.MathUtils.lerp(lips.upper.mesh.scale.x, 1.0, 5 * delta)
    );
    lips.lower.mesh.scale.setScalar(
      THREE.MathUtils.lerp(lips.lower.mesh.scale.x, 1.0, 5 * delta)
    );
  }

  // Wander & physics movement
  wanderTimer += delta;
  if (!isHovering && wanderTimer > 4.0) {
    wanderTimer = 0;
    targetPos.set(
      (Math.random() - 0.5) * 3,
      (Math.random() - 0.5) * 1.5,
      (Math.random() - 0.5) * 1
    );
  }

  // Interpolate creature position
  if (!isHovering) {
    creatureGroup.position.x +=
      (targetPos.x - creatureGroup.position.x) * 2.0 * delta;
    creatureGroup.position.y +=
      (targetPos.y - creatureGroup.position.y) * 2.0 * delta;
    creatureGroup.position.z +=
      (targetPos.z - creatureGroup.position.z) * 2.0 * delta;
  }

  // Gravity & spring physics on Y
  velocity.y -= 0.5 * delta;
  const baseHeight = isHovering ? 0 : targetPos.y;
  const springForce = (baseHeight - creatureGroup.position.y) * 3.0;
  velocity.y += springForce * delta;
  velocity.y *= 0.96;
  creatureGroup.position.y += velocity.y;

  // Blink & breath

  // Breath scale
  const breath = 1 + Math.sin(time * 3) * 0.02;

  // Squash & stretch based on Y velocity
  const stretch = 1 + velocity.y * 0.4;
  const inverseStretch = 1 / stretch;

  let currentScaleY = stretch * breath;
  let currentScaleXZ = inverseStretch * breath;

  // Blinking
  blinkTimer += delta;
  if (blinkTimer > nextBlinkTime && !isBlinking) {
    triggerBlink();
  }

  if (isBlinking) {
    const blinkPhase = blinkTimer / blinkDuration;
    if (blinkPhase < 1.0) {
      // Close then reopen
      leftEye.scale.y = Math.max(0.1, Math.abs(Math.cos(blinkPhase * Math.PI)));
      rightEye.scale.y = Math.max(
        0.1,
        Math.abs(Math.cos(blinkPhase * Math.PI))
      );
    } else {
      // End blink
      isBlinking = false;
      leftEye.scale.y = 1;
      rightEye.scale.y = 1;
      nextBlinkTime = Math.random() * 3 + 2;
      blinkTimer = 0;
    }
  }

  // Spin on click
  if (spinVelocity > 0.001) {
    creatureGroup.rotation.y += spinVelocity;
    spinVelocity *= 0.92;
  }

  // --- Camera controls update (WASD movement + mouse look) ---
  if (cameraControlsEnabled) {
    const moveVec = new THREE.Vector3();

    // Forward/back (W/S)
    const forward = new THREE.Vector3(Math.sin(camYaw), 0, -Math.cos(camYaw));
    if (camKeys.w) moveVec.add(forward);
    if (camKeys.s) moveVec.sub(forward);

    // Right/left (D/A)
    const right = new THREE.Vector3(Math.cos(camYaw), 0, Math.sin(camYaw));
    if (camKeys.d) moveVec.add(right);
    if (camKeys.a) moveVec.sub(right);

    if (moveVec.lengthSq() > 0.000001) {
      moveVec.normalize().multiplyScalar(camSpeed * delta);
      camera.position.add(moveVec);
    }

    // Update camera look direction from yaw/pitch
    const lx = Math.sin(camYaw) * Math.cos(camPitch);
    const ly = Math.sin(camPitch);
    const lz = -Math.cos(camYaw) * Math.cos(camPitch);
    const lookDir = new THREE.Vector3(lx, ly, lz);
    camera.lookAt(camera.position.clone().add(lookDir));
  }

  // Apply combined scales with smoothing
  creatureGroup.scale.x = THREE.MathUtils.lerp(
    creatureGroup.scale.x,
    currentScaleXZ,
    15 * delta
  );
  creatureGroup.scale.y = THREE.MathUtils.lerp(
    creatureGroup.scale.y,
    currentScaleY,
    15 * delta
  );
  creatureGroup.scale.z = THREE.MathUtils.lerp(
    creatureGroup.scale.z,
    currentScaleXZ,
    15 * delta
  );

  renderer.render(scene, camera);
}
// Pause physics when tab is hidden
document.addEventListener("visibilitychange", () => {
  isPaused = document.hidden;
  // Reset clock
  clock.getDelta();
});
// Resize
window.addEventListener("resize", () => {
  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
});

animate();
// Enable camera controls (WASD + mouse). Comment this line to disable.
//enableCameraControls();
