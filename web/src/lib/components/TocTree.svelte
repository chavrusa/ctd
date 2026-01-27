<script lang="ts">
	import type { TocEntry } from '$lib/types';
	import { ChevronRight, ExternalLink, File, FileText, Loader2 } from 'lucide-svelte';
	import { cn } from '$lib/utils';
	import TocTree from './TocTree.svelte';

	interface Props {
		entries: TocEntry[];
		selectedPath: string | null;
		onSelect: (entry: TocEntry) => void;
		expandedPaths?: Set<string>;
		depth?: number;
	}

	let { entries, selectedPath, onSelect, expandedPaths = new Set(), depth = 0 }: Props = $props();

	let localExpanded: Record<string, boolean> = $state({});
	let loadingPaths: Set<string> = $state(new Set());

	async function handleFolderClick(entry: TocEntry) {
		// If this folder has a $ref and no children, load them
		if (entry.$ref && !entry.children) {
			loadingPaths.add(entry.path);
			loadingPaths = new Set(loadingPaths);

			try {
				const res = await fetch('/' + entry.$ref);
				if (!res.ok) throw new Error(`Failed to load: ${res.status}`);
				const childToc = await res.json();
				// Merge children into entry
				entry.children = childToc.children;
				// Clear the $ref to indicate it's loaded
				delete entry.$ref;
			} catch (error) {
				console.error('Failed to load toc:', error);
			} finally {
				loadingPaths.delete(entry.path);
				loadingPaths = new Set(loadingPaths);
			}
		}

		toggleFolder(entry.path);
	}

	function toggleFolder(path: string) {
		localExpanded[path] = !isExpanded(path);
	}

	function isExpanded(path: string): boolean {
		// Local state takes precedence, then check expandedPaths from parent
		if (path in localExpanded) return localExpanded[path];
		return expandedPaths.has(path);
	}

	function isLoading(path: string): boolean {
		return loadingPaths.has(path);
	}

	function getIcon(type: string) {
		if (type === 'pdf') return FileText;
		return File;
	}

	function handleFileClick(entry: TocEntry) {
		// If entry has external URL, open it in new tab
		if (entry.url) {
			window.open(entry.url, '_blank', 'noopener,noreferrer');
		} else {
			onSelect(entry);
		}
	}
</script>

<div class="flex flex-col">
	{#each entries as entry}
		{@const isFolder = entry.type === 'folder'}
		{@const expanded = isExpanded(entry.path)}
		{@const isSelected = selectedPath === entry.path}
		{@const Icon = getIcon(entry.type)}

		{@const loading = isLoading(entry.path)}
		<button
			class={cn(
				'w-full flex items-center gap-1.5 py-1.5 text-left text-sm rounded-md transition-colors',
				'hover:bg-gray-100 dark:hover:bg-gray-800',
				isSelected && 'bg-gray-100 dark:bg-gray-800 font-medium'
			)}
			style="padding-left: {8 + depth * 16}px; padding-right: 8px;"
			title={entry.title || entry.name}
			onclick={() => {
				if (isFolder) {
					handleFolderClick(entry);
				} else {
					handleFileClick(entry);
				}
			}}
		>
			{#if isFolder}
				{#if loading}
					<Loader2 class="h-4 w-4 shrink-0 animate-spin text-gray-400" />
				{:else}
					<ChevronRight
						class={cn('h-4 w-4 shrink-0 transition-transform', expanded && 'rotate-90')}
					/>
				{/if}
			{:else if entry.url}
				<ExternalLink class="h-4 w-4 shrink-0 text-blue-500" />
			{:else}
				<Icon class="h-4 w-4 shrink-0 text-gray-500" />
			{/if}
			<span class="truncate">{entry.title || entry.name}</span>
		</button>

		{#if isFolder && expanded && entry.children}
			<TocTree
				entries={entry.children}
				{selectedPath}
				{onSelect}
				{expandedPaths}
				depth={depth + 1}
			/>
		{/if}
	{/each}
</div>
