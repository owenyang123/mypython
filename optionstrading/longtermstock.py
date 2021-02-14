import glob, os
os.chdir("D:\pythonproject\mypython\optionstrading")
file_list=[]
for file in glob.glob("*ND20*.csv"):
    file_list.append(file)
file_list.sort()
print len(file_list)
n=int(input('plese input the number of days(less than 30): '))
if n<0:exit()
file_list=file_list[0-n:]
days=len(file_list)*0.65
stockdays={}
for i in file_list:
    with open(i) as fd:
        for j in fd.readlines():
            if len(j) > 10:
                temp=j.replace("\n","").split(",")
                if len(temp)>2:
                    if not temp[0].isalpha() or temp[0]=="call" or temp[0]=="put":temp.pop(0)
                    stockdays[temp[0]]=stockdays.get(temp[0],0)+1
listorder=sorted(stockdays.items(),key=lambda x:x[1],reverse=True)
print [i for i in listorder if i[1]>days]

os.chdir("D:\pythonproject\mypython\optionstrading")
file_list=[]
for file in glob.glob("2*.csv"):
    file_list.append(file)
file_list.sort()
print len(file_list)
file_list=file_list[0-n:]
days=len(file_list)*0.65
stockdays={}
for i in file_list:
    with open(i) as fd:
        for j in fd.readlines():
            if len(j) > 10:
                temp=j.replace("\n","").split(",")
                if len(temp) > 2:
                    if not temp[0].isalpha() or temp[0]=="call" or temp[0]=="put":temp.pop(0)
                    stockdays[temp[0]]=stockdays.get(temp[0],0)+1
listorder=sorted(stockdays.items(),key=lambda x:x[1],reverse=True)
print [i for i in listorder if i[1]>days]
