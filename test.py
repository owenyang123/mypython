import yfinance as yf  
import matplotlib.pyplot as plt
data = yf.download('oxy','2020-01-01','2020-04-01')
print type(data)
data.High.plot()
plt.show()