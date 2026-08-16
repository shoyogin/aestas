/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'night-bordeaux': '#461220',
        'burnt-rose': '#8c2f39',
        'dusty-mauve': '#b23a48',
        'powder-blush': '#fcb9b2',
        'peach-fuzz': '#fed0bb',
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'bloom-in': {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'bloom-in': 'bloom-in 1s ease-out forwards',
      },
    },
  },
  plugins: [],
}
