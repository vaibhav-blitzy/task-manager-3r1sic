import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F46E5',    // Primary actions, links, active states
        secondary: '#9333EA',   // Secondary actions, highlights
        success: '#22C55E',     // Completed status, success messages
        warning: '#F59E0B',     // Warning states, medium priority
        error: '#EF4444',       // Error messages, high priority tasks
        neutral: {
          100: '#F3F4F6',       // Page backgrounds
          200: '#E5E7EB',       // Container backgrounds, dividers
          700: '#374151',       // Body text
          900: '#111827',       // Headings, important text
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      fontSize: {
        xs: '12px',    // Labels
        sm: '14px',    // Body text, buttons
        base: '16px',  // Standard text
        lg: '18px',    // Small headings
        xl: '20px',    // Medium headings
        '2xl': '24px', // Large headings
      },
      screens: {
        sm: '640px',   // Mobile breakpoint
        md: '1024px',  // Tablet breakpoint
        lg: '1440px',  // Desktop breakpoint
        xl: '1920px',  // Large desktop
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
      },
      borderRadius: {
        DEFAULT: '4px',
        md: '6px',
        lg: '8px',
        full: '9999px',
      },
    },
  },
  plugins: [],
}

export default config