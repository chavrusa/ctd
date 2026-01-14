<script lang="ts">
	import { onMount } from 'svelte';
	import { ChevronRight, Search, FileText, X } from 'lucide-svelte';
	import Glossary from './Glossary.svelte';
	import type { TocEntry } from '$lib/types';

	interface Props {
		toc: TocEntry;
	}

	let { toc }: Props = $props();

	// Track expanded folders by path
	let expandedPaths: Set<string> = $state(new Set());
	let searchQuery = $state('');
	let matchingPaths: Set<string> = $state(new Set());
	let initialized = false;

	// Initialize with first 3 levels expanded (only once)
	onMount(() => {
		if (toc && !initialized) {
			const initial = new Set<string>();
			collectPathsToDepth(toc, 0, 3, initial);
			expandedPaths = initial;
			initialized = true;
		}
	});

	function collectPathsToDepth(node: TocEntry, depth: number, maxDepth: number, paths: Set<string>) {
		if (node.type === 'folder' && depth < maxDepth) {
			paths.add(node.path);
			for (const child of node.children ?? []) {
				collectPathsToDepth(child, depth + 1, maxDepth, paths);
			}
		}
	}

	function toggleFolder(path: string) {
		const newSet = new Set(expandedPaths);
		if (newSet.has(path)) {
			newSet.delete(path);
		} else {
			newSet.add(path);
		}
		expandedPaths = newSet;
	}

	function isExpanded(path: string): boolean {
		return expandedPaths.has(path);
	}

	// Search functionality - run on input, not as reactive effect
	function handleSearch() {
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			const matches = new Set<string>();
			const ancestors = new Set<string>();
			findMatches(toc, query, [], matches, ancestors);
			matchingPaths = matches;
			// Auto-expand ancestors of matches
			const newExpanded = new Set(expandedPaths);
			for (const path of ancestors) {
				newExpanded.add(path);
			}
			expandedPaths = newExpanded;
		} else {
			matchingPaths = new Set();
		}
	}

	function findMatches(
		node: TocEntry,
		query: string,
		ancestorPaths: string[],
		matches: Set<string>,
		ancestors: Set<string>
	) {
		const nameMatch = node.name.toLowerCase().includes(query);
		const titleMatch = node.title?.toLowerCase().includes(query);
		const summaryMatch = node.summary?.toLowerCase().includes(query);

		if (nameMatch || titleMatch || summaryMatch) {
			matches.add(node.path);
			// Add all ancestors so we can expand them
			for (const p of ancestorPaths) {
				ancestors.add(p);
			}
		}

		if (node.children) {
			const newAncestors = [...ancestorPaths, node.path];
			for (const child of node.children) {
				findMatches(child, query, newAncestors, matches, ancestors);
			}
		}
	}

	function clearSearch() {
		searchQuery = '';
		matchingPaths = new Set();
	}

	function isMatch(path: string): boolean {
		return matchingPaths.has(path);
	}

	function hasMatchingDescendant(node: TocEntry): boolean {
		if (matchingPaths.has(node.path)) return true;
		if (node.children) {
			return node.children.some(child => hasMatchingDescendant(child));
		}
		return false;
	}

	// Get file type icon color
	function getTypeColor(type: string): string {
		switch (type) {
			case 'pdf': return 'text-blue-500';
			case 'docx': return 'text-blue-600';
			case 'xlsx': case 'csv': return 'text-green-500';
			case 'png': case 'jpg': case 'gif': return 'text-purple-500';
			case 'mp3': case 'mp4': return 'text-orange-500';
			default: return 'text-gray-400';
		}
	}
</script>

