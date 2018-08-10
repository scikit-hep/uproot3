def resize(file, size):
    original_position = file.tell()
    l = []
    for x in range(size - get_eof_position(file)):
        l.append(0)
    file.seek(0, 2)
    file.write(bytes(l))
    file.seek(original_position)
    return file

def get_eof_position(file):
    original_position = file.tell()
    eof_position = file.seek(0, 2)
    file.seek(original_position)
    return eof_position
