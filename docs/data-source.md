# Data Source

The source of truth for this dataset is the official Project Gutenberg RDF
metadata archive.

```text
https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2
```

The raw file belongs in:

```text
data/raw/rdf-files.tar.bz2
```

Download it with:

```sh
python3 scripts/download_raw_data.py
```

## Why Official RDF

The official RDF archive is used because it is the richest official metadata
source for Project Gutenberg ebooks. It contains book records, people, subjects,
bookshelves, languages, rights, download counts, and file-format URLs.

Using the official source makes the dataset more reproducible than building it
from an unofficial API response.

## Gutendex

Gutendex is a useful JSON API for Project Gutenberg metadata, but it is not the
source of truth for this dataset.

During early testing, a list-style Gutendex metadata request was slow from our
environment. A single-book request was much faster. Because this project is
focused on bulk metadata access, the official RDF archive is a better source for
the generated dataset.

## Raw Data Rule

Files in `data/raw` should stay unchanged. The importer reads raw metadata and
creates generated CSV files in `data/processed`.

If the processed files need to change, regenerate them from the raw archive
instead of editing CSV rows manually.
