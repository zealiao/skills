#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
import sys
import urllib.parse
import urllib.request

DEFAULT_API_KEY = "ns1SH9hOjRP0lG/JNKaO7RLIBBK4Z6V50yTH7ke3ffKLj1m5L3vYMmqmHQ=="
DEFAULT_BASE_URL = "https://api.tikhub.io"
DEFAULT_ENDPOINT = "/api/v1/douyin/app/v3/fetch_one_video_by_share_url"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def _extract_first_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s]+", text)
    if not match:
        return None
    return match.group(0).rstrip(".,)")


def _build_share_url(args: argparse.Namespace) -> str:
    if args.share_url:
        return args.share_url.strip()
    if args.share_text:
        found = _extract_first_url(args.share_text)
        if found:
            return found
        raise ValueError("No URL found in --share-text.")
    raise ValueError("Provide either --share-url or --share-text.")


def _pretty_error_text(text: str) -> str:
    lowered = text.lower()
    if "cloudflare" in lowered and "1010" in lowered:
        return (
            "Access denied by Cloudflare (1010). "
            "This environment is blocked by api.tikhub.io. "
            "Try running the same command on your local network/VPS, or contact TikHub support to allow your IP."
        )
    return text


def _should_retry_http(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Douyin video data from a share link via TikHub API."
    )
    parser.add_argument("--share-url", help="Douyin share URL, e.g. https://v.douyin.com/xxxx/")
    parser.add_argument("--share-text", help="Full shared text that contains a Douyin URL")
    parser.add_argument("--api-key", help="TikHub API key; defaults to env or built-in key")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="TikHub API base URL")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Retry attempts on transient failures")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Initial retry delay seconds (uses linear backoff: delay * attempt)",
    )
    parser.add_argument(
        "--user-agent",
        default=os.getenv("TIKHUB_USER_AGENT") or DEFAULT_USER_AGENT,
        help="HTTP User-Agent header; defaults to a browser-like UA",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print full API response (default prints only response.data when available)",
    )
    args = parser.parse_args()

    try:
        share_url = _build_share_url(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    api_key = args.api_key or os.getenv("TIKHUB_API_KEY") or DEFAULT_API_KEY
    if not api_key:
        print("Missing API key. Set --api-key or TIKHUB_API_KEY.", file=sys.stderr)
        return 2

    query = urllib.parse.urlencode({"share_url": share_url})
    url = args.base_url.rstrip("/") + DEFAULT_ENDPOINT + "?" + query

    req = urllib.request.Request(url, method="GET")
    req.add_header("accept", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", args.user_agent)

    attempts = max(1, args.retries)
    raw = ""
    status = 0
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                raw = resp.read().decode("utf-8")
                status = resp.status
                last_err = None
                break
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", errors="replace")
            if attempt < attempts and _should_retry_http(exc.code):
                time.sleep(args.retry_delay * attempt)
                continue
            print(_pretty_error_text(err), file=sys.stderr)
            return 1
        except urllib.error.URLError as exc:
            last_err = exc
            if attempt < attempts:
                time.sleep(args.retry_delay * attempt)
                continue
            print(f"Network error: {exc}", file=sys.stderr)
            return 1

    if last_err is not None:
        print(f"Network error: {last_err}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(raw if args.raw else '{"error":"Non-JSON response from API"}', file=sys.stderr)
        return 1

    if status >= 400:
        print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None), file=sys.stderr)
        return 1

    output = payload if args.raw else payload.get("data", payload)
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
