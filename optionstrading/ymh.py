import numpy as np
import seaborn as sns
import basictools as bt
import optionsplay as op
sns.set(style="whitegrid")
import stockplay as sp
import pandas as pd
import csv




str1='JWN ,NTAP ,SNPS ,CPRT ,TJX ,COST ,MDT ,LB ,PGR ,A ,KEYS ,HRL ,ROST ,NVDA ,ADSK ,HPE ,PVH ,BBY ,TTWO ,DG ,DE ,INTU ,ULTA ,DLTR ,RCL ,HPQ ,ADI ,AZO ,DXC '
list1=str1.replace(",","").split(" ")
l=op.caifuziyou(list1)
with open(r'ymh1.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([bt.get_data(0)]+t)

l=sp.caifuziyou(list1)
with open(r'ymh1.csv','a') as fd:
    for t in l:
        if t[-1]!=0:
            writer=csv.writer(fd)
            writer.writerow([bt.get_data(0)]+t)

'''
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
content = pd.read_html(url)
stocklist = content[0]['Symbol'].tolist()
=======
str1="CPB 17 ,JWN 11 ,NTAP 10 ,SNPS 3 ,CPRT 3 ,TJX 4 ,COST 11 ,MDT 4 ,LB 3 ,PGR 3 ,A 4 ,KEYS 9 ,HRL 4 ,ROST 4 ,KSS 2 ,NVDA 4 ,ADSK 10 ,HPE 4 ,PVH 10 ,BBY 4 ,TTWO 3 ,DG 11 ,DE 5 ,AAP 2 ,INTU 4 ,GPS 11 ,ULTA 11 ,DLTR 11 ,LOW 3 ,HPQ 10 ,TIF 16 ,WMT 2 ,HD 2 ,ADI 3 ,AZO 9 ,DXC 11 ,"
l1=[]
for i in str1.split(","):
    for j in range(len(i)):
        if i[j]==" ":
            l1.append(i[0:j])
            break

'''











