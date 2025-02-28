module.exports = {
  // Use TypeScript parser for ESLint
  parser: '@typescript-eslint/parser',
  
  // Parser options
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true, // Enable JSX support
    },
    project: './tsconfig.json', // Path to TypeScript config
    tsconfigRootDir: __dirname,
  },
  
  // Environment settings
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  
  // Configurations to extend
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:import/errors',
    'plugin:import/warnings',
    'plugin:import/typescript',
    'plugin:jsx-a11y/recommended',
    'plugin:prettier/recommended', // Make sure this is last to override other formatting rules
  ],
  
  // ESLint plugins
  plugins: [
    'react',
    'react-hooks',
    '@typescript-eslint',
    'import',
    'jsx-a11y',
    'prettier',
  ],
  
  // Plugin settings
  settings: {
    react: {
      version: 'detect', // Auto-detect React version
    },
    'import/resolver': {
      typescript: {}, // Use TypeScript resolver for import plugin
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
  
  // ESLint rules
  rules: {
    // TypeScript specific rules
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-non-null-assertion': 'warn',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/await-thenable': 'error',
    '@typescript-eslint/no-misused-promises': 'error',
    
    // React specific rules
    'react/prop-types': 'off', // Not needed with TypeScript
    'react/react-in-jsx-scope': 'off', // Not needed with React 17+
    'react/display-name': 'off',
    'react/jsx-uses-react': 'off', // Not needed with React 17+
    'react/jsx-uses-vars': 'error',
    'react/no-unescaped-entities': 'warn',
    'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
    
    // React hooks rules
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // Import rules
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
    'import/no-duplicates': 'error',
    'import/no-unresolved': 'error',
    'import/no-cycle': 'error',
    'import/first': 'error',
    'import/no-named-as-default-member': 'warn',
    
    // Accessibility rules
    'jsx-a11y/anchor-is-valid': 'warn',
    'jsx-a11y/click-events-have-key-events': 'warn',
    'jsx-a11y/no-static-element-interactions': 'warn',
    
    // General rules
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'warn',
    'no-alert': 'error',
    'no-duplicate-imports': 'off', // Covered by import/no-duplicates
    'prefer-const': 'error',
    'spaced-comment': ['error', 'always'],
    'eqeqeq': ['error', 'always'],
    'curly': ['error', 'all'],
    'no-unused-expressions': 'off', // Sometimes conflicts with TypeScript
    '@typescript-eslint/no-unused-expressions': ['error', { allowShortCircuit: true, allowTernary: true }],
    
    // Prettier integration
    'prettier/prettier': [
      'error',
      {
        singleQuote: true,
        trailingComma: 'es5',
        printWidth: 100,
        tabWidth: 2,
        semi: true,
      },
    ],
  },
  
  // Overrides for specific file patterns
  overrides: [
    {
      // Test files
      files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-non-null-assertion': 'off',
      },
    },
    {
      // Configuration files
      files: ['*.js', '*.cjs'],
      rules: {
        '@typescript-eslint/no-var-requires': 'off',
      },
    },
  ],
};