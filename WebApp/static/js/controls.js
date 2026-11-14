const $ = (selector) => document.querySelector(selector);
const state = {wheelSpeed: 40, armSpeed: 30, wheelDirection: 'stop', armDirection: 'stop', claw: 'open'};
const heldDirections = new Map();
let pendingCommand = null;
let sending = false;
let backendOnline = true;
let toastTimer;

function toast(message) {
  $('#toast').textContent = message;
  $('#toast').classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').classList.remove('visible'), 3500);
}

function payload() {
  return {
    wheel: {speed: state.wheelSpeed, direction: state.wheelDirection},
    arm: {speed: state.armSpeed, direction: state.armDirection, claw: state.claw}
  };
}

// These commands go to the Flask simulator. Hardware mappings belong in Python.
async function transmit() {
  pendingCommand = payload();
  if (sending) return;
  sending = true;
  while (pendingCommand) {
    const command = pendingCommand;
    pendingCommand = null;
    try {
      const response = await fetch('/api/command', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(command), signal: AbortSignal.timeout(2000)
      });
      if (!response.ok) throw new Error('Command rejected');
      backendOnline = true;
    } catch (_) {
      pendingCommand = null;
      heldDirections.clear();
      state.wheelDirection = 'stop';
      state.armDirection = 'stop';
      if (backendOnline) toast('Cannot reach Flask. Check that app.py is running.');
      backendOnline = false;
      render();
    }
  }
  sending = false;
}

function render() {
  for (const part of ['wheel', 'arm']) {
    const speed = state[part + 'Speed'];
    $('#' + part + '-speed').value = speed;
    $('#' + part + '-speed').style.setProperty('--fill', speed + '%');
    $('#' + part + '-value').textContent = speed + '%';
  }
  $('#claw-label').textContent = state.claw === 'open' ? 'Open' : 'Closed';
  $('#claw-button').setAttribute('aria-label', state.claw === 'open' ? 'Close gripper' : 'Open gripper');
  document.querySelectorAll('.direction-button').forEach(button => {
    button.classList.toggle('active', state[button.dataset.part + 'Direction'] === button.dataset.direction);
  });
}

function refreshDirections() {
  for (const part of ['wheel', 'arm']) {
    const held = [...heldDirections.values()].filter(value => value.part === part);
    state[part + 'Direction'] = held.length && state[part + 'Speed'] > 0 ? held[held.length - 1].direction : 'stop';
  }
  render();
  transmit();
}

function changeSpeed(part, value) {
  const speed = Math.max(0, Math.min(100, Math.round(Number(value) / 5) * 5));
  if (state[part + 'Speed'] === speed) return;
  state[part + 'Speed'] = speed;
  refreshDirections();
}

function releaseAll() {
  if (!heldDirections.size && state.wheelDirection === 'stop' && state.armDirection === 'stop') return;
  heldDirections.clear();
  refreshDirections();
}

function toggleClaw() {
  state.claw = state.claw === 'open' ? 'closed' : 'open';
  render();
  transmit();
}

const directionKeys = {ArrowLeft: ['wheel', 'left'], ArrowRight: ['wheel', 'right'], KeyA: ['arm', 'left'], KeyD: ['arm', 'right']};
const speedKeys = {KeyW: ['wheel', 5], KeyS: ['wheel', -5], KeyR: ['arm', 5], KeyF: ['arm', -5]};
window.addEventListener('keydown', event => {
  if (event.ctrlKey || event.altKey || event.metaKey) return;
  if (directionKeys[event.code]) {
    event.preventDefault();
    if (event.repeat) return;
    const [part, direction] = directionKeys[event.code];
    heldDirections.set(event.code, {part, direction});
    refreshDirections();
  } else if (speedKeys[event.code]) {
    event.preventDefault();
    const [part, delta] = speedKeys[event.code];
    changeSpeed(part, state[part + 'Speed'] + delta);
  } else if (event.code === 'Space') {
    event.preventDefault();
    if (!event.repeat) toggleClaw();
  }
});
window.addEventListener('keyup', event => {
  if (!heldDirections.has(event.code)) return;
  event.preventDefault();
  heldDirections.delete(event.code);
  refreshDirections();
});
window.addEventListener('blur', releaseAll);
document.addEventListener('visibilitychange', () => { if (document.hidden) releaseAll(); });

document.querySelectorAll('.direction-button').forEach(button => {
  button.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    heldDirections.set('pointer-' + event.pointerId, {part: button.dataset.part, direction: button.dataset.direction});
    refreshDirections();
  });
  const release = event => {
    if (heldDirections.delete('pointer-' + event.pointerId)) refreshDirections();
  };
  button.addEventListener('pointerup', release);
  button.addEventListener('pointercancel', release);
  button.addEventListener('lostpointercapture', release);
});
for (const part of ['arm', 'wheel']) {
  $('#' + part + '-speed').addEventListener('input', event => changeSpeed(part, event.target.value));
}
$('#claw-button').addEventListener('click', toggleClaw);
setInterval(() => { if (backendOnline && !document.hidden) transmit(); }, 250);
window.addEventListener('pagehide', () => {
  state.wheelDirection = 'stop';
  state.armDirection = 'stop';
  fetch('/api/command', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload()), keepalive: true
  }).catch(() => {});
});

// Flask supplies this URL from ESP32_IP. No camera setup dialog is needed.
const camera = $('#camera-image');
const streamUrl = camera.dataset.streamUrl;
let cameraRetry;
function connectCamera() {
  clearTimeout(cameraRetry);
  $('#camera-status').textContent = 'Connecting to camera…';
  // A fresh URL lets a failed request retry without reusing a cached error.
  camera.src = streamUrl + (streamUrl.includes('?') ? '&' : '?') + 't=' + Date.now();
}
camera.addEventListener('load', () => {
  clearTimeout(cameraRetry);
  camera.style.visibility = 'visible';
  $('#camera-message').hidden = true;
  $('#camera-status').textContent = 'Camera connected';
});
camera.addEventListener('error', () => {
  camera.style.visibility = 'hidden';
  $('#camera-message').hidden = false;
  $('#camera-status').textContent = 'Reconnecting automatically…';
  clearTimeout(cameraRetry);
  cameraRetry = setTimeout(connectCamera, 5000);
});
render();
connectCamera();
