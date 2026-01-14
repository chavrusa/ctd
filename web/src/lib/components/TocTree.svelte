<script lang="ts">
	import type { TocEntry } from '$lib/types';
	import { ChevronRight, File, FileText } from 'lucide-svelte';
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

	function toggleFolder(path: string) {
		localExpanded[path] = !isExpanded(path);
	}

	function isExpanded(path: string): boolean {
		// Local state takes precedence, then check expandedPaths from parent
		if (path in localExpanded) return localExpanded[path];
		return expandedPaths.has(path);
	}

	function getIcon(type: string) {
		if (type === 'pdf') return FileText;
		return File;
	}
</script>

<div class="flex flex-col">
	{#each entries as entry}
		{@const isFolder = entry.type === 'folder'}
		{@const expanded = isExpanded(entry.path)}
		{@const isSelected = selectedPath === entry.path}
		{@const Icon = getIcon(entry.type)}

		<button
			class={cn(
				'w-full flex items-center gap-1.5 py-1.5 text-left text-sm rounded-md transition-colors',
				'hover:bg-gray-100 dark:hover:bg-gray-800',
				isSelected && 'bg-gray-100 dark:bg-gray-800 font-medium'
			)}
			style="padding-left: {8 + depth * 16}px; padding-right: 8px;"
			title={entry.name}
			onclick={() => {
				if (isFolder) {
					toggleFolder(entry.path);
				} else {
					onSelect(entry);
				}
			}}
		>
			{#if isFolder}
				<ChevronRight
					class={cn('h-4 w-4 shrink-0 transition-transform', expanded && 'rotate-90')}
				/>
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
