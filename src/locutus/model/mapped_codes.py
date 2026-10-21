"""Harmonize mapped codes to term-wyrm's preferred CURIEs and systems.

Only mapped (public ontology) codes are harmonized; the codes in a user's own
data dictionary are theirs to name. Mappings coming in (REST, sideload) are
strict, so bad codes are rejected before anything is saved. Exports are
lenient: older mappings that can't be matched still go out, with a warning.
"""

import logging
from collections.abc import Callable, Iterable

from term_wyrm import CodingError, default_vocabularies

from locutus.model.exceptions import UnrecognizedMappingCode

logger = logging.getLogger(__name__)


def harmonize_mapping(mapping: dict) -> dict:
    """A copy of ``mapping`` with its code and system harmonized.

    Raises CodingError if they don't identify a known vocabulary.
    """
    coding = default_vocabularies().harmonize_coding(
        mapping.get("code") or "", mapping.get("system")
    )
    return {**mapping, "code": coding.code, "system": coding.system}


def harmonize_mappings(
    mappings: Iterable[dict],
    describe: Callable[[int, dict], str] = lambda i, _: f"mapping {i}",
) -> list[dict]:
    """Harmonize every mapping, or raise UnrecognizedMappingCode listing all
    that failed. ``describe`` names a mapping (by index) in the error."""
    harmonized, problems = [], []
    for i, mapping in enumerate(mappings):
        try:
            harmonized.append(harmonize_mapping(mapping))
        except CodingError as e:
            problems.append(f"{describe(i, mapping)}: {e}")
    if problems:
        raise UnrecognizedMappingCode(problems)
    return harmonized


def harmonize_for_export(code: str, system: str) -> tuple[str, str]:
    """The harmonized code and system, or the originals (with a warning) when
    they can't be matched."""
    try:
        coding = default_vocabularies().harmonize_coding(code, system, strict=False)
    except CodingError as e:
        logger.warning("Exporting mapping as stored; it can't be harmonized: %s", e)
        return code, system
    return coding.code, coding.system
