FUSE-based Filesystem for SimpleNote
====================================
`SimpleNote <http://simplenoteapp.com/>`_ is a set of applications and a
service that stores simple textual notes.

SimpleNoteFS is a FUSE-based filesystem for accessing these notes.

Caveat Emptor
-------------
As of this writing the SimpleNote API doesn't have a means to query useful
notes metadata like the title and note size. This means that to provide a
directory listing SimpleNoteFS must perform a full retrieval of all notes,
making startup quite slow.
