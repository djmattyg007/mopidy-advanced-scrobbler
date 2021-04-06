*************************
Mopidy-Advanced-Scrobbler
*************************

Mopidy extension for comprehensive management of `Last.fm <https://last.fm>`_ scrobbles.

This extension requires a free user account at Last.fm.


About
=====

This extension aims to provide advanced scrobbling functionality above and beyond
what the existing Mopidy Scrobbler extension provides:

- Caching scrobbles in case no internet connection is available
- Delete scrobbles before they're submitted
- Automatic cleaning of song metadata (provided by
  `music-metadata-filter <https://github.com/djmattyg007/music-metadata-filter>`_ package)
- Manually edit song metadatad
- Completely ignore tracks played by specific extensions

**Important**: Out of the box, this extension won't automatically scrobble the
songs you're listening to. Instead, it will record them so that you can scrobble
them yourself later. Please refer to the Usage section later on in the readme.

I might add automatic scrobbling at a later date. If you're considering a PR to
add this functionality, please open an issue first to discuss the implementation.


Installation
============

Install by running::

    sudo python3 -m pip install Mopidy-Advanced-Scrobbler


Configuration
=============

The extension is enabled by default when it is installed. However, to actually
make use of the ability to scrobble, you'll need to provide several details. In
addition to providing your Last.fm username and password, you'll also need to
create an API account:

https://www.last.fm/api/account/create

Then fill out your credentials in the Mopidy configuration file::

    [advanced_scrobbler]
    api_key = bf572286a9ea25a28b9c896b03b7176e
    api_secret = f89e3f3cf54ee6f248d55dac328d4bc0
    username = djmattyg007
    password = secret

The following configuration values are available:

- ``advanced_scrobbler/enabled``: If the Advanced Scrobbler extension should be
  enabled or not. Defaults to enabled.
- ``advanced_scrobbler/api_key``: The API account's API key.
- ``advanced_scrobbler/api_secret``: The API account's API secret.
- ``advanced_scrobbler/username``: Your Last.fm username.
- ``advanced_scrobbler/password``: Your Last.fm password.
- ``advanced_scrobbler/db_timeout``: Database connection timeout in seconds.
- ``advanced_scrobbler/scrobble_time_threshold``: The amount of a song that must
  have been listened, as a percentage. Valid values are between 50 and 100.
  Defaults to 50.
- ``advanced_scrobbler/ignored_uri_schemes``: A list of track URI schemes that
  should be completely ignored. No record will ever be submitted or recorded for
  tracks coming from these extensions. Defaults to an empty list.


Usage
=====

Enter the address of the Mopidy server that you are connecting to in your browser
(e.g. http://localhost:6680/advanced_scrobbler).

There are two main pages: "Plays" and "Corrections". The "Plays" page contains a
list of every track you've listened to, and when it was listened to. It also notes
if track metadata has been altered from what was originally provided, and if so,
what it was before it was altered.

From this page you can also edit track metadata, delete plays individually or in
bulk, and scrobble tracks individually or in bulk. Selecting "Scrobble to here"
will ensure all plays recorded up to and including the selected play are scrobbled,
leaving any plays recorded after the selected play.

While editing track metadata, you can decide to save the edit permanently as a
manual correction. If the same track is played in future, this manual correction
will be automatically applied when recording the play. You can also decide to
automatically update any other plays of the same track that have not yet been
submitted. If a track's metadata was corrected automatically, you will also have
the option of "approving" the automatic correction. This will convert it into a
manual correction for you.

The "Corrections" page simply lists all existing manual corrections. On this page,
corrections can be edited or deleted.


Project resources
=================

- `Source code <https://github.com/djmattyg007/mopidy-advanced-scrobbler>`_
- `Issue tracker <https://github.com/djmattyg007/mopidy-advanced-scrobbler/issues>`_
- `Changelog <https://github.com/djmattyg007/mopidy-advanced-scrobbler/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `djmattyg007 <https://github.com/djmattyg007>`_
- Current maintainer: `djmattyg007 <https://github.com/djmattyg007>`_
- `Contributors <https://github.com/djmattyg007/mopidy-advanced-scrobbler/graphs/contributors>`_
