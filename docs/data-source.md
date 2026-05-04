# Data Source

The source of truth is the official Project Gutenberg RDF metadata archive:

```text
https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2
```

Store the archive at:

```text
data/raw/rdf-files.tar.bz2
```

Download it with:

```sh
python3 scripts/download_raw_data.py
```

Useful downloader options:

```sh
python3 scripts/download_raw_data.py --force
python3 scripts/download_raw_data.py --output /path/to/rdf-files.tar.bz2
python3 scripts/download_raw_data.py --retries 5
```

The downloader writes to a temporary `.part` file and replaces the final archive
only after a complete download.

## Why RDF

The RDF archive is the richest official bulk metadata source for Project
Gutenberg. It includes book records, people, subjects, bookshelves, languages,
rights, download counts, and file-format URLs.

Gutendex is useful for quick JSON lookups, but it is not the dataset source. The
initial API speed check that motivated local exports is recorded in
[benchmark.md](benchmark.md).

## Raw Data Rule

Files in `data/raw` should stay unchanged. Treat them as source inputs, not
working files.

If processed CSV files need to change, regenerate them from the raw archive
instead of editing generated rows manually:

```sh
python3 scripts/import_rdf_metadata.py
```
