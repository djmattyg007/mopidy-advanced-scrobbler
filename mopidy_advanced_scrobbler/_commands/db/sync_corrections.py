from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Tuple
from urllib.parse import urlparse

import questionary
from prompt_toolkit.completion import FuzzyWordCompleter
from rich.table import Table, box

from mopidy_advanced_scrobbler._commands import AbortCommand, Counter
from mopidy_advanced_scrobbler._commands.db import (
    attach_external_db,
    connect_internal_db,
    verify_external_db,
)
from mopidy_advanced_scrobbler._commands.output import stderr, stdout


if TYPE_CHECKING:
    from argparse import Namespace

    from mopidy_advanced_scrobbler.db import Connection


load_both_differ_query = """
SELECT main.corrections.track_uri,
    main.corrections.title as main_title, main.corrections.artist as main_artist, main.corrections.album as main_album,
    ext.corrections.title as ext_title, ext.corrections.artist as ext_artist, ext.corrections.album as ext_album FROM main.corrections
INNER JOIN ext.corrections ON ext.corrections.track_uri = main.corrections.track_uri
WHERE main_title != ext_title OR main_artist != ext_artist OR main_album != ext_album
"""

update_correction_query = """
UPDATE {0}.corrections SET title = ?, artist = ?, album = ? WHERE track_uri = ?
"""

load_only_in_main_query = """
SELECT
    main.corrections.track_uri,
    main.corrections.title,
    main.corrections.artist,
    main.corrections.album
FROM main.corrections
LEFT JOIN ext.corrections ON ext.corrections.track_uri = main.corrections.track_uri
WHERE ext.corrections.track_uri IS NULL
"""
load_only_in_ext_query = """
SELECT
    ext.corrections.track_uri,
    ext.corrections.title,
    ext.corrections.artist,
    ext.corrections.album
FROM ext.corrections
LEFT JOIN main.corrections ON main.corrections.track_uri = ext.corrections.track_uri
WHERE main.corrections.track_uri IS NULL
"""


class DataMismatchChoiceEnum(enum.Enum):
    CHOOSE_INTERNAL = enum.auto()
    CHOOSE_EXTERNAL = enum.auto()
    MANUAL_EDIT = enum.auto()
    SKIP_TRACK = enum.auto()


class DataMismatchCounterEnum(enum.Enum):
    UPDATE = enum.auto()
    SKIP = enum.auto()


choice_choose_internal = questionary.Choice(
    title="Use Internal Values",
    value=DataMismatchChoiceEnum.CHOOSE_INTERNAL,
)
choice_choose_external = questionary.Choice(
    title="Use External Values",
    value=DataMismatchChoiceEnum.CHOOSE_EXTERNAL,
)
choice_manual_edit = questionary.Choice(
    title="Manually Edit Values",
    value=DataMismatchChoiceEnum.MANUAL_EDIT,
)
choice_skip = questionary.Choice(
    title="Skip Track",
    value=DataMismatchChoiceEnum.SKIP_TRACK,
)


def make_differ_table(result) -> Table:
    table = Table(title=result["track_uri"], show_footer=False, box=box.HEAVY_HEAD, show_lines=True)
    table.add_column(header="", style="bold")
    table.add_column(header="Internal")
    table.add_column(header="External")
    table.add_row("Title", result["main_title"], result["ext_title"])
    table.add_row("Artist", result["main_artist"], result["ext_artist"])
    table.add_row("Album", result["main_album"], result["ext_album"])
    return table


def run(args: Namespace, config):
    verify_external_db(args.external_db, config)
    db = connect_internal_db(config)
    attach_external_db(db, args.external_db)

    differ_counter: Counter[DataMismatchCounterEnum] = Counter()
    try:
        sync_both_differ(db, differ_counter, include_filesystem_uris=args.include_filesystem_uris)
    finally:
        updated_count = differ_counter.get(DataMismatchCounterEnum.UPDATE)
        if updated_count > 0:
            stdout.print(f"Updated {updated_count} entries!", style="success")
        else:
            stdout.print("No entries were updated.", style="notice")
        skipped_count = differ_counter.get(DataMismatchCounterEnum.SKIP)
        if skipped_count > 0:
            stdout.print(f"Skipped {skipped_count} entries.", style="notice")

    sync_only_in_main(db, include_filesystem_uris=args.include_filesystem_uris)
    sync_only_in_ext(db, include_filesystem_uris=args.include_filesystem_uris)

    stdout.print("Success!", style="success")
    return 0


