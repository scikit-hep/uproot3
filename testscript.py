from newwriter import NewWriter
from write.TObjString.tobjstring import TObjString
file = NewWriter("abcd.root")
item = TObjString("Hello World")
for x in range(15):
    file[str(x)] = item