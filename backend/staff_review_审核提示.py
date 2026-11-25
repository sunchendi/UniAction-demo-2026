"""Advisory flags for a school's pending notice review queue."""

from collections import defaultdict
from unicodedata import normalize
from urllib.parse import urlsplit, urlunsplit


def source_key(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.hostname.endswith(".invalid"):
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))
    except ValueError:
        return None


def needs_eligibility_evidence(rule):
    return rule.op == "needs_staff_review" or any(needs_eligibility_evidence(child) for child in rule.children)


def review_checks(notices):
    """Compare latest notices on separate IDs within the supplied school."""
    index = defaultdict(list)
    keys_by_id = {}
    peers = {notice.id: notice for notice in notices if notice.publication_status != "archived"}
    for notice in peers.values():
        keys = [("same_source", notice.source_hash)]
        if source := source_key(notice.source_url):
            keys.append(("same_link", source))
        titles = {
            "".join(char for char in normalize("NFKC", title).casefold() if char.isalnum())
            for title in (notice.title.ko, notice.title.zh)
        }
        keys.extend(("same_title", title) for title in sorted(titles) if title)
        keys_by_id[notice.id] = keys
        for key in keys:
            index[key].append(notice.id)

    checks = {}
    for notice in peers.values():
        if notice.publication_status not in {"draft", "under_review"}:
            continue
        reasons = defaultdict(set)
        for key in keys_by_id[notice.id]:
            for peer_id in index[key]:
                if peer_id != notice.id:
                    reasons[peer_id].add(key[0])
        ranked = sorted(reasons, key=lambda peer: ("same_source" not in reasons[peer], "same_link" not in reasons[peer], peer))
        checks[notice.id] = {
            "missing_deadline": not (notice.official_deadline or notice.application_window.closes_at),
            "missing_evidence": needs_eligibility_evidence(notice.eligibility_rules),
            "duplicates": [
                {"id": peer, "title": peers[peer].title.model_dump(), "reasons": sorted(reasons[peer])}
                for peer in ranked[:5]
            ],
        }
    return checks
