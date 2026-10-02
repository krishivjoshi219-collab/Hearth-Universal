"""Real web tools: keyless search + page fetch with SSRF guardrails.
No API keys needed. Every outbound host is audited; loopback, metadata
endpoints, and private ranges are hard-blocked (SSRF-proof).
"""
from __future__ import annotations
import html as _html
import ipaddress
import re
import socket
import urllib.parse
import urllib.request

FETCH_TIMEOUT = 15
FETCH_MAX_BYTES = 200_000
SEARCH_TIMEOUT = 15

_BLOCKED_HOSTS = ("localhost", "metadata.google.internal")
_METADATA_NETS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),  # current-network / invalid
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),  # link-local v6
    ipaddress.ip_network("::ffff:0:0/96"),  # v4-mapped v6 (covers ::ffff:127.0.0.1)
)


def _host_allowed(url: str) -> tuple[bool, str]:
    try:
        host = urllib.parse.urlparse(url).hostname or ""
    except Exception:
        return False, "unparseable URL"
    if not host or host.lower() in _BLOCKED_HOSTS:
        return False, f"blocked host '{host}'"
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if any(ip in net for net in _METADATA_NETS):
                return False, f"host '{host}' resolves to private/link-local IP"
    except socket.gaierror:
        return False, f"host '{host}' does not resolve"
    return True, ""


def web_search(query: str, count: int = 5) -> dict:
    """Keyless web search with provider fallback: DDG html, then DDG Instant
    Answer API (rarely rate-limited). Always returns the same result shape."""
    from . import audit as _audit
    q = (query or "")[:300].strip()
    if not q:
        return {"ok": False, "error": "empty query"}
    results, source = _search_ddg_html(q, count)
    if not results:
        results, source = _search_ddg_ia(q, count)
    _audit.append("agent", "web_search", {"q": q, "results": len(results), "source": source})
    return {"ok": True, "query": q, "results": results, "source": source}


def _search_ddg_html(q: str, count: int) -> tuple[list, str]:
    import json as _json
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(q)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Hearth/1.0)"}, method="POST")
        with urllib.request.urlopen(req, timeout=SEARCH_TIMEOUT) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception:
        return [], "ddg-html-error"
    results = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?(?:class="result__snippet"[^>]*>(.*?)</a>)?', page, re.S):
        link, title, snippet = m.group(1), m.group(2), m.group(3) or ""
        title = re.sub(r"<[^>]+>", "", title).strip()
        title = _html.unescape(title)[:200]
        snippet = re.sub(r"<[^>]+>", "", snippet).strip()
        snippet = _html.unescape(snippet)[:400]
        # DDG wraps links in /l/?uddg=<real>
        if "uddg=" in link:
            link = urllib.parse.unquote_plus(link.split("uddg=", 1)[1].split("&")[0])
        # Drop ad/tracking redirects — never present sponsored links as results.
        if any(t in link for t in ("/y.js?", "ad_domain=", "ad_provider=", "doubleclick.net")):
            continue
        if link.startswith("http"):
            results.append({"title": title, "url": link[:500], "snippet": snippet})
        if len(results) >= max(1, min(count, 10)):
            break
    return results, "ddg-html"


def _search_ddg_ia(q: str, count: int) -> tuple[list, str]:
    """Fallback: official Instant Answer API (abstract + related topics)."""
    import json as _json
    url = ("https://api.duckduckgo.com/?q=" + urllib.parse.quote_plus(q)
           + "&format=json&no_html=1&skip_disambig=1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Hearth/1.0)"})
        with urllib.request.urlopen(req, timeout=SEARCH_TIMEOUT) as r:
            data = _json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return [], "ddg-ia-error"
    results = []
    if data.get("AbstractURL", "").startswith("http") and data.get("AbstractText"):
        results.append({"title": (data.get("Heading") or q)[:200],
                        "url": data["AbstractURL"][:500],
                        "snippet": data["AbstractText"][:400]})
    for t in data.get("RelatedTopics", []):
        if isinstance(t, dict) and str(t.get("FirstURL", "")).startswith("http"):
            results.append({"title": str(t.get("Text", ""))[:200].split(" - ")[0] or t["FirstURL"],
                            "url": t["FirstURL"][:500],
                            "snippet": str(t.get("Text", ""))[:400]})
        if len(results) >= max(1, min(count, 10)):
            break
    return results, "ddg-instant-answer"


_TAG_RE = re.compile(r"<(script|style|nav|footer|header|aside|noscript)[^>]*>.*?</\1>", re.S | re.I)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """SSRF-safe: never auto-follow redirects; caller must re-validate."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def web_fetch(url: str) -> dict:
    """Fetch a page and return readable text (scripts/styles stripped, capped)."""
    from . import audit as _audit
    url = (url or "")[:1000].strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "only http(s) URLs"}
    ok, reason = _host_allowed(url)
    if not ok:
        _audit.append("sentinel", "egress_blocked", {"url": url, "reason": reason})
        return {"ok": False, "error": f"blocked: {reason}"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Hearth/1.0)"}, method="GET")
        # Do NOT follow redirects automatically: validate each hop against SSRF policy.
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(req, timeout=FETCH_TIMEOUT) as r:
            status = getattr(r, "status", 200) or 200
            if status in (301, 302, 303, 307, 308):
                loc = r.headers.get("Location", "")
                nxt = urllib.parse.urljoin(url, loc)
                ok2, reason2 = _host_allowed(nxt)
                if not ok2:
                    _audit.append("sentinel", "egress_blocked", {"url": nxt, "reason": f"redirect: {reason2}"})
                    return {"ok": False, "error": f"blocked redirect: {reason2}"}
                return {"ok": False, "error": "redirects require explicit follow (blocked for SSRF safety)"}
            raw = r.read(FETCH_MAX_BYTES + 1)
            final_url = r.geturl()
    except Exception as e:
        _audit.append("agent", "web_fetch", {"url": url, "error": type(e).__name__})
        return {"ok": False, "error": f"fetch failed: {type(e).__name__}"}
    if len(raw) > FETCH_MAX_BYTES:
        raw = raw[:FETCH_MAX_BYTES]
    try:
        text = raw.decode("utf-8", "replace")
    except Exception:
        return {"ok": False, "error": "undecodable content"}
    if "<html" in text[:2000].lower() or "<body" in text[:4000].lower():
        text = _TAG_RE.sub(" ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = _html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()[:12000]
    _audit.append("agent", "web_fetch", {"url": url, "final": final_url, "chars": len(text)})
    return {"ok": True, "url": final_url, "text": text}
