import pickle
import numpy

streamers = pickle.load(open("write/streamers.pickle", "rb"))

file = numpy.memmap("taxis.root", )

#streamers[key] = value - Change as needed
streamers["TNamed"] =

pickle.dump(streamers, open("write/streamers.pickle", "wb"))