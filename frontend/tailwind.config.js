/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"Inter"', 'ui-sans-serif', 'sans-serif'],
      },
      colors: {
        ink: {
          950: '#0b0f14',
          900: '#0f1620',
          800: '#151f2c',
          700: '#1d2b3a',
          600: '#2a3d51',
        },
        paper: {
          50: '#faf8f3',
          100: '#f2eee2',
          200: '#e6dfcc',
        },
        amber: {
          400: '#f2b134',
          500: '#e29b1f',
        },
        teal: {
          400: '#4fd1c5',
          500: '#2fb3a6',
        },
        coral: {
          400: '#ef6f6c',
        },
      },
    },
  },
  plugins: [],
}
