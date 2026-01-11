<script lang="ts">
	import type { TocEntry } from '$lib/types';
	import { FileText, Download } from 'lucide-svelte';

	interface Props {
		entry: TocEntry | null;
		scrollPosition?: number | null;
		onScrollChange?: (scroll: number) => void;
	}

	let { entry, scrollPosition = null, onScrollChange }: Props = $props();

	function getViewerType(type: string): 'pdf' | 'image' | 'audio' | 'video' | 'text' | 'download' {
		if (type === 'pdf') return 'pdf';
		if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(type)) return 'image';
		if (['mp3', 'wav', 'ogg'].includes(type)) return 'audio';
		if (['mp4', 'webm', 'mov'].includes(type)) return 'video';
		if (['txt', 'md', 'csv'].includes(type)) return 'text';
		return 'download';
	}

	let viewerType = $derived(entry ? getViewerType(entry.type) : null);

	// For PDFs, append #page=N if we have a scroll position
	let fileUrl = $derived(() => {
		if (!entry) return null;
		let url = `/${entry.path}`;
		if (viewerType === 'pdf' && scrollPosition) {
			url += `#page=${scrollPosition}`;
		}
		return url;
	});

	let scrollContainer: HTMLDivElement | undefined = $state();

	function handleScroll(e: Event) {
		if (!onScrollChange) return;
		const target = e.target as HTMLDivElement;
		// Debounce and report scroll position (rounded to nearest 10px for cleaner URLs)
		const pos = Math.round(target.scrollTop / 10) * 10;
		onScrollChange(pos);
	}
</script>

{#if entry && fileUrl()}
	<div class="h-full flex flex-col">
		<!-- Header with context -->
		{#if entry.summary}
			<div class="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
				<h2 class="font-medium text-lg">{entry.title || entry.name}</h2>
				<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{entry.summary}</p>
			</div>
		{/if}

		<!-- Viewer area -->
		<div class="flex-1 overflow-hidden">
			{#if viewerType === 'pdf'}
				<iframe src={fileUrl()} class="w-full h-full" title={entry.name}></iframe>
			{:else if viewerType === 'image'}
				<div
					class="h-full overflow-auto p-4 flex items-start justify-center"
					bind:this={scrollContainer}
					onscroll={handleScroll}
				>
					<img src={fileUrl()} alt={entry.name} class="max-w-full" />
				</div>
			{:else if viewerType === 'audio'}
				<div class="h-full flex items-center justify-center p-4">
					<audio src={fileUrl()} controls class="w-full max-w-lg">
						Your browser does not support the audio element.
					</audio>
				</div>
			{:else if viewerType === 'video'}
				<div class="h-full flex items-center justify-center p-4 bg-black">
					<!-- svelte-ignore a11y_media_has_caption -->
					<video src={fileUrl()} controls class="max-w-full max-h-full">
						Your browser does not support the video element.
					</video>
				</div>
			{:else}
				<!-- Download fallback -->
				<div class="h-full flex flex-col items-center justify-center gap-4 p-4">
					<FileText class="h-16 w-16 text-gray-400" />
					<p class="text-gray-600 dark:text-gray-400">Preview not available for this file type</p>
					<a
						href={fileUrl()}
						download
						class="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
					>
						<Download class="h-4 w-4" />
						Download {entry.name}
					</a>
				</div>
			{/if}
		</div>
	</div>
{:else}
	<!-- Empty state / landing -->
	<div class="h-full flex flex-col items-center justify-center p-8 text-center">
		<FileText class="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
		<h2 class="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">
			CTD Document Archive
		</h2>
		<p class="text-gray-600 dark:text-gray-400 max-w-md">
			Select a document from the sidebar to view it. This archive contains regulatory documents for ALLN-177 and ALLN-346 drug trials.
		</p>
	</div>
{/if}
