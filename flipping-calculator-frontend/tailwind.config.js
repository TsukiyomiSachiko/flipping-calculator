import tsukiThemePreset from 'tsuki-theme/tailwind-preset.js';

/** @type {import('tailwindcss').Config} */
export default {
  presets: [tsukiThemePreset],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        luxury: {
          dark: '#080512',      // Extremely dark velvet purple-black
          darker: '#04020a',    // Pure obsidian
          card: 'rgba(20, 15, 38, 0.65)', // Elegant semi-transparent glass
          gold: '#d4af37',      // OSRS/Roman gold
          goldBright: '#f3e5ab', // Radiant gold
          goldDark: '#aa7c11',   // Deep bronze gold
          purple: '#8b5cf6',    // Amethyst purple
          purpleDark: '#4c1d95',// Deep violet
          purpleLight: '#c084fc',// Soft lavender
          border: 'rgba(139, 92, 246, 0.12)', // Subtle purple glow border
          goldBorder: 'rgba(212, 175, 55, 0.12)', // Subtle gold border
        },
        osrs: {
          gold: '#d4af37',
          green: '#10b981', // Emerald green
          red: '#f43f5e',   // Ruby red
          blue: '#3b82f6',  // Sapphire blue
        }
      },
      fontFamily: {
        cinzel: ['Cinzel', 'serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      boxShadow: {
        'luxury-shadow': '0 10px 30px -10px rgba(0,0,0,0.7)',
        'purple-glow': '0 0 15px rgba(139, 92, 246, 0.12)',
        'gold-glow': '0 0 20px rgba(212, 175, 55, 0.18)',
        'card-hover': '0 12px 24px -10px rgba(139, 92, 246, 0.2), 0 0 15px rgba(212, 175, 55, 0.05)',
      },
      backgroundImage: {
        'luxury-radial': 'radial-gradient(circle at 50% 50%, #150f2b 0%, #080512 100%)',
        'card-gradient': 'linear-gradient(135deg, rgba(24, 18, 48, 0.7) 0%, rgba(13, 9, 25, 0.85) 100%)',
        'gold-gradient': 'linear-gradient(135deg, #f3e5ab 0%, #d4af37 50%, #aa7c11 100%)',
        'purple-gradient': 'linear-gradient(135deg, #c084fc 0%, #8b5cf6 50%, #5b21b6 100%)',
        'dark-gradient': 'linear-gradient(180deg, #0b0717 0%, #05030b 100%)',
      },
      animation: {
        'pulse-subtle': 'pulseSubtle 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float-slow': 'floatSlow 8s ease-in-out infinite',
        'float-delayed': 'floatSlow 8s ease-in-out infinite 4s',
      },
      keyframes: {
        pulseSubtle: {
          '0%, 100%': { opacity: '0.85' },
          '50%': { opacity: '1' },
        },
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0) scale(1)' },
          '50%': { transform: 'translateY(-15px) scale(1.03)' },
        }
      }
    },
  },
  plugins: [],
}

