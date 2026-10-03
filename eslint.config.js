// Lint the hand-written front end and the Node check scripts. Vendor, data and
// generated files are excluded. Rules stay close to ESLint's
// recommended set: the aim is to catch real mistakes, not to impose style,
// which Prettier handles.
import js from '@eslint/js';
import globals from 'globals';

export default [
  {
    ignores: [
      'docs/vendor/**',
      'docs/data/**',
      'node_modules/**',
      'exports/**',
      'reference/**',
    ],
  },
  js.configs.recommended,
  {
    files: ['docs/**/*.js'],
    languageOptions: { ecmaVersion: 2023, sourceType: 'module', globals: { ...globals.browser } },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' }],
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
  {
    files: ['docs/flood-worker.js'],
    languageOptions: { globals: { ...globals.worker } },
  },
  {
    files: ['scripts/**/*.mjs', 'eslint.config.js'],
    languageOptions: { ecmaVersion: 2023, sourceType: 'module', globals: { ...globals.node } },
    rules: { 'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }] },
  },
];
