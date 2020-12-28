BEGIN EXCLUSIVE TRANSACTION;

PRAGMA user_version = 1;

CREATE TABLE plays (
    play_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_uri TEXT NOT NULL,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT NOT NULL,
    musicbrainz_id TEXT NOT NULL,
    duration INTEGER NOT NULL,
    played_at INTEGER NOT NULL,
    submitted_at INTEGER DEFAULT NULL
)

CREATE TABLE corrections (
    track_uri TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT NOT NULL
)

END TRANSACTION;
