#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from urllib.request import urlretrieve

RAW_DATA_URL = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
DEFAULT_OUTPUT = Path("data/raw/rdf-files.tar.bz2")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
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
    urlretrieve(RAW_DATA_URL, args.output)
    logging.info("download complete: %.1f MB", args.output.stat().st_size / 1024 / 1024)


if __name__ == "__main__":
    main()
