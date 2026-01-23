export interface TocEntry {
	name: string;
	type: 'folder' | 'pdf' | 'docx' | 'xlsx' | 'csv' | 'txt' | 'png' | 'jpg' | 'gif' | 'mp3' | 'mp4' | string;
	path: string;
	children?: TocEntry[];
	// Lazy loading: URL to child toc.json for this folder
	$ref?: string;
	// External URL: for entries that link to external resources (e.g., EMA documents)
	url?: string;
	// Metadata fields (from metadata.json)
	title?: string;
	summary?: string;
	tags?: string[];
	drug?: string;
}
