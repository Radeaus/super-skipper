"""Compare what a media player plays with the keywords of a rule."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.media_player import (
    ATTR_MEDIA_ALBUM_NAME,
    ATTR_MEDIA_ARTIST,
    ATTR_MEDIA_CHANNEL,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_TITLE,
)

from .const import (
    CONF_IGNORE_TEXTS,
    CONF_KEYWORDS,
    CONF_MATCH_FIELDS,
    CONF_MATCH_MODE,
    DEFAULT_MATCH_FIELDS,
    MatchField,
    MatchMode,
)

FIELD_ATTRIBUTES = {
    MatchField.TITLE: ATTR_MEDIA_TITLE,
    MatchField.ARTIST: ATTR_MEDIA_ARTIST,
    MatchField.ALBUM: ATTR_MEDIA_ALBUM_NAME,
    MatchField.CHANNEL: ATTR_MEDIA_CHANNEL,
}

# The attributes that tell one track from the next.
KEY_ATTRIBUTES = (
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_ARTIST,
    ATTR_MEDIA_ALBUM_NAME,
    ATTR_MEDIA_CHANNEL,
    ATTR_MEDIA_CONTENT_ID,
)

type MatchKey = tuple[str | None, ...]


def normalize(text: str) -> str:
    """Lowercase, drop accents and collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return " ".join(stripped.casefold().split())


def match_key(attributes: Mapping[str, Any]) -> MatchKey:
    """Return what identifies the current track."""
    return tuple(
        str(value) if (value := attributes.get(attribute)) is not None else None
        for attribute in KEY_ATTRIBUTES
    )


def compile_keywords(keywords: list[str], mode: MatchMode) -> re.Pattern[str]:
    """Build one pattern for all keywords; raises re.error for a bad regex."""
    parts = []
    for keyword in keywords:
        if mode is MatchMode.REGEX:
            parts.append(f"(?:{keyword})")
            continue
        escaped = re.escape(normalize(keyword))
        if mode is MatchMode.WHOLE_WORD:
            escaped = rf"(?<!\w){escaped}(?!\w)"
        parts.append(escaped)
    pattern = "|".join(parts) if parts else r"(?!)"
    return re.compile(pattern, re.IGNORECASE)


@dataclass(frozen=True)
class Matcher:
    """The compiled keywords of one rule."""

    pattern: re.Pattern[str]
    fields: tuple[MatchField, ...]
    ignore_texts: tuple[str, ...]

    @classmethod
    def from_config(cls, data: Mapping[str, Any]) -> Matcher:
        """Build the matcher from the data of a rule."""
        mode = MatchMode(data.get(CONF_MATCH_MODE, MatchMode.WHOLE_WORD))
        fields = tuple(
            MatchField(field)
            for field in data.get(CONF_MATCH_FIELDS, DEFAULT_MATCH_FIELDS)
        )
        return cls(
            pattern=compile_keywords(list(data.get(CONF_KEYWORDS, [])), mode),
            fields=fields,
            ignore_texts=tuple(
                normalized
                for text in data.get(CONF_IGNORE_TEXTS, [])
                if (normalized := normalize(text))
            ),
        )

    def text_of(self, attributes: Mapping[str, Any]) -> str:
        """Join the searched fields of a state into one normalized string."""
        values = []
        for field in self.fields:
            value = attributes.get(FIELD_ATTRIBUTES[field])
            if value:
                values.append(str(value))
        return normalize(" - ".join(values))

    def matches(self, text: str) -> bool:
        """Return whether a keyword occurs in the text."""
        return bool(text) and self.pattern.search(text) is not None

    def is_ignored(self, text: str) -> bool:
        """Return whether the text is station information, not a track."""
        return any(ignored in text for ignored in self.ignore_texts)


def describe(attributes: Mapping[str, Any]) -> str:
    """A short human readable description of what plays."""
    title = attributes.get(ATTR_MEDIA_TITLE)
    artist = attributes.get(ATTR_MEDIA_ARTIST)
    if title and artist:
        return f"{artist} – {title}"
    return str(title or artist or attributes.get(ATTR_MEDIA_CHANNEL) or "")
