import uproot.tree as tree_reader
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
                dtype = "int"
            elif branch._fLeaves[0].__class__.__name__ == "TLeafB":

            name = uproot.write.objects.TTree.branch()

        ttree = uproot.write.objects.TTree.TTree(fixstring(tree._fName), fixstring(tree._fTitle), branches)
        ttree.fields = ttree.emptyfields()

        for n in list(ttree.fields):
            if hasattr(tree, n):
                ttree.fields[n] = getattr(tree, n)

        return ttree

