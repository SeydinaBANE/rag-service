from __future__ import annotations


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping, fixed-size character windows.

    Pure and deterministic. Whitespace-only windows are dropped so a trailing
    sliver of padding never becomes a chunk.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]
    step = max(size - overlap, 1)
    windows = (cleaned[start : start + size] for start in range(0, len(cleaned), step))
    return [window for window in windows if window.strip()]
