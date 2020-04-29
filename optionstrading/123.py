import yfinance as yf
import numpy as np
import time
import datetime
import basictools as bt
import os

print bt.get_date_delta("2020-06-18","2020-06-04")

stock="BA"
days="19"
mail1="owenyang@junoier.net"
str1="sudo echo " + "\'"+stock+" \'" +"| "+"mail -s " +"\'" +days+ "days left to earning call" + "\' " +mail1
print str1

temp = yf.Ticker("MMM")
print temp.calendar