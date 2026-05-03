# PostgreSQL Import

The Postgres loader imports generated CSV files into relational tables.

## Requirements

Install dependencies:

```sh
python3 -m pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

If `DATABASE_URL` is already set in the terminal, that value is used instead of
the `.env` value.

## Run

```sh
python3 scripts/load_postgres.py
```

By default, the loader:

- reads CSV files from `data/processed`
- creates the schema and tables if needed
- creates indexes
- truncates existing data
- loads CSV data with PostgreSQL `COPY`

## Options

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

Show more detailed logs:

```sh
python3 scripts/load_postgres.py --log-level DEBUG
```

## Tables Created

The loader creates:

```text
books
authors
categories
book_authors
book_categories
formats
```

Foreign keys are created for join tables and format rows. The loader also creates
indexes for common lookup fields such as book title, author name, category name,
category type, and format MIME type.

## Important Behavior

The default import is destructive for existing rows in these tables because it
truncates before loading. Use `--no-truncate` only when you intentionally want to
append data.

For normal full refreshes, keep the default truncation behavior.
