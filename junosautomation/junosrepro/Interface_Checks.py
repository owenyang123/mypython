import os
import re
#print "start"
#Finds interfaces related information from RSI and stores it to a file

def interface(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Interface_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show lacp interfaces")
        f.write("\n==========================\n")
        for result in re.findall('show.lacp.interfaces(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show lacp statistics interfaces")
        f.write("\n==========================\n")
        for result in re.findall('show.lacp.statistics.interfaces(.*?)show.', fp.read(), re.S):
            f.write(result)
        
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show interfaces terse")
        f.write("\n==========================\n")
        for result in re.findall('show.interfaces.terse(.*?)show.', fp.read(), re.S):
            f.write(result)
    f.close()

if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    interface(a,file_name) 
    
#print "interface_analysis_complete"