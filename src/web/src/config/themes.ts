// Define the theme type options
export type ThemeType = 'light' | 'dark';

// Define the color palette structure
export interface ColorPalette {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  neutral: {
    100: string;
    200: string;
    700: string;
    900: string;
  };
  background: {
    primary: string;
    secondary: string;
  };
  text: {
    primary: string;
    secondary: string;
    disabled: string;
  };
}

// Define typography structure
export interface Typography {
  fontFamily: string;
  headings: {
    h1: {
      fontSize: string;
      fontWeight: number;
    };
    h2: {
      fontSize: string;
      fontWeight: number;
    };
    h3: {
      fontSize: string;
      fontWeight: number;
    };
  };
  body: {
    fontSize: string;
    fontWeight: number;
  };
  labels: {
    fontSize: string;
    fontWeight: number;
  };
  buttons: {
    fontSize: string;
    fontWeight: number;
  };
}

// Define spacing structure
export interface Spacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
}

// Define border radius structure
export interface BorderRadius {
  sm: string;
  md: string;
  lg: string;
}

// Define shadows structure
export interface Shadows {
  sm: string;
  md: string;
  lg: string;
}

// Define the complete theme structure
export interface Theme {
  colors: ColorPalette;
  typography: Typography;
  spacing: Spacing;
  borderRadius: BorderRadius;
  shadows: Shadows;
}

// Define color palettes for light and dark themes
export const themeColors: Record<ThemeType, ColorPalette> = {
  light: {
    primary: '#4F46E5', // Primary actions, links, active states
    secondary: '#9333EA', // Secondary actions, highlights
    success: '#22C55E', // Completed status, success messages
    warning: '#F59E0B', // Warning states, medium priority
    error: '#EF4444', // Error messages, high priority tasks
    neutral: {
      100: '#F3F4F6', // Page backgrounds
      200: '#E5E7EB', // Container backgrounds, dividers
      700: '#374151', // Body text
      900: '#111827', // Headings, important text
    },
    background: {
      primary: '#FFFFFF',
      secondary: '#F9FAFB',
    },
    text: {
      primary: '#111827',
      secondary: '#6B7280',
      disabled: '#9CA3AF',
    },
  },
  dark: {
    primary: '#818CF8', // Lighter shade for dark mode
    secondary: '#A78BFA', // Lighter shade for dark mode
    success: '#34D399', // Lighter shade for dark mode
    warning: '#FBBF24', // Lighter shade for dark mode
    error: '#F87171', // Lighter shade for dark mode
    neutral: {
      100: '#1F2937', // Dark mode page backgrounds (inverted)
      200: '#374151', // Dark mode container backgrounds (inverted)
      700: '#D1D5DB', // Dark mode body text (inverted)
      900: '#F9FAFB', // Dark mode headings (inverted)
    },
    background: {
      primary: '#111827',
      secondary: '#1F2937',
    },
    text: {
      primary: '#F9FAFB',
      secondary: '#D1D5DB',
      disabled: '#6B7280',
    },
  },
};

// Define typography settings
export const typography: Typography = {
  fontFamily: 'Inter, sans-serif',
  headings: {
    h1: {
      fontSize: '24px',
      fontWeight: 600,
    },
    h2: {
      fontSize: '20px',
      fontWeight: 600,
    },
    h3: {
      fontSize: '18px',
      fontWeight: 600,
    },
  },
  body: {
    fontSize: '14px',
    fontWeight: 400,
  },
  labels: {
    fontSize: '12px',
    fontWeight: 500,
  },
  buttons: {
    fontSize: '14px',
    fontWeight: 500,
  },
};

// Define spacing values
export const spacing: Spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
};

// Define border radius values
export const borderRadius: BorderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
};

// Define shadow values
export const shadows: Shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
};

// Set default theme
export const defaultTheme: ThemeType = 'light';

// Utility function to get colors for a specific theme
export function getThemeColors(theme?: ThemeType): ColorPalette {
  if (theme && Object.keys(themeColors).includes(theme)) {
    return themeColors[theme];
  }
  return themeColors[defaultTheme];
}