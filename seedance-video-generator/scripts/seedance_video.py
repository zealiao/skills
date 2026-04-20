#!/usr/bin/env python3
"""CLI for managing Seedance video generation tasks via Volcengine Ark."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_ENDPOINT = "/contents/generations/tasks"


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip())


def build_headers() -> dict[str, str]:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise SystemExit("Missing ARK_API_KEY")

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    api_base = os.environ.get("ARK_API_BASE", DEFAULT_API_BASE).rstrip("/")
    request = urllib.request.Request(
        f"{api_base}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=build_headers(),
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ark HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Ark request failed: {exc.reason}") from exc


def request_json(method: str, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    api_base = os.environ.get("ARK_API_BASE", DEFAULT_API_BASE).rstrip("/")
    url = f"{api_base}{path}"
    if query:
        encoded_query = urllib.parse.urlencode(
            [(key, value) for key, value in query.items() if value is not None and value != ""],
            doseq=True,
        )
        if encoded_query:
            url = f"{url}?{encoded_query}"

    request = urllib.request.Request(
        url,
        headers=build_headers(),
        method=method,
    )

    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ark HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Ark request failed: {exc.reason}") from exc


def add_reference_items(payload: dict[str, Any], item_type: str, values: list[str], role: str) -> None:
    if not values:
        return

    content = payload.setdefault("content", [])
    for url in values:
        content.append(
            {
                "type": item_type,
                item_type: {"url": url},
                "role": role,
            }
        )


def build_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload:
        with Path(args.payload).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise SystemExit("Payload file must contain a JSON object")
        return payload

    model = args.model or os.environ.get("SEEDANCE_MODEL")
    if not model:
        raise SystemExit("Missing model. Pass --model or set SEEDANCE_MODEL")
    if not args.prompt:
        raise SystemExit("Missing prompt. Pass --prompt unless using --payload")

    payload: dict[str, Any] = {
        "model": model,
        "content": [{"type": "text", "text": args.prompt}],
    }

    if args.generate_audio:
        payload["generate_audio"] = True
    if args.ratio:
        payload["ratio"] = args.ratio
    if args.duration is not None:
        payload["duration"] = args.duration
    if args.watermark is not None:
        payload["watermark"] = args.watermark

    add_reference_items(payload, "image_url", args.image_url, "reference_image")
    add_reference_items(payload, "video_url", args.video_url, "reference_video")
    add_reference_items(payload, "audio_url", args.audio_url, "reference_audio")
    return payload


def summarize_response(response: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "id": response.get("id"),
        "status": response.get("status"),
        "model": response.get("model"),
    }

    for key in ("created_at", "updated_at", "request_id"):
        if key in response:
            summary[key] = response[key]

    summary["raw"] = response
    return summary


def run_create(args: argparse.Namespace) -> int:
    payload = build_payload_from_args(args)

    if args.print_payload:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    response = post_json(DEFAULT_ENDPOINT, payload)
    if args.dump_json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(summarize_response(response), ensure_ascii=False, indent=2))
    return 0


def run_get(args: argparse.Namespace) -> int:
    response = request_json("GET", f"{DEFAULT_ENDPOINT}/{args.task_id}")
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def run_list(args: argparse.Namespace) -> int:
    query: dict[str, Any] = {
        "page_index": args.page_index,
        "page_size": args.page_size,
    }
    if args.status:
        query["filter.status"] = args.status
    if args.task_ids:
        query["filter.task_ids"] = ",".join(args.task_ids)

    response = request_json("GET", DEFAULT_ENDPOINT, query=query)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def run_delete(args: argparse.Namespace) -> int:
    response = request_json("DELETE", f"{DEFAULT_ENDPOINT}/{args.task_id}")
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seedance video generation task helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a video generation task")
    create_parser.add_argument("--model", help="Ark endpoint/model id, e.g. ep-xxxxxxxx")
    create_parser.add_argument("--prompt", help="Prompt text")
    create_parser.add_argument("--payload", help="Path to a JSON file matching the request body")
    create_parser.add_argument("--image-url", action="append", default=[], help="Reference image URL")
    create_parser.add_argument("--video-url", action="append", default=[], help="Reference video URL")
    create_parser.add_argument("--audio-url", action="append", default=[], help="Reference audio URL")
    create_parser.add_argument("--ratio", help="Aspect ratio, e.g. 16:9")
    create_parser.add_argument("--duration", type=int, help="Video duration in seconds")
    create_parser.add_argument("--generate-audio", action="store_true", help="Ask the model to generate audio")
    create_parser.add_argument(
        "--watermark",
        dest="watermark",
        action="store_true",
        default=None,
        help="Enable watermark",
    )
    create_parser.add_argument(
        "--no-watermark",
        dest="watermark",
        action="store_false",
        help="Disable watermark",
    )
    create_parser.add_argument("--dump-json", action="store_true", help="Print the raw API response")
    create_parser.add_argument("--print-payload", action="store_true", help="Print the request body without sending")
    create_parser.set_defaults(func=run_create)

    get_parser = subparsers.add_parser("get", help="Get a single video generation task")
    get_parser.add_argument("task_id", help="Task id returned by the create API")
    get_parser.set_defaults(func=run_get)

    list_parser = subparsers.add_parser("list", help="List video generation tasks")
    list_parser.add_argument("--page-index", type=int, default=1, help="Page index, default 1")
    list_parser.add_argument("--page-size", type=int, default=20, help="Page size, default 20")
    list_parser.add_argument(
        "--status",
        help="Filter by task status",
    )
    list_parser.add_argument(
        "--task-id",
        dest="task_ids",
        action="append",
        default=[],
        help="Filter by task id; repeat for multiple ids",
    )
    list_parser.set_defaults(func=run_list)

    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete a task via the official cancel/delete API",
    )
    delete_parser.add_argument("task_id", help="Task id to delete or cancel")
    delete_parser.set_defaults(func=run_delete)

    return parser


def main() -> int:
    load_local_env()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
