# Project Gutenberg Ebook Metadata Dataset

Clean CSV exports from the official Project Gutenberg RDF metadata catalog.

This repository does not include ebook text. It extracts book-level metadata
into six relational CSV tables that can be used directly, analyzed locally, or
loaded into PostgreSQL.

## What You Get

Generated CSV files are published through this repository's GitHub Releases.
You can also regenerate them from the official Project Gutenberg RDF archive.

The export contains:

```text
books.csv
authors.csv
categories.csv
book_authors.csv
book_categories.csv
formats.csv
```

Use [docs/schema.md](docs/schema.md) for column definitions and row counts.

## Quick Start

Install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Download the official RDF archive:

```sh
python3 scripts/download_raw_data.py
```

Generate CSV files:

```sh
python3 scripts/import_rdf_metadata.py
```

The default paths are:

```text
data/raw/rdf-files.tar.bz2
data/processed/
```

For a small test run:

```sh
python3 scripts/import_rdf_metadata.py --limit 100
```

## PostgreSQL

Create a `.env` file with a database URL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

Load the generated CSV files:

```sh
python3 scripts/load_postgres.py
```

The loader creates tables, truncates existing rows, bulk-loads the CSV files with
PostgreSQL `COPY`, and creates indexes for common catalog/API queries. See
[docs/postgres-import.md](docs/postgres-import.md) for options, index behavior,
and import safety notes.

## Repository Layout

```text
data/
  raw/          official Gutenberg RDF archive
  processed/    generated CSV files
docs/           focused project documentation
scripts/
  download_raw_data.py
  import_rdf_metadata.py
  load_postgres.py
```

## Documentation

- [Product spec](docs/product-spec.md): purpose, users, scope, and non-goals
- [Data source](docs/data-source.md): official RDF source and raw-data rules
- [Schema](docs/schema.md): CSV tables, columns, relationships, and row counts
- [PostgreSQL import](docs/postgres-import.md): database loading and indexes
- [Benchmark](docs/benchmark.md): initial API speed check that motivated exports
- [Attribution](ATTRIBUTION.md): Project Gutenberg source and license notes

## Notes

- Raw source files in `data/raw` should stay unchanged.
- Generated CSV files in `data/processed` can be recreated from the raw archive.
- `.env` should not be committed because it may contain database credentials.