<div class="h-full flex flex-col">
	<!-- Search bar -->
	<div class="sticky top-0 bg-gray-50 dark:bg-gray-950 p-4 border-b border-gray-200 dark:border-gray-800 z-10">
		<div class="relative max-w-md">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
			<input
				type="text"
				bind:value={searchQuery}
				oninput={handleSearch}
				placeholder="Search documents..."
				class="w-full pl-10 pr-10 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
			/>
			{#if searchQuery}
				<button
					onclick={clearSearch}
					class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
				>
					<X class="h-4 w-4" />
				</button>
			{/if}
		</div>
		{#if searchQuery && matchingPaths.size > 0}
			<p class="text-xs text-gray-500 mt-2">{matchingPaths.size} result{matchingPaths.size === 1 ? '' : 's'} found</p>
		{:else if searchQuery && matchingPaths.size === 0}
			<p class="text-xs text-gray-500 mt-2">No results found</p>
		{/if}
	</div>

	<!-- TOC content -->
	<div class="flex-1 overflow-auto p-4">
		<div class="max-w-4xl mx-auto">
			<!-- Welcome section -->
			<div class="mb-8">
				<h1 class="text-2xl font-bold mb-3 text-gray-900 dark:text-gray-100">
					CTD Document Archive
				</h1>
				<p class="text-gray-600 dark:text-gray-400 mb-4">
					A public archive of regulatory documents from clinical drug trials, made accessible for researchers, patients, healthcare professionals, and AI agents.
				</p>

				<!-- Drug cards -->
				<div class="grid sm:grid-cols-3 gap-4 mb-6">
					<div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
						<h3 class="font-semibold text-gray-900 dark:text-gray-100">ALLN-346</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
							Engineered uricase for hyperuricemia and gout in CKD patients. FDA Fast Track designation.
						</p>
					</div>
					<div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
						<h3 class="font-semibold text-gray-900 dark:text-gray-100">ALLN-177 (Reloxaliase)</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
							Oral enzyme therapy for enteric hyperoxaluria. Degrades dietary oxalate to prevent kidney stones.
						</p>
					</div>
					<div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
						<h3 class="font-semibold text-gray-900 dark:text-gray-100">Divalent siRNA</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
							siRNA therapeutic for prion disease. IND cleared March 2025. <a href="https://doi.org/10.1101/2024.12.05.627039" class="text-blue-500 hover:underline">CC-BY-4.0</a>
						</p>
					</div>
				</div>

				<!-- Quick guide -->
				<div class="text-sm text-gray-500 dark:text-gray-400 space-y-1 mb-6">
					<p><strong class="text-gray-700 dark:text-gray-300">Navigate:</strong> Click folders to expand/collapse. Click files to view.</p>
					<p><strong class="text-gray-700 dark:text-gray-300">Search:</strong> Use the search box above to find documents.</p>
					<p><strong class="text-gray-700 dark:text-gray-300">Share:</strong> URLs update as you navigate - copy to share direct links.</p>
				</div>

				<!-- Glossary -->
				<Glossary />
			</div>

			<!-- Section header -->
			<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
				Documents
			</h2>

			<!-- Tree -->
			{#if toc.children}
				{#each toc.children as child}
					{@render tocNode(child, 0)}
				{/each}
			{/if}
		</div>
	</div>
</div>

{#snippet tocNode(node: TocEntry, depth: number)}
	{@const expanded = isExpanded(node.path)}
	{@const matched = isMatch(node.path)}
	{@const hasMatch = hasMatchingDescendant(node)}
	{@const shouldShow = !searchQuery || hasMatch}

	<!-- Use visibility/height for hiding so Cmd+F still works -->
	<div
		class="select-text"
		style={shouldShow ? '' : 'height: 0; overflow: hidden; opacity: 0; pointer-events: none;'}
	>
		{#if node.type === 'folder'}
			<!-- Folder -->
			<div class="py-1">
				<button
					onclick={() => toggleFolder(node.path)}
					title={node.name}
					class="flex items-start gap-2 w-full text-left group hover:bg-gray-100 dark:hover:bg-gray-800 rounded px-2 py-1 -ml-2 transition-colors"
				>
					<ChevronRight
						class="h-4 w-4 mt-0.5 shrink-0 text-gray-400 transition-transform duration-200 {expanded ? 'rotate-90' : ''}"
					/>
					<div class="flex-1 min-w-0">
						<span
							class="font-medium text-gray-900 dark:text-gray-100 {matched ? 'bg-yellow-200 dark:bg-yellow-800' : ''}"
						>
							{node.title ?? node.name}
						</span>
						{#if node.summary}
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 {matched && !node.name.toLowerCase().includes(searchQuery.toLowerCase()) ? 'bg-yellow-100 dark:bg-yellow-900' : ''}">
								{node.summary}
							</p>
						{/if}
					</div>
				</button>

				<!-- Children - use CSS for collapsing to keep in DOM -->
				{#if node.children}
					<div
						class="ml-6 border-l border-gray-200 dark:border-gray-700 pl-2 transition-all duration-200"
						style={expanded ? '' : 'max-height: 0; overflow: hidden; opacity: 0;'}
					>
						{#each node.children as child}
							{@render tocNode(child, depth + 1)}
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<!-- File -->
			<div class="py-1">
				<a
					href="#{node.path}"
					title={node.name}
					class="flex items-start gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded px-2 py-1 -ml-2 transition-colors group"
				>
					<FileText class="h-4 w-4 mt-0.5 shrink-0 {getTypeColor(node.type)}" />
					<div class="flex-1 min-w-0">
						<span
							class="text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 {matched ? 'bg-yellow-200 dark:bg-yellow-800' : ''}"
						>
							{node.title ?? node.name}
						</span>
						<span class="text-xs text-gray-400 ml-1">({node.type})</span>
						{#if node.drug}
							<span class="text-xs text-blue-500 ml-1">[{node.drug}]</span>
						{/if}
						{#if node.summary}
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 {matched && !node.name.toLowerCase().includes(searchQuery.toLowerCase()) ? 'bg-yellow-100 dark:bg-yellow-900' : ''}">
								{node.summary}
							</p>
						{/if}
					</div>
				</a>
			</div>
		{/if}
	</div>
{/snippet}
