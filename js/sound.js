// ═══════════════════════════════════════
//  PAMBARAM - sound.js
//  Procedural audio synthesis (mirrors sound.py)
// ═══════════════════════════════════════

class SoundManager {
  constructor(enabled = true) {
    this.enabled = enabled;
    this._cache = {};
    this._ctx = null;
    this._init();
  }

  _init() {
    if (!this.enabled) return;
    try {
      this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (_) {
      this.enabled = false;
    }
  }

  _tone(freq, duration, volume = 0.3, wave = 'sine', decay = 2.0, freqEnd = null) {
    if (!this._ctx) return null;
    const ctx = this._ctx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = wave;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    if (freqEnd) {
      osc.frequency.exponentialRampToValueAtTime(freqEnd, ctx.currentTime + duration);
    }
    gain.gain.setValueAtTime(volume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + duration);
    return osc;
  }

  _make(name, segments) {
    if (!this._ctx) return;
    // Store a function to play the sound later (since we can't pre-render)
    this._cache[name] = () => {
      segments.forEach(seg => {
        // seg is {freq, duration, volume, wave, decay, freqEnd}
        const osc = this._tone(seg.freq, seg.duration, seg.volume || 0.3, seg.wave || 'sine', seg.decay || 2.0, seg.freqEnd);
      });
    };
  }

  _buildAll() {
    this._make('click', [
      {freq: 720, duration: 0.05, volume: 0.3, wave: 'square', decay: 10}
    ]);
    this._make('launch', [
      {freq: 180, duration: 0.22, volume: 0.4, wave: 'sine', decay: 4.0, freqEnd: 420}
    ]);
    this._make('dash', [
      {freq: 300, duration: 0.12, volume: 0.3, wave: 'square', decay: 8.0, freqEnd: 520}
    ]);
    this._make('collision', [
      {freq: 90, duration: 0.12, volume: 0.4, wave: 'sawtooth', decay: 9.0}
    ]);
    this._make('special', [
      {freq: 440, duration: 0.08, volume: 0.4, wave: 'sine', decay: 3.0, freqEnd: 660},
      {freq: 660, duration: 0.14, volume: 0.4, wave: 'sine', decay: 4.0, freqEnd: 880}
    ]);
    this._make('ringout', [
      {freq: 500, duration: 0.35, volume: 0.4, wave: 'sine', decay: 2.5, freqEnd: 90}
    ]);
    this._make('victory', [
      {freq: 523, duration: 0.12, volume: 0.3, wave: 'sine', decay: 3.0},
      {freq: 659, duration: 0.12, volume: 0.3, wave: 'sine', decay: 3.0},
      {freq: 784, duration: 0.25, volume: 0.4, wave: 'sine', decay: 2.5}
    ]);
  }

  play(name) {
    if (!this.enabled || !this._ctx) return;
    // Resume context if suspended
    if (this._ctx.state === 'suspended') {
      this._ctx.resume();
    }
    const sound = this._cache[name];
    if (sound) sound();
  }

  // Call this after user interaction to unlock audio
  resume() {
    if (this._ctx && this._ctx.state === 'suspended') {
      this._ctx.resume();
    }
  }
}

// Auto-build sounds on first play? We'll build on instantiation.
// We'll build on first play or on init.
// For simplicity, we build in the constructor after ctx creation.
// Modify _init to call _buildAll.
// We'll override _init to include build.
const origInit = SoundManager.prototype._init;
SoundManager.prototype._init = function() {
  if (!this.enabled) return;
  try {
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    this._buildAll();
  } catch (_) {
    this.enabled = false;
  }
};

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SoundManager;
}