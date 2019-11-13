#!/usr/bin/python


"""
Converts NTP timestamp (in hex) to human readable timestamp, example run:
    -bash-3.2$ ./ntpHexTimestampToHumanStamp-v1.py BA368E7F.20000000
    Thu Dec 31 1998 23:59:59.125000 UTC
"""


__author__  = "Jonathan Natale"


import sys
import re
import time


# Revison History:
#     v0 - works; no fractional second support
#     v1 - added fractional second support


# To Do:
#     1 - change math (FP errors?)
#     2 - make more readable (ref ./ntpDecTimestampToHumanStamp-v1.py


# 1970 - 1900, in seconds:
secondsFromNtpEpochToUnixEpoch = 2208988800

thirtyTwoBitsAsFloat = 4294967296.0


# Input Sanity Checks:
assert(len(sys.argv) == 2)
assert(re.search("^[0-9a-fA-F]{8}\.[0-9a-fA-F]{8}$", sys.argv[1]))


fractionalSecondsSinceNtpEpochHexString = sys.argv[1].replace(".", "")
fractionalSecondsSinceNtpEpoch = int(fractionalSecondsSinceNtpEpochHexString, 16)
fractionalSecondsSinceUnixEpoch = fractionalSecondsSinceNtpEpoch - (secondsFromNtpEpochToUnixEpoch << 32)
secondsSinceUnixEpoch = fractionalSecondsSinceUnixEpoch >> 32
fractionalSecondsOnly = (fractionalSecondsSinceUnixEpoch - (secondsSinceUnixEpoch << 32)) / thirtyTwoBitsAsFloat
humanReadableTimestampTuple = time.gmtime(secondsSinceUnixEpoch)

"""
Python 2.6 added a new strftime/strptime macro %f, which does microseconds
    (http://stackoverflow.com/questions/698223/how-can-i-parse-a-time-string-containing-milliseconds-in-it-with-python)
-but at the time of writing this script, JNPR uses v2.4.  UGH
"""
print "%s.%09d UTC" % (time.strftime("%a %b %d %Y %H:%M:%S", humanReadableTimestampTuple), fractionalSecondsOnly * 1000000000)
