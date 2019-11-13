import re
import os
#print "start"

def hardware(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+"\Hardware_Checks.txt"
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis alarms")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.alarms.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show system core-dumps")
        f.write("\n==========================\n")
        for result in re.findall('show.system.core-dumps.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis hardware detail")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.hardware.detail.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis environment")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.environment.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis fpc pic-status")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.fpc.pic-status.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis fpc detail")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.fpc.detail.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show pfe terse")
        f.write("\n==========================\n")
        for result in re.findall('show.pfe.terse.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis fabric summary")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.fabric.summary(.*?)show.', fp.read(), re.S):
            f.write(result)
    
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis fabric fpcs")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.fabric.fpcs.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:   
        f.write("\n\n==========================")
        f.write("\nstart-show chassis fabric plane")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.fabric.plane.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)   
    f.close()

if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    hardware(a,file_name) 

#print "hardware_analysis_complete"