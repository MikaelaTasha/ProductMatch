"""Conservative title normalization; never replace the original listing text."""

NORMALIZATION_VERSION = 'lowercase-whitespace-v1'


def normalize_title(title: str | None) -> str | None:
    """Lowercase letters and collapse whitespace, retaining other characters.

    None remains missing; an empty or whitespace-only title becomes ''.
    This does not extract attributes, convert units, or determine a match.
    """
    if title is None:
        return None
    if not isinstance(title, str):
        raise TypeError('title must be a string or None')
    return ' '.join(title.lower().split())
