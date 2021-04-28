#!/usr/bin/python3
import remoteconnection as rc
import os,sys
from multiprocessing import Pool
import time

if __name__ == '__main__':
    date=rc.get_date(0).replace("-","")
    boxname=["erebus.ultralab.juniper.net","hypnos.ultralab.juniper.net","moros.ultralab.juniper.net","norfolk.ultralab.juniper.net","alcoholix.ultralab.juniper.net","antalya.ultralab.juniper.net","automatix.ultralab.juniper.net","beltway.ultralab.juniper.net","bethesda.ultralab.juniper.net","botanix.ultralab.juniper.net","dogmatix.ultralab.juniper.net","getafix.ultralab.juniper.net","idefix.ultralab.juniper.net","kratos.ultralab.juniper.net","pacifix.ultralab.juniper.net","photogenix.ultralab.juniper.net","rio.ultralab.juniper.net","matrix.ultralab.juniper.net","cacofonix.ultralab.juniper.net","asterix.ultralab.juniper.net","timex.ultralab.juniper.net","greece.ultralab.juniper.net","holland.ultralab.juniper.net","nyx.ultralab.juniper.net","atlantix.ultralab.juniper.net","obelix.ultralab.juniper.net","camaro.ultralab.juniper.net","mustang.ultralab.juniper.net"]
    instance=[]
    pool=Pool(20)
    for i in boxname:
        dir_name=i.split(".")[0]+date
        pool.apply_async(rc.build_directory,args = (dir_name,))
    pool.close()
    pool.join()
# set task accounting on 
    cli_cmd="cli set task accounting on"
    instance,result_list=[],{}
    pool=Pool(10)
    for i in boxname:
        dir_name=i.split(".")[0]+date
        result_list.update({i:pool.apply_async(rc.deploycmd_noshow,args = (i,cli_cmd,))})
    pool.close()
    pool.join()
    if True not in set([i.get() for i in result_list.values()]):sys.exit(0)

    
###get cpu usage
    num=int(input("how many times will be collected at interval 10s :",))
    filename=input("please name the file you want to save :",)
    cli_cmd="cli show task accounting  detail \|no-more "
    for _ in range(num):
        pool=Pool(10)
        for i in boxname:
            dir_name=i.split(".")[0]+date
            pool.apply_async(rc.getoutput,args = (i,cli_cmd,filename,))
        pool.close()
        pool.join()
        time.sleep(5)
# set task accounting off 
    cli_cmd="cli set task accounting off"
    instance,result_list=[],[]
    pool=Pool(10)
    for i in boxname:
        dir_name=i.split(".")[0]+date
        pool.apply_async(rc.deploycmd_noshow,args = (i,cli_cmd,))
    pool.close()
    pool.join()


