/**
 * PostCSS Configuration
 * 
 * This file configures the CSS processing pipeline for the Task Management System frontend.
 * It sets up TailwindCSS and other PostCSS plugins to optimize our CSS workflow.
 */

const tailwindcss = require('tailwindcss'); // tailwindcss 3.3.x
const autoprefixer = require('autoprefixer'); // autoprefixer ^10.4.x

module.exports = {
  plugins: [
    // Import and process CSS @import directives
    require('postcss-import'),
    
    // Process Tailwind directives and generate utility classes
    tailwindcss,
    
    // Add vendor prefixes to CSS rules using values from Can I Use
    // Ensures cross-browser compatibility for modern CSS features
    autoprefixer,
    
    // Only minify CSS in production mode
    ...(process.env.NODE_ENV === 'production'
      ? [
          // Compress and optimize CSS for production
          require('cssnano')({
            preset: ['default', {
              discardComments: {
                removeAll: true,
              },
              // Preserve z-index values
              zindex: false,
            }])
        ]
      : [])
  ]
};