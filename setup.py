import os
import warnings

from setuptools import setup

# Nice big warning
WARNING_TMPL = """File {filename} is not present! Try running 'make' first.

    MISSING FILE: {filename}
    This data file is not present or is not readable, so it has not been
    included in the distribution.
"""

FILE_SPEC = [("share/man/man1", ["data/renumber.1.gz"])]


def data_files(file_spec):
    for dest_dir, files in file_spec:
        readable = []
        for filename in files:
            if os.access(filename, os.R_OK):
                readable.append(filename)
            else:
                warnings.warn(WARNING_TMPL.format(filename=filename))
        if readable:
            yield (dest_dir, readable)


setup(
    data_files=list(data_files(FILE_SPEC))
)
