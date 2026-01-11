<script lang="ts">
	import { onMount } from 'svelte';
	import type { TocEntry } from '$lib/types';
	import { FileText, Download, Loader2 } from 'lucide-svelte';
	import * as XLSX from 'xlsx';
	import mammoth from 'mammoth';
	import TocView from './TocView.svelte';

	interface Props {
		entry: TocEntry | null;
		scrollPosition?: number | null;
		onScrollChange?: (scroll: number) => void;
	}

	let { entry, scrollPosition = null, onScrollChange }: Props = $props();

	type ViewerType = 'pdf' | 'image' | 'audio' | 'video' | 'text' | 'spreadsheet' | 'docx' | 'download';

	function getViewerType(type: string): ViewerType {
		if (type === 'pdf') return 'pdf';
		if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(type)) return 'image';
		if (['mp3', 'wav', 'ogg'].includes(type)) return 'audio';
		if (['mp4', 'webm', 'mov'].includes(type)) return 'video';
		if (['txt', 'md', 'csv', 'rtf'].includes(type)) return 'text';
		if (['xls', 'xlsx'].includes(type)) return 'spreadsheet';
		if (type === 'docx') return 'docx';
		return 'download';
	}

	let viewerType = $derived(entry ? getViewerType(entry.type) : null);

	// TOC data for landing page
	let tocData: TocEntry | null = $state(null);
	let tocLoading = $state(false);

	onMount(async () => {
		// Load TOC JSON for landing view
		tocLoading = true;
		try {
			const res = await fetch('/toc.json');
			if (res.ok) {
				tocData = await res.json();
			}
		} catch (e) {
			console.error('Failed to load TOC:', e);
		} finally {
			tocLoading = false;
		}
	});

	let fileUrl = $derived(() => {
		if (!entry) return null;
		// Encode path segments but preserve slashes
		const encodedPath = entry.path.split('/').map(segment => encodeURIComponent(segment)).join('/');
		let url = `/${encodedPath}`;
		if (viewerType === 'pdf' && scrollPosition) {
			url += `#page=${scrollPosition}`;
		}
		return url;
	});

	// State for fetched content
	let textContent: string | null = $state(null);
	let spreadsheetData: string[][] | null = $state(null);
	let docxHtml: string | null = $state(null);
	let loading = $state(false);
	let error: string | null = $state(null);

	// Fetch content when entry changes
	$effect(() => {
		if (!entry || !viewerType) return;

		textContent = null;
		spreadsheetData = null;
		docxHtml = null;
		error = null;

		if (viewerType === 'text') {
			loadTextContent();
		} else if (viewerType === 'spreadsheet') {
			loadSpreadsheet();
		} else if (viewerType === 'docx') {
			loadDocx();
		}
	});

	async function loadTextContent() {
		if (!entry) return;
		loading = true;
		try {
			const res = await fetch(`/${entry.path}`);
			if (!res.ok) throw new Error('Failed to load file');
			textContent = await res.text();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load file';
		} finally {
			loading = false;
		}
	}

	async function loadSpreadsheet() {
		if (!entry) return;
		loading = true;
		try {
			const res = await fetch(`/${entry.path}`);
			if (!res.ok) throw new Error('Failed to load file');
			const buffer = await res.arrayBuffer();
			const workbook = XLSX.read(buffer, { type: 'array' });
			const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
			spreadsheetData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 }) as string[][];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load spreadsheet';
		} finally {
			loading = false;
		}
	}

	async function loadDocx() {
		if (!entry) return;
		loading = true;
		try {
			const res = await fetch(`/${entry.path}`);
			if (!res.ok) throw new Error('Failed to load file');
			const buffer = await res.arrayBuffer();
			const result = await mammoth.convertToHtml({ arrayBuffer: buffer });
			docxHtml = result.value;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load document';
		} finally {
			loading = false;
		}
	}

	let scrollContainer: HTMLDivElement | undefined = $state();

	function handleScroll(e: Event) {
		if (!onScrollChange) return;
		const target = e.target as HTMLDivElement;
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
		<div class="flex-1 overflow-hidden relative">
			{#if loading}
				<div class="h-full flex items-center justify-center">
					<Loader2 class="h-8 w-8 animate-spin text-gray-400" />
				</div>
			{:else if error}
				<div class="h-full flex flex-col items-center justify-center gap-4 p-4">
					<p class="text-red-500">{error}</p>
					<a
						href={fileUrl()}
						download
						class="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
					>
						<Download class="h-4 w-4" />
						Download instead
					</a>
				</div>
			{:else if viewerType === 'pdf'}
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
				<div class="h-full flex flex-col items-center justify-center gap-4 p-4">
					<audio src={fileUrl()} controls class="w-full max-w-lg">
						Your browser does not support the audio element.
					</audio>
				</div>
			{:else if viewerType === 'video'}
				<div class="h-full flex flex-col items-center justify-center gap-4 p-4 bg-black">
					<!-- svelte-ignore a11y_media_has_caption -->
					<video src={fileUrl()} controls class="max-w-full max-h-[calc(100%-4rem)]">
						Your browser does not support the video element.
					</video>
				</div>
			{:else if viewerType === 'text' && textContent !== null}
				<div
					class="h-full overflow-auto p-4"
					bind:this={scrollContainer}
					onscroll={handleScroll}
				>
					<pre class="text-sm font-mono whitespace-pre-wrap break-words text-gray-800 dark:text-gray-200">{textContent}</pre>
				</div>
			{:else if viewerType === 'spreadsheet' && spreadsheetData !== null}
				<div
					class="h-full overflow-auto"
					bind:this={scrollContainer}
					onscroll={handleScroll}
				>
					<table class="min-w-full text-sm border-collapse">
						<tbody>
							{#each spreadsheetData as row, i}
								<tr class={i === 0 ? 'bg-gray-100 dark:bg-gray-800 font-medium sticky top-0' : 'border-b border-gray-200 dark:border-gray-700'}>
									{#each row as cell}
										<td class="px-3 py-2 border-r border-gray-200 dark:border-gray-700 whitespace-nowrap">
											{cell ?? ''}
										</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else if viewerType === 'docx' && docxHtml !== null}
				<div
					class="h-full overflow-auto p-6 prose dark:prose-invert max-w-none"
					bind:this={scrollContainer}
					onscroll={handleScroll}
				>
					{@html docxHtml}
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

			<!-- Download button for non-PDF viewers -->
			{#if viewerType && viewerType !== 'pdf' && viewerType !== 'download' && !loading && !error}
				<a
					href={fileUrl()}
					download
					class="absolute top-3 right-3 p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
					title="Download {entry.name}"
				>
					<Download class="h-5 w-5 text-gray-600 dark:text-gray-400" />
				</a>
			{/if}
		</div>
	</div>
{:else}
	<!-- Landing view with TOC -->
	{#if tocLoading}
		<div class="h-full flex items-center justify-center">
			<Loader2 class="h-8 w-8 animate-spin text-gray-400" />
		</div>
	{:else if tocData}
		<TocView toc={tocData} />
	{:else}
		<div class="h-full flex flex-col items-center justify-center p-8 text-center">
			<FileText class="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
			<h2 class="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">
				CTD Document Archive
			</h2>
			<p class="text-gray-600 dark:text-gray-400 max-w-md">
				Select a document from the sidebar to view it.
			</p>
		</div>
	{/if}
{/if}
