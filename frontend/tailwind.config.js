/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#050505',
        neonBlue: '#00f3ff',
        neonPurple: '#bc13fe',
        matrixGreen: '#00ff41',
      },
      fontFamily: {
        mono: ['"Fira Code"', '"JetBrains Mono"', 'monospace'],
        display: ['"Outfit"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
