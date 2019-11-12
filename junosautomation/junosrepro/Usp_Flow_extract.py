import os
import re
#from pprint import pprint
# print "start"

def spu_extract(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+r'\Usp_flow_extract.txt'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-test")
        f.write("\n==========================\n")
        result = re.findall('Start.SPU....(.*?)End.SPU...', fp.read(), re.S)
#        for test in result:
        for i in result:
            j=i.split('\n')
            if "show usp flow counters all" in i:
                f.write("\n\n")
                f.write(j[0])
            p=re.findall('show.usp.flow.counters.all(.*?)show.', i, re.S)
            if p:  
                f.write("\n==========================")
                f.write("\nshow usp flow counters all")
                f.write("\n==========================\n")
                f.write(p[0])
#                q=p[0].split('\n')
#                for r in q:
#                    #if "Drop:" in r:
#                   if r:
#                        s=r.split()
#                        #print s[-1]
#                        if not (s[-1] == '0'):
#                            f.write("\n")
#                            f.write(r)
#                    
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    spu_extract(a,file_name)  

#print "extensive_analysis_complete"