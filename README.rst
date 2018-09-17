s3monkey: Access your S3 buckets like they're native files
==========================================================

Platforms like `Heroku <https://heroku.com/>`_ don't allow for FUSE filesystem
usage, so I had to get a bit creative.

Introducing, **s3monkey**, a library that mocks out all standard Python library
system file operations, allowing you to use already–written code to interface
with Amazon S3.

All standard library file operation modules are patched when using the provided
context manager, including the built–in ``open``, ``os``, ``io``, & ``pathlib``.

If you're interested in financially supporting Kenneth Reitz open source, consider `visiting this link <https://cash.me/$KennethReitz>`_. Your support helps tremendously with sustainability of motivation, as Open Source is no longer part of my day job.


Potential Use Cases
-------------------

- Running Jupyter Notebooks on non-persistient storage (still being worked out).
- Storing user uploads for Django applications (e.g. the ``media`` folder). 

Usage
-----

``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` are expected to be set:

.. code-block:: shell

    $ AWS_ACCESS_KEY_ID=xxxxxxxxxxx
    $ AWS_SECRET_ACCESS_KEY=xxxxxxxxxxx

Basic usage:

.. code-block:: python

    from s3monkey import S3FS

    with S3FS(bucket='media.kennethreitz.com', mount_point='/app/data') as fs:

        # Create a 'test' key on S3, with the contents of 'hello'.
        with open('/app/data/test', 'w') as f:
            f.write('hello')

        # List the keys in the S3 bucket.
        print(os.listdir('/app/data'))
        # ['file1.txt', 'file2.txt', 'file2.txt', 'test', …]

Installation
------------

.. code-block:: shell

    $ pipenv install s3monkey

This module only supports Python 3.
