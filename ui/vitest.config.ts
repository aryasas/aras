import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

// claude-sonnet-4-6
// Unit/component test config for the aras-core framework layer. Reuses the app's
// vite config (plugins, aliases) and layers jsdom + RTL on top. Playwright e2e
// lives separately (test:e2e); these are fast in-process component tests.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      exclude: ['node_modules', 'tests/**', 'e2e/**'],
      css: false,
    },
  }),
)
