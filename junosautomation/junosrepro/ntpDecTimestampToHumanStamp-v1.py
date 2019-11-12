#!/usr/bin/python


"""
Converts NTP timestamp (in hex) to human readable timestamp, example run:
    -bash-3.2$ ./ntpDecTimestampToHumanStamp-v1.py 3124137599.2147483648
    Thu Dec 31 23:59:59 1998 UTC
"""


__author__  = "Jonathan Natale"


# To Do:
#     1 - add leap second support


# Revison History:
#     v1 - works
#     v2 - added nanosecond support; made code more readable


import sys
import re
import time


# 1970 - 1900, in seconds:
secondsFromNtpEpochToUnixEpoch = 2208988800


# Input Sanity Checks:
assert(len(sys.argv) == 2)
assert(re.search("[0-9]{1,10}\.[0-9]+$", sys.argv[1]))


userInput = sys.argv[1]
dotIndex = userInput.index(".")

secondsSinceNtpEpoch = userInput[:dotIndex]
secondsSinceNtpEpoch = int(secondsSinceNtpEpoch)
secondsSinceUnixEpoch = secondsSinceNtpEpoch - 2208988800

fractionalSeconds = userInput[dotIndex + 1:]

humanReadableTimestampTuple = time.gmtime(secondsSinceUnixEpoch)
humanReadableTimestampString = time.strftime("%a %b %d %Y %H:%M:%S", humanReadableTimestampTuple)


print "%s.%s UTC" % (humanReadableTimestampString, fractionalSeconds)
