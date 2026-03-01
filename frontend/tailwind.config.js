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
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'bounce-slow': 'bounce 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(5px) translateX(-50%)', left: '50%' },
          '100%': { opacity: '1', transform: 'translateY(0) translateX(-50%)', left: '50%' },
        }
      }
    },
  },
  plugins: [],
}
