/// <reference types="vite/client" />

// Extend the ImportMetaEnv interface to include our custom environment variables
interface ImportMetaEnv {
  // Custom environment variables for API and authentication endpoints
  readonly VITE_API_URL: string;
  readonly VITE_AUTH_URL: string;
  readonly VITE_WEBSOCKET_URL: string;
  
  // Default Vite environment variables
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
  readonly BASE_URL: string;
}

// Extend the ImportMeta interface to ensure import.meta.env has our environment type
interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Declare module for importing SVG files
// Enables importing SVGs both as React components and URLs
declare module '*.svg' {
  import React from 'react';
  const content: React.FC<React.SVGProps<SVGSVGElement>> & {
    src: string;
  };
  export default content;
}

// Declare module for importing PNG files as URLs
declare module '*.png' {
  const src: string;
  export default src;
}

// Declare module for importing JPG files as URLs
declare module '*.jpg' {
  const src: string;
  export default src;
}

// Declare module for importing CSS files as modules
// Enables type-safe CSS module imports with class name mapping
declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}