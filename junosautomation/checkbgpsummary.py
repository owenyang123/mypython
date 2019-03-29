import re
filename=raw_input("please input file name :")
if filename=="":
    print "please input the correct file name with path"
    print "Anylysis quits"
    os._exit(0)
logfiles=open(filename,"r")
if logfiles.read()=="" or logfiles.read()==None:
    print "Anylysis is not necessary"
    os._exit(0)
logfiles.close()

logfiles=open(filename,"r")
localmsg=[]
dict1={}
for line in logfiles:
    l = []
    for i in  line.split(" "):
        if i=="":
            pass
        else:
            l.append(i)
    if len(l)>3:
        dict1[l[0]]=l[1:]

for i in dict1.keys():
    print i,dict1[i]
logfiles.close()
