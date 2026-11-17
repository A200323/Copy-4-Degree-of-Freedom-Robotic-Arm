// Load after the inline controls in templates/index2.html.
// Uses the existing arm, elbow and lr range inputs and Flask /gamepad-action route.
(() => {
  "use strict";

  const shortcuts = {
    KeyU: ["arm", 1], KeyJ: ["arm", -1],
    KeyI: ["elbow", 1], KeyK: ["elbow", -1],
    KeyN: ["lr", -1], KeyM: ["lr", 1]
  };
  const axes = new Map();
  const heldKeys = new Map();
  const tickMs = 50;

  for (const name of ["arm", "elbow", "lr"]) {
    const slider = document.getElementById(name);
    if (!slider || slider.type !== "range") continue;

    const center = (Number(slider.min) + Number(slider.max)) / 2;
    slider.value = center;
    const axis = {
      name, slider, center, holds: new Map(), timer: null,
      pointer: null, sending: false, pending: null, neutralPending: false
    };
    axes.set(name, axis);
    slider.style.touchAction = "none";

    // Handle a pointer as a held direction. Drag across the center to reverse.
    function pointerDirection(event) {
      const rect = slider.getBoundingClientRect();
      const distance = name === "lr"
        ? (event.clientX - rect.left) / rect.width - 0.5
        : 0.5 - (event.clientY - rect.top) / rect.height;
      return Math.abs(distance) < 0.025 ? 0 : Math.sign(distance);
    }
    slider.addEventListener("pointerdown", event => {
      if (event.button !== 0 || axis.pointer !== null) return;
      event.preventDefault();
      slider.focus();
      axis.pointer = event.pointerId;
      slider.setPointerCapture(event.pointerId);
      hold(axis, "pointer", pointerDirection(event));
    });
    slider.addEventListener("pointermove", event => {
      if (axis.pointer === event.pointerId) hold(axis, "pointer", pointerDirection(event));
    });
    function releasePointer(event) {
      if (axis.pointer !== event.pointerId) return;
      axis.pointer = null;
      release(axis, "pointer");
    }
    for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) {
      slider.addEventListener(event, releasePointer);
    }
  }

  // Keep the latest pending position per joint. Always send a queued release
  // before a new press so an old movement cannot arrive after its release.
  async function publish(axis, value) {
    axis.pending = value;
    if (value === axis.center) axis.neutralPending = true;
    if (axis.sending) return;
    axis.sending = true;
    try {
      while (axis.pending !== null) {
        const next = axis.neutralPending ? axis.center : axis.pending;
        axis.neutralPending = false;
        if (axis.pending === next) axis.pending = null;
        try {
          const response = await fetch("/gamepad-action", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({action: axis.name, value: next}),
            signal: AbortSignal.timeout(2000)
          });
          if (!response.ok) throw new Error("Flask rejected the slider command");
        } catch {
          const notice = document.getElementById("notice");
          if (notice) notice.textContent = "Slider command could not reach Flask.";
        }
      }
    } finally {
      axis.sending = false;
    }
  }

  function setValue(axis, value) {
    const previous = axis.slider.value;
    axis.slider.value = value; // Native range clamps the value to min and max.
    if (axis.slider.value !== previous) publish(axis, Number(axis.slider.value));
  }

  function advance(axis) {
    const direction = Array.from(axis.holds.values()).pop();
    if (!direction) {
      setValue(axis, axis.center);
      return;
    }
    const step = Number(axis.slider.step) || 1;
    setValue(axis, Number(axis.slider.value) + direction * step);
  }

  function hold(axis, source, direction) {
    if (axis.holds.get(source) === direction) return;
    axis.holds.delete(source);
    axis.holds.set(source, direction);
    advance(axis);
    if (axis.timer === null) axis.timer = setInterval(() => advance(axis), tickMs);
  }

  function release(axis, source) {
    if (!axis.holds.delete(source) || axis.holds.size) return;
    clearInterval(axis.timer);
    axis.timer = null;
    setValue(axis, axis.center);
  }

  // Capture these shortcuts before the template's old one-step key handler.
  window.addEventListener("keydown", event => {
    if (event.ctrlKey || event.metaKey || event.altKey || event.isComposing) return;
    if (event.target.isContentEditable || event.target.closest?.("textarea, select, input:not([type=range])")) return;
    let binding = shortcuts[event.code];
    // A focused slider can also be operated with its native arrow keys.
    if (!binding && axes.has(event.target.id)) {
      const direction = {ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1}[event.code];
      if (direction) binding = [event.target.id, direction];
    }
    if (!binding) return;
    const axis = axes.get(binding[0]);
    if (!axis) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.repeat || heldKeys.has(event.code)) return;
    heldKeys.set(event.code, axis);
    if (axis.name !== "lr") {
      document.querySelectorAll("[data-joint]").forEach(button => {
        button.setAttribute("aria-pressed", String(button.dataset.joint === axis.name));
      });
    }
    hold(axis, event.code, binding[1]);
  }, true);

  window.addEventListener("keyup", event => {
    const axis = heldKeys.get(event.code);
    if (!axis) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    heldKeys.delete(event.code);
    release(axis, event.code);
  }, true);

  function releaseAll() {
    heldKeys.clear();
    for (const axis of axes.values()) {
      clearInterval(axis.timer);
      axis.timer = null;
      axis.holds.clear();
      axis.pointer = null;
      setValue(axis, axis.center);
    }
  }
  window.addEventListener("blur", releaseAll);
  window.addEventListener("pagehide", releaseAll);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) releaseAll();
  });
})();
