(() => {
  "use strict";

  const contract = Object.freeze({
    schema: "PFIV025Stage8Phase82HapticsContractV1",
    targetVersion: "v0.2.5",
    stage: "Stage 8",
    phase: "8.2",
    defaultPreferences: Object.freeze({ haptic: false, sound: false, intensity: "light" }),
    capabilitySources: Object.freeze(["navigator.vibrate", "AudioContext"]),
    userActivationRequired: true,
    unsupportedDelivery: "visual_only",
  });
  const preferences = { haptic: false, sound: false, intensity: "light" };
  let audioContext = null;

  function capability() {
    return Object.freeze({
      haptic: typeof navigator.vibrate === "function",
      sound: typeof (window.AudioContext || window.webkitAudioContext) === "function",
    });
  }

  function hasUserActivation() {
    return navigator.userActivation?.isActive === true;
  }

  function configure(next = {}) {
    preferences.haptic = next.haptic === true;
    preferences.sound = next.sound === true;
    preferences.intensity = next.intensity === "standard" ? "standard" : "light";
    const detected = capability();
    if (document.body) {
      document.body.dataset.v025HapticPreference = preferences.haptic ? "enabled" : "disabled";
      document.body.dataset.v025SoundPreference = preferences.sound ? "enabled" : "disabled";
      document.body.dataset.v025HapticCapability = detected.haptic ? "supported" : "unsupported";
      document.body.dataset.v025SoundCapability = detected.sound ? "supported" : "unsupported";
    }
    return Object.freeze({ ...preferences, capability: detected });
  }

  function vibrationPattern(kind) {
    const light = { select: [6], soft: [6], confirm: [10], warning: [14, 24, 14], error: [18, 28, 18] };
    const standard = { select: [10], soft: [8], confirm: [14], warning: [18, 28, 18], error: [22, 32, 22] };
    const source = preferences.intensity === "standard" ? standard : light;
    return source[kind] || source.select;
  }

  function playTone(kind) {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!preferences.sound || !AudioContextCtor || !hasUserActivation()) return false;
    try {
      audioContext = audioContext || new AudioContextCtor();
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(kind === "error" ? 190 : kind === "warning" ? 250 : 380, audioContext.currentTime);
      gain.gain.setValueAtTime(0.001, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.025, audioContext.currentTime + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.08);
      oscillator.connect(gain).connect(audioContext.destination);
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.09);
      return true;
    } catch (_error) {
      return false;
    }
  }

  function emit(kind = "select") {
    const detected = capability();
    const userActivation = hasUserActivation();
    let hapticDelivered = false;
    if (preferences.haptic && detected.haptic && userActivation) {
      try {
        hapticDelivered = navigator.vibrate(vibrationPattern(kind)) === true;
      } catch (_error) {
        hapticDelivered = false;
      }
    }
    const soundDelivered = playTone(kind);
    const delivery = hapticDelivered || soundDelivered ? "multimodal" : "visual_only";
    if (document.body) {
      document.body.dataset.v025HapticStatus = delivery;
      const feedbackRequested = preferences.haptic || preferences.sound;
      document.body.dataset.v025HapticDegraded = delivery !== "visual_only" || !feedbackRequested
        ? "none"
        : !userActivation
          ? "activation_required_silent"
          : (!detected.haptic || !detected.sound) ? "unsupported_silent" : "none";
    }
    return Object.freeze({ delivery, hapticDelivered, soundDelivered, userActivation, capability: detected });
  }

  function initialize() {
    const hapticToggle = document.querySelector('[data-feedback-toggle="haptic"]');
    const soundToggle = document.querySelector('[data-feedback-toggle="sound"]');
    configure({
      haptic: hapticToggle ? Boolean(hapticToggle.checked) : false,
      sound: soundToggle ? Boolean(soundToggle.checked) : false,
    });
    hapticToggle?.addEventListener("change", () => configure({ haptic: Boolean(hapticToggle.checked), sound: preferences.sound }));
    soundToggle?.addEventListener("change", () => configure({ haptic: preferences.haptic, sound: Boolean(soundToggle.checked) }));
  }

  window.PFI_V025_STAGE8_HAPTICS = Object.freeze({ contract, capability, configure, emit });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
