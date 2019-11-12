from Extensive_em_fab_Checks import extensive
from Interface_Checks import interface
from Hardware_Checks import hardware
from Configuration import configuration
#from test import test
from Storage_Checks import storage
from Cluster_Checks import cluster
from RE_SPU_Checks import re_spu
from SPU_Checks import spu
from Usp_Flow_extract import spu_extract
#print "start"
#a="C:\Users\Gowtham\Desktop\srx5k"
#file_name=a+"\RSI_example.txt"
print "Enter folder name which contains RSI:"
a=raw_input()
print "Enter rsi path, inclusing RSI name:"
file_name=raw_input()

if __name__ == "__main__":
#    test(a,file_name)
    extensive(a,file_name)    
    interface(a,file_name)
    hardware(a,file_name)
    configuration(a,file_name)
    storage(a,file_name)
    cluster(a,file_name)
    re_spu(a,file_name)
    spu(a,file_name)
    spu_extract(a, file_name)
  
#print "stop"