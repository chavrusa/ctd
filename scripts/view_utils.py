#!/usr/bin/env python3
"""Shared utilities for hierarchical view generation.

Provides common functionality for creating symlink-based views
like By-ATC, By-CTD, By-Date, etc.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TypeVar, Any

T = TypeVar('T')


@dataclass
class ViewStatistics:
    """Track statistics for view generation."""
    dirs_created: int = 0
    symlinks_created: int = 0
    symlinks_skipped: int = 0
    symlinks_broken: int = 0
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"Directories created: {self.dirs_created}",
            f"Symlinks created: {self.symlinks_created}",
            f"Symlinks skipped (already exist): {self.symlinks_skipped}",
            f"Broken symlinks: {self.symlinks_broken}",
        ]
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
        return "\n".join(lines)


def create_symlink_safe(
    target: Path,
    link: Path,
    allow_broken: bool = False,
    stats: ViewStatistics | None = None
) -> bool:
    """Create symlink with idempotency check.

    Args:
        target: The target path the symlink should point to
        link: The path where the symlink will be created
        allow_broken: If True, creates symlink even if target doesn't exist
        stats: Optional ViewStatistics to track counts

    Returns:
        True if symlink was created, False if skipped or failed
    """
    # Ensure parent directory exists
    link.parent.mkdir(parents=True, exist_ok=True)
    if stats and not link.parent.exists():
        stats.dirs_created += 1

    # Check if symlink already exists
    if link.is_symlink():
        if stats:
            stats.symlinks_skipped += 1
        return False

    # Check if target exists (unless allowing broken symlinks)
    if not allow_broken and not target.exists():
        if stats:
            stats.errors.append(f"Target does not exist: {target}")
        return False

    # Create relative symlink
    try:
        # Calculate relative path from link to target
        rel_target = os.path.relpath(target, link.parent)
        link.symlink_to(rel_target)

        if stats:
            stats.symlinks_created += 1
            if not target.exists():
                stats.symlinks_broken += 1

        return True

    except OSError as e:
        if stats:
            stats.errors.append(f"Failed to create symlink {link}: {e}")
        return False


def build_hierarchy_tree(
    items: list[T],
    key_func: Callable[[T], tuple[str, ...]],
    value_func: Callable[[T], Any] | None = None
) -> dict:
    """Build nested tree structure from flat items list.

    Args:
        items: List of items to organize
        key_func: Function that returns hierarchy tuple for each item
                  e.g., ("L - Antineoplastic", "L01 - Antineoplastics", "L01FF - PD-1")
        value_func: Optional function to extract value for leaf nodes.
                    If None, items are stored directly.

    Returns:
        Nested dict structure with items at leaf nodes
    """
    tree: dict = {}

    for item in items:
        keys = key_func(item)
        value = value_func(item) if value_func else item

        # Navigate/create path to leaf
        node = tree
        for key in keys[:-1]:
            if key not in node:
                node[key] = {}
            node = node[key]

        # Store item at leaf - use list if multiple items at same path
        leaf_key = keys[-1]
        if leaf_key not in node:
            node[leaf_key] = []
        node[leaf_key].append(value)

    return tree


def walk_tree(
    tree: dict,
    path: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], list]]:
    """Walk a hierarchy tree and yield (path, items) for each leaf.

    Args:
        tree: Nested dict from build_hierarchy_tree
        path: Current path (used for recursion)

    Yields:
        Tuples of (path_tuple, items_list) for each leaf node
    """
    results = []
    for key, value in tree.items():
        current_path = path + (key,)
        if isinstance(value, list):
            # Leaf node with items
            results.append((current_path, value))
        elif isinstance(value, dict):
            # Branch node - recurse
            results.extend(walk_tree(value, current_path))
    return results


def collapse_single_children(tree: dict) -> dict:
    """Collapse single-child branches for cleaner structure.

    If a node has exactly one child that is also a branch,
    combine them into "parent/child" path.

    Args:
        tree: Nested dict structure

    Returns:
        New tree with single-child branches collapsed
    """
    result = {}

    for key, value in tree.items():
        if isinstance(value, dict):
            # Recursively collapse children first
            collapsed_child = collapse_single_children(value)

            # If this node has exactly one child branch, collapse
            if len(collapsed_child) == 1:
                child_key, child_value = next(iter(collapsed_child.items()))
                if isinstance(child_value, dict):
                    # Combine keys with separator
                    combined_key = f"{key}/{child_key}"
                    result[combined_key] = child_value
                    continue

            result[key] = collapsed_child
        else:
            # Leaf node - keep as-is
            result[key] = value

    return result


def create_view_structure(
    tree: dict,
    base_dir: Path,
    symlink_creator: Callable[[tuple[str, ...], Any, ViewStatistics], None],
    stats: ViewStatistics | None = None
) -> ViewStatistics:
    """Walk tree and create directories + symlinks.

    Args:
        tree: Hierarchy tree from build_hierarchy_tree
        base_dir: Base directory for the view
        symlink_creator: Function called for each leaf item with
                         (path_tuple, item, stats)
        stats: Optional existing stats to update

    Returns:
        ViewStatistics with counts
    """
    if stats is None:
        stats = ViewStatistics()

    for path_tuple, items in walk_tree(tree):
        # Create directory for this path
        dir_path = base_dir.joinpath(*path_tuple)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            stats.dirs_created += 1

        # Create symlinks for items at this leaf
        for item in items:
            symlink_creator(path_tuple, item, stats)

    return stats


def escape_for_path(s: str) -> str:
    """Escape a string for use in file paths.

    Replaces problematic characters with dashes.
    """
    # Replace forward slashes (common in EMA product numbers)
    s = s.replace('/', '-')
    # Replace backslashes
    s = s.replace('\\', '-')
    # Replace colons (problematic on Windows)
    s = s.replace(':', '-')
    # Replace other problematic characters
    for char in ['<', '>', '"', '|', '?', '*']:
        s = s.replace(char, '-')
    # Collapse multiple dashes
    while '--' in s:
        s = s.replace('--', '-')
    return s.strip('-')


def extract_title_from_ema_name(full_name: str) -> str:
    """Extract human-readable title from EMA document name.

    EMA document names often have format:
    "Drug Name : EPAR - Document Type"
    "Drug Name : Document Type - Some qualifier"

    We want just the document type part after the last " - ".

    Args:
        full_name: Full EMA document name

    Returns:
        Cleaned title for use in symlink names
    """
    # Remove file extension if present
    if '.' in full_name:
        name_part = full_name.rsplit('.', 1)[0]
    else:
        name_part = full_name

    # Look for common patterns
    # "Drug : EPAR - Public assessment report" -> "Public assessment report"
    if ' : EPAR - ' in name_part:
        title = name_part.split(' : EPAR - ', 1)[1]
    elif ' : ' in name_part and ' - ' in name_part:
        # "Drug : Some Type - Qualifier" -> last part after " - "
        after_colon = name_part.split(' : ', 1)[1]
        if ' - ' in after_colon:
            title = after_colon.rsplit(' - ', 1)[1]
        else:
            title = after_colon
    elif ' - ' in name_part:
        # Just take the last part after " - "
        title = name_part.rsplit(' - ', 1)[1]
    else:
        title = name_part

    # Clean up the title
    title = title.strip()

    # Remove trailing language codes like "_en"
    for lang_suffix in ['_en', '_de', '_fr', '_es', '_it']:
        if title.lower().endswith(lang_suffix):
            title = title[:-len(lang_suffix)]

    return title.strip()


def format_dated_filename(date: str, title: str, ext: str) -> str:
    """Format a filename with date prefix.

    Args:
        date: Date string in YYYY-MM-DD format
        title: Human-readable title
        ext: File extension (with or without dot)

    Returns:
        Formatted filename like "2024-06-15 Public assessment report.pdf"
    """
    # Ensure extension has dot
    if not ext.startswith('.'):
        ext = '.' + ext

    # Clean up title for use in filename
    title = title.strip()
    # Replace characters that are problematic in filenames
    title = escape_for_path(title)

    return f"{date} {title}{ext}"


if __name__ == "__main__":
    # Test the functions
    print("Testing extract_title_from_ema_name:")
    test_names = [
        "Clopidogrel BMS : EPAR - Public assessment report",
        "Keytruda : EPAR - Scientific discussion",
        "Some Drug : Product information - Annex I",
        "simple-document-name_en.pdf",
    ]
    for name in test_names:
        title = extract_title_from_ema_name(name)
        print(f"  {name!r}")
        print(f"    -> {title!r}")
        print()

    print("Testing format_dated_filename:")
    print(f"  {format_dated_filename('2024-06-15', 'Public assessment report', 'pdf')}")
    print(f"  {format_dated_filename('2023-11-10', 'Scientific discussion', '.pdf')}")

    print("\nTesting escape_for_path:")
    print(f"  'EMEA/H/C/005824' -> '{escape_for_path('EMEA/H/C/005824')}'")
