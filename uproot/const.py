#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
