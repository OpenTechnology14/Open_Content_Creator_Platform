import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

// Explicit test-only entry. Production/dev builds never import the synthetic IPC fixture.
export default defineConfig({
  plugins: [{
    name: 'extend-synthetic-browser-fixture',
    enforce: 'pre',
    transform(code: string, id: string) {
      if (id.endsWith('/src/routes/+page.svelte')) {
        return code.replace('<script lang="ts">', '<script lang="ts">\nimport "../../tests/browser-fixture.js";')
          .replace('<div class:compact=', '<p role="status">Browser fixture · synthetic data · no native operations</p>\n<div class:compact=');
      }
    },
  }, sveltekit()],
  server: { host: '127.0.0.1', strictPort: true, watch: { ignored: ['**/src-tauri/**'] } },
});
