import numpy as np
import seaborn as sns
import basictools as bt
import optionsplay as op
sns.set(style="whitegrid")
import stockplay as sp



'''
str1='COST,TQQQ'
stocklist = str1.replace(" ","").split(",")
print op.caifuziyou(stocklist)

print sp.caifuziyou(stocklist)
'''




str1='HPE 2020-05-21 ,CPRT 2020-05-20 ,A 2020-05-21 ,RCL 2020-05-13 ,JWN 2020-05-19 ,NCLH 2020-05-14 ,LOW 2020-05-20 ,TJX 2020-05-21 ,NVDA 2020-05-21 ,INTU 2020-05-21 ,ADI 2020-05-20 ,BBY 2020-05-21 ,CSCO 2020-05-13 ,DE 2020-05-22 ,KSS 2020-05-19 ,LB 2020-05-20 ,HRL 2020-05-21 ,AAP 2020-05-19 ,TTWO 2020-05-20 ,HD 2020-05-19 ,VFC 2020-05-15 ,WMT 2020-05-19 ,MDT 2020-05-21 ,PGR 2020-05-20 ,AMAT 2020-05-14 ,ROST 2020-05-21 ,SNPS 2020-05-20 ,NLOK 2020-05-14 '
x=[i[0] for i in bt.rmvdate(str1)]

print op.caifuziyou(x)

print sorted(sp.caifuziyou(x),key=lambda x:x[-3])

