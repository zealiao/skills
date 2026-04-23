#!/usr/bin/env python3

import argparse
import json
import mimetypes
import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


DEFAULT_BUCKET = "aishipin"
DEFAULT_ENDPOINT_URL = "https://s3.bitiful.net"
DEFAULT_REGION = "cn-east-1"


def emit(payload, exit_code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def env_or_default(name, default):
    return os.environ.get(name, default)


def required_env(name):
    value = os.environ.get(name)
    if not value:
        emit(
            {
                "error": f"Missing required environment variable: {name}",
                "hint": "Set BITIFUL_ACCESS_KEY and BITIFUL_SECRET_KEY before running this command.",
            },
            1,
        )
    return value


def make_client():
    return boto3.client(
        "s3",
        endpoint_url=env_or_default("BITIFUL_ENDPOINT_URL", DEFAULT_ENDPOINT_URL),
        aws_access_key_id=required_env("BITIFUL_ACCESS_KEY"),
        aws_secret_access_key=required_env("BITIFUL_SECRET_KEY"),
        region_name=env_or_default("BITIFUL_REGION", DEFAULT_REGION),
        config=Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=20,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


def bucket_name():
    return env_or_default("BITIFUL_BUCKET", DEFAULT_BUCKET)


def public_url(key):
    bucket = bucket_name()
    endpoint = env_or_default(
        "BITIFUL_PUBLIC_BASE_URL",
        f"https://{bucket}.s3.bitiful.net",
    ).rstrip("/")
    return f"{endpoint}/{key}"


def upload_file(client, source, key):
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        emit({"error": f"Source file not found: {source_path}"}, 1)

    extra_args = {}
    content_type, _ = mimetypes.guess_type(str(source_path))
    if content_type:
        extra_args["ContentType"] = content_type

    if extra_args:
        client.upload_file(
            str(source_path),
            bucket_name(),
            key,
            ExtraArgs=extra_args,
        )
    else:
        client.upload_file(str(source_path), bucket_name(), key)

    emit(
        {
            "action": "upload",
            "bucket": bucket_name(),
            "key": key,
            "source": str(source_path),
            "url": public_url(key),
            "content_type": content_type,
        }
    )


def download_file(client, key, destination):
    destination_path = Path(destination).expanduser().resolve()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket_name(), key, str(destination_path))

    emit(
        {
            "action": "download",
            "bucket": bucket_name(),
            "key": key,
            "destination": str(destination_path),
        }
    )


def list_objects(client, prefix, max_keys):
    response = client.list_objects_v2(
        Bucket=bucket_name(),
        Prefix=prefix or "",
        MaxKeys=max_keys,
    )
    contents = response.get("Contents", [])
    emit(
        {
            "action": "list",
            "bucket": bucket_name(),
            "prefix": prefix or "",
            "count": len(contents),
            "items": [
                {
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat(),
                    "etag": item["ETag"],
                }
                for item in contents
            ],
        }
    )


def delete_object(client, key):
    client.delete_object(Bucket=bucket_name(), Key=key)
    emit({"action": "delete", "bucket": bucket_name(), "key": key})


def generate_presigned_url(client, key, expires_in):
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name(), "Key": key},
        ExpiresIn=expires_in,
    )
    emit(
        {
            "action": "presign",
            "bucket": bucket_name(),
            "key": key,
            "expires_in": expires_in,
            "url": url,
        }
    )


def head_object(client, key):
    response = client.head_object(Bucket=bucket_name(), Key=key)
    emit(
        {
            "action": "head",
            "bucket": bucket_name(),
            "key": key,
            "content_length": response.get("ContentLength"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag"),
            "last_modified": response.get("LastModified").isoformat()
            if response.get("LastModified")
            else None,
            "metadata": response.get("Metadata", {}),
        }
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Bitiful S4 helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload = subparsers.add_parser("upload", help="Upload a file")
    upload.add_argument("source", help="Local file path")
    upload.add_argument("key", help="Object key in bucket")

    download = subparsers.add_parser("download", help="Download a file")
    download.add_argument("key", help="Object key in bucket")
    download.add_argument("destination", help="Local output path")

    list_cmd = subparsers.add_parser("list", help="List objects")
    list_cmd.add_argument("--prefix", default="", help="Prefix filter")
    list_cmd.add_argument("--max-keys", type=int, default=100, help="Max keys")

    delete = subparsers.add_parser("delete", help="Delete an object")
    delete.add_argument("key", help="Object key in bucket")

    presign = subparsers.add_parser("presign", help="Generate a presigned URL")
    presign.add_argument("key", help="Object key in bucket")
    presign.add_argument("--expires-in", type=int, default=3600, help="Expiry in seconds")

    head = subparsers.add_parser("head", help="Read object metadata")
    head.add_argument("key", help="Object key in bucket")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = make_client()

    try:
        if args.command == "upload":
            upload_file(client, args.source, args.key)
        if args.command == "download":
            download_file(client, args.key, args.destination)
        if args.command == "list":
            list_objects(client, args.prefix, args.max_keys)
        if args.command == "delete":
            delete_object(client, args.key)
        if args.command == "presign":
            generate_presigned_url(client, args.key, args.expires_in)
        if args.command == "head":
            head_object(client, args.key)
    except (ClientError, BotoCoreError, NoCredentialsError) as exc:
        emit(
            {
                "error": str(exc),
                "command": args.command,
                "bucket": bucket_name(),
            },
            1,
        )

    emit({"error": f"Unsupported command: {args.command}"}, 1)


if __name__ == "__main__":
    main()
