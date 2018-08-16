import pickle
import numpy

streamers = pickle.load(open("write/streamers.pickle", "rb"))

file = numpy.memmap("taxis.root", mode = "r", dtype = numpy.uint8)

#streamers[key] = value - Change as needed
streamers["TAxis"] = file[481:2133]
streamers["TNamed"] = file[2133:2524]
streamers["TObject"] = file[2524:2826]
streamers["TAttAxis"] = file[2826:4137]
streamers["THashList"] = file[4137:4326]
streamers["TList"] = file[4326:4529]
streamers["TSeqCollection"] = file[4529:4741]
streamers["TCollection"] = file[4741:5157]
streamers["TString"] = file[5157:5218]

pickle.dump(streamers, open("write/streamers.pickle", "wb"))