# Project Gutenberg Ebook Metadata Dataset

This repository builds a clean metadata dataset from the official Project
Gutenberg RDF catalog.

It does not include ebook text content. It extracts book-level metadata into CSV
tables that are easy to use directly or import into PostgreSQL.

## Data Source

Raw metadata comes from the official Project Gutenberg RDF feed:

```text
https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2
```

Place the raw archive here:

```text
data/raw/rdf-files.tar.bz2
```

## Output Files

Generated CSV files are published through this repository's GitHub Releases.

The repository also includes scripts so users can regenerate the CSV files
themselves from the official Project Gutenberg RDF archive.

The generated files are:

```text
books.csv
authors.csv
categories.csv
book_authors.csv
book_categories.csv
formats.csv
```

When generated locally, these files are written to `data/processed`.

## Structure

```text
data/
  raw/          official Gutenberg source archive
  processed/    generated CSV files
docs/           project, schema, source, import, and benchmark notes
scripts/
  download_raw_data.py
  import_rdf_metadata.py
  load_postgres.py
```

## Documentation

- [Product spec](docs/product-spec.md)
- [Schema](docs/schema.md)
- [Data source](docs/data-source.md)
- [PostgreSQL import](docs/postgres-import.md)
- [Benchmark](docs/benchmark.md)
- [Attribution](ATTRIBUTION.md)

## Install

Create and activate a virtual environment, then install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Generate CSV Files

If you want to regenerate the dataset yourself, first download the official RDF
archive:

```sh
python3 scripts/download_raw_data.py
```

To force a fresh download:

```sh
python3 scripts/download_raw_data.py --force
```

Run:

```sh
python3 scripts/import_rdf_metadata.py
```

By default this reads:

```text
data/raw/rdf-files.tar.bz2
```

and writes:

```text
data/processed/
```

You can also pass paths manually:

```sh
python3 scripts/import_rdf_metadata.py \
  --input data/raw/rdf-files.tar.bz2 \
  --output-dir data/processed
```

For testing a smaller import:

```sh
python3 scripts/import_rdf_metadata.py --limit 100
```

## Load Into PostgreSQL

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

Then run:

```sh
python3 scripts/load_postgres.py
```

By default, the loader:

- reads CSV files from `data/processed`
- creates tables if they do not exist
- truncates existing data
- bulk-loads the CSV files using PostgreSQL `COPY`

Use another schema:

```sh
python3 scripts/load_postgres.py --schema gutenberg
```

Use another env file:

```sh
python3 scripts/load_postgres.py --env-file .env.local
```

Skip table creation:

```sh
python3 scripts/load_postgres.py --no-create
```

Append without truncating:

```sh
python3 scripts/load_postgres.py --no-truncate
```

Show more detailed loader logs:

```sh
python3 scripts/load_postgres.py --log-level DEBUG
```

## Tables

### books

One row per Project Gutenberg ebook.

Main fields:

```text
id
gutenberg_id
title
issued
rights
media_type
download_count
languages
source_url
```

### authors

One row per unique author or contributor.

Main fields:

```text
id
source_id
name
birth_year
death_year
```

### categories

One row per unique subject or bookshelf.

Main fields:

```text
id
name
type
```

`type` is usually:

```text
subject
bookshelf
```

### book_authors

Join table between books and authors.

Main fields:

```text
book_id
author_id
role
```

`role` can be:

```text
author
translator
```

### book_categories

Join table between books and categories.

Main fields:

```text
book_id
category_id
```

### formats

Download and file-format metadata for each book.

Main fields:

```text
id
book_id
mime_type
url
extent
modified
```

## Current Generated Size

Current generated CSV record counts, excluding headers:

```text
78402   books.csv
26823   authors.csv
42697   categories.csv
79073   book_authors.csv
470438  book_categories.csv
2187291 formats.csv
```

`formats.csv` is large because Project Gutenberg lists many file variants per
book.

## Notes

- Raw data should stay unchanged in `data/raw`.
- Generated CSV files can be recreated from the raw RDF archive.
- `.env` should not be committed because it may contain database credentials.
