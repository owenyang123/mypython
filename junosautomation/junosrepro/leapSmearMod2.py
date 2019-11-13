#!/usr/local/bin/python2.7

# File:  leapSmearMod2.py
# Author:  Jonathan A. Natale
# Date:  1-Jan-2017
# Synopsis:  Determines if the leap smear intervals that do not create errors that are missed by this script are missed due to the stcky bit lost after 8 shifts issue.


#for x in [71613]:
for x in [72485, 72927, 73815, 76627, 77805, 80769, 82251, 84693, 87381, 89271, 90155, 90909, 93195, 94535, 94905, 99645, 103005, 103441, 104353, 105339]:
    print "trying x = %d" % (x)
    ss = (x + 1.) / x
    t = 0.
    oldT = 0.
    for y in range(0, x):
        t += ss
        #if (oldT == t):
        print "t = %50.50f" % (t)
        oldT = t
    if (t == x + 1.):
        print "hit x = %d" % (x)
