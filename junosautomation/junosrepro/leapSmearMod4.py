#!/usr/local/bin/python2.7


# File:  leapSmearMod4.py (fixes OS float bug) 
# Author:  Jonathan A. Natale
# Date:  27-Jan-2017
# Synopsis:  Determines if my FP fix works for leap smear interval 68985.


import sys
import floatFixV2


# FOR VARIOUS LEAP SMEARING PERIODS, ...
# *theses are the ones that hit the FP issue:
#for x in [68985, 71613, 72485, 72927, 73815, 76627, 77805, 80769, 82251, 84693, 87381, 89271, 90155, 90909, 93195, 94535, 94905, 99645, 103005, 103441, 104353, 105339]:)
for x in range (68985, 68986):
    #print "trying x = %d" % (x)

    
    # The following try: plus 2 lines does:
    # ss = (x + 1.) / x
    # --this is the length of the smeared second
    try:
        ss = floatFixV2.addFpCorrectly(x/1., 1.)
    except floatFixV2.FpTypeError:
        print "nan, inf, and/or -inf unexpectedly passed to floatFixV2 while calculating ss"
        sys.exit(1)
    except floatFixV2.FpNotFpError:
        print "non-float unexpectedly passed to floatFixV2 while while calculating ss"
        sys.exit(2)
    ss = ss / x
    #print "ss = %100.100f" % ss


    # ...ADD UP ALL THE SMEARED SECONDS, ...
    t = 0.
    oldT = 0.
    for y in range(0, x):


        # The following try: does:
        # t += ss
        try:
            t = floatFixV2.addFpCorrectly(t, ss)
        except floatFixV2.FpTypeError:
            print "nan, inf, and/or -inf unexpectedly passed to floatFixV2 while summing"
            sys.exit(3)
        except floatFixV2.FpNotFpError:
            print "non-float unexpectedly passed to floatFixV2 while summing"
            sys.exit(4)
        print "t = %50.50f" % (t)
        oldT = t


        # ...AND THEN CHECK IF THE SUM EQUALS THE SMEARING PERIOD:
        try:
            st = floatFixV2.addFpCorrectly(x/1., 1.)
        except floatFixV2.FpTypeError:
            print "nan, inf, and/or -inf unexpectedly passed to floatFixV2 while checking if sum is correct"
            sys.exit(5)
        except floatFixV2.FpNotFpError:
            print "non-float unexpectedly passed to floatFixV2 while checking if sum is correct"
            sys.exit(6)

    if (t == st):
        print "hit x = %d" % (x)
