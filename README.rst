FUSE-based Filesystem for SimpleNote
====================================
`SimpleNote <http://simplenoteapp.com/>`_ is a set of applications and a
service that stores simple textual notes.

SimpleNoteFS is a FUSE-based filesystem for accessing these notes. It's quite
experimental, and it's possible it will delete or otherwise mangle your notes.
So beware.

Installation
------------
Requires FUSE + the `FUSE Python bindings
<http://pypi.python.org/pypi/fuse-python/0.2>`_. It can optionally use `keyring
<http://pypi.python.org/pypi/keyring>`_ to store your SimpleNote credentials.

Caveat Emptor
-------------
As of this writing the SimpleNote API doesn't have a means to query just note
metadata like the title and note size. This means that to provide a directory
listing SimpleNoteFS must perform a full retrieval of all notes, making startup
quite slow.
