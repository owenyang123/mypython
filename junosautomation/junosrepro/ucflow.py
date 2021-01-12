#!/usr/bin/env python
'''
Created on Feb 4, 2012

@author: Murtuza Attarwala
'''
import sys, os
import glob
from optparse import OptionParser

class MyParser(OptionParser):
    def format_epilog(self, formatter):
        return self.epilog

class stackElement:
    def __init__(self, depth, function, condition=None, call=False, goto=False, ret=False):
        self.depth = depth
        self.condition = condition
        self.call = call
        self.goto = goto
        self.function = function
        self.ret = ret
        self.dup = False

def maxCallDepth():
    return MAXCALLDEPTH

def isComment(line):
    if line.strip().find("//") == 0:
        return True
    elif line.strip().find("#") == 0:
        return True
    return False

def isCondition(line):
    if isComment(line):
        return False
    if line.find("if ") != -1 and line.find("(") != -1:
        return True
    return False

def isGoto(line):
    if isComment(line):
        return False
    if line.find("goto ") == -1:
        return False
    return True

def isCall(line):
    if isComment(line) == False and line.find(' call ') != -1:
        return True
    return False

def isReturn(line):
    if isComment(line) == False and line.find('return;') != -1:
        return True
    return False

def isBegin(line):
    if isComment(line):
        return False
    if line.startswith('begin') == True and line.rstrip(' \t\n').endswith('begin') == True:
        return True

def isEnd(line):
    if isComment(line):
        return False
    if line.startswith(' ') == False and line.rstrip("\n").endswith("end"):
        return True
    return False

def isFunction(line):
    if line.startswith(' ') == True or isComment(line) == True:
        return False
    elif line.rstrip("\n").endswith(":"):
        return True

def getFunctionStart(f, function):
    global previousBeginPos
    global previousFunction
    #reset the file pointer to the beginning of file
    f.seek(0)
    line = f.readline()
    while line:
        # Instructions cannot start with whitespace
        # Ignore comments
        if line.startswith(' ') == True or isComment(line) == True:
            line = f.readline()
            continue
        elif line.rstrip("\n").endswith(":") and line.rstrip('\n:') == function:
            return True
        elif line.rstrip("\n").endswith(":"):
            previousFunction = line.rstrip('\n:')
            line = f.readline()
            continue
        elif isBegin(line):
            previousBeginPos = f.tell()
            line = f.readline()
            continue
        line = f.readline()

    return False

def getNextFunction(f, line):
    while line:
        if line.startswith(' ') == True or isComment(line) == True:
            line = f.readline()
            continue
        if line.rstrip("\n").endswith(":"):
            return line.rstrip('\n:')
        line = f.readline()
    return None

def parseReturn(depth, condition=None):
    s = stackElement(depth, "return", condition)
    s.ret = True
    return s

def getFunction(depth, line, condition=None, call=False):
    function = line.split()[-1].rsplit(";", 1)[0]
    if function.find("::") != -1:
        function = function.rsplit("::", 1)[-1]
    s = stackElement(depth, function, condition, call)
    try:
        if function is not None and functionDict[function] == True:
            s.dup = True
    except KeyError:
        functionDict[function] = True
    return s

def parseCall(depth, beginPos, f, inLine, flow):
    returnTo = False
    callPos = depth
    insertFunction = False
    #save the location from where we branched
    #we need to rewind back to this position
    parseLoc = f.tell()
    sCall = getFunction(depth, inLine, None, True)
    function = None
    #rewind to the top to get the return to address
    f.seek(beginPos)
    line = f.readline()
    nextLine = f.readline()
    while nextLine and nextLine != inLine:
        line = nextLine
        nextLine = f.readline()
    #Now walk till the end and see if we have return_to
    if line.find("RETURN_TO") != -1:
        returnTo = True
        left = line.find('(')
        right = line.rfind(')')
        function = line[left+1:right]
    if returnTo == False:
        #if we didn't find return to address, then we need to return to the
        #next instruction, so get it's address
        function = getNextFunction(f, line)
    try:
        if function is not None and functionDict[function] == False:
            insertFunction = True
    except KeyError:
        functionDict[function] = True
        insertFunction = True

    if insertFunction == True:
        sReturnTo = stackElement(depth, function)
        flow.append(sReturnTo)
    flow.append(sCall)
    f.seek(parseLoc)

