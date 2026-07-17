#!/usr/bin/env python3
"""Find real-life TikTok hook candidates through TikHub with a hard cost gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SEARCH_ENDPOINT = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_video_search_result"
KEYCHAIN_SERVICE = "video-content-skills/tikhub"
DEFAULT_UNIT_COST_USD = 0.001


def resolve_api_key() -> str:
    """Load the credential only after execution has passed every budget check."""
    value = os.environ.get("TIKHUB_API_KEY", "").strip()
    if value:
        return value
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            os.environ.get("USER", ""),
            "-s",
            KEYCHAIN_SERVICE,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise SystemExit(
        "TikHub key not found. Set TIKHUB_API_KEY or store it in macOS Keychain "
        f"service {KEYCHAIN_SERVICE!r}."
    )


def request_json(url: str, api_key: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"TikHub HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"TikHub request failed: {exc.reason}") from exc


def extract_candidates(payload: dict[str, Any], query: str) -> list[dict[str, Any]]:
    items = payload.get("data", {}).get("search_item_list", [])
    candidates: list[dict[str, Any]] = []
    for item in items:
        aweme = item.get("aweme_info") or {}
        video_id = str(aweme.get("aweme_id") or "").strip()
        author = aweme.get("author") or {}
        username = str(author.get("unique_id") or "").strip()
        if not video_id or not username:
            continue
        stats = aweme.get("statistics") or {}
        video = aweme.get("video") or {}
        candidates.append(
            {
                "query": query,
                "video_id": video_id,
                "creator": username,
                "description": str(aweme.get("desc") or "").strip(),
                "duration_seconds": round(float(video.get("duration") or 0) / 1000, 3),
                "views": int(stats.get("play_count") or 0),
                "likes": int(stats.get("digg_count") or 0),
                "comments": int(stats.get("comment_count") or 0),
                "shares": int(stats.get("share_count") or 0),
                "published_at": int(aweme.get("create_time") or 0),
                "source_url": f"https://www.tiktok.com/@{username}/video/{video_id}",
                "license_status": "unverified",
                "review_status": "unreviewed",
            }
        )
    return candidates


def build_search_url(query: str, args: argparse.Namespace) -> str:
    params = urllib.parse.urlencode(
        {
            "keyword": query,
            "region": args.region,
            "count": args.count,
            "sort_type": args.sort_type,
            "publish_time": args.publish_time,
        }
    )
    return f"{SEARCH_ENDPOINT}?{params}"


def write_outputs(output_dir: Path, candidates: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.json").write_text(
        json.dumps({"summary": summary, "candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# TikTok real-footage hook candidates",
        "",
        f"- Queries: {', '.join(summary['queries'])}",
        f"- Requests: {summary['request_count']}",
        f"- Estimated cost: ${summary['estimated_cost_usd']:.3f}",
        f"- Unique candidates: {summary['unique_candidates']}",
        "- Licensing: discovery only; every candidate remains unverified until the creator grants rights.",
        "",
        "| Views | Likes | Creator | Description | Source |",
        "| ---: | ---: | --- | --- | --- |",
    ]
    for candidate in candidates:
        description = candidate["description"].replace("|", "\\|").replace("\n", " ")[:140]
        lines.append(
            f"| {candidate['views']:,} | {candidate['likes']:,} | "
            f"@{candidate['creator']} | {description} | [TikTok]({candidate['source_url']}) |"
        )
    (output_dir / "candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", required=True, help="Repeat for multiple searches")
    parser.add_argument("--output-dir", type=Path, default=Path(".work/tikhub-hook-search/latest"))
    parser.add_argument("--region", default="US")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--sort-type", type=int, default=1, help="TikHub/TikTok sort mode; 1 is most liked")
    parser.add_argument("--publish-time", type=int, default=180, help="TikHub publish-time filter")
    parser.add_argument("--unit-cost-usd", type=float, default=DEFAULT_UNIT_COST_USD)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cost-authorized", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queries = list(dict.fromkeys(query.strip() for query in args.query if query.strip()))
    if not queries:
        raise SystemExit("At least one non-empty --query is required")
    if not 1 <= args.count <= 20:
        raise SystemExit("--count must be between 1 and 20")
    if args.unit_cost_usd < 0:
        raise SystemExit("--unit-cost-usd cannot be negative")

    request_count = len(queries)
    estimated_cost = request_count * args.unit_cost_usd
    preview = {
        "mode": "execute" if args.execute else "dry-run",
        "queries": queries,
        "request_count": request_count,
        "results_requested": request_count * args.count,
        "estimated_cost_usd": round(estimated_cost, 6),
        "region": args.region,
        "credential_loaded": False,
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    if not args.cost_authorized:
        raise SystemExit("Paid execution requires --cost-authorized")
    if args.max_requests is None or request_count > args.max_requests:
        raise SystemExit("Execution blocked: set --max-requests at or above the previewed request count")
    if args.max_cost_usd is None or estimated_cost > args.max_cost_usd + 1e-12:
        raise SystemExit("Execution blocked: set --max-cost-usd at or above the previewed estimate")

    api_key = resolve_api_key()
    combined: dict[str, dict[str, Any]] = {}
    for query in queries:
        payload = request_json(build_search_url(query, args), api_key)
        if payload.get("code") not in (0, 200):
            raise SystemExit(f"TikHub returned code={payload.get('code')}: {payload.get('message_zh') or payload.get('message')}")
        for candidate in extract_candidates(payload, query):
            combined.setdefault(candidate["video_id"], candidate)

    candidates = sorted(combined.values(), key=lambda item: (item["views"], item["likes"]), reverse=True)
    summary = {
        **preview,
        "credential_loaded": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "unique_candidates": len(candidates),
    }
    write_outputs(args.output_dir.expanduser().resolve(), candidates, summary)
    print(f"Saved {len(candidates)} unique candidates to {args.output_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
