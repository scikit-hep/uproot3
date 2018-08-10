from writer import Writer
from write.TObjString.tobjstring import TObjString
file = Writer("abcd.root")
item = TObjString("Hello World")
for x in range(15):
    file[str(x)] = item