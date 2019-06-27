import uproot.tree as tree_reader
import uproot
import uproot.write.objects.TTree

def ttree(tree):
    if isinstance(tree, uproot.write.objects.TTree.TTree):
        return tree
    elif isinstance(tree, uproot.rootio.TTree): #f._context.classes["TTree"]?
        raise NotImplementedError
