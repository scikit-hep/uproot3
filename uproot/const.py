#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

"""ROOT constants used in deserialization."""

import numpy

# used in unmarshaling
kByteCountMask        = numpy.int64(0x40000000)
kByteCountVMask       = numpy.int64(0x4000)
kClassMask            = numpy.int64(0x80000000)
kNewClassTag          = numpy.int64(0xFFFFFFFF)

kIsOnHeap             = numpy.uint32(0x01000000)
kIsReferenced         = numpy.uint32(1 << 4)

kMapOffset            = 2

# not used?
kNullTag              = 0
kNotDeleted           = numpy.uint32(0x02000000)
kZombie               = numpy.uint32(0x04000000)
kBitMask              = numpy.uint32(0x00FFFFFF)
kDisplacementMask     = numpy.uint32(0xFF000000)

################################################################ core/zip/inc/Compression.h

kZLIB                 = 1
kLZMA                 = 2
kOldCompressionAlgo   = 3
kLZ4                  = 4
kUndefinedCompressionAlgorithm = 5

################################################################ constants for streamers

kBase                 = 0
kChar                 = 1
kShort                = 2
kInt                  = 3
kLong                 = 4
kFloat                = 5
kCounter              = 6
kCharStar             = 7
kDouble               = 8
kDouble32             = 9
kLegacyChar           = 10
kUChar                = 11
kUShort               = 12
kUInt                 = 13
kULong                = 14
kBits                 = 15
kLong64               = 16
kULong64              = 17
kBool                 = 18
kFloat16              = 19
kOffsetL              = 20
kOffsetP              = 40
kObject               = 61
kAny                  = 62
kObjectp              = 63
kObjectP              = 64
kTString              = 65
kTObject              = 66
kTNamed               = 67
kAnyp                 = 68
kAnyP                 = 69
kAnyPnoVT             = 70
kSTLp                 = 71

kSkip                 = 100
kSkipL                = 120
kSkipP                = 140

kConv                 = 200
kConvL                = 220
kConvP                = 240

kSTL                  = 300
kSTLstring            = 365

kStreamer             = 500
kStreamLoop           = 501

################################################################ constants from core/foundation/inc/ESTLType.h

kNotSTL               = 0
kSTLvector            = 1
kSTLlist              = 2
kSTLdeque             = 3
kSTLmap               = 4
kSTLmultimap          = 5
kSTLset               = 6
kSTLmultiset          = 7
kSTLbitset            = 8
kSTLforwardlist       = 9
kSTLunorderedset      = 10
kSTLunorderedmultiset = 11
kSTLunorderedmap      = 12
kSTLunorderedmultimap = 13
kSTLend               = 14
kSTLany               = 300

################################################################ IOFeatures

kGenerateOffsetMap    = 1
