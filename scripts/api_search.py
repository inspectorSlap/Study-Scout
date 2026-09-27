#!/usr/bin/env python3
"""Run one released StudyScout query against one scholarly API with auditable pagination."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from release_guard import require_release
from rig_common import CONTROL, DATA, append_rows, read_csv


QUERIES = DATA / "searches" / "queries.csv"
LEDGER = DATA / "searches" / "retrieval-ledger.csv"
RAW = DATA / "searches" / "raw"
RESULTS = DATA / "searches" / "results"
LEDGER_FIELDS = [
    "execution_id", "query_id", "stage", "source_id", "source_name", "access_method",
    "parameters_json", "filters", "run_started_at", "run_completed_at", "requested_page_size",
    "pagination_start", "pagination_end", "pages_retrieved", "result_count", "results_available",
    "serious_candidate_count", "api_failure", "api_truncated", "terminal_condition", "status",
    "raw_response_paths", "normalized_result_paths", "notes",
]
RESULT_FIELDS = ["source_position", "title", "authors", "year", "venue", "url", "doi", "arxiv_id", "external_id", "peer_reviewed_hint", "raw_record_path"]
USER_AGENT = "StudyScout/0.1"


@dataclass(frozen=True)
class Page:
    rows: list[dict[str, str]]
    total: int | None
    next_token: str | None
    exhausted: bool
    capped: bool = False


@dataclass(frozen=True)
class Source:
    source_id: str
    name: str
    endpoint: str
    extension: str
    initial_token: str
    build_url: Callable[[str, int, str, str | None], str]
    parse: Callable[[bytes, str, int, int], Page]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean(value: object) -> str:
    return "" if value is None else " ".join(str(value).split())


def first(value: object) -> str:
    return clean(value[0]) if isinstance(value, list) and value else clean(value)


def position(rows: list[dict[str, str]], raw_path: str, offset: int) -> list[dict[str, str]]:
    for number, row in enumerate(rows, start=offset + 1):
        row["source_position"] = str(number)
        row["raw_record_path"] = raw_path
    return rows


def openalex_url(query: str, size: int, token: str, email: str | None) -> str:
    parameters = {"search": query, "per-page": size, "cursor": token, "select": "id,doi,title,publication_year,primary_location,authorships,type"}
    if email:
        parameters["mailto"] = email
    return "https://api.openalex.org/works?" + urllib.parse.urlencode(parameters)


def parse_openalex(payload: bytes, raw_path: str, size: int, offset: int) -> Page:
    data = json.loads(payload)
    rows = []
    for work in data.get("results", []):
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        doi = re.sub(r"^https?://doi\.org/", "", clean(work.get("doi")), flags=re.I)
        url = clean(location.get("landing_page_url") or work.get("doi") or work.get("id"))
        arxiv = ""
        match = re.fullmatch(r"10\.48550/arxiv\.(.+)", doi, flags=re.I) or re.search(r"arxiv\.org/(?:abs|pdf)/([^?#/]+)", url, flags=re.I)
        if match:
            arxiv = re.sub(r"v\d+$", "", match.group(1).removesuffix(".pdf"), flags=re.I)
        rows.append({
            "title": clean(work.get("title")),
            "authors": "; ".join(clean((item.get("author") or {}).get("display_name")) for item in work.get("authorships", []) if (item.get("author") or {}).get("display_name")),
            "year": clean(work.get("publication_year")), "venue": clean(source.get("display_name")),
            "url": url, "doi": doi, "arxiv_id": arxiv, "external_id": clean(work.get("id")), "peer_reviewed_hint": "UNKNOWN",
        })
    meta = data.get("meta") or {}
    token = clean(meta.get("next_cursor")) or None
    return Page(position(rows, raw_path, offset), meta.get("count"), token, len(rows) < size or not token)


def crossref_url(query: str, size: int, token: str, email: str | None) -> str:
    parameters = {"query.bibliographic": query, "rows": size, "cursor": token, "select": "DOI,title,author,published,container-title,URL,type"}
    if email:
        parameters["mailto"] = email
    return "https://api.crossref.org/works?" + urllib.parse.urlencode(parameters)


def parse_crossref(payload: bytes, raw_path: str, size: int, offset: int) -> Page:
    message = json.loads(payload).get("message") or {}
    rows = []
    for item in message.get("items", []):
        authors = [clean(" ".join(filter(None, (author.get("given", ""), author.get("family", ""))))) for author in item.get("author", [])]
        parts = ((item.get("published") or {}).get("date-parts") or [[]])[0]
        rows.append({
            "title": first(item.get("title")), "authors": "; ".join(filter(None, authors)), "year": clean(parts[0] if parts else ""),
            "venue": first(item.get("container-title")), "url": clean(item.get("URL")), "doi": clean(item.get("DOI")).lower(),
            "arxiv_id": "", "external_id": clean(item.get("DOI")).lower(), "peer_reviewed_hint": "UNKNOWN",
        })
    token = clean(message.get("next-cursor")) or None
    return Page(position(rows, raw_path, offset), message.get("total-results"), token, len(rows) < size or not token)


def semantic_url(query: str, size: int, token: str, email: str | None) -> str:
    del email
    parameters = {"query": query, "limit": size, "offset": token, "fields": "paperId,title,authors,year,venue,url,externalIds,publicationTypes,openAccessPdf"}
    return "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(parameters)


def parse_semantic(payload: bytes, raw_path: str, size: int, offset: int) -> Page:
    data = json.loads(payload)
    rows = []
    for item in data.get("data", []):
        external = item.get("externalIds") or {}
        kinds = item.get("publicationTypes") or []
        rows.append({
            "title": clean(item.get("title")), "authors": "; ".join(clean(author.get("name")) for author in item.get("authors", []) if author.get("name")),
            "year": clean(item.get("year")), "venue": clean(item.get("venue")), "url": clean(item.get("url") or (item.get("openAccessPdf") or {}).get("url")),
            "doi": clean(external.get("DOI")).lower(), "arxiv_id": clean(external.get("ArXiv")), "external_id": clean(item.get("paperId")),
            "peer_reviewed_hint": "UNKNOWN",
        })
    next_value = data.get("next")
    token = str(next_value) if next_value is not None else None
    return Page(position(rows, raw_path, offset), data.get("total"), token, len(rows) < size or not token, bool(token and int(token) >= 1000))


def arxiv_url(query: str, size: int, token: str, email: str | None) -> str:
    del email
    translated = " AND ".join(f"all:{term}" for term in re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", query))
    return "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": translated, "start": token, "max_results": size, "sortBy": "relevance", "sortOrder": "descending"})


def parse_arxiv(payload: bytes, raw_path: str, size: int, offset: int) -> Page:
    root = ET.fromstring(payload)
    namespaces = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
    rows = []
    for entry in root.findall("a:entry", namespaces):
        url = clean(entry.findtext("a:id", default="", namespaces=namespaces))
        arxiv = re.sub(r"v\d+$", "", url.rstrip("/").rsplit("/", 1)[-1])
        published = clean(entry.findtext("a:published", default="", namespaces=namespaces))
        rows.append({
            "title": clean(entry.findtext("a:title", default="", namespaces=namespaces)),
            "authors": "; ".join(clean(author.findtext("a:name", default="", namespaces=namespaces)) for author in entry.findall("a:author", namespaces)),
            "year": published[:4], "venue": "arXiv", "url": url,
            "doi": clean(entry.findtext("{http://arxiv.org/schemas/atom}doi", default="")), "arxiv_id": arxiv,
            "external_id": arxiv, "peer_reviewed_hint": "FALSE",
        })
    total_text = root.findtext("o:totalResults", default="", namespaces=namespaces)
    total = int(total_text) if total_text.isdigit() else None
    next_offset = offset + len(rows)
    exhausted = len(rows) < size or (total is not None and next_offset >= total)
    return Page(position(rows, raw_path, offset), total, None if exhausted else str(next_offset), exhausted)


def dblp_url(query: str, size: int, token: str, email: str | None) -> str:
    del email
    return "https://dblp.org/search/publ/api?" + urllib.parse.urlencode({"q": query, "h": size, "f": token, "format": "json"})


def parse_dblp(payload: bytes, raw_path: str, size: int, offset: int) -> Page:
    container = ((json.loads(payload).get("result") or {}).get("hits") or {})
    hits = container.get("hit") or []
    if isinstance(hits, dict):
        hits = [hits]
    rows = []
    for hit in hits:
        info = hit.get("info") or {}
        authors = (info.get("authors") or {}).get("author", [])
        if isinstance(authors, (str, dict)):
            authors = [authors]
        names = [clean(author.get("text")) if isinstance(author, dict) else clean(author) for author in authors]
        rows.append({
            "title": clean(info.get("title")), "authors": "; ".join(filter(None, names)), "year": clean(info.get("year")),
            "venue": clean(info.get("venue")), "url": clean(info.get("ee") or info.get("url")), "doi": clean(info.get("doi")).lower(),
            "arxiv_id": "", "external_id": clean(info.get("key")), "peer_reviewed_hint": "UNKNOWN",
        })
    total_text = clean(container.get("@total"))
    total = int(total_text) if total_text.isdigit() else None
    next_offset = offset + len(rows)
    exhausted = len(rows) < size or (total is not None and next_offset >= total)
    return Page(position(rows, raw_path, offset), total, None if exhausted else str(next_offset), exhausted)


SOURCES = {
    "openalex": Source("S-01", "OpenAlex", "api.openalex.org", "json", "*", openalex_url, parse_openalex),
    "crossref": Source("S-02", "Crossref", "api.crossref.org", "json", "*", crossref_url, parse_crossref),
    "semantic-scholar": Source("S-03", "Semantic Scholar Graph", "api.semanticscholar.org", "json", "0", semantic_url, parse_semantic),
    "arxiv": Source("S-04", "arXiv", "export.arxiv.org", "xml", "0", arxiv_url, parse_arxiv),
    "dblp": Source("S-05", "DBLP", "dblp.org", "json", "0", dblp_url, parse_dblp),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--source", choices=sorted(SOURCES))
    parser.add_argument("--query-id")
    parser.add_argument("--execution-id")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--filters", default="", help="Annotation only; does not filter provider results")
    args = parser.parse_args()

    if args.list_sources:
        for key, source in SOURCES.items():
            print(f"{key}\t{source.source_id}\t{source.name}\t{source.endpoint}")
        return 0
    if not args.source or not args.query_id or not args.execution_id:
        parser.error("--source, --query-id, and --execution-id are required")
    if not re.fullmatch(r"R-S[12]-\d{6}", args.execution_id):
        parser.error("invalid StudyScout execution ID")
    if not 1 <= args.page_size <= 100 or not 1 <= args.max_pages <= 100:
        parser.error("page size and page count must be in 1..100")

    queries = {row["query_id"]: row for row in read_csv(QUERIES)}
    if args.query_id not in queries:
        parser.error(f"register the query first: {args.query_id}")
    if args.execution_id in {row["execution_id"] for row in read_csv(LEDGER)}:
        parser.error(f"execution ID already exists: {args.execution_id}")
    query = queries[args.query_id]
    expected = "1" if query["stage"] == "STAGE_1_COLD" else "2"
    if not args.execution_id.startswith(f"R-S{expected}-"):
        parser.error("execution/query stage mismatch")

    require_release()
    from validate_records import validate
    errors = validate()
    if errors:
        parser.error("invalid workspace: " + "; ".join(errors))

    source = SOURCES[args.source]
    source_register = {row["source_id"]: row for row in read_csv(CONTROL / "SOURCE_REGISTER.csv")}
    if source.source_id not in source_register or source_register[source.source_id]["cold_allowed"] != "TRUE":
        parser.error("source is not enabled for cold search")

    raw_dir = RAW / args.execution_id
    if raw_dir.exists() and any(raw_dir.iterdir()):
        parser.error("execution raw directory already contains data")
    raw_dir.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS / f"{args.execution_id}.{args.source}.csv"
    RESULTS.mkdir(parents=True, exist_ok=True)
    token = source.initial_token
    initial_token = token
    rows: list[dict[str, str]] = []
    raw_paths: list[str] = []
    total: int | None = None
    terminal, status, api_failure, api_truncated, notes = "PENDING", "COMPLETE", "FALSE", "FALSE", ""
    pages = 0
    started = now()
    contact = os.environ.get("PRIOR_ART_CONTACT_EMAIL")
    headers = {"User-Agent": f"{USER_AGENT} ({contact})" if contact else USER_AGENT, "Accept": "application/json, application/atom+xml;q=0.9, */*;q=0.1"}
    if args.source == "openalex" and os.environ.get("OPENALEX_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["OPENALEX_API_KEY"]
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if args.source == "semantic-scholar" and api_key:
        headers["x-api-key"] = api_key
    try:
        for number in range(1, args.max_pages + 1):
            if number > 1:
                time.sleep(3.1)
            url = source.build_url(query["query_text"], args.page_size, token, contact)
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                payload = response.read()
            raw_relative = Path("data/searches/raw") / args.execution_id / f"page-{number:04d}.{args.source}.{source.extension}"
            (RAW.parent.parent.parent / raw_relative).write_bytes(payload)
            raw_paths.append(raw_relative.as_posix())
            if payload.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                raise PermissionError("API returned an HTML access challenge")
            page = source.parse(payload, raw_relative.as_posix(), args.page_size, len(rows))
            rows.extend(page.rows)
            pages += 1
            total = page.total if page.total is not None else total
            if page.exhausted:
                terminal = "SOURCE_EXHAUSTED"
                break
            token = page.next_token or token
            if page.capped:
                terminal, api_truncated = "API_RESULT_CAP", "TRUE"
                break
        if terminal == "PENDING":
            terminal = "PAGE_LIMIT_REACHED"
    except urllib.error.HTTPError as exc:
        terminal = "RATE_LIMITED" if exc.code == 429 else "API_FAILURE"
        status, api_failure, notes = "FAILED", "TRUE", f"HTTP {exc.code}: {exc.reason}"
    except PermissionError as exc:
        terminal, status, notes = "ACCESS_BLOCKED", "BLOCKED", str(exc)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        terminal, status, api_failure, notes = "API_FAILURE", "FAILED", "TRUE", f"{type(exc).__name__}: request or response processing failed"

    with result_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result_relative = result_path.relative_to(DATA.parent).as_posix()
    append_rows(LEDGER, LEDGER_FIELDS, [{
        "execution_id": args.execution_id, "query_id": args.query_id, "stage": query["stage"],
        "source_id": source.source_id, "source_name": source.name, "access_method": "API",
        "parameters_json": json.dumps({"page_size": args.page_size, "max_pages": args.max_pages, "timeout_seconds": 45}, sort_keys=True, separators=(",", ":")),
        "filters": args.filters, "run_started_at": started, "run_completed_at": now(), "requested_page_size": str(args.page_size),
        "pagination_start": initial_token, "pagination_end": token, "pages_retrieved": str(pages), "result_count": str(len(rows)),
        "results_available": "" if total is None else str(total), "serious_candidate_count": "0", "api_failure": api_failure,
        "api_truncated": api_truncated, "terminal_condition": terminal, "status": status,
        "raw_response_paths": ";".join(raw_paths), "normalized_result_paths": result_relative, "notes": notes,
    }])
    print(f"{args.execution_id}: {len(rows)} results, {pages} page(s), terminal={terminal}")
    return 0 if status == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
