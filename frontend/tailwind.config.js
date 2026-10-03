/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#009bff',
          orange: '#ff882b',
          dark: '#090604',
          sidebar: '#0d0b09',
          border: '#292521',
          surface: '#1c1a18',
        },
        rag: {
          web: '#8b5cf6',
          vectorstore: '#3b82f6',
          native: '#10b981',
          error: '#ef4444',
        }
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(to right, #009bff, #ff882b)',
        'composer-gradient': 'linear-gradient(to right, #a6d5ff, #ffc49d)',
        'chat-light': 'linear-gradient(to right, #e6f5ff, #fff0e5)',
        'chat-dark': 'linear-gradient(to right, #141210, #1a1714)',
        'history-light': 'linear-gradient(to right, #fff3e9, #ffffff)',
        'history-dark': 'linear-gradient(to right, #161311, #0f0d0c)',
      }
    },
  },
  plugins: [],
}
