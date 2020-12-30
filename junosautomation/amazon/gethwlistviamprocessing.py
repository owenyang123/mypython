from jnpr.junos import Device
import multiprocessing
from lxml import etree
import os
from os import getpid
import datetime
list1=["erebus.ultralab.juniper.net","hypnos.ultralab.juniper.net","moros.ultralab.juniper.net","norfolk.ultralab.juniper.net","alcoholix.ultralab.juniper.net","antalya.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","getafix.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","matrix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","asterix.ultralab.juniper.net","timex.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","nyx.ultralab.juniper.net","atlantix.ultralab.juniper.net","obelix.ultralab.juniper.net","camaro.ultralab.juniper.net","mustang.ultralab.juniper.net"]
dict1={}
def listhw(str1):
    if not str1:return None
    global dict1
    try:
        dev = Device(host = str1, user='labroot', password='lab123')
        dev.open()
        x=dev.rpc.get_chassis_inventory()
        dev.close()
        head=etree.tostring(x).split("\n")
        temp=[str1]
        for i in head:
            if "description" in i:
                temp_str=i.replace("<"," ").replace(">"," ")
                if ("DPC" in temp_str or "MPC" in temp_str or "RE"in temp_str) and "PMB" not in temp_str:
                    if i[13]=="M" or i[13]=="D" or i[13]=="R":temp.append(i[13:-14])
        dict1[temp[0]]=list(set(temp[1:]))
        multiprocessing.freeze_support()
    except:
        multiprocessing.freeze_support()
        print str1+" is unreachable"
        pass
    print os.getpid()
    return dict1
if __name__ == '__main__':
    jobs=[]
    multiprocessing.freeze_support()
    p=multiprocessing.Pool(processes=50)
    data=p.map(listhw,[i for i in list1])
    p.close()
    for i in data:
        if i:print i.items()[0][0]+": "+", ".join(i.items()[0][1])
