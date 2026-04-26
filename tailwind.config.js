/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        space: {
          900: '#0a0a1a',
          800: '#12122a',
          700: '#1a1a3a',
          600: '#2a2a4a',
        },
        cosmic: {
          gold: '#f4c542',
          silver: '#c0c0e0',
          rose: '#e84a7f',
          purple: '#9b59b6',
          blue: '#3498db',
          teal: '#1abc9c',
        },
        element: {
          fire: '#e74c3c',
          earth: '#27ae60',
          air: '#3498db',
          water: '#9b59b6',
        },
      },
      fontFamily: {
        cinzel: ['Cinzel', 'serif'],
        quicksand: ['Quicksand', 'sans-serif'],
        cormorant: ['Cormorant Garamond', 'serif'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'twinkle': 'twinkle 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'spin-slow': 'spin 20s linear infinite',
        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
        'shooting-star': 'shootingStar 3s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 10px currentColor)' },
          '50%': { opacity: '0.8', filter: 'drop-shadow(0 0 20px currentColor)' },
        },
        twinkle: {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shootingStar: {
          '0%': { transform: 'translateX(0) translateY(0)', opacity: '1' },
          '70%': { opacity: '1' },
          '100%': { transform: 'translateX(300px) translateY(300px)', opacity: '0' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      boxShadow: {
        'glow-gold': '0 0 20px rgba(244, 197, 66, 0.3)',
        'glow-silver': '0 0 20px rgba(192, 192, 224, 0.3)',
        'glow-rose': '0 0 20px rgba(232, 74, 127, 0.3)',
        'glow-purple': '0 0 20px rgba(155, 89, 182, 0.3)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
