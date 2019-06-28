#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import numpy

import uproot
import uproot.write.objects.TTree

def fixstring(string):
    if isinstance(string, bytes):
        return string
    else:
        return string.encode("utf-8")

def ttree(tree):
    if isinstance(tree, uproot.write.objects.TTree.TTree):
        return tree
    elif isinstance(tree, uproot.rootio.TTree): #f._context.classes["TTree"]?

        #Get Branch information from tree and create list of branches
        branches = []
        for branch in tree._fBranches():
            name = branch._fName
            title = branch._fTitle
            if branch._fLeaves[0].__class__.__name__ == "TLeafI":
                dtype = numpy.dtype("int32")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafB":
                dtype = numpy.dtype("int8")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafC":
                dtype = numpy.dtype("S") #Variable length strings?
            elif branch._fleaves[0].__class__.__name__ == "TLeafD":
                dtype = numpy.dtype("float64")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafD32":
            #   dtype = numpy.dtype("float24") #Truncated 24 bit floating point - Double32
                raise NotImplementedError
            elif branch._fLeaves[0].__class__.__name__ == "TLeafElement":
            #   dtype = ....
                raise NotImplementedError
            elif branch._fLeaves[0].__class__.__name__ == "TLeafF":
                dtype = numpy.dtype("float32")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafF16":
                dtype = numpy.dtype("float16")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafL":
                dtype = numpy.dtype("int64")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafO":
                dtype = numpy.dtype("bool")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafS":
                dtype = numpy.dtype("int16")
            elif branch._fLeaves[0].__class__.__name__ == "TLeafObject":
            #   dtype = ...
                raise NotImplementedError
            name = uproot.write.objects.TTree.branch(dtype, name, title)
            # Have to add branch attributes

        ttree = uproot.write.objects.TTree.TTree(fixstring(tree._fName), fixstring(tree._fTitle), branches)
        ttree.fields = ttree.emptyfields()

        for n in list(ttree.fields):
            if hasattr(tree, n):
                ttree.fields[n] = getattr(tree, n)

        return ttree

