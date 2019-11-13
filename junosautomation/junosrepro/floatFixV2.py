#!/usr/local/bin/python2.7


# File:  floatFixiV2
# Author:  Jonathan A. Natale
# Date:  26-Jan-2017
# Synopsis:  Fixes floating (FP) point issue with sticky bit -- on some systems, the sticky bit is lost if it is shifted more than 8 bits.
# Example:
#                                                                                                                    1          2         3         4         5                                      
#                                                                                                           1234567890123 4567890123456789012345678901234567890123                                    
#  4095.05615204245304994401521980762481689453125000000000   = 0x1.ffe1cbff5e3e1p+11 = 0x40affe1cbff5e3e1 =  111111111111.00001110010111111111101011110001111100001                                   
# +   1.0000137123424794882708965815254487097263336181640625 = 0x1.0000e60e10001p+0  = 0x3ff0000170168000 =             1.0000000000000000111001100000111000010000000000000001                        
#                                                                                                                                                                    12345678^                        
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------                        
#                                                                                                           1000000000000.0000111001100000111000010000000000000000101                                 
#                                                                                                                                                                LGRS                                 
#                                                                                                                                                                0101           (x101=+1vs0100=nc)   
#  4096.0561657547959839575923979282379150390625             = 0x1.0000e60e10001p+12 = 0x40b0000e60e10001 = 1000000000000.0000111001100000111000010000000000000001              (wftac-tools; correct)
#  4096.056165754795074462890625                             = 0x1.0000e60e10000p+12 = 0x40b0000e60e10000 = 1000000000000.0000111001100000111000010000000000000000              (automation ; WRONG  )
#                   ^                                                          ^                        ^                                                        ^                                    
# Rule Summary for FP Rounding (per IEEE-754:)
# LGRS  (LSb/Guard/Round/Sticky; NOTE: if ANY bits underflow to/thru S it "Sticks" to "1")
# x0xx no change
# x11x add 1 to LSb
# x101 add 1 to LSb
# 0100 no change
# 1100 add 1 to LSb



# Revision history:
#     floatFix-v0 - fixes hits prior to re-normalization; not tested well; has debug code
#     floatFixV1 - added comments; fixed file header; works (call commented out after confirmation so feature can be imported) for hits prior to re-normallization; changed file name so it can be imported
#     floatFixV1 - fixed handling of 0.; fixed a vs b bug; work in progress

import sys


class FpTypeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class FpNotFpError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def addFpCorrectly(a, b):
    #print "in addFpCorrectly()"
    if (a == float("nan") or a == float("inf") or a == float("-inf")):
        raise FpTypeError(a)
    if (b == float("nan") or b == float("inf") or b == float("-inf")):
        raise FpTypeError(b)
    if (not isinstance(a, (float))):
        raise FpNotFpError(a)
    if (not isinstance(b, (float))):
        raise FpNotFpError(a)
    if (a > b):
        t = a
        a = b
        b = t
    if (a == 0.):
        exponentA = 0
    else:
        exponentA = int(a.hex()[19:21], 0)
    if (b == 0.):
        exponentB = 0
    else:
        exponentB = int(b.hex()[19:21], 0)
    expDiff = exponentB - exponentA
    #print "exponentA = %d, exponentB = %d, expDiff = %d" % (exponentA, exponentB, expDiff)


    if (expDiff < 11):
        return (a + b)


    if (a == 0.):
        mantissaA = 0
    else:
        mantissaA = int(a.hex()[19:21], 0)
    if (b == 0.):
        mantissaB = 0
    else:
        mantissaB = int(a.hex()[19:21], 0)


    L = (1 & mantissaB) ^ ((1 << expDiff) & mantissaA)
    G = (1 >> (expDiff - 1)) & mantissaA
    R = (1 >> (expDiff - 2)) & mantissaA
    S = 0
    #print "L = %d, G = %d, R = %d, S = %d" % (L, G, R, S)


    for x in range (0, (expDiff - 2)):
        S = S | ((1 >> x) & mantissaA)
    S_upTo8 = 0
    for x in range (0, (expDiff - 2)):
        S_upTo8 = S_upTo8 | (1 >> x & mantissaA)
    if ((S_upTo8 == 0) and (L == 0) and (G == 1) and (R == 0) and (S == 1)):
        return (a + b + 2**(-52 + exponentA))
    else:
        return (a + b)

#
#try:
#    #result = addFpCorrectly(4095.05615204245304994401521980762481689453125000000000, 1.0000137123424794882708965815254487097263336181640625)
#    result = addFpCorrectly(0., 1.0000277777777777377110624001943506300449371337890625)
#    #result = addFpCorrectly(1, 1)
#except FpTypeError:
#    print "nan, inf, and/or -inf passed to addFpCorrectly()"
#    sys.exit(1)
#except FpNotFpError:
#    print "one or both args passed to addFpCorrectly() not floats"
#    sys.exit(2)


#print "res = %70.70f" % result


# Since this will be imported, we donot want to exit like this:
#sys.exit(0)
