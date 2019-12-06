import os
import csv
import re
path123=raw_input('please input path: ')
reg=r'(\.doc$)'
pdfre=re.compile(reg)
for path,d,filelist in os.walk(path123):
    for filename in filelist:
        t=os.path.join(path,filename)
        if re.findall(pdfre,t):
            print t

