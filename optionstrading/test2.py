import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
import basictools as bt
import time
import csv
import optionsplay as op

str1="LNT ,AMCR ,D ,ANSS ,ALB ,UAA ,LNC ,PWR ,CDW ,SBAC ,HII ,AES ,CTSH ,FRT ,ATO ,RCL ,EXR ,MET ,ES ,EOG ,AWK ,IRM ,SYY ,FISV ,FLT ,LIN ,CF ,MRO ,HPQ ,ESS ,DISH ,FTNT ,EQIX ,CVS ,KIM ,ZTS ,TMUS ,AEP ,J ,FOXA ,ED ,FIS ,BWA ,ZBH ,MAA ,BR ,COTY ,MYL ,AMAT ,AEE ,UDR ,DLR ,MAR ,FLIR ,QRVO ,AMP ,CTVA ,MCHP ,VFC ,DISCK ,NRG ,MTD ,CNP ,IFF ,NWSA ,NLOK ,CSCO ,GPN ,BLL ,ALXN ,REG ,WYNN ,VMC ,EVRG ,NCLH ,GPC ,BKNG ,EXC ,BDX ,APA ,PYPL "

stocklist=str1.replace(" ","").split(",")

print op.wealthfree(stocklist)