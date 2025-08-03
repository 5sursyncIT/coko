/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // African-inspired color palette
      colors: {
        // African-inspired color palette
        'african-gold': '#D4AF37',
        'african-orange': '#FF8C00',
        'african-red': '#DC143C',
        'african-green': '#228B22',
        'african-brown': '#8B4513',
        'african-earth': '#CD853F',
        
        // Senegal flag colors
        'senegal-green': '#00853F',
        'senegal-yellow': '#FDEF42',
        'senegal-red': '#E31B23',
        
        // UI colors
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        
        // Primary colors inspired by African sunsets
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: '#fef7ed',
          100: '#fdedd3',
          200: '#fbd7a5',
          300: '#f8bc6d',
          400: '#f59532',
          500: '#f2750a', // Main orange
          600: '#e35d06',
          700: '#bc4509',
          800: '#973710',
          900: '#7c2f11',
          950: '#431506'
        },
        // Secondary colors inspired by African earth
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
          50: '#f6f3f0',
          100: '#e8e0d8',
          200: '#d2c1b1',
          300: '#b89d84',
          400: '#a17c5e',
          500: '#8b6341', // Main brown
          600: '#7a5437',
          700: '#65442e',
          800: '#543829',
          900: '#472f25',
          950: '#261812'
        },
        // Accent colors inspired by African textiles
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9', // Main blue
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // Success colors inspired by African vegetation
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e', // Main green
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16'
        },
        // Warning colors
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b', // Main yellow
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          950: '#451a03'
        },
        // Error colors
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444', // Main red
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
          950: '#450a0a'
        },
        // Neutral colors with warm undertones
        neutral: {
          50: '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#d6d3d1',
          400: '#a8a29e',
          500: '#78716c',
          600: '#57534e',
          700: '#44403c',
          800: '#292524',
          900: '#1c1917',
          950: '#0c0a09'
        },
        // African flag colors for special elements
        african: {
          gold: '#FFD700',
          red: '#CE1126',
          green: '#009639',
          black: '#000000'
        }
      },
      
      // Typography inspired by African design
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
        display: ['Poppins', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif']
      },
      
      // Spacing scale optimized for mobile-first African users
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
        '144': '36rem'
      },
      
      // Border radius for modern African aesthetic
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem'
      },
      
      // Box shadows with warm undertones
      boxShadow: {
        'warm': '0 4px 6px -1px rgba(251, 146, 60, 0.1), 0 2px 4px -1px rgba(251, 146, 60, 0.06)',
        'warm-lg': '0 10px 15px -3px rgba(251, 146, 60, 0.1), 0 4px 6px -2px rgba(251, 146, 60, 0.05)',
        'earth': '0 4px 6px -1px rgba(139, 99, 65, 0.1), 0 2px 4px -1px rgba(139, 99, 65, 0.06)',
        'earth-lg': '0 10px 15px -3px rgba(139, 99, 65, 0.1), 0 4px 6px -2px rgba(139, 99, 65, 0.05)'
      },
      
      // Animation and transitions
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounceGentle 2s infinite'
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' }
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' }
        }
      },
      
      // Screen sizes optimized for African mobile usage
      screens: {
        'xs': '475px',
        '3xl': '1600px'
      },
      
      // Typography scale
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        '7xl': ['4.5rem', { lineHeight: '1' }],
        '8xl': ['6rem', { lineHeight: '1' }],
        '9xl': ['8rem', { lineHeight: '1' }]
      },
      
      // Z-index scale
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100'
      },
      
      // Backdrop blur
      backdropBlur: {
        'xs': '2px'
      },
      
      // Grid template columns for complex layouts
      gridTemplateColumns: {
        '16': 'repeat(16, minmax(0, 1fr))',
        'auto-fit': 'repeat(auto-fit, minmax(250px, 1fr))',
        'auto-fill': 'repeat(auto-fill, minmax(250px, 1fr))'
      },
      
      // Aspect ratios for media content
      aspectRatio: {
        '4/3': '4 / 3',
        '3/2': '3 / 2',
        '2/3': '2 / 3',
        '9/16': '9 / 16'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms')({
      strategy: 'class'
    }),
    require('@tailwindcss/typography'),
    // Custom plugin for African-specific utilities
    function({ addUtilities, addComponents, theme }) {
      // African-inspired gradient utilities
      addUtilities({
        '.bg-gradient-sunset': {
          'background-image': 'linear-gradient(135deg, #f59532 0%, #f2750a 50%, #e35d06 100%)'
        },
        '.bg-gradient-earth': {
          'background-image': 'linear-gradient(135deg, #8b6341 0%, #7a5437 50%, #65442e 100%)'
        },
        '.bg-gradient-savanna': {
          'background-image': 'linear-gradient(135deg, #22c55e 0%, #16a34a 50%, #15803d 100%)'
        },
        '.bg-gradient-sky': {
          'background-image': 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%)'
        }
      })
      
      // African-inspired component classes
      addComponents({
        '.card-african': {
          '@apply bg-white dark:bg-neutral-800 rounded-2xl shadow-warm border border-neutral-200 dark:border-neutral-700 p-6': {}
        },
        '.btn-african': {
          '@apply inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-xl shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2': {}
        },
        '.btn-primary': {
          '@apply btn-african bg-primary-500 hover:bg-primary-600 text-white focus:ring-primary-500': {}
        },
        '.btn-secondary': {
          '@apply btn-african bg-secondary-500 hover:bg-secondary-600 text-white focus:ring-secondary-500': {}
        },
        '.input-african': {
          '@apply block w-full px-4 py-3 border border-neutral-300 dark:border-neutral-600 rounded-xl shadow-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100': {}
        },
        '.text-gradient-sunset': {
          '@apply bg-gradient-to-r from-primary-500 to-primary-600 bg-clip-text text-transparent': {}
        }
      })
    }
  ]
}