import os
import re
# print "start"

def re_spu(e,file_name):
    directory=e+"\RSI_analysis"
    check=directory+r'\re_cpu_Checks.txt'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    f = open(check, 'w')
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show chassis routing-engine")
        f.write("\n==========================\n")
        for result in re.findall('show.chassis.routing-engine.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system processes extensive")
        f.write("\n==========================\n")
        for result in re.findall('show.system.processes.extensive.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)

    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system statistics")
        f.write("\n==========================\n")
        for result in re.findall('show.system.statistics.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)            
    
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system virtual-memory")
        f.write("\n==========================\n")
        for result in re.findall('show.system.virtual-memory.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)    
            
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system buffer")
        f.write("\n==========================\n")
        for result in re.findall('show.system.buffer.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)    
    
    with open(file_name) as fp:
        f.write("\n==========================")
        f.write("\nstart-show system queues")
        f.write("\n==========================\n")
        for result in re.findall('show.system.queues.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)    
                
    with open(file_name) as fp:
        f.write("\n==============================\n")
        f.write("============SPU===============")
        f.write("\n==============================\n")
        f.write("\n==========================")
        f.write("\nstart-show security flow session summary")
        f.write("\n==========================\n")
        for result in re.findall('show.security.flow.session.summary.no-forwarding(.*?)show.', fp.read(), re.S):
            f.write(result)        
    f.close()
    
if __name__ == "__main__":
    print "Enter folder name which contains RSI:"
    a=raw_input()
    print "Enter rsi path, inclusing RSI name:"
    file_name=raw_input()
    re_spu(a,file_name)  

#print "extensive_analysis_complete"