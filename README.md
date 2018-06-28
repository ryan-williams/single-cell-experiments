# Single Cell Experiments

Experiments to run single cell analyses efficiently at scale. Using a
combination of [Zarr], [anndata], [Scanpy], and [Apache Spark] -- and possibly
other things too.

The work in this repository is exploratory and not suitable for production.

## Overview

### [`src/anndata`](src/anndata)
- a git submodule for [tomwhite/anndata](https://github.com/tomwhite/anndata)
- WIP support for [AnnData] backed by [Zarr]

### [`src/scanpy`](src/scanpy)
- [`AnnDataRdd`](src/scanpy/anndata_spark.py): [AnnData] implementation backed by a [Spark RDD](https://spark.apache.org/docs/2.3.1/rdd-programming-guide.html#resilient-distributed-datasets-rdds)
- [`scanpy_spark.py`](src/scanpy/scanpy_spark.py): some [ScanPy] function implemented for `AnnDataRdd`s

### [`cli.py`](./cli.py)
A command-line interface for converting between various HDF5 formats (10X's, [Loom], [AnnData]) and [Zarr] equivalents:

```
# Download a 10X HDF5 file locally
wget -O files/ica_cord_blood_h5.h5 https://storage.googleapis.com/ll-sc-data/hca/immune-cell-census/ica_cord_blood_h5.h5

# Convert to .h5ad
python cli.py files/ica_cord_blood_h5.h5 files/ica_cord_blood.h5ad

# Convert to .zarr
python cli.py files/ica_cord_blood.h5ad files/ica_cord_blood.h5ad.zarr
```

`.zarr` outputs can also be written directly to `gs://` and `s3://` URLs.


## Testing

Create and activate a Python 3 virtualenv, and install the requirements:

```
python3 -m virtualenv venv  # python 3 is required!
. venv/bin/activate
pip install -r requirements.txt
```

Install and configure Spark 2.3.1:

```
wget http://www-us.apache.org/dist/spark/spark-2.3.1/spark-2.3.1-bin-hadoop2.7.tgz
tar xf spark-2.3.1-bin-hadoop2.7.tgz
export SPARK_HOME=spark-2.3.1-bin-hadoop2.7
```

Run Tests:

```
python src/scanpy/test_scanpy_spark.py
```

### Troubleshooting

#### Error:

```
socket.gaierror: [Errno 8] nodename nor servname provided, or not known
```

#### Fix:
You [likely need to add a mapping for 127.0.0.1 to your `/etc/hosts`](https://stackoverflow.com/a/41231625):

```
echo '127.0.0.1    localhost' | sudo tee /etc/hosts >> /dev/null
```

#### Error:

```
  …
  File "/Users/ryan/c/hdf5-experiments/test/lib/python3.6/site-packages/pyspark/java_gateway.py", line 93, in launch_gateway
    raise Exception("Java gateway process exited before sending its port number")
Exception: Java gateway process exited before sending its port number
```

#### Fix:

```
export SPARK_LOCAL_IP=127.0.0.1
```

#### In IntelliJ:

You may need to additionally set the `PYSPARK_PYTHON` environment variable in your test configuration (to the `venv/bin/python` binary from your virtualenv above), otherwise workers will use a different/incompatible Python.

Sample configuration:

![](https://cl.ly/241w3k0d1f2d/Screen%20Shot%202018-06-27%20at%205.44.28%20PM.png)

Env vars:

![](https://cl.ly/0K0n0H132d3k/Screen%20Shot%202018-06-27%20at%205.45.12%20PM.png)


## People
- [Tom White](https://github.com/tomwhite/)
- [Ryan Williams](https://github.com/ryan-williams)
- [Uri Laserson](https://github.com/laserson)


[Zarr]: http://zarr.readthedocs.io/en/stable/
[anndata]: http://anndata.readthedocs.io/en/latest/
[Scanpy]: http://scanpy.readthedocs.io/en/latest/
[Apache Spark]: https://spark.apache.org/
[Loom]: http://loompy.org/