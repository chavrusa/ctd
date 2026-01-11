<script lang="ts">
	import { onMount } from 'svelte';
	import { Menu, X, Sun, Moon, Home } from 'lucide-svelte';
	import TocTree from '$lib/components/TocTree.svelte';
	import DocumentViewer from '$lib/components/DocumentViewer.svelte';
	import type { TocEntry } from '$lib/types';
	import { cn } from '$lib/utils';

	let toc: TocEntry | null = $state(null);
	let selectedEntry: TocEntry | null = $state(null);
	let expandedPaths: Set<string> = $state(new Set());
	let scrollPosition: number | null = $state(null);
	let mobileMenuOpen = $state(false);
	let darkMode = $state(false);

	onMount(async () => {
		// Load TOC
		const res = await fetch('/toc.json');
		toc = await res.json();

		// Check URL hash for deep link
		handleHashChange();
		window.addEventListener('hashchange', handleHashChange);

		// Check for dark mode preference
		darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
		updateDarkMode();

		return () => {
			window.removeEventListener('hashchange', handleHashChange);
		};
	});

	function parseHash(): { path: string; scroll: number | null } {
		const hash = window.location.hash.slice(1);
		if (!hash) return { path: '', scroll: null };

		const [pathPart, queryPart] = hash.split('?');
		const path = decodeURIComponent(pathPart);

		let scroll: number | null = null;
		if (queryPart) {
			const params = new URLSearchParams(queryPart);
			const scrollParam = params.get('scroll') || params.get('page');
			if (scrollParam) scroll = parseInt(scrollParam, 10);
		}

		return { path, scroll };
	}

	function handleHashChange() {
		const { path, scroll } = parseHash();
		scrollPosition = scroll;

		if (path && toc) {
			const entry = findEntryByPath(toc, path);
			if (entry) {
				selectedEntry = entry;
				// Expand all parent folders
				expandedPaths = getParentPaths(path);
			}
		}
	}

	function findEntryByPath(root: TocEntry, path: string): TocEntry | null {
		if (root.path === path) return root;
		if (root.children) {
			for (const child of root.children) {
				const found = findEntryByPath(child, path);
				if (found) return found;
			}
		}
		return null;
	}

	function getParentPaths(filePath: string): Set<string> {
		const paths = new Set<string>();
		const parts = filePath.split('/');

		// Build up each parent path
		// e.g., "documents/ALLN-346/foo/bar.pdf" -> ["documents", "documents/ALLN-346", "documents/ALLN-346/foo"]
		for (let i = 1; i < parts.length; i++) {
			paths.add(parts.slice(0, i).join('/'));
		}

		return paths;
	}

	function selectDocument(entry: TocEntry) {
		selectedEntry = entry;
		scrollPosition = null;
		updateHash(entry.path, null);
		mobileMenuOpen = false;
	}

	function updateHash(path: string, scroll: number | null) {
		let hash = encodeURIComponent(path);
		if (scroll !== null) {
			const param = selectedEntry?.type === 'pdf' ? 'page' : 'scroll';
			hash += `?${param}=${scroll}`;
		}
		window.history.replaceState(null, '', '#' + hash);
	}

	function handleScrollChange(scroll: number) {
		scrollPosition = scroll;
		if (selectedEntry) {
			updateHash(selectedEntry.path, scroll);
		}
	}

	function toggleDarkMode() {
		darkMode = !darkMode;
		updateDarkMode();
	}

	function updateDarkMode() {
		if (darkMode) {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}
	}

	function goHome() {
		selectedEntry = null;
		scrollPosition = null;
		window.history.replaceState(null, '', window.location.pathname);
	}
</script>

<svelte:head>
	<title>CTD Document Archive</title>
</svelte:head>

<div class="h-screen flex flex-col">
	<!-- Header -->
	<header class="h-14 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex items-center px-4 gap-4 shrink-0">
		<button
			class="lg:hidden p-2 -ml-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
			onclick={() => mobileMenuOpen = !mobileMenuOpen}
		>
			{#if mobileMenuOpen}
				<X class="h-5 w-5" />
			{:else}
				<Menu class="h-5 w-5" />
			{/if}
		</button>

		<button onclick={goHome} class="font-semibold hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
			CTD Document Archive
		</button>

		<div class="flex-1"></div>

		{#if selectedEntry}
			<button
				class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
				onclick={goHome}
				title="Back to Table of Contents"
			>
				<Home class="h-5 w-5" />
			</button>
		{/if}

		<button
			class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
			onclick={toggleDarkMode}
			title="Toggle dark mode"
		>
			{#if darkMode}
				<Sun class="h-5 w-5" />
			{:else}
				<Moon class="h-5 w-5" />
			{/if}
		</button>
	</header>

	<div class="flex-1 flex overflow-hidden">
		<!-- Sidebar -->
		<aside
			class={cn(
				'w-80 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col shrink-0 overflow-hidden',
				'fixed inset-y-14 left-0 z-40 lg:static lg:inset-auto',
				'transition-transform lg:transition-none',
				mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
			)}
		>
			<div class="flex-1 overflow-y-auto p-2">
				{#if toc?.children}
					<TocTree
						entries={toc.children}
						selectedPath={selectedEntry?.path ?? null}
						onSelect={selectDocument}
						{expandedPaths}
					/>
				{:else}
					<div class="p-4 text-gray-500 text-sm">Loading...</div>
				{/if}
			</div>
		</aside>

		<!-- Mobile overlay -->
		{#if mobileMenuOpen}
			<button
				class="fixed inset-0 bg-black/50 z-30 lg:hidden"
				onclick={() => mobileMenuOpen = false}
				aria-label="Close menu"
			></button>
		{/if}

		<!-- Main content -->
		<main class="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-950">
			<DocumentViewer
				entry={selectedEntry}
				{scrollPosition}
				onScrollChange={handleScrollChange}
			/>
		</main>
	</div>
</div>
