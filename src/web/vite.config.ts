import { defineConfig } from 'vite'; // v4.4.9
import react from '@vitejs/plugin-react'; // v4.0.4
import viteTsconfigPaths from 'vite-tsconfig-paths'; // v4.2.0
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  // Configure plugins for React with Fast Refresh and TypeScript path resolution
  plugins: [
    react(), // Enables React support and Fast Refresh
    viteTsconfigPaths() // Resolves imports using TypeScript path mappings
  ],
  
  // Resolve path aliases for cleaner imports and better code organization
  resolve: {
    alias: {
      '@': './src', // Root source directory
      '@components': './src/components', // UI components
      '@hooks': './src/hooks', // Custom React hooks
      '@utils': './src/utils', // Utility functions
      '@api': './src/api', // API integration
      '@features': './src/features', // Feature modules
      '@store': './src/store', // Redux store
      '@assets': './src/assets', // Static assets
      '@types': './src/types', // TypeScript type definitions
      '@config': './src/config', // Configuration files
      '@contexts': './src/contexts', // React contexts
      '@services': './src/services', // Service layer
    },
  },
  
  // Development server configuration
  server: {
    port: 3000, // Default port for development
    host: true, // Listen on all network interfaces
    open: true, // Automatically open browser on start
    strictPort: false, // Find another port if 3000 is in use
    proxy: {
      // Proxy API requests to backend server
      '/api': {
        target: 'http://localhost:5000', // Backend API server
        changeOrigin: true, // Changes the origin of the host header to the target URL
        secure: false, // Accepts self-signed certificates
      },
      // Proxy WebSocket connections for real-time features
      '/ws': {
        target: 'ws://localhost:5007', // WebSocket server
        ws: true, // Enables WebSocket proxy
      },
    },
  },
  
  // Production build configuration
  build: {
    outDir: 'dist', // Output directory for production build
    sourcemap: true, // Generate source maps for debugging
    minify: 'terser', // Use Terser for minification
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log statements in production
      },
    },
    rollupOptions: {
      output: {
        // Split chunks for optimal loading and caching
        manualChunks: {
          // Core libraries
          vendor: ['react', 'react-dom', 'react-router-dom', '@reduxjs/toolkit', 'react-redux'],
          // Chart libraries for analytics and reporting features
          charts: ['chart.js', 'react-chartjs-2'],
        },
      },
    },
  },
  
  // Testing configuration
  test: {
    globals: true, // Make test variables available globally
    environment: 'jsdom', // Use jsdom for DOM environment
    setupFiles: ['./src/__tests__/setup.ts'], // Test setup file
  },
  
  // Define global constants that can be replaced at build time
  define: {
    // This will be replaced during the build process with the actual version
    __APP_VERSION__: '{{APP_VERSION}}',
  },
});