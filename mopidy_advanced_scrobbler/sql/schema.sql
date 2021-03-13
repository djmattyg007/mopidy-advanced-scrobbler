BEGIN EXCLUSIVE TRANSACTION;

PRAGMA user_version = 1;

CREATE TABLE plays (
    play_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_uri TEXT NOT NULL,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT NOT NULL,
    orig_artist TEXT NOT NULL,
    orig_title TEXT NOT NULL,
    orig_album TEXT NOT NULL,
    corrected INTEGER NOT NULL DEFAULT 0,
    musicbrainz_id TEXT DEFAULT NULL,
    duration INTEGER NOT NULL,
    played_at INTEGER NOT NULL,
    submitted_at INTEGER DEFAULT NULL
);

CREATE TABLE corrections (
    track_uri TEXT PRIMARY KEY,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT NOT NULL
);

END TRANSACTION;
