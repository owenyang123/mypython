#!/usr/local/bin/python2.7


# File:  leapSmearMod5.py (fixes OS float bug) 
# Author:  Jonathan A. Natale
# Date:  27-Jan-2017
# Synopsis:  Determines if my FP fix works for leap smear interval(s).


import sys
#import floatFixV5


# FOR VARIOUS LEAP SMEARING INTERVALS, ...
# *theses are the ones that hit the FP issue:
#for x in [68985, 71613, 72485, 72927, 73815, 76627, 77805, 80769, 82251, 84693, 87381, 89271, 90155, 90909, 93195, 94535, 94905, 99645, 103005, 103441, 104353, 105339]:)
#for x in range (68985, 68986):  # works
#for x in range (36000, 108001):
#for x in [36529]:  # works
#for x in [36530,36529,65536,68985,71613,72485,72751,72927,73815,76627,77805,80769,81777,82251,84693,87381,89271,90155,90909,93195,94535,94819,94905,99645,103005,103441,104353,105339]:
for x in [104353]:
    #print "trying x = %d" % (x)

    
    # The following try: plus 2 lines does:
    ss = (x + 1.) / x
    # --this is the length of the smeared second
    #try:
    #    ss = floatFixV5.addFpCorrectly(x/1., 1.)
    #except floatFixV5.FpTypeError:
    #    print "nan, inf, and/or -inf unexpectedly passed to floatFixV5 while calculating ss"
    #    sys.exit(1)
    #except floatFixV5.FpNotFpError:
    #    print "non-float unexpectedly passed to floatFixV5 while while calculating ss"
    #    sys.exit(2)
    #ss = ss / x
    print "ss = %100.100f" % ss


    # ...ADD UP ALL THE SMEARED SECONDS, ...
    t = 0.
    oldT = 0.
    for y in range(0, x):


        # The following try: does:
        t += ss
        #try:
        #    t = floatFixV5.addFpCorrectly(t, ss)
        #except floatFixV5.FpTypeError:
        #    print "nan, inf, and/or -inf unexpectedly passed to floatFixV5 while summing"
        #    sys.exit(3)
        #except floatFixV5.FpNotFpError:
        #    print "non-float unexpectedly passed to floatFixV5 while summing"
        #    sys.exit(4)
        print "t = %50.50f" % (t)
        oldT = t


        # ...AND THEN CHECK IF THE SUM EQUALS THE SMEARING INTERVAL PLUS 1:
        # The following try: does:
        st = x/1. + 1.
        #try:
        #    st = floatFixV5.addFpCorrectly(x/1., 1.)
        #except floatFixV5.FpTypeError:
        #    print "nan, inf, and/or -inf unexpectedly passed to floatFixV5 while checking if sum is correct"
        #    sys.exit(5)
        #except floatFixV5.FpNotFpError:
        #    print "non-float unexpectedly passed to floatFixV5 while checking if sum is correct"
        #    sys.exit(6)

    if (t == st):
        print "hit x = %d" % (x)
