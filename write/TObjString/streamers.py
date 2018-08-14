import pickle

class TObjStringStreamers(object):
    
    def __init__(self, sink, pos):
        self.sink = sink
        self.pos = pos
        
    def write(self):

        self.sink.file.seek(self.pos)
        streamer = pickle.load(open("streamers.pickle", "rb"))
        self.sink.file.write(streamer["TObjString"])
        self.pos = self.sink.file.tell()

