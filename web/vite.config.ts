import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		headers: {
			// Prevent caching of toc.json during development
			'Cache-Control': 'no-store'
		}
	}
});
