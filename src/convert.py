from gcsfs import GCSFileSystem
from gcsfs.mapping import GCSMap
from h5py import Dataset, File, Group
from s3fs import S3FileSystem
from s3fs.mapping import S3Map
import os
import sys
import zarr

from scanpy.api import read_10x_h5, read_loom

from os.path import splitext

import re
from urllib.parse import urlparse


def exists(uri):
    p = urlparse(uri)
    if p.scheme == 'gs':
        fs = GCSFileSystem()
        fs.exists(uri)
    elif p.scheme == 's3':
        fs = S3FileSystem()
        fs.exists(uri)
    elif not p.scheme:
        os.path.exists(uri)
    else:
        raise Exception('Unrecognized scheme %s in URL %s' % (p.scheme, uri))


def make_store(path):
    m = re.match('^gc?s://', path)
    if m:
        gcs = GCSFileSystem()
        return GCSMap(path[len(m.group(0)):], gcs=gcs)

    if path.startswith('s3://'):
        s3 = S3FileSystem()
        return S3Map(path[len('s3://')], s3=s3)

    return zarr.DirectoryStore(path)


def build_chunks_map(o, chunk_size, axis = 0):
    if isinstance(o, Group) or isinstance(o, File):
        r = {}
        for k, v in o.items():
            r[k] = build_chunks_map(v, chunk_size)
        return r
    elif isinstance(o, Dataset):
        shape = o.shape
        elems_per_main_axis_entry = o.size // shape[axis]
        size_per_main_axis_entry = elems_per_main_axis_entry * o.dtype.itemsize
        main_axis_entries_per_chunk = chunk_size // size_per_main_axis_entry
        chunks = list(shape)
        chunks[axis] = main_axis_entries_per_chunk
        return tuple(chunks)
    else:
        raise Exception('Unrecognized HDF5 object: %s' % f)


def convert(
        input,
        output,
        chunk_size=16 * 1024 * 1024,
        genome=None,
        overwrite=False
):
    if exists(output) and not overwrite:
        raise Exception(
            'Output path already exists: %s; use --overwrite/-f to overwrite' % output
        )

    input_path, input_ext = splitext(input)
    output_path, output_ext = splitext(output)

    print('converting: %s to %s' % (input, output))

    if output_ext == '.zarr':

        if input_ext == '.h5' or input_ext == '.loom' or input_ext == '.h5ad':
            # Convert 10x (HDF5) to Zarr
            source = File(input, 'r')
            zarr.tree(source)

            chunks_map = build_chunks_map(source, chunk_size)

            print('converting %s to %s, with uncompressed-chunk-sizes of %d' % (input, output, chunk_size))

            store = make_store(output)
            dest = zarr.group(store=store, overwrite=overwrite)

            zarr.copy_all(
                source,
                dest,
                log=sys.stdout,
                # possibly related to https://github.com/h5py/h5py/issues/973
                without_attrs=(input_ext != '.h5'),
                chunks=chunks_map
            )
            zarr.tree(dest)
        else:
            raise Exception('Unrecognized input extension: %s' % input_ext)

    elif output_ext == '.h5ad':
        if input_ext == '.h5':
            if not genome:
                keys = list(File(input).keys())
                if len(keys) == 1:
                    genome = keys[0]
                else:
                    raise Exception(
                        'Set --genome flag when converting from 10x HDF5 (.h5) to Anndata HDF5 (.h5ad); top-level groups in file %s: %s'
                        % (input, ','.join(keys))
                    )
            adata = read_10x_h5(input, genome=genome)

            # TODO: respect overwrite flag
            adata.write(output)
        elif input_ext == '.loom':
            # reads the whole dataset in memory!
            adata = read_loom(input)
            adata.write(output)
        else:
            raise Exception('Unrecognized input extension: %s' % input_ext)

    else:
        raise Exception('Unrecognized output extension: %s' % output_ext)

