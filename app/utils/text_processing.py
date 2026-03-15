"""Text processing utilities — cleaning, chunking, normalization."""

import html
import re


def clean_text(text: str) -> str:
    """Clean raw text from Reddit or other sources."""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove image/media markdown (must run before link stripping)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
    # Strip markdown links but keep the text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Collapse multiple whitespace/newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def prepare_embedding_text(title: str, body: str) -> str:
    """Combine title and body into one string for embedding."""
    cleaned_title = clean_text(title)
    cleaned_body = clean_text(body)
    combined = f"{cleaned_title}. {cleaned_body}" if cleaned_body else cleaned_title
    # Truncate to ~8000 chars (roughly 2000 tokens for the embedding model)
    return combined[:8000]
