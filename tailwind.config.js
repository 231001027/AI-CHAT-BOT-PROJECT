/** @type {import('tailwindcss').Config} */
export default {
  // Dark variants only apply under a class we never set — light theme only
  darkMode: ['selector', '.never-use-dark-mode'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#1E4DB7',
          purple: '#5B3FD9',
          green: '#2EAF62',
          50: '#eef4ff',
          100: '#d9e6ff',
          200: '#bcd3ff',
          300: '#8eb6ff',
          400: '#598dff',
          500: '#1E4DB7',
          600: '#1a42a3',
          700: '#163680',
          800: '#132b66',
          900: '#0f1f47',
        },
        purple: {
          50: '#f3f0ff',
          100: '#ebe5ff',
          200: '#d9ceff',
          300: '#b8a4ff',
          400: '#9772ff',
          500: '#5B3FD9',
          600: '#4f33c0',
          700: '#3f29a0',
          800: '#2f1f78',
          900: '#1f1568',
        },
        green: {
          50: '#eafff3',
          100: '#d2ffe6',
          200: '#a8ffcc',
          300: '#6ef0a3',
          400: '#3ed67d',
          500: '#2EAF62',
          600: '#1f9a52',
          700: '#1a7c43',
          800: '#156234',
          900: '#0f4a28',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(30, 77, 183, 0.08)',
        card: '0 10px 40px -12px rgba(30, 77, 183, 0.15)',
        'card-hover': '0 20px 60px -15px rgba(30, 77, 183, 0.25)',
        glow: '0 0 40px -8px rgba(91, 63, 217, 0.4)',
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
        '4xl': '2.25rem',
      },
      backgroundImage: {
        'grid-light':
          "url(\"data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 .5H40' fill='none' stroke='%23e2e8f0' stroke-width='1'/%3E%3C/svg%3E\")",
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.8)', opacity: '0.6' },
          '100%': { transform: 'scale(2)', opacity: '0' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        wave: {
          '0%, 100%': { transform: 'scaleY(0.3)' },
          '50%': { transform: 'scaleY(1)' },
        },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 2.5s cubic-bezier(0.4,0,0.6,1) infinite',
        shimmer: 'shimmer 2s infinite',
        wave: 'wave 1s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
