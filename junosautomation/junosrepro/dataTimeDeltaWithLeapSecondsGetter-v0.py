#!/usr/bin/python


"""
    Gets the difference between two human readable timestamps,
    INCLUDING ANY HISTORIC LEAP SECONDS.
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
assert(len(sys.argv) == 4)
assert(re.search("[0-9]{1,10}\.[0-9]+$", sys.argv[1]))


userInput = sys.argv[1]
userInput2 = sys.argv[2]
userInput3 = sys.argv[3]
dotIndex = userInput.index(".")

secondsSinceNtpEpoch = userInput[:dotIndex]
secondsSinceNtpEpoch = int(secondsSinceNtpEpoch)
secondsSinceUnixEpoch = secondsSinceNtpEpoch - 2208988800

fractionalSeconds = userInput[dotIndex + 1:]

humanReadableTimestampTuple = time.gmtime(secondsSinceUnixEpoch)
humanReadableTimestampString = time.strftime("%a %b %d %Y %H:%M:%S", humanReadableTimestampTuple)


print "%s.%s UTC" % (humanReadableTimestampString, fractionalSeconds)

#time.strptime("30 Nov 00", "%d %b %y")
sooner = time.strptime(userInput2, "%a %b %d %Y %H:%M:%S")
later = time.strptime(userInput3, "%a %b %d %Y %H:%M:%S")
print sooner
print later

# Parsed from http://www.ietf.org/timezones/data/leap-seconds.list on 7-Feb-2015:
leaps = ( \
2272060800, \
2287785600, \
2303683200, \
2335219200, \
2366755200, \
2398291200, \
2429913600, \
2461449600, \
2492985600, \
2524521600, \
2571782400, \
2603318400, \
2634854400, \
2698012800, \
2776982400, \
2840140800, \
2871676800, \
2918937600, \
2950473600, \
2982009600, \
3029443200, \
3076704000, \
3124137600, \
3345062400, \
3439756800, \
3550089600, \
3644697600, \
)

