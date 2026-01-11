<script lang="ts">
	import { RTFJS } from 'rtf.js';
	import { Loader2, Download } from 'lucide-svelte';

	interface Props {
		src: string;
		onScrollChange?: (scroll: number) => void;
	}

	let { src, onScrollChange }: Props = $props();

	let htmlElements: HTMLElement[] | null = $state(null);
	let rawText: string | null = $state(null);
	let loading = $state(false);
	let error: string | null = $state(null);
	let scrollContainer: HTMLDivElement | undefined = $state();
	let contentContainer: HTMLDivElement | undefined = $state();

	function stringToArrayBuffer(str: string): ArrayBuffer {
		const buffer = new ArrayBuffer(str.length);
		const bufferView = new Uint8Array(buffer);
		for (let i = 0; i < str.length; i++) {
			bufferView[i] = str.charCodeAt(i);
		}
		return buffer;
	}

	// Extract plain text from RTF by stripping control words
	function extractPlainText(rtf: string): string {
		return rtf
			.replace(/\\[a-z]+[-]?\d*\s?/gi, '') // Remove control words
			.replace(/[{}]/g, '') // Remove braces
			.replace(/\\'([0-9a-f]{2})/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16))) // Decode hex chars
			.replace(/\r\n/g, '\n')
			.trim();
	}

	async function loadRtf() {
		loading = true;
		error = null;
		htmlElements = null;
		rawText = null;

		try {
			const res = await fetch(src);
			if (!res.ok) throw new Error('Failed to load RTF file');

			const rtfContent = await res.text();

			// Disable logging for cleaner output
			RTFJS.loggingEnabled(false);

			try {
				const doc = new RTFJS.Document(stringToArrayBuffer(rtfContent), {});
				htmlElements = await doc.render();
			} catch (parseError) {
				// RTF parsing failed - fall back to plain text extraction
				console.warn('RTF parsing failed, falling back to text extraction:', parseError);
				rawText = extractPlainText(rtfContent);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load RTF file';
		} finally {
			loading = false;
		}
	}

	// Append rendered elements to the container
	$effect(() => {
		if (htmlElements && contentContainer) {
			contentContainer.innerHTML = '';
			for (const el of htmlElements) {
				contentContainer.appendChild(el.cloneNode(true));
			}
		}
	});

	// Load RTF when src changes
	$effect(() => {
		if (src) {
			loadRtf();
		}
	});

	function handleScroll(e: Event) {
		if (!onScrollChange) return;
		const target = e.target as HTMLDivElement;
		const pos = Math.round(target.scrollTop / 10) * 10;
		onScrollChange(pos);
	}
</script>

{#if loading}
	<div class="h-full flex items-center justify-center">
		<Loader2 class="h-8 w-8 animate-spin text-gray-400" />
	</div>
{:else if error}
	<div class="h-full flex flex-col items-center justify-center gap-4">
		<p class="text-red-500">{error}</p>
		<a
			href={src}
			download
			class="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
		>
			<Download class="h-4 w-4" />
			Download file
		</a>
	</div>
{:else if htmlElements}
	<div
		class="h-full overflow-auto p-6"
		bind:this={scrollContainer}
		onscroll={handleScroll}
	>
		<div
			bind:this={contentContainer}
			class="rtf-content prose dark:prose-invert max-w-none"
		></div>
	</div>
{:else if rawText}
	<div
		class="h-full overflow-auto p-4"
		bind:this={scrollContainer}
		onscroll={handleScroll}
	>
		<div class="mb-3 px-2 py-1.5 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-sm rounded border border-amber-200 dark:border-amber-800">
			RTF formatting could not be rendered. Showing extracted text.
		</div>
		<pre class="text-sm font-mono whitespace-pre-wrap break-words text-gray-800 dark:text-gray-200">{rawText}</pre>
	</div>
{/if}

<style>
	.rtf-content :global(p) {
		margin: 0.5em 0;
	}
	.rtf-content :global(table) {
		border-collapse: collapse;
		margin: 1em 0;
	}
	.rtf-content :global(td),
	.rtf-content :global(th) {
		border: 1px solid #ddd;
		padding: 0.5em;
	}
</style>
