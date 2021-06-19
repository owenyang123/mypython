import re
line = "Cats are smarter than dogs"
matchObj = re.match( r'(.*) are (.*?) .*', line, re.M|re.I)
if matchObj:
    print("matchObj.group() : ", matchObj.group(0))
    print( "matchObj.group(1) : ", matchObj.group(1))
    print( "matchObj.group(1) : ", matchObj.group(2))