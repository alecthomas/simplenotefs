#!/usr/bin/env python

try:
    import keyring
except ImportError:
    keyring = None

from collections import defaultdict
from datetime import datetime
from getpass import getpass
from optparse import OptionParser
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time, mktime
import errno
import os
errno.ENOATTR = 93

from fuse import FUSE, Operations, LoggingMixIn
from simplenote import Simplenote


class SimpleNoteFS(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""

    def __init__(self, api):
        self.api = api
        # A mapping from keys to "file names"
        self.fd = 0
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.mode = 0600
        #self.icon = open('simplenote.icns', 'rb').read()
        self._files = {}

    @property
    def files(self):
        if not self._files:
            for entry in self.api.index():
                if entry['deleted']:
                    continue
                note = self.api.get_note(entry['key'])
                filename = note['content'].decode('utf-8').splitlines()
                if filename:
                    filename = filename[0].strip()
                    self._files['/' + filename.encode('utf-8') + '.txt'] = note
        return self._files

    def valid_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        # Don't allow hidden files or non-.txt files
        return not path.startswith('.') and path.endswith('.txt')

    def create(self, path, mode):
        path = path[1:]
        if not self.valid_path(path):
            raise OSError(errno.EACCES, '')
        title, ext = os.path.splitext(path)
        key = self.api.create_note(title)
        now = datetime.now()
        self._files['/' + path] = {'content': title, 'created': now,
                                    'modified': now, 'key': key}
        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path == '/':
            return dict(st_mode=(S_IFDIR | self.mode), st_nlink=2, st_size=0,
                        st_ctime=time(), st_mtime=time(), st_atime=time(),
                        st_uid=self.uid, st_gid=self.gid)
#        elif path == '/.VolumeIcon.icns':
#            return dict(st_mode=(S_IFREG | 0400), st_nlink=1,
#                        st_size=len(self.icon), st_ctime=time(),
#                        st_mtime=time(), st_atime=time(),
#                        st_uid=self.uid, st_gid=self.gid)
        else:
            mode = S_IFREG
        if not self.valid_path(path):
            raise OSError(errno.EACCES, '')
        file = self.files.get(path, None)
        if not file:
            raise OSError(errno.ENOENT, '')
        ctime = mktime(file['created'].timetuple())
        mtime = mktime(file['modified'].timetuple())
        size = len(file['content'])
        return dict(st_mode=(mode | 0600), st_nlink=1, st_size=size,
                    st_ctime=ctime, st_mtime=mtime, st_atime=time(),
                    st_uid=self.uid, st_gid=self.gid)

    def mkdir(self, path, mode):
        # TODO Implement "search" folders?
        raise OSError(errno.ENOENT, '')

    def open(self, path, flags):
        print flags
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
#        if path == '/.VolumeIcon.icns':
#            data = self.icon
#        else:
        data = self.files[path]['content']
        return data[offset:offset + size]

    def readdir(self, path, fh):
        return ['.', '..'] + [file[1:] for file in self.files] # + ['.VolumeIcon.icns']

    def rename(self, old, new):
        self.files[new] = self.files.pop(old)

    def statfs(self, path):
        # TODO Make this show something useful
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        raise OSError(errno.EIO, '')

    def truncate(self, path, length, fh=None):
        pass

    def unlink(self, path):
        note = self.files.get(path, None)
        if not note:
            raise OSError(errno.ENOENT, '')
        self.api.delete_note(note['key'])
        del self.files[path]

    def write(self, path, data, offset, fh):
        note = self.files[path]
        note['content'] = note['content'][:offset] + data
        key = self.api.update_note(note['key'], note['content'])
        print key
        note['key'] = key
        note['modified'] = datetime.now()
        return len(data)


if __name__ == "__main__":
    if len(argv) != 2:
        print 'usage: %s <mountpoint>' % argv[0]
        exit(1)
    password = None
    email = raw_input('E-Mail address: ')
    if keyring:
        password = keyring.get_password('simplenotefs', email)
    if not password:
        password = getpass()
        if keyring:
            keyring.set_password('simplenotefs', email, password)
    api = Simplenote(email, password)
    fuse = FUSE(SimpleNoteFS(api), argv[1], foreground=True)
