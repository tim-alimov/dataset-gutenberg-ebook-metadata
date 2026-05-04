#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import tarfile
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "pgterms": "http://www.gutenberg.org/2009/pgterms/",
}

RDF_ABOUT = f"{{{NS['rdf']}}}about"


@dataclass(frozen=True)
class Person:
    source_id: str | None
    name: str
    birth_year: int | None = None
    death_year: int | None = None


@dataclass(frozen=True)
class Category:
    name: str
    type: str


@dataclass(frozen=True)
class FileFormat:
    url: str
    mime_type: str
    extent: int | None = None
    modified: str | None = None


@dataclass
class Book:
    gutenberg_id: int
    title: str | None = None
    issued: str | None = None
    rights: str | None = None
    media_type: str | None = None
    download_count: int | None = None
    languages: list[str] = field(default_factory=list)
    authors: list[Person] = field(default_factory=list)
    translators: list[Person] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    formats: list[FileFormat] = field(default_factory=list)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/rdf-files.tar.bz2"),
        help="RDF archive, RDF file, or directory of RDF files.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    export_csvs(iter_books(args.input, args.limit), args.output_dir)


def iter_books(input_path: Path, limit: int | None = None) -> Iterator[Book]:
    count = 0
    if input_path.is_dir():
        paths = [path for path in sorted(input_path.rglob("*.rdf")) if "test" not in path.parts]
        if limit is not None:
            paths = paths[:limit]
        for path in progress_iter(paths, total=len(paths), desc="parse rdf"):
            if "test" in path.parts:
                continue
            yield parse_rdf(path.read_bytes())
            count += 1
            if limit is not None and count >= limit:
                return
        return

    if input_path.suffix == ".rdf":
        yield parse_rdf(input_path.read_bytes())
        return

    with tarfile.open(input_path, "r:*") as archive:
        members = [
            member
            for member in archive
            if member.isfile() and member.name.endswith(".rdf") and "/test/" not in member.name
        ]
        if limit is not None:
            members = members[:limit]

        for member in progress_iter(members, total=len(members), desc="parse rdf"):
            if not member.isfile() or not member.name.endswith(".rdf"):
                continue
            if "/test/" in member.name:
                continue
            file_obj = archive.extractfile(member)
            if file_obj is None:
                continue
            yield parse_rdf(file_obj.read())
            count += 1
            if limit is not None and count >= limit:
                return


def progress_iter(items, total: int | None, desc: str):
    if tqdm is None:
        return items
    return tqdm(items, total=total, desc=desc, unit="file")


def parse_rdf(content: bytes) -> Book:
    root = ET.fromstring(content)
    ebook = root.find("pgterms:ebook", NS)
    if ebook is None:
        raise ValueError("RDF file does not contain pgterms:ebook")

    book = Book(
        gutenberg_id=parse_gutenberg_id(ebook.attrib.get(RDF_ABOUT, "")),
        title=text(ebook, "dcterms:title"),
        issued=text(ebook, "dcterms:issued"),
        rights=text(ebook, "dcterms:rights"),
        download_count=int_text(ebook, "pgterms:downloads"),
    )
    book.authors = people(ebook, "dcterms:creator")
    book.translators = people(ebook, "dcterms:contributor")
    book.languages = values(ebook, "dcterms:language")
    book.media_type = first_value(ebook, "dcterms:type")
    book.categories = categories(ebook)
    book.formats = formats(ebook)
    return book


