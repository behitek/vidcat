import os
import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

_UNSAFE_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_WIN_NAMES = {"CON", "PRN", "AUX", "NUL",
                        *(f"COM{i}" for i in range(1, 10)),
                        *(f"LPT{i}" for i in range(1, 10))}

# A "group code" token like "AMBER01" or "BLAZE02" - two-or-more letters
# followed by digits. Requiring 2+ letters avoids misreading incidental
# tokens such as version tags ("v2") as a group code.
_CODE_TOKEN_RE = re.compile(r'^[A-Za-z]{2,}[0-9]+$')


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
    """Parse a filename into (order, suffix, matched).

    Strips the extension and splits the stem on every underscore, then looks
    for a "group code" token (e.g. "AMBER01") by scanning the segments from
    the end - this recognizes the same code regardless of what prefix comes
    before it, e.g. "1_output_AMBER01", "output_AMBER01", "01_AMBER01" and
    plain "AMBER01" all resolve to suffix "AMBER01". A leading run of digits
    (when present) is used as the order for within-group sorting.

    If no segment looks like a group code, falls back to the legacy
    "<order>_<suffix>" convention: if the first part is a non-empty run of
    digits and the second part is non-empty, uses (int(first_part),
    second_part) - any further underscore-separated segments are ignored.

    If neither rule matches, returns (None, whole_stem, False) - the caller
    treats unmatched filenames as singleton groups.
    """
    stem, _ext = os.path.splitext(os.path.basename(filename))
    parts = stem.split('_')

    for token in reversed(parts):
        if _CODE_TOKEN_RE.match(token):
            order = int(parts[0]) if parts[0].isdigit() else None
            return order, token, True

    if len(parts) >= 2 and parts[0].isdigit() and parts[1]:
        return int(parts[0]), parts[1], True

    return None, stem, False


def group_videos_by_suffix(video_paths: Sequence[str]):
    """Group videos by filename suffix, ordered by first appearance.

    See `parse_order_suffix` for how the grouping suffix is extracted.
    Videos whose filename matches neither the group-code pattern nor the
    legacy `<order>_<suffix>` convention become their own singleton group
    (keyed by original index, so they never merge with each other even if
    their stems happen to collide). Within a matched group, items are sorted
    by (order, index) ascending, so drag-drop reordering in the UI doesn't
    change concatenation order within a group.
    """
    buckets = {}
    order_keys = []
    for idx, path in enumerate(video_paths):
        order, suffix, matched = parse_order_suffix(path)
        key = ('suffix', suffix) if matched else ('unmatched', idx)
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
