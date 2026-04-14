/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        osrs: {
          gold: '#FFA500',
          green: '#00FF00',
          red: '#FF0000',
          blue: '#0099FF',
        }
      }
    },
  },
  plugins: [],
}
