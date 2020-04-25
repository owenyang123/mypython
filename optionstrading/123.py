import yfinance as yf
aapl = yf.Ticker("AAPL")
data=aapl.option_chain('2020-04-30').calls
print aapl.info
print data['ask']
