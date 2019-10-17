import os
import re

path123 = raw_input('please input path: ')
reg = r'(\.py$)'
pdfre = re.compile(reg)
count=0
for path, d, filelist in os.walk(path123):
    for filename in filelist:
        t = os.path.join(path, filename)
        if re.findall(pdfre, t):
            count+=1
            print count


def walker(filepath,filetype):
    reg = filetype
    pdfre = re.compile(reg)
    for path, d, filelist in os.walk(filepath):
        for filename in filelist:
            t = os.path.join(path, filename)
            if re.findall(pdfre, t):
                print t


walker("D:/","pdf")