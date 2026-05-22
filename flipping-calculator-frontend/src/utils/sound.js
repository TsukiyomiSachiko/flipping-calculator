// Synthesize a premium luxury warning chime sound using the HTML5 Web Audio API
export const playAlertSound = () => {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    
    const now = ctx.currentTime;
    
    // Play a sequence of tones representing a luxurious warning alert
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
  } catch (e) {
    console.error('Failed to play alert sound:', e);
  }
};
