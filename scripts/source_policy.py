"""What may be cited. Owner, 2026-09-25: "please dont reference wikipedia. If the data is not
peer-reviewed, dont include it", and "If a wikipedia value can be traced to a paper, then cite
the paper". A wiki is never a source: a value it gives is cited to the paper behind it, or not
shown. Used by the apply steps (a wiki is never recorded) and by the export (a wiki that is on
record anyway is never published).
"""

from __future__ import annotations

import re

# Wikipedia and its mirrors, and any page served from a wiki (/wiki/ in the path, raw wikitext).
# A file that merely sits on a wiki host (a vendor PDF on static.igem.wiki) is judged as the
# document it is, not as a wiki page.
_WIKI = re.compile(r"wikipedia\.org|wikimedia\.org|wikiwand\.com|fandom\.com|/wiki/|(?<![a-z])(?:wikitext|wikipedia|wiki page)(?![a-z])", re.I)


def is_wiki(*texts: object) -> bool:
    """True when any of a document's url, path or title shows it is a wiki page."""
    return any(_WIKI.search(str(t)) for t in texts if t)


def is_wiki_document(d: dict) -> bool:
    return is_wiki(d.get("url"), d.get("local_path"), d.get("title"), d.get("reference_text"))


def strip_wiki_links(text: str | None) -> str | None:
    """A list of links ("a; b; c") without its wiki pages; None when nothing is left."""
    if not text or not is_wiki(text):
        return text
    parts = [p.strip() for p in re.split(r";\s*", text) if p.strip()]
    kept = [p for p in parts if not is_wiki(p)]
    return "; ".join(kept) if kept else None


# The Moon line (owner, 2026-09-25): peer-reviewed papers, the flying agency's own primary
# records (mission and technical reports, the Lunar Sample Compendium, the NSSDCA catalogue,
# LROC coordinate tables) and the Lunar Sourcebook. Web articles, educational pages and
# compilations of other people's data (PSRD, NASA education pages, Gasteiner's CSV, ALSJ) are not.
MOON_ACCEPTED_KINDS = ("paper", "primary_report", "catalogue", "compendium")


def is_accepted_moon_document(d: dict) -> bool:
    return not is_wiki_document(d) and (d.get("kind") or "") in MOON_ACCEPTED_KINDS
