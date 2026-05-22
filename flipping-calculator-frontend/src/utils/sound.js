// Synthesize a premium luxury warning chime sound using the HTML5 Web Audio API
let sharedCtx = null;
let pendingAlertSound = false;

const getAudioContext = () => {
  if (typeof window === 'undefined') return null;
  if (!sharedCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      sharedCtx = new AudioContextClass();
    }
  }
  return sharedCtx;
};

// Play a sequence of tones representing a luxurious warning alert on a given context
const synthesizeChime = (ctx) => {
  const now = ctx.currentTime;
  
  const playTone = (freq, start, duration, volume) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sine'; // Soft, clean tone
    osc.frequency.setValueAtTime(freq, start);
    
    gain.gain.setValueAtTime(volume, start);
    gain.gain.exponentialRampToValueAtTime(0.001, start + duration);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start(start);
    osc.stop(start + duration);
  };
  
  // Elegant warning chime: G5 followed by C6 with subtle overlap
  playTone(783.99, now, 0.35, 0.12);       // G5
  playTone(1046.50, now + 0.15, 0.55, 0.12); // C6
};

const events = ['click', 'keydown', 'mousedown', 'touchstart'];

const cleanupListeners = () => {
  events.forEach((event) => {
    window.removeEventListener(event, unlockAudioContext);
  });
};

const registerListeners = () => {
  if (typeof window !== 'undefined') {
    events.forEach((event) => {
      window.addEventListener(event, unlockAudioContext, { passive: true });
    });
  }
};

// Global event listener to unlock the AudioContext and play any pending alert on user gesture
const unlockAudioContext = () => {
  const ctx = getAudioContext();
  if (!ctx) return;

  if (ctx.state === 'suspended') {
    ctx.resume().then(() => {
      if (pendingAlertSound) {
        pendingAlertSound = false;
        synthesizeChime(ctx);
      }
      cleanupListeners();
    }).catch(() => {});
  } else {
    if (pendingAlertSound) {
      pendingAlertSound = false;
      synthesizeChime(ctx);
    }
    cleanupListeners();
  }
};

// Main function to trigger the warning sound
export const playAlertSound = () => {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    if (ctx.state === 'suspended') {
      // AudioContext is blocked by browser autoplay policy.
      // Mark as pending so we play it as soon as the user interacts with the page.
      pendingAlertSound = true;
      
      // Re-register gesture listeners in case they were cleaned up or not registered
      registerListeners();
      
      // Try to resume immediately in case we are currently in an event handler context
      ctx.resume().then(() => {
        if (pendingAlertSound) {
          pendingAlertSound = false;
          synthesizeChime(ctx);
        }
      }).catch((err) => {
        console.warn('AudioContext resume failed:', err);
      });
      return;
    }

    synthesizeChime(ctx);
  } catch (e) {
    console.error('Failed to play alert sound:', e);
  }
};

// Add listeners to unlock the audio context on initial user gestures
registerListeners();
