import dataclasses
from enum import IntEnum
from typing import Optional

from mopidy.models import Track


class Corrected(IntEnum):
    NOT_CORRECTED = 0
    MANUALLY_CORRECTED = 1
    AUTO_CORRECTED = 2


@dataclasses.dataclass(frozen=True)
class Play(object):
    track_uri: str
    artist: str
    title: str
    album: str
    corrected: Corrected
    musicbrainz_id: Optional[str]
    duration: int
    played_at: int
    submitted_at: Optional[int]


@dataclasses.dataclass(frozen=True)
class RecordedPlay(Play):
    play_id: int


@dataclasses.dataclass(frozen=True)
class Correction(object):
    track_uri: str
    artist: str
    title: str
    album: str


def prepare_play(track: Track, correction: Correction, played_at: int) -> Play:
    if correction:
        artist = correction.artist
        title = correction.title
        corrected = Corrected.MANUALLY_CORRECTED
    else:
        artist = ", ".join(sorted([artist.name for artist in track.artists]))
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

    return Play(**data)
