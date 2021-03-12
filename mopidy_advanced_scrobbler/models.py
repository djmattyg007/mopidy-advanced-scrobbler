from __future__ import annotations

import dataclasses
from dataclasses_json import dataclass_json, LetterCase
from enum import IntEnum
from music_metadata_filter.filter import MetadataFilter
from music_metadata_filter.filters import make_spotify_filter, make_remastered_filter
from typing import Mapping, Optional
from urllib.parse import urlparse

from mopidy.models import Track


metadata_filters_mapping: Mapping[str, MetadataFilter] = {
    "spotify": make_spotify_filter(),
    "local": make_remastered_filter(),
}


class Corrected(IntEnum):
    NOT_CORRECTED = 0
    MANUALLY_CORRECTED = 1
    AUTO_CORRECTED = 2


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass(frozen=True)
class Play(object):
    track_uri: str
    artist: str
    title: str
    album: str
    corrected: Corrected
    musicbrainz_id: Optional[str]
    duration: int  # Number of seconds
    played_at: int  # UNIX timestamp
    submitted_at: Optional[int]  # UNIX timestamp


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass(frozen=True)
class RecordedPlay(Play):
    play_id: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass(frozen=True)
class PlayEdit(object):
    play_id: int
    track_uri: str
    title: str
    artist: str
    album: str
    save_correction: bool
    update_all_unsubmitted: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass(frozen=True)
class Correction(object):
    track_uri: str
    artist: str
    title: str
    album: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass(frozen=True)
class CorrectionEdit(object):
    track_uri: str
    artist: str
    title: str
    album: str
    update_all_unsubmitted: bool


play_schema = Play.schema()
recorded_play_schema = RecordedPlay.schema()
play_edit_schema = PlayEdit.schema()
correction_schema = Correction.schema()


def prepare_play(track: Track, played_at: int, correction: Optional[Correction]) -> Play:
    track_uri = track.uri
    if correction:
        artist = correction.artist
        title = correction.title
        album = correction.album or ""
        corrected = Corrected.MANUALLY_CORRECTED
    else:
        artist, title, album = format_track_data(track)
        corrected = Corrected.NOT_CORRECTED

        track_uri_parsed = urlparse(track_uri)
        metadata_filter = metadata_filters_mapping.get(track_uri_parsed.scheme, None)
        if metadata_filter:
            artist, title, album, corrected = apply_metadata_filter(metadata_filter, artist, title, album)

    data = {
        "track_uri": track_uri,
        "artist": artist,
        "title": title,
        "album": album,
        "corrected": corrected,
    }

    if track.musicbrainz_id:
        data["musicbrainz_id"] = track.musicbrainz_id
    else:
        data["musicbrainz_id"] = None

    if track.length:
        data["duration"] = track.length // 1000
    else:
        data["duration"] = 0

    data["played_at"] = played_at
    data["submitted_at"] = None

    return Play.from_dict(data)


def format_track_data(track: Track):
    artist_names = []
    for artist in track.artists:
        if artist.name:
            artist_name = artist.name.strip()
            if artist_name:
                artist_names.append(artist_name)

    artist = ", ".join(sorted(artist_names))
    title = track.name or ""
    if track.album and track.album.name:
        album = track.album.name
    else:
        album = ""

    return artist, title, album


def apply_metadata_filter(metadata_filter: MetadataFilter, orig_artist: str, orig_title: str, orig_album: str):
    artist = metadata_filter.filter_field("artist", orig_artist)
    title = metadata_filter.filter_field("track", orig_title)
    album = metadata_filter.filter_field("album", orig_album)

    if artist != orig_artist or title != orig_title or album != orig_album:
        corrected = Corrected.AUTO_CORRECTED
    else:
        corrected = Corrected.NOT_CORRECTED

    return artist, title, album, corrected
