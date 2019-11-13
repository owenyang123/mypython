import os
import re
# print "start"

def extensive(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Extensive_em_fab_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show interfaces extensive")
        f.write("\n==========================\n")
        for result in re.findall('show.interfaces..-......extensive.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show interfaces em extensive")
        f.write("\n==========================\n")
        for result in re.findall('show.interfaces.em..extensive.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show interfaces fab extensive")
        f.write("\n==========================\n")
        for result in re.findall('show.interfaces.fab..extensive.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)          
    f.close()

if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    extensive(a,file_name)    

#print "extensive_analysis_complete"