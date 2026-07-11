import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        // Light mode (Option B)
        canvas: '#f5f5f0',
        surface: '#ffffff',
        'surface-2': '#fafaf7',
        border: '#e5e5dc',
        'border-2': '#d4d4c8',
        forest: {
          DEFAULT: '#166534',
          2: '#15803d',
          3: '#16a34a',
          soft: '#dcfce7',
          dim: 'rgba(22,101,52,0.08)',
        },
        amber: {
          DEFAULT: '#b45309',
          2: '#d97706',
          soft: '#fef3c7',
          dim: 'rgba(180,83,9,0.08)',
        },
        sage: {
          DEFAULT: '#6b7c5e',
          dim: 'rgba(107,124,94,0.1)',
        },
        ink: {
          DEFAULT: '#1c1c18',
          2: '#4a4a42',
          3: '#8a8a7e',
          4: '#b4b4a8',
        },
        // Dark mode (Option C)
        dark: {
          base: '#100e0a',
          2: '#171410',
          3: '#1f1b14',
          4: '#26211a',
          5: '#2e2820',
        },
        gold: {
          DEFAULT: '#f5a623',
          2: '#e8950f',
          3: '#fbbf24',
          dim: 'rgba(245,166,35,0.1)',
          glow: 'rgba(245,166,35,0.2)',
        },
        parchment: {
          DEFAULT: '#f5ead8',
          2: '#a89878',
          3: '#6b5c44',
          4: '#3d3020',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