def sync_both_differ(
    db: Connection,
    counter: Counter[DataMismatchCounterEnum],
    *,
    include_filesystem_uris: bool = False,
):
    stdout.print(
        "Synchronising differences between existing entries in both databases.", style="notice"
    )

    results = db.execute(load_both_differ_query)
    for result in results:
        track_uri = result["track_uri"]
        parsed_track_uri = urlparse(track_uri)
        if not parsed_track_uri.scheme:
            stderr.print(
                f"Invalid track URI found in internal corrections database: {track_uri}",
                style="warning",
            )
            continue
        elif parsed_track_uri.scheme in ("file", "local"):
            if not include_filesystem_uris:
                continue

        table = make_differ_table(result)
        stdout.print(table)

        response = questionary.select(
            message="",
            choices=(choice_choose_internal, choice_choose_external, choice_manual_edit),
        ).ask()
        if response is None:
            raise AbortCommand

        if response == DataMismatchChoiceEnum.CHOOSE_INTERNAL:
            update_ext_from_main(db, result)
        elif response == DataMismatchChoiceEnum.CHOOSE_EXTERNAL:
            update_main_from_ext(db, result)
        elif response == DataMismatchChoiceEnum.MANUAL_EDIT:
            while True:
                title, artist, album = edit_values(result)
                if questionary.confirm("Empty album correct?", auto_enter=False).ask():
                    break
            update_both(db, track_uri, title, artist, album)
        elif response == DataMismatchChoiceEnum.SKIP_TRACK:
            counter.incr(DataMismatchCounterEnum.SKIP)
            continue
        else:
            stderr.print("Unrecognised option.", style="error")
            raise AbortCommand

        counter.incr(DataMismatchCounterEnum.UPDATE)


def update_ext_from_main(db: Connection, result):
    db.execute(
        update_correction_query.format("ext"),
        (result["main_title"], result["main_artist"], result["main_album"], result["track_uri"]),
    )


def update_main_from_ext(db: Connection, result):
    db.execute(
        update_correction_query.format("main"),
        (result["ext_title"], result["ext_artist"], result["ext_album"], result["track_uri"]),
    )


def update_both(db: Connection, track_uri: str, title: str, artist: str, album: str):
    with db:
        db.execute("BEGIN")
        db.execute(
            update_correction_query.format("main"),
            (title, artist, album, track_uri),
        )
        db.execute(
            update_correction_query.format("ext"),
            (title, artist, album, track_uri),
        )


def edit_values(result) -> Tuple[str, str, str]:
    title = ""
    while title == "":
        if result["main_title"] == result["ext_title"]:
            default = result["main_title"]
        else:
            default = ""
        title = questionary.text(
            "Title:",
            default=default,
            completer=FuzzyWordCompleter([result["main_title"], result["ext_title"]]),
        ).ask()
        if title is None:
            raise AbortCommand
        title = title.strip()

    artist = ""
    while artist == "":
        if result["main_artist"] == result["ext_artist"]:
            default = result["main_artist"]
        else:
            default = ""
        artist = questionary.text(
            "Artist:",
            default=default,
            completer=FuzzyWordCompleter([result["main_artist"], result["ext_artist"]]),
        ).ask()
        if artist is None:
            raise AbortCommand
        artist = artist.strip()

    while True:
        if result["main_album"] == result["ext_album"]:
            default = result["main_album"]
        else:
            default = ""
        album = questionary.text(
            "Album:",
            default=default,
            completer=FuzzyWordCompleter([result["main_album"], result["ext_album"]]),
        ).ask()
        if album is None:
            raise AbortCommand
        album = album.strip()
        if album != "":
            break
        if questionary.confirm("Are you sure?", auto_enter=False).ask():
            break

    return title, artist, album


def sync_only_in_main(db: Connection, *, include_filesystem_uris: bool = False) -> int:
    stdout.print("Copying entries only in internal database to external database.", style="notice")
    insert_query = "INSERT INTO ext.corrections (track_uri, title, artist, album)"
    query = f"{insert_query} {load_only_in_main_query}"
    if not include_filesystem_uris:
        query += (
            " AND main.corrections.track_uri NOT LIKE 'file:%'"
            " AND main.corrections.track_uri NOT LIKE 'local:%'"
        )
    cursor = db.execute(query)

    entry_count = cursor.rowcount
    if entry_count > 0:
        stdout.print(f"Copied {entry_count} entries!", style="success")
    else:
        stdout.print("No entries were copied.", style="notice")

    return entry_count


def sync_only_in_ext(db: Connection, *, include_filesystem_uris: bool = False) -> int:
    stdout.print("Copying entries only in external database to internal database.", style="notice")
    insert_query = "INSERT INTO main.corrections (track_uri, title, artist, album)"
    query = f"{insert_query} {load_only_in_ext_query}"
    if not include_filesystem_uris:
        query += (
            " AND ext.corrections.track_uri NOT LIKE 'file:%'"
            " AND ext.corrections.track_uri NOT LIKE 'local:%'"
        )
    cursor = db.execute(query)

    entry_count = cursor.rowcount
    if entry_count > 0:
        stdout.print(f"Copied {entry_count} entries!", style="success")
    else:
        stdout.print("No entries were copied.", style="notice")

    return entry_count


__all__ = ("run",)
