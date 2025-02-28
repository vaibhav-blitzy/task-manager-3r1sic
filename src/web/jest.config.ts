import type { Config } from '@jest/types'; // ^29.5.0

/**
 * Helper function to generate Jest configuration
 * @returns Complete Jest configuration object
 */
const configGenerator = (): Config.InitialOptions => {
  return {
    // Use ts-jest preset for TypeScript support
    preset: 'ts-jest',
    
    // Use jsdom environment for React components
    testEnvironment: 'jsdom',
    
    // Setup files for React Testing Library
    setupFilesAfterEnv: ['@testing-library/jest-dom/extend-expect'],
    
    // Transform files with ts-jest and handle other file types
    transform: {
      '^.+\\.(ts|tsx)$': 'ts-jest',
      '^.+\\.(js|jsx)$': 'babel-jest',
      '^.+\\.svg$': '<rootDir>/src/web/__mocks__/svgTransform.js',
      '^.+\\.(css|scss)$': '<rootDir>/src/web/__mocks__/styleMock.js',
    },
    
    // Configure module name mapping for imports and mocks
    moduleNameMapper: {
      '^@/(.*)$': '<rootDir>/src/web/$1',
      '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
      '\\.(jpg|jpeg|png|gif|webp)$': '<rootDir>/src/web/__mocks__/fileMock.js',
    },
    
    // Specify test file patterns
    testMatch: [
      '<rootDir>/src/web/**/__tests__/**/*.{ts,tsx}',
      '<rootDir>/src/web/**/*.{spec,test}.{ts,tsx}',
    ],
    
    // Collect coverage from application source files
    collectCoverageFrom: [
      '<rootDir>/src/web/**/*.{ts,tsx}',
      '!<rootDir>/src/web/**/*.d.ts',
      '!<rootDir>/src/web/**/__tests__/**/*',
      '!<rootDir>/src/web/**/__mocks__/**/*',
      '!<rootDir>/src/web/index.tsx',
      '!<rootDir>/src/web/setupTests.ts',
    ],
    
    // Set coverage thresholds as per requirements
    coverageThreshold: {
      global: {
        statements: 85,
        branches: 75,
        functions: 90,
        lines: 85,
      },
    },
    
    // Define module directories
    moduleDirectories: ['node_modules', 'src'],
    
    // File extensions to consider
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
    
    // Ignore node_modules in tests
    testPathIgnorePatterns: ['/node_modules/'],
    
    // Configure reporters including JUnit XML for CI integration
    reporters: [
      'default',
      ['jest-junit', {
        outputDirectory: './test-results/jest',
        outputName: 'results.xml',
      }],
    ],
  };
};

export default configGenerator();