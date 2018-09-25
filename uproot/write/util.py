import datetime

def time():
    now = datetime.datetime.now()
    return (now.year - 1995) << 26 | now.month << 22 | now.day << 17 | now.hour << 12 | now.minute << 6 | now.second