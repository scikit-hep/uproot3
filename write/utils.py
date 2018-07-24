import numpy

def resizer(file, size): 
    cp = numpy.zeros(file.shape)
    cp[:] = file[:]
    fp = numpy.memmap(filename = file.filename, mode = "w+", dtype = file.dtype, shape = (size,))
    fp[:cp.size] = cp[:]
    del file,cp
    return fp
    
    