# test coverage

| Can be tested | Is it tested? |
|:--------------|:-------------:|
| flat numerical types (including booleans) | yes |
| strings (`TLeafC` and `TString`) | yes |
| signed/unsigned integers | yes |
| fixed-size array leaves | yes |
| variable-size array leaves | yes |
| split objects (`small-evnt-tree-fullsplit.root`) | yes |
| split objects in `TClonesArray` | **no** |
| leaflist (FIXME: not implemented) | **no** |
| unsplit objects (won't do) | **no** |
| `std::vector`, `std::string` (???) | **no** |
| branch with "speed bumps" | yes |
| all compression algorithms (none, zlib, lzma, lz4; ignoring "old") | yes |
| `TTree` versions from 16 (2009) to 19 (present) | yes |
| nested directories | **no** |
| arrays interface | yes |
| iterator interface | yes |
| selection by list of branch names | **no** |
| pass array to fill, rather than `dtype` | **no** |
| different `outputtypes` | **no** |
| memory-mapped files | yes |
| standard files (not using; remove?) | **no** |
| XRootD (would have to get XRootD library into `tests_require` somehow...) | **no** |
| big files (64-bit addresses in TFile header) | **no** |
| parallel processing (not deterministic: hard to include in test suite) | **no** |
| exception raising! | **no** |
| `repr` print-outs | **no** |
| informational methods (keys/branches listings) | partial |