def parseCondition(depth, beginPos, flow, f, line, parentCondition = None):
    condition = None
    if line.strip().startswith('if ') or line.strip().startswith('else '):
        if line.strip().startswith('if ') or line.strip().startswith('else if '):
            #get everything between the first and last closing brace
            #find the occurrence of first opening brace
            left = line.find('(')
            right = line.rfind(')')
            if right != -1:
                condition = line[left+1:right]
            else:
                #traverse till we find ")"
                condition = line[left+1:]
                line = f.readline()
                while line:
                    right = line.rfind(')')
                    if right != -1:
                        condition += line[:right]
                        break
                    line = f.readline()
        if parentCondition is not None:
            condition = parentCondition + ") && (" + condition
        line = f.readline()
        #Now traverse till we encounter closing brace
        while line:
            if isGoto(line):
                s = getFunction(depth, line, condition);
                flow.append(s)
            elif isReturn(line):
                s = parseReturn(depth, condition)
                flow.append(s)
            elif isCall(line):
                parseCall(depth, beginPos, f, line, flow)
            elif line.rstrip("\n").endswith("}"):
                break
            elif line.rstrip("\n").endswith("else {"):
                parseCondition(depth, beginPos, flow, f, line)
            elif isCondition(line):
                parseCondition(depth, beginPos, flow, f, line, condition)
            line = f.readline()

def parseInstruction(depth, flow, f):
    goto = False
    call = False
    ret = False
    #Walk till we find the begin
    line = f.readline()
    while line:
        if isBegin(line):
            #Store it's location, and eat it
            #We will need to rewind to begin, if this instruction has a call
            beginPos = f.tell()
            break
        line = f.readline()
    #Parse till we encounter end
    line = f.readline()
    while line:
        if isEnd(line):
            break
        elif isCondition(line):
            parseCondition(depth, beginPos, flow, f, line)
        elif isGoto(line):
            goto = True
            #put the element on the stack
            s = getFunction(depth, line)
            flow.append(s)
        elif isReturn(line):
            s = parseReturn(callPos - 1)
            ret = True;
            flow.append(s)
        elif isCall(line):
            parseCall(depth, beginPos, f, line, flow)
            call = True
        line = f.readline()
    if goto == False and call == False and ret == False:
        #Need to read the next statement, as that will be the branch
        function = getNextFunction(f, line)
        if function is not None:
            s = stackElement(depth, function)
            try:
                if functionDict[function] == True:
                    s.dup = True
            except KeyError:
                functionDict[function] = True
            flow.append(s)


def buildFlow(depth, flow, function, f, inStackElement=None):
    indent=""
    fmt=""
    dup=""
    if depth > 0:
        for i in range(0, depth - 1):
            found = False
            #if there is anything with depth of i then put |
            for item in flow:
                if item.depth == i:
                    found = True
                    indent += "|  "
                    break
            if found == False:
                indent += "   "
        fmt += "|\n" + indent + "+->"
    if inStackElement is not None and inStackElement.dup == True:
        dup="*"
    if inStackElement is not None and inStackElement.condition is not None:
        print indent + fmt + "(" + inStackElement.condition + ") " + function + dup
    elif inStackElement is not None and inStackElement.call == True:
        print indent + fmt + "call " + function + dup
    elif inStackElement is not None and inStackElement.ret == False:
        print indent + fmt + function + dup
    elif inStackElement is None:
        print indent + fmt + function + dup
    if (inStackElement is not None and inStackElement.ret == False and \
            inStackElement.dup == False) or inStackElement is None:
        parseInstruction(depth, flow, f)
    while len(flow) > 0:
        s = flow.pop()
        name = s.function
        depth = s.depth + 1
        if (depth == maxCallDepth()):
            continue
        if s.ret == True or getFunctionStart(f, name):
            buildFlow(depth, flow, name, f, s)
        else:
            for f1 in filelist:
                if f1 is not f and getFunctionStart(f1, name):
                    buildFlow(depth, flow, name, f1, s)
def main(argv):
    path = './'
    flow = []
    global filelist
    filelist = []
    global functionDict
    functionDict = {}
    global previousBeginPos
    previousBeginPos = 0
    global MAXCALLDEPTH
    MAXCALLDEPTH = 0
    global callPos
    callPos = 0
    depth = 0
    functionFound = False
    parser = MyParser(usage="%prog [-i <depth>] <label>\n"
            "Script to generate visual instruction flow for ucode.",
            version = "%prog 1.0",
            epilog="Arguments:\n"
            "  label                 show instruction flow starting with label\n")
    parser.add_option("-i", "--instructions", type="int", dest="max_depth",
                      default=5,
                      help="Max Instruction Depth [default: %default]")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit()
    for infile in glob.glob(os.path.join(path, '*.t')):
        f = open(infile, "r")
        filelist.append(f)
    for f in filelist:
        #position the file at the beginning of the function
        if getFunctionStart(f, args[0]):
            functionFound = True
	    MAXCALLDEPTH = options.max_depth
            buildFlow(depth, flow, args[0], f)
            break
    if functionFound == False:
        print "Label \'%s\' doesn't exist" % (args[0])

if __name__ == '__main__':
    main(sys.argv)
