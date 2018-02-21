import os
import sys

# Path hacking, for vendored pyfakefs.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import chardet
import bucketstore
from pyfakefs import fake_filesystem as fake_fs
from pyfakefs.fake_filesystem_unittest import Patcher
from pyfakefs import mox3_stubout, fake_filesystem, fake_pathlib, fake_filesystem_shutil


class S3Patcher(Patcher):
    """docstring for S3Patcher"""
    def __init__(self, filesystem):
        super(S3Patcher, self).__init__()
        self.fs = filesystem

    def _refresh(self):
        if self._stubs is not None:
            self._stubs.smart_unset_all()
        self._stubs = mox3_stubout.StubOutForTesting()

        for name in self._fake_module_classes:
            self._fake_modules[name] = self._fake_module_classes[name](self.fs)
        self._fake_modules['path'] = self._fake_modules['os'].path
        self.fake_open = fake_filesystem.FakeFileOpen(self.fs)

        self._isStale = False


class WrittenS3File(fake_fs.FakeFileWrapper):
    """A File to be written to Amazon S3."""
    def __init__(self, *args, **kwargs):
        self.filesystem = kwargs['filesystem']
        super(WrittenS3File, self).__init__(*args, **kwargs)

    def upload(self):
        """Uploads the key to Amazon S3."""
        self._io.seek(0)
        self.filesystem.bucket[self.key] = self._io.read()

    def close(self):
        """Close the file."""
        # ignore closing a closed file
        if not self._is_open():
            return

        self.upload()

        # for raw io, all writes are flushed immediately
        if self.allow_update and not self.raw_io:
            self.flush()
        if self._closefd:
            self._filesystem._close_open_file(self.filedes)
        else:
            self._filesystem.open_files[self.filedes].remove(self)
        if self.delete_on_close:
            self._filesystem.remove_object(self.get_object().path)


class S3File(fake_fs.FakeFile):
    """docstring for S3File"""

    def __init__(self, key, filesystem):
        self.key = key
        super(S3File, self).__init__(self.key.name, filesystem=filesystem)

    def IsLargeFile(self):
        return False

    @property
    def byte_contents(self):
        data = self.key.get()

        self.set_contents(data, encoding=chardet.detect(data))
        return data

    @property
    def contents(self):
        return self.byte_contents

    @property
    def contents(self):
        return self.key.get()

    def __repr__(self):
        return "<S3File {}>".format(self.key)


class S3FS(fake_fs.FakeFilesystem):
    """A Mocked S3 Filesystem."""

    def __init__(self, bucket, mount_point, other_dirs=None, **kwargs):
        super(S3FS, self).__init__()
        self.bucket_name = bucket
        self.bucket = bucketstore.get(self.bucket_name, **kwargs)
        self.mount_point = mount_point
        self.patcher = S3Patcher(filesystem=self)

        if not other_dirs:
            other_dirs = ['.']

            for _dir in other_dirs:
                _dir = os.path.abspath(_dir)

                self.add_real_directory(
                    source_path=_dir,
                    read_only=True,
                    lazy_read=True
                )

        self.keys = []

        # Create the mount point.
        self.CreateDirectory(mount_point)

        self.refresh()

    def __enter__(self):
        self.patcher.setUp()
        self.patcher.fs = self
        return self

    def __exit__(self, type, value, traceback):
        self.patcher.tearDown()

    def add_key(self, key):
        self.keys.append(key)

        file = S3File(key=self.bucket.key(key), filesystem=self)
        self.AddObject(file_path=self.mount_point, file_object=file)

    def remove_key(self, key):
        del self.keys[self.keys.index(key)]
        self.RemoveObject(file_path='{}/{}'.format(self.mount_point, key))

    def refresh(self):
        for key in self.keys:
            try:
                self.remove_key(key)
            except (FileNotFoundError, NotADirectoryError):
                pass

        for key in self.bucket.list():
            try:
                self.add_key(key)
            except FileExistsError:
                pass

    def open_callback(self, locals):
        # Return a WrittenS3File class if things match up.
        if 'w' in locals['mode'] and locals['file_'].startswith(self.mount_point):
            key = locals['file_'][len('{}/'.format(self.mount_point)):]
            return WrittenS3File, key
        else:
            return None, None
