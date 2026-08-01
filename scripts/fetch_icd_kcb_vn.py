"""Fetch Vietnamese ICD-10 rows from icd.kcb.vn backend API.

The Angular app at https://icd.kcb.vn/icd-10/icd10-dual uses the backend
https://ccs.whiteneuron.com/api/ICD10/. This script fetches politely, caches
responses, and writes partial results even if child endpoint discovery is not
complete.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://ccs.whiteneuron.com/api/ICD10"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Vietnamese ICD-10 rows from icd.kcb.vn backend")
    parser.add_argument("--output", default="data/raw/icd10_kcb_vi.csv")
    parser.add_argument("--cache-dir", default="data/processed/icd_kcb_cache")
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of queued nodes to expand")
    parser.add_argument("--max-requests", type=int, default=500, help="Maximum uncached HTTP requests in this run")
    parser.add_argument("--quiet-warnings", action="store_true", help="Do not print each failed URL")
    parser.add_argument("--base-url", default=BASE_URL)
    return parser


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json"


def fetch_json(url: str, cache_dir: Path, delay: float, *, quiet: bool = False) -> tuple[dict | None, bool]:
    """Return (payload, made_request). Failed responses are cached as metadata."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / cache_key(url)
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("__failed__"):
            return None, False
        return cached, False

    time.sleep(delay)
    request = Request(url, headers={"User-Agent": "ai-race-icd-fetch/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        cache_path.write_text(
            json.dumps({"__failed__": True, "url": url, "status": exc.code}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if not quiet:
            print(f"WARN fetch failed {url}: HTTP {exc.code}")
        return None, True
    except (URLError, TimeoutError) as exc:
        if not quiet:
            print(f"WARN fetch failed {url}: {exc}")
        return None, True

    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload, True


def normalize_name(raw: str, code: str) -> str:
    text = " ".join((raw or "").split())
    prefix = f"({code}) "
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def row_from_item(item: dict, parent_code: str, level: int) -> dict[str, str]:
    data = item.get("data") or {}
    source_id = str(item.get("id") or data.get("id") or "").strip()
    code = str(data.get("id") or item.get("id") or data.get("code") or "").strip()
    raw_name = str(data.get("name") or "").strip()
    name = normalize_name(raw_name, code)
    return {
        "code": code,
        "name": name,
        "parent_code": parent_code,
        "level": str(level),
        "aliases": raw_name if raw_name and raw_name != name else "",
        "source_id": source_id,
        "model": str(item.get("model") or ""),
        "is_leaf": str(bool(item.get("is_leaf"))).lower(),
    }


def node_data_url(base_url: str, model: str, node_id: str) -> str:
    return f"{base_url}/data/{model}?{urlencode({'id': node_id, 'lang': 'dual'})}"


def child_models(model: str) -> tuple[str, ...]:
    if model == "root":
        return ("chapter",)
    if model == "chapter":
        return ("section",)
    if model == "section":
        return ("type",)
    if model == "type":
        return ("type", "disease")
    return ("chapter", "section", "type")


def discover_children_from_html(payload: dict | None, model: str) -> list[tuple[str, str]]:
    if not payload or payload.get("status") != "success":
        return []
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return []
    raw_html = data.get("data", {}).get("html") or ""
    allowed = set(child_models(model))
    children: list[tuple[str, str]] = []
    for match in re.finditer(r'href="(chapter|section|type)/([^"#?]+)"', raw_html):
        child_model = match.group(1)
        child_id = html.unescape(match.group(2)).strip()
        if child_model in allowed and child_id:
            children.append((child_model, child_id))
    return list(dict.fromkeys(children))


def fetch_node(base_url: str, model: str, node_id: str, cache_dir: Path, delay: float, quiet: bool = False) -> tuple[dict | None, bool]:
    return fetch_json(node_data_url(base_url, model, node_id), cache_dir, delay, quiet=quiet)


def item_from_node_payload(payload: dict | None) -> dict | None:
    if not payload or payload.get("status") != "success":
        return None
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def extract_items(payload: dict | None) -> list[dict]:
    if not payload or payload.get("status") != "success":
        return []
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("children", "childs", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def fetch_children(base_url: str, model: str, node_id: str, cache_dir: Path, delay: float, quiet: bool = False) -> tuple[list[tuple[str, str]], bool]:
    payload, made_request = fetch_node(base_url, model, node_id, cache_dir, delay, quiet=quiet)
    return discover_children_from_html(payload, model), made_request


def embedded_disease_rows(payload: dict | None, parent_code: str, level: int) -> list[dict[str, str]]:
    if not payload or payload.get("status") != "success":
        return []
    data = payload.get("data") or {}
    raw_html = data.get("data", {}).get("html") or "" if isinstance(data, dict) else ""
    rows: list[dict[str, str]] = []
    pattern = re.compile(
        r'href="disease/([^"#?]+)"\s+name="([^"]+)".*?field" hidden>name</div>.*?<div class="id" hidden>\1</div>',
        re.DOTALL,
    )
    for match in pattern.finditer(raw_html):
        source_id = html.unescape(match.group(1)).strip()
        code = html.unescape(match.group(2)).strip()
        content_match = re.search(
            r'<div class="content d-inline-block" >([^<]+)</div><span class="icons">\s*<div class="content-raw" hidden>' + re.escape(source_id) + r':',
            raw_html[match.start() : match.end() + 600],
            re.DOTALL,
        )
        name = " ".join(html.unescape(content_match.group(1)).split()) if content_match else code
        rows.append(
            {
                "code": code,
                "name": name,
                "parent_code": parent_code,
                "level": str(level),
                "aliases": "",
                "source_id": source_id,
                "model": "disease",
                "is_leaf": "true",
            }
        )
    return rows


def write_rows(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["code", "name", "parent_code", "level", "aliases", "source_id", "model", "is_leaf"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = build_parser().parse_args()
    cache_dir = Path(args.cache_dir)
    output_path = Path(args.output)

    requests_made = 0
    root_payload, made_request = fetch_json(f"{args.base_url}/root", cache_dir, args.delay, quiet=args.quiet_warnings)
    requests_made += int(made_request)
    root_items = extract_items(root_payload)
    rows = [
        {
            "code": "ROOT",
            "name": "ICD-10 tiếng Việt",
            "parent_code": "",
            "level": "0",
            "aliases": "",
            "source_id": "ROOT",
            "model": "root",
            "is_leaf": "false",
        }
    ]

    queue: deque[tuple[str, str, str, int]] = deque()
    for item in root_items:
        row = row_from_item(item, "ROOT", 1)
        rows.append(row)
        if row["code"] and row["is_leaf"] != "true":
            queue.append(("chapter", row["code"], row["code"], 2))

    expanded = 0
    seen = {row["code"] for row in rows}
    while queue:
        if args.limit is not None and expanded >= args.limit:
            break
        if requests_made >= args.max_requests:
            print(f"stopped=max_requests requests_made={requests_made}")
            break
        model, node_id, parent_code, level = queue.popleft()
        payload, made_request = fetch_node(args.base_url, model, node_id, cache_dir, args.delay, quiet=args.quiet_warnings)
        requests_made += int(made_request)
        children = discover_children_from_html(payload, model)
        expanded += 1

        for disease_row in embedded_disease_rows(payload, node_id, level + 1):
            if disease_row["code"] not in seen:
                rows.append(disease_row)
                seen.add(disease_row["code"])

        for child_model, child_id in children:
            if child_model == "disease":
                continue
            if requests_made >= args.max_requests:
                break
            payload, made_request = fetch_node(args.base_url, child_model, child_id, cache_dir, args.delay, quiet=args.quiet_warnings)
            requests_made += int(made_request)
            child = item_from_node_payload(payload)
            if child is None:
                continue
            row = row_from_item(child, parent_code, level)
            if not row["code"] or row["code"] in seen:
                continue
            rows.append(row)
            seen.add(row["code"])
            for disease_row in embedded_disease_rows(payload, row["code"], level + 1):
                if disease_row["code"] not in seen:
                    rows.append(disease_row)
                    seen.add(disease_row["code"])
            if row["is_leaf"] != "true":
                queue.append((child_model, row["code"], row["code"], level + 1))

    write_rows(rows, output_path)
    print(f"rows={len(rows)} expanded={expanded} requests_made={requests_made} output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
