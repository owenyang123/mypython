#!/usr/bin/env python
import sys
import re

'''
TODO: per process filter

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

        if re.match(r'^\s*$',eachline) is not None:
            if debug: print "\tskip empty line"
            linenum+=1
            continue

        #find the i/o line:
        #Jul 20 13:42:09 [JUNOScript] - [66816] Outgoing: </rpc-reply>
        pat1=re.compile((r'(Jul 20 \d{2}:\d{2}:\d{2} \[JUNOScript\] '
                         r'- \[\d+\] '
                         r'(?:Outgoing|Incoming): )'
                         r'(.*)'))

        m1=pat1.search(eachline)

        #found io line {{{3}}}
        if m1 is not None:

            if debug:
                print '\t','line', linenum, 'matches style1'
                print '\t',m1.groups()

            #for io line, check the tag to see if it is complete
            io=m1.group(1)
            afterio=m1.group(2)
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
                #print current line
                #and start a new merge
                else:                   #{{{5}}}
                    if debug: 
                        print '\tio not same with previous line, will print'\
                        ' previous merge and start new merge'
                    print_mergedline(line_aftermerge,merged)
                    #print eachline,

                    #clear previous merge
                    mergedtag=''

                    #start a new merge
                    merged=True
                    mergedtag+=afterio
                    line_aftermerge=io+mergedtag

            io_prev=io

        else:

            if debug: print 'line', linenum, 'no match stype1,not interested'
            if debug: print "not empty line, will print previous merge"
            print_mergedline(line_aftermerge,merged)
            print str(linenum).rjust(6),eachline,

            #clear previous merge
            mergedtag=''
            merged=False

            #style2:
            #Jul 20 13:41:46 [JUNOScript] Started tracing session: 66894
            #<junoscript version="1.0">

            pat2=r'^(\s*)(<.*>)(\s*)'
            m2=re.search(pat2,eachline)

            if m2 is not None:

                #print 'line', linenum, 'matches style2', m2.groups()
                pass
            else:
                #print 'line', linenum, 'no match style2'
                pass
        linenum+=1

mymain()
