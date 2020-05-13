import numpy as np
import seaborn as sns

import basictools as bt
import optionsplay as op
import stockplay as sp
sns.set(style="whitegrid")
import stockplay as sp
<<<<<<< HEAD
stocklist = ["QCOM"]
print sp.caifuziyou(stocklist)

=======

stocklist = ["JD"]
print sp.caifuziyou(stocklist)
print op.caifuziyou(stocklist)
>>>>>>> ffe59675086bf4d4727bd513136978bea4bf4d63

'''
str1='COST,TQQQ'
stocklist = str1.replace(" ","").split(",")
print op.caifuziyou(stocklist)

print sp.caifuziyou(stocklist)
'''




str1='CSCO2020-05-13 ,NCLH2020-05-14 ,TTWO2020-05-20 ,VFC2020-05-15 ,ZBH2020-05-11 ,JWN2020-05-19 ,AEE2020-05-11 ,AAP2020-05-19 ,A2020-05-21 ,MAR2020-05-11 ,WMT2020-05-19 ,HRL2020-05-21 ,COTY2020-05-11 ,IFF2020-05-11 ,CPRT2020-05-20 ,LOW2020-05-20 ,ROST2020-05-21 ,SNPS2020-05-20 ,PGR2020-05-20 ,ADI2020-05-20 ,HPE2020-05-21 ,LB2020-05-20 ,UAA2020-05-11 ,AMCR2020-05-11 ,NLOK2020-05-14 ,KSS2020-05-19 ,BBY2020-05-21 ,NVDA2020-05-21 ,TJX2020-05-21 ,HD2020-05-19 ,MDT2020-05-21 ,MYL2020-05-11 ,INTU2020-05-21 ,AMAT2020-05-14 ,DXC2020-05-21 '
<<<<<<< HEAD
l= [i[0] for i in bt.rmvdate(str1)]
print op.caifuziyou(l)
=======

print op.caifuziyou([i[0] for i in bt.rmvdate(str1)])

>>>>>>> ffe59675086bf4d4727bd513136978bea4bf4d63
