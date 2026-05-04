#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

RAW_DATA_URL = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
DEFAULT_OUTPUT = Path("data/raw/rdf-files.tar.bz2")
CHUNK_SIZE = 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.output.exists() and args.output.stat().st_size > 0 and not args.force:
        logging.info("raw data already exists: %s", args.output)
        logging.info("use --force to download again")
        return

    logging.info("downloading %s", RAW_DATA_URL)
    logging.info("writing to %s", args.output)
    download_file(RAW_DATA_URL, args.output, retries=args.retries)
    logging.info("download complete: %.1f MB", args.output.stat().st_size / 1024 / 1024)


def download_file(url: str, output: Path, retries: int) -> None:
    partial = output.with_suffix(output.suffix + ".part")
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        if partial.exists():
            partial.unlink()

        try:
            expected_size = stream_download(url, partial)
            actual_size = partial.stat().st_size

            if expected_size is not None and actual_size != expected_size:
                raise RuntimeError(
                    f"incomplete download: got {actual_size} of {expected_size} bytes"
                )

            partial.replace(output)
            return
        except (OSError, RuntimeError, URLError) as exc:
            last_error = exc
            logging.warning("download attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(attempt * 2)

    raise SystemExit(f"download failed after {retries} attempts: {last_error}")


def stream_download(url: str, output: Path) -> int | None:
    with urlopen(url, timeout=60) as response:
        expected_size = response.headers.get("Content-Length")
        expected_bytes = int(expected_size) if expected_size else None
        downloaded = 0
        next_log_at = CHUNK_SIZE * 10

        with output.open("wb") as handle:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)

                if downloaded >= next_log_at:
                    if expected_bytes:
                        percent = downloaded / expected_bytes * 100
                        logging.info(
                            "downloaded %.1f/%.1f MB (%.1f%%)",
                            downloaded / 1024 / 1024,
                            expected_bytes / 1024 / 1024,
                            percent,
                        )
                    else:
                        logging.info("downloaded %.1f MB", downloaded / 1024 / 1024)
                    next_log_at += CHUNK_SIZE * 10

        return expected_bytes


if __name__ == "__main__":
    main()
