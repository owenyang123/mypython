import os
import re
# print "start"

def spu(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\SPU_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-SPU")
        f.write("\n==========================\n")
        for result in re.findall('Start.SPU...(.*?)End.SPU...', fp.read(), re.S):
            f.write(result)
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    spu(a,file_name)  

#print "extensive_analysis_complete"