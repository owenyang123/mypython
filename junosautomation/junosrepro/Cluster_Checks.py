import os
import re
# print "start"

def cluster(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Cluster_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis cluster status")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.cluster.status(.*?)show.', fp.read(), re.S):
            f.write(result)
        
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis cluster interfaces")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.cluster.interfaces(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis cluster information")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.cluster.information.detail.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis cluster statistics")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.cluster.statistics(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system license")
        f.write("\n==========================\n")
        for result in re.findall('show.system.license(.*?)show.', fp.read(), re.S):
            f.write(result)
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    cluster(a,file_name)  

#print "extensive_analysis_complete"