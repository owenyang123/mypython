import re
import os 


def configuration(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Configuration.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    f = open(check, 'w')
    with open(file_name) as fp:
        for result in re.findall('show.configuration...except.SECRET-DATA(.*?)tnpdump', fp.read(), re.S):
            f.write(result)
    f.close()
    
#print "start"


if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    configuration(a,file_name)
    
#print "config_generation_complete"
# extract me
# extract me
# extract me