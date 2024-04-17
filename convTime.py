import time

def StrTimeToInt(strTime):
    if not strTime:
        return None
    # yyyy/mm/dd HH:MM:SS
    # 0123456789012345678
    ye = int(strTime[:4])
    mo = int(strTime[5:7])
    da = int(strTime[8:10])
    ho = int(strTime[11:13])
    mi = int(strTime[14:16])
    se = int(strTime[17:])
    t = time.mktime((ye, mo, da, ho, mi, se, 0, 1, -1)) - time.timezone + 3600
    return t

