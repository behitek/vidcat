import os
import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

_ORDER_SUFFIX_RE = re.compile(r'^(\d+)_(.+)$')
_UNSAFE_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_WIN_NAMES = {"CON", "PRN", "AUX", "NUL",
                        *(f"COM{i}" for i in range(1, 10)),
                        *(f"LPT{i}" for i in range(1, 10))}


@dataclass
class VideoItem:
    index: int
    path: str
    order: Optional[int]


@dataclass
class VideoGroup:
    suffix: str
    items: list = field(default_factory=list)

    @property
    def paths(self):
        return [it.path for it in self.items]


def parse_order_suffix(filename):
    """Parse a filename into (order, suffix).

    Strips the extension and splits the stem at the first underscore. If the
    text before that underscore is a non-empty run of digits, returns
    (int(order), remainder). Otherwise returns (None, whole_stem).
    """
    stem, _ext = os.path.splitext(os.path.basename(filename))
    match = _ORDER_SUFFIX_RE.match(stem)
    if match:
        return int(match.group(1)), match.group(2)
    return None, stem


def group_videos_by_suffix(video_paths: Sequence[str]):
    """Group videos by filename suffix, ordered by first appearance.

    Videos whose filename doesn't match `<order>_<suffix>` become their own
    singleton group (keyed by original index, so they never merge with each
    other even if their stems happen to collide). Within a matched group,
    items are sorted by (order, index) ascending, so drag-drop reordering in
    the UI doesn't change concatenation order within a group.
    """
    buckets = {}
    order_keys = []
    for idx, path in enumerate(video_paths):
        order, suffix = parse_order_suffix(path)
        key = ('suffix', suffix) if order is not None else ('unmatched', idx)
        if key not in buckets:
            buckets[key] = VideoGroup(suffix=suffix, items=[])
            order_keys.append(key)
        buckets[key].items.append(VideoItem(index=idx, path=path, order=order))

    groups = [buckets[key] for key in order_keys]
    for group in groups:
        group.items.sort(key=lambda it: (it.order if it.order is not None else 0, it.index))
    return groups


def assign_group_indices(video_paths: Sequence[str]):
    """Return [(group_idx, suffix), ...] aligned 1:1 with video_paths by original index."""
    groups = group_videos_by_suffix(video_paths)
    result = [None] * len(video_paths)
    for group_idx, group in enumerate(groups):
        for item in group.items:
            result[item.index] = (group_idx, group.suffix)
    return result


def sanitize_suffix(suffix: str) -> str:
    """Make a suffix safe to embed in an output filename."""
    cleaned = _UNSAFE_CHARS_RE.sub('_', suffix).strip(' .')
    if not cleaned:
        cleaned = "video"
    if cleaned.upper() in _RESERVED_WIN_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned[:100]


def dedupe_suffixes(suffixes: Sequence[str]):
    """Disambiguate a list of sanitized suffixes by appending _2, _3, ... to duplicates."""
    seen = {}
    result = []
    for suffix in suffixes:
        seen[suffix] = seen.get(suffix, 0) + 1
        result.append(suffix if seen[suffix] == 1 else f"{suffix}_{seen[suffix]}")
    return result
