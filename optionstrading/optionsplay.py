import numpy as np
import csv
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import basictools as bt
import pandas_datareader as pdr
import yfinance as yf
import os
import time
sns.set(style="whitegrid")

str1="AMAT ,MTD ,SYY ,DISCK ,QRVO ,FRT ,KLAC ,FLT ,NEM ,BDX ,CTSH ,IPGP ,EQIX ,MRO ,ALL ,NCLH ,MAA ,TDG ,VRSK ,KIM ,ANSS ,ESS ,EQR ,GPC ,MLM ,ED ,DISH ,CTVA ,WU ,AME ,JKHY ,OXY ,LNC ,PYPL ,BWA ,BKNG ,ATO ,RSG ,ANET ,AWK ,AMCR ,BR ,MCHP ,AES ,ZBH ,HII ,NRG ,SBAC ,IFF ,EXC ,CF ,J ,WRK ,WYNN ,NWSA ,AMP ,INCY ,CVS ,LIN ,AEP ,DLR ,D ,UAA ,PRU ,HPQ ,ATVI ,ALXN ,FISV ,FIS ,CSCO ,EVRG ,DIS ,EOG ,ALB ,VMC ,CDW ,SWKS ,NLOK ,EXPD ,VFC ,EXR ,PGR ,FTNT ,ALK ,REG ,HSIC ,ES ,MOS ,AEE ,FOXA ,UDR ,MYL ,PWR ,AOS ,MPC ,RCL ,GPN ,LNT ,ZTS ,REGN ,LDOS ,MET ,ITW ,IRM ,COTY ,CNP ,APA ,TMUS ,FLIR ,EA ,DVA ,MAR ,GM ,BLL ,"
stocklist=str1.replace(" ","").split(",")
earningdate = {'EOG': '2020-05-07', 'EXC': '2020-05-08', 'LIN': '2020-05-07', 'VFC': '2020-05-15', 'WU': '2020-05-05', 'QRVO': '2020-05-07', 'BR': '2020-05-08', 'SBAC': '2020-05-05', 'FLIR': '2020-05-06', 'PRU': '2020-05-05', 'BWA': '2020-05-06', 'AWK': '2020-05-06', 'MYL': '2020-05-11', 'UAA': '2020-05-11', 'ATVI': '2020-05-05', 'HSIC': '2020-05-05', 'CTSH': '2020-05-07', 'FIS': '2020-05-07', 'GPN': '2020-05-06', 'D': '2020-05-05', 'EVRG': '2020-05-06', 'PYPL': '2020-05-06', 'EQR': '2020-05-05', 'WRK': '2020-05-05', 'GPC': '2020-05-06', 'MRO': '2020-05-06', 'GM': '2020-05-06', 'MAR': '2020-05-11', 'VRSK': '2020-05-05', 'FOXA': '2020-05-06', 'AMCR': '2020-05-11', 'MAA': '2020-05-06', 'KIM': '2020-05-08', 'EXR': '2020-05-06', 'SYY': '2020-05-05', 'APA': '2020-05-06', 'AEP': '2020-05-06', 'AES': '2020-05-07', 'TDG': '2020-05-05', 'FLT': '2020-05-07', 'REGN': '2020-05-05', 'AMAT': '2020-05-14', 'IFF': '2020-05-11', 'SWKS': '2020-08-05', 'KLAC': '2020-05-05', 'ESS': '2020-05-06', 'TMUS': '2020-05-06', 'NWSA': '2020-05-07', 'AME': '2020-05-05', 'AMP': '2020-05-06', 'OXY': '2020-05-05', 'ED': '2020-05-07', 'DISCK': '2020-05-06', 'EA': '2020-05-05', 'COTY': '2020-05-11', 'DLR': '2020-05-07', 'ITW': '2020-05-05', 'BDX': '2020-05-07', 'ES': '2020-05-06', 'MPC': '2020-05-05', 'IPGP': '2020-05-05', 'BLL': '2020-05-07', 'MOS': '2020-08-03', 'MCHP': '2020-05-07', 'IRM': '2020-05-07', 'NEM': '2020-05-05', 'CTVA': '2020-05-07', 'ATO': '2020-05-06', 'DVA': '2020-05-05', 'FISV': '2020-05-07', 'REG': '2020-05-07', 'LNT': '2020-05-07', 'ZBH': '2020-05-11', 'NLOK': '2020-05-14', 'AOS': '2020-05-05', 'LNC': '2020-05-06', 'EXPD': '2020-05-05', 'J': '2020-05-06', 'CF': '2020-05-06', 'JKHY': '2020-05-04', 'FRT': '2020-05-06', 'ZTS': '2020-05-06', 'ALL': '2020-05-05', 'ALK': '2020-05-05', 'ALB': '2020-05-06', 'VMC': '2020-05-06', 'MET': '2020-05-06', 'CDW': '2020-05-06', 'ANET': '2020-05-05', 'AEE': '2020-05-11', 'WYNN': '2020-05-06', 'NRG': '2020-05-07', 'ANSS': '2020-05-06', 'CVS': '2020-05-06', 'RCL': '2020-05-05', 'DISH': '2020-05-07', 'LDOS': '2020-05-05', 'DIS': '2020-05-05', 'INCY': '2020-05-05', 'PGR': '2020-05-05', 'HII': '2020-05-07', 'FTNT': '2020-05-06', 'CNP': '2020-05-07', 'HPQ': '2020-05-07', 'MLM': '2020-05-05', 'ALXN': '2020-05-06', 'MTD': '2020-05-07', 'UDR': '2020-05-06', 'PWR': '2020-05-07', 'EQIX': '2020-05-06', 'NCLH': '2020-05-07', 'RSG': '2020-05-05', 'CSCO': '2020-05-13', 'BKNG': '2020-05-07'}

#x=yf.Ticker("OXY")
#print sorted(list(x.options))

print bt.closestprice([1,2,3,4,5,6,12],10)