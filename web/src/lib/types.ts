export interface TocEntry {
	name: string;
	type: 'folder' | 'pdf' | 'docx' | 'xlsx' | 'csv' | 'txt' | 'png' | 'jpg' | 'gif' | 'mp3' | 'mp4' | string;
	path: string;
	children?: TocEntry[];
	// Metadata fields (from metadata.json)
	title?: string;
	summary?: string;
	tags?: string[];
	drug?: string;
}
