# &mu;proot

&mu;proot (micro-Python ROOT) is an experiment to see how little is needed to read data from a ROOT file. &mu;proot has no dependencies other than Python and Numpy— and the [LZMA](https://pypi.python.org/pypi/backports.lzma) and [LZ4](https://pypi.python.org/pypi/lz4) libraries if you read ROOT files with these compression options enabled (you would be prompted with instructions if this is the case; note that Python 3.3+ has LZMA support built-in). You do not need to have the C++ version of ROOT installed to use &mu;proot.

It is important to note that &mu;proot is _not_ maintained by the [ROOT project team](https://root.cern/), and it is not a fully featured ROOT replacement. It is a file format library, intended to make ROOT files accessible in environments where it is difficult to deploy ROOT. Compare to h5py, which only reads HDF5 files, or parquet-python, which only reads Parquet files.

&mu;proot is just ROOT I/O.

## Scope

The primary goal of &mu;proot is to present data from ROOT files as Numpy arrays, making them accessible to any scientific Python projects based on Numpy (i.e. all of them). Reading and decompression are lazy, so &mu;proot benefits from the same selective reading as ROOT— you only have to wait for the branches you're interested in. Since most of the time is spent loading data from disk/network, decompression, and Numpy/Numba calculations, &mu;proot can be as fast as reading your ROOT file in C++.

[**TODO:** performance plots]

## Status and goals

&mu;proot currently reads flat ROOT TTrees into Numpy arrays (in less than 1000 lines of Python code). The following are in scope:

   * reading fully split, [structured objects into PLUR](https://github.com/diana-hep/plur);
   * writing flat ROOT TTrees;
   * reading a few basic types of non-TTree objects, relelvant for analysis, such as histograms and graphs;
   * import-on-demand connections to Pandas, Keras, TensorFlow, PySpark, etc.;
   * read/decompress TBaskets in parallel;
   * remotely access files through XRootD's Python interface;
   * conveniences for dealing with large sets of files (TChain equivalent).

## Acknowledgements

Conversations with Philippe Canal were essential for context, finding my way through 20 years of living codebase. Brian Bockelman's BulkIO additions to C++ ROOT also helped to clarify the distinction between I/O and interface. Also, Sebastien Binet's [go-hep](https://github.com/go-hep/hep) provided a clean implementation to ~~pillage~~ replicate.