def export_csvs(books: Iterator[Book], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    book_rows = []
    author_rows = []
    category_rows = []
    book_author_rows = []
    book_category_rows = []
    format_rows = []

    author_ids: dict[tuple[str | None, str, int | None, int | None], int] = {}
    category_ids: dict[tuple[str, str], int] = {}
    seen_book_ids: set[int] = set()

    for book in books:
        if book.gutenberg_id in seen_book_ids:
            continue
        seen_book_ids.add(book.gutenberg_id)

        book_rows.append(
            {
                "id": book.gutenberg_id,
                "gutenberg_id": book.gutenberg_id,
                "title": book.title,
                "issued": book.issued,
                "rights": book.rights,
                "media_type": book.media_type,
                "download_count": book.download_count,
                "languages": "; ".join(book.languages),
                "source_url": f"https://www.gutenberg.org/ebooks/{book.gutenberg_id}",
            }
        )

        for person, role in (
            *((person, "author") for person in book.authors),
            *((person, "translator") for person in book.translators),
        ):
            author_id = get_author_id(person, author_ids, author_rows)
            book_author_rows.append(
                {"book_id": book.gutenberg_id, "author_id": author_id, "role": role}
            )

        for category in book.categories:
            category_id = get_category_id(category, category_ids, category_rows)
            book_category_rows.append(
                {"book_id": book.gutenberg_id, "category_id": category_id}
            )

        for index, item in enumerate(book.formats, start=1):
            format_rows.append(
                {
                    "id": f"{book.gutenberg_id}-{index}",
                    "book_id": book.gutenberg_id,
                    "mime_type": item.mime_type,
                    "url": item.url,
                    "extent": item.extent,
                    "modified": item.modified,
                }
            )

    tables = [
        ("books.csv", book_rows),
        ("authors.csv", author_rows),
        ("categories.csv", category_rows),
        ("book_authors.csv", dedupe(book_author_rows)),
        ("book_categories.csv", dedupe(book_category_rows)),
        ("formats.csv", format_rows),
    ]
    for filename, rows in progress_iter(tables, total=len(tables), desc="write csv"):
        write_csv(output_dir / filename, rows)


def get_author_id(
    person: Person,
    author_ids: dict[tuple[str | None, str, int | None, int | None], int],
    author_rows: list[dict[str, object]],
) -> int:
    key = (person.source_id, person.name, person.birth_year, person.death_year)
    if key not in author_ids:
        author_ids[key] = len(author_ids) + 1
        author_rows.append(
            {
                "id": author_ids[key],
                "source_id": person.source_id,
                "name": person.name,
                "birth_year": person.birth_year,
                "death_year": person.death_year,
            }
        )
    return author_ids[key]


def get_category_id(
    category: Category,
    category_ids: dict[tuple[str, str], int],
    category_rows: list[dict[str, object]],
) -> int:
    key = (category.name, category.type)
    if key not in category_ids:
        category_ids[key] = len(category_ids) + 1
        category_rows.append(
            {"id": category_ids[key], "name": category.name, "type": category.type}
        )
    return category_ids[key]


def people(ebook: ET.Element, path: str) -> list[Person]:
    result = []
    for wrapper in ebook.findall(path, NS):
        agent = wrapper.find("pgterms:agent", NS)
        if agent is None:
            continue
        name = text(agent, "pgterms:name")
        if not name:
            continue
        result.append(
            Person(
                source_id=agent_id(agent.attrib.get(RDF_ABOUT)),
                name=name,
                birth_year=int_text(agent, "pgterms:birthdate"),
                death_year=int_text(agent, "pgterms:deathdate"),
            )
        )
    return result


def categories(ebook: ET.Element) -> list[Category]:
    result = []
    for value in values(ebook, "dcterms:subject"):
        result.append(Category(name=value, type="subject"))
    for value in values(ebook, "pgterms:bookshelf"):
        result.append(Category(name=value, type="bookshelf"))
    return unique_categories(result)


def formats(ebook: ET.Element) -> list[FileFormat]:
    result = []
    for wrapper in ebook.findall("dcterms:hasFormat", NS):
        file_element = wrapper.find("pgterms:file", NS)
        if file_element is None:
            continue
        url = file_element.attrib.get(RDF_ABOUT)
        if not url:
            continue
        for mime_type in values(file_element, "dcterms:format"):
            result.append(
                FileFormat(
                    url=url,
                    mime_type=mime_type,
                    extent=int_text(file_element, "dcterms:extent"),
                    modified=text(file_element, "dcterms:modified"),
                )
            )
    return result


def values(element: ET.Element, path: str) -> list[str]:
    result = []
    for wrapper in element.findall(path, NS):
        value = wrapper.find(".//rdf:value", NS)
        if value is not None and value.text:
            result.append(value.text.strip())
    return unique(result)


def first_value(element: ET.Element, path: str) -> str | None:
    items = values(element, path)
    return items[0] if items else None


def text(element: ET.Element, path: str) -> str | None:
    child = element.find(path, NS)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def int_text(element: ET.Element, path: str) -> int | None:
    value = text(element, path)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_gutenberg_id(value: str) -> int:
    match = re.search(r"ebooks/(\d+)", value)
    if not match:
        raise ValueError(f"Cannot parse Gutenberg ID from {value!r}")
    return int(match.group(1))


def agent_id(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"agents/(\d+)", value)
    return match.group(1) if match else value


def unique(values_: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values_:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def unique_categories(values_: list[Category]) -> list[Category]:
    seen = set()
    result = []
    for value in values_:
        key = (value.name, value.type)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def dedupe(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen = set()
    result = []
    for row in rows:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
