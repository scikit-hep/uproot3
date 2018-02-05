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

from collections import namedtuple
import unittest

import numpy

import uproot
from uproot.interp.jagged import asstlvector
from uproot.interp.numerical import asdtype

class TestSTLVector(unittest.TestCase):
    def runTest(self):
        pass

    def test_vector_of_numbers(self):
        branch = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]["StlVecU32"]
        a = branch.array()
        for i in range(100):
            self.assertEqual(a[i].tolist(), [i] * (i % 10))

        branch = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]["StlVecF64"]
        a = branch.array()
        for i in range(100):
            self.assertEqual(a[i].tolist(), [i] * (i % 10))

    def test_vector_of_vector_of_numbers(self):
        branch = uproot.open("tests/samples/vectorVectorDouble.root")["t"]["x"]
        self.assertEqual(branch.array().tolist(), [[[]], [[[], []]], [[[10.0], [], [10.0, 20.0]]], [[[20.0, -21.0, -22.0]]], [[[200.0], [-201.0], [202.0]]]])

    def test_strings1(self):
        tree = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]
        self.assertEqual(tree.array("Str").tolist(), ['evt-000', 'evt-001', 'evt-002', 'evt-003', 'evt-004', 'evt-005', 'evt-006', 'evt-007', 'evt-008', 'evt-009', 'evt-010', 'evt-011', 'evt-012', 'evt-013', 'evt-014', 'evt-015', 'evt-016', 'evt-017', 'evt-018', 'evt-019', 'evt-020', 'evt-021', 'evt-022', 'evt-023', 'evt-024', 'evt-025', 'evt-026', 'evt-027', 'evt-028', 'evt-029', 'evt-030', 'evt-031', 'evt-032', 'evt-033', 'evt-034', 'evt-035', 'evt-036', 'evt-037', 'evt-038', 'evt-039', 'evt-040', 'evt-041', 'evt-042', 'evt-043', 'evt-044', 'evt-045', 'evt-046', 'evt-047', 'evt-048', 'evt-049', 'evt-050', 'evt-051', 'evt-052', 'evt-053', 'evt-054', 'evt-055', 'evt-056', 'evt-057', 'evt-058', 'evt-059', 'evt-060', 'evt-061', 'evt-062', 'evt-063', 'evt-064', 'evt-065', 'evt-066', 'evt-067', 'evt-068', 'evt-069', 'evt-070', 'evt-071', 'evt-072', 'evt-073', 'evt-074', 'evt-075', 'evt-076', 'evt-077', 'evt-078', 'evt-079', 'evt-080', 'evt-081', 'evt-082', 'evt-083', 'evt-084', 'evt-085', 'evt-086', 'evt-087', 'evt-088', 'evt-089', 'evt-090', 'evt-091', 'evt-092', 'evt-093', 'evt-094', 'evt-095', 'evt-096', 'evt-097', 'evt-098', 'evt-099'])

    def test_strings2(self):
        tree = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]
        self.assertEqual(tree.array("StdStr").tolist(), ['std-000', 'std-001', 'std-002', 'std-003', 'std-004', 'std-005', 'std-006', 'std-007', 'std-008', 'std-009', 'std-010', 'std-011', 'std-012', 'std-013', 'std-014', 'std-015', 'std-016', 'std-017', 'std-018', 'std-019', 'std-020', 'std-021', 'std-022', 'std-023', 'std-024', 'std-025', 'std-026', 'std-027', 'std-028', 'std-029', 'std-030', 'std-031', 'std-032', 'std-033', 'std-034', 'std-035', 'std-036', 'std-037', 'std-038', 'std-039', 'std-040', 'std-041', 'std-042', 'std-043', 'std-044', 'std-045', 'std-046', 'std-047', 'std-048', 'std-049', 'std-050', 'std-051', 'std-052', 'std-053', 'std-054', 'std-055', 'std-056', 'std-057', 'std-058', 'std-059', 'std-060', 'std-061', 'std-062', 'std-063', 'std-064', 'std-065', 'std-066', 'std-067', 'std-068', 'std-069', 'std-070', 'std-071', 'std-072', 'std-073', 'std-074', 'std-075', 'std-076', 'std-077', 'std-078', 'std-079', 'std-080', 'std-081', 'std-082', 'std-083', 'std-084', 'std-085', 'std-086', 'std-087', 'std-088', 'std-089', 'std-090', 'std-091', 'std-092', 'std-093', 'std-094', 'std-095', 'std-096', 'std-097', 'std-098', 'std-099'])

    def test_strings3(self):
        tree = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]
        self.assertEqual(tree.array("StlVecStr").tolist(), [[], ['vec-001'], ['vec-002', 'vec-002'], ['vec-003', 'vec-003', 'vec-003'], ['vec-004', 'vec-004',
 'vec-004', 'vec-004'], ['vec-005', 'vec-005', 'vec-005', 'vec-005', 'vec-005'], ['vec-006', 'vec-006', 'vec-006', 'vec-006', 'vec-006', 'vec-006'], ['vec-007', 'vec-007', 'vec-007', 'vec-007', 'vec-007', 'vec-007', 'vec-007'], ['vec-008', 'vec-008', 'vec-008', 'vec-008', 'vec-008', 'vec-008', 'vec-008', 'vec-008'], ['vec-009', 'vec-009', 'vec-009', 'vec-009', 'vec-009', 'vec-009', 'vec-009', 'vec-009', 'vec-009'], [], ['vec-011'], ['vec-012', 'vec-012'], ['vec-013', 'vec-013', 'vec-013'], ['vec-014', 'vec-014', 'vec-014', 'vec-014'], ['vec-015', 'vec-015', 'vec-015', 'vec-015', 'vec-015'], ['vec-016', 'vec-016', 'vec-016', 'vec-016', 'vec-016', 'vec-016'], ['vec-017', 'vec-017', 'vec-017', 'vec-017', 'vec-017', 'vec-017', 'vec-017'], ['vec-018', 'vec-018', 'vec-018', 'vec-018', 'vec-018', 'vec-018', 'vec-018', 'vec-018'], ['vec-019', 'vec-019', 'vec-019', 'vec-019', 'vec-019', 'vec-019', 'vec-019', 'vec-019', 'vec-019'], [], ['vec-021'], ['vec-022', 'vec-022'], ['vec-023', 'vec-023', 'vec-023'], ['vec-024', 'vec-024', 'vec-024', 'vec-024'], ['vec-025', 'vec-025', 'vec-025', 'vec-025', 'vec-025'], ['vec-026', 'vec-026', 'vec-026', 'vec-026', 'vec-026', 'vec-026'], ['vec-027', 'vec-027', 'vec-027', 'vec-027', 'vec-027', 'vec-027', 'vec-027'], ['vec-028', 'vec-028', 'vec-028', 'vec-028', 'vec-028', 'vec-028', 'vec-028', 'vec-028'], ['vec-029', 'vec-029', 'vec-029', 'vec-029', 'vec-029', 'vec-029', 'vec-029', 'vec-029', 'vec-029'], [], ['vec-031'], ['vec-032', 'vec-032'], ['vec-033', 'vec-033', 'vec-033'], ['vec-034', 'vec-034', 'vec-034', 'vec-034'], ['vec-035', 'vec-035', 'vec-035', 'vec-035', 'vec-035'], ['vec-036', 'vec-036', 'vec-036', 'vec-036', 'vec-036', 'vec-036'], ['vec-037', 'vec-037', 'vec-037', 'vec-037', 'vec-037', 'vec-037', 'vec-037'], ['vec-038', 'vec-038', 'vec-038', 'vec-038', 'vec-038', 'vec-038', 'vec-038', 'vec-038'], ['vec-039', 'vec-039', 'vec-039', 'vec-039', 'vec-039', 'vec-039', 'vec-039', 'vec-039', 'vec-039'], [], ['vec-041'], ['vec-042', 'vec-042'], ['vec-043', 'vec-043', 'vec-043'], ['vec-044', 'vec-044', 'vec-044', 'vec-044'], ['vec-045', 'vec-045', 'vec-045', 'vec-045', 'vec-045'], ['vec-046', 'vec-046', 'vec-046', 'vec-046', 'vec-046', 'vec-046'], ['vec-047', 'vec-047', 'vec-047', 'vec-047', 'vec-047', 'vec-047', 'vec-047'], ['vec-048', 'vec-048', 'vec-048', 'vec-048', 'vec-048', 'vec-048', 'vec-048', 'vec-048'], ['vec-049', 'vec-049', 'vec-049', 'vec-049', 'vec-049', 'vec-049', 'vec-049', 'vec-049', 'vec-049'], [], ['vec-051'], ['vec-052', 'vec-052'], ['vec-053', 'vec-053', 'vec-053'], ['vec-054', 'vec-054', 'vec-054', 'vec-054'], ['vec-055', 'vec-055', 'vec-055', 'vec-055', 'vec-055'], ['vec-056', 'vec-056', 'vec-056', 'vec-056', 'vec-056', 'vec-056'], ['vec-057', 'vec-057', 'vec-057', 'vec-057', 'vec-057', 'vec-057', 'vec-057'], ['vec-058', 'vec-058', 'vec-058', 'vec-058', 'vec-058', 'vec-058', 'vec-058', 'vec-058'], ['vec-059', 'vec-059', 'vec-059', 'vec-059', 'vec-059', 'vec-059', 'vec-059', 'vec-059', 'vec-059'], [], ['vec-061'], ['vec-062', 'vec-062'], ['vec-063', 'vec-063', 'vec-063'], ['vec-064', 'vec-064', 'vec-064', 'vec-064'], ['vec-065', 'vec-065', 'vec-065', 'vec-065', 'vec-065'], ['vec-066', 'vec-066', 'vec-066', 'vec-066', 'vec-066', 'vec-066'], ['vec-067', 'vec-067', 'vec-067', 'vec-067', 'vec-067', 'vec-067', 'vec-067'], ['vec-068', 'vec-068', 'vec-068', 'vec-068', 'vec-068', 'vec-068', 'vec-068', 'vec-068'], ['vec-069', 'vec-069', 'vec-069', 'vec-069', 'vec-069', 'vec-069', 'vec-069', 'vec-069', 'vec-069'], [], ['vec-071'], ['vec-072', 'vec-072'], ['vec-073', 'vec-073', 'vec-073'], ['vec-074', 'vec-074', 'vec-074', 'vec-074'], ['vec-075', 'vec-075', 'vec-075', 'vec-075', 'vec-075'], ['vec-076', 'vec-076', 'vec-076', 'vec-076', 'vec-076', 'vec-076'], ['vec-077', 'vec-077', 'vec-077', 'vec-077', 'vec-077', 'vec-077', 'vec-077'], ['vec-078', 'vec-078', 'vec-078', 'vec-078', 'vec-078', 'vec-078', 'vec-078', 'vec-078'], ['vec-079', 'vec-079', 'vec-079', 'vec-079', 'vec-079', 'vec-079', 'vec-079', 'vec-079', 'vec-079'], [], ['vec-081'], ['vec-082', 'vec-082'], ['vec-083', 'vec-083', 'vec-083'], ['vec-084', 'vec-084', 'vec-084', 'vec-084'], ['vec-085', 'vec-085', 'vec-085', 'vec-085', 'vec-085'], ['vec-086', 'vec-086', 'vec-086', 'vec-086', 'vec-086', 'vec-086'], ['vec-087', 'vec-087', 'vec-087', 'vec-087', 'vec-087', 'vec-087', 'vec-087'], ['vec-088', 'vec-088', 'vec-088', 'vec-088', 'vec-088', 'vec-088', 'vec-088', 'vec-088'], ['vec-089', 'vec-089', 'vec-089', 'vec-089', 'vec-089', 'vec-089', 'vec-089', 'vec-089', 'vec-089'], [], ['vec-091'], ['vec-092', 'vec-092'], ['vec-093', 'vec-093', 'vec-093'], ['vec-094', 'vec-094', 'vec-094', 'vec-094'], ['vec-095', 'vec-095', 'vec-095', 'vec-095', 'vec-095'], ['vec-096', 'vec-096', 'vec-096', 'vec-096', 'vec-096', 'vec-096'], ['vec-097', 'vec-097', 'vec-097', 'vec-097', 'vec-097', 'vec-097', 'vec-097'], ['vec-098', 'vec-098', 'vec-098', 'vec-098', 'vec-098', 'vec-098', 'vec-098', 'vec-098'], ['vec-099', 'vec-099', 'vec-099', 'vec-099', 'vec-099', 'vec-099', 'vec-099', 'vec-099', 'vec-099']])

    def test_array(self):
        tree = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]
        self.assertEqual(tree.array("ArrayI16[10]").tolist(), [[i] * 10 for i in range(100)])

    def test_slice(self):
        tree = uproot.open("tests/samples/small-evnt-tree-fullsplit.root")["tree"]
        self.assertEqual(tree.array("SliceI16").tolist(), [[], [1], [2, 2], [3, 3, 3], [4, 4, 4, 4], [5, 5, 5, 5, 5], [6, 6, 6, 6, 6, 6], [7, 7, 7, 7, 7, 7, 7], [8, 8, 8, 8, 8, 8, 8, 8], [9, 9, 9, 9, 9, 9, 9, 9, 9], [], [11], [12, 12], [13, 13, 13], [14, 14, 14, 14], [15, 15, 15, 15, 15], [16, 16, 16, 16, 16, 16], [17, 17, 17, 17, 17, 17, 17], [18, 18, 18, 18, 18, 18, 18, 18], [19, 19, 19, 19, 19, 19, 19, 19, 19], [], [21], [22, 22], [23, 23, 23], [24, 24, 24, 24], [25, 25, 25, 25, 25], [26, 26, 26, 26, 26, 26], [27, 27, 27, 27, 27, 27, 27], [28, 28, 28, 28, 28, 28, 28, 28], [29, 29, 29, 29, 29, 29, 29, 29, 29], [], [31], [32, 32], [33, 33, 33], [34, 34, 34, 34], [35, 35, 35, 35, 35], [36, 36, 36, 36, 36, 36], [37, 37, 37, 37, 37, 37, 37], [38, 38, 38, 38, 38, 38, 38, 38], [39, 39, 39, 39, 39, 39, 39, 39, 39], [], [41], [42, 42], [43, 43, 43], [44, 44, 44, 44], [45, 45, 45, 45, 45], [46, 46, 46, 46, 46, 46], [47, 47, 47, 47, 47, 47, 47], [48, 48, 48, 48, 48, 48, 48, 48], [49, 49, 49, 49, 49, 49, 49, 49, 49], [], [51], [52, 52], [53, 53, 53], [54, 54, 54, 54], [55, 55, 55, 55, 55], [56, 56, 56, 56, 56, 56], [57, 57, 57, 57, 57, 57, 57], [58, 58, 58, 58, 58, 58, 58, 58], [59, 59, 59, 59, 59, 59, 59, 59, 59], [], [61], [62, 62], [63, 63, 63], [64, 64, 64, 64], [65, 65, 65, 65, 65], [66, 66, 66, 66, 66, 66], [67, 67, 67, 67, 67, 67, 67], [68, 68, 68, 68, 68, 68, 68, 68], [69, 69, 69, 69, 69, 69, 69, 69, 69], [], [71], [72, 72], [73, 73, 73], [74, 74, 74, 74], [75, 75, 75, 75, 75], [76, 76, 76, 76, 76, 76], [77, 77, 77, 77, 77, 77, 77], [78, 78, 78, 78, 78, 78, 78, 78], [79, 79, 79, 79, 79, 79, 79, 79, 79], [], [81], [82, 82], [83, 83, 83], [84, 84, 84, 84], [85, 85, 85, 85, 85], [86, 86, 86, 86, 86, 86], [87, 87, 87, 87, 87, 87, 87], [88, 88, 88, 88, 88, 88, 88, 88], [89, 89, 89, 89, 89, 89, 89, 89, 89], [], [91], [92, 92], [93, 93, 93], [94, 94, 94, 94], [95, 95, 95, 95, 95], [96, 96, 96, 96, 96, 96], [97, 97, 97, 97, 97, 97, 97], [98, 98, 98, 98, 98, 98, 98, 98], [99, 99, 99, 99, 99, 99, 99, 99, 99]])
