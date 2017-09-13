# uproot

uproot (or &mu;proot, for "micro-Python ROOT") is a demonstration of how little is needed to read data from a ROOT file. Only about a thousand lines of Python code can convert ROOT TTrees into Numpy arrays.

It is important to note that uproot is _not_ maintained by the [ROOT project team](https://root.cern/) and it is _not_ a fully featured ROOT replacement. Think of it as a file format library, analogous to h5py, parquet-python, or PyFITS. It just reads (and someday writes) files.

uproot has requires only Python and Numpy. The other packages listed below are merely recommended, as they unlock special features:

   * **Python 2.6, 2.7 or 3.4+** _(required)_
   * **Numpy 1.4+** _(required)_
   * **python-lzma** ([pip](https://pypi.python.org/pypi/backports.lzma), [conda](https://anaconda.org/conda-forge/backports.lzma)) if you want to read ROOT files compressed with LZMA and you're using Python 2 (lzma is part of Python 3's standard library)
   * **python-lz4** ([pip](https://pypi.python.org/pypi/lz4), [conda](https://anaconda.org/anaconda/lz4)) if you want to read ROOT files compressed with LZ4
   * **python-futures** ([pip](https://pypi.python.org/pypi/futures), [conda](https://anaconda.org/anaconda/futures)) if you want to read and/or decompress basket data in parallel and you're using Python 2 (futures is part of Python 3's standard library)
   * **pyxrootd** (no pip, [conda](https://anaconda.org/search?q=xrootd), [source](http://xrootd.org/dload.html)) if you want to access files with XRootD (`root://`) protocol. (Hint: if you install from source, you may have to set `PYTHONPATH` and `LD_LIBRARY_PATH`.)

You do not need C++ ROOT to run uproot.

## Examples

Load a tree from a file:

```python
>>> import uproot
>>> tree = uproot.open("tests/Zmumu.root")["events"]
>>> tree
<TTree 'events' len=2304 at 0x73c8a1191450>
```

Note that this one-liner would segfault in PyROOT because of a mismatch between ROOT's memory management and Python's. In uproot, there's only one memory manager, Python, and segfaults are extremely rare.

```python
>>> import ROOT
>>> tree = ROOT.TFile("tests/Zmumu.root").Get("events")
>>> tree
```

Next, get all the data as arrays (if you have enough memory):

```python
>>> for branchname, array in tree.arrays().items():
...     print("{}\t{}".format(branchname, array))
...
b'Q2'    [-1  1  1 ..., -1 -1 -1]
b'pz1'   [-68.96496181 -48.77524654 -48.77524654 ..., -74.53243061 -74.53243061
          -74.80837247]
b'Q1'    [ 1 -1 -1 ...,  1  1  1]
b'py1'   [ 17.4332439  -16.57036233 -16.57036233 ...,   1.19940578   1.19940578
            1.2013503 ]
b'E2'    [  60.62187459   82.20186639   81.58277833 ...,  168.78012134  170.58313243
           170.58313243]
b'Run'   [148031 148031 148031 ..., 148029 148029 148029]
b'eta2'  [-1.05139 -1.21769 -1.21769 ..., -1.4827  -1.4827  -1.4827 ]
b'Type'  [ 2 71 84 ...,  2 71 71]
b'pt2'   [ 38.8311  44.7322  44.7322 ...,  72.8781  72.8781  72.8781]
b'E1'    [ 82.20186639  62.34492895  62.34492895 ...,  81.27013558  81.27013558
           81.56621735]
b'pz2'   [ -47.42698439  -68.96496181  -68.44725519 ..., -152.2350181  -153.84760383
          -153.84760383]
b'pt1'   [ 44.7322  38.8311  38.8311 ...,  32.3997  32.3997  32.3997]
b'M'     [ 82.46269156  83.62620401  83.30846467 ...,  95.96547966  96.49594381
           96.65672765]
b'phi2'  [-0.440873  2.74126   2.74126  ..., -2.77524  -2.77524  -2.77524 ]
b'px1'   [-41.19528764  35.11804977  35.11804977 ...,  32.37749196  32.37749196
           32.48539387]
b'px2'   [ 34.14443725 -41.19528764 -40.88332344 ..., -68.04191497 -68.79413604
          -68.79413604]
b'Event' [10507008 10507008 10507008 ..., 99991333 99991333 99991333]
b'py2'   [-16.11952457  17.4332439   17.29929704 ..., -26.10584737 -26.39840043
          -26.39840043]
b'eta1'  [-1.21769 -1.05139 -1.05139 ..., -1.57044 -1.57044 -1.57044]
b'phi1'  [ 2.74126   -0.440873  -0.440873  ...,  0.0370275  0.0370275  0.0370275]
```

Or just get one or a few arrays:

```python
>>> tree.array("M")
array([ 82.46269156,  83.62620401,  83.30846467, ...,  95.96547966,
        96.49594381,  96.65672765])
>>> 
>>> tree.arrays(["px1", "py1", "pz1"])
{'py1': array([ 17.4332439 , -16.57036233, -16.57036233, ...,   1.19940578,
                 1.19940578,   1.2013503 ]),
 'px1': array([-41.19528764,  35.11804977,  35.11804977, ...,  32.37749196,
                32.37749196,  32.48539387]),
 'pz1': array([-68.96496181, -48.77524654, -48.77524654, ..., -74.53243061,
               -74.53243061, -74.80837247])}
```

## More examples

<p align="center"><a href="https://gist.github.com/search?utf8=%E2%9C%93&q=%22import+uproot%22+OR+%22from+uproot%22&ref=searchresults" target="_blank">&gt;&gt;&gt; Find more examples as GitHub Gists! &lt;&lt;&lt;</a></p>

## Performance plots

[TODO]

## Status

The following features are planned:

   * reading "leaf list" and fixed-sized leaf arrays as Numpy recarrays and multidimensional shapes;
   * writing flat TTrees (not structrued, and also not from the same file as reading);
   * reading a few basic types of non-TTree objects, relelvant for analysis, such as histograms and graphs;
   * import-on-demand connections to Pandas, Keras, TensorFlow, PySpark, etc.;

## Acknowledgements

Conversations with Philippe Canal were essential for context, finding my way through 20 years of living codebase. Brian Bockelman's BulkIO additions to C++ ROOT also helped to clarify the distinction between I/O and interface. Also, Sebastien Binet's [go-hep](https://github.com/go-hep/hep) provided a clean implementation to ~~pillage~~ replicate.
