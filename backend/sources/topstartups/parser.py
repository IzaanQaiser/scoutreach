import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlsplit

from backend.sources.topstartups.exceptions import TopStartupsParseError
from backend.sources.topstartups.types import TopStartupsCompany, TopStartupsStage


_WHITESPACE = re.compile(r"\s+")
_STAGE = re.compile(
    r"\bpre[-\s]?seed\b|\bpost[-\s]?ipo\b|\bseries\s+([a-g])\b|\bseed\b",
    re.IGNORECASE,
)
_LOCATION = re.compile(r"(?:📍\s*)?HQ:\s*(.+)", re.IGNORECASE)


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list["_Node | str"] = field(default_factory=list)


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self._stack = [self.root]

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        node = _Node(tag, {name: value or "" for name, value in attrs})
        self._stack[-1].children.append(node)
        if tag not in {"br", "img", "hr", "input", "meta", "link"}:
            self._stack.append(node)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        if self._stack[-1].tag == tag:
            self._stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def parse_companies_page(
    html: str,
    *,
    source_url: str,
) -> tuple[list[TopStartupsCompany], bool]:
    parser = _TreeParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        raise TopStartupsParseError("TopStartups returned malformed HTML") from None

    cards = [
        node
        for node in _walk(parser.root)
        if _has_class(node, "infinite-item")
        and _first(
            node,
            lambda candidate: candidate.attrs.get("id") == "item-card-filter",
        )
        is not None
    ]
    if not cards and _first(
        parser.root,
        lambda node: node.attrs.get("id")
        in {"item-card-filter", "startup-website-link"},
    ):
        raise TopStartupsParseError(
            "TopStartups startup-card layout is unsupported"
        )
    companies = [_parse_card(card, source_url) for card in cards]
    return companies, _has_enabled_next_page(parser.root)


def _parse_card(card: _Node, source_url: str) -> TopStartupsCompany:
    name_heading = _first(card, lambda node: node.tag == "h3")
    website_link = _parent(card, name_heading) if name_heading is not None else None
    if website_link is None or website_link.tag != "a":
        raise TopStartupsParseError(
            "TopStartups startup card is missing its name/site structure"
        )
    name = _clean_text(_text(name_heading))
    website = website_link.attrs.get("href", "").strip()
    domain = _domain(website)
    if not name or not website or domain is None:
        raise TopStartupsParseError(
            "TopStartups startup card is missing its name/site structure"
        )

    categories = [
        _clean_text(_text(node))
        for node in _walk(card)
        if node.attrs.get("id") == "industry-tags" and _clean_text(_text(node))
    ]
    description = _section_text(card, "What they do:", stop_id="industry-tags")
    quick_facts = _section_text(card, "Quick facts:")
    funding_text = _section_text(card, "Funding:")

    location = None
    if quick_facts:
        match = _LOCATION.search(quick_facts)
        if match:
            location = _clean_text(
                re.split(
                    r"\s+(?:Founded:|\d[\d,\-–—]*\s+employees?)\b",
                    match.group(1),
                )[0]
            ) or None

    return TopStartupsCompany(
        name=name,
        website=website,
        domain=domain,
        description=description,
        categories=categories,
        location=location,
        stage=_stage(funding_text),
        funding_text=funding_text,
        source_url=source_url,
    )


def _section_text(
    card: _Node,
    label: str,
    *,
    stop_id: str | None = None,
) -> str | None:
    header = _first(
        card,
        lambda node: node.attrs.get("id") == "card-header"
        and _clean_text(_text(node)).casefold() == label.casefold(),
    )
    if header is None:
        return None
    parent = _parent(card, header)
    if parent is None:
        return None

    chunks: list[str] = []
    started = False
    for child in parent.children:
        if child is header:
            started = True
            continue
        if not started:
            continue
        if isinstance(child, _Node) and stop_id and _contains_id(child, stop_id):
            break
        chunks.append(_text(child) if isinstance(child, _Node) else child)
    value = _clean_text(" ".join(chunks))
    return value or None


def _stage(funding_text: str | None) -> TopStartupsStage | None:
    if not funding_text:
        return None
    match = _STAGE.search(funding_text)
    if match is None:
        return None
    value = match.group(0).casefold().replace(" ", "-")
    if value.startswith("pre-"):
        return "Pre-Seed"
    if value.startswith("post-"):
        return "Post-IPO"
    if match.group(1):
        return f"Series {match.group(1).upper()}"  # type: ignore[return-value]
    return "Seed"


def _domain(website: str) -> str | None:
    candidate = website if "://" in website else f"https://{website}"
    hostname = urlsplit(candidate).hostname
    if hostname is None:
        return None
    hostname = hostname.lower().rstrip(".")
    return hostname[4:] if hostname.startswith("www.") else hostname


def _has_enabled_next_page(root: _Node) -> bool:
    link = _first(root, lambda node: _has_class(node, "infinite-more-link"))
    if link is None or not link.attrs.get("href"):
        return False
    return not (
        _has_class(link, "disabled")
        or link.attrs.get("aria-disabled", "").casefold() == "true"
        or "disabled" in link.attrs
    )


def _walk(node: _Node):
    for child in node.children:
        if isinstance(child, _Node):
            yield child
            yield from _walk(child)


def _first(node: _Node, predicate):
    return next((candidate for candidate in _walk(node) if predicate(candidate)), None)


def _parent(root: _Node, target: _Node) -> _Node | None:
    for node in [root, *_walk(root)]:
        if target in node.children:
            return node
    return None


def _text(value: _Node | str) -> str:
    if isinstance(value, str):
        return value
    separator = "\n" if value.tag == "br" else " "
    return separator.join(_text(child) for child in value.children)


def _clean_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def _has_class(node: _Node, class_name: str) -> bool:
    return class_name in node.attrs.get("class", "").split()


def _contains_id(node: _Node, element_id: str) -> bool:
    return node.attrs.get("id") == element_id or any(
        candidate.attrs.get("id") == element_id for candidate in _walk(node)
    )
