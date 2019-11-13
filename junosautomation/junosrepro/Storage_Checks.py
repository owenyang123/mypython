import os
import re
# print "start"

def storage(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Storage_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show version")
        f.write("\n==========================\n")
        for result in re.findall('show.version.detail.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)

    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system storage")
        f.write("\n==========================\n")
        for result in re.findall('show.system.storage.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    storage(a,file_name)    

#print "extensive_analysis_complete"