<<<<<<< HEAD
s="_VLMCS._TCP.wm.com"
temp=""
for i in s:
    if i==".":temp+=" ."
    else:temp+=" "+str(hex(ord(i)))
print temp
=======
from pandas_datareader.data import Options
fbop=Options('FB','google')
options_df=fbop.get_options_data(expiry=fbop.expiry_dates[0])
print (options_df)
>>>>>>> 21ecb61c0c2c638a89938bfc2459bcc40364a066
