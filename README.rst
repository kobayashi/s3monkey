pyS3fs: Access your S3 buckets like they're native files
========================================================

Platforms like `Heroku <https://heroku.com/>`_ don't allow for FUSE filesystem
usage, so I had to get a bit creative.

Introducing, **pyS3fs**, a library that mocks out all standard Python library
system file operations, allowing you to use already–written code to interface
with Amazon S3.

All standard library file operation modules are patched when using the provided
context manager, including ``os``, ``io``, & ``pathlib``.

Usage
-----

``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` are expected to be set::

    $ AWS_ACCESS_KEY_ID=xxxxxxxxxxx
    $ AWS_SECRET_ACCESS_KEY=xxxxxxxxxxx

Create a ``test`` key on S3, with the contents of ``hello``::

    with S3FS(bucket_name='media.kennethreitz.com', mount_point='/app/data') as fs:

        with open('/app/data/test', 'w') as f:
            f.write('hello')

