# Product Spec: Project Gutenberg Ebook Metadata Dataset

## Purpose

This project provides Project Gutenberg ebook metadata as clean, local CSV files.
It is built for people who want Gutenberg metadata without repeatedly calling a
public API or parsing the full official RDF catalog themselves.

The dataset does not include ebook text content. It focuses only on metadata:
books, authors, categories, book-author relationships, book-category
relationships, and available file formats.

## Why This Exists

Project Gutenberg has official machine-readable metadata, but the raw RDF catalog
is not convenient for many users. It requires downloading and parsing a large RDF
archive before the data can be used in normal tools.

Gutendex also provides a useful JSON API for Project Gutenberg metadata. During
early testing, however, list-style metadata access was slow from our environment.
That made it less suitable as the main source for bulk metadata workflows.

This project solves that problem by using the official Project Gutenberg RDF
metadata as the source and converting it into simple CSV tables that can be
loaded locally, opened in data tools, or imported into PostgreSQL.

## Target Users

- Developers building ebook catalog, search, or recommendation applications.
- Data users who want Gutenberg metadata in CSV form.
- People who want to import Gutenberg metadata into PostgreSQL.
- API developers who need clean relational tables for books, authors,
  categories, and formats.

## Scope

This project includes:

- official Project Gutenberg RDF metadata as raw input
- scripts to convert RDF metadata into CSV tables
- scripts to load the CSV tables into PostgreSQL
- normalized metadata tables for relational database use

This project does not include:

- full ebook text
- cleaned book content
- cover image downloads
- a public API server
- a web application

Those can be built in another project using this dataset as the import source.

## Output Tables

The generated dataset contains six CSV files:

```text
books.csv
authors.csv
categories.csv
book_authors.csv
book_categories.csv
formats.csv
```

The structure is relational because one book can have multiple authors,
categories, and file formats.

## Value

The value of this dataset is convenience and speed for bulk metadata usage.
Instead of calling an API many times or parsing RDF from scratch, users can work
with ready-made CSV files or load the data into PostgreSQL.

This makes the dataset useful as a foundation for future applications, including
a Django REST Framework API or an ebook discovery website.

## Source Of Truth

The source of truth is the official Project Gutenberg RDF feed:

```text
https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2
```

Gutendex is useful for comparison and quick exploration, but it is not the main
source for this dataset.
