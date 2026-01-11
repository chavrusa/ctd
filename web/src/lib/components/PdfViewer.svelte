<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-svelte';
	import * as pdfjsLib from 'pdfjs-dist';

	interface Props {
		url: string;
		initialPage?: number;
		onPageChange?: (page: number) => void;
	}

	let { url, initialPage = 1, onPageChange }: Props = $props();

	let container: HTMLDivElement;
	let canvas: HTMLCanvasElement;
	let pdf: pdfjsLib.PDFDocumentProxy | null = $state(null);
	let currentPage = $state(initialPage);
	let totalPages = $state(0);
	let scale = $state(1.5);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Set worker path
	onMount(async () => {
		pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
		await loadPdf();
	});

	onDestroy(() => {
		if (pdf) {
			pdf.destroy();
		}
	});

	async function loadPdf() {
		loading = true;
		error = null;

		try {
			const loadingTask = pdfjsLib.getDocument(url);
			pdf = await loadingTask.promise;
			totalPages = pdf.numPages;

			// Clamp initial page to valid range
			if (currentPage < 1) currentPage = 1;
			if (currentPage > totalPages) currentPage = totalPages;

			await renderPage(currentPage);
		} catch (e) {
			console.error('Failed to load PDF:', e);
			error = 'Failed to load PDF';
		} finally {
			loading = false;
		}
	}

	async function renderPage(pageNum: number) {
		if (!pdf || !canvas) return;

		const page = await pdf.getPage(pageNum);
		const viewport = page.getViewport({ scale });

		canvas.height = viewport.height;
		canvas.width = viewport.width;

		const context = canvas.getContext('2d');
		if (!context) return;

		await page.render({
			canvasContext: context,
			viewport
		}).promise;
	}

	async function goToPage(pageNum: number) {
		if (!pdf || pageNum < 1 || pageNum > totalPages) return;
		currentPage = pageNum;
		await renderPage(currentPage);
		onPageChange?.(currentPage);
	}

	async function prevPage() {
		await goToPage(currentPage - 1);
	}

	async function nextPage() {
		await goToPage(currentPage + 1);
	}

	async function zoomIn() {
		scale = Math.min(scale + 0.25, 3);
		await renderPage(currentPage);
	}

	async function zoomOut() {
		scale = Math.max(scale - 0.25, 0.5);
		await renderPage(currentPage);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
			prevPage();
		} else if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
			nextPage();
		}
	}

	// Re-render when scale changes
	$effect(() => {
		if (pdf && canvas) {
			renderPage(currentPage);
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="h-full flex flex-col bg-gray-100 dark:bg-gray-900" bind:this={container}>
	<!-- Toolbar -->
	<div class="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center gap-2">
			<button
				onclick={prevPage}
				disabled={currentPage <= 1}
				class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
				title="Previous page"
			>
				<ChevronLeft class="h-5 w-5" />
			</button>

			<span class="text-sm">
				<input
					type="number"
					min="1"
					max={totalPages}
					value={currentPage}
					onchange={(e) => goToPage(parseInt(e.currentTarget.value))}
					class="w-12 px-1 py-0.5 text-center border rounded dark:bg-gray-700 dark:border-gray-600"
				/>
				<span class="text-gray-500"> / {totalPages}</span>
			</span>

			<button
				onclick={nextPage}
				disabled={currentPage >= totalPages}
				class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
				title="Next page"
			>
				<ChevronRight class="h-5 w-5" />
			</button>
		</div>

		<div class="flex items-center gap-2">
			<button
				onclick={zoomOut}
				disabled={scale <= 0.5}
				class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
				title="Zoom out"
			>
				<ZoomOut class="h-5 w-5" />
			</button>

			<span class="text-sm text-gray-500 w-12 text-center">{Math.round(scale * 100)}%</span>

			<button
				onclick={zoomIn}
				disabled={scale >= 3}
				class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
				title="Zoom in"
			>
				<ZoomIn class="h-5 w-5" />
			</button>
		</div>
	</div>

	<!-- PDF Canvas -->
	<div class="flex-1 overflow-auto flex justify-center p-4">
		{#if loading}
			<div class="flex items-center justify-center h-full">
				<span class="text-gray-500">Loading PDF...</span>
			</div>
		{:else if error}
			<div class="flex items-center justify-center h-full">
				<span class="text-red-500">{error}</span>
			</div>
		{:else}
			<canvas bind:this={canvas} class="shadow-lg"></canvas>
		{/if}
	</div>
</div>
