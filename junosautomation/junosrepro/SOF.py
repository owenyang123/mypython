import os
import re

# print "start"

def spu(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+r'\SOF_Usp_flow.txt'
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
                q=p[0].split('\n')
                strings=('SPU session non-llf and pkt non-llf 3310091340',
                         'NP session llf and pkt llf from DRV',
                         'NP session llf and wrong spu id 1',
                         'Rcv fragment pkt', 'Set SO flag in snd vector')
                for r in q:
                    #if ('SPU session non-llf and pkt non-llf 3310091340' in r or 'NP session llf and pkt llf from DRV' in r or 'NP session llf and wrong spu id 1' in r or 'Rcv fragment pkt' in r or 'Set SO flag in snd vector' in r):
                    if any(s in r for s in strings):
                        f.write("\n")
                        f.write(r)
                    
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    spu(a,file_name)  

#print "extensive_analysis_complete"