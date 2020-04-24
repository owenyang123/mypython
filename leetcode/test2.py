from pandas_datareader.data import Options
fbop=Options('FB','google')
options_df=fbop.get_options_data(expiry=fbop.expiry_dates[0])
print (options_df)