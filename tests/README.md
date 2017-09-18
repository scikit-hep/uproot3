# Test coverage

| Can be tested | Is it tested? |
|:--------------|:-------------:|
| flat numerical types (including booleans) | &#x2713; |
| strings (`TLeafC` and `TString`) | &#x2713; |
| signed/unsigned integers | &#x2713; |
| fixed-size array leaves | &#x2713; |
| variable-size array leaves | &#x2713; |
| split objects (`small-evnt-tree-fullsplit.root`) | &#x2713; |
| split objects in `TClonesArray` | **no** |
| leaflist (FIXME: not implemented) | **no** |
| unsplit objects (won't do) | **no** |
| `std::vector`, `std::string` (???) | **no** |
| branch with "speed bumps" | &#x2713; |
| all compression algorithms (none, zlib, lzma, lz4; ignoring "old") | &#x2713; |
| `TTree` versions from 16 (2009) to 19 (present) | &#x2713; |
| nested directories | **no** |
| arrays interface | &#x2713; |
| iterator interface | &#x2713; |
| selection by list of branch names | **no** |
| pass array to fill, rather than `dtype` | **no** |
| different `outputtypes` | **no** |
| memory-mapped files | &#x2713; |
| standard files (not using; remove?) | **no** |
| XRootD (would have to get XRootD library into `tests_require` somehow...) | **no** |
| big files (64-bit addresses in TFile header) | **no** |
| parallel processing (not deterministic: hard to include in test suite) | **no** |
| exception raising! | **no** |
| `repr` print-outs | **no** |
| informational methods (keys/branches listings) | partial |
