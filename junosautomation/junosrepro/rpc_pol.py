#!/usr/bin/env python
import sys
import re

'''
TODO: 
1. per process filter
2. how to encap if debug: print, into a func


'''

debug=False

def print_mergedline(line_aftermerge,merged):     #{{{1}}}
    '''
    check if there is merged line and print it if any
    return the merged line as well
    '''
    global debug 
    global linenum

    #if a new i/o string seen, and we've merged some chars, print
    #the merged line only
    if merged:
        if debug: print '\tnewline after merge is:'
        print str(linenum-1).rjust(6),line_aftermerge
        return line_aftermerge
    else:
        if debug: print "\tno merge before, won't print"

#def myprint(msglist):   #{{{1}}}
#    global debug
#    if debug:
#        print str(msglist)

def mymain():   #{{{1}}}

    global debug 
    global linenum

    if len(sys.argv) >= 2:
        fn=sys.argv[1]
    if len(sys.argv) > 2:
        debug=sys.argv[2]

    linenum=1
    line_aftermerge=mergedtag=''
    io_prev=''
    merged=False

    for eachline in open(fn,'r'):       #{{{2}}}

        if debug: print 'get a line: ', linenum, '"', eachline.strip(), '"'

        #skip empty line {{{3}}}
        if re.match(r'^\s*$',eachline) is not None:
            if debug: print "\tskip empty line"
            linenum+=1
            continue

        #if found io line {{{3}}}
        #Jul 20 13:42:09 [JUNOScript] - [66816] Outgoing: </rpc-reply>
        pat_ioline=re.compile(
                (
                    r'('
                        r'Jul 20 \d{2}:\d{2}:\d{2} '    #date
                        r'\[JUNOScript\] - '            #fixed
                        r'\[\d+\] '                     #pid
                        r'(?:Outgoing|Incoming): '      #incoming/outgoing
                    r')'
                    r'(.*)'                             #tags
                )
            )

        ioline=pat_ioline.search(eachline)

        if ioline is not None:

            if debug:
                print '\t','line', linenum, 'matches style1'
                print '\t',ioline.groups()

            #for io line, check the tag to see if it is complete
            io=ioline.group(1)
            afterio=ioline.group(2)
            pat4=r'(<.*>)'
            if debug:print '\tio is ', '"',repr(io),'"'
            #if debug:print '\tafterio is(repr) ', '"',repr(afterio),'"'
            if debug:print '\tafterio is(repr) ', repr(afterio)
            #m4=re.search(re.escape(pat4),
            m4=re.search(pat4,afterio)

            #complete tag {{{4}}}
            if m4 is not None:
                if debug: 
                    print '\t',afterio,' looks a complete tag'
                #markit, print the previous merged line if any, and current line
                print_mergedline(line_aftermerge,merged)
                print str(linenum).rjust(6),eachline,
                merged=False

            #incomplete tag {{{4}}}
            else:

                #1. compare with only the "last" line
                #2. TODO:also compare with all last and later lines until one
                #of below is seen:
                #  a. a new timestamp
                #  b. a complete tag
                #  c. a non-io line

                if debug: print '\t',afterio,' looks not a complete tag'

                #if not a complete tag, 
                #check if i/o string are same
                #if same, then merge all chars, and don't print
                if io==io_prev:         #{{{5}}}

                    if debug: print '\tio same with previous line, will merge'
                    if afterio=='\r':   #{{{6}}}
                        if debug: print "\tseeing ^M, need to print previous"\
                            " merge and start a new one"
                        print_mergedline(line_aftermerge,merged)
                        if debug: print "\tcurrent line is:"
                        print str(linenum).rjust(6),eachline,

                        #clear previous merge
                        mergedtag=''
                        merged=False
                    else:               #{{{6}}}
                        if debug: print '\tnot ^M, will merge'
                        mergedtag+=afterio
                        line_aftermerge=io+mergedtag
                        if debug: print '\ttag merged as(repr)',repr(mergedtag)
                        merged=True

                #if not same, 
                #print the previous merged line if any, 
                #and start a new merge
                else:                   #{{{5}}}

                    if debug: 
                        print '\tio not same with previous line, will print'\
                        ' previous merge and start new merge'
                    print_mergedline(line_aftermerge,merged)

                    #clear previous merge
                    mergedtag=''

                    #start a new merge
                    merged=True
                    mergedtag+=afterio
                    line_aftermerge=io+mergedtag

            io_prev=io

        else:           
            #if not io line {{{3}}}
            #print previously merged tags (if any), and 
            #print current line

            if debug: print 'line', linenum, 'no match stype1,not interested'
            if debug: print "not empty line, will print previous merge"
            print_mergedline(line_aftermerge,merged)
            print str(linenum).rjust(6),eachline,

            #clear previous merge
            mergedtag=''
            merged=False

            #Jul 20 13:41:46 [JUNOScript] Started tracing session: 66894
            #<junoscript version="1.0">

            #pat2=r'^(\s*)(<.*>)(\s*)'
            #m2=re.search(pat2,eachline)

            #if m2 is not None:

            #    #print 'line', linenum, 'matches style2', m2.groups()
            #    pass
            #else:
            #    #print 'line', linenum, 'no match style2'
            #    pass
        linenum+=1

if __name__ == "__main__":
    mymain()
