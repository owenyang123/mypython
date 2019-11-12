#!/usr/bin/python3
# notes regarding python v3 and pexpect--
#     v2: print "BLAH" + int VS
#     v3: print("BLAH %d" % theInt)
#     Jim Boyle installed pexpect on svl-jtac-lnx01 on ~23-Dec-2014
 

# file: vzLogin-v2.py
 

# Written by Jonathan Natale for JNPR on 6-Jan-2015.


# Caveats:
# credentials.cfg file that has 1 line w/ userId and password, in that order, separated by spaces must exist
# last send ("70) is echoed (why?)
# log file has VT codes instead of having textual end-result of these codes


# Version History:
# v0 - initial
# v1 - first copy to ~/z
# v2 - added log file, removed need for <cr> at end, handled timeouts better, improved user messages, misc. clean-up


# To Do:
# see ?s imbedded in code
# see to do's in code
# add option to spec log file
# try/catch
# handle VT codes


# ~= Expect
import pexpect

# for argv, exit, et. al.
import sys

# for future use
import random

# regular expressions (for future use)
import re


# command line check
if len(sys.argv) != 2:
    print("e1: USAGE: %s <token>, exiting..." % sys.argv[0])
    sys.exit(1)

# get token from command line
token = sys.argv[1]


# get credentials from the credentials.cfg file (should have 1 line w/ userId and password, in that order, separated by spaces)

# open file
fobj = open("credentials.cfg", "r")

# read file
theLine = fobj.readline()

# close file
fobj.close()

# remove extra spaces (to do: handle tabs)
theLine = re.sub(" +", " ", theLine)

# extract userid and password
theCredentials = theLine.split(" ")
theUserId = theCredentials[0]
thePassword = theCredentials[1]


# text for key exchange (to do: check this message):
ssh_newkey = "Are you sure you want to continue connecting"

# ssh command line to get to "Vendor Annex"
p=pexpect.spawn("ssh -p 5000 z419512@199.45.47.14")

# may be bugs with this (???)
p.timeout=12

# to see what is happening as we go
#p.logfile = sys.stdout # this broke next p.expect (needs "" ???)


# log file
fout = open('mylog.txt','wb')
p.logfile = fout


# sends & expects...

i=p.expect([ssh_newkey, "Password: ", pexpect.EOF, pexpect.TIMEOUT])
if i==0:
    # ssh_newkey hit
    # say yes to key exchange
    p.sendline("yes")
    i=p.expect([ssh_newkey, "Password: ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1:
    # typical
    # "Password: " hit (note trick--may be hit w/ or w/o previous ssh_newkey hit)
    pass
elif i == 2 or i == 3:
    # timeout or eof hit (note trick again --may be hit w/ or w/o previous ssh_newkey hit)
    print("e2: timed out, or session died, while waiting for \"Password: \" from the Vendor Annex, exiting...")
    sys.exit(1)
else:
    # catch-all hit, will probably never be hit but if it is, then either expect options above were changed or server hit ssh_newkey twice
    print("e3: %s dies in an unexpected spot, exiting..." % __file__)
    sys.exit(1)

# at "Password: " prompt (note that Vendor Annex usually pukes up TWO prompts, so there may be a race here (to do?))
p.sendline(token)
i=p.expect(["\[Enter 1-10\]> ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1 or i == 2:
    print("e4: timed out, or session died, while waiting for \"[Enter 1-10]\" from the Vendor Annex, exiting...")
    sys.exit(1)
elif i!=0:
    print("e5: unexpected error, exiting...")
    sys.exit(1)

# got "[Enter 1-10]> " prompt

p.sendline("9")
i=p.expect(["login: ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1 or i == 2:
    print("e6: timed out, or session died, while waiting for \"login: \" from the Jump Server, exiting...")
    sys.exit(1)
elif i!=0:
    print("e7: unexpected error, exiting...")
    sys.exit(1)

# got "login: " prompt

p.sendline(theUserId)
i=p.expect(["Password: ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1 or i == 2:
    print("e8: timed out, or session died, while waiting for \"Password: \" from the Jump Server, exiting...")
    sys.exit(1)
elif i != 0:
    print("e9: unexpected error, exiting...")
    sys.exit(1)

# got "Password: " prompt

p.sendline(thePassword)
i=p.expect(["Enter Selection: ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1 or i == 2:
    print("e10: timed out, exiting...")
    sys.exit(1)
elif i != 0:
    print("e11: unexpected error, or session died, while waiting for \"Enter Selection: \" from the Jump Server, exiting...")
    sys.exit(1)

# got "Enter Selection: " prompt

p.sendline("70")
i=p.expect(["Enter Selection: ", pexpect.EOF, pexpect.TIMEOUT])
if i == 1 or i == 2:
    print("e12: timed out, or session died, while waiting for \"Enter Selection: \" from the cities page, exiting...")
    sys.exit(1)
elif i != 0:
    print("e13: unexpected error, exiting...")
    sys.exit(1)

# got "Enter Selection: " prompt again (in diff logical spot, this time in the cities page)

#Seems <cr> not needed if logging to a file (???)
#print("OK!  Enter <CR> to land on cities page...")


# relinquish CLI ctrl to user
p.interact()

