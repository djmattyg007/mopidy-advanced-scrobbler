from __future__ import annotations

import dataclasses
from dataclasses_json import dataclass_json, LetterCase
from enum import IntEnum
from typing import Optional

from mopidy.models import Track


# TODO: Add "not corrected but verified" status
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
    if correction:
        artist = correction.artist
        title = correction.title
        corrected = Corrected.MANUALLY_CORRECTED
    else:
        artist_names = []
        for artist in track.artists:
            if artist.name:
                artist_name = artist.name.strip()
                if artist_name:
                    artist_names.append(artist_name)

        artist = ", ".join(sorted(artist_names))
        title = track.name or ""
        corrected = Corrected.NOT_CORRECTED

    data = {
        "track_uri": track.uri,
        "artist": artist,
        "title": title,
        "corrected": corrected,
    }

    if correction:
        data["album"] = correction.album or ""
    elif track.album and track.album.name:
        data["album"] = track.album.name
    else:
        data["album"] = ""

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
