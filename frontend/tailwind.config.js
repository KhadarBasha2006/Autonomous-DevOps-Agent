/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#172033',
          900: '#0f172a',
        }
      }
    },
  },
  plugins: [],
}